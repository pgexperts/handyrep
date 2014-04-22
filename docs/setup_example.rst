Example Setup Narrative
=======================

Sally Admin is setting up HandyRep to provide high-availability for a four-server cluster, which contains:

* db01: Initial PostgreSQL master
* db02: Initial PostgreSQL replica
* pgb01: pgBouncer server 1, and handyrep server
* pgb02: pgBouncer server 2

Sally has the following server environment:

* Ubuntu 12.04
* PostgreSQL 9.3.4
* Apache/mod_wsgi
* Relatively small database ("app-prod")
* No archiving/DR set up at this time (relying on pgdumps)
* HandyRep doesn't modify external load-balancing for the pgbouncer servers.
* No auto-vivification for Postgres service
* Using SaltStack for configuration management.

She's also working under the following requirements:

* 5 minute failover window
* Up to 1 minute of data loss permitted

Setting up pgb01
----------------

Sally installs the following from apt-get (using apt.postgresql.org for some):

* PostgreSQL-9.3-client
* pgbouncer
* python-pip
* psycopg2
* Apache
* mod_wsgi

In order to get current versions, she installs the following into a virtualenv using pip:

* flask and related requirements for the GUI
* fabric
* ConfigObj
* jinja2

She then creates a "handyrep" user with its own home directory, and adds that user to the "admins" group.  She uses visudo to modify the admins group to not require a password for sudo.  

Switching to the handyrep user, she generates an ssh key, and then copies that public key to that user's authorized_keys on all servers. She then downloads the handyrep code and installs it at /srv/handyrep, and the handyrepGUI code at /srv/handyrepGUI.

Setting up db01
----------------

Sally installs postgresql 9.3 from apt-get on the master.  

She then sets up PostgreSQL on the master, setting it up for replication.  This includes the following settings which she sets up in Salt as templates:

::

    In postgresql.conf.conf:
        wal_level = hot_standby
        max_wal_senders = 6

    In pg_hba.conf:
        host    replication     postgres   192.168.100.0/24   md5
        

In Salt, she starts up PostgreSQL, and adds the user "handyrep" as a superuser.  She also adds the handyrep shell user and its ssh authorized keys, and adds it to sudoers.

To be continued ...




