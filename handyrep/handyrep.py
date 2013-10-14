import fabric
from lib.utils import HandyRepUtils
from lib.config import ReadConfig
from lib.error import CustomError
from plugins.plugins import Plugins
import json
from datetime import datetime, timedelta
import logging

class HandyRep(Object):

    def __init__(config_file='handyrep.conf'):
        # read and validate the config file
        config = ReadConfig(config_file)
        self.conf = config.read()
        self.servers = {}
        self.tabname = """ "%s"."%s" """ % (self.conf["handyrep"]["handyrep_schema"],self.conf["handyrep"]["handyrep_table"],)
        self.sync_config(False)
        self.serv_updated = None
        self.status = "OK"
        # return a handyrep object
        return self

    def check_hr_master(self):
        # check plugin method to see
        hrs_method = self.get_plugin(self.conf["handyrep"]["master_check_method"])
        # return result
        hrstatus = hrs_method(*self.conf["handyrep"],["master_check_parameters"])
        return hrstatus

    def verify_servers(self, update_defs = True):
        # check each server definition against
        # the reality
        allgood = True
        for someserver, servdetails in self.servers.iteritems():
            if servdetails["enabled"]:
                if servdetails["role"] == "master":
                    if not verify_master(someserver):
                        allgood = False
                else:
                    if not verify_replica(someserver)
                        allgood = False
            # return false if serverdefs don't match
            # success otherwise
        return allgood

    def read_serverfile(self):
        try:
            servfile = open(self.conf["handyrep"]["server_file"],'r')
        except:
            return None
        else:
            serverdata = json.load(servfile)
            servfile.close()
            return serverdata

    def init_handyrep_db(self):
        # initialize the handrep schema
        # per settings
        # we assume that if the table exists
        # the functions do too
        htable = self.conf["handyrep"]["handyrep_table"]
        hschema = self.conf["handyrep"]["handyrep_schema"]
        mconn = master_connection()
        mcur = mconn.cursor()
        has_tab = self.get_one_value(mcur, """SELECT count(*) FROM
            pg_stat_user_tables
            WHERE relname = %s and schemaname = %s""",(htable, hschema,))
        if not has_tab:
            # need schema test here for 9.2:
            has_schema = self.get_one_value(mcur, """SELECT count(*) FROM pg_namespace WHERE nspname = %s""",(htable,))
            if not has_schema:
                self.execute_it(mcur, """CREATE SCHEMA "%s" """ % hschema, [], "Unable to create the handyrep schema")

            self.execute_it(mcur, """CREATE TABLE %s ( updated timestamptz, config JSON, servers JSON )""" % self.tabname, [], "Unable to create handrep table")
            self.execute_it(mcur, "INSERT INTO" + tabname + " VALUES ( %s, %s, %s )""",(self.serv_updated, json.dumps(self.conf), json.dumps(self.servers),))
            mcur.execute("""SET SEARCH_PATH="%s",public,pg_catalog""" % hschema)
            
            # load all functions in the functions directory
            self.run_sql_dir(mcur, self.conf["handyrep"]["functions_dir"])

        # done
        mconn.commit()
        mconn.disconnect()
        return True

    def sync_config(self, write_servers = False):
        # read serverdata from file
        # this function does a 3-way sync of data
        # looking for the very latest server configuration
        # between the config file, the servers.save file
        # and the database
        serverdata = read_serverfile()
        confupdate = datetime.strptime(self.conf["timestamp"]["last_updated"],'%Y-%m-%d %H:%M:%S')
        # compare dates on serverdata vs config file
        if serverdata:
            servdate = datetime.strptime(serverdata["updated"],'%Y-%m-%d %H:%M:%S')
            if servdate > confupdate:
                self.servers = serverdata
                self.serv_updated = servdate
            else:
                self.serverdefaults()
                self.serv_updated = confupdate
        else:
            self.serverdefaults()
            self.serv_updated = confupdate
            
        # open the handyrep table on the master
        utils = HandyrepUtils(self.conf, self.servers)
        sconn = utils.best_connection()
        scur = sconn.cursor()
        dbconf = get_one_row(scur,"""SELECT * FROM %s """ % self.tabname)
        if dbconf:
            # if handyrep table more updated
            #supercede local servers.save
            dbdate = dbconf[0]
            if dbdate > supdate:
                self.servers = json.loads(dbconf[2])
                self.serv_update =
            # save all files
        else:
            self.init_handyrep_db()
        if write_servers:
            self.write_servers()
        # return true if changes synced
        return true

    def write_servers(write_table=True):
    # write server data to all locations
        # update date
        self.servers
        # write server data to file
        servfile = open(self.conf["handyrep"]["server_file"],"w")
        json.dump(self.servers, servfile)
        servfile.close()
        # write server data to table
        if write_table:
            try:
                sconn = master_connection()
            except:
                raise CustomError("DBCONN","Unable to sync configuration to database due to failed connection to master")
            scur = sconn.cursor()
            dbconf = get_one_row(scur,"""SELECT * FROM %s """ % self.tabname)
            if dbconf:
                if dbconf[0] < self.serv_updated
                try:
                    cur.execute("UPDATE " + tabname + """ SET updated = %s,
                    config = %s, servers = %s""",(self.serv_updated, json.dumps(self.conf), json.dumps(self.servers),))
                except Exception as e:
                        # something else is wrong, abort
                    sconn.disconnect()
                    raise CustomError("DBCONN","Unable to write HandyRep table to database for unknown reasons, please fix: %s" % e.pgerror)
            else:
                self.init_handyrep_db()
            sconn.commit()
            sconn.disconnnect()
        return True

    def serverdefaults(self):
        # loop through servers and server defaults
        # assigning defaults where individual servers don't
        # have settings
        # then assign the group to "servers"
        self.servers = self.conf["servers"]
        for sdefkey, sdefval in self.conf["server_defaults"].iteritems():
            if sdefval is not None:
                for servname, servsets in self.servers.iteritems():
                    if sdefkey in servsets:
                        if servsets[sdefkey] is None:
                            servsets[sdefkey] = sdefval
                    else:
                        servsets[sdefkey] = sdefval
                    self.servers[servname]["status"] = "unknown"
                    
        return

    def get_master_name(self):
        for servname, servdata in self.servers.iteritems():
            if servdata["role"] == "master" and servdata["enabled"]:
                return servname

        # no master?  raise error
        raise CustomError("CONFIG","No currently enabled master is configured")

    def poll_master(self):
        # check master using poll method
        poll = get_plugin(self.conf["failover"]["poll_method"])
        master = get_master_name()
        check = poll(self.conf, self.servers, master)
        return check

    def poll_server(self, replicaserver):
        # check replical using poll method
        poll = get_plugin(self.conf["failover"]["poll_method"])
        check = poll(self.conf, self.servers, replicaserver)
        return check

    def verify_master(self):
        # connect to master
        mconn = None
        try:
            mconn = self.master_connection()
        except Exception as e:
            log_activity("Connection to master failed %s" % e.message, True)
            if mconn is not None:
                mconn.disconnect()
            self.servers[self.get_master_name()]["status"] = ["unavailable"]
            return False
        mcur = mconn.cursor()
        # check that you can do a simple write
        try:
            mcur.execute("""UPDATE %s SET updated = updated""" % self.tabname);
        except Exception as e:
            log_activity("Unable to write to master database: %s" % e.pgerror,True)
            mconn.disconnect()
            self.servers[self.get_master_name()]["status"] = ["unavailable"]
            mconn.disconnect()
            return False
        # return success
        mconn.disconnect()
        self.servers[self.get_master_name()]["status"] = ["healthy"]
        return True

    def verify_replica(self, replicaserver):
        # check that you can connect
        # returns status information:
        try:
            rconn = self.connection(replicaserver)
        except Exception as e:
            log_activity("Connection to replica %s failed %s" % (replicaserver, e.message,), True)
            self.servers[replicaname]["status"] = "unavailable"
            return False
        # check that it's in replication
        rcur = rconn.cursor()
        if not self.is_replica(rcur):
            rconn.disconnect()
            self.servers[replicaname]["status"] = "non-replica"
            return False
        rconn.disconnect()
        # check that it's seen from master
        # this will error out if we can't reach the
        # master
        mconn = self.master_connection()
        mcur = mconn.cursor()
        repinfo = get_one_row(mcur, """SELECT lag_mb FROM pg_replica_status(%s)""",(replicaserver,))
        mconn.disconnect()
        if not repinfo:
            self.servers[replicaname]["status"] = "disconnected"
            return False
        # check replica lag
        self.servers[replicaname]["lag_mb"] = repinfo[0]
        if repinfo[0] > self.servers[replicaname]["lag_limit"]:
            self.servers[replicaname]["status"] = "lagged"
            return False
        else
            self.servers[replicaname]["status"] = "healthy"
        return True
        # otherwise, return success

    def is_master(self, servername):
        if self.servers[servername]["role"] == 'master' and self.servers[servername]["enabled"]:
            return True
        else:
            return False

    def list_servers(self, verify=True):
        # list all servers and their current info/status
        # returns JSON information

    def get_server_status(self, servername, verify=True):
        # returns server info as JSON
        
        # return all status info

    def failover_check(self, verify=False):
        # check if we're the hr master:
        if not self.check_hr_master():
            return "Not Handyrep Master"
        # poll master
        for checknum in range(1,self.conf["failover"]["fail_retries"] + 1)
            if verify:
                result = self.verify_master()
            else:
                result = self.poll_master()
            if result:
                break
        # if failed, failover
        if not result:
            self.status = "down"
            # try to restart the master if configured
            if self.conf["failover"]["restart_master"]:
                if self.restart_master():
                    self.status = "OK"
                    return "OK"
            failres = self.failover()
            return failres
        # return
        self.status = "OK"
        return "OK"

    def restart_master(self):
        # attempt to restart the master on the
        # master server
        master = self.get_master_name()
        restart_cmd = self.get_plugin(self.servers[master]["restart_method"])
        if restart_cmd(self.conf, self.servers):
            # wait recovery_wait for it to come up
            tries = (self.conf["failover"]["recovery_wait"] / self.conf["failover"]["fail_retry_interval"])
            for mpoll in range(1,tries):
                if poll(master):
                    self.servers[master]["status"] = "healthy"
                    self.write_servers()
                    

        self.servers[master]["status"] = "down"
        self.write_servers(False)
        return False

    def failover(self, newmaster=None, remaster=None):
        # if newmaster isnt set, poll replicas for new master
        # according to selection_method
        oldmaster = self.get_master_name()
        self.status = "failing over"
        if not newmaster:
            newmaster = self.select_new_master()
        # if remaster not set, get from settings
        if not remaster:
            remaster = self.conf["failover"]["remaster"]
        # attempt STONITH
        if not self.stonith(oldmaster):
            # if failed, abort and reset
            self.status = oldstatus
            raise CustomError("FAILOVER","Unable to shut down old master, aborting")
        # attempt replica promotion
        promotion = self.promote(newmaster)
        if promotion:
            # if success, update servers.save
            self.status = 'OK'
            # if remastering, attempt to remaster
            if remaster:
                for servername, servinfo in self.servers.keys():
                    if servinfo["role"] == "replica" and servinfo["enabled"]:
                        self.remaster(servname, newmaster)
            # run post-failover scripts
            self.postfailover()
            result = "OK"
        else:
            # if failed, try to abort and reset
            self.restart_master()
            self.shutdown(newmaster)
            self.status = "failed"
            result = "failed"
        # update servers.save
        self.write_servers()
        return result

    def stonith(self, oldmaster):
        # test if we can ssh to master
        
            # check if PG is running
            # if so, run shutdown
            # if shutdown fails, error out
        # test if master IP is up

    def promote(self, newmaster):
        # test access to new master
        # can we ssh?
        # is it running?
        # is it a replica?
        # if all true, send promote command
        # return true if successful, otherwise error

    def remaster(self, replicaserver, newmaster=None):
        # use master from settings if not supplied
        # change replica config
        # restart replica
        # check for fail
        # sync server config

    def clone(self, replicadict, clonefrom=None):
        # use config master if not supplied
        # abort if this is already a replica
        # clone using clone_method
        # write recovery.conf
        # start replica
        # update servers.save
        # check replica status to make sure it's up
            # updates servers.save and fail if not
        # report success

    def reclone(self, replicaserver, clonefrom=None):
        # check server config
        # shutdown replica, if required
        # clone using clone_method, with delete flag if necessary
        # write recovery.conf
        # write servers.save
        # start up replica
        # check status
            # update servers.save on fail
        # return success

    def shutdown(self, servername):
        # shutdown server
        # poll for shut down
        # update server info

    def remove(self, replicaserver):
        # shutdown replica
        # remove from servers.save

    def get_server_info(self, servername=None, format="json", sync=True):
        # formats: json, yaml
        # if sync:
            # verify_servers
            # sync_config if changed
        # if all, return all servers
        # otherwise return just the one

    def get_server_role(self, serverrole, format="json", sync=True):
        # formats: json, yaml
        # roles: master, replicas
        # if sync:
            # verify_servers
            # sync_config if changed
        # return master if master
        # if replicas, return all replicas

    def change_server(self, servername, serverdict, isnew=false):
        # verify servers
        # validate new settings
        # check for settings we don't do, like recloning
        # check each setting against the existing settings for the server
        # for changed settings & new servers
            # does the setting need to be pushed to the server?
            # if so, push it to the server
            # check for success; error out on fail
        # sync server config
        # exit with success

    def clean_archive(self, expire_hours=None, archivedict=None):
        # if not archive details, then
        # use config
        # delete files from archive which are older
        # than setting

    def push_replica_conf(self, replicaserver):
        # write new recovery.conf per servers.save
        # restart the replica
        # report success

    def push_archive_script(self, masterserver):
        # write a wal_archive executable script
        # to the replica

    def use_plugin(self, pluginname, parameters):
        # call method from the plugins class

    def connection(self, servername, autocommit=False):
        connect_string = "dbname=%s host=%s port=%s user=%s application_name=handyrep " % (self.conf["handyrep"]["handyrep_db"], self.servers[servername]["hostname"], self.servers[servername]["port"], self.conf["handyrep"]["handyrep_user"],)

        try:
            conn = psycopg2.connect( connect_string )
        except:
            raise CustomError("DBCONN","ERROR: Unable to connect to Postgres using the connections string %s" % connect_string)

        if autocommit:
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

        return conn

    def is_replica(self, rcur):
        try:
            reptest = get_one_val(rcur,"SELECT pg_is_in_recovery();")
        except Exception as e:
            raise CustomError("QUERY","Unable to check replica status: %s" % e.pgerror)

        return reptest

    def master_connection(self, autocommit=False):
        # connect to the master.  if unable to
        # or if it's not really the master, fail
        master = get_master_name()
        try:
            mconn = self.connection(master, autocommit=False)
        except:
            raise CustomError("DBCONN","Unable to connect to configured master server.")

        reptest = is_replica(mconn.cursor())
        if reptest:
            mconn.disconnect()
            raise CustomError("CONFIG","Server configured as the master is actually a replica, aborting connection.")
        return mconn
        # no master?
        raise CustomError("CONFIG","No master server found in server configuration")

    def best_connection(self, autocommit=False):
        # loop through the available servers, starting with the master
        # until we can connect to one of them
        try:
            bconn = master_connection()
        except:
        # master didn't work?  try again with replicas
            for someserver in self.servers.keys():
                try:
                    bconn = self.connection(someserver, autocommit)
                except:
                    continue
                else:
                    return bconn
        # still nothing?  error out
        raise CustomError('DBCONN',"FATAL: no accessible database servers in current server list.  Update the configuration manually and try again.")

    def run_sql_dir(self, sqlcursor, dirname):
        # need function here to read files in order
        # from a sql directory
        # and then push them via psycopg2

        