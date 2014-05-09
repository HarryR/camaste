VERSION=1.6.0

all: start

.PHONY: start
start: bin/nginx-$(VERSION)
	mkdir -p logs tmp/hls
	./start.sh $(VERSION)

.PHONY: stop
stop:
	./stop.sh

bin/nginx-$(VERSION): src/nginx-$(VERSION)/objs/nginx
	mkdir -p bin
	cp src/nginx-$(VERSION)/objs/nginx bin/nginx-$(VERSION)

src/nginx-$(VERSION).tar.gz:
	mkdir -p src
	wget -O $@ http://nginx.org/download/nginx-$(VERSION).tar.gz

src/nginx-$(VERSION): src/nginx-$(VERSION).tar.gz
	cd src && tar -xf nginx-$(VERSION).tar.gz

src/nginx-rtmp-module:
	cd src && git clone https://github.com/arut/nginx-rtmp-module.git

src/nginx-$(VERSION)/objs/nginx: src/nginx-$(VERSION) src/nginx-rtmp-module src/headers-more-nginx-module-0.25
	cd src/nginx-$(VERSION) && ./configure --add-module=`pwd`/../nginx-rtmp-module/ \
										   --add-module=`pwd`/../headers-more-nginx-module-0.25/ \
										   --with-http_ssl_module --with-http_auth_request_module \
										   --without-http_uwsgi_module --without-http_scgi_module \
										   --without-http_memcached_module --without-http_ssi_module \
										   --without-http_fastcgi_module --with-file-aio --with-ipv6 \
										   --without-http_userid_module --without-http_autoindex_module \
										   --without-http_map_module --without-http_empty_gif_module \
										   --with-http_flv_module --with-http_mp4_module \
										   --http-proxy-temp-path=tmp/proxy_temp \
										   --http-client-body-temp-path=tmp/client_body_temp
	make -C src/nginx-$(VERSION)

src/headers-more-nginx-module-0.25: src/headers-more-nginx-module-v0.25.tar.gz
	if [ ! -d $@ ]; then \
		cd src && tar -xf headers-more-nginx-module-v0.25.tar.gz ;\
	fi

src/headers-more-nginx-module-v0.25.tar.gz:
	wget -O $@ https://github.com/openresty/headers-more-nginx-module/archive/v0.25.tar.gz

clean: stop
	rm -rf logs src bin proxy_temp fastcgi_temp client_body_temp tmp