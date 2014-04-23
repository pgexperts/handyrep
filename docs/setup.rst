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

And one of the following:

* apache2 + mod_wsgi
* nginx + uWSGI
* daemontools

Plus, if using the sample WebGUI:

* Flask-WTF 0.9.4+
* MarkupSafe 0.18+
* WTForms 1.0.5+
* Werkzeug 0.9.4+
* itsdangerous 0.23+
* requests 2.2.1+
* wsgiref 0.1.2+

Plus these general packages:

* postgresql client software
* ssh

Additionally, depending on your configuration and which plugins you are using, you may require any of the following additional software:

* pg_isready from PostgreSQL 9.3 or later (recommended)
* pgBouncer, HAProxy, or a similar connection proxy

PostgreSQL Servers Configuration
-------------------------------

HandyRep does not set up PostgreSQL on each node.  You are expected to do the installation and setup yourself, as well as configure PostgreSQL.conf on the master to be compatible with replication.  We recommend using a configuration management system (such as Puppet, Chef or Salt) for this.  You need to set up the initial master and configure it as well.

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

Some general notes on making settings in handyrep.conf:

**Disabling Settings**: It's preferred to set settings to nothing rather than deleting the entire setting.  This is as follows:

::

    archive_delete_method =

... and *not* by setting the setting to "None", "NULL", "0" or "''", any of which may cause errors.

Note that blanking a setting sets it to its default, *except* for plugin settings.

**Booleans**: use "True" and "False".

**Methods**: any setting called "*_method" refers to a plugin name, and its value should match a plugin name exactly.

**File Paths**: since HandyRep is generally run under a web server, it is far better practice to use complete file paths and not relative file paths.

Section handyrep
----------------

last_updated
    Date the configuration file was last updated.  Entered by the user, strictly for administrator information.
    
override_server_file
    If set to True, HandyRep will take server definitions from handyrep.conf instead of from saved server information.
    
server_file
    Filename for the servers JSON definition file.  Default servers.save.  If running HandyRep under WSGI, this needs to be
    a full path, not just a filename.

authentication_method
    Plugin to use for authentication into Handyrep itself.  Defaults to no authentication.
    
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
    Directory where the templates are stored.  If running under WSGI, needs to be a full path.
    
test_ssh_command
    Simple always-succeeds command to test if SSH access is working.  Default is "ls".
    
push_alert_method
    If we are pushing alerts to the monitoring system, the name of the plugin used to do that.  If left blank, HandyRep will not attempt to push alerts.

Section passwords
-----------------

Passwords for various things.  This section does not get displayed in API calls for config variables.
Database passwords can be left blank if using .pgpass files or some form of
passwordless authentication.

handyrep_db_pass
    Password for the handyrep database user, if required.

superuser_pass
    Password for "postgres".

replication_pass
    Password for replication user

admin_password
    API password for HandyRep administration rights in the REST interface, if using "simple" authentication.

read_password
    API password for HandyRep read-only rights, if using "simple" authentication.


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

poll_connection_proxy
    Should handyrep poll connection proxies (such as pgBouncer) every verify cycle
    to see if they're still running?

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

archive_script_method
    Plugin name for the archiving script, which controls how archiving happens.
    Also controls start, stop and poll methods for archiving.

archive_delete_method
    Plugin name of how to figure out which files to delete.  Used only for shared archives.

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

This section is read *only* during initial HandyRep setup, or if override_server_file is set to True.  Otherwise it is ignored in favor of the contents of servers.save.

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
    The role of the server in replication. Handyrep requires "master" and "replica" roles, which are the only PostgreSQL servers.  However, certain plugins use additional server roles, such as "archive", "pgbouncer", and "proxy".

failover_priority
    The priority of this server to be the new master in a failover event, if using the select_by_priority method, or if breaking ties with other methods.  Lower numbers are chosen first.

enabled
    Is this server enabled?  Disabled servers are ignored for most
    purposes.

In addition to the above, each server definition may change any of the various settings in server_defaults.  You may also add additional settings not used in server_defaults, such as setting "ip_address" required by the multi_pgbouncer_bigip plugin. 

Section plugins
---------------

This section contains configuration information for each of the various plugins which may have been enabled by the other methods, in the form:

::

    [[plugin_name]]
        config_key = value

The plugin_name here must match exactly the name as written in the *_method configuration where it is called, and the name of the python module of the plugin itself.  For this reason, configurations for plugins are global to their use, which may limit your ability to cope with differently configured nodes.

Each plugin defines its own configuration settings.  See Plugins docs for more information.  Plugin settings, in general, do *not* have defaults, so it's important to populate all required settings for plugins.

If a plugin has no configuration, you should still define a section for it so that the lack of configuration is clearly intentional. The one exception to plugin configuration is the master_check_method, which uses the master_check_parameters in the handyrep section.




