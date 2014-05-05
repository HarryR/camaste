REDIS_VER=2.8.9
REDIS_DIR=redis-$(REDIS_VER)
REDIS_TAR=$(REDIS_DIR).tar.gz
REDIS_URL=http://download.redis.io/releases/$(REDIS_TAR)
REDIS_BLD_DIR=src/$(REDIS_DIR)/src

all: run

run: bin/redis-server
	./start.sh

bin/redis-server: src/$(REDIS_DIR)/src/redis-server
	mkdir -p bin
	cp $(REDIS_BLD_DIR)/redis-server bin/
	cp $(REDIS_BLD_DIR)/redis-cli bin/
	cp $(REDIS_BLD_DIR)/redis-sentinel bin/
	cp $(REDIS_BLD_DIR)/redis-check-dump bin/
	cp $(REDIS_BLD_DIR)/redis-check-aof bin/

src/$(REDIS_TAR):
	mkdir -p src
	wget -O $@ $(REDIS_URL)

src/$(REDIS_DIR): src/$(REDIS_TAR)
	cd src && tar -xf $(REDIS_TAR)

src/$(REDIS_DIR)/src/redis-server: src/$(REDIS_DIR)
	cd src/$(REDIS_DIR) && make