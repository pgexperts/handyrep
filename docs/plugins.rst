Plugins and the Plugin API
==========================

Most of the actual "work" of HandyRep is done by plugins.  In general, the main handyrep.py program does not directy manipulate database servers, connection proxies, or other services at all; instead, all of this work is delegated to Plugins.  This allows HandyRep to theoretically support any combination of external server technologies.

Plugins and HandyRep.conf
-------------------------

The handyrep.conf directives which are *_method are all plugin references.  Each of these should be filled with the name of a single plugin which handles that task.  The plugin name is identical to the module name (filename) of the plugin, as well as the plugin class name.

The Plugins section of the handyrep.conf contains configuration variables for the individual plugin.  Again, each of the subsections should carry the exact name of the plugin.  Note that variables in these sections are not validated because users can add new plugin configurations of their own.

If you install a new plugin, you will want to add that plugin as a subsection in the Plugins section.

List of Existing Plugins
========================

Each plugin listed below has a run() method and a test() method.  Parameters listed are for the run() method.  If the plugin has additional methods, those are explained below run/test.

Generic Plugins
---------------

These are not real plugins; they are example or generic plugins for plugin development.

handyrepplugin
~~~~~~~~~~~~~~

This is the "parent" plugin class which is extended by all plugins.

failplugin
~~~~~~~~~~

Generic "failure" plugin.  Always returns FAIL when called.  Called if a user calls a plugin which doesn't exist.  Implements "run" and "test" only.

successplugin
~~~~~~~~~~~~~

Generic "success" plugin.  Always returns SUCCESS when called.  Implements "run" and "test" only.

Authentication Plugins
----------------------

These plugins govern how users of handyrep itself, both the API and the GUI, are authenticated.  If you're using handyrep as a library, you can safely ignore them, as you need to do your own authentication then.

zero_auth
~~~~~~~~~

Use this plugin if you don't want to authenticate users of handyrep at all.

**Parameters**

username
    authentication username; ignored

userpass
    authentication password; ignored

funcname
    called API function name, ignored

**No configuration***


simple_password_auth
~~~~~~~~~~~~~~~~~~~~

This authentication plugin makes use of an admin and a read-only password, set in the config file, to authenticate everything.

**Parameters**

username
    authentication username; ignored

userpass
    authentication password

funcname
    called API function name

**Configuration**

ro_function_list
    list of API function names which are considered "read-only" and
    thus safe for users with just the read-only password

Also requires that the admin_password and read_password parameters in handyrep.conf be set.

ldap_auth
~~~~~~~~~

Authenticates users against an LDAP database.


HandyRep Availability Plugins
-----------------------------

These plugins are called to determine if the existing HandyRep is the HandyRep master server for the current cluster.  Used for high-availablity setups where HandyRep is installed on more than one machine.  Note that this does not cause HR to shut down, merely to skip the failover check.

They are added to the *master_check_method* configuration directive.

one_hr_master
~~~~~~~~~~~~~

No parameters.

No configuration.

Plugin to use if there is no possibility of two HandyRep servers on your network, and no need to check for a conflict.  Automatically succeeds.

check_last_ip_db
~~~~~~~~~~~~~~~~

No parameters.

**Configuration**

last_ip_timeout
    window of time to consider a conflict between HandyRep masters.  Interval value; acceptable time amounts are: seconds, minutes, hours.  e.g. "60 seconds"

Checks the configured handyrep table for the IP address and last update time for the handyrep status row.  If there's a different IP and it's been less than last_ip_timeout seconds, then return FAIL; otherwise, return SUCCESS.  Best values for last_ip_timeout are generally 3 to 10 times the polling interval.

If using this version, which HandyRep server wins is timing-based: "first in wins".

Polling Plugins
---------------

These plugins implement the "poll" method for HandyRep.  Each is a way of polling a PostgreSQL database server, including retries.

For the below plugins, they may have no specific configuration.  Most configuration of polling behavior is in the *failover* section of handyrep.conf.

poll_connect
~~~~~~~~~~~~

**Parameters**

servername
    required.  The name of the server to poll in the servers dictionary.

**Configuration**

No specific configuration.

Polling method to use with older versions of PostgreSQL (pre-9.3).  Polls servers by attempting to connect to the database as the "handyrep" user, then immediately disconnecting.  May return false negatives because of this.

