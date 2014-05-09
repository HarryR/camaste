__all__ = ('RoomsApp',)

import logging
LOGGER = logging.getLogger()

class RoomsApp(object):
	def __init__(self, app):
		app.register('room.join', self.join)
		app.register('room.part', self.part)
		app.register('room.send', self.send)
		logging.info('Configured Rooms application')

	def on_msg(self, enduser, msg):
		if msg.kind == 'message':
			enduser.ok('rooms.msg', {
				'message': msg.body
			})

	def join(self, enduser, room):
		enduser.subscribe(room, self.on_msg)
		return {
			'room': room,
			'join': True
		}

	def part(self, enduser, room):
		enduser.unsubscribe(room)
		return {
			'room': room,
			'part': True
		}

	def send(self, enduser, room, msg):
		enduser.publish(room, {
			"body": msg
		})
		return {
			'room': room,
			'sent': True
		}