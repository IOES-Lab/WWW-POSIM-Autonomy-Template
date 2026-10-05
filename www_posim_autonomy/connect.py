"""Download a fresh session profile, then relay approved ROS messages over WSS."""
import argparse
import getpass
import http.cookiejar
import json
import os
from pathlib import Path
import subprocess
import signal
import sys
import urllib.request
from urllib.parse import urlparse

class SameOriginRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        before,after=urlparse(req.full_url),urlparse(newurl)
        if (before.scheme,before.hostname,before.port)!=(after.scheme,after.hostname,after.port):
            raise ValueError('Cross-origin API redirects are not allowed.')
        return super().redirect_request(req,fp,code,msg,headers,newurl)

class API:
    def __init__(self,url,email=None,password=None):
        p=urlparse(url)
        if p.scheme!='https' and not (p.scheme=='http' and p.hostname in ('localhost','127.0.0.1','::1','host.docker.internal')):raise ValueError('Use HTTPS, or a local simulator/tunnel.')
        self.url=url.rstrip('/');self.jar=http.cookiejar.CookieJar();self._cookie=None
        self.opener=urllib.request.build_opener(SameOriginRedirect(),urllib.request.HTTPCookieProcessor(self.jar))
        if email is not None:self.call('/auth/login',{'username':email,'password':password})
    def cookie(self):
        return self._cookie or '; '.join(c.name+'='+c.value for c in self.jar)
    def use_cookie(self,value):
        if value and (not isinstance(value,str) or len(value)>4096 or any(c in value for c in '\r\n')):raise ValueError('Invalid authentication input.')
        self._cookie=value
    def call(self,path,body=None):
        csrf=next((item.split('=',1)[1] for item in self.cookie().split('; ') if item.startswith('wwos_csrf=')),'')
        headers={'Content-Type':'application/json','X-WWOS-CSRF':csrf}
        if self._cookie:headers['Cookie']=self._cookie
        req=urllib.request.Request(self.url+path,data=json.dumps(body).encode() if body is not None else None,headers=headers)
        with self.opener.open(req,timeout=15) as r:return json.load(r)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--server',required=True);parser.add_argument('--email')
    parser.add_argument('--local',action='store_true',help='Use a licensed installed simulator without another web login')
    parser.add_argument('--profile',default='profile.json');parser.add_argument('--rviz-config',default='session.rviz')
    parser.add_argument('--control',action='store_true');args=parser.parse_args()
    endpoint=urlparse(args.server)
    if endpoint.username or endpoint.password or endpoint.query or endpoint.fragment or endpoint.path.rstrip('/')!='/api':
        parser.error('Use an API URL ending in /api without credentials, query or fragment')
    if args.local:
        if args.email or endpoint.hostname not in ('localhost','127.0.0.1','::1','host.docker.internal'):
            parser.error('--local requires your installed simulator on a local address, without --email')
    elif not args.email:parser.error('--email is required for a web session')
    api=API(args.server,None if args.local else args.email,None if args.local else getpass.getpass('Password: '));profile=api.call('/rviz/profile')
    if args.control and (profile.get('control_mode')!='ros2' or not profile.get('command_topics')):
        parser.error('Start a ROS2 direct-control world before using --control')
    path=Path(args.profile);path.write_text(json.dumps(profile,indent=2));path.chmod(0o600)
    endpoint=urlparse(args.server);origin=endpoint._replace(path='',query='',fragment='').geturl()
    url=endpoint._replace(scheme='wss' if endpoint.scheme=='https' else 'ws',path='/ros',query='',fragment='').geturl()
    # Private stdin transfers only the short-lived login cookie. No second
    # password prompt, credential file or secret command-line argument.
    command=[sys.executable,'-m','www_posim_autonomy.relay','--url',url,'--auth-stdin','--origin',origin,'--profile',str(path),'--rviz-config',args.rviz_config]
    if args.control:command+=['--control']
    process=subprocess.Popen(command,stdin=subprocess.PIPE,text=True)
    process.stdin.write(json.dumps({'cookie':api.cookie()}));process.stdin.close()
    try:code=process.wait()
    except KeyboardInterrupt:
        if process.poll() is None:process.send_signal(signal.SIGINT)
        try:process.wait(timeout=7)
        except subprocess.TimeoutExpired:process.kill();process.wait()
        code=130
    raise SystemExit(code)

if __name__=='__main__':main()