poll_isready
~~~~~~~~~~~~

**Parameters**

servername
    required.  The name of the server to poll in the servers dictionary.

**Configuration**

isready_path
    required.  full path to the pg_isready executable on the HandyRep server.

Polling method to use for PostgreSQL 9.3 and later.  Uses pg_isready to check if the server is up.  

Archive Management Plugins
--------------------------

These plugins power the *archive_script_method* or *archive_delete_method* directive in the configuration to manage WAL archiving.  They are not called if the "archive" parameter in the configuration has been set to False.  Note that setting "archive" to False in the configuration does not change anything on the individual servers.

archive_local_dir
~~~~~~~~~~~~~~~~~

**Parameters**

servername
    server to push the archive script to

**Configuration**

archive_directory
    full path to directory where archive copies are kept
    
archive_script_path
    full path to which to write the archive executable
    
archive_template
    template to use for the archive.sh file
    
stop_archiving_file
    full path of touch file to halt archving

cleanup_archive
    boolean: whether or not to run cleanup on
    the archive directory using pg_archivecleanup
    
archivecleanup_path
    full path to pg_archivecleanup

**Extra Methods**

recoveryline
    returns archive recovery line or lines for recovery.conf
    to handyrep.py, so that it can push a recovery.conf file

poll
    does nothing; put here to support the poll() call from verify_all()

stop
    pushes a noarchiving file to the current master to halt archiving

start
    pushes a new script, plus removes the noarchiving file, in order to
    restart archiving on the master

This plugin is meant for pushing archiving scripts to servers who write archives to a directory which is locally mounted, e.g. a SAN fileshare.  Cleanup_archive can be enabled or disabled; this is so that you can avoid having premature archive truncation in a system where a SAN-mounted archive is shared among several replicas.  In that case, you probably want to create an archive_delete_method.

archive_two_servers
~~~~~~~~~~~~~~~~~~~

**Parameters**

servername
    server to push the archive script to

**Configuration**

archive_directory
    full path to directory where archive copies are kept

archive_script_path
    full path to which to write the archive executable

archive_template
    template to use for the archive.sh file

stop_archiving_file
    full path of touch file to halt archving

archivecleanup_path
    full path to pg_archivecleanup

disable_on_fail
    whether or not to automatically disable archiving if the
    replica no longer responds to ssh

**Extra Methods**

recoveryline
    returns archive recovery line or lines for recovery.conf
    to handyrep.py, so that it can push a recovery.conf file

poll
    checks if the replica is currently responding to SSH.  If not, it
    will disable archiving if disable_on_fail is set.

stop
    pushes a noarchiving file to the current master to halt archiving

start
    pushes a new script, plus removes the noarchiving file, in order to
    restart archiving on the master

This plugin is meant for pushing archiving scripts in a two-server system, where there is always one master and one replica, or less.  In such a system, each server is constantly set up to archive to the other server.

If disable_on_fail is true, then the replica is checked every Verify cycle.  If it doesn't respond to SSH, then the plugin will automatically push a noarchiving file to the master.

*WARNING* this plugin will break if there is more than one enabled replica!


archive_delete_find
~~~~~~~~~~~~~~~~~~~

**No_ _Parameters**

**Configuration**

archive_delete_hours
    number of hours of logs to retain

archive_directory
    full path directory the archive files are kept in

Note: requires an "archive" server to be set up in the servers dictionary.

Simple archive file management until which uses "find" from the Linux command line to delete all WAL files older than archive_delete_hours.  Note that file copying, moving, etc. can mess this method up.

Replica Cloning Plugins
-----------------------

The plugins control how new replicas are deployed based on creating a full file copy of the master, or "clone".  This is selected in the *clone_method* on each individual server's configuration (different replicas may have different clone methods).

clone_basebackup
~~~~~~~~~~~~~~~~

**Parameters**

servername
    server name of the replica on which a clone is to be made

clonefrom
    server name of the server to clone from.  Usually the overall master server.

reclone
    whether to overwrite any existing database which may be
    already on the target server.

**Configuration**

basebackup_path
    full path to the pg_basebasebackup executable

extra_parameters
    additional paramters to be passed to pg_basebackup, if any

