"""Cross-platform thin launcher; ROS/Gazebo stay in cached Docker containers."""
import argparse
from datetime import datetime,timezone
import getpass
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
import uuid
import webbrowser
import urllib.request
from . import __version__
from .connect import API

PROTOCOL=2
def compatible(manifest):
    parse=lambda s:tuple(int(v) for v in s.split('.'))
    return manifest['protocol']==PROTOCOL and parse(__version__)>=parse(manifest['minimum_client'])

def runtime_manifest(timeout=40):
    deadline=time.monotonic()+timeout
    while True:
        try:
            with urllib.request.urlopen('http://127.0.0.1:3300/api/versions',timeout=3) as response:return json.load(response)
        except (OSError,ValueError):
            if time.monotonic()>=deadline:raise RuntimeError('Local runtime did not become ready.')
            time.sleep(.5)

def runtime_matches(local,server):
    return all(server.get(k) is not None and local.get(k)==server.get(k) for k in ('version','protocol','rules_version','adapter_sha256'))

def compose(directory,action,gpu=False):
    files=['-f',str(Path(__file__).with_name('standalone-compose.yaml'))]
    if gpu:files+=['-f',str(Path(__file__).with_name('standalone-gpu.yaml'))]
    env=dict(os.environ,WWW_POSIM_DATA=str(directory/'data'))
    return subprocess.run(['docker','compose','--project-name','www-posim-standalone',*files,*action],env=env,check=True)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--server',required=True,help='HTTPS server API, ending in /api')
    parser.add_argument('--email',required=True);parser.add_argument('--directory',type=Path,default=Path.home()/'.www-posim')
    parser.add_argument('--gpu',action='store_true');parser.add_argument('--runtime-image');parser.add_argument('--web-image');parser.add_argument('--check-only',action='store_true')
    args=parser.parse_args()
    if not shutil.which('docker'):parser.error('Install official Docker Engine/Desktop; Windows needs WSL2.')
    if args.gpu and platform.system()=='Darwin':parser.error('Mac Docker cannot expose the Apple GPU to Gazebo; omit --gpu.')
    if args.runtime_image:os.environ['WWW_POSIM_RUNTIME_IMAGE']=args.runtime_image
    if args.web_image:os.environ['WWW_POSIM_WEB_IMAGE']=args.web_image
    api=API(args.server,args.email,getpass.getpass('WWW-POSIM password: '))
    manifest=api.call('/versions')
    if not compatible(manifest):parser.error('Client update required. Upgrade the template source package to the server minimum version.')
    usage=api.call('/account/usage');print(json.dumps({'version':__version__,'usage':usage},indent=2))
    if args.check_only:return
    if not os.getenv('WWW_POSIM_RUNTIME_IMAGE') or not os.getenv('WWW_POSIM_WEB_IMAGE'):
        parser.error('A published runtime is not configured yet. Use administrator-provided native image tags or the locally built images via --runtime-image/--web-image.')
    folder=args.directory.resolve();(folder/'data').mkdir(parents=True,exist_ok=True)
    device_file=folder/'device-id';device=device_file.read_text() if device_file.exists() else uuid.uuid4().hex;device_file.write_text(device)
    for name in ('nginx.conf',):shutil.copyfile(Path(__file__).with_name(name),folder/name)
    os.environ['WWW_POSIM_HOME']=str(folder)
    state=folder/'data'/'license.json';lease=None;renew_at=0.;version_at=time.monotonic()+300
    try:
        state.unlink(missing_ok=True)
        compose(folder,['up','-d'],args.gpu)
        local=runtime_manifest()
        if not runtime_matches(local,manifest):raise RuntimeError('Runtime update required. Use simulator image tags matching the server; unchanged Docker layers are reused.')
        webbrowser.open('http://127.0.0.1:3300')
        print('Simulator: http://127.0.0.1:3300. Keep this launcher running. Ctrl+C stops it.')
        while True:
            now=time.monotonic()
            session_file=folder/'data'/'session.json';request_file=folder/'data'/'session-request.json'
            session=json.loads(session_file.read_text()) if session_file.exists() else {}
            requested=json.loads(request_file.read_text()) if request_file.exists() else {}
            running=session.get('kind')=='generated' and session.get('status') in ('starting','running')
            pending=requested.get('kind')=='generated' and requested.get('nonce')!=session.get('nonce') and session.get('kind')=='idle'
            if now>=version_at:
                manifest=api.call('/versions')
                if not compatible(manifest) or not runtime_matches(local,manifest):raise RuntimeError('Mandatory client/runtime update; restart after upgrading.')
                version_at=now+300
            if running or pending:
                if not lease:
                    lease=api.call('/license/start',{'device':device,'client_version':__version__,'protocol':PROTOCOL});renew_at=now+20
                elif now>=renew_at:lease.update(api.call('/license/heartbeat',{'token':lease['token']}));renew_at=now+20
                expiry=datetime.fromisoformat(lease['expires_at']).timestamp()
                server_time=datetime.fromisoformat(lease['server_time']).timestamp()
                # Use server-granted duration; do not assume device clock equals server clock.
                if now<renew_at:
                    remaining=max(0,expiry-server_time-(20-(renew_at-now)))
                    temp=state.with_suffix('.tmp');temp.write_text(json.dumps({'expires_at':time.time()+remaining,'client_version':__version__}));temp.replace(state)
            elif lease:
                api.call('/license/end',{'token':lease['token']});lease=None;state.unlink(missing_ok=True)
            time.sleep(1)
    except KeyboardInterrupt:pass
    except Exception as e:print('Stopping local runtime: '+str(e),file=sys.stderr)
    finally:
        state.unlink(missing_ok=True)
        try:
            if lease:api.call('/license/end',{'token':lease['token']})
        except Exception:pass
        compose(folder,['down'],args.gpu)

if __name__=='__main__':main()
