"""Cookie authentication for the read-only RViz relay; no saved passwords."""
import getpass
import http.cookiejar
import json
import urllib.request
from urllib.parse import urlparse

def login(api_url,username,password=None):
    endpoint=urlparse(api_url)
    if endpoint.scheme!='https' and not (endpoint.scheme=='http' and endpoint.hostname in ('127.0.0.1','localhost','::1','host.docker.internal')):
        raise ValueError('Use an HTTPS API or a loopback SSH tunnel')
    jar=http.cookiejar.CookieJar()
    opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    value=json.dumps({'username':username,'password':password or getpass.getpass('Beta password: ')}).encode()
    request=urllib.request.Request(api_url.rstrip('/')+'/auth/login',data=value,headers={'Content-Type':'application/json'})
    with opener.open(request,timeout=10) as response:
        result=json.load(response)
    if not result.get('user'):raise ValueError('Beta authentication failed')
    return '; '.join(cookie.name+'='+cookie.value for cookie in jar)
