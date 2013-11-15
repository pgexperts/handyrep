-- users and databases for testing handyrep

CREATE ROLE replicator WITH replication;
CREATE ROLE handyrep WITH login superuser;
CREATE ROLE libdata WITH login createdb;
CREATE ROLE bench WITH login createdb;
CREATE DATABASE libdata;
CREATE DATABASE bench;
CREATE DATABASE handyrep;

