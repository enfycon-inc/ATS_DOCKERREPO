"""Linux regression checks using a fake Docker CLI; never touch real containers."""
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile

MOCK = r'''#!/usr/bin/env python3
import os, sys
from pathlib import Path
a=sys.argv[1:]
case=os.environ['CASE']
if a[0]=='login':
    sys.stdin.read(); sys.exit(0)
if a[0] in ['pull','tag']: sys.exit(0)
if a[0]=='run' or (a[0]=='exec' and 'cat' in a):
    if case=='missing' and a[0]=='run': sys.exit(1)
    source='model Example {\n  id String @id\n}\n'
    if a[0]=='exec': source=source.replace('\n','\r\n')
    if case=='changed' and a[0]=='run': source=source.replace('String','Int')
    sys.stdout.write(source); sys.exit(0)
if a[0]=='image': print('new-image'); sys.exit(0)
if a[0]=='inspect':
    fmt=a[a.index('-f')+1]
    if fmt=='{{.State.Status}}': print('running')
    elif 'State.Health' in fmt: print('healthy')
    elif fmt=='{{.Image}}': print(Path('actual').read_text())
    else: sys.exit(4)
    sys.exit(0)
if a[0]=='compose':
    if 'ps' in a: print('backend-container'); sys.exit(0)
    if 'config' in a: sys.exit(0)
    if 'up' in a:
        env=Path('.env').read_text()
        selected='new-image' if 'prod-gha-1-1' in env else 'old-image'
        if case=='mismatch': selected='old-image'
        Path('actual').write_text(selected); sys.exit(0)
    if 'exec' in a: sys.exit(0)
raise SystemExit('Unhandled mocked Docker command: '+str(a))
'''

def check(source):
    for case in ['crlf', 'changed', 'missing', 'mismatch', 'consumed', 'manual', 'parser']:
        with tempfile.TemporaryDirectory(prefix='ats-deploy-test-') as folder:
            root = Path(folder)
            (root / 'bin').mkdir()
            docker = root / 'bin/docker'
            docker.write_text(MOCK)
            docker.chmod(0o755)
            sleep = root / 'bin/sleep'
            sleep.write_text('#!/bin/sh\nexit 0\n')
            sleep.chmod(0o755)
            original = 'BACKEND_IMAGE=ats-backend:prod-old\nPARSER_IMAGE=ats-parser:prod-old\nFRONTEND_IMAGE=ats-frontend:prod-old\n'
            (root / '.env').write_text(original)
            (root / 'compose.yml').write_text('mock')
            (root / 'actual').write_text('old-image')
            # Deliberately consume stdin, as Docker Compose does in the real backup.
            (root / 'backup.sh').write_text('cat >/dev/null\necho BACKUP_DONE\n')
            script = source.split('\n', 1)[1].rsplit('\nATS_DEPLOY', 1)[0]
            script = script.replace('cd /var/www/ats-prod', 'cd ' + shlex.quote(folder))
            if case == 'consumed':
                script = script.replace('sh ./backup.sh </dev/null', 'sh ./backup.sh')
            env = {**os.environ, 'PATH': str(root / 'bin') + ':' + os.environ['PATH'],
                   'CASE': case, 'GH_TOKEN': 'test', 'GH_ACTOR': 'test',
                   'IMAGE_OWNER': 'enfycon-inc', 'RELEASE_TAG': 'gha-1-1',
                   'EVENT_NAME': 'repository_dispatch', 'DISPATCH_REPO': 'enfycon-inc/ats_backend'}
            if case in ['manual', 'parser']:
                env.update(EVENT_NAME='workflow_dispatch', SERVICE='parser' if case == 'parser' else 'backend')
            env.pop('DOCKER_CONFIG', None)
            result = subprocess.run(['bash', '-se'], input=script, text=True,
                                    capture_output=True, env=env, timeout=60)
            output = result.stdout + result.stderr
            if case in ['crlf', 'manual', 'parser']:
                assert result.returncode == 0 and 'Deployment successful:' in output, output
                assert (root / 'actual').read_text() == 'new-image', output
                if case == 'parser': assert 'Verified running image: worker' in output, output
            else:
                assert result.returncode != 0 and 'Deployment successful:' not in output, output
                assert (root / '.env').read_text() == original, output
                assert (root / 'actual').read_text() == 'old-image', output
                if case == 'mismatch': assert 'restoring previous' in output, output
                if case == 'consumed': assert 'before running-image verification' in output, output
            print('PASS ' + case)

if __name__ == '__main__':
    check(Path(sys.argv[1] if len(sys.argv) > 1 else 'deployment/github/deploy-current-vps.sh').read_text())
