__all__ = ['RealtimeServer', 'MessageHandler']

import json, logging

from tornado import stack_context
import tornado.httpserver
import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.gen

import tornadoredis
from tornadoredis.client import reply_pubsub_message

import sockjs.tornado

LOGGER = logging.getLogger()




"""
.d88888b           dP                                  oo dP                         
88.    "'          88                                     88                         
`Y88888b. dP    dP 88d888b. .d8888b. .d8888b. 88d888b. dP 88d888b. .d8888b. 88d888b. 
      `8b 88    88 88'  `88 Y8ooooo. 88'  `"" 88'  `88 88 88'  `88 88ooood8 88'  `88 
d8'   .8P 88.  .88 88.  .88       88 88.  ... 88       88 88.  .88 88.  ... 88       
 Y88888P  `88888P' 88Y8888' `88888P' `88888P' dP       dP 88Y8888' `88888P' dP       
"""
class RedisSubscriber(object):
    """
    Multiplexes subscriptions while using only a single Redis client.
    """
    def __init__(self, tornado_redis_client):
        self.redis = tornado_redis_client
        self.subs = {}
        self.extra_debug = False


    def _on_message(self, msg):
        if not msg:
            return
        if msg.kind == 'disconnect':
            self.close()
        else:
            if msg.body is not None:
                # XXX: handle ValueError...
                msg.body = json.loads(msg.body)
            if isinstance(msg.channel, (set,list,tuple)):
                channels = msg.channel
            else:
                channels = set([msg.channel])
            for channel in channels:
                if channel in self.subs:
                    msg.channel = channel
                    for obj, callback in self.subs[msg.channel].items():
                        callback(obj, msg)


    def close(self):
        for channel in self.subs.keys():
            self.redis.unsubscribe(channel)
        self.subs = {}


    def _publish_channel(self, channel, msg, json_encoded_msg):
        """
        Send a message to a channel.
        All local subscribers of the channel will get sent the message
        without going through Redis.
        """
        if channel in self.subs:
            LOGGER.debug('_publish_channel: Redis publish channel:%s msg:%s', channel, json_encoded_msg)
            self.redis.publish(channel, json_encoded_msg)
            # Then dispatch the message to local clients, avoids JSON encoding
            # PUBLISH doesn't send the message to ourselves
            pubsub_msg = reply_pubsub_message(('message', channel, msg))
            for obj, callback in self.subs[channel].items():
                if self.extra_debug:
                    LOGGER.debug('_publish_channel: Internal publish channel:%s target:%s msg:%s', channel, obj, json_encoded_msg)
                callback(obj, pubsub_msg)

    def publish(self, channels, obj):
        """
        Pubishes the object to the channel.
        Object must be JSON encodable.
        """
        assert isinstance(obj, dict)
        json_encoded_obj = json.dumps(obj)
        if not isinstance(channels,(list,set,tuple)):
            channels = [channels]
        for channel in channels:
            assert isinstance(channel, (str,unicode))
            self._publish_channel(channel, obj, json_encoded_obj)


    def _subscribe_channel(self, channel, obj, callback):
        assert isinstance(channel, (str,unicode))
        no_subs_for_channel = channel not in self.subs
        if no_subs_for_channel:
            self.subs[channel] = {}
        callback = stack_context.wrap(callback)
        self.subs[channel][obj] = callback    
        if not self.redis.subscribed:
            if self.extra_debug:
                LOGGER.debug("_subscribe_channel: Redis subscription listener started")
            self.redis.listen(self._on_message)
        if no_subs_for_channel:
            if self.extra_debug:
                LOGGER.debug("_subscribe_channel: redis.subscribe('%s')", channel)
            self.redis.subscribe(channel)

    def subscribe(self, channels, obj, callback):
        """
        Subscribes an object to a channel
        """
        assert obj is not None
        assert callable(callback)
        if not isinstance(channels,(list,set,tuple)):
            channels = [channels]
        for channel in channels:
            self._subscribe_channel(channel, obj, callback)


    def _unsubscribe_channel(self, channel, obj):
        if channel not in self.subs:
            LOGGER.warn("_unsubscribe_channel: Trying to unsubscribe from unknown channel '%s'", channel)
            return
        if obj in self.subs[channel]:
            callback = self.subs[channel][obj]
            callback(obj, reply_pubsub_message(("unsubscribe", channel, None)))
            del self.subs[channel][obj]
            if len(self.subs[channel]) == 0:
                del self.subs[channel]
                self.redis.unsubscribe(channel)

    def unsubscribe(self, channels, obj):
        assert obj is not None
        if not isinstance(channels,(list,set,tuple)):
            channels = [channels]
        for channel in channels:
            assert isinstance(channel, (str,unicode))
            self._unsubscribe_channel(channel, obj)






