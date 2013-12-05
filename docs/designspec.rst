HandyRep
========

This is the original design spec for HandyRep. It is not completely up to date, and is superceded by other documentation.

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
* these plugins are python code added to the plugin folder
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

Cluster and Server Statuses
---------------------------

Handyrep will consistently report the "health" of the cluster.  This health will have 3 degrees:

* 0 : "unknown" : status checks have not been run.  This status should only exist for a very short time.
* 1 :  "healthy" : cluster has a viable master, and all replicas are "healthy" or "lagged"
* 3 : "warning" : cluster has a viable master, but has one or more issues, including connnection problems, failure to fail over, or downed replicas.
* 5 : "down" : cluster has no working master, or is in an indeterminate state and requires administrator intervention

This is recorded in four cluster-wide fields:

* status: the above status label
* status_no: the above status number
* status_ts: the last timestamp when status was checked
* status_message: a message about the last issue found which causes a change in status.  May not be complete or representative.

Servers also have several statuses:

* 0, "unknown" : server has not been checked yet
* 1. "healthy" : server is operating normally
* 2. "lagged" : for replicas, indicates that the replica is running but has exceeded the configured lag threshold
* 3. "warning" : server is operating, but has one or more issues, such as inability to ssh, or out-of-connections.
* 4. "unavailable" : cannot determine status of server because we cannot connect to it.
* 5. "down" : server is verified down.

This is recorded in four per-server fields, which are the same as the four fields for the general cluster status, but apply only to that specific server.  For servers which are disabled, the status will no longer be updated.

Return Dictionary
-----------------

* All methods which are callable from the outside return a dictionary.
* This dictionary has "result" and "details" keys, and possibly other keys.
* "result" is either "SUCCESS" or "FAIL"

Plugins
-------

* Most direct server actions are implemented via plugins.
* Each plugin is its own module in the plugins directory.
* Each plugin module has exactly one class, named after itself
* Each plugin class has two methods, run() and test().  Parameters of these methods vary.
* run() and test() should return the usual Return Dictionary.

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

* Only one (network or mounted) location for archiving
* Assumes that all replicas can access the same archive
* Assumes that all nodes can use the same archiving scripts, if pushing scripts is enabled
* Assumes that the postgres user does all archive work
* Supporting only PostgreSQL 9.2 and later
* Does not deal with PITR, except to support WAL-E archiving
* Supports only one cluster
* Does not manage postgresql.conf at all
* Binary replication only
* Streaming or dual replication.  No archive-only replication.
* Assumes that hostnames are universal, not relative
* Does not do rsync/ssh config on nodes
* Assumes that all nodes use the same administration methods.
* does not support the "trigger file" method of replica promotion
* does not manage .pgpass or other authentication setup for the replication user

Future Plans
------------

* integrate with Salt/Puppet/Chef
* write replication config stuff for PostgreSQL.conf (probably through Salt/Puppet/Chef)
* GUI interface
* ability to query any handyrep server in a cluster
* support pg_rewind
* support cascading replication
* support runtime changes of the archive location by pushing recovery.conf and other scripts



