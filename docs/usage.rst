HandyRep General Usage
======================

HandyRep is a RESTful network service or library which manages status monitoring and failover for a single replication cluster of PostgreSQL servers.

Daemon Usage
------------

HandyRep ships with the HandyRep WSGI Daemon, which is the standard way to use HandyRep.  This Daemon runs constantly on the HandyRep server, performing scheduled checks and tasks, and responding to GET and POST requests for status information and to perform manual actions (such as cloning a new replica).  In this mode, HandyRep supplies a service-oriented interface for managing your database cluster; you run the daemon and whenever you need to make changes to the cluster, you send it commands.

Note that the Daemon is single-process; HandyRep does not currently do any multiprocess activity.

Library Usage
-------------

HandyRep can also be incorporated into a larger application as a library instead.  100% of HandyRep's functionality is accessible through the API in the HandyRep class.  See the API docs for more information.

Note that, if you use HandyRep as a library, it is up to you to manage scheduled checks and tasks, and ensure that you don't start more than one instance of the library at once.

The rest of this document assumes that you are running in Daemon mode.  If you are using HandyRep as a library, you will need to map to the appropriate API calls.

Assumptions Made by HandyRep
----------------------------

HandyRep is designed around the following assumptions about your PostgreSQL cluster, none of which are expected to change.

* One HandyRep server controls only one contiguous cluster of PostgreSQL servers (i.e. one master and zero to many replicas).
* Does not manage postgresql.conf at all
* Binary replication only
* No archive-only replication
* Assumes that hostnames are universal, not relative

If you are doing log archiving, HandyRep also makes the following assumptions:

* Only one (network or mounted) location for archiving
* Assumes that all replicas can access the same archive
* Assumes that all nodes can use the same archiving scripts, if pushing scripts is enabled
* Assumes that the postgres user does all archive work

Currently Not Implemented
-------------------------

The following features are not yet supported.  They may be in some future HandyRep version, according to demand and contributions.

* GUI web interface
* Communications protocol between HandyRep servers in an HA configuration.
* Automated re-routing of requests to the current HandyRep master in HA configurations.
* Support for pg_rewind on failback.
* Support for cascading replication.
* HandyRep log rotation.

Plugins
-------

Most of HandyRep's interactions with the servers in your cluster is carried out by various plugins, which are Python code classes in the plugins directory.  This allows HandyRep to support a variety of different platform infrastructures without changes to the core code.  For more information, see the Plugins documentation.

Configuration and Server Data Preservation
==========================================

When HandyRep is first launched (either as a Daemon, or when initialized as a library), it reads the setup in handyrep.conf for all information about your cluster setup.  After this launch, HandyRep maintains its own redundant store of server information and status data.  This information is stored in two places:

servers.save
    A JSON file on the current HandyRep server, by default named "servers.save" in the HandyRep working directory (but relocatable using handyrep.conf).

HandyRep table
    A table on your database server, located in the handyrep database and schema defined in handyrep.conf.

HandyRep will treat these as the authoritative source of information on your current server configuration over whatever is in handyrep.conf, if present. This allows HandyRep to preserve server changes without overwriting handyrep.conf, and to preserve server information even if the HandyRep server itself is lost.

If you need to override saved server information because of downtime changes, set override_server_file in handyrep.conf and then reload HandyRep.  Note that this will entirely replace any other saved server information, so make sure to enter all server configuration in handyrep.conf.

Monitoring and Failover
=======================

The primary purpose of HandyRep is to monitor the health of your cluster, and if the master fails while one or more replicas is operational, to automatically fail over to them.

Polling vs. Verification
------------------------

"Polling" is designed to be done frequently, and makes a lightweight check of the master and the replicas to see if they are still up and responding.  This allows HandyRep to poll frequently, even serveral times a minute.

"Verification" is a more resource-consumptive check which tries to test each server in several different ways, including checking for replication lag, service status, connection to the master, and other potential issues.  Since this check takes more time, it should be run less frequently, maybe once per hour.

FailoverCheck
-------------

The primary activity of HandyRep is the FailoverCheck.  If running in Daemon mode, the FailoverCheck polls the servers every poll_interval and verifies them every verify_interval.  If the master fails, and one or more replicas is operating ("healthy" or "lagged"), FailoverCheck will attempt failover.

Additional failover logic applies, some of which is controlled by configuration variables.  See the configuration documentation, and the failover logic diagram for more information.

There are also separate Poll and Verify checks if you want to check the status of a server without necessarily triggering Failover.

Status
------

HandyRep maintains status information about the master, the replicas, and the overall cluster which can be referenced by monitoring utilities and for administrator dashboards.  See "Status Information" in the API docs for more details about the various statuses and what they mean.

Log
---

HandyRep keeps a log of all of its actions, at a location configured in handyrep.conf.  The tail of this log is available via the API so that you can check recent actions including failover.




