#!/bin/bash
if [ $# -eq 0 ]; then
	echo "Usage: start.sh <nginx-version>"
	exit
fi

BASE=`dirname $0`
cd $BASE
STARTNGINX=0
if [ -f logs/nginx.pid ]
then
	sudo kill -HUP `cat logs/nginx.pid`
	if [ $? -eq 1 ]
	then
		STARTNGINX=1
	fi
else
	STARTNGINX=1
fi
if [ $STARTNGINX -eq 1 ]
then
	sudo bin/nginx-$1 -p `pwd`
fi
