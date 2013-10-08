-- users and database for the libdata database

CREATE ROLE libdata PASSWORD 'books' LOGIN;

CREATE DATABASE libdata;

ALTER DATABASE libdata OWNER TO libdata;

ALTER ROLE postgres PASSWORD 'superuser';

CREATE ROLE bench PASSWORD 'benchmark' LOGIN CREATEDB;

