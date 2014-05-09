import argparse, sys, re

import logging
import logging.config
from . import RealtimeServer
from .apps import ChatApp

def test_echo(conn, **kwargs):
    return kwargs


def is_valid_hostname(hostname):
    if len(hostname) > 255:
        return False
    if hostname[-1] == ".":
        hostname = hostname[:-1] # strip exactly one dot from the right, if present
    allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    return all(allowed.match(x) for x in hostname.split("."))


class HostnameAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if len(values) > 1:
            raise argparse.ArgumentError(self, "can only accept 1 hostname")
        value = values[0]
        if not is_valid_hostname(value):
            raise argparse.ArgumentError(self, "invalid hostnaem or ip")
        setattr(namespace, self.dest, value)

class TcpIpPortAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):        
        if len(values) > 1:
            raise argparse.ArgumentError(self, "can only accept 1 port")
        try:
            value = int(values[0])
        except:
            raise argparse.ArgumentError(self, "must be valid TCP/IP port")
        if value < 1 or value >= 0xFFFF:
            raise argparse.ArgumentError(self, "out of range for TCP/IP port")
        setattr(namespace, self.dest, value)


def main():
    parser = argparse.ArgumentParser(description='Camaste! Realtime Component')
    parser.add_argument('--logging', type=argparse.FileType('r'), help='Python logging.conf', metavar='CONF_FILE')
    parser.add_argument('--http-host', type=str, action=HostnameAction, default='0.0.0.0', nargs=1, metavar='HOST', help='Bind Host for HTTP server')
    parser.add_argument('--http-port', type=int, action=TcpIpPortAction, default=8081, nargs=1, metavar='PORT', help='Bind Port for HTTP server')
    parser.add_argument('--redis-host', type=str, action=HostnameAction, default='localhost', nargs=1, metavar='HOST', help='Redis Server port')
    parser.add_argument('--redis-port', type=int, action=TcpIpPortAction, default=6379, nargs=1, metavar='PORT', help='Redis Server port')

    args = parser.parse_args().__dict__

    if args['logging'] is not None:
        logging.config.fileConfig(args['logging'])

    server = RealtimeServer(args)
    ChatApp(server)
    server.register('test.echo', test_echo)
    server.run()
    return 0
    
if __name__ == '__main__':
    sys.exit(main())