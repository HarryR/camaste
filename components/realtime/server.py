#!/usr/bin/env python
from __future__ import print_function

import sys, argparse, json
import uuid
from random import choice

# Core Tornado stuff
try:
    import tornado.httpserver
    import tornado.web
    import tornado.websocket
    import tornado.ioloop
    import tornado.gen
except:
    print('Please install tornado to run')
    exit(1)

# Redis
try:
    import redis
    import tornadoredis
    import tornadoredis.pubsub
except:
    print('Please install tornadoredis to run')
    exit(1)

# SockJS
try:
    import sockjs.tornado
except:
    print('Please install the sockjs-tornado package to run')
    exit(1)

import logging

LOGGER = logging.getLogger().setLevel(logging.INFO)


class MessageHandler(sockjs.tornado.SockJSConnection):
    def __init__(self, app, session):
        super(MessageHandler, self).__init__(session)
        self.app = app
        self.redis = app.redis
        self.sub = app.subscriber
        self.cmds = {
            'echo': True
        }

    """
    SockJS connection handler.

    Note that there are no "on message" handlers - SockJSSubscriber class
    calls SockJSConnection.broadcast method to transfer messages
    to subscribed clients.
    """
    def _enter_leave_notification(self, msg_type):
        broadcasters = list(self.sub.subscribers['broadcast_channel'].keys())
        message = json.dumps({'type': msg_type,
                              'user': self.user_id,
                              'msg': '',
                              'user_list': [{'id': b.user_id,
                                             'name': b.user_name}
                                            for b in broadcasters]})
        if broadcasters:
            broadcasters[0].broadcast(broadcasters, message)

    def ok(self, token, response):
        """
        Respond successfully to the message
        """
        assert response is not None
        return self._respond(token, 1, response)

    def error(self, token, response=None):
        """
        Respond with an error to the message
        """
        return self._respond(token, 0, response)

    def event(self, name, data):
        return self._respond(name, 1, data)

    def _respond(self, token, is_ok=1, response=None):
        """
        Send 'realtime' formatted response back to client
        """
        if response is None:
            response = {}
        response['id'] = token
        response['_'] = is_ok
        response = json.dumps(response)
        print("SENDING RESPONSE", response)
        self.send(response)

    def on_message(self, raw_msg):
        # Invalid packets are straight up ignored
        print("RAW MSG", raw_msg)
        try:
            msg = json.loads(raw_msg)
        except ValueError:            
            print("Error: json parse error")
            return
        if not isinstance(msg, dict):
            print(type(msg))
            print("Error: message not dict")
            return        
        if len(msg) != 3 or 'id' not in msg or 'call' not in msg or 'args' not in msg:            
            print("Error: bad params in message dict")
            return            
        if not isinstance(msg['id'], (str,unicode)):
            print(type(msg['id']))
            print("Error: invalid ID")
            return
        if not isinstance(msg['args'], (dict,)):
            self.error(msg['id'], {'args': 'Invalid'})
            return
        if msg['call'] not in self.cmds:
            self.error(msg['id'], {'call': 'Unknown'})
            return
        method = None
        try:        
            method = getattr(self, 'do_' + msg['call'])
        except AttributeError:
            self.error(msg['id'], {'call': 'Unimplemented?'})
            return
        try:
            args = msg['args']
            response = method(**args)            
            self.ok(msg['id'], response)
        except:
            # XXX: gotta log exception somewhere?
            self.error(msg['id'], {'call': 'Server Error'})

    def do_echo(self, *args, **kwargs):
        print("ECHO: ----")
        print("  args", args)
        print("  kwargs", kwargs)
        print("-----")
        print("")
        return {
            'args': args,
            'kwargs': kwargs
        }

    def on_open(self, request):
        """
        # Generate a user ID and name to demonstrate 'private' channels
        self.user_id = str(uuid.uuid4())[:5]
        self.user_name = (
            choice(['John', 'Will', 'Bill', 'Ron', 'Sam', 'Pete']) +
            ' ' +
            choice(['Smith', 'Doe', 'Strong', 'Long', 'Tall', 'Small']))
        # Send it to user
        self._send_message('uid', self.user_name, self.user_id)
        # Subscribe to 'broadcast' and 'private' message channels
        self.sub.subscribe(['broadcast_channel', 'private.{}'.format(self.user_id)], self)
        # Send the 'user enters the chat' notification
        self._enter_leave_notification('enters')
        """
        pass

    def on_close(self):
        """
        # TODO: cleanup everything
        self.sub.subscriber.unsubscribe('private.{}'.format(self.user_id), self)
        self.sub.subscriber.unsubscribe('broadcast_channel', self)
        # Send the 'user leaves the chat' notification
        self._enter_leave_notification('leaves')
        """
        pass

class IndexHandler(tornado.web.RequestHandler):
    """Regular HTTP handler to serve the chatroom page"""
    def get(self):
        self.render('index.html')

def getarg(wut):
    return wut[0] if isinstance(wut, list) else wut

class RealtimeApp(object):
    def __init__(self, args):
        self.args = args
        conf = self.conf = {
            'http_port': getarg(args.http_port),
            'redis_host': getarg(args.redis_host),
            'redis_port': getarg(args.redis_port),
        }

        self.redis = tornadoredis.Client(conf['redis_host'], conf['redis_port'])
        self.subscriber = tornadoredis.pubsub.SockJSSubscriber(self.redis)

        self.sockjs_router = sockjs.tornado.SockJSRouter(lambda x: MessageHandler(self, x), '/realtime')
        self.tornado_app = tornado.web.Application( [(r"/", IndexHandler)] + self.sockjs_router.urls)
        self.http_server = tornado.httpserver.HTTPServer(self.tornado_app)

    @staticmethod
    def checkargs(args):
        http_port = getarg(args.http_port)
        if http_port < 1 or http_port >= 0xffff:
            print("Error: Invalid HTTP port:", http_port)
            return False
        redis_port = getarg(args.redis_port)
        if redis_port < 1 or redis_port >= 0xffff:
            print("Error: Invalid Redis port:", redis_port)
            return False
        return True

    def run(self):
        self.http_server.listen(self.conf['http_port'])
        print('Camaste! Realtime is running at 0.0.0.0:%d\n' % (self.conf['http_port'],))
        tornado.ioloop.IOLoop.instance().start()

def main():
    parser = argparse.ArgumentParser(description='Camaste! Realtime Component')
    parser.add_argument('--http-port', type=int, default=8081, nargs=1, help='Port to listen on')
    parser.add_argument('--redis-host', type=str, default="localhost", nargs=1, help='Redis Server port')
    parser.add_argument('--redis-port', type=int, default=6379, nargs=1, help='Redis Server port')

    args = parser.parse_args()
    if not RealtimeApp.checkargs(args):
        return 1

    app = RealtimeApp(args)
    app.run()
    return 0
    
    
if __name__ == '__main__':
    sys.exit(main())