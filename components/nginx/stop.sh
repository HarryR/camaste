#!/bin/bash
BASE=`dirname $0`
cd $BASE
if [ -f logs/nginx.pid ]; then
	kill -TERM `cat logs/nginx.pid` &> /dev/null
	rm -f logs/nginx.pid
fi