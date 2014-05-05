# Layout

 * `components/publisher` - Haxe/Flash based webcam streaming SWF
 * `components/frontend` - Django based frontend
 * `components/realtime` - Tornado / Redis based realtime stuff
 * `components/nginx` - Nginx with rtmp module + config for testing + proxy for frontend & realtime
 * `components/redis` - Redis server
 * `vagrant` - Vagrant box for running the app in
 * `deploy` - Directory where publicly accessible data goes (for collectstatic & uploads)

# TODO:

 * More implementation of site frontend
 * Implement more models in Django project
 * Configurable options in 'publisher' component so model can choose different broadcast settings in frontend
 * Figure out what sorts of billing will be done
 * Fill out the spec with more technical details
 * Decide on realtime service which supports sock.js
 * More info on this document?

# Architecture

 * Web Frontend
 * RTMP Server
 * Backend Hooks/Control Service (internal)
 * Web Chat/Realtime Service

Technology:
 * nginx + nginx-rtmp-module
 * Django 1.6
 * MySQL 5.x for most data
 * Redis (for live/realtime data + fast backend stuff)

## Web Frontend

 Django based application provides the frontend & admin interface for the site.
 Functionality:

All users:
  * Browse active models + view model profiles (CORE)
  * Browse live streams (CORE)
  * Signup / Login / Activate Account / Reset Password (CORE)
  * Purchase credits

Models only:
  * Signup as Model (CORE)
  * Edit model profile + 'approval status' + manage model stuff (CORE)
  * Broadcast as model (CORE)

Admin:
  * Manage site finances
  * Manage promotions and other shit
  * Approve/disapprove new models


## Web Chat/Realtime Service

The realtime service provides support for real-time notification of web clients from the backend and the webapp.

The main uses for this service will be:
 * Realtime model chat
 * Realtime notifications of show/model status
 * Update of credits status/usage

It must be fast and scalable, it shouldn't depend on Django or MySQL and shouldn't have to handle much (if any) business logic - just delivering notifications from the backend to a specific client (for notifications) or a channel of clients (for chat).

Possible softwares:
 * http://simplapi.wordpress.com/2013/09/22/sockjs-on-steroids/ ?
 * Probably going to be python + gevent based, unless other *fast* service can be found

## RTMP Service

The RTMP service is going to be powered by nginx-rtmp-module, this module has the following critical features:

 * HTTP Live streaming support (for iPad/iOS support and HTML5 only video)
 * HTTP based control and stats interface
 * Automatic saving of stream keyframes
 * Hooks on all types of RTMP events (e.g. publish, play)
 * Can do server-side redirection of streams

Using the hooks and the control interface we can implement all of the backend functionality required for cam site.

Documentation:

 * Homepage: https://github.com/arut/nginx-rtmp-module/
 * Blog: http://nginx-rtmp.blogspot.fr/
 * Configuration Docs: https://github.com/arut/nginx-rtmp-module/wiki/Directives

### Implementing + Hooks + Billing

The publishers will connect to an endpoint like rtmp://$ip/publish/$token, we can provide this URL to the publishers to use with their own streaming software or they can use flash based broadcaster on our site. When a publisher connects the rtmp module calls our `on_publish` hook where we authenticate the token + ensure the publisher can only publish 1 stream at a time.

When clients connect we can do authentication too via the `on_play` hook. The `on_update` hook is called every 30 seconds (configurable via `notify_update_timeout`) for *every* active connection (both publisher and client). We can use this callback to implement per minute billing, or time limit cut-off etc.

The `on_publish_done` callback can be used to update the site and disable the `is_broadcasting` flag on the model.

### Example Config

```
rtmp {
	server {
		listen 1935;
		ping 30s;
		notify_method get;

		application src {
			live on;
			allow publish all;
			allow play all;

			on_play http://localhost/backend/on_play;
			on_publish http://localhost/backend/on_publish;
			on_play_done http://localhost/backend/on_play_done;
			on_publish_done http://localhost/backend/on_publish_done;
			on_record_done http://localhost/backend/on_record_done;
			on_update http://localhost/backend/on_update;
			notify_update_timeout 30s;

			meta copy;
			sync 100ms;s
			interleave on;
		 	wait_key on;
    		wait_video on;
    		drop_idle_publisher 30s;
			idle_streams on;
		}

		application hls {
			live on;
			hls on;
			hls_path tmp/hls;
			hls_fragment 15s;
		}
	}
}
```


## Backend Hooks / Control Service

Ideally the backend billing stuff should be separated from the frontend and must be able to run independently.
It should probably use Redis for storage.
It probably shouldn't use Django because it needs to be *fast*, lightweight and possibly asynchronous?

Functionality:
 
 * All the hooks required for the RTMP server
 * Core authentication of publishers & clients
 * Billing
 * Time limiting of sessions


TODO?
 * Performer, should rename to ModelProfile?
 * Need to keep all monetary balances SEPERATE from the Performer/Account models

Realtime chat:
 * http://simplapi.wordpress.com/2013/09/22/sockjs-on-steroids/