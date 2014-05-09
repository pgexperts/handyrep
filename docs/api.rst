HandyRep Library API
====================

Web vs. Library Access
----------------------

The API below is the full library API for importing HandyRep as a class.
The vast majority of these functions are also available via the web API, with
identical parameters as described.  A few functions are marked as
"Not available in web API".

General
=======

Initialization
--------------

If calling HandyRep as a library, it needs to be initialized.  In the
web services version, this is the reason for the daemonfunctions.py module.

::
    HandyRep
        config_file filename default 'handyrep.conf'

    from handyrep import HandyRep
    hr = HandyRep('handyrep.conf')

config_file
    The configuration file for the handyrep cluster.  If not
    supplied, defaults to the file 'handyrep.conf' in the working
    directory.  Can be an absolute path, or relative to the
    handyrep working directory.

Initialization will fail if the configuration file does not exist or
is malformatted.

Return Types
------------

All APIs return dictionaries, for easy conversion to JSON and other formats.  In the
web API, these are returned as JSON but have identical layout. Most of the
time, this return is in the format of the "return dictionary", or RD:

::
    { "result" : "FAIL"
      "details" : "could not ssh to master" }

An RD always contains to keys: "result" which is either "SUCCESS" or "FAIL", and "details"
which has human-readable output about the success or failure.  Often, for a success, "details" will be a zero-length string.  RDs may have other, additional keys depending on the API function called.

Some functions return dictionaries which are not RDs, primarily functions which provide
data for display.  All strings are unicode by default.

Information API
===============

The information API consists of functions designed to provide the administrator or
monitoring software with information about the status of various cluster resources.

Status Information
------------------

HandyRep tracks status at two levels: for the cluster as a whole, and for each
individual server.  In both cases, status information consists of four fields:

status
    one of "unknown","healthy","lagged","warning","unavailable", or "down".
    see below for explanation of these statuses.
    
status_no
    status number corresponding to above, for creating alert thresholds.
    
status_ts
    the last timestamp when status was checked, in unix standard format
    
status_message
    a message about the last issue found which causes a change in status.
    May not be complete or representative.

The list of statuses for the cluster as a whole is as follows:

0 : "unknown"
    status checks have not been run.  This status should only exist for a very short time.
    
1 :  "healthy"
    cluster has a viable master, and all replicas are "healthy" or "lagged"
    
3 : "warning"
    cluster has a viable master, but has one or more issues,
    including connnection problems, failure to fail over, or
    downed replicas.
    
5 : "down"
    cluster has no working master, or is in an indeterminate state
    and requires administrator intervention

Statuses for individual servers are as follows:

0 :  "unknown"
    server has not been checked yet
    
1 : "healthy"
    server is operating normally
    
2 : "lagged"
    for replicas, indicates that the replica is running but has
    exceeded the configured lag threshold
    
3 : "warning"
    server is operating, but has one or more issues, such as
    inability to ssh, or out-of-connections.
    
4 : "unavailable"
    cannot determine status of server because we cannot connect
    to it.
    
5 : "down"
    server is verified down.

server roles
------------

Servers each assigned a "role" which is required (as is a hostname).  Currently defined roles are:

master
    current or past PostgreSQL replication master

replica
    current or past PostgreSQL replica database

proxy
    current or past connection proxy for database connections

pgbouncer
    same as "proxy", just specifically pgbouncer

archive
    server/storage which only holds archive files.  Note that archive servers
    are not polled, so status information is not updated.

Servers can be created with other, user-defined roles, and certain plugins may create servers with additional roles.  In general, servers with roles other than the first four above will not be polled or verified, and as a result their "status" information will be meaningless.


get_status
----------

Returns dictionary of all status information for the cluster.

:: 
    get_status
        check_type [default "cached", "poll", "verify"]

*check_type*
    allows you to specify that the server is to poll or fully verify all servers
    before returning status information.  Defaults to "cached", which means just
    return information from HandyRep's last check

return:

