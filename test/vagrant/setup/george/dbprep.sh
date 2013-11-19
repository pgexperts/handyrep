#!/bin/bash

# stop postgres
service postgresql stop

# copy configuration files
cp /setup/john/postgres/conf/* /etc/postgresql/9.3/main/
#cp /setup/postgres/pgbouncer.ini /etc/pgbouncer/
#cp /setup/postgres/userlist.txt /etc/pgbouncer/
#cp /setup/postgres/pgbouncer.default /etc/default/pgbouncer
#chown -R postgres /etc/pgbouncer

# create pitr-replication dir and copy stuff
cp -r -p /setup/scripts /var/lib/postgresql/

# create the archiving and replica directories
mkdir /var/lib/postgresql/wal_archive
chown -R postgres /var/lib/postgresql/*

#link pg_ctl and friends
ln -s /usr/lib/postgresql/9.3/bin/pg_ctl /usr/bin/pg_ctl
ln -s /usr/lib/postgresql/9.3/bin/initdb /usr/bin/initdb
ln -s /usr/lib/postgresql/9.3/bin/pg_archivecleanup /usr/bin/pg_archivecleanup

# restart postgresql
#su - postgres -c "/usr/bin/pg_ctl -D /etc/postgresql/9.3/main start"
#service postgresql start

# load the libdata database
#psql -U postgres -f /setup/john/postgres/users.sql postgres
#pg_restore -e -U postgres -d libdata /setup/postgres/libdata.dump

exit 0
