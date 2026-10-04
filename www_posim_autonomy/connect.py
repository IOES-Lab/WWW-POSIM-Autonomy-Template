"""Download a fresh session profile, then relay approved ROS messages over WSS."""
import argparse
import getpass
import http.cookiejar
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request
from urllib.parse import urlparse

class API:
    def __init__(self,url,email,password):
        p=urlparse(url)
        if p.scheme!='https' and not (p.scheme=='http' and p.hostname in ('localhost','127.0.0.1','host.docker.internal')):raise ValueError('Use HTTPS, or a local simulator/tunnel.')
        self.url=url.rstrip('/');self.jar=http.cookiejar.CookieJar()
        self.opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        self.call('/auth/login',{'username':email,'password':password})
    def call(self,path,body=None):
        csrf=next((c.value for c in self.jar if c.name=='wwos_csrf'),'')
        req=urllib.request.Request(self.url+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json','X-WWOS-CSRF':csrf})
        with self.opener.open(req,timeout=15) as r:return json.load(r)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--server',required=True);parser.add_argument('--email',required=True)
    parser.add_argument('--profile',default='profile.json');parser.add_argument('--control',action='store_true');args=parser.parse_args()
    api=API(args.server,args.email,getpass.getpass('Password: '));profile=api.call('/rviz/profile')
    path=Path(args.profile);path.write_text(json.dumps(profile,indent=2));path.chmod(0o600)
    endpoint=urlparse(args.server);origin=endpoint._replace(path='',query='',fragment='').geturl()
    url=endpoint._replace(scheme='wss' if endpoint.scheme=='https' else 'ws',path='/ros',query='',fragment='').geturl()
    # Relay prompts separately; passwords are never put in process arguments or files.
    command=[sys.executable,'-m','www_posim_autonomy.relay','--url',url,'--api-url',args.server,'--username',args.email,'--origin',origin,'--profile',str(path)]
    if args.control:command+=['--control']
    raise SystemExit(subprocess.call(command))

if __name__=='__main__':main()
