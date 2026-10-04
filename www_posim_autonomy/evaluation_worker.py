"""Private stdin entry point for the PC-local ROS client container."""
import json
import signal
import sys
import threading
from .connect import API
from .evaluate import evaluate

def main():
    data=json.load(sys.stdin)
    api=API(data.pop('server'));api.use_cookie(data.pop('cookie'));api.origin=data.pop('origin')
    cancel=threading.Event()
    for name in (signal.SIGTERM,signal.SIGINT):signal.signal(name,lambda *_:cancel.set())
    try:
        evaluate(api,**data,stop=cancel,notify=lambda line:print(line,flush=True))
    except Exception as error:print(str(error),file=sys.stderr);raise SystemExit(1)

if __name__=='__main__':main()