Also makes use of *replication_user* from the *handyrep* section.

Does a full copy of the master to a new replica using pg_basebackup -x.  If reclone is selected, does an "rm -rf *" on the PGDATA directory on the target server first.  For this reason, this plugin will need an update before it works on Windows.

If reclone is not set, and the target server is known to HR to be a running PostgreSQL server, the plugin will fail the reclone.

Also, clone_basebackup currently does not handle tablespaces or symlinks (to WAL, for example) at all.  Nor does it create a pg_stat directory if a separate one is being used.

clone_rsync
~~~~~~~~~~~

**Parameters**

servername
    server name of the replica on which a clone is to be made

clonefrom
    server name of the server to clone from.  Usually the overall master server.

reclone
    whether to overwrite any existing database which may be
    already on the target server.

**Configuration**

rsync_path
    full path to the rsync executable on the replica

use_ssh
    boolean; whether to use SSH for rsync or not

ssh_path
    full path to the SSH executable on the replica

use_compression
    boolean; disable in order to turn off compression if
    you care more about speed than bandwidth

extra_parameters
    additional paramters to be passed to rsync, if any

Also makes use of *replication_user* from the *handyrep* section.

Also makes use of the optional *wal_location* setting for the master and replica servers.  You must add this to each server config if you want to symlink WAL to a new location.

Clones a new replica server from the replica using rsync, which is more suitable for large databases.  Assumes either passwordless/passphraseless ssh or a passwordless rsync server is expected.  Support for passwords could be added, but is not currently present.

Not currently Windows-compatible.

Clone_rsync currently does not handle tablespaces, although that could easily be added in the future.

Replica Status Plugins
----------------------

These plugins control how replica status is calculated, particularly for determining which replicas are "lagged".  They populate the *replication_status_method* directive.  All of these plugins should populate the "lag" field of each replica; whether they populate additional, non-default fields is up to you.  They should also return whether or not the replica is currently in replication.

replication_mb_lag_93
~~~~~~~~~~~~~~~~~~~~~

**Parameters**

replicaserver
    the replica for which we calculate lag

**Configuration**

None

**Extra Return Values**

lag
    replay lag in MB (approximate)

replicating
    whether or not the replica is currently in replication

This plugin calculates approximate replay lag in megabytes, using a calculation which only works with 9.3 (9.2 requires different math, and 9.1 requires different columns).  It does this by looking at pg_stat_replication on the master, so is not useful if the master is down.  If no record is found in pg_stat_replication, then the replica is determined not to be in replication.

Note that, if the "handyrep" database user is not a superuser, this plugin will report all replicas as being not in replication since it cannot read pg_stat_replication.

Replica Promotion Plugins
-------------------------

These plugins determine how a replica server is promoted, that is, turned into a new master or standalone.  They populate the *promotion_method* directive of each server configuration.  This means that different servers may have different promtion methods.

promote_pg_ctl
~~~~~~~~~~~~~~

**Parameters**

servername
    replica to be promoted

**Configuration**

pg_ctl_path
    full path to the pg_ctl executable

Promotes the replica by sending "pg_ctl promote" via SSH.


Replica Selection Plugins
-------------------------

These plugins control how a replica is selected to become the new master for auto-failover, or if the DBA does not select a specific replica for manual falover.  This is the *selection_method* directive.

select_replica_priority
~~~~~~~~~~~~~~~~~~~~~~~

**Parameters**

None

**Configuration**

None.

Makes use of the *failover_priority* field on each replica's server configuration.

**Extra Return Values**

Instead of an RD, returns a sorted list of replica server names.  If no replicas can be found, returns an empty list.

Returns all replicas with a status of "healthy" or "lagged" status, sorted first by status (so that "healthy" replicas are first), then by failover_priority.  "Unknown" replicas (ones which have been added but not verified) are also filtered out.

This is also the appropriate plugin to use if you have only one replica.

Connection Proxy Plugins
------------------------

These plugins control your connection proxy so that it points to the correct master and replica(s).  These populate the *connection_failover_method* directive.

multi_pgbouncer
~~~~~~~~~~~~~~~

**Parameters**

newmaster
    optional, the name of the new master during a failover transition.  If not supplied the master from the serverlist is selected.

**Configuration**

