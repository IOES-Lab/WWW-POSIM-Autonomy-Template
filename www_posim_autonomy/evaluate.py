"""One local action: queue server Gazebo, relay ROS, run local code, save score.

The algorithm stays on the participant PC. Passwords and login cookies never
enter command lines, saved settings, profiles, or submitted results.
"""
import argparse
import getpass
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import threading
import time
from urllib.parse import urlparse
from .connect import API
from .standalone import compatible


def stop_process(process):
    """Only stop the process group we created for this run."""
    if process is None or process.poll() is not None:return
    try:
        if os.name=='nt':process.send_signal(signal.CTRL_BREAK_EVENT)
        else:os.killpg(process.pid,signal.SIGINT)
        process.wait(timeout=5)
    except (OSError,subprocess.TimeoutExpired):
        if process.poll() is None:
            if os.name=='nt':process.terminate()
            else:os.killpg(process.pid,signal.SIGTERM)
            try:process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                if os.name=='nt':process.kill()
                else:os.killpg(process.pid,signal.SIGKILL)
                process.wait(timeout=3)


def start_process(command,**kwargs):
    options={'creationflags':subprocess.CREATE_NEW_PROCESS_GROUP} if os.name=='nt' else {'start_new_session':True}
    return subprocess.Popen(command,**options,**kwargs)


