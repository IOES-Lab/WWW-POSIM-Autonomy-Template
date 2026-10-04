"""Local ROS publications -> authenticated bounded direct-control WSS."""
import json
import threading
import time
from urllib.parse import urlparse
import websocket
from rosidl_runtime_py.utilities import get_message
from rosidl_runtime_py.convert import message_to_ordereddict


class ControlClient:
    def __init__(self, node, profile, url, cookie, origin):
        if profile.get('control_mode')!='ros2' or not profile.get('session_nonce'):
            raise ValueError('Download a profile from an active ROS2 direct-control session.')
        expected={'/wwos/cmd_vel':'geometry_msgs/msg/TwistStamped','/wwos/thrusters':'std_msgs/msg/Float64MultiArray'}
        topics=profile.get('command_topics',[])
        if not topics or any(expected.get(e.get('name'))!=e.get('type') for e in topics):raise ValueError('Unsupported command profile')
        self.node=node;self.profile=profile;self.url=urlparse(url)._replace(path='/control',query='',fragment='').geturl()
        self.cookie=cookie;self.origin=origin;self.lock=threading.Lock();self.latest=None
        self.stop_event=threading.Event();self.acks=0;self.connections=0;self.last_error=None;self.last_ack=None
        self.subscriptions=[node.create_subscription(get_message(e['type']),e['name'],lambda m,e=e:self.receive(m,e),1) for e in topics]
        self.thread=threading.Thread(target=self.run,daemon=True);self.thread.start()

    def receive(self, message, entry):
        with self.lock:self.latest=(time.monotonic(),entry,dict(message_to_ordereddict(message)))

    def recent(self):
        with self.lock:
            return self.latest if self.latest and time.monotonic()-self.latest[0]<.3 else None

    def run(self):
        while not self.stop_event.is_set():
            if not self.recent():self.stop_event.wait(.05);continue
            ws=None
            try:
                ws=websocket.create_connection(self.url,timeout=1,**({'cookie':self.cookie,'origin':self.origin} if self.cookie else {}))
                ws.send(json.dumps({'op':'acquire','session_nonce':self.profile['session_nonce']}))
                acquired=json.loads(ws.recv())
                if acquired.get('op')!='acquired':raise ValueError(acquired.get('detail','control_acquire_rejected'))
                self.connections+=1;offset=acquired['server_time']-time.time();sequence=0;previous=None
                while not self.stop_event.is_set():
                    current=self.recent()
                    if not current:break
                    if current[0]==previous:self.stop_event.wait(.01);continue
                    previous=current[0];sequence+=1
                    ws.send(json.dumps({'op':'publish','topic':current[1]['name'],'type':current[1]['type'],'msg':current[2],
                        'lease':acquired['lease'],'session_nonce':self.profile['session_nonce'],'sequence':sequence,'sent_at':time.time()+offset},allow_nan=False))
                    ack=json.loads(ws.recv())
                    if ack.get('op')!='ack' or ack.get('sequence')!=sequence or not ack.get('accepted'):raise ValueError(ack.get('detail','control_rejected'))
                    self.acks+=1;self.last_ack=ack;self.last_error=None
                ws.send(json.dumps({'op':'release'}))
            except Exception as error:
                self.last_error=str(error)[:120]
                if not self.stop_event.is_set():self.node.get_logger().warning('Remote control unavailable: '+self.last_error)
            finally:
                if ws:
                    try:ws.close()
                    except Exception:pass
            self.stop_event.wait(.2)

    def close(self):
        self.stop_event.set();self.thread.join(timeout=3)
        for subscription in self.subscriptions:self.node.destroy_subscription(subscription)

    def report(self):return {'acks':self.acks,'connections':self.connections,'last_error':self.last_error,'last_ack':self.last_ack,'transport':'bounded_command_wss'}
