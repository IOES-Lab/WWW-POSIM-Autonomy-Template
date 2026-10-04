"""ROS2 telemetry relay, with explicit optional bounded command forwarding."""
import argparse
import base64
import json
import re
import math
import yaml
from pathlib import Path
import signal
import threading
import time
from urllib.parse import urlparse
import websocket
from .beta_login import login
import rclpy
from rclpy.signals import SignalHandlerOptions
from rclpy.qos import QoSProfile, DurabilityPolicy
from rosidl_runtime_py.utilities import get_message
from rosidl_runtime_py.set_message import set_message_fields
from geometry_msgs.msg import TransformStamped
from tf2_msgs.msg import TFMessage

parser=argparse.ArgumentParser()
parser.add_argument('--url',default='ws://127.0.0.1:19090')
parser.add_argument('--profile',type=Path,required=True,help='Session profile downloaded by www-posim-connect')
parser.add_argument('--report',type=Path)
parser.add_argument('--rviz-config',type=Path,help='Write a session-specific RViz view before connecting')
parser.add_argument('--api-url',help='Beta API, e.g. http://127.0.0.1:19090/api through SSH')
parser.add_argument('--username',help='Beta username; password is prompted locally')
parser.add_argument('--origin',default='http://127.0.0.1:3000',help='Origin allowed by the server WebSocket gateway')
parser.add_argument('--control',action='store_true',help='Forward the profile command topics to the direct propulsion gateway')
args=parser.parse_args()
url=urlparse(args.url)
if url.scheme!='wss' and not (url.scheme=='ws' and url.hostname in ('127.0.0.1','localhost','::1','host.docker.internal')):
    parser.error('Use a loopback SSH tunnel, or a TLS wss endpoint with certificate verification.')
profile=json.loads(args.profile.read_text())
if bool(args.api_url)!=bool(args.username):parser.error('--api-url and --username must be used together')
cookie=login(args.api_url,args.username) if args.api_url else None
if profile.get('remote_publish') is not False:parser.error('A read-only profile is required')
entries=profile['topics']
if not entries or len(entries)>(16 if cookie else 32) or len({e['name'] for e in entries})!=len(entries):parser.error('Invalid topic list')
if args.rviz_config:
    config=yaml.safe_load(Path(__file__).with_name('wwos.rviz').read_text())
    odom=next((entry['name'] for entry in entries if entry['type']=='nav_msgs/msg/Odometry'),None)
    if odom:
        display=config['Visualization Manager']['Displays'][1]
        display['Name']='Robot odometry';display['Topic']['Value']=odom
    point=profile.get('initial_position',{'x':0,'y':0,'z':0})
    if not all(isinstance(point.get(k),(int,float)) and math.isfinite(point[k]) and abs(point[k])<=20000 for k in ('x','y','z')):parser.error('Invalid initial position')
    view=config['Visualization Manager']['Views']['Current']
    view['Target Frame']='wwos_remote_robot'
    view['Focal Point']={'X':0,'Y':0,'Z':0}
    grid=config['Visualization Manager']['Displays'][0]
    grid.update({'Cell Size':10,'Plane Cell Count':200})
    args.rviz_config.write_text(yaml.safe_dump(config,sort_keys=False))
rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
node=rclpy.create_node('wwos_remote_rviz_relay')
publishers={}
for entry in entries:
    cls=get_message(entry['type'])
    qos=QoSProfile(depth=10,durability=DurabilityPolicy.TRANSIENT_LOCAL if entry.get('transient') else DurabilityPolicy.VOLATILE)
    publishers[entry['name']]=(cls,node.create_publisher(cls,entry['name'],qos))
stop=threading.Event();counts={};errors={};connection_count=0
derived_tf=publishers['/tf'][1] if '/tf' in publishers else node.create_publisher(TFMessage,'/tf',10)
derived_pose_count=0
for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,lambda *_:stop.set())

def normalize_fields(message, fields):
    """rosbridge serializes unknown floating-point values (NaN) as JSON null."""
    types=message.get_fields_and_field_types()
    result={}
    for name,value in fields.items():
        field_type=types.get(name,'')
        current=getattr(message,name)
        if isinstance(value,dict):value=normalize_fields(current,value)
        elif value is None and field_type in ('float','double','float32','float64'):value=float('nan')
        elif isinstance(value,list) and re.search(r'float|double',field_type):value=[float('nan') if item is None else item for item in value]
        result[name]=value
    return result

def worker():
    global connection_count,derived_pose_count
    while not stop.is_set():
        ws=None
        try:
            ws=websocket.create_connection(args.url,timeout=2,origin=args.origin,**({'cookie':cookie} if cookie else {}))
            connection_count+=1
            for entry in entries:
                ws.send(json.dumps({'op':'subscribe','id':entry['name'],'topic':entry['name'],'type':entry['type'],'throttle_rate':100 if entry['name']!='/clock' else 20,'queue_length':1}))
            while not stop.is_set():
                try:raw=ws.recv()
                except websocket.WebSocketTimeoutException:continue
                if not raw:break
                if len(raw)>2_000_000:raise ValueError('message_limit')
                value=json.loads(raw)
                name=value.get('topic')
                if value.get('op')!='publish' or name not in publishers:continue
                try:
                    cls,publisher=publishers[name];message=cls();fields=value['msg']
                    # rosbridge represents uint8[] image/point-cloud bytes as base64.
                    if 'data' in fields and isinstance(fields['data'],str):fields=dict(fields,data=list(base64.b64decode(fields['data'],validate=True)))
                    set_message_fields(message,normalize_fields(message,fields));publisher.publish(message);counts[name]=counts.get(name,0)+1
                    if cls.__module__.startswith('nav_msgs.msg._odometry'):
                        # A client-local alias, derived only from received native
                        # odometry, keeps RViz on the robot without competing
                        # with a robot's own base_link TF authority.
                        pose=message.pose.pose
                        values=[getattr(pose.position,k) for k in ('x','y','z')]+[getattr(pose.orientation,k) for k in ('x','y','z','w')]
                        if not message.header.frame_id or not all(math.isfinite(v) for v in values):raise ValueError('invalid_odometry_transform')
                        transform=TransformStamped();transform.header=message.header;transform.child_frame_id='wwos_remote_robot'
                        transform.transform.translation.x=pose.position.x;transform.transform.translation.y=pose.position.y;transform.transform.translation.z=pose.position.z
                        transform.transform.rotation=pose.orientation
                        derived_tf.publish(TFMessage(transforms=[transform]));derived_pose_count+=1
                except Exception as e:errors[name]=str(e)
        except Exception as e:
            if not stop.is_set():node.get_logger().warning('Remote connection unavailable; reconnecting: '+str(e))
        finally:
            if ws:
                try:ws.close()
                except Exception:pass
        stop.wait(2)

thread=threading.Thread(target=worker,daemon=True);thread.start()
control=None
if args.control:
    from .control_client import ControlClient
    control=ControlClient(node,profile,args.url,cookie,args.origin)
try:
    while not stop.is_set():rclpy.spin_once(node,timeout_sec=.2)
finally:
    stop.set();thread.join(timeout=5)
    if control:control.close()
    if args.report:args.report.write_text(json.dumps({'messages':counts,'errors':errors,'connections':connection_count,'remote_publish':False,'command_forwarding':control.report() if control else None,'odometry_derived_local_tf':derived_pose_count},indent=2))
    node.destroy_node();rclpy.shutdown()
