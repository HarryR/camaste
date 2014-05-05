#!/bin/bash
BASE=`dirname $0`
cd $BASE
STARTNGINX=0
if [ -f logs/nginx.pid ]
then
	kill -HUP `cat logs/nginx.pid`
	if [ $? -eq 1 ]
	then
		STARTNGINX=1
	fi
else
	STARTNGINX=1
fi
if [ $STARTNGINX -eq 1 ]
then
	bin/nginx -p `pwd`
fi
