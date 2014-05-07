#!/bin/bash
BASE=`dirname $0`
cd $BASE
if [ -f logs/nginx.pid ]; then
	sudo kill -TERM `cat logs/nginx.pid` &> /dev/null
	sudo rm -f logs/nginx.pid
fi