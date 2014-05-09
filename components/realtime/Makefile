all: check start

.PHONY: check
check:
	pyflakes realtime
	pychecker -Q --only realtime

.PHONY: start
start:
	python -mrealtime --logging=logging.conf
