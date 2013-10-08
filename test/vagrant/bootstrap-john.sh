#!/usr/bin/env bash

# setup apt-get to pull from apt.postgresql.org
echo "deb http://apt.postgresql.org/pub/repos/apt/ precise-pgdg main 9.3" > /etc/apt/sources.list.d/pgdg.list
wget --quiet -O - http://apt.postgresql.org/pub/repos/apt/ACCC4CF8.asc | apt-key add -

# update apt
apt-get update
apt-get -y -q install pgdg-keyring

# install postgresql and a bunch of accessories
apt-get -y -q install postgresql-client-9.3
apt-get -y -q install postgresql-9.3
apt-get -y -q install postgresql-contrib-9.3

# install alternate editor and tmux
apt-get -y -q install joe
apt-get -y -q install tmux

/setup/john/dbprep.sh

echo ''
echo 'vagrant loaded and ready for tutorial'
echo 'version 0.1 of handyrep test environment'

exit 0




