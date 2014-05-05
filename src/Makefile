all: run

.PHONY: sql
sql:
	./manage.py dbshell

.PHONY: shell
shell:
	./manage.py shell

.PHONY: run
run:
	./manage.py collectstatic --noinput > /dev/null
	./manage.py runserver 0.0.0.0:8080

.PHONY: reset
reset:
	./manage.py sqlreset
	./manage.py syncdb --noinput
	./manage.py collectstatic --noinput > /dev/null
	./manage.py runserver 0.0.0.0:8080
