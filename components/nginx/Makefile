VERSION=1.6.0

all: run

run: bin/nginx-$(VERSION)
	mkdir -p logs tmp/hls
	./start.sh $(VERSION)

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

src/nginx-$(VERSION)/objs/nginx: src/nginx-$(VERSION) src/nginx-rtmp-module
	cd src/nginx-$(VERSION) && ./configure --add-module=`pwd`/../nginx-rtmp-module/ --with-http_ssl_module \
										   --without-http_uwsgi_module --without-http_scgi_module \
										   --without-http_memcached_module --without-http_ssi_module \
										   --with-http_flv_module --with-http_mp4_module
	make -C src/nginx-$(VERSION)

clean:
	./stop.sh
	rm -rf logs src bin proxy_temp fastcgi_temp client_body_temp tmp