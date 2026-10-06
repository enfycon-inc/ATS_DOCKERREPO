import base64
import json
import os
from pathlib import Path
import re
import subprocess

operation = os.environ['OPERATION']
if not os.environ.get('VPS_HOST_FINGERPRINT', '').startswith('SHA256:'):
    raise ValueError('Configure the verified VPS_HOST_FINGERPRINT repository variable')
images = {}
if operation == 'deploy':
    existing = os.environ.get('EXISTING_RELEASE')
    if existing:
        if not re.fullmatch(r'gha-[0-9]+-[0-9]+', existing):
            raise ValueError('Invalid existing image tag')
        service = os.environ['SERVICE']
        if service not in ('all','frontend','backend','parser'):
            raise ValueError('Unknown service')
        services = ('frontend','backend','parser') if service == 'all' else (service,)
        for service in services:
            reference = 'ghcr.io/'+os.environ['IMAGE_OWNER'].lower()+'/ats-'+service+':'+existing
            subprocess.run(['docker','pull',reference],check=True)
            obj = json.loads(subprocess.check_output(['docker','image','inspect',reference]))[0]
            digest = next(d for d in obj['RepoDigests'] if d.startswith('ghcr.io/'+os.environ['IMAGE_OWNER'].lower()+'/ats-'+service+'@'))
            subprocess.run(['python3','deployment/bluegreen/stage.py',service,digest],check=True)
            images[service] = digest
    else:
        for file in Path('tested').rglob('image.json'):
            for service, reference in json.loads(file.read_text()).items():
                if service in images:
                    raise ValueError('Duplicate service image')
                images[service] = reference
        expected = os.environ['SERVICE']
        if os.environ['EVENT_NAME'] == 'repository_dispatch':
            expected = {'enfycon-inc/ats_backend':'backend','enfycon-inc/ats_frontend_main':'frontend',
                        'enfycon-inc/resume-parser':'parser'}[os.environ['DISPATCH_REPO']]
        expected_set = {'frontend','backend','parser'} if expected == 'all' else {expected}
        if set(images) != expected_set:
            raise ValueError('Required tested image artifacts are missing')
elif operation not in ('bootstrap','rollback','status','cleanup'):
    raise ValueError('Unknown production operation')
controller = base64.b64encode(Path('deployment/bluegreen/release.py').read_bytes()).decode()
if os.environ.get('GITHUB_ACTIONS') == 'true':
    print('::add-mask::' + controller)
with open(os.environ['GITHUB_ENV'],'a') as stream:
    stream.write('DEPLOY_IMAGES='+json.dumps(images,separators=(',',':'))+'\n')
    stream.write('CONTROLLER_B64='+controller+'\n')
