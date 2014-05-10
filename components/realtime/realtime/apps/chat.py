__all__ = ('ChatApp',)

import logging
LOGGER = logging.getLogger()



"""
dP     dP                            .d88888b    dP              dP            
88     88                            88.    "'   88              88            
88     88 .d8888b. .d8888b. 88d888b. `Y88888b. d8888P .d8888b. d8888P .d8888b. 
88     88 Y8ooooo. 88ooood8 88'  `88       `8b   88   88'  `88   88   88ooood8 
Y8.   .8P       88 88.  ... 88       d8'   .8P   88   88.  .88   88   88.  ... 
`Y88888P' `88888P' `88888P' dP        Y88888P    dP   `88888P8   dP   `88888P' 
"""
class ChatUserState(object):
    __slots__ = ('name', 'token2chan', 'chan2token')
    def __init__(self):
        self.name = None
        self.token2chan = {}
        self.chan2token = {}




                                          
"""
 a88888b. dP                  dP    .d888b.                    
d8'   `88 88                  88   d8'   '88                    
88        88d888b. .d8888b. d8888P 88aaaaa88  d88888b. .d8888b. 
88        88'  `88 88'  `88   88   88     88  88'  `88 88'  `88 
Y8.   .88 88    88 88.  .88   88   88     88  88.  .88 88.  .88 
 Y88888P' dP    dP `88888P8   dP   88     88  88Y888P' 88Y888P' 
                                              88       88       
                                              dP       dP  
"""
class ChatApp(object):
    def __init__(self, app):
        app.register('chat.join', self.join)
        app.register('chat.part', self.part)
        app.register('chat.sendmsg', self.sendmsg)
        LOGGER.info('Configured Chat application')


    def has_state(self, enduser):
        return enduser.has('chat')


    def state(self, enduser):
        """
        Get the ChatUserState object for an end-user
        """
        state = enduser.get('chat')
        if state is None:
            state = ChatUserState()
            enduser.set('chat', state)
        return state


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