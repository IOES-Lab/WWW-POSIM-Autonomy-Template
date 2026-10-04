"""Desktop/package entry point. The simulator engine is installed separately."""
import sys
from . import __version__

def main():
    args=sys.argv[1:]
    if args==['--version']:
        print('WWW-POSIM '+__version__);return
    action=args.pop(0) if args and args[0] in ('run','evaluate','evaluation') else ('evaluation' if not args else 'run')
    sys.argv=[sys.argv[0],*args]
    if action=='evaluation':
        from .evaluation_app import main as execute
    elif action=='evaluate':
        from .evaluate import main as execute
    else:
        from .standalone import main as execute
    execute()

if __name__=='__main__':main()
