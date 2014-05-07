all:
	$(error Please use "make start" or "make stop")

# These call '*-vagrant' or '*-components' depending on if they're 
# running as Vagrant or on the developers machine.
start:
	@./start.sh
stop:
	@./stop.sh

.PHONY: start-vagrant
start-vagrant:
	cd vagrant && vagrant up

.PHONY: ssh
ssh:
	@cd vagrant && vagrant ssh

.PHONY: start-components
start-components:
	make -C components/nginx
	make -C components/redis
	make -C components/frontend

.PHONY: stop-components
stop-components:
	make -C components/nginx stop
	make -C components/redis stop