from __future__ import print_function
__all__ = ['RealtimeServer', 'MessageHandler']

import json, logging

# Core Tornado stuff
try:
    import tornado.httpserver
    import tornado.web
    import tornado.websocket
    import tornado.ioloop
    import tornado.gen
except:
    print('Please install: tornado')
    exit(1)

# Redis
try:
    import redis
    import tornadoredis
    import tornadoredis.pubsub
except:
    print('Please install: tornadoredis')
    exit(1)

# SockJS
try:
    import sockjs.tornado
except:
    print('Please install: sockjs-tornado')
    exit(1)

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)






def getarg(wut):
    """
    Used with argparse because sometimes it returns a single value
    sometimes a list... wtf? I prefere optparse
    """
    return wut[0] if isinstance(wut, list) else wut







class MessageHandler(sockjs.tornado.SockJSConnection):
    def __init__(self, app, session):
        super(MessageHandler, self).__init__(session)
        self._app = app

    def ok(self, token, response):
        """
        Respond successfully to the message
        """
        assert response is not None
        self._respond(token, 1, response)

    def error(self, token, response=None):
        """
        Respond with an error to the message
        """
        self._respond(token, 0, response)

    def event(self, name, data):
        self._respond(name, 1, data)

    def _respond(self, token, is_ok=1, response=None):
        """
        Send 'realtime' formatted response back to client
        """
        if response is None:
            response = {}
        response['id'] = token
        response['_'] = is_ok
        try:
            response = json.dumps(response)
        except:
            LOGGER.exception("Failed to encode response")
        self.send(response)

    def _parse_msg(self, raw_msg):
        """
        Parses the raw JSON message and ensures it passes strict
        type checks
        """
        try:
            msg = json.loads(raw_msg)
        except ValueError:            
            LOGGER.debug("%s: _parse_msg: Could not json.loads(raw_msg)", self.conn_info.ip)
            return
        if not isinstance(msg, dict):
            LOGGER.debug("%s: _parse_msg: message is not dict", self.conn_info.ip)
            return        
        if len(msg) != 3 or 'id' not in msg or 'call' not in msg or 'args' not in msg:            
            LOGGER.debug("%s: _parse_msg: message doesnt have right keys", self.conn_info.ip)
            return            
        if not isinstance(msg['id'], (str,unicode)):
            LOGGER.debug("%s: _parse_msg: id is not string...", self.conn_info.ip)
            return
        if not isinstance(msg['args'], (dict,)):
            LOGGER.debug("%s: _parse_msg: args is not dict", self.conn_info.ip)
            return self.error(msg['id'], {'args': 'Invalid'})
        if len(msg['args']) > 20:
            LOGGER.debug("%s: _parse_msg: too many args", self.conn_info.ip)
            return self.error(msg['id'], {'args': 'Too Many'})       
        return msg

    def on_message(self, raw_msg):     
        """
        Handles a 
        """   
        msg = self._parse_msg(raw_msg)        
        if not msg:            
            return            
        if msg['call'] in self._app._cmds:
            method = self._app._cmds[msg['call']]
        else:
            LOGGER.debug("%s: on_message: unknown call '%s'", self.conn_info.ip, msg['call'])
            return self.error(msg['id'], {'call': 'Unknown'})
        try:
            args = msg['args']
            response = method(self, **args)            
            if response is not None:
                self.ok(msg['id'], response)
        except Exception as ex:
            LOGGER.exception("%s: on_message: exception on '%s' call", self.conn_info.ip, msg['call'])
            self.error(msg['id'], {'call': 'Server Error'})

    def on_open(self, conn_info):
        self.conn_info = conn_info

    def on_close(self):        
        pass



class RealtimeServer(object):
    def __init__(self, args):
        self.args = args
        conf = self.conf = {
            'http_port': getarg(args.http_port),
            'redis_host': getarg(args.redis_host),
            'redis_port': getarg(args.redis_port),
        }

        self.redis = tornadoredis.Client(conf['redis_host'], conf['redis_port'])
        self.subscriber = tornadoredis.pubsub.SockJSSubscriber(self.redis)

        self.sockjs_router = sockjs.tornado.SockJSRouter(self.make_request, '/realtime')
        self.tornado_app = tornado.web.Application(self.sockjs_router.urls)
        self.http_server = tornado.httpserver.HTTPServer(self.tornado_app)

        self._cmds = {}

    def register(self, cmd, callback):
        self._cmds[cmd] = callback

    def make_request(self, session):
        return MessageHandler(self, session)        

    @staticmethod
    def checkargs(args):
        http_port = getarg(args.http_port)
        if http_port < 1 or http_port >= 0xffff:
            LOGGER.critical("Error: Invalid HTTP port: %d", http_port)
            return False
        redis_port = getarg(args.redis_port)
        if redis_port < 1 or redis_port >= 0xffff:
            LOGGER.critical("Error: Invalid Redis port: %d", redis_port)
            return False
        return True

    def run(self):
        self.http_server.listen(self.conf['http_port'])
        LOGGER.info('Camaste! Realtime is running at 0.0.0.0:%d', self.conf['http_port'])
        tornado.ioloop.IOLoop.instance().start()


