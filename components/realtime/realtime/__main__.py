import argparse, sys

from . import RealtimeServer

def do_echo(conn, **kwargs):
    print conn
    print kwargs
    return {'cool': 'dude'}

def main():
    parser = argparse.ArgumentParser(description='Camaste! Realtime Component')
    parser.add_argument('--http-port', type=int, default=8081, nargs=1, help='Port to listen on')
    parser.add_argument('--redis-host', type=str, default="localhost", nargs=1, help='Redis Server port')
    parser.add_argument('--redis-port', type=int, default=6379, nargs=1, help='Redis Server port')

    args = parser.parse_args()
    if not RealtimeServer.checkargs(args):
        return 1

    app = RealtimeServer(args)
    app.register('echo', do_echo)
    app.run()
    return 0
    
if __name__ == '__main__':
    sys.exit(main())