"""ATS release controller. Run as root over SSH; no listening port, no builds."""
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

SERVICES = ('frontend', 'backend', 'parser', 'worker')
PAIR = ('backend', 'frontend')


def canonical_schema(value):
    return value.replace('\r\n', '\n').rstrip('\n')


def retained_ids(state):
    order = [state['current'], state.get('previous'), *reversed(state['successful'])]
    return list(dict.fromkeys(x for x in order if x))[:5]


def keep_images(state):
    ids = retained_ids(state)
    if state.get('pending'):
        ids.append(state['pending'])
    return {v['id'] for key in ids for v in state['releases'][key]['images'].values()}


def atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(json.dumps(data, indent=2) if not isinstance(data, str) else data)
    temp.chmod(0o600)
    os.replace(temp, path)


class Controller:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.home = self.root / 'bluegreen'
        self.statefile = self.home / 'state.json'
        self.state = json.loads(self.statefile.read_text()) if self.statefile.exists() else None
        self.config = json.loads((self.home / 'runtime.json').read_text()) if self.state else None

    def command(self, args, timeout=180, data=None, check=True):
        result = subprocess.run(args, cwd=self.root, input=data, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                stdin=subprocess.DEVNULL if data is None else None,
                                timeout=timeout)
        if check and result.returncode:
            # Do not include command arguments or inspection output containing secrets.
            output = result.stdout[-3000:]
            if self.config:
                for template in self.config['templates'].values():
                    for item in template['Config']['Env']:
                        key, _, value = item.partition('=')
                        if re.search('PASSWORD|SECRET|TOKEN', key, re.I) and len(value) > 3:
                            output = output.replace(value, '[redacted]')
            raise RuntimeError(output or 'Command failed: ' + args[0])
        return result.stdout

    def docker(self, *args, **kwargs):
        return self.command(['docker', *args], **kwargs)

    def compose(self, *args, **kwargs):
        return self.docker('compose', '-f', 'compose.yml', *args, **kwargs)

    def inspect(self, name):
        return json.loads(self.docker('inspect', name))[0]

    def image(self, name):
        obj = json.loads(self.docker('image', 'inspect', name))[0]
        return {'id': obj['Id'], 'ref': name,
                'digest': next(iter(obj.get('RepoDigests', [])), None),
                'revision': (obj['Config'].get('Labels') or {}).get('org.opencontainers.image.revision')}

    def save(self):
        atomic(self.statefile, self.state)

    def initialize(self):
        if self.state:
            return
        self.home.mkdir(mode=0o700, parents=True, exist_ok=True)
        templates, images, containers = {}, {}, {}
        for service in SERVICES:
            name = self.compose('ps', '-q', service).strip()
            if not name:
                raise RuntimeError('Missing production service: ' + service)
            obj = self.inspect(name)
            templates[service] = obj
            containers[service] = obj['Name'].lstrip('/')
            images[service] = self.image(obj['Config']['Image'])
        caddy = self.compose('ps', '-q', 'caddy').strip()
        caddy_obj = self.inspect(caddy)
        data_mount = next(m for m in caddy_obj['Mounts'] if m['Destination'] == '/data')
        base = (self.root / 'Caddyfile').read_text()
        if 'backend:5000' not in base or 'frontend:3000' not in base:
            raise RuntimeError('Review existing Caddy routes before initialization')
        networks = list(templates['backend']['NetworkSettings']['Networks'])
        if len(networks) != 1:
            raise RuntimeError('Review backend network configuration')
        self.config = {'templates': templates, 'network': networks[0], 'caddy': caddy,
                       'caddy_base': base, 'assets_root': str(Path(data_mount['Source']) / 'ats-static'),
                       'resource_group': templates['backend']['HostConfig']['CgroupParent'],
                       'registry_owner': os.environ['IMAGE_OWNER']}
        self.config['project'] = templates['backend']['Config']['Labels']['com.docker.compose.project']
        backend_env = dict(x.split('=', 1) for x in templates['backend']['Config']['Env'])
        frontend_env = dict(x.split('=', 1) for x in templates['frontend']['Config']['Env'])
        self.config['public_urls'] = [backend_env['FRONTEND_URL'], frontend_env['NEXT_PUBLIC_API_URL'].rstrip('/') + '/api/health', backend_env['KEYCLOAK_ISSUER']]
        postgres = self.compose('ps', '-q', 'postgres').strip()
        postgres_env = dict(x.split('=', 1) for x in self.inspect(postgres)['Config']['Env'])
        self.config['postgres'] = {'container': postgres, 'user': postgres_env['POSTGRES_USER'], 'database': postgres_env['POSTGRES_DB']}
        atomic(self.home / 'runtime.json', self.config)
        release_id = 'initial-' + time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
        record = {'id': release_id, 'time': time.time(), 'status': 'success',
                  'images': images, 'containers': containers, 'caddy': base, 'assets': [], 'adapters': {}}
        record['schema_hash'] = hashlib.sha256(self.schema(images['backend']).encode()).hexdigest()
        for mount in templates['parser']['Mounts']:
            if mount['Destination'] in ('/app/app/parser.py', '/app/app/database.py'):
                data = Path(mount['Source']).read_bytes()
                digest = hashlib.sha256(data).hexdigest()
                target = self.home / 'adapters' / digest / Path(mount['Source']).name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                target.chmod(0o600)
                record['adapters'][mount['Destination']] = str(target)
        self.state = {'current': release_id, 'previous': None, 'successful': [release_id],
                      'releases': {release_id: record}, 'pending': None, 'cleanup_error': None}
        self.assets(record)
        self.save()
        print('Initialized release journal from live containers')

    def admission(self, extra):
        group = self.config['resource_group']
        current = int((Path('/sys/fs/cgroup') / group / 'memory.current').read_text())
        limit_text = (Path('/sys/fs/cgroup') / group / 'memory.max').read_text().strip()
        if limit_text == 'max':
            raise RuntimeError('ATS memory limit must be configured')
        limit = int(limit_text)
        if current + extra + 256 * 1024**2 > limit:
            raise RuntimeError('Insufficient ATS memory headroom; active release unchanged')
        if shutil.disk_usage(self.root).free < 3 * 1024**3:
            raise RuntimeError('Insufficient disk headroom; active release unchanged')

    def clone(self, service, record, image, backend=None, parser=None):
        template = self.config['templates'][service]
        name = 'ats-release-' + record['id'] + '-' + service
        values = dict(item.split('=', 1) for item in template['Config']['Env'])
        if backend:
            values['INTERNAL_API_URL'] = 'http://' + backend + ':5000'
        if parser:
            values['PYTHON_PARSER_URL'] = 'http://' + parser + ':8000'
        if service == 'backend':
            values['ATS_SKIP_BOOTSTRAP'] = 'true'
        folder = self.home / 'releases' / record['id']
        folder.mkdir(mode=0o700, parents=True, exist_ok=True)
        envfile = folder / (service + '.env')
        if any('\n' in v or '\r' in v for v in values.values()):
            raise RuntimeError('Multiline container environment needs review')
        atomic(envfile, '\n'.join(k + '=' + v for k, v in values.items()) + '\n')
        host = template['HostConfig']
        args = ['create', '--name', name, '--network', self.config['network'],
                '--restart', 'unless-stopped', '--memory', str(host['Memory']),
                '--cpus', str(host.get('NanoCpus', 1000000000) / 1000000000),
                '--cgroup-parent', self.config['resource_group'], '--env-file', str(envfile),
                '--label', 'ats.release.managed=true', '--label', 'ats.release.id=' + record['id'],
                '--label', 'ats.release.owner=' + self.config['project'],
                '--label', 'ats.release.service=' + service]
        logging = host.get('LogConfig', {})
        args += ['--log-driver', logging.get('Type') or 'json-file']
        for key, value in logging.get('Config', {}).items():
            args += ['--log-opt', key + '=' + value]
        if service == 'backend' and parser:
            # Existing ATS binaries also call the legacy hostname "api" directly.
            # Pin that name to this release's parser instead of the shared alias.
            parser_ip = self.inspect(parser)['NetworkSettings']['Networks'][self.config['network']]['IPAddress']
            if not parser_ip:
                raise RuntimeError('Selected parser has no private IP')
            args += ['--add-host', 'api:' + parser_ip]
        mounts = copy.deepcopy(template['Mounts'])
        for mount in mounts:
            source = mount.get('Name') if mount['Type'] == 'volume' else mount['Source']
            # Freeze mounted parser adapters with each release.
            if service in ('parser', 'worker') and mount['Destination'] in ('/app/app/parser.py', '/app/app/database.py'):
                source = record['adapters'][mount['Destination']]
            spec = 'type=' + mount['Type'] + ',src=' + source + ',dst=' + mount['Destination']
            if not mount['RW']:
                spec += ',readonly'
            args += ['--mount', spec]
        health = template['Config'].get('Healthcheck')
        if health and health.get('Test', ['NONE'])[0] != 'NONE':
            test = health['Test']
            args += ['--health-cmd', shlex.join(test[1:]) if test[0] == 'CMD' else test[1],
                     '--health-interval', '10s', '--health-timeout', '4s', '--health-retries', '30',
                     '--health-start-period', '30s']
        args.append(image['id'])
        if service == 'worker':
            args += template['Config']['Cmd']
        self.docker(*args)
        envfile.unlink()
        record['containers'][service] = name
        self.save()
        self.docker('start', name)
        return name

    def healthy(self, record, services=SERVICES, timeout=210):
        deadline = time.monotonic() + timeout
        stable = None
        while time.monotonic() < deadline:
            ready = True
            for service in services:
                obj = self.inspect(record['containers'][service])
                state = obj['State']
                if obj['Image'] != record['images'][service]['id']:
                    raise RuntimeError('Running image mismatch: ' + service)
                if state['Status'] != 'running' or state.get('OOMKilled') or state.get('Health', {}).get('Status') in ('starting', 'unhealthy'):
                    ready = False
                if service == 'parser' and ready:
                    try:
                        self.docker('exec', record['containers'][service], 'python', '-c',
                                    "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/openapi.json',timeout=4).read()", timeout=10)
                    except RuntimeError:
                        ready = False
                if service == 'worker' and ready and record['containers'][service].startswith('ats-release-'):
                    # "running" alone includes the model-loading phase. Celery
                    # emits this only after its broker connection and consumer start.
                    logs = self.docker('logs', '--tail', '1000', record['containers'][service])
                    ready = bool(re.search(r'celery@[^\s]+ ready\.', logs))
            if ready:
                stable = stable or time.monotonic()
                if time.monotonic() - stable >= 10:
                    return
            else:
                stable = None
            time.sleep(3)
        raise RuntimeError('Candidate readiness checks timed out')

    def schema(self, image):
        # No network, writable mounts, or startup side effects when reading schema.
        value = self.docker('run', '--rm', '--network', 'none', '--entrypoint', 'cat',
                            image['id'], '/app/prisma/schema.prisma')
        if not value.strip():
            raise RuntimeError('Empty Prisma schema')
        return canonical_schema(value)

    def assets(self, record):
        folder = self.home / 'releases' / record['id'] / 'assets'
        folder.mkdir(parents=True, exist_ok=True)
        self.docker('cp', record['containers']['frontend'] + ':/app/.next/static/.', str(folder))
        target = Path(self.config['assets_root'])
        target.mkdir(parents=True, exist_ok=True)
        files = []
        for source in folder.rglob('*'):
            if not source.is_file():
                continue
            if source.is_symlink():
                raise RuntimeError('Unexpected static asset symlink')
            relative = source.relative_to(folder)
            dest = target / relative
            if dest.exists() and hashlib.sha256(dest.read_bytes()).digest() != hashlib.sha256(source.read_bytes()).digest():
                raise RuntimeError('Frontend static asset collision: ' + str(relative))
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists():
                shutil.copyfile(source, dest)
                dest.chmod(0o644)
            files.append(str(relative))
        record['assets'] = files

    def routing(self, record):
        names = record['containers']
        config = self.config['caddy_base'].replace('backend:5000', names['backend'] + ':5000')
        config = config.replace('reverse_proxy ' + names['backend'] + ':5000',
                                'reverse_proxy ' + names['backend'] + ':5000 {\n    stream_close_delay 5m\n  }')
        frontend = '''handle /_next/static/* {
    uri strip_prefix /_next/static
    root * /data/ats-static
    file_server
  }
  handle {
    reverse_proxy %s:3000 {
      stream_close_delay 5m
    }
  }''' % names['frontend']
        return config.replace('reverse_proxy frontend:3000', frontend)

    def reload(self, config):
        self.docker('exec', '-i', self.config['caddy'], 'caddy', 'validate',
                    '--config', '-', '--adapter', 'caddyfile', data=config)
        self.docker('exec', '-i', self.config['caddy'], 'caddy', 'reload',
                    '--config', '-', '--adapter', 'caddyfile', data=config)
        # Keep the existing bind-mounted inode so a future restart reads this config.
        (self.root / 'Caddyfile').write_text(config)

    def public_checks(self, record):
        self.healthy(record)
        for url in self.config['public_urls']:
            with urllib.request.urlopen(url, timeout=15) as response:
                if response.status != 200:
                    raise RuntimeError('Public readiness failed')
        # Confirm Caddy loaded these upstreams, not merely an older healthy release.
        self.verify_routes(record)

    def login_checks(self, record):
        code = '''(async()=>{const base='http://127.0.0.1:5000/api/auth';
const request=async(path,body,token)=>{const r=await fetch(base+path,{method:body?'POST':'GET',headers:{'Content-Type':'application/json',...(token?{Authorization:'Bearer '+token}:{})},...(body?{body:JSON.stringify(body)}:{}),signal:AbortSignal.timeout(20000)});if(!r.ok)throw Error(path+' '+r.status);return r.json()};
const login=await request('/login',{email:process.env.PLATFORM_ADMIN_EMAIL,password:process.env.PLATFORM_ADMIN_PASSWORD});
if(!login.accessToken||!login.refreshToken)throw Error('Missing token pair');
await request('/me',null,login.accessToken);const renewed=await request('/refresh',{refreshToken:login.refreshToken});
if(!renewed.accessToken)throw Error('Refresh failed');console.log('PASS login/profile/refresh');
})().catch(()=>{console.error('Candidate authentication checks failed');process.exit(1)});'''
        self.docker('exec', record['containers']['backend'], 'node', '-e', code, timeout=90)
        parser_ip = self.inspect(record['containers']['parser'])['NetworkSettings']['Networks'][self.config['network']]['IPAddress']
        check = "require('dns').lookup('api',(e,a)=>{if(e||a!==process.argv[1])process.exit(1);else fetch('http://api:8000/openapi.json').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))})"
        self.docker('exec', record['containers']['backend'], 'node', '-e', check, parser_ip, timeout=30)

    def recover(self):
        pending = self.state.get('pending')
        if not pending:
            return
        record = self.state['releases'][pending]
        current = self.state['releases'][self.state['current']]
        self.reload(current['caddy'])
        # Restore worker if a handoff started before interruption.
        candidate_worker = record['containers']['worker']
        if candidate_worker != current['containers']['worker']:
            output = self.docker('inspect', candidate_worker, check=False)
            if output.strip().startswith('['):
                self.drain_worker(candidate_worker)
        self.docker('start', current['containers']['worker'])
        self.healthy(current)
        if self.state.get('pending_action') == 'rollback':
            self.state['releases'][pending] = self.state.pop('rollback_snapshot')
        else:
            record['status'] = 'failed-restored'
        self.state['pending'] = None
        self.state.pop('pending_action', None)
        self.save()
        print('Recovered interrupted deployment to last successful release')

    def backup(self):
        stamp = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
        folder = self.root / 'backups'
        folder.mkdir(mode=0o700, exist_ok=True)
        postgres = self.config['postgres']
        backend = self.state['releases'][self.state['current']]['containers']['backend']
        commands = [('ats-' + stamp + '.dump', ['docker', 'exec', postgres['container'], 'pg_dump', '-U', postgres['user'], '-d', postgres['database'], '-Fc']),
                    ('uploads-' + stamp + '.tar.gz', ['docker', 'exec', backend, 'tar', '-czf', '-', '/app/public', '/app/uploads'])]
        for name, args in commands:
            path = folder / name
            temp = path.with_name(name + '.tmp')
            with temp.open('wb') as stream:
                temp.chmod(0o600)
                result = subprocess.run(args, stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.PIPE, timeout=300)
            if result.returncode:
                temp.unlink(missing_ok=True)
                raise RuntimeError('Backup command failed')
            os.replace(temp, path)
        for path in folder.iterdir():
            if path.is_file() and re.fullmatch(r'(ats-|uploads-)[0-9TZ]+\.(dump|tar\.gz)', path.name) and path.stat().st_mtime < time.time() - 7 * 86400:
                path.unlink()
        print('Backup completed: ' + stamp)

    def drain_worker(self, name):
        if self.inspect(name)['State']['Status'] != 'running':
            return
        self.docker('kill', '--signal', 'TERM', name)
        deadline = time.monotonic() + 360
        while self.inspect(name)['State']['Status'] == 'running':
            if time.monotonic() >= deadline:
                raise RuntimeError('Worker has not drained; do not force-kill active tasks')
            time.sleep(3)

    def deploy(self, release_id, requested):
        if not re.fullmatch(r'gha-[0-9]+-[0-9]+', release_id):
            raise ValueError('Invalid release ID')
        if release_id in self.state['releases']:
            raise ValueError('Release ID already recorded; use rollback or a fresh run')
        if any(int(key.split('-')[1]) >= int(release_id.split('-')[1])
               for key in self.state['successful'] if key.startswith('gha-')):
            raise ValueError('Stale workflow run; active release unchanged')
        old = self.state['releases'][self.state['current']]
        self.assert_routes_unchanged(old)
        record = {'id': release_id, 'time': time.time(), 'status': 'preparing',
                  'images': copy.deepcopy(old['images']), 'containers': copy.deepcopy(old['containers']),
                  'assets': [], 'caddy': old['caddy'], 'adapters': copy.deepcopy(old['adapters'])}
        self.state['releases'][release_id] = record
        self.state['pending'] = release_id
        self.state['pending_action'] = 'deploy'
        self.save()
        switched = False
        worker_stopped = False
        try:
            for service, reference in requested.items():
                if service not in ('frontend', 'backend', 'parser'):
                    raise ValueError('Unknown image service')
                prefix = 'ghcr.io/' + self.config['registry_owner'] + '/ats-' + service
                if not re.fullmatch(re.escape(prefix) + r'@sha256:[a-f0-9]{64}', reference):
                    raise ValueError('Use an immutable ATS registry digest')
                self.docker('pull', reference, timeout=600)
                record['images'][service] = self.image(reference)
                if service == 'parser':
                    record['images']['worker'] = copy.deepcopy(record['images']['parser'])
            old_hash = old.get('schema_hash') or hashlib.sha256(self.schema(old['images']['backend']).encode()).hexdigest()
            new_hash = hashlib.sha256(self.schema(record['images']['backend']).encode()).hexdigest()
            if old_hash != new_hash:
                raise RuntimeError('Prisma schema changed: apply a reviewed compatible migration separately')
            record['schema_hash'] = new_hash
            parser_changed = record['images']['parser']['id'] != old['images']['parser']['id']
            extra = sum(self.config['templates'][s]['HostConfig']['Memory'] for s in PAIR)
            if parser_changed:
                extra += self.config['templates']['parser']['HostConfig']['Memory']
            self.admission(extra)
            if parser_changed:
                self.clone('parser', record, record['images']['parser'])
                self.healthy(record, ['parser'])
            backend = self.clone('backend', record, record['images']['backend'], parser=record['containers']['parser'])
            self.clone('frontend', record, record['images']['frontend'], backend=backend)
            self.healthy(record, PAIR)
            self.login_checks(record)
            self.assets(record)
            record['caddy'] = self.routing(record)
            self.save()
            self.backup()
            if parser_changed:
                # Celery SIGTERM performs warm shutdown, completing active tasks.
                worker_stopped = True
                self.drain_worker(old['containers']['worker'])
                self.clone('worker', record, record['images']['worker'])
                self.healthy(record, ['worker'])
            record['status'] = 'switching'
            self.save()
            switched = True
            self.reload(record['caddy'])
            self.public_checks(record)
            time.sleep(15)
            self.public_checks(record)
            self.state['previous'] = self.state['current']
            self.state['current'] = release_id
            self.state['successful'].append(release_id)
            self.state['pending'] = None
            self.state.pop('pending_action', None)
            record['status'] = 'success'
            self.save()
        except Exception:
            try:
                if switched:
                    self.reload(old['caddy'])
                if worker_stopped:
                    if record['containers']['worker'] != old['containers']['worker']:
                        self.drain_worker(record['containers']['worker'])
                    self.docker('start', old['containers']['worker'])
                self.healthy(old)
                record['status'] = 'failed-restored'
                self.state['pending'] = None
                self.state.pop('pending_action', None)
                self.save()
            except Exception:
                record['status'] = 'recovery-required'
                self.save()
                raise RuntimeError('Deployment failed and recovery needs attention')
            self.discard_failed(record)
            self.cleanup()
            raise
        self.cleanup()
        print('DEPLOYMENT_VERIFIED ' + release_id)

    def discard_failed(self, record):
        active = {name for key in retained_ids(self.state) for name in self.state['releases'][key]['containers'].values()}
        for name in record['containers'].values():
            if name not in active and name.startswith('ats-release-' + record['id'] + '-'):
                output = self.docker('inspect', name, check=False)
                if output.strip().startswith('['):
                    self.stop_retired(json.loads(output)[0], next(s for s in SERVICES if name.endswith('-' + s)))
                    self.docker('rm', name)
        folder = self.home / 'releases' / record['id']
        if folder.exists():
            shutil.rmtree(folder)

    def rollback(self, target):
        target = target or self.state.get('previous')
        if target not in retained_ids(self.state) or target == self.state['current']:
            raise ValueError('Select another retained successful release')
        record = self.state['releases'][target]
        old_id = self.state['current']
        old = self.state['releases'][old_id]
        self.assert_routes_unchanged(old)
        old_hash = old.get('schema_hash') or hashlib.sha256(self.schema(old['images']['backend']).encode()).hexdigest()
        target_hash = record.get('schema_hash') or hashlib.sha256(self.schema(record['images']['backend']).encode()).hexdigest()
        if old_hash != target_hash:
            raise RuntimeError('Rollback database compatibility review required')
        self.state['pending'] = target
        self.state['pending_action'] = 'rollback'
        self.state['rollback_snapshot'] = copy.deepcopy(record)
        self.save()
        self.state['pending'] = target
        self.state['pending_action'] = 'rollback'
        self.state['rollback_snapshot'] = copy.deepcopy(record)
        self.save()
        worker_changed = record['images']['worker']['id'] != old['images']['worker']['id']
        worker_handoff = False
        try:
            if not worker_changed:
                record['containers']['worker'] = old['containers']['worker']
            missing = []
            for service in PAIR + ('parser',):
                output = self.docker('inspect', record['containers'][service], check=False)
                try:
                    obj = json.loads(output)[0]
                except (ValueError, IndexError):
                    missing.append(service)
                    continue
                if obj['State']['Status'] != 'running':
                    missing.append(service)
            if missing:
                if 'parser' in missing:
                    # Recreated parser IPs require fresh release-specific clients.
                    missing = list(dict.fromkeys([*missing, *PAIR]))
                self.admission(sum(self.config['templates'][s]['HostConfig']['Memory'] for s in missing))
                for service in ('parser', 'backend', 'frontend'):
                    if service not in missing:
                        continue
                    name = record['containers'][service]
                    if name.startswith('ats-release-'):
                        self.docker('rm', name, check=False)
                    self.clone(service, record, record['images'][service],
                               backend=record['containers']['backend'] if service == 'frontend' else None,
                               parser=record['containers']['parser'] if service == 'backend' else None)
                record['caddy'] = self.routing(record)
                self.healthy(record, PAIR + ('parser',))
                self.login_checks(record)
            if worker_changed:
                worker_handoff = True
                self.drain_worker(old['containers']['worker'])
                output = self.docker('inspect', record['containers']['worker'], check=False)
                try:
                    obj = json.loads(output)[0]
                    self.docker('start', obj['Id'])
                except (ValueError, IndexError):
                    self.clone('worker', record, record['images']['worker'])
                self.healthy(record, ['worker'])
            for service in SERVICES:
                obj = self.inspect(record['containers'][service])
                if obj['State']['Status'] != 'running' or obj['Image'] != record['images'][service]['id'] or obj['State'].get('Health', {}).get('Status') in ('starting', 'unhealthy'):
                    self.healthy(record)
                    break
            self.save()
            self.reload(record['caddy'])
            self.public_checks_fast(record)
        except Exception:
            self.reload(old['caddy'])
            if worker_handoff:
                output = self.docker('inspect', record['containers']['worker'], check=False)
                if output.strip().startswith('[') and record['containers']['worker'] != old['containers']['worker']:
                    self.drain_worker(record['containers']['worker'])
                self.docker('start', old['containers']['worker'])
            self.healthy(old)
            self.state['releases'][target] = self.state.pop('rollback_snapshot')
            self.state['pending'] = None
            self.state.pop('pending_action', None)
            self.save()
            self.cleanup()
            raise
        self.state['previous'] = old_id
        self.state['current'] = target
        self.state['pending'] = None
        self.state.pop('pending_action', None)
        self.state.pop('rollback_snapshot', None)
        self.save()
        self.cleanup()
        print('ROLLBACK_VERIFIED ' + target)

    def public_checks_fast(self, record):
        for url in self.config['public_urls'][:2]:
            with urllib.request.urlopen(url, timeout=15) as response:
                if response.status != 200:
                    raise RuntimeError('Rollback public checks failed')
        self.verify_routes(record)

    def assert_routes_unchanged(self, record):
        if canonical_schema((self.root / 'Caddyfile').read_text()) != canonical_schema(record['caddy']):
            raise RuntimeError('Caddy routes changed outside the release controller; review before deployment')

    def verify_routes(self, record):
        loaded = json.loads(self.docker('exec', self.config['caddy'], 'wget', '-qO-', 'http://127.0.0.1:2019/config/'))
        dials = set()
        def walk(value):
            if isinstance(value, dict):
                if 'dial' in value:
                    dials.add(value['dial'])
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)
        walk(loaded)
        initial = record['caddy'] == self.config['caddy_base']
        for service, port in [('frontend',3000),('backend',5000)]:
            name = service if initial else record['containers'][service]
            if name + ':' + str(port) not in dials:
                raise RuntimeError('Loaded rollback upstream mismatch: ' + service)

    def cleanup(self):
        retained = retained_ids(self.state)
        protected = keep_images(self.state)
        obsolete_owned = {image['id'] for key, record in self.state['releases'].items()
                          if key not in retained for image in record['images'].values()} - protected
        active_names = {name for key in (self.state['current'], self.state.get('previous')) if key
                        for name in self.state['releases'][key]['containers'].values()}
        try:
            # Stop/remove only our retired application containers, not infrastructure.
            objects = [self.inspect(obj) for obj in self.docker('ps', '-aq', '--filter', 'label=ats.release.managed=true', '--filter', 'label=ats.release.owner=' + self.config['project']).split()]
            order = {'frontend':0, 'backend':1, 'worker':2, 'parser':3}
            objects.sort(key=lambda obj: order.get(obj['Config']['Labels'].get('ats.release.service'),4))
            for inspected in objects:
                obj = inspected['Id']
                if inspected['Name'].lstrip('/') not in active_names:
                    self.stop_retired(inspected)
                    self.docker('rm', obj)
            # Legacy containers have compose labels. Remove them only after initial
            # release is no longer the active or immediate rollback target.
            for service in ('frontend','backend','worker','parser'):
                template = self.config['templates'][service]
                name = template['Name'].lstrip('/')
                if name not in active_names:
                    output = self.docker('inspect', name, check=False)
                    try:
                        obj = json.loads(output)[0]
                    except (ValueError, IndexError):
                        continue
                    self.stop_retired(obj, service)
                    self.docker('rm', name)
            used = set()
            for container in self.docker('ps', '-aq').split():
                used.add(self.inspect(container)['Image'])
            canonical_tags = set()
            for key in retained:
                for service in ('frontend', 'backend', 'parser'):
                    tag = 'ats-' + service + ':release-' + key
                    self.docker('tag', self.state['releases'][key]['images'][service]['id'], tag)
                    canonical_tags.add(tag)
            for line in self.docker('image', 'ls', '--no-trunc', '--format', '{{json .}}').splitlines():
                image = json.loads(line)
                owned = re.fullmatch(r'ats-(frontend|backend|parser)', image['Repository']) or re.fullmatch(
                    r'ghcr.io/' + re.escape(self.config['registry_owner']) + r'/ats-(frontend|backend|parser)', image['Repository'])
                reference = image['Repository'] + ':' + image['Tag']
                if image['Tag'] == '<none>' and image['ID'] not in protected and image['ID'] not in used and (owned or image['ID'] in obsolete_owned):
                    self.docker('image', 'rm', image['ID'])
                    continue
                if owned and image['Tag'] != '<none>' and reference not in canonical_tags:
                    if image['ID'] in protected or image['ID'] not in used:
                        self.docker('image', 'rm', reference)
            keep_assets = {asset for key in retained for asset in self.state['releases'][key]['assets']}
            asset_root = Path(self.config['assets_root'])
            for path in asset_root.rglob('*'):
                if path.is_file() and str(path.relative_to(asset_root)) not in keep_assets:
                    path.unlink()
            for key, record in list(self.state['releases'].items()):
                if key not in retained:
                    folder = self.home / 'releases' / key
                    if folder.exists():
                        shutil.rmtree(folder)
                    del self.state['releases'][key]
            protected_adapters = {v for key in retained for v in self.state['releases'][key]['adapters'].values()}
            for path in (self.home / 'adapters').rglob('*'):
                if path.is_file() and str(path) not in protected_adapters:
                    path.unlink()
            self.state['successful'] = [key for key in self.state['successful'] if key in retained]
            self.state['cleanup_error'] = None
        except Exception as exc:
            self.state['cleanup_error'] = str(exc)
            print('CLEANUP_WARNING: release healthy but cleanup needs attention')
        self.save()

    def stop_retired(self, obj, service=None):
        if obj['State']['Status'] != 'running':
            return
        service = service or obj['Config']['Labels'].get('ats.release.service')
        if service in ('backend', 'frontend', 'parser'):
            port = {'backend':5000, 'frontend':3000, 'parser':8000}[service]
            code = "const fs=require('fs');const port='" + format(port, '04X') + "';let n=0;for(const f of ['/proc/net/tcp','/proc/net/tcp6']){for(const l of fs.readFileSync(f,'utf8').trim().split('\\n').slice(1)){const a=l.trim().split(/\\s+/);if(a[1].split(':')[1]===port&&a[3]==='01')n++}}process.exit(n?1:0)"
            deadline = time.monotonic() + 300
            while True:
                try:
                    if service == 'parser':
                        python = "from pathlib import Path; port='%04X'; n=sum(1 for f in ('/proc/net/tcp','/proc/net/tcp6') for l in Path(f).read_text().splitlines()[1:] if l.split()[1].split(':')[1]==port and l.split()[3]=='01'); raise SystemExit(1 if n else 0)" % port
                        self.docker('exec', obj['Id'], 'python', '-c', python)
                    else:
                        self.docker('exec', obj['Id'], 'node', '-e', code)
                    break
                except RuntimeError:
                    if time.monotonic() >= deadline:
                        raise RuntimeError('Retired HTTP requests still draining; cleanup will retry')
                    time.sleep(3)
        if service == 'backend' and obj['Config'].get('Labels', {}).get('io.ats.graceful-shutdown') == 'true':
            # New backend images forward TERM to Node and Nest closes Bull workers.
            # Never force-kill a mail/CV task to satisfy a cleanup deadline.
            self.docker('kill', '--signal', 'TERM', obj['Id'])
            deadline = time.monotonic() + 360
            while self.inspect(obj['Id'])['State']['Status'] == 'running':
                if time.monotonic() >= deadline:
                    raise RuntimeError('Backend jobs still draining; cleanup will retry')
                time.sleep(3)
        elif service == 'worker':
            self.drain_worker(obj['Id'])
        elif service == 'backend':
            # The initial legacy image runs Node under a shell and has no drain
            # hooks. Refuse retirement while its shared queues contain work.
            check = "(async()=>{const {Queue}=require('bullmq');const qs=['mass_mail','bulk_cv'].map(n=>new Queue(n,{connection:{host:process.env.REDIS_HOST,port:Number(process.env.REDIS_PORT||6379)}}));let busy=false;for(const q of qs){const c=await q.getJobCounts('active','wait','prioritized');busy=busy||Object.values(c).some(n=>n>0);await q.close()}if(busy)process.exit(1);const fs=require('fs');for(const pid of fs.readdirSync('/proc').filter(p=>/^\\d+$/.test(p)&&Number(p)!==process.pid)){try{const c=fs.readFileSync('/proc/'+pid+'/cmdline','utf8');if(c.includes('node')&&(c.includes('dist/main')||c.includes('dist/src/main')))process.kill(Number(pid),'SIGTERM')}catch(e){}}})().catch(()=>process.exit(1))"
            self.docker('exec', obj['Id'], 'node', '-e', check, timeout=30)
            deadline = time.monotonic() + 30
            while self.inspect(obj['Id'])['State']['Status'] == 'running':
                if time.monotonic() >= deadline:
                    raise RuntimeError('Legacy backend has not exited; cleanup will retry')
                time.sleep(1)
        else:
            self.docker('stop', '--time', '30', obj['Id'])

    def install_operations(self):
        # Retain the old files for recovery, then remove application declarations
        # from the infrastructure compose file. Their running containers are not
        # recreated; future compose up must not revive superseded app services.
        saved = self.home / 'original-compose.yml'
        if not saved.exists():
            shutil.copyfile(self.root / 'compose.yml', saved)
            saved.chmod(0o600)
            text = (self.root / 'compose.yml').read_text()
            for service in SERVICES:
                text = re.sub(r'^  ' + service + r':\n.*?(?=^  [a-z][a-z_-]*:|^volumes:|\Z)', '', text, flags=re.M | re.S)
            (self.root / 'compose.yml').write_text(text)
            try:
                self.compose('config', '--quiet')
            except Exception:
                shutil.copyfile(saved, self.root / 'compose.yml')
                saved.unlink()
                raise
        backup = self.root / 'backup.sh'
        original = self.home / 'original-backup.sh'
        if not original.exists():
            shutil.copyfile(backup, original)
            original.chmod(0o600)
        backup.write_text('#!/bin/sh\nset -eu\nexec /usr/bin/python3 ' + shlex.quote(str(self.home / 'release.py')) + ' ' + shlex.quote(str(self.root)) + ' backup </dev/null\n')
        backup.chmod(0o700)
        units = Path('/etc/systemd/system')
        entry = '/usr/bin/python3 ' + str(self.home / 'release.py') + ' ' + str(self.root)
        (units / 'ats-release-reconcile.service').write_text('[Unit]\nDescription=Recover interrupted ATS release\nAfter=docker.service\nRequires=docker.service\nConditionPathExists=' + str(self.statefile) + '\n[Service]\nType=oneshot\nExecStart=' + entry + ' reconcile\nTimeoutStartSec=600\n[Install]\nWantedBy=multi-user.target\n')
        (units / 'ats-release-cleanup.service').write_text('[Unit]\nDescription=Retain five ATS releases\nAfter=docker.service\n[Service]\nType=oneshot\nExecStart=' + entry + ' cleanup\nTimeoutStartSec=900\n')
        (units / 'ats-release-cleanup.timer').write_text('[Unit]\nDescription=Retry ATS release cleanup\n[Timer]\nOnBootSec=5min\nOnUnitActiveSec=15min\nPersistent=true\n[Install]\nWantedBy=timers.target\n')
        self.command(['systemctl', 'daemon-reload'])
        self.command(['systemctl', 'enable', 'ats-release-reconcile.service'])
        self.command(['systemctl', 'enable', '--now', 'ats-release-cleanup.timer'])
        # The stable controller is sufficient; transient SSH copies hold no images.
        for path in self.home.glob('controller-gha-*.py'):
            if re.fullmatch(r'controller-gha-[0-9]+-[0-9]+\.py', path.name):
                path.unlink()

    def prepare_handoff(self):
        if self.config.get('handoff_version') == 1:
            return
        current = self.state['releases'][self.state['current']]
        self.assert_routes_unchanged(current)
        original = copy.deepcopy(self.state)
        base = self.config['caddy_base']
        def delayed(text):
            if not text.startswith('{\n'):
                raise RuntimeError('Review Caddy global options before handoff setup')
            return text.replace('{\n','{\n  shutdown_delay 5s\n',1)
        try:
            self.config['caddy_base'] = delayed(base)
            for record in self.state['releases'].values():
                record['caddy'] = delayed(record['caddy'])
            self.reload(current['caddy'])
            self.public_checks_fast(current)
            self.config['handoff_version'] = 1
            atomic(self.home / 'runtime.json', self.config)
            self.save()
        except Exception:
            self.state = original
            self.config['caddy_base'] = base
            self.reload(original['releases'][original['current']]['caddy'])
            raise


def main():
    root, action = sys.argv[1:3]
    controller = Controller(root)
    with open(Path(root) / '.dashboard.lock', 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if action == 'status':
            if not controller.state:
                print('Blue/green not initialized')
                return
            print(json.dumps({'current': controller.state['current'], 'previous': controller.state['previous'],
                              'retained': retained_ids(controller.state), 'pending': controller.state['pending'],
                              'cleanup_error': controller.state.get('cleanup_error')}))
            return
        controller.initialize()
        controller.recover()
        if action in ('deploy', 'bootstrap'):
            controller.prepare_handoff()
            requested = json.loads(os.environ.get('DEPLOY_IMAGES', '{}'))
            controller.deploy(os.environ['RELEASE_ID'], requested)
            controller.install_operations()
        elif action == 'rollback':
            controller.prepare_handoff()
            controller.rollback(os.environ.get('ROLLBACK_TARGET') or None)
        elif action == 'cleanup':
            controller.cleanup()
        elif action == 'backup':
            controller.backup()
        elif action == 'reconcile':
            pass
        else:
            raise ValueError('Unknown release action')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('RELEASE_FAILED: ' + str(exc), file=sys.stderr)
        sys.exit(1)
