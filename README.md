HandyRep
========

HandyRep is a server-based tool designed to allow you to manage a PostgreSQL "replication cluster", defined as a master and one or more replicas on the same network.  It is distinct from other PostgreSQL replication management tools in the following ways:

1. Written entirely in Python, for easy hackability
2. All functionality is accessable either as a Python library, or using a REST interface with the optional uWSGI server
3. Supports user-supplied plugins to let it interface with applications in your environment.
4. Supports automated failover logic for high availability

Among its other useful features and advantages are:

* Can be run from a 3rd-party server (such as a pgbouncer server)
* Can be run in a failover configuration, with a 2nd Handyrep server which doesn't accept commands.
* Designed to minimize the per-node installation/configuration requirements.  No "agent" is installed on the nodes.
* Supports multiple replicas and remastering
* Integrates 3rd-party connection failover

Further documentaton is found in the Docs folder.

Copyright
=========

HandyRep is copyright 2013 PostgreSQL Experts Inc.  Portions copyright its individual contributors.

It is available under The PostgreSQL License.  See LICENSE.txt for details.