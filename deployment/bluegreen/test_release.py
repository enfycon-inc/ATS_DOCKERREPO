import copy
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('release', Path(__file__).with_name('release.py'))
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class Fake(release.Controller):
    def __init__(self, root):
        self.root = Path(root)
        self.home = self.root / 'bluegreen'
        self.home.mkdir()
        self.statefile = self.home / 'state.json'
        images = {s: {'id': 'old-' + ('parser' if s == 'worker' else s), 'ref':'old', 'revision':'old'} for s in release.SERVICES}
        names = {s: 'initial-' + s for s in release.SERVICES}
        initial = {'id':'initial','images':images,'containers':names,'status':'success',
                   'assets':[],'adapters':{},'caddy':'old routing','time':0}
        self.state = {'current':'initial','previous':None,'successful':['initial'],
                      'pending':None,'releases':{'initial':initial},'cleanup_error':None}
        templates = {s:{'Name':'/'+names[s], 'HostConfig':{'Memory':1}, 'Config':{'Env':[]}} for s in release.SERVICES}
        self.config = {'templates':templates,'registry_owner':'enfycon-inc',
                       'assets_root':str(self.root/'assets'),'caddy_base':'reverse_proxy frontend:3000\nreverse_proxy backend:5000','project':'ats-prod'}
        self.objects = {}
        for s in release.SERVICES:
            self.objects[names[s]] = {'Id':names[s],'Name':'/'+names[s],'Image':images[s]['id'],
                'State':{'Status':'running','Health':{'Status':'healthy'}},'Config':{'Labels':{}}}
        self.routes = 'old routing'
        self.mode = None
        self.save()

    def inspect(self, name):
        return self.objects[name]

    def image(self, name):
        service = name.split('/ats-')[-1].split('@')[0]
        return {'id':'new-'+service, 'ref':name,'revision':'new'}

    def docker(self, *args, **kwargs):
        if args[0] == 'inspect':
            return json.dumps([self.objects[args[1]]]) if args[1] in self.objects else 'missing'
        if args[0] == 'ps':
            names = list(self.objects)
            if '--filter' in args:
                names = [n for n in names if n.startswith('ats-release-')]
            return '\n'.join(names)
        if args[0] == 'image':
            return ''
        if args[0] == 'logs':
            return 'celery@test ready.'
        if args[0] == 'exec' and any('getJobCounts' in arg for arg in args):
            self.objects[args[1]]['State']['Status'] = 'exited'
        if args[0] == 'start':
            self.objects[args[1]]['State']['Status'] = 'running'
        if args[0] in ('stop','kill'):
            name = args[-1]
            if name in self.objects:
                self.objects[name]['State']['Status'] = 'exited'
        if args[0] == 'rm':
            self.objects.pop(args[-1], None)
        return ''

    def clone(self, service, record, image, **kwargs):
        name = 'ats-release-'+record['id']+'-'+service
        record['containers'][service] = name
        self.objects[name] = {'Id':name,'Name':'/'+name,'Image':image['id'],
            'State':{'Status':'running','Health':{'Status':'healthy'}},'Config':{'Labels':{'io.ats.graceful-shutdown':'true'}}}
        if self.mode == 'wrong-image' and service == 'backend':
            self.objects[name]['Image'] = 'wrong'
        self.save()
        return name

    def admission(self, extra):
        if self.mode == 'capacity':
            raise RuntimeError('Insufficient memory')

    def schema(self, image):
        return 'changed' if self.mode == 'schema' and image['id'].startswith('new-') else 'same'

    def assets(self, record):
        pass

    def backup(self):
        if self.mode == 'backup':
            raise RuntimeError('Backup failed')

    def login_checks(self, record):
        if self.mode == 'login':
            raise RuntimeError('Login failed')

    def reload(self, config):
        if self.mode == 'caddy' and config != 'old routing':
            raise RuntimeError('Invalid Caddy config')
        self.routes = config

    def public_checks(self, record):
        self.healthy(record)
        if self.mode == 'public':
            raise RuntimeError('Public checks failed')

    def public_checks_fast(self, record):
        pass

    def assert_routes_unchanged(self, record):
        pass


