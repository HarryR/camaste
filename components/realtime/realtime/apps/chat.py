__all__ = ('ChatApp',)

import logging
LOGGER = logging.getLogger()

class ChatApp(object):
    def __init__(self, app):
        app.register('chat.join', self.join)
        app.register('chat.part', self.part)
        app.register('chat.sendmsg', self.sendmsg)
        LOGGER.info('Configured Chat application')

    def on_msg(self, enduser, msg):
        if msg.kind == 'message':
            enduser.reply('chat.msg', {
                'channel': msg.channel,
                'body': msg.body
            })

    def join(self, enduser, token):
        # TODO: check if enduser is allowed to join
        enduser.subscribe(token, self.on_msg)
        return {
            'token': token,
            'join': True
        }

    def part(self, enduser, token):
        # TODO: check if enduer is in room
        enduser.unsubscribe(token)
        return {
            'token': token,
            'part': True
        }

    def sendmsg(self, enduser, token, text):
        # TODO: check if enduser is in allowed to post
        # TODO: map token to channel
        enduser.publish(token, {
            "text": text
        })
        return {
            'token': token,
            'sent': True
        }