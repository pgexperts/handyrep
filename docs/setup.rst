HandyRep Setup
==============

HandyRep Server Installation
----------------------------

HandyRep is a Python application which has the following module dependencies:

* python 2.7
* fabric 1.8.0+
* paramiko
* jinja2
* psycopg2 2.5+

Plus, if you are using the Daemon:

* flask 0.8+

Plus these general packages:

* postgresql client software
* ssh

Additionally, depending on your configuration and which plugins you are using, you may require any of the following additional software:

* pg_isready from PostgreSQL 9.3 or later (recommended)
* pgBouncer, HAProxy, or a similar connection proxy

PostgreSQL Servers Configuration
-------------------------------

HandyRep does not set up PostgreSQL on each node.  You are expected to do the installation and setup yourself, as well as configure PostgreSQL.conf to be compatible with replication.  We recommend using a configuration management system (such as Puppet, Chef or Salt) for this.  You need to set up the initial master and configure it as well.

Note that this does mean that the various servers in your cluster can have different configurations, as long as they are all compatible with replication.  This allows for setups such as having designated reporting servers.

Each node also needs the following software:

* PostgreSQL 9.1 or later
* sudo
* sshd

Depending on configuration, you may also want to install and set up the following software on each node:

* WAL-E or Barman
* rsync

Users, SSH and Permissions Configuration
----------------------------------------

HandyRep runs as a designated user on the HandyRep server, usually "handyrep".  This user is expected to have all of the following abilities and permissions:

* passwordless sudo on the HandyRep server
* passphraseless ssh key login on all nodes
* passwordless sudo on all nodes
* a writeable home directory on each node
* ability to psql as postgres to all PostgreSQL servers in the cluster, using an md5 password.
* a "handyrep" user in the database, with superuser permissions.
* ability to overwrite the archiving script, if applicable.

In some cases, the HandyRep server may also be a node for one service or another, so also make sure that the handyrep user has ssh key login on its own server.

HandyRep makes use of two users on nodes: the os superuser and the database owner and superuser, usually "root" and "postgres" respectively (but configurable if not).  HandyRep expects certain things from the "postgres" user on the remote nodes:

* it should own the PGDATA directory and the recovery configuration file.
* it should be able to execute the core PostgreSQL binary utilities without indirection (i.e. use pg_ctl, not pg_ctlcluster).
* it should have md5 or passwordless psql login, both locally, and on other PostgreSQL servers in the cluster.

Additionally, if you are using rsync and not pg_basebackup for replica cloning, you will need to ensure that the postgres user has passwordless ssh login between PostgreSQL servers in the cluster.

Templates
---------

The templates directory contains jinga2 templates which allow HandyRep to write configuration files and shell scripts to other servers.  This templates directory is relocatable by changing handyrep.conf.  Ideally, the templates in this directory should be under centralized configuration file management, allowing adminstrators to manage configuration settings which are not dynamically written out by HandyRep.

See Usage for more information on these templates.

Configuring Other Servers
-------------------------

HandyRep may be programmed to work with pgBouncer, HAProxy, S3, Barman, WAL-E, BigIP, or many other network services which are complimentary to maintaining PostgreSQL high availability.  These are all managed via plugins.

If you are using these other services, and expect HandyRep to manage them during failover, then it needs permissions to modify the service's configuration or give it directions.  For example, if using the pgbouncer plugin, then HandyRep needs the ability to rewrite pgbouncer.ini and restart pgbouncer, which would mean SSH and Sudo access on that server.

handyrep.conf
=============

The main configuration file for HandyRep is usually called handyrep.conf, and needs to be named when starting HandyRep.  It has a lot of configuration variables in order to allow intergration with a wide variety of network and server infrastructures.

Section handyrep
----------------

last_updated
    Date the configuration file was last updated.  Entered by the user, strictly for administrator information.
    
override_server_file
    If set to True, HandyRep will take server definitions from handyrep.conf instead of from saved server information.
    
server_file
    Filename (or full path) for the servers JSON definition file.  Default servers.save.
    
master_check_method
    Plugin to use in order to check if this HandyRep is the current HandyRep master server.  See "Multiple HandyRep Servers" in Usage.
    
master_check_parameters
    Text list; parameters for the named plugin.
    
log_verbose
    If set to true, log every action, not just errors and failovers.
    
log_file
    Filename or path of HandyRep's log file.
    
postgresql_version
    Version number of PostgreSQL on the cluster.  Needed for some plugins.
    
handyrep_db
    Database where HandyRep stores its status data.  This database must be created by the user if it doesn't already exist.
    
handyrep_schema
    Schema which HandyRep uses for data.  Created by HandyRep.
    
handyrep_table
    Table in which HandyRep stores status data.

handyrep_user
    User handyrep uses when updating its own status data.
    
postgres_superuser
    Name of the PostgreSQL superuser.  Usually "postgres".

replication_user
    Name of the user used for streaming replication connections.  Often the same as the superuser.
    
templates_dir
    Directory where the templates are stored.
    
test_ssh_command
    Simple always-succeeds command to test if SSH access is working.  Default is "ls".
    
push_alert_method
    If we are pushing alerts to the monitoring system, the name of the plugin used to do that.  If left blank, HandyRep will not attempt to push alerts.

Section passwords
-----------------