def evaluate(api,task,command,output,*,practice=False,seed=0,alias='Participant',
             job_id=None,stop=None,notify=print,queue_timeout=7200):
    """API can be a logged-in server client or an unauthenticated local API."""
    if not command or any(not isinstance(x,str) or not x for x in command):raise ValueError('Choose a local command and arguments.')
    if not re.fullmatch(r'[\w .-]{2,40}',alias):raise ValueError('Use a public alias, without email or punctuation.')
    stop=stop or threading.Event()
    manifest=api.call('/versions')
    if not compatible(manifest):raise RuntimeError('Update the installed client before evaluation.')
    enabled=api.call('/auth/me')['enabled']
    if not practice and not enabled:raise ValueError('Official evaluation requires an authenticated server.')
    catalog=api.call('/competition/catalog')
    definition=next((item for item in catalog['tasks'] if item['id']==task),None)
    if not definition:raise ValueError('Unknown task.')
    start=dict(catalog.get('evaluation_start') or dict(job_id='11f0df7a50b64019b7544199',spawn_latitude=35.07446,spawn_longitude=129.08468,depth_m=0,streaming=False))
    if job_id:start['job_id']=job_id
    start.update(robot_id=definition['robot'],control_mode='ros2',scenario='none',competition_task=task,
                 graded=not practice,competition_seed=seed if practice else 0)
    # All preflight checks happen before admission or world mutations.
    probe=subprocess.run([sys.executable,'-c','import rclpy; import rosidl_runtime_py; import geometry_msgs.msg'],capture_output=True)
    if probe.returncode:raise RuntimeError('Run Evaluation from a ROS2-enabled Python environment (the native ROS environment or the local simulator client container).')
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    queued=False;scoring=False;relay=None;controller=None;logs=[];result=None
    # Keep the student/relay DDS network independent of the local engine (73).
    env=dict(os.environ,ROS_DOMAIN_ID='76',ROS_AUTOMATIC_DISCOVERY_RANGE='LOCALHOST')
    try:
        if enabled:
            api.call('/beta/queue',start);queued=True
            notify('Queued. Waiting does not consume simulation time.')
            deadline=time.monotonic()+queue_timeout
            while True:
                if stop.is_set():raise InterruptedError('Cancelled while waiting.')
                status=api.call('/beta/status');request=status.get('request') or {}
                if request.get('status')=='active':break
                if request.get('status') not in ('queued','starting'):raise RuntimeError('Session ended: '+str(request.get('reason') or request.get('status')))
                if time.monotonic()>deadline:raise TimeoutError('Queue wait timed out.')
                notify('Queue position '+str(status.get('queue_position',0))+'; next slot estimate '+str(round(status.get('next_slot_seconds',0)))+'s')
                stop.wait(2)
        else:
            requested=api.call('/session/start',start)
        notify('Preparing native Gazebo and sensors.')
        deadline=time.monotonic()+180
        while True:
            if stop.is_set():raise InterruptedError('Cancelled during preparation.')
            session=api.call('/session')
            if session.get('status')=='running' and (session.get('competition') or {}).get('task')==task and (enabled or session.get('nonce')==requested.get('request_id')):break
            if time.monotonic()>deadline:raise TimeoutError('Gazebo world did not become ready.')
            stop.wait(.5)
        nonce=session['nonce'];profile=api.call('/rviz/profile')
        if profile.get('session_nonce')!=nonce or profile.get('control_mode')!='ros2':raise RuntimeError('Session changed before ROS connection.')
        endpoint=urlparse(api.url)
        origin=getattr(api,'origin',None) or endpoint._replace(path='',query='',fragment='').geturl()
        url=endpoint._replace(scheme='wss' if endpoint.scheme=='https' else 'ws',path='/ros',query='',fragment='').geturl()
        with tempfile.TemporaryDirectory(prefix='www-posim-evaluation-') as directory:
            private=Path(directory);path=private/'profile.json';path.write_text(json.dumps(profile));path.chmod(0o600)
            ready=private/'ready.json'
            log=(output/'relay.log').open('w');logs.append(log)
            relay=start_process([sys.executable,'-m','www_posim_autonomy.relay','--url',url,'--origin',origin,
                '--profile',str(path),'--control','--auth-stdin','--ready-file',str(ready),'--report',str(output/'relay-report.json')],
                stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,text=True,env=env)
            relay.stdin.write(json.dumps({'cookie':api.cookie() or None}));relay.stdin.close()
            deadline=time.monotonic()+30
            while not ready.exists():
                if stop.is_set():raise InterruptedError('Cancelled during connection.')
                if relay.poll() is not None:raise RuntimeError('ROS relay failed. See the local relay.log.')
                if time.monotonic()>deadline:raise TimeoutError('No native odometry reached the local ROS relay.')
                stop.wait(.2)
            if json.loads(ready.read_text()).get('session_nonce')!=nonce:raise RuntimeError('Relay belongs to another world.')
            deadline=time.monotonic()+45
            while True:
                if stop.is_set():raise InterruptedError('Cancelled before scoring.')
                control=api.call('/vehicle/external')
                if control.get('session_nonce')!=nonce:raise RuntimeError('World changed before control became ready.')
                if control.get('available'):break
                if time.monotonic()>deadline:raise TimeoutError('Native sensors and propulsion did not become ready.')
                stop.wait(.25)
            api.call('/competition/run/start',dict(session_nonce=nonce,display_name=alias,baseline=False));scoring=True
            log=(output/'algorithm.log').open('w');logs.append(log)
            # No shell parsing: the user's saved argument list is executed locally.
            controller=start_process(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
                env=dict(env,WWW_POSIM_PROFILE=str(path)))
            notify('Local algorithm running. Gazebo and official scoring stay on the server.' if not practice else 'Practice running. Local results do not enter the official leaderboard.')
            deadline=time.monotonic()+1900
            while True:
                if stop.is_set():raise InterruptedError('Cancelled by participant.')
                if relay.poll() is not None:raise RuntimeError('ROS relay disconnected.')
                value=api.call('/competition/run')
                if value.get('session_nonce')!=nonce:raise RuntimeError('Evaluation session changed.')
                if value.get('status')=='finished':
                    scoring=False
                    path='/competition/run/export'
                    if enabled:path+='?run_id='+str(value['run_id'])
                    result=api.call(path)
                    saved=output/'result.json';saved.write_text(json.dumps(result,indent=2)+'\n')
                    notify('Saved '+str(saved)+'; score '+str(result['result']['report']['score']))
                    break
                if controller.poll() not in (None,0) and value.get('status')=='running':raise RuntimeError('Local algorithm failed. See the local algorithm.log.')
                if time.monotonic()>deadline:raise TimeoutError('Evaluation exceeded the server wall-time limit.')
                stop.wait(.5)
    finally:
        stop_process(controller);stop_process(relay)
        for log in logs:log.close()
        if scoring:
            try:
                interrupted=api.call('/competition/run/stop',{})
                if interrupted.get('status')=='finished':
                    path='/competition/run/export'
                    if enabled:path+='?run_id='+str(interrupted['run_id'])
                    evidence=api.call(path)
                    (output/'interrupted-result.json').write_text(json.dumps(evidence,indent=2)+'\n')
                    notify('Interrupted run saved for diagnosis; it does not award an official score.')
            except Exception:notify('Interrupted evidence could not be exported; the server retains its run record.')
        if queued:
            try:api.call('/beta/release',{})
            except Exception:notify('Could not release the server slot; use End session on the web page. Its lease still expires automatically.')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server',required=True,help='Server API ending /api, or licensed local http://127.0.0.1:3300/api')
    parser.add_argument('--email');parser.add_argument('--task',required=True)
    parser.add_argument('--alias',default='Participant');parser.add_argument('--practice',action='store_true')
    parser.add_argument('--seed',type=int,default=0);parser.add_argument('--job-id')
    parser.add_argument('--output',type=Path,default=Path('evaluation-results'))
    parser.add_argument('--client-image',help='Run ROS and your algorithm in a PC-local client container; no host ROS needed')
    parser.add_argument('--project',type=Path,default=Path.cwd(),help='Code directory mounted in the local ROS client')
    parser.add_argument('command',nargs=argparse.REMAINDER,help='After --, the local algorithm command and arguments')
    args=parser.parse_args()
    api=API(args.server)
    if api.call('/auth/me')['enabled']:
        if not args.email:parser.error('--email is required for server evaluation')
        api.call('/auth/login',dict(username=args.email,password=getpass.getpass('Password: ')))
    command=args.command[1:] if args.command[:1]==['--'] else args.command
    try:
        options=dict(practice=args.practice,seed=args.seed,alias=args.alias,job_id=args.job_id)
        if args.client_image:
            from .client_container import evaluate_in_container
            evaluate_in_container(api,args.task,command,args.output,image=args.client_image,project=args.project,**options)
        else:evaluate(api,args.task,command,args.output,**options)
    except KeyboardInterrupt:print('Evaluation cancelled.',file=sys.stderr);raise SystemExit(130)
    except Exception as error:print(str(error),file=sys.stderr);raise SystemExit(1)

if __name__=='__main__':main()
