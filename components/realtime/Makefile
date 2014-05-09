all: check start

.PHONY: check
check:
	pyflakes realtime

.PHONY: start
start:
	python -mrealtime --logging=logging.conf