handyrep_db_pass
    Password for the handyrep database user, if required.

superuser_pass
    Password for "postgres".

replication_pass
    Password for replication user

admin_password
    API password for HandyRep administration rights in the REST interface.

read_password
    API password for HandyRep read-only rights.


Section failover
----------------

auto_failover
    If True, HandyRep will attempt to automatically fail over if a failure of the master is detected.

poll_method
    Plugin name for the "polling" plugin.
    
poll_interval
    Number of seconds between polling all of the servers.
    
verify_frequency
    Do a full verify after this number of polling cycles.
    
fail_retries
    If polling or other connections to a server fails, how many times should HandyRep keep trying to connect before declaring failure?
    
fail_retry_interval
    How long should HandyRep wait between retries (in seconds)?
    
recovery_retries
    How many times should HandyRep try to contact a server which has been promoted, newly cloned, or restarted before giving up?

selection_method
    Plugin name for the method used to determine which replica should be the new master in a failover.

remaster
    Should HandyRep attempt to remaster all other replicas in the cluster when the master changes?  Requires PostgreSQL 9.3 or better.

restart_master
    Should HandyRep try to restart the master before going ahead with failover?  Set to false if another service already handles auto-vivification.

connection_failover_method
    Plugin name for the plugin used to fail over connections after a database failover.  If left blank, HandyRep will not attempt to fail over connections.

replication_status_method
    Plugin name for the plugin used to check status of each replica, both replication connection and lag.

Section extra_failover_commands
-------------------------------

This section may contain a series of extra commands to be run after failover in order to fail over other services, set alerts, log things, or perform other tasks.  Note that these commands are not checked for success, merely called.  Default is blank (no commands); to provide a failover command, fill it out in the following form:

::

    [[command_name]]
        command = Plugin Name
        parameters = list, of, parameters

Section archive
---------------

archiving
    Is PostgreSQL doing WAL archiving as well as streaming replication?
    
archive_server
    Server name of the server where the archive files are kept.  See Servers below.
    
archive_directory
    Name of the directory where WAL archive files are kept, if applicable.
    
archive_bin
    Full path of the executable script run as the archive_command on the master PostgreSQL server.
    
archive_template
    Name of the template for the archiving script.
    
push_archive_script
    Should HandyRep push a rewritten archiving script to each server?

archive_delete_hours
    Number of hours archive WAL files should be kept.  If HandyRep is not managing expiration, set to zero.

archive_delete_method
    Plugin name of how to figure out which files to delete that are older than archive_delete_hours.

no_archive_file
    Trigger file to disable archiving, if enabled in your template.

Section server_defaults
-----------------------

These are default values for all servers in the HandyRep cluster, unless overridden by specific server settings.  As with individual server configuration, these are *only* read from handyrep.conf when HandyRep is first started up, or when override_server_file is set to True.

port
    The PostgreSQL TCP port.
    
pgdata
    Full path to the data directory.
    
pgconf
    Full path to postgresql.conf.
    
replica_conf
    Full path to the location of recovery.conf, or whatever your replica configuration file is called if on 9.4 or later.

recovery_template
    Template used for recovery.conf.

ssh_user
    The user to use for SSHing to this server.

ssh_key
    Full path on the HandyRep server for the SSH key to access this server.

restart_method
    Plugin name for the plugin used for starting, stopping, restarting and reloading the PostgreSQL server.

promotion_method
    Plugin name for the method used to promote a replica to be a standalone/master.

lag_limit
    Number of units before a particular replica is considered "lagged".  Units are defined by the replication_status_method plugin.

clone_method
    Plugin name of the plugin used to clone a new replica.

failover_priority = 999
    Default failover priority for a new server.

Section servers
---------------

This section has a series of server definitions, each one of which has informtion about that server, in the form:

::

    [[server_name]]
        hostname = replica1
        role = replica
        failover_priority = 1
        enabled = True

Where the configuration parameters are:

server_name
    A unique and permanent name used hereafter in HandyRep to refer to this server.

hostname
    The DNS name or IP address of the server.

role
    The role of the server in replication.  Options include master, replica, archive, and proxy, but any label can be used.  HandyRep cares only about "master" and "replica"; other labels are there for administrator information only,
    or to support certain plugins (such as "multi_pgbouncer"), or for archiving.

failover_priority
    The priority of this server to be the new master in a failover event, if using the select_by_priority method, or if breaking ties with other methods.  Lower numbers are chosen first.

enabled
    Is this server enabled for replication?  Note that non-database servers may be marked as "False" even though they may be used for some other purpose (i.e. archive storage).

In addition to the above, each server definition may change any of the various settings in server_defaults.

Section plugins
---------------

This section contains configuration information for each of the various plugins which may have been enabled by the other methods, in the form:

::

    [[plugin_name]]
        config_key = value

The plugin_name here must match exactly the name as written in the *_method configuration where it is called, and the name of the python module of the plugin itself.  For this reason, configurations for plugins are global to their use, which may limit your ability to cope with differently configured nodes.

Each plugin defines its own configuration settings.  See Plugins docs for more information.

If a plugin has no configuration, you should still define a section for it so that the lack of configuration is clearly intentional.

The one exception to plugin configuration is the master_check_method, which uses the master_check_parameters in the handyrep section.


    