class Tests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.controller = Fake(self.folder.name)
        self.clock = patch.object(release.time,'monotonic',side_effect=itertools.count(0,5))
        self.sleep = patch.object(release.time,'sleep')
        self.clock.start(); self.sleep.start()

    def tearDown(self):
        self.clock.stop(); self.sleep.stop(); self.folder.cleanup()

    def deploy(self, n, service='backend'):
        self.controller.deploy('gha-'+str(n)+'-1', {service:'ghcr.io/enfycon-inc/ats-'+service+'@sha256:'+'a'*64})

    def test_crlf_only_is_not_schema_change(self):
        self.assertEqual(release.canonical_schema('model A {\r\n}\r\n'),release.canonical_schema('model A {\n}\n'))
        self.assertNotEqual(release.canonical_schema('id Int'),release.canonical_schema('id String'))

    def test_unlabeled_legacy_image_is_supported(self):
        self.controller.docker=lambda *args,**kw: json.dumps([{'Id':'legacy','RepoDigests':[],'Config':{'Labels':None}}])
        self.assertIsNone(release.Controller.image(self.controller,'legacy')['revision'])

    def test_cleanup_does_not_delete_foreign_or_running_images(self):
        deleted=[]
        real=self.controller.docker
        rows=[{'Repository':'ghcr.io/enfycon-inc/ats-backend','Tag':'<none>','ID':'failed-unused'},
              {'Repository':'ghcr.io/enfycon-inc/ats-backend','Tag':'<none>','ID':'old-backend'},
              {'Repository':'enfysync-backend','Tag':'old','ID':'foreign-unused'}]
        def docker(*args,**kw):
            if args[:2]==('image','ls'):return '\n'.join(json.dumps(r) for r in rows)
            if args[:2]==('image','rm'):deleted.append(args[2]);return ''
            return real(*args,**kw)
        self.controller.docker=docker
        self.controller.cleanup()
        self.assertEqual(deleted,['failed-unused'])

    def test_external_routes_are_not_overwritten(self):
        path=self.controller.root/'Caddyfile'
        path.write_text('old routing')
        record=self.controller.state['releases']['initial']
        release.Controller.assert_routes_unchanged(self.controller,record)
        path.write_text('old routing\nnew-enfysync-site')
        with self.assertRaisesRegex(RuntimeError,'review'):
            release.Controller.assert_routes_unchanged(self.controller,record)

    def runtime_router(self):
        c=self.controller
        c.config.update(router={'id':'router'},network='private')
        c.objects['ats-release-router']={'Image':'router','State':{'Status':'running'}}
        (c.home/'router').mkdir()
        current=c.state['releases']['initial'];current['proxy_slot']=0
        for service in release.PAIR:
            c.objects[current['containers'][service]]['NetworkSettings']={'Networks':{'private':{'IPAddress':'172.18.0.2' if service=='backend' else '172.18.0.3'}}}
        target=copy.deepcopy(current);target.update(id='candidate',proxy_slot=1)
        c.state['releases']['candidate']=target
        runtime={'slot':'0','addresses':{},'ready':True,'commands':[]}
        def command(value):
            runtime['commands'].append(value)
            if value.startswith('show map'):return '0x001 active '+runtime['slot']+'\n'
            if value.startswith('set map'):runtime['slot']=value.split()[-1];return ''
            if value.startswith('set server'):
                runtime['addresses'][value.split()[2].split('/')[0]]=value.split()[-1];return ''
            if value=='show stat':
                return '# pxname,svname,status\n'+''.join(service+'_1,app,'+('UP' if runtime['ready'] else 'DOWN')+'\n' for service in release.PAIR)
            if value=='show servers state':
                return ''.join('1 '+name+' 1 app '+address+'\n' for name,address in runtime['addresses'].items())
            raise AssertionError(value)
        c.router_command=command
        c.reload=lambda config: self.fail('Runtime switch must not reload Caddy')
        return c,target,runtime

    def test_runtime_switch_changes_one_map_for_both_services(self):
        c,target,runtime=self.runtime_router()
        c.switch(target)
        self.assertEqual(runtime['slot'],'1')
        self.assertEqual(sum(cmd.startswith('set map') for cmd in runtime['commands']),1)
        self.assertEqual((c.home/'router'/'active.map').read_text(),'active 1\n')
        self.assertEqual(set(runtime['addresses']),{'frontend_1','backend_1'})

    def test_unhealthy_router_targets_never_change_map(self):
        c,target,runtime=self.runtime_router();runtime['ready']=False
        with self.assertRaisesRegex(RuntimeError,'not ready'):
            c.switch(target)
        self.assertEqual(runtime['slot'],'0')
        self.assertFalse(any(cmd.startswith('set map') for cmd in runtime['commands']))

    def test_stale_active_addresses_are_not_rewritten(self):
        c,target,runtime=self.runtime_router();runtime['slot']='1'
        with self.assertRaisesRegex(RuntimeError,'address mismatch'):
            c.switch(target)
        self.assertFalse(any(cmd.startswith('set server') for cmd in runtime['commands']))

    def test_success_keeps_previous_ready(self):
        self.deploy(1)
        self.assertEqual(self.controller.state['current'],'gha-1-1')
        self.assertEqual(self.controller.state['previous'],'initial')
        self.assertTrue(all(self.controller.objects['initial-'+s]['State']['Status']=='running' for s in release.SERVICES))

    def test_failures_do_not_publish_or_change_routes(self):
        for mode in ['capacity','schema','backup','login','wrong-image','caddy','public']:
            with self.subTest(mode=mode):
                self.controller.mode = mode
                with self.assertRaises(RuntimeError):
                    self.deploy(len(self.controller.state['releases']))
                self.assertEqual(self.controller.state['current'],'initial')
                self.assertEqual(self.controller.routes,'old routing')
                self.assertIsNone(self.controller.state['pending'])

    def test_retention_has_exactly_five_successes(self):
        for n in range(1,8):
            self.deploy(n)
        self.assertEqual(release.retained_ids(self.controller.state),['gha-7-1','gha-6-1','gha-5-1','gha-4-1','gha-3-1'])
        self.assertEqual(len(self.controller.state['releases']),5)
        self.assertTrue(all('gha-7-1' in n or 'gha-6-1' in n or 'initial-parser'==n or 'initial-worker'==n for n in self.controller.objects))

    def test_previous_rollback_is_a_route_switch(self):
        self.deploy(1); self.deploy(2)
        before=set(self.controller.objects)
        self.controller.rollback(None)
        self.assertEqual(self.controller.state['current'],'gha-1-1')
        self.assertEqual(set(self.controller.objects),before)

    def test_unknown_rollback_cannot_change_routes(self):
        with self.assertRaises(ValueError):
            self.controller.rollback('not-retained')
        self.assertEqual(self.controller.routes,'old routing')

    def test_cold_retained_release_is_recreated_before_switch(self):
        self.deploy(1); self.deploy(2); self.deploy(3)
        self.controller.rollback('gha-1-1')
        self.assertEqual(self.controller.state['current'],'gha-1-1')
        self.assertEqual(self.controller.state['previous'],'gha-3-1')
        self.assertIsNone(self.controller.state['pending'])

    def test_failed_rollback_preserves_successful_target(self):
        self.deploy(1); self.deploy(2)
        self.controller.mode='caddy'
        # Both routes use distinct container names; force only target reload failure.
        previous_reload=self.controller.reload
        old_routes=self.controller.routes
        self.controller.reload=lambda config: previous_reload(config) if config==old_routes else (_ for _ in ()).throw(RuntimeError('Failed target reload'))
        self.controller.mode=None
        with self.assertRaises(RuntimeError):
            self.controller.rollback('gha-1-1')
        self.assertEqual(self.controller.state['current'],'gha-2-1')
        self.assertEqual(self.controller.state['releases']['gha-1-1']['status'],'success')
        self.assertIsNone(self.controller.state['pending'])

    def test_interrupted_rollback_does_not_disqualify_target(self):
        self.deploy(1); self.deploy(2)
        self.controller.state['pending']='gha-1-1'
        self.controller.state['pending_action']='rollback'
        self.controller.state['rollback_snapshot']=copy.deepcopy(self.controller.state['releases']['gha-1-1'])
        self.controller.recover()
        self.assertEqual(self.controller.state['current'],'gha-2-1')
        self.assertEqual(self.controller.state['releases']['gha-1-1']['status'],'success')
        self.assertIsNone(self.controller.state['pending'])

    def test_interrupted_switch_recovers_previous(self):
        record=copy.deepcopy(self.controller.state['releases']['initial'])
        record.update(id='gha-1-1',status='switching',caddy='candidate routing')
        self.controller.state['releases']['gha-1-1']=record
        self.controller.state['pending']='gha-1-1'
        self.controller.routes='candidate routing'
        self.controller.recover()
        self.assertEqual(self.controller.routes,'old routing')
        self.assertIsNone(self.controller.state['pending'])

    def test_pending_images_are_protected_from_pruning(self):
        self.controller.state['releases']['candidate']=copy.deepcopy(self.controller.state['releases']['initial'])
        self.controller.state['releases']['candidate']['images']['backend']['id']='candidate-image'
        self.controller.state['pending']='candidate'
        self.assertIn('candidate-image',release.keep_images(self.controller.state))

    def test_parser_and_worker_change_as_one_version(self):
        self.deploy(1,'parser')
        record=self.controller.state['releases']['gha-1-1']
        self.assertEqual(record['images']['parser']['id'],record['images']['worker']['id'])
        self.assertIn('gha-1-1-worker',record['containers']['worker'])


if __name__=='__main__':
    unittest.main()
