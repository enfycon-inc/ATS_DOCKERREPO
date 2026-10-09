"""ATS release controller. Run as root over SSH; no listening port, no builds."""
import copy
import csv
import ipaddress
import socket
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


def validate_additive_migration(sql):
    if '-- ATS: rollback-compatible' not in sql:
        raise RuntimeError('Migration needs an explicit rollback compatibility review')
    plain = re.sub(r'/\*.*?\*/|--[^\n]*', '', sql, flags=re.S)
    # Referential actions are DDL, not data mutations.
    plain = re.sub(r'\bON\s+(DELETE|UPDATE)\s+(CASCADE|RESTRICT|NO\s+ACTION|SET\s+(NULL|DEFAULT))', '', plain, flags=re.I)
    if re.search(r'\b(DROP|TRUNCATE|DELETE|UPDATE|INSERT|RENAME)\b|\bALTER\s+COLUMN\b|\bDISABLE\s+TRIGGER\b', plain, re.I):
        raise RuntimeError('Destructive/data-changing migration needs separate review; traffic unchanged')
    if not re.search(r'^\s*BEGIN\s*;', plain, re.I) or not re.search(r'COMMIT\s*;\s*$', plain, re.I):
        raise RuntimeError('Migration must be transactional')
    if not re.search(r"SET\s+LOCAL\s+lock_timeout\s*=\s*'5s'", plain, re.I):
        raise RuntimeError('Migration must bound lock waits to five seconds')


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
                        if re.search('PASSWORD|SECRET|TOKEN|DATABASE_URL', key, re.I) and len(value) > 3:
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

    def migrate(self, image, old_hash, new_hash):
        baseline = self.config.get('prisma_baseline')
        if not baseline:
            raise RuntimeError('Adopt the production Prisma baseline before a new backend release')
        active = self.state['releases'][self.state['current']]['containers']['backend']
        query = "(async()=>{const {PrismaClient}=require('@prisma/client');const p=new PrismaClient();try{console.log(JSON.stringify(await p.$queryRawUnsafe('SELECT migration_name,checksum,finished_at,rolled_back_at FROM ats._prisma_migrations ORDER BY started_at')))}finally{await p.$disconnect()}})().catch(()=>{console.error('Prisma migration history unavailable');process.exit(1)})"
        history = json.loads(self.docker('exec', active, 'node', '-e', query))
        if any(not row['finished_at'] and not row['rolled_back_at'] for row in history):
            raise RuntimeError('A failed Prisma migration requires explicit resolution')
        applied = {row['migration_name']:row['checksum'] for row in history if row['finished_at'] and not row['rolled_back_at']}
        with tempfile.TemporaryDirectory(dir=self.home, prefix='migration-') as tmp:
            folder = Path(tmp)
            container = self.docker('create', '--network', 'none', '--entrypoint', 'cat', image['id']).strip()
            try:
                self.docker('cp', container + ':/app/prisma/.', str(folder))
            finally:
                self.docker('rm', container)
            files = {p.parent.name:p for p in (folder / 'migrations').glob('*/migration.sql')}
            if not files or not set(applied).issubset(files):
                raise RuntimeError('Backend image is missing Prisma migration history')
            if applied.get(baseline['name']) != baseline['checksum']:
                raise RuntimeError('Production Prisma baseline does not match the reviewed baseline')
            for name, path in sorted(files.items()):
                checksum = hashlib.sha256(path.read_bytes()).hexdigest()
                if name in applied:
                    if checksum != applied[name]:
                        raise RuntimeError('An applied migration was changed: ' + name)
                else:
                    validate_additive_migration(path.read_text())
            values = dict(item.split('=',1) for item in self.config['templates']['backend']['Config']['Env'])
            values.update(CHECKPOINT_DISABLE='1', PRISMA_HIDE_UPDATE_MESSAGE='1')
            env = folder / 'migration.env'
            atomic(env, '\n'.join(k+'='+v for k,v in values.items())+'\n')
            self.admission(256 * 1024**2)
            args = ['run', '--rm', '--network', self.config['network'], '--memory', str(256*1024**2),
                    '--cpus', '0.5', '--cgroup-parent', self.config['resource_group'], '--env-file', str(env),
                    '--entrypoint', '/app/node_modules/.bin/prisma', image['id']]
            self.docker(*args, 'migrate', 'deploy', '--schema', '/app/prisma/schema.prisma', timeout=180)
            self.docker(*args, 'migrate', 'diff', '--from-schema-datasource', '/app/prisma/schema.prisma',
                        '--to-schema-datamodel', '/app/prisma/schema.prisma', '--exit-code', timeout=90)
        compatible = set(self.config.get('compatible_schema_hashes', []))
        compatible.update([old_hash, new_hash])
        self.config['compatible_schema_hashes'] = sorted(compatible)
        atomic(self.home / 'runtime.json', self.config)
        print('PRISMA_MIGRATIONS_VERIFIED')

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
        if self.config.get('proxy_caddy'):
            return self.config['proxy_caddy']
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
        self.switch(current)
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
        # Compose containers can be recreated independently of application releases.
        # Resolve the live database, rather than reusing the initialization-time ID.
        candidates = self.docker('compose', '-p', self.config['project'], '-f', 'compose.yml',
                                 'ps', '-q', 'postgres').split()
        if len(candidates) != 1:
            raise RuntimeError('Database backup requires exactly one running production PostgreSQL container')
        database = self.inspect(candidates[0])
        labels = database.get('Config', {}).get('Labels') or {}
        if (not database.get('State', {}).get('Running') or
                labels.get('com.docker.compose.project') != self.config['project'] or
                labels.get('com.docker.compose.service') != 'postgres'):
            raise RuntimeError('Database backup target does not match the running production PostgreSQL service')
        backend = self.state['releases'][self.state['current']]['containers']['backend']
        commands = [('ats-' + stamp + '.dump', ['docker', 'exec', candidates[0], 'pg_dump', '-U', postgres['user'], '-d', postgres['database'], '-Fc']),
                    ('uploads-' + stamp + '.tar.gz', ['docker', 'exec', backend, 'tar', '-czf', '-', '/app/public', '/app/uploads'])]
        for name, args in commands:
            path = folder / name
            temp = path.with_name(name + '.tmp')
            with temp.open('wb') as stream:
                temp.chmod(0o600)
                result = subprocess.run(args, stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.PIPE, timeout=300)
            if result.returncode:
                temp.unlink(missing_ok=True)
                kind = 'Database' if name.startswith('ats-') else 'Uploads'
                raise RuntimeError(kind + ' backup command failed (exit ' + str(result.returncode) + ')')
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
            record['schema_hash'] = new_hash
            parser_changed = record['images']['parser']['id'] != old['images']['parser']['id']
            extra = sum(self.config['templates'][s]['HostConfig']['Memory'] for s in PAIR)
            if parser_changed:
                extra += self.config['templates']['parser']['HostConfig']['Memory']
            self.admission(extra)
            backed_up = False
            if record['images']['backend']['id'] != old['images']['backend']['id'] or old_hash != new_hash:
                self.backup()
                backed_up = True
                self.migrate(record['images']['backend'], old_hash, new_hash)
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
            if not backed_up:
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
            self.switch(record)
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
                    self.switch(old)
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
        compatible = set(self.config.get('compatible_schema_hashes', []))
        if old_hash != target_hash and not {old_hash,target_hash}.issubset(compatible):
            raise RuntimeError('Rollback database compatibility review required')
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
            self.switch(record)
            self.public_checks_fast(record)
        except Exception:
            self.switch(old)
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
        if self.config.get('router'):
            if not {'ats-release-router:3000','ats-release-router:5000'}.issubset(dials):
                raise RuntimeError('Caddy router upstream mismatch')
            self.verify_router(record)
            return
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
            self.retire_legacy_backend(obj)
        else:
            self.docker('stop', '--time', '30', obj['Id'])

    def queue_control(self, action, snapshot=None):
        active = self.state['releases'][self.state['current']]['containers']['backend']
        script = '''(async()=>{
const {Queue}=require('bullmq');
const qs=['mass_mail','bulk_cv'].map(name=>new Queue(name,{connection:{host:process.env.REDIS_HOST,port:Number(process.env.REDIS_PORT||6379)}}));
try {
 const action=process.argv[1], previous=JSON.parse(process.argv[2]); let result;
 if(action==='snapshot')result=await Promise.all(qs.map(async q=>({name:q.name,paused:await q.isPaused()})));
 else if(action==='pause') {for(const q of qs)if(!previous.find(p=>p.name===q.name).paused)await q.pause();}
 else if(action==='active')result=(await Promise.all(qs.map(q=>q.getActiveCount()))).reduce((a,b)=>a+b,0);
 else if(action==='restore') {for(const q of qs)if(!previous.find(p=>p.name===q.name).paused)await q.resume();}
 else throw Error('Unknown queue action');
 console.log(JSON.stringify(result??null));
}finally{await Promise.all(qs.map(q=>q.close()))}
})().catch(()=>{console.error('Queue retirement operation failed');process.exit(1)});'''
        return json.loads(self.docker('exec', active, 'node', '-e', script, action,
                                      json.dumps(snapshot or []), timeout=30).strip())

    def restore_retirement_queues(self):
        marker = self.home / 'queue-retirement.json'
        if marker.exists():
            self.queue_control('restore', json.loads(marker.read_text()))
            marker.unlink()

    def retire_legacy_backend(self, obj):
        # Container PID 1 ignores default TERM when the old image has no Node
        # shutdown handler. Pause only job dispatch, let every active job finish,
        # and stop the idle process. Queued jobs remain in Redis throughout.
        self.restore_retirement_queues()
        previous = self.queue_control('snapshot')
        marker = self.home / 'queue-retirement.json'
        atomic(marker, previous)
        try:
            self.queue_control('pause', previous)
            deadline = time.monotonic() + 300
            while self.queue_control('active'):
                if time.monotonic() >= deadline:
                    raise RuntimeError('Active backend jobs still draining; cleanup will retry')
                time.sleep(3)
            # HTTP connections drained above; global queue pause prevents an idle
            # legacy worker from claiming a job between verification and exit.
            self.docker('kill', '--signal', 'KILL', obj['Id'])
        finally:
            self.restore_retirement_queues()

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

    def router_command(self, command):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(10)
            client.connect(str(self.home / 'router' / 'admin.sock'))
            client.sendall((command + '\n').encode())
            client.shutdown(socket.SHUT_WR)
            chunks = []
            while True:
                chunk = client.recv(65536)
                if not chunk:
                    break
                chunks.append(chunk)
        return b''.join(chunks).decode()

    def router_slot(self, record):
        if 'proxy_slot' not in record:
            occupied = {r['proxy_slot'] for r in self.state['releases'].values() if 'proxy_slot' in r}
            record['proxy_slot'] = next(n for n in range(6) if n not in occupied)
            self.save()
        return str(record['proxy_slot'])

    def router_addresses(self, record):
        result = {}
        for service in PAIR:
            obj = self.inspect(record['containers'][service])
            if obj['State']['Status'] != 'running' or obj['Image'] != record['images'][service]['id']:
                raise RuntimeError('Router target is not the verified running image')
            address = obj['NetworkSettings']['Networks'][self.config['network']]['IPAddress']
            result[service] = str(ipaddress.IPv4Address(address))
        return result

    def router_configuration(self):
        text = '''global
  stats socket /route/admin.sock mode 600 level admin
  maxconn 4096
defaults
  mode http
  timeout connect 5s
  timeout client 5m
  timeout server 5m
  timeout tunnel 1h
frontend frontend
  bind :3000
  use_backend frontend_%[str(active),map(/route/active.map)]
frontend backend
  bind :5000
  use_backend backend_%[str(active),map(/route/active.map)]
'''
        rows = {}
        for record in self.state['releases'].values():
            if 'proxy_slot' not in record:
                continue
            try:
                rows[str(record['proxy_slot'])] = self.router_addresses(record)
            except (RuntimeError, KeyError):
                pass  # Older retained images need to be recreated before use.
        for slot in range(6):
            for service, port in [('frontend', 3000), ('backend', 5000)]:
                address = rows.get(str(slot), {}).get(service, '127.0.0.1')
                text += (f'backend {service}_{slot}\n  http-reuse safe\n'
                         f'  server app {address}:{port} check inter 1s rise 1 fall 3\n')
        return text

    def verify_router(self, record):
        slot = self.router_slot(record)
        mapping = self.router_command('show map /route/active.map')
        if not any(line.split()[1:] == ['active', slot] for line in mapping.splitlines() if len(line.split()) == 3):
            raise RuntimeError('Active router release mismatch')
        states = self.router_command('show servers state').splitlines()
        for service, address in self.router_addresses(record).items():
            if not any(len(row := line.split()) > 4 and row[1] == service + '_' + slot and row[3] == 'app' and row[4] == address for line in states):
                raise RuntimeError('Runtime router address mismatch: ' + service)

    def switch(self, record):
        if not self.config.get('router'):
            self.reload(record['caddy'])
            return
        slot = self.router_slot(record)
        addresses = self.router_addresses(record)
        folder = self.home / 'router'
        obj = self.inspect('ats-release-router')
        if obj['Image'] != self.config['router']['id']:
            raise RuntimeError('Unexpected router image; review required')
        if obj['State']['Status'] != 'running':
            self.docker('start', 'ats-release-router')
        deadline = time.monotonic() + 20
        while True:
            try:
                self.router_command('show map /route/active.map')
                break
            except (OSError, TimeoutError):
                if time.monotonic() >= deadline:
                    raise RuntimeError('Router runtime unavailable')
                time.sleep(.2)
        # Persist validated server addresses for a Docker/VPS restart. The running
        # process is never reloaded during a release switch.
        atomic(folder / 'haproxy.cfg', self.router_configuration())
        self.docker('exec', 'ats-release-router', 'haproxy', '-c', '-f', '/route/haproxy.cfg')
        active = self.router_command('show map /route/active.map')
        selected = any(line.split()[1:] == ['active', slot] for line in active.splitlines() if len(line.split()) == 3)
        for service, address in addresses.items():
            name = service + '_' + slot + '/app'
            if selected:
                # Never rewrite an active target; a stale journal must recover
                # using another slot rather than disturb in-flight requests.
                self.verify_router(record)
                break
            self.router_command('set server ' + name + ' addr ' + address)
        deadline = time.monotonic() + 15
        while True:
            stats = csv.DictReader(self.router_command('show stat').lstrip('# ').splitlines())
            ready = {row['pxname'] for row in stats if row['svname'] == 'app' and row['status'] == 'UP'}
            if {'frontend_' + slot, 'backend_' + slot}.issubset(ready):
                break
            if time.monotonic() >= deadline:
                raise RuntimeError('Router targets not ready; traffic unchanged')
            time.sleep(.2)
        atomic(folder / 'active.map', 'active ' + slot + '\n')
        self.router_command('set map /route/active.map active ' + slot)
        self.verify_router(record)

    def prepare_router(self):
        if self.config.get('router'):
            return
        current = self.state['releases'][self.state['current']]
        self.assert_routes_unchanged(current)
        original = copy.deepcopy(self.state)
        old_config = copy.deepcopy(self.config)
        folder = self.home / 'router'
        folder.mkdir(mode=0o700, exist_ok=True)
        self.admission(64 * 1024**2)
        migration = self.home / 'router-migration.json'
        atomic(migration, {'state': original, 'config': old_config})
        try:
            for record in self.state['releases'].values():
                self.router_slot(record)
            atomic(folder / 'haproxy.cfg', self.router_configuration())
            atomic(folder / 'active.map', 'active ' + self.router_slot(current) + '\n')
            self.docker('pull', 'haproxy:3.2-alpine', timeout=180)
            image = self.image('haproxy:3.2-alpine')
            self.docker('run', '--rm', '--user', '0:0', '--network', 'none',
                        '-v', str(folder) + ':/route', image['id'],
                        'haproxy', '-c', '-f', '/route/haproxy.cfg')
            self.docker('run', '-d', '--name', 'ats-release-router', '--user', '0:0',
                        '--network', self.config['network'], '--restart', 'unless-stopped',
                        '--memory', str(64 * 1024**2), '--cpus', '0.15',
                        '--cgroup-parent', self.config['resource_group'],
                        '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
                        '--log-opt', 'max-size=5m', '--log-opt', 'max-file=2',
                        '-v', str(folder) + ':/route', image['id'],
                        'haproxy', '-W', '-db', '-f', '/route/haproxy.cfg')
            self.config['router'] = image
            deadline = time.monotonic() + 20
            while not (folder / 'admin.sock').exists():
                if time.monotonic() >= deadline:
                    raise RuntimeError('Router runtime socket unavailable')
                time.sleep(.2)
            self.switch(current)
            routed = copy.deepcopy(current)
            routed['containers'].update(frontend='ats-release-router', backend='ats-release-router')
            self.config['proxy_caddy'] = self.routing(routed)
            self.reload(self.config['proxy_caddy'])  # One-time infrastructure migration.
            for record in self.state['releases'].values():
                record['caddy'] = self.config['proxy_caddy']
            self.public_checks_fast(current)
            atomic(self.home / 'runtime.json', self.config)
            self.save()
            migration.unlink()
        except Exception:
            self.config = old_config
            self.state = original
            self.reload(original['releases'][original['current']]['caddy'])
            atomic(self.home / 'runtime.json', self.config)
            self.save()
            self.docker('rm', '-f', 'ats-release-router', check=False)
            migration.unlink(missing_ok=True)
            raise

    def recover_router_migration(self):
        marker = self.home / 'router-migration.json'
        if not marker.exists():
            return
        original = json.loads(marker.read_text())
        self.config, self.state = original['config'], original['state']
        self.reload(self.state['releases'][self.state['current']]['caddy'])
        atomic(self.home / 'runtime.json', self.config)
        self.save()
        self.docker('rm', '-f', 'ats-release-router', check=False)
        marker.unlink()
        print('Recovered interrupted one-time router setup')



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
                              'cleanup_error': controller.state.get('cleanup_error'),
                              'prisma_baseline': controller.config.get('prisma_baseline', {}).get('name')}))
            return
        controller.recover_router_migration()
        controller.restore_retirement_queues()
        controller.initialize()
        controller.recover()
        if action in ('deploy', 'bootstrap'):
            controller.prepare_router()
            requested = json.loads(os.environ.get('DEPLOY_IMAGES', '{}'))
            controller.deploy(os.environ['RELEASE_ID'], requested)
            controller.install_operations()
        elif action == 'rollback':
            controller.prepare_router()
            controller.rollback(os.environ.get('ROLLBACK_TARGET') or None)
        elif action == 'cleanup':
            controller.cleanup()
        elif action == 'backup':
            controller.backup()
        elif action == 'reconcile':
            if controller.config.get('router'):
                controller.switch(controller.state['releases'][controller.state['current']])
                controller.public_checks_fast(controller.state['releases'][controller.state['current']])
        else:
            raise ValueError('Unknown release action')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        # Some subprocess/IO exceptions have an empty string representation. Keep
        # the failure actionable without printing command arguments or secrets.
        detail = str(exc).strip() or (type(exc).__name__ + ': ' + repr(exc))
        print('RELEASE_FAILED: ' + detail, file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
