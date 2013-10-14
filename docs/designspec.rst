HandyRep
========

General
-------

* Written entirely in Python
* Intended to be run on a single server (not on each server in the cluster)
* Can be run from a 3rd server (such as a pgbouncer server)
* Can be run in a failover configuration, with a 2nd Handyrep which doesn't accept commands.
* Designed to minimize the per-node installation requirements.
* Controls one single PostgreSQL cluster of master-slave replicas
* Supports multiple replicas

Setup Requirements
------------------

On Handyrep Server:
* python 2.7+, plus fabric, paramiko, pyyaml, psycopg2, jinja2 and uWSGI
* ssh and rsync
* ssh keys to all servers as user with sudo postgres and root
* postgres password

Optional (on Handyrep Server):
* pg_isready from PostgreSQL 9.3
* pgbouncer, pgpool2 or HAProxy
* ssh keys to archive location

On Nodes:
* PostgreSQL
* sudo
* postgres port open to HandyRep server
* directory controlled by handyrep user and accessible to postgres user
* postgresql.conf set up for replication

Optional on Nodes:
* WAL-E and/or archive scripts
* rsync/ssh config to other nodes

Configuration
-------------

* Two YAML configuration files: handyrep.conf and servers.save
* Handyrep.conf represents initial default config and general config
* Servers.save is generated and written by the runtime, and is automatically updated with current server information.
* Both configuration files are written to the database in a table called handyrep.
* Configuration files are timestamped to figure out "latest".
* All server configuration stuff has a "default" and a per-server setting as an override.

Plug-Ins
--------

* users can write plugin methods for various tasks: server check, cloning, new master selection, extra failover commands
* these plugins are python code added to plugins.py
* they can then be added to the config

Daemon
------

* HandyRep will run as a uWSGI daemon/server.
* The web service will require simple authentication
* It will take HandyRep commands by POST
* It will supply data when polled in JSON format

Polling and Automated Failover
------------------------------

* If configured, every poll_interval HandyRep will poll the master for uptime.
* If the master doesn't respond using poll_method in poll_tries, HandyRep will intiate failover.
* New master will be determined by selection_method
* HandyRep will try to fail over to new master or roll back on fail
* If configured, HandyRep will also try to remaster other replicas.  It will NOT rollback if these fail.
* Will also execute post-failover_commands as configured.

Actions Supported by HandyRep
-----------------------------

* initialize
* check handyrep status
* verify servers (against config)
* sync configuration
* check master
* check replica(s)
* get server(s) status
* failover check
* failover
* stonith (the master)
* promote (a replica)
* remaster (a replica)
* clone (a new replica)
* reclone (a replica)
* shutdown (a server)
* remove (a replica)
* get server info (current config)
* get server by role (master, replica)
* validate server settings (against correct format)
* change server (new config)
* clean archive (of old files)

Limitations
-----------

* Only one (network) location for archiving
* Assumes that all replicas can access the same archive
* Supporting only PostgreSQL 9.2 and later
* Does not deal with PITR, except to support WAL-E archiving
* Supports only one cluster
* Does not manage postgresql.conf at all
* Binary replication only
* Assumes that hostnames are universal, not relative
* Does not do rsync/ssh config on nodes
* Assumes that all nodes use the same administration methods.

Future Plans
------------

* integrate with Salt/Puppet/Chef
* write replication config stuff for PostgreSQL.conf (probably through Salt/Puppet/Chef)
* GUI interface
* ability to query any handyrep server in a cluster
* support pg_rewind
* push archive script from HandyRep server
* support cascading replication



