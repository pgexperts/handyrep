HandyRep
========

HandyRep is a server-based tool designed to allow you to manage a PostgreSQL "replication cluster", defined as a master and one or more replicas on the same network.  It is distinct from other PostgreSQL replication management tools in the following ways:

1. Written entirely in Python, for easy hackability
2. All functionality is accessable either as a Python library, or using a REST interface with the optional Flask application
3. Supports user-supplied plugins to let it interface with applications in your environment.
4. Supports automated failover logic for high availability

Among its other useful features and advantages are:

* Can be run from a 3rd-party server (such as a pgbouncer server)
* Can be run in a failover configuration, with a 2nd Handyrep server which doesn't accept commands (future planned feature).
* Designed to minimize the per-node installation/configuration requirements.  No "agent" is installed on the nodes.
* Supports multiple replicas and remastering
* Integrates 3rd-party connection failover

Further documentaton is found in the Docs folder.

Support and Collaboration
=========================

Discussion of HandyRep usage and development can be found on the HandyRep
Google Group: http://groups.google.com/d/forum/handyrep

The HandyRep project is located at http://handyrep.org

Copyright
=========

HandyRep is copyright 2013-2014 PostgreSQL Experts Inc.  Portions copyright its individual contributors.

It is available under The PostgreSQL License.  See LICENSE.txt for details.

Trademark
=========

The HandyRep name, HandyRep logo, and PGX Logo are trademarks of PostgreSQL Experts Inc.  Permission to use
these trademark is granted provided that such use is in reference to PostgreSQL Experts, the HandyRep Project,
software packages composed of the HandyRep Project's code, or usage or forks of the HandyRep Project code.  
You may not state or imply, through such usage, ownership of these trademarks, or endorsement
of any product, service, organization, or person by the HandyRep Project or PostgreSQL Experts Inc. 
Any other use requires written permission by PostgreSQL Experts, Inc.