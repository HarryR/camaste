#!/bin/bash
if [ $# -eq 0 ]; then
	echo "Usage: start.sh <redis-version>"
	exit
fi

BASE=`dirname $0`
cd $BASE
mkdir -p $BASE/run/
STARTREDIS=0
if [ -f $BASE/run/redis.pid ]
then
	kill -HUP `cat logs/redis.pid`
	if [ $? -eq 1 ]
	then
		STARTREDIS=1
	fi
else
	STARTREDIS=1
fi
if [ $STARTREDIS -eq 1 ]
then
	$BASE/bin/redis-server-$1 conf/redis.conf
fi
