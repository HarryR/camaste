#!/bin/bash
if [ `whoami` = vagrant ]; then
	make start-components
else
	make start-vagrant
fi