from django.conf.urls import patterns, url
from django.http import HttpResponse


"""
888888ba           oo                   
88    `8b                               
88     88 .d8888b. dP 88d888b. dP.  .dP 
88     88 88'  `88 88 88'  `88  `8bd8'  
88     88 88.  .88 88 88    88  .d88b.  
dP     dP `8888P88 dP dP    dP dP'  `dP 
               .88                      
           d8888P    


This module handles callbacks for events on the nginx-rtmp-module server.
The hooks (like publish and publish_done) maintain database state and send out
notifications via Redis.

Basically this makes sure that when a whore goes offline by accident the private
show stops and the fappers get notified instantly... that kinda stuff.
"""

class NginxHooks(object):
	@classmethod
	def on_publish(cls, request):
		"""
		call=publish
		addr - client IP address
		clientid - nginx client id (displayed in log and stat)
		app - application name
		flashVer - client flash version
		swfUrl - client swf url
		tcUrl - tcUrl
		pageUrl - client page url
		name - stream name
		"""
		return HttpResponse(status=403)

	@classmethod
	def on_play(cls, request):
		"""
		call=play
		addr - client IP address
		clientid - nginx client id (displayed in log and stat)
		app - application name
		flashVer - client flash version
		swfUrl - client swf url
		tcUrl - tcUrl
		pageUrl - client page url
		name - stream name
		"""
		return HttpResponse(status=403)

	@classmethod
	def on_play_done(cls, request):
		"""
		HTTP return code not checked!
		call=play_done
		addr - client IP address
		clientid - nginx client id (displayed in log and stat)
		app - application name
		flashVer - client flash version
		swfUrl - client swf url
		tcUrl - tcUrl
		pageUrl - client page url
		name - stream name
		"""
		return HttpResponse(status=403)

	@classmethod
	def on_publish_done(cls, request):
		"""
		HTTP return code not checked!
		call=publish_done
		addr - client IP address
		clientid - nginx client id (displayed in log and stat)
		app - application name
		flashVer - client flash version
		swfUrl - client swf url
		tcUrl - tcUrl
		pageUrl - client page url
		name - stream name
		"""
		return HttpResponse(status=403)

	@classmethod
	def on_record_done(cls, request):
		"""
		HTTP return code not checked!
		call=record_done
		addr - client IP address
		clientid - nginx client id (displayed in log and stat)
		app - application name
		flashVer - client flash version
		swfUrl - client swf url
		tcUrl - tcUrl
		pageUrl - client page url
		name - stream name
		"""
		return HttpResponse(status=403)

	@classmethod
	def on_update(cls, request):
		"""
		If a request returns HTTP result other than 2xx connection is terminated.
		call=update
		addr - client IP address
		clientid - nginx client id (displayed in log and stat)
		app - application name
		flashVer - client flash version
		swfUrl - client swf url
		tcUrl - tcUrl
		pageUrl - client page url
		name - stream name
		time - is the number of seconds since play/publish call
		timestamp - is RTMP timestamp of the last audio/video packet sent to the client
		"""
		return HttpResponse(status=403)





urlpatterns = patterns('backend.hooks.nxrtmp',
	url(r'^on_play$', NginxHooks.on_play, name='nxrtmp.on_play'),
	url(r'^on_publish$', NginxHooks.on_publish, name='nxrtmp.on_publish'),
	url(r'^on_update$', NginxHooks.on_update, name='nxrtmp.on_update'),
	url(r'^on_record_done$', NginxHooks.on_record_done, name='nxrtmp.on_record_done'),
	url(r'^on_publish_done$', NginxHooks.on_publish_done, name='nxrtmp.on_publish_done'),
	url(r'^on_play_done$', NginxHooks.on_play_done, name='nxrtmp.on_play_done'),
)