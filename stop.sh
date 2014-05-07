#!/bin/sh
if [ `whoami` = vagrant ]; then
	make stop-components
else
	make stop-vagrant
fi