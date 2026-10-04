import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from www_posim_autonomy.evaluate import evaluate
from www_posim_autonomy.connect import API,SameOriginRedirect

class Orchestration(unittest.TestCase):
    def test_queue_cancellation_releases_only_its_own_admission(self):
        calls=[];stop=threading.Event()
        class Client:
            url='https://example.test/api'
            def call(self,path,body=None):
                calls.append(path)
                if path=='/versions':return dict(protocol=2,minimum_client='0.2.1')
                if path=='/auth/me':return dict(enabled=True)
                if path=='/competition/catalog':return dict(tasks=[dict(id='surface_station',robot='wamv')])
                if path=='/beta/queue':stop.set();return {}
                return {}
        with tempfile.TemporaryDirectory() as folder,patch('www_posim_autonomy.evaluate.subprocess.run',return_value=SimpleNamespace(returncode=0)):
            with self.assertRaises(InterruptedError):evaluate(Client(),'surface_station',['python3','controller.py'],folder,stop=stop,notify=lambda _:None)
        self.assertEqual(calls[-1],'/beta/release')
        self.assertNotIn('/competition/run/start',calls)
    def test_rejected_admission_never_releases_an_existing_session(self):
        calls=[]
        class Client:
            url='https://example.test/api'
            def call(self,path,body=None):
                calls.append(path)
                if path=='/versions':return dict(protocol=2,minimum_client='0.2.1')
                if path=='/auth/me':return dict(enabled=True)
                if path=='/competition/catalog':return dict(tasks=[dict(id='surface_station',robot='wamv')])
                if path=='/beta/queue':raise RuntimeError('already_queued_or_running')
                return {}
        with tempfile.TemporaryDirectory() as folder,patch('www_posim_autonomy.evaluate.subprocess.run',return_value=SimpleNamespace(returncode=0)):
            with self.assertRaises(RuntimeError):evaluate(Client(),'surface_station',['python3','controller.py'],folder,notify=lambda _:None)
        self.assertNotIn('/beta/release',calls)
    def test_algorithm_launches_after_scoring_and_credentials_are_not_saved(self):
        events=[];nonce='evaluation-test-nonce';secret='wwos_session=private-cookie; wwos_csrf=private-csrf'
        class Client:
            url='https://example.test/api'
            def cookie(self):return secret
            def call(self,path,body=None):
                events.append(path)
                return {
                    '/versions':dict(protocol=2,minimum_client='0.2.1'),
                    '/auth/me':dict(enabled=True),
                    '/competition/catalog':dict(tasks=[dict(id='surface_station',robot='wamv')]),
                    '/beta/status':dict(request=dict(status='active')),
                    '/session':dict(nonce=nonce,status='running',competition=dict(task='surface_station')),
                    '/rviz/profile':dict(session_nonce=nonce,control_mode='ros2'),
                    '/vehicle/external':dict(session_nonce=nonce,available=True),
                    '/competition/run':dict(session_nonce=nonce,status='finished',run_id=12),
                    '/competition/run/export?run_id=12':dict(result=dict(report=dict(score=0)),official=True),
                }.get(path,{})
        class Process:
            def __init__(self):self.stdin=SimpleNamespace(write=lambda _:None,close=lambda:None)
            def poll(self):return None
        def spawn(command,**kwargs):
            if '--ready-file' in command:
                Path(command[command.index('--ready-file')+1]).write_text(json.dumps(dict(session_nonce=nonce)))
            else:events.append('algorithm_started');self.assertIs(kwargs['stdin'],__import__('subprocess').DEVNULL)
            self.assertNotIn(secret,' '.join(command))
            self.assertEqual(kwargs['env']['ROS_DOMAIN_ID'],'76')
            self.assertEqual(kwargs['env']['ROS_AUTOMATIC_DISCOVERY_RANGE'],'LOCALHOST')
            return Process()
        with tempfile.TemporaryDirectory() as folder,patch('www_posim_autonomy.evaluate.subprocess.run',return_value=SimpleNamespace(returncode=0)),patch('www_posim_autonomy.evaluate.start_process',side_effect=spawn),patch('www_posim_autonomy.evaluate.stop_process'):
            result=evaluate(Client(),'surface_station',['python3','controller.py'],folder,notify=lambda _:None)
            self.assertTrue(result['official'])
            self.assertLess(events.index('/competition/run/start'),events.index('algorithm_started'))
            self.assertEqual(events[-1],'/beta/release')
            self.assertNotIn(secret,''.join(p.read_text() for p in Path(folder).iterdir()))
    def test_cross_origin_redirect_cannot_forward_login(self):
        import urllib.request
        request=urllib.request.Request('https://first.test/api/auth/login',data=b'private')
        with self.assertRaises(ValueError):SameOriginRedirect().redirect_request(request,None,307,'',{},'https://other.test/login')
        api=API('https://first.test/api')
        with self.assertRaises(ValueError):api.use_cookie('bad\r\nCookie: bad')

if __name__=='__main__':unittest.main()
