#!/bin/sh
set -e

if [ -e /.installed ]; then
  echo "Already Installed."
  exit
fi

apt-get update

echo mysql-server-5.5 mysql-server/root_password password foobar | debconf-set-selections
echo mysql-server-5.5 mysql-server/root_password_again password foobar | debconf-set-selections

apt-get -y install tmux python-setuptools mysql-server python-dev python-pip git pv python-mysqldb python-lxml vim-nox make libpcre3-dev

echo "CREATE DATABASE camaste;" | mysql -u root -pfoobar
echo "GRANT ALL PRIVILEGES ON *.* TO 'camaste'@localhost IDENTIFIED BY 'camaste';" | mysql -u root -pfoobar

touch /.installed