::
    { cluster : { cluster status fields }
      servers : { server1 : { server1 hostname and status info },
                  server2 : { server2 status info } ...
    }

example:

::

    hr.get_status()
    
    {'cluster': {u'status': u'warning', u'status_ts': u'2013-11-14 03:57:43', u'status_message': u'1 replicas are down', u'status_no': 3}, 'servers': {u'paul': {u'status': u'unavailable', u'status_ts': u'2013-11-14 03:57:43', u'hostname': u'paul', u'enabled': True, u'role': u'replica', u'status_message': u'server not responding to polling', u'status_no': 4}, u'john': {u'status': u'healthy', u'status_ts': u'2013-11-14 00:35:49', u'hostname': u'john', u'enabled': True, u'role': u'master', u'status_message': u'master responding to polling', u'status_no': 1}}}

get_cluster_status
------------------

Like get_status, but returns only the cluster status fields.

::

    get_cluster_status
        verify Boolean default False

verify
    whether to verify all cluster data, or to just return cached
    data.  Default (False) is to use cached.

Returns status dictionary: status, status_no, status_ts, status_message.

    
get_master_name
---------------

Returns the name of the current master.

::

    get_master_name

Returns the name of the current master.  If there is no configured master,
or if the master has been disabled, returns None.

get_server_info
---------------

Returns server configuration and status details for the named server(s).

::

    get_server_info
        servername ServerName default None
        verify Boolean default False

servername
    The server whose data to return.  If None, return a
    dictionary of all servers.

verify
    Whether to verify all server data first.  Default is to
    use cached data.

Returns dictionary of servers

::

    { servername: { server details } }

Example:

::

    hr.get_server_info("john", False)
    
    { "john": {
        "status": "healthy",
        "status_ts": "2014-02-02 07:24:34",
        "lag_limit": 1000,
        ...
        "hostname": "john",
        "promotion_method": "promote_pg_ctl"
    } }

read_log
--------

Retrieves the last N lines of the handyrep log and presents them as a list in reverse chonological order.

::

    read_log
        numlines Integer default 20

numlines
    how many lines of the log to retrieve


get_setting
-----------

Retrieves a single configuration setting.

::

    get_setting
        setting_name string OR list

setting_name
    can be either a string for a single setting, or a list which is the full path
    to that setting in conf.  If just a string, the setting is assumed to be in the
    "handyrep" section.

Note: the Web API has a slightly different version of this function, which can't return
settings from nested sections:

::

    get_setting
        category string default "handyrep"
        setting string

category
    section of the config

setting
    the individual setting name

In either case, get_setting will refuse to return anything in the "passwords" section.

set_verbose
-----------

Toggles verbose logging.

::

    set_verbose
        verbose boolean default True


Availability API
================

The availability API are a set of functions related to maintaining uptime
of the cluster.  They include functions for polling servers and for failover.
Some central concepts:

* "poll" means to use the lightweight polling method to check servers, whereas "verify" does a more complete (and time-consuming) check that servers are fully operational.
* the cluster is considered "available" if the master is running and healthy, even if we have no replicas.
* program logic is designed to avoid false positives; if the status of a server cannot be unambiguously determined, it simply sounds the alarm
and aborts rather than performing an unnecessary failover.

failover_check
--------------

Core function of HandyRep.  Intended to be run every few seconds or minutes
to check if a failover is required and update the status of all servers.
Wraps most of the other availability functions.  Updates the status
dictionary.  Performs an auto_failover if a failover is required,
and if auto_failover is configured.

This function is not available through the Web API, is it is invoked only
by the Periodic portion of that daemon.

::

    failover_check
        verify Boolean, default False

verify
    should we run a full verification on all servers before checking
    for failover, or just a poll?

Returns RD

SUCCESS
    current master is now healthy and running,
    or we successfully failed over and the new master
    is good, or this is not the HR master.

FAIL
    master is down, we could not restart it, not safe to fail over,
    failover failed, or an unforseen issue occurred.  Check details.

The failover check is intended to be run for each polling interval from
handyrep.conf.  Generally one runs with verify=False more frequently (the poll_interval), and verify=True less frequently (the verify_interval).


poll_master
-----------

Uses the configured polling method to check the master for availability.
Updates the status dictionary in the process.  Can only determine up/down,
and cannot determine if the master has issues; as a result, will not
change "warning" to "healthy".  Also checks that the master is actually
a master and not a replica.

::

    poll_master

Returns RD

SUCCESS:
    current master is responding to polling

FAIL:
    current master is not responding to polling, or the handyrep or polling
    method configuration is wrong

poll
----

Uses the configured polling method to check the designated server for availability.
Updates the status dictionary in the process.  Can only determine up/down,
and cannot determine if the master has issues; as a result, will not
change "warning" to "healthy".

::

    poll
        servername

Returns RD

SUCCESS:
    server is responding to polling

FAIL:
    server is not responding to polling, or the handyrep or polling
    method configuration is wrong

poll_all
--------

Polls all servers using the configured polling method.  Also checks
the number of currently enabled and running masters and replicas.
Intended to be part of availablity checks.  Updates the status dictionary.

::

    poll_all

Returns RD with extra fields

SUCCESS
    The master is running.

FAIL
    The master is down, or no master is configured, or multiple masters are
    configured.

failover_ok
    Boolean field indicating whether it is OK to fail over.  Basically a check
    that there is one master and at least one working replica.

verify_master
-------------

Checks the master server to make sure it's fully operating, including checking
that we can connect, we can write data, and that ssh and control commands
are available.  Updates the status dictionary.

Not available in web API, see "verify_server" below.

::

    verify_master

Returns RD with extra fields

SUCCESS
    the master is verified to be running, although it may have known
    non-fatal issues.

FAIL
    the master is verified to be not running, unresponsive, or may be
    blocking data writes.

ssh
    text field, which, if it exists, shows an error message from attempts
    to connect to the master via ssh

psql
    text field which, if it exists, shows an error message from attempts
    to make a psql connection to the master

verify_replica
--------------

Checks that the replica is running and is in replication.  Also checks
that we can connect to the database and that we have a working
control connection for the server.  Uses the replication_status plugin.  Updates the status dictionary.

Not available in web API, see "verify_server" below.

::

    verify_replica
        replicaname

Returns RD with extra fields

SUCCESS
    the replica is verified to be running, although it may have known
    non-fatal issues.

FAIL
    the replica is verified to be not running, unresponsive, or may
    be running but not in replication

ssh
    text field, which, if it exists, shows an error message from attempts
    to connect to the master via ssh

psql
    text field which, if it exists, shows an error message from attempts
    to make a psql connection to the master

verify_server
-------------

Shell function for verify_replica and verify_master, which checks the role
of the server and then runs the appropriate check.

This function is available through the Web API as the way to access verify_master or verify_replica.

verify_all
----------

Does complete check of all enabled servers in the server list.  Updates
the status dictionary.  Returns detailed check information about each
server.

::

    verify_all

Returns RD with extra fields

SUCCESS
    the master is up and running

FAIL
    the master is not running, or master configuration is messed up
    (no masters, two masters, etc.)

failover_ok
    at least one replica is healthy and available for failover

servers
    dictionary includes a key for each checked server, with the
    details of the verification check


Action API
==========

A set of API functions designed to be called manually by user input.
Intended for management of your handyrep cluster.

init_handyrep_db
----------------

Creates the initial handyrep schema and table.  

::

    init_handyrep_db

Returns an RD.  Fails if it cannot connect to the master, or does not have permissions to create schemas and tables, or if the cited database does not exist.

reload_conf
-----------

Reload handyrep configuration from the handyrep.conf file.  Allows changing of configuration files.

::

    reload_conf
        config_file FilePath default 'handyrep.conf'

config_file
    File path location of the configuration file.  Defaults to the
    previous config location, or to 'handyrep.conf' in the working directory if there is no prior location.

Returns RD

Note: this does not cause a change to servers configuration unless
"override_server_file" is set to True in the new configuration
file itself.


shutdown
--------

Shut down the designated server.  Checks to make sure that the server
is actually down.

::
    shutdown
        servername server name

servername
    the name of the server to shut down.  required

Returns RD

SUCCESS
    the server is shut down

FAIL
    the server will not shut down.  check details.

startup
-------

Starts the designated server.  Checks to make sure that the server
is actually up.

::
    startup
        servername server name

servername
    the name of the server to start.  required

Returns RD

SUCCESS
    the server is running

FAIL
    the server will not start.  check details.

restart
-------

restarts the designated server.  Checks to make sure that the server
is actually up.

::
    restart
        servername server name

servername
    the name of the server to restart.  required

Returns RD

SUCCESS
    the server is running

FAIL
    the server will not restart.  check details.

promote
-------

promotes the designated replica to become a master or standalone.  Does
NOT do other failover procedures.  Does not prevent creating two masters.

::
    promote
        newmaster server name

newmaster
    the name of the server to promote.  required

Returns RD

SUCCESS
    the server has been promoted

FAIL
    the server could not be promoted.  check details.
    

manual_failover
---------------

Fail over to a new master, presumably for planned downtimes, maintenance,
or server migrations.

::
    manual_failover
        newmaster ServerName, default None
        remaster Boolean, default None

newmaster
    Server to fail over to.  If not supplied, use the same master
    selection process as auto-failover.

remaster
    Whether or not to remaster all other servers to replicate from the new
    master.  If not supplied, setting in handyrep.conf is used.

SUCCESS
    failed over to the new master successfully.  Check details in case
    postfailover commands failed.

FAIL
    unable to fail over to the new master. Cluster may have been left in
    an indeterminate state.  check details.

clone
-----

Create a clone from the master, and starts it up.  Uses the configured cloning method and plugin.

::
    clone
        replicaserver ServerName
        reclone Boolean default False
        clonefrom ServerName default None

replicaserver
    the new replica to clone to

reclone
    Whether to clone over an existing replica, if any.  If set to False (the default), clone will abort if this server has an operational PostgreSQL on it.

clonefrom
    The server to clone from.  Defaults to the current master.

Returns RD:
    
SUCCESS
    the replica was cloned and is running

FAIL
    either cloning or starting up the new replica failed, or
    you attempted to clone over an existing running server

Notes: the clone command does not install PostgreSQL binaries, create the
directories on the server, or configure postgresql.conf, so those things
need to be already done before cloning.

enable
------

Enable a server definition already created.  Also verifies the server defintion.

::

    enable
        servername ServerName

servername
    the server to enable

Returns RD:

SUCCESS
    the server was enabled

disable
-------

Mark an existing server disabled so that it is no longer checked.
Also attempts to shut down the indicated server.

::

    disable
        servername ServerName

servername
    the server to disable

SUCCESS
    the server was disabled

remove
------

Delete the definition of a disabled server.

::

    remove
        servername ServerName

Returns RD:

SUCCESS
    the server defintion was deleted

FAILURE
    the server definition is still enabled, so it can't
    be deleted


alter_server_def
----------------

Change details of a server after initialization.  Required
because the .conf file is not considered the canonical
information about servers once servers.save has been created.

::

    alter_server_def
        servername ServerName
        serverprops

servername
    The existing server whose details are to be changed.

serverprops
    a set of key-value pairs for settings to change.  Settings
    may be "changed" to the existing value, so it is permissible
    to pass in an entire dictionary of the server config with
    one changed setting.

Note that serverprops may need special handling in the Web API, since URLs only
accept strings.  See the Web Service Daemon documentation.

Returns RD with extra fields:

definition
    the resulting new definition for the server

add_server
----------

Add a new server to a running handyrep.  Needed because handyrep.conf
is not considered the canonical source of server information once
handyrep has been started.

::

    add_server
        servername string
        serverprops

servername
    The existing server whose details are to be changed.

serverprops
    a set of key-value pairs for server settings.  Note that the
    hostname setting is required, and the new server will be
    rejected without it.

Note that serverprops may need special handling in the Web API, since URLs only
accept strings.  See the Web Service Daemon documentation.

New servers are always added as "disabled", and need to be enabled as a
separate action.  Further, "role" defaults to "replica" if not supplied.

Returns RD with extra fields:

definition
    the resulting new definition for the server

connection_proxy_init
---------------------

Set up the connection proxy configuration according to the configured
connection failover plugin.  Not all connection proxy plugins support initialization.

::

    connection_proxy_init

Returns RD:

SUCCESS
    proxy configuration pushed, or connection failover is not
    being used

FAIL
    error in pushing new configuration, or proxy does not support
    initialization
    

cleanup_archive
---------------

Delete old WALs from a shared WAL archive, according to the
expiration settings in handyrep.conf.  Uses the configured
archive deletion plugin, if any.

::

    cleanup_archive

Returns RD:

SUCCESS
    archives deleted, or archiving is disabled so no action taken.

FAIL
    archives could not be deleted, possibly because of a permissions
    or configuration issue.

Note: generally this method would be called by a cron job.

start_archiving
---------------

Start archiving on the master.

::

    start_archving

Returns RD:

SUCCESS
    archiving should be enabled

FAIL
    either archving is not configured, or was unable to modify the master.

This call will push an archive.sh script and remove any noarchiving file, if defined and present (all of this is via plugin methods).  It does not set archiving=on in postgresql.conf, so if archiving has not begun after running this, that's the first thing to check.

stop_archiving
--------------

Stops copying of WAL files on the master.

::

    stop_archving

Returns RD:

SUCCESS
    noarchving flag is set, or archiving is otherwise disabled

FAIL
    could not disable archiving, either because it is not configured, or because
    there's something wrong with the master.

Implemented via the archving plugin.  Most archving plugins implement this via a noarchving touch file.  This does mean that if the master's disk is 100% full, it will not work.


