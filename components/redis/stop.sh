#!/bin/bash
BASE=`dirname $0`
cd $BASE
if [ -f run/redis.pid ]; then
	kill -TERM `cat run/redis.pid` &> /dev/null
	rm -f run/redis.pid
fi