pgbouncerbin
    full path to the pgbouncer executable.  Used for restarting pgbouncer.

template
    the pgbouncer.ini template file for overwriting pgbouncer.ini

owner
    the system user who runs the pgbouncer process and owns its files

config_location
    the location of pgbouncer.ini

database_list
    the full list of all databases to which pgbouncer is to offer a connection.

readonly_suffix
    the string suffix to add to each database name for the read-only version of that database, to be directed to a replica.

all_replicas
    whether to supply a read-only connection to all replicas or just one.

extra_connect_param
    extra connection parameters to be added to each database definition in pgbouncer.ini

**Additional Methods**

init()
    Parameters: bouncerserver (optional).  Supports main function connection_proxy_init.  Does initial overwriting of pgbouncer.ini during a non-failover situation.

poll()
    Parameters: bouncerserver (optional).  Supports poll(), verify_all() and poll_all() by allowing polling of bouncer servers to determine availability status.

Manages one or more pgbouncer servers' connection lists.  On a failover or initialization, overwrites all pgbouncer.ini files with one generated from the template and restarts those servers.  The list of pgbouncer servers is all enabled servers in the server list with role "pgbouncer".

If all_replicas is chosen, a digit is added to the end of the readonly suffix.  Ordering of replicas is arbitrary, but will be among the enabled and running replicas at the time the plugin is called.

The included poll() method attempts to connect to each bouncer server using psql as the handyrep user and handyrep database (as configured).  pgbouncers which do not respond are marked unavailable.

multi_pgbouncer_pacemaker
~~~~~~~~~~~~~~~~~~~~~~~~~

Configuration, Parameters and Methods identical to multi_pgbouncer.

This plugin is for clusters where pgbouncer is managed by Pacemaker or some other management utility.  It does not restart pgbouncer if it's not already running, and makes the assumption that if pgbouncer is down, it's supposed to be down.  It only pushes an error if there are no pgbouncer servers running.

multi_pgbouncer_bigip
~~~~~~~~~~~~~~~~~~~~~

Parameters the same as multi_pgbouncer.

**Configuration**

Same as multi_pgbouncer, plus:

bigip_user
    sudo username for tmsh commands

tmsh_path
    full path to the tmsh executable

Also, add this to the passwords section:

bigip_password
    ssh password for the bigip server login, if required

Additionally, each pgbouncer server definition must include an ip_address field which is the bouncer's ip_address as seen by BigIP.  Also, one server must be created with the role "bigip".

Additional methods the same as multi_pgbouncer.

This configuration is for where load-balancing among pgbouncers is managed by the BigIP load-balancing utility.  In the event that a specific bouncer is not responding to configuration changes at failover, it will update BigIP to not loadbalance to that bouncer.  It does not do other updating of BigIP, except at failover time.

PostgreSQL Management Plugins
-----------------------------

These plugins control starting, stopping and restarting PostgreSQL on masters and replicas.  They are called by the *restart_method* directive in each server configuration, so choice of plugin can vary per server.  Note that the status runmode of each of these plugins is used as part of service verification.

restart_pg_ctl
~~~~~~~~~~~~~~

**Parameters**

servername
    target server name

runmode
    The service status change to be made: start, stop, faststop, restart, reload, or status.

**Configuration**

pg_ctl_path
    full path to pg_ctl executable

pg_ctl_flags
    optional; any additional flags to be passed to pg_ctl

Makes changes to PostgreSQL's running status by calling the pg_ctl command as the postgres user.

restart_service
~~~~~~~~~~~~~~~

**Parameters**

servername
    target server name

runmode
    The service status change to be made: start, stop, faststop, restart, reload, or status.

**Configuration**

service_name
    The name of the service as configured in the service manager.

Changes PostgreSQL's operation by calling the "service" utility on the target server as root.  Assumes that the service utility is controlled via "service servicename command" syntax.

The Plugin API and Writing Your Own
===================================

One of the core tenets of HandyRep is the ability to write your own plugins so that you can integrate HandyRep with whatever other software you already have in your infrastructure.  Here's the basic rules:

* all plugins go in the plugins/ directory/module
* all plugins extend the handyrepplugin template class
* every plugin consists of a module and a class which has the same name as the module
* all plugins implement the run() and test() functions.  Some may need to implement additional functions, according to plugin type.





