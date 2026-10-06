"""Disposable GitHub-runner image tests. No production credentials or network."""
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import time
import uuid


def command(*args, data=None, timeout=240):
    result = subprocess.run(args, input=data, text=True,
                            stdin=subprocess.DEVNULL if data is None else None,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    if result.returncode:
        raise RuntimeError(result.stdout[-5000:])
    return result.stdout


def main(service, image):
    prefix = 'ats-ci-' + secrets.token_hex(4)
    names = []
    secrets_to_mask = []
    network = prefix
    command('docker', 'network', 'create', '--internal', network)
    with tempfile.TemporaryDirectory(prefix='ats-stage-') as directory:
        folder = Path(directory)
        def start(kind, ref, env=None, mounts=None, extra=None):
            name = prefix + '-' + kind
            names.append(name)
            args = ['docker', 'run', '-d', '--name', name, '--network', network]
            for key, value in (env or {}).items():
                args += ['-e', key + '=' + value]
                if any(word in key for word in ('PASSWORD','SECRET')):
                    secrets_to_mask.append(value)
            for source, dest in (mounts or []):
                args += ['--mount', 'type=bind,src=' + str(Path(source).resolve()) + ',dst=' + dest + ',readonly']
            command(*(args + [ref] + (extra or [])))
            return name
        def exec_(name, *args, **kw):
            return command('docker', 'exec', '-i', name, *args, **kw)
        def wait(name, args, timeout=240):
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                states = json.loads(command('docker','inspect',*names))
                for state in states:
                    if state['State']['Status'] in ('exited','dead'):
                        raise RuntimeError('Staging service exited: ' + state['Name'])
                try:
                    exec_(name, *args, timeout=10)
                    return
                except (RuntimeError, subprocess.TimeoutExpired):
                    time.sleep(3)
            logs = command('docker','logs','--tail','70',name)
            raise RuntimeError('Isolated staging readiness failed: ' + name + '\n' + logs)
        try:
            if service == 'parser':
                password = secrets.token_hex(24)
                postgres = start('postgres','postgres:16-alpine',{'POSTGRES_DB':'parser_ci','POSTGRES_USER':'parser_ci','POSTGRES_PASSWORD':password})
                wait(postgres,['pg_isready','-U','parser_ci','-d','parser_ci'])
                exec_(postgres,'psql','-U','parser_ci','-d','parser_ci',data='CREATE SCHEMA ats;')
                redis = start('redis','redis:7-alpine')
                parser = start('parser', image, {'DATABASE_URL':'postgresql://parser_ci:'+password+'@'+postgres+':5432/parser_ci',
                    'CELERY_BROKER_URL':'redis://'+redis+':6379/0','CELERY_RESULT_BACKEND':'redis://'+redis+':6379/0',
                    'HF_HUB_OFFLINE':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1'})
                wait(parser, ['python','-c',"import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/openapi.json', timeout=4).read()"])
                exec_(parser, 'python', '-c', "import app.tasks; from app.celery_app import celery_app; assert celery_app.conf.task_time_limit == 300; print('PASS parser API and worker imports')")
            elif service == 'frontend':
                secret = secrets.token_hex(32)
                secret = secrets.token_hex(32)
                frontend = start('frontend', image, {'PORT':'3000','AUTH_TRUST_HOST':'true','AUTH_SECRET':secret,'NEXTAUTH_SECRET':secret})
                wait(frontend, ['node','-e',"fetch('http://127.0.0.1:3000/api/health').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"])
                exec_(frontend,'node','-e',"const fs=require('fs');if(!fs.existsSync('/app/.next/BUILD_ID')||!fs.existsSync('/app/.next/static'))process.exit(1);console.log('PASS frontend readiness and versioned assets')")
            elif service == 'backend':
                password = secrets.token_hex(24)
                client_secret = secrets.token_hex(24)
                postgres = start('postgres','postgres:16-alpine',{'POSTGRES_DB':'ats_db','POSTGRES_USER':'ats_user','POSTGRES_PASSWORD':password})
                wait(postgres,['pg_isready','-U','ats_user','-d','ats_db'])
                for file in ['init-schemas.sql','baseline.sql','compatibility.sql']:
                    exec_(postgres,'psql','-v','ON_ERROR_STOP=1','-U','ats_user','-d','ats_db',data=Path('deployment/production',file).read_text())
                exec_(postgres,'psql','-U','ats_user','-d','ats_db',data='ALTER DATABASE ats_db SET search_path=ats,mass_mail,public;')
                redis = start('redis','redis:7-alpine')
                realm = folder / 'realm.json'
                realm.write_text(Path('deployment/bluegreen/stage-realm.json').read_text().replace('__CI_SECRET__',client_secret))
                realm.chmod(0o644)
                keycloak = start('keycloak','quay.io/keycloak/keycloak:24.0',{
                    'KEYCLOAK_ADMIN':'ci-admin','KEYCLOAK_ADMIN_PASSWORD':password,
                    'KC_DB':'postgres','KC_DB_URL':'jdbc:postgresql://' + postgres + ':5432/ats_db',
                    'KC_DB_USERNAME':'ats_user','KC_DB_PASSWORD':password,'KC_DB_SCHEMA':'keycloak',
                    'KC_HTTP_ENABLED':'true','KC_HOSTNAME_STRICT':'false','JAVA_OPTS_APPEND':'-Xms128m -Xmx384m'},
                    [(realm,'/opt/keycloak/data/import/realm.json')],['--verbose','start-dev','--import-realm'])
                # JDK image has no curl; check Keycloak from the backend network.
                tenant = str(uuid.uuid4())
                env = {'PORT':'5000','DATABASE_URL':'postgresql://ats_user:'+password+'@'+postgres+':5432/ats_db?schema=ats&options=-csearch_path%3Dats,mass_mail,public',
                    'REDIS_HOST':redis,'REDIS_PORT':'6379','BASE_DOMAIN':'ci.invalid','FRONTEND_URL':'http://frontend:3000',
                    'KEYCLOAK_INTERNAL_URL':'http://'+keycloak+':8080','KEYCLOAK_ISSUER':'http://'+keycloak+':8080/realms/enfycon-ats',
                    'KEYCLOAK_CLIENT_ID':'enfycon-ats','KEYCLOAK_CLIENT_SECRET':client_secret,
                    'KEYCLOAK_ADMIN':'ci-admin','KEYCLOAK_ADMIN_PASSWORD':password,'DEFAULT_TENANT_ID':tenant,
                    'PLATFORM_ADMIN_EMAIL':'ci-admin@example.invalid','PLATFORM_ADMIN_PASSWORD':password,'PLATFORM_ADMIN_NAME':'CI Administrator'}
                # Wait before app initialization so Keycloak provisioning can succeed.
                probe = start('probe',image,env,extra=['node','-e','setInterval(()=>{},1000)'])
                wait(probe,['node','-e',"fetch('http://"+keycloak+":8080/realms/enfycon-ats').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"])
                backend = start('backend',image,env)
                wait(backend,['node','-e',"fetch('http://127.0.0.1:5000/api/health').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"])
                # Bootstrap provisioning is asynchronous; readiness is not login readiness.
                wait(backend,['node','-e',"fetch('http://127.0.0.1:5000/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:process.env.PLATFORM_ADMIN_EMAIL,password:process.env.PLATFORM_ADMIN_PASSWORD})}).then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"])
                smoke = Path('deployment/bluegreen/stage-smoke.cjs').read_text()
                result = exec_(backend,'node','-',data=smoke,timeout=180)
                if 'SMOKE_CHECKS_COMPLETE' not in result:
                    raise RuntimeError('Staging business checks incomplete')
                print(result)
            else:
                raise ValueError('Unknown service')
            print('STAGING_VERIFIED ' + service)
        except Exception:
            for name in names:
                result = subprocess.run(['docker','logs','--tail','70',name],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
                logs = result.stdout
                for secret in secrets_to_mask:
                    logs = logs.replace(secret,'[redacted]')
                print('STAGING_DIAGNOSTIC ' + name + '\n' + logs, flush=True)
            raise
        finally:
            for name in reversed(names):
                subprocess.run(['docker','rm','-f','-v',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            subprocess.run(['docker','network','rm',network],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)


if __name__ == '__main__':
    main(*sys.argv[1:3])
