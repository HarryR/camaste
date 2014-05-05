REDIS_VER=2.8.9
REDIS_DIR=redis-$(REDIS_VER)
REDIS_TAR=$(REDIS_DIR).tar.gz
REDIS_URL=http://download.redis.io/releases/$(REDIS_TAR)
REDIS_BLD_DIR=src/$(REDIS_DIR)/src

all: run

.PHONY: run
run: bin/redis-server-$(REDIS_VER)
	./start.sh $(REDIS_VER)

bin/redis-server-$(REDIS_VER): src/$(REDIS_DIR)/src/redis-server
	if [ -d bin ]; then mkdir -p bin; fi	
	cp $(REDIS_BLD_DIR)/redis-server bin/redis-server-$(REDIS_VER)
	cp $(REDIS_BLD_DIR)/redis-cli bin/redis-cli-$(REDIS_VER)
	cp $(REDIS_BLD_DIR)/redis-sentinel bin/redis-sentinel-$(REDIS_VER)
	cp $(REDIS_BLD_DIR)/redis-check-dump bin/redis-check-dump-$(REDIS_VER)
	cp $(REDIS_BLD_DIR)/redis-check-aof bin/redis-check-aof-$(REDIS_VER)

src/$(REDIS_TAR):
	if [ -d src ]; then mkdir -p src; fi
	wget -O $@ $(REDIS_URL)

src/$(REDIS_DIR)/src/redis-server: src/$(REDIS_TAR)
	if [ ! -d src/$(REDIS_DIR) ]; then mkdir -p src && cd src && tar -xf $(REDIS_TAR); fi	
	cd src/$(REDIS_DIR) && make

clean:
	./stop.sh
	rm -rf bin run src