"""
 88888888b                dP dP     dP                            
 88                       88 88     88                            
a88aaaa    88d888b. .d888b88 88     88 .d8888b. .d8888b. 88d888b. 
 88        88'  `88 88'  `88 88     88 Y8ooooo. 88ooood8 88'  `88 
 88        88    88 88.  .88 Y8.   .8P       88 88.  ... 88       
 88888888P dP    dP `88888P8 `Y88888P' `88888P' `88888P' dP       
"""
class EndUserConnection(sockjs.tornado.SockJSConnection):
    """
    This represents an end-users connection (via SockJS) to the `RealtimeServer`.
    It does protocol handing for the JSON based messages to & from the client-side JS code.
    It also provides utility methods for subscribing to Redis channels.
    """
    def __init__(self, app, session):
        super(EndUserConnection, self).__init__(session)
        self._app = app
        self._close_callbacks = []
        self._channels = {}


    def on_open(self, conn_info):
        """
        Called by SockJSConnection when connection is initialised 
        """
        self.conn_info = conn_info


    def on_close(self):        
        """
        Called by SockJSConnection upon disconnection or other close condition
        """
        for callback in self._close_callbacks:
            callback(self)
        for channel in self._channels.keys():
            self.unsubscribe(channel)


    def publish(self, channels, obj):
        self._app.sub.publish(channels, obj)


    def subscribe(self, channel, callback):
        """
        Subscribe enduser to a redis pubsub channel.
        When enduser disconnects channel will be auto-unsubscribed
        """
        assert channel is not None        
        self._channels[channel] = True
        self._app.sub.subscribe(channel, self, callback)


    def unsubscribe(self, channel):
        if channel in self._channels:
            del self._channels[channel]
            self._app.sub.unsubscribe(channel, self)


    def add_cleanup(self, callback):
        """
        Call the function when the connection is closed
        """
        self._close_callbacks.append(callback)


    def ok(self, token, response, status=1):
        """
        Respond successfully to the message
        """
        assert response is not None
        self._respond(token, status, response)


    def error(self, token, response=None, status=0):
        """
        Respond with an error to the message
        """
        self._respond(token, status, response)


    def _respond(self, token, is_ok=1, response=None):
        """
        Send 'realtime' formatted response back to client
        """
        if response is None:
            response = {}
        else:
            assert isinstance(response, dict)
        response['id'] = token
        response['_'] = is_ok
        try:
            response = json.dumps(response)
        except:
            LOGGER.exception("Failed to encode response!")
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
        Handles a raw message the SockJS connection.
        It parses the message, dispatches the RPC call and send the reply
        """   
        try:
            msg = self._parse_msg(raw_msg)        
            if not msg:            
                return            
            if msg['call'] in self._app._cmds:
                method = self._app._cmds[msg['call']]
                LOGGER.debug("%s: on_message: %s(%s)", self.conn_info.ip, msg['call'], json.dumps(msg['args']))
            else:
                LOGGER.warning("%s: on_message: unknown call '%s'", self.conn_info.ip, msg['call'])
                return self.error(msg['id'], {'call': 'Unknown'})
            try:
                kwargs = msg['args']
                response = method(self, **kwargs)            
                if response is not None:
                    assert isinstance(response, dict)
                    self.ok(msg['id'], response)
            except:
                # Catch-all exception handler, send back generic 'Server Error'
                LOGGER.exception("%s: on_message: exception on '%s' call", self.conn_info.ip, msg['call'])
                self.error(msg['id'], {'call': 'Server Error'})
        except:
            # So.. just incase _parse_msg errors out.. or something! Don't crash... please don't crash...
            LOGGER.exception("%s: on_message: cannot parse raw message: '%s'", raw_msg)





"""
.d88888b                                               
88.    "'                                              
`Y88888b. .d8888b. 88d888b. dP   .dP .d8888b. 88d888b. 
      `8b 88ooood8 88'  `88 88   d8' 88ooood8 88'  `88 
d8'   .8P 88.  ... 88       88 .88'  88.  ... 88       
 Y88888P  `88888P' dP       8888P'   `88888P' dP       
"""                                                                                                   
class RealtimeServer(object):
    def __init__(self, conf):
        self.conf = conf        

        self.redis = tornadoredis.Client(conf['redis_host'], conf['redis_port'])
        self.sub = RedisSubscriber(self.redis)

        self.sockjs_router = sockjs.tornado.SockJSRouter(self.make_request, '/realtime')
        self.tornado_app = tornado.web.Application(self.sockjs_router.urls)
        self.http_server = tornado.httpserver.HTTPServer(self.tornado_app)

        self._cmds = {}


    def register(self, cmd, callback):
        assert cmd is not None
        assert callable(callback)
        self._cmds[cmd] = callback
        LOGGER.debug("Registered command '%s' to %s", cmd, callback)


    def make_request(self, session):
        return EndUserConnection(self, session)        


    def run(self):
        self.http_server.listen(self.conf['http_port'], self.conf['http_host'])
        LOGGER.info('Camaste! Realtime @ http://%s:%d/realtime', self.conf['http_host'], self.conf['http_port'])
        tornado.ioloop.IOLoop.instance().start()


