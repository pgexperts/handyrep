from fabric.api import execute, sudo, run, env, task
from fabric.network import disconnect_all
from fabric.contrib.files import upload_template
from lib.config import ReadConfig
from lib.error import CustomError
import json
from datetime import datetime, timedelta
import logging
import time
import importlib
from plugins.failplugin import failplugin
import lib.fabric_utils
from lib.misc_utils import ts_string, string_ts, now_string, succeeded, failed

class HandyRep(Object):

    def __init__(config_file='handyrep.conf'):
        # read and validate the config file
        config = ReadConfig(config_file)
        self.conf = config.read()
        self.servers = {}
        self.tabname = """ "%s"."%s" """ % (self.conf["handyrep"]["handyrep_schema"],self.conf["handyrep"]["handyrep_table"],)
        self.status = { "status": "unknown",
            "status_no" = 0,
            "status_message" = "status not checked yet"
            "status_ts" = '1970-01-01 00:00:00' }
        self.sync_config(False)
        # return a handyrep object
        return self

    def log(self, category, message, iserror=False, alert_type=None):
        if iserror:
            logging.error("%s: %s" % (category, message,))
        else:
            logging.info("%s: %s" % (category, message,))
            
        if alert_type:
            self.push_alert(alert_type, category, message)
        return True

    def push_alert(self, alert_type, category, message):
        if self.conf["handyrep"]["push_alert_method"]:
            alert = self.get_plugin(self.conf["handyrep"]["push_alert_method"])
            return alert.run(alert_type, category, message)
        else:
            return self.return_dict(True,"push alerts are disabled in config")

    def status_no(self, status):
        statdict = { "unknown" : 0,
                    "healthy" : 1,
                    "lagged" : 2,
                    "warning" : 3,
                    "unavailable" : 4,
                    "down" : 5 }
        return statusdict[status]

    def is_server_failure(self, oldstatus, newstatus):
        # tests old against new status to see if a
        # server has failed
        statdict = { "unknown" : [],
                    "healthy" : ["unavailable","down",],
                    "lagged" : ["unavailable","down",],
                    "warning" : ["unavailable","down",],
                    "unavailable" : [],
                    "down" : [] }
        return newstatus in statdict[oldstatus]

    def is_server_recovery(self, oldstatus, newstatus):
        # tests old against new status to see if a server has
        # recovered
        statdict = { "unknown" : [],
                    "healthy" : [],
                    "lagged" : [],
                    "warning" : ["healthy","lagged",],
                    "unavailable" : ["healthy","lagged",],
                    "down" : ["healthy","lagged","warning",] }
        return newstatus in statdict[oldstatus]

    def clusterstatus(self):
        # compute the cluster status based on
        # the status of the individual servers
        # in the cluster
        # returns full status dictionary
        # first see if we have a master and its status
        mastername = self.get_master_name()
        if not mastername:
            return { "status" : "down",
                    "status_no" : 5,
                    "status_ts" : self.now_string,
                    "status_message" : "no master server configured or found" }
                    
        masterstat = self.servers[mastername]
        if masterstat["status_no"] > 3:
            return { "status" : "down",
                    "status_no" : 5,
                    "status_ts" : self.now_string,
                    "status_message" : "master is down or unavailable" }
        elif masterstat["status_no"] > 1:
            return { "status" : "warning",
                    "status_no" : 3,
                    "status_ts" : self.now_string,
                    "status_message" : "master has one or more issues" }
        # now loop through the replicas, checking status
        replicacount = 0
        failedcount = 0
        for servname, servinfo in self.servers.iteritems():
            # enabled replicas only
            if servinfo["role"] = "replica" and servinfo["enabled"]:
                replicacount += 1
                if servinfo["status_no"] > 3:
                    failedcount += 1

        if failedcount:
            return { "status" : "warning",
                    "status_no" : 3,
                    "status_ts" : self.now_string,
                    "status_message" : "%d replicas are down" % failedcount }
        elif replicacount == 0:
            return { "status" : "warning",
                    "status_no" : 3,
                    "status_ts" : self.now_string,
                    "status_message" : "no configured replica for this cluster" }
        else:
            return { "status" : "healthy",
                    "status_no" : 1,
                    "status_ts" : self.now_string,
                    "status_message" : "" }
        

    def status_update(self, servername, newstatus, newmessage=None):
        # function for updating server statuses
        # returns nothing, because we're not going to check it
        # check if server status has changed.
        # if not, update timestamp and exit
        servconf = self.servers[servername]
        if servconf["status"] == newstatus:
            servconf["status_ts"] = self.self.now_string())
            return
        # if status has changed, log the vector and quantity of change
        newstatno = self.status_no(newstatus)
        self.log(servername, "server status changed from %s to %s" % (servconf["status"],newstatus,))
        if newstatno > servconf["status"]:
            if is_server_recovery(servconf["status"],newstatus):
                # if it's a recovery, then let's log it
                self.log("RECOVERY", "server %s has recovered" % servername)
        else:
            if is_server_failure(servconf["status"],newstatus):
                self.log("FAILURE", "server %s has failed, details: %s" % (servername, newmessage,), True, "WARNING")

        # then update status for this server
        servconf.update({ "status" : newstatus,
                        "status_no": newstatno,
                        "status_ts" : self.now_string(),
                        "status_message" : newmessage })
                        
        # compute status for the whole cluster
        clusterstatus = self.conf["status"]
        newcluster = self.clusterstatus()
        # has cluster status changed?
        # if so, figure out vector and quantity of change
        if clusterstatus["status_no"] < newcluster["status_no"]:
            # we've had a failure, push it
            if newcluster["status"] == "warning":
                self.log("STATUS_WARNING", "replication cluster is not fully operational, see logs for details", True, "WARNING")
            else:
                self.log("CLUSTER_DOWN", "database replication cluster is DOWN", True, "CRITICAL")
        elif clusterstatus["status_no"] > newcluster["status_no"]:
            self.log("RECOVERY", "database replication cluster has recovered to status %s" % newcluster["status"])
            
        self.status = newcluster
        self.write_servers()
        return

    def no_master_status(self):
        # called when we suddenly find that there's no enabled master
        # available
        self.status.update({ "status" = "down",
                    "status_no" = 5,
                    "status_message" = "no configured and enabled master found"
                    "status_ts" = now_string})
        self.log("CONFIG","No configured and enabled master found", True, "WARNING")
        return

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

            self.execute_it(mcur, """CREATE TABLE %s ( updated timestamptz, config JSON, servers JSON, status JSON )""" % self.tabname, [], "Unable to create handrep table")
            self.execute_it(mcur, "INSERT INTO" + tabname + " VALUES ( %s, %s, %s )""",(self.serv_updated, json.dumps(self.conf), json.dumps(self.servers),))
            mcur.execute("""SET SEARCH_PATH="%s",public,pg_catalog""" % hschema)
            
            # load all functions in the functions directory
            self.run_sql_dir(mcur, self.conf["handyrep"]["functions_dir"])

        # done
        mconn.commit()
        mconn.disconnect()
        return True

    def sync_config(self, write_servers = True):
        # read serverdata from file
        # this function does a 3-way sync of data
        # looking for the very latest server configuration
        # between the config file, the servers.save file
        # and the database
        # if the serverfile is more updated, use that
        # if the database is more updated, use that
        # if neither is present, or if the OVERRIDE conf
        # option is present, then use the config file
        use_conf = "conf"
        if not self.conf["handyrep"]["override_server_file"]:
            serverdata = self.read_serverfile()
            if serverdata:
                servfiledate = servdata["status"]["status_ts"]
            # open the handyrep table on the master
            sconn = self.best_connection()
            scur = sconn.cursor()
            dbconf = get_one_row(scur,"""SELECT updated, config, servers, status FROM %s """ % self.tabname)
            if dbconf:
                # we have both, check which one is more recent
                if serverdata:
                    if servfiledate > dbconf[0]:
                        use_conf = "file"
                    elif servfiledate < dbconf[0]
                        use_conf = "db"
                else
                    use_conf = "db"
            else:
                if serverdate:
                    use_conf = "file"
        # by now, we should know which one to use:
        if use_conf = "conf":
            # merge server defaults and server config
            for server in self.conf["servers"].keys():
                # set self.servers to the merger of settings
                self.servers[server] = merge_server_settings(server)
                
            # populate self.status
            self.status = self.clusterstatus()

        elif use_conf = "file":
            # set self.servers to the file data
            self.servers = serverdata["servers"]
            # set self.status from the file
            self.status = serverdata["status"]
            
        elif use_conf = "db":
            # set self.servers to servers field
            self.servers = dbconf[2]
            # set self.status to status field
            self.servers = dbconf[3]

        # write all servers
        if write_servers:
            self.write_servers()
        # don't bother to return anything in particular
        # we don't check it
        return



    def write_servers():
    # write server data to all locations
        # write server data to file
        try:
            servfile = open(self.conf["handyrep"]["server_file"],"w")
            servout = { "servers" : self.servers,
                        "status": self.status }
            json.dump(servout, servfile)
        except:
            self.log("FILEERROR","Unable to sync configuration to servers file due to permissions or configuration error", True)
            return False
        finally:
            try:
                servfile.close()
            except:
                pass
        # if possible, update the table via the master:
        if self.get_master_name():
            try:
                sconn = master_connection()
            except:
                self.log("DBCONN","Unable to sync configuration to database due to failed connection to master", True)
            scur = sconn.cursor()
            dbconf = get_one_row(scur,"""SELECT * FROM %s """ % self.tabname)
            if dbconf:
                if dbconf[0] < self.serv_updated
                try:
                    cur.execute("UPDATE " + tabname + """ SET updated = %s,
                    config = %s, servers = %s, status = %s""",(self.status["status_ts"], json.dumps(self.conf), json.dumps(self.servers),json.dumps(self.status),))
                except Exception as e:
                        # something else is wrong, abort
                    sconn.disconnect()
                    self.log("DBCONN","Unable to write HandyRep table to database for unknown reasons, please fix: %s" % e.pgerror, True)
                    return False
            else:
                self.init_handyrep_db()
            sconn.commit()
            sconn.disconnnect()
            return True
        else:
            self.log("CONFIG","Unable to save config, status to database since there is no configured master", True, "WARNING")
            return False

    def get_master_name(self):
        for servname, servdata in self.servers.iteritems():
            if servdata["role"] == "master" and servdata["enabled"]:
                return servname
        # no master?  return None and let the calling function
        # handle it
        return None

    def poll_master(self):
        # check master using poll method
        poll = get_plugin(self.conf["failover"]["poll_method"])
        master = get_master_name()
        if master:
            check = poll.run(self.conf, self.servers, master)
            if failed(check):
                self.status_update(master, "down", "master does not respond to polling")
            else:
                # if master was down, recover it
                # but don't eliminate warnings
                if self.servers[master]["status_no"] > 3:
                    self.status_update(master, "healthy", "master responding to polling")
                else:
                    # update timestamp but don't change message/status
                    self.status_update(master, self.servers[master]["status"])
            return check
        else:
            self.no_master_status()
            return return_dict( False, "No configured master found, poll failed" )

    def poll_server(self, replicaserver):
        # check replica using poll method
        if not replicaserver in self.servers:
            return return_dict( False, "Requested server not configured" )
        poll = get_plugin(self.conf["failover"]["poll_method"])
        check = poll.run(self.conf, self.servers, replicaserver)
        if succeeded(check):
            # if responding, improve the status if it's 
            if self.servers[replicaserver]["status"] in ["unknown","down","unavailable"]:
                self.status_update(replicaserver, "healthy", "server responding to polling")
            else:
                # update timestamp but don't change message/status
                self.status_update(replicaserver, self.servers[replicaserver]["status"])
        else:
            self.status_update(replicaserver, "down", "server not responding to polling")
        return check

    def verify_master(self):
        # check that you can ssh
        issues = {}
        master = get_master_name()
        if not master:
            self.no_master_status()
            return 
        if not self.test_ssh(master):
            self.status_update(master, "warning","cannot SSH to master")
            issues["ssh"] = "cannot SSH to master"
        # connect to master
        try:
            mconn = self.master_connection()
        except Exception as e:
            self.status_update(master, "warning","cannot psql to master")
            issues["psql"] = "cannot psql to master"

        #if both psql and ssh down, we're down:
        if "ssh" in issues and "psql" in issues:
            self.status_update(master, "unavailable", "psql and ssh both failing")
            return returndict(False, "master not responding")
        # if we have ssh but not psql, see if we can check if pg is running
        elif "ssh" not in issues and "psql" in issues:
            # try polling first, maybe master is just full up on connections
            if succeeded(poll_master()):
                self.status_update(master, "warning", "master running but we cannot connect")
                return return_dict(True, "master running but we cannot connect")
            else:
                # ok, let's ssh in and see if we can psql
                checkpg = pg_service_status(master)
                if succeeded(checkpg):
                    # postgres is up, just misconfigured
                    self.status_update(master, "unavailable", "master running but we cannot connect")
                    return return_dict(True, "master running but we cannot connect")
                else:
                    self.status_update(master, "down", "master is down")
                    return return_dict(False, "master is down")
        # if we have psql and ssh, check writability
        else:
            mcur = mconn.cursor()
            # check that you can do a simple write
            try:
                tempname = """ "%s".temp_test """ % self.conf["handrep"]["handyrep_schema"]
                mcur.execute("""CREATE TEMPORARY TABLE %s ( testval text );""" % tempname);
            except Exception as e:
                mconn.disconnect()
                self.status_update(master, "down","master running but cannot write to disk")
                return return_dict(False, "master is running by writes are frozen")
            # return success,
            mconn.disconnect()
            self.status_update(master, "healthy", "passed verification check")
            return return_dict(True, "master OK")

    def verify_replica(self, replicaserver):
        # replica verification for when the whole server
        # is running.  not for when in a failover state;
        # then you should use check_replica instead
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
        # poll the replica status table
        # which lets us know status and lag
        repinfo = self.hr_function(mcur, """handyrep_replica_status(%s)""",(replicaserver,))
        mconn.disconnect()
        if not repinfo:
            self.servers[replicaname]["status"] = "disconnected"
            return False
        # check replica lag
        self.servers[replicaname]["lag_mb"] = repinfo[3]
        if repinfo[3] > self.servers[replicaname]["lag_limit"]:
            self.servers[replicaname]["status"] = "lagged"
            return False
        else
            self.servers[replicaname]["status"] = "healthy"
            return True
        # otherwise, return success

    def verify_server(self, servername):
        if not self.servers[servername]["enabled"]:
            # disabled servers always return False
            return False
            
        if self.servers[servername]["role"] == "master":
            return self.verify_master()
        else:
            return self.verify_replica(servername)

    def verify_all(self):
        # verify all servers, preparatory to listing
        # information
        # returns True if all servers OK, False if not
        verification = True
        for server, servdetail in self.servers.iteritems():
            if servdetail["enabled"]:
                if servdetail["role"] == "master":
                    if not self.verify_master():
                        verification = False
                else:
                    if not self.verify_replica(server):
                        verification = False
        # update status
        if verification:
            self.status_update(
        # save all data
        self.write_servers()
        # always returns true
        return verification

    def check_replica(self, replicaserver):
        # replica verification
        # prior to failover
        # checks the replicas and sees if they're lagged
        # without connecting to the master
        try:
            rconn = self.connection(replicaserver)
        except Exception as e:
            log_activity("Connection to replica %s failed %s" % (replicaserver, e.message,), True)
            self.servers[replicaname]["status"] = "unavailable"
            return False
        # check that it's in replication
        rcur = rconn.cursor()
        if self.is_replica(rcur):
            # update lag status
            repinfo = self.hr_function("handyrep_replica_lag")
            rconn.disconnect()
            self.servers[replicaname]["lag_mb"] = repinfo[3]
            if repinfo[3] > self.servers[replicaname]["lag_limit"]:
                self.servers[replicaname]["status"] = "lagged"
                # a lagged server is still useful
                return True
            else
                self.servers[replicaname]["status"] = "healthy"
                return True
        else:
            rconn.disconnect()
            self.servers[replicaname]["status"] = "non-replica"
            return False

    def is_master(self, servername):
        if self.servers[servername]["role"] == 'master' and self.servers[servername]["enabled"]:
            return True
        else:
            return False

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

    def pg_service_status(self, servername):
        # check the service status on the master
        restart_cmd = self.get_plugin(self.servers[servername]["restart_method"])
        return restart_cmd.run("status"))

    def restart_master(self):
        # attempt to restart the master on the
        # master server
        master = self.get_master_name()
        restart_cmd = self.get_plugin(self.servers[master]["restart_method"])
        if restart_cmd(self.conf, self.servers):
            # wait recovery_wait for it to come up
            tries = (self.conf["failover"]["recovery_retries"])
            for mpoll in range(1,tries):
                if poll(master):
                    self.servers[master]["status"] = "healthy"
                    self.write_servers()
                    return True
                else:
                    time.sleep(self.conf["failover"]["fail_retry_interval"])
                    
        self.servers[master]["status"] = "down"
        self.write_servers()
        return False

    def auto_failover(self, newmaster=None, remaster=None):
        # if newmaster isnt set, poll replicas for new master
        # according to selection_method
        oldmaster = self.get_master_name()
        oldstatus = self.status
        self.status_update("failing over","Began failover")
        if not newmaster:
            # returns a list of potential new masters
            # this step should check all of them
            replicas = self.select_new_master()
            if not replicas:
                # no valid masters found, abort
                self.status_update(oldstatus,"No viable replicas found, aborting failover", "FAILOVER")
                return False
        else:
            if check_replica(newmaster):
                replicas = [newmaster,]
            else:
                self.status_update(oldstatus,"Designated new master is not working", "FAILOVER")
                return False
        # if remaster not set, get from settings
        if not remaster:
            remaster = self.conf["failover"]["remaster"]
        # attempt STONITH
        if not self.shutdown_old_master(oldmaster):
            # if failed, try to rewrite connections instead:
                if self.conf["failover"]["connection_failover"] and self.connection_failover(replicas[0]):
                    self.servers[oldmaster]["status"] = "unavailable"
                    # and we can continue
                else:
                    # we can't shut down the old master, reset and abort
                    self.connection_failover()
                    self.status_update(oldstatus, "Unable to shut down old master", "FAILOVER")
                    return False
            #raise CustomError("FAILOVER","Unable to shut down old master, aborting")
        # attempt replica promotion
        for replica in replicas:
            if self.promote(replica):
            # if success, update servers.save
                self.status = 'OK'
                # if remastering, attempt to remaster
                if remaster:
                    for servername, servinfo in self.servers.keys():
                        if servinfo["role"] == "replica" and servinfo["enabled"]:
                            self.remaster(servname, newmaster)
                # fail over connections:
                if self.connection_failover():
                    # run post-failover scripts
                    # we don't check the result because
                    # this isn't part of the workflow
                    self.postfailover_scripts()
                    self.status_message = "Failed over to new master %s" % replica
                    return True
                else:
                    # augh.  promotion succeeded but we can't fail over
                    # the connections.  abort
                    self.status_update("down","DB connections are not failed over to new master", "FAILOVER")
                    return False
            else:
                # try another replica
                continue

        # if we've gotten to this point, then we've failed at promoting
        # any replicas
        else:
            # if failed, try to abort and reset
            self.restart_master()
            self.status_update("down","Unable to promote any replicas", "FAILOVER")
            return False

    def manual_failover(self, newmaster, remaster=None):
        # if newmaster isnt set, poll replicas for new master
        # according to selection_method
        oldmaster = self.get_master_name()
        oldstatus = self.status
        self.status_update("failing over","Began failover")
        if not newmaster:
            # returns a list of potential new masters
            # this step should check all of them
            replicas = self.select_new_master()
            if not replicas:
                # no valid masters found, abort
                self.status_update(oldstatus,"No viable replicas found, aborting failover")
                return False
        else:
            if check_replica(newmaster):
                replicas = [newmaster,]
            else:
                self.status_update(oldstatus,"Designated new master is not working")
                return False
        # if remaster not set, get from settings
        if not remaster:
            remaster = self.conf["failover"]["remaster"]
        # attempt STONITH
        if not self.shutdown_old_master(oldmaster):
            # we can't shut down the old master, reset and abort
            self.status_update(oldstatus, "Unable to shut down old master", "FAILOVER")
            return False
        # attempt replica promotion
        for replica in replicas:
            if self.promote(replica):
            # if success, update servers.save
                self.status = 'OK'
                # if remastering, attempt to remaster
                if remaster:
                    for servername, servinfo in self.servers.keys():
                        if servinfo["role"] == "replica" and servinfo["enabled"]:
                            self.remaster(servname, newmaster)
                # fail over connections:
                if self.connection_failover():
                    # run post-failover scripts
                    # we don't check the result because
                    # this isn't part of the workflow
                    self.postfailover_scripts()
                    self.status_message = "Failed over to new master %s" % replica
                    return True
                else:
                    # augh.  promotion succeeded but we can't fail over
                    # the connections.  abort
                    self.status_update("down","DB connections are not failed over to new master", "FAILOVER")
                    return False
            else:
                # try another replica
                continue

        # if we've gotten to this point, then we've failed at promoting
        # any replicas
        else:
            # if failed, try to restart the original master
            # and reset
            if self.restart_master():
                self.status_update("OK","Replica promotion failed", "FAILOVER")
                return False
            else:
                self.status_update("down","Unable to promote any replicas", "FAILOVER")
                return False

    def shutdown_old_master(self, oldmaster):
        # test if we can ssh to master and run shutdown
        if self.shutdown(oldmaster):
            # if shutdown works, return True
            self.servers[oldmaster]["status"] = "down"
            return True
        else:
            # we can't connect to the old master
            # by ssh, try PG
            try:
                dbconn = self.connection(oldmaster)
                dbconn.disconnect()
            except Exception as e:
            # connection failed, looks like the
            # master is gone
                self.servers[oldmaster]["status"] = "unavailable"
                self.servers[oldmaster]["enabled"] = False
                self.write_servers()
                return True
        else:
            # run shutdown command anyway but don't check the result
            # this is in case a service has auto-restart
            self.shutdown(oldmaster)
            return True

    def shutdown(self, servername):
        # shutdown server
        shutdown = self.get_plugin(self.servers["servername"]["restart_method"])
        shut = shutdown(self.conf, self.servers, servername, "stop")
        # poll for shut down
        if shut:
            # update server info
            self.servers[servername]["status"] = "down"
            self.write_servers()
            return True
        else:
            self.servers[servername]["status"] = "unavailable"
            self.write_servers()
            self.status_update(self.status, "Unable to shut down server %s" % servername, "REPLICA")
            return False

    def startup(self, servername)
        # start server
        startup = self.get_plugin(self.servers["servername"]["restart_method"])
        started = startup(self.conf, self.servers, servername, "start")
        # poll to check availability
        if started:
            if not self.poll(servername):
                # not available?  wait a bit and try again
                time.sleep(10)
                if self.poll(servername):
                    self.servers[servername]["status"] = "healthy"
                    return True
                else:
                    self.servers[servername]["status"] = "down"
                    return False
            else:
                self.servers[servername]["status"] = "healthy"
                return True
        else:
            self.servers[servername]["status"] = "down"
            return False

    def restart(self, servername)
        # start server
        startup = self.get_plugin(self.servers["servername"]["restart_method"])
        started = startup(self.conf, self.servers, servername, "restart")
        # poll to check availability
        if started:
            if not self.poll(servername):
                # not available?  wait a bit and try again
                time.sleep(10)
                if self.poll(servername):
                    self.servers[servername]["status"] = "healthy"
                    return True
                else:
                    self.servers[servername]["status"] = "down"
                    return False
            else:
                self.servers[servername]["status"] = "healthy"
                return True
        else:
            self.servers[servername]["status"] = "down"
            return False

    def get_replicas_by_status(self, repstatus):
        reps = []
        for rep, repdetail in self.servers.iteritems():
            if repdetail["enabled"] and (repdetail["status"] == repstatus):
                reps.append(rep)
                
        return reps

    def promote(self, newmaster):
        # send promotion command
        promotion_command = get_plugin(self.servers["newmaster"]["promotion_command"])
        result = promotion_command(self.conf, self.servers, newmaster)
        if result:
            # check that we can still connect with the replica, error if not
            result = False
            nmconn = self.connection(newmaster)
            nmcur = nmconn.cursor()
            # poll for out-of-replication
            for i in range(1,self.conf["failover"]["recovery_retries"]):
                repstat = self.get_one_value(nmcur, "SELECT pg_is_in_recovery()")
                if repstat:
                    time.sleep(self.conf["failover"]["fail_retry_interval"])
                else:
                    result = True
                    self.servers[newmaster]["role"] = "master"
                    self.servers[newmaster]["status"] = "healthy"
                    break
            
            nmconn.disconnect()
        else:
            # promotion failed, better re-verify the server
            self.verify_replica(newmaster)
            self.status_update(self.status, "Promoting replica %s failed" % newmaster, "FAILOVER")

        # update server info
        self.write_servers()
        # return success as boolean
        return result

    def get_replica_list(self):
        reps = []
        reps.append(self.get_replicas_by_status("healthy"))
        reps.append(self.get_replicas_by_status("lagged"))
        return reps

    def select_new_master(self):
        # first check all replicas
        for rep in get_replica_list():
            self.check_replica(rep)

        selection = self.get_plugin(self.conf["failover"]["selection_method"])
        reps = selection(self.conf, self.servers)
        return reps

    def remaster(self, replicaserver, newmaster=None):
        # use master from settings if not supplied
        if not newmaster:
            newmaster = self.get_master_name()
        # change replica config
        result = self.push_replica_config(replicaserver, newmaster)
        if result:
            # restart replica
            restart = self.get_plugin(self.servers[replicaserver]["restart_method"])
            result = restart(self.conf, self.servers, replicaserver)
        # check for fail
        if not result:
            self.servers[replicaserver]["status"] = "disconnected"
            # sync server config
            self.write_servers()
            log_activity("remastering of replica %s failed" % replicaserver, True)

        return result

    def add_server(self, servername, *kwargs):
        # add all of the data for a new server
        # hostname is required
        if "hostname" not in (kwargs):
            raise CustomError("USER","Hostname is required for new servers")
        # assign defaults to everything
        self.servers[servername] = self.conf["server_defaults"]
        # now add the arguments
        for key, setting in kwargs.iteritems():
            self.servers[servername][key] = setting
        # role defaults to "replica"
        if "role" not in (kwargs):
            self.servers[servername]["role"] = "replica"
        # this server will be added as enabled=False
        self.servers[servername]["enabled"] = False
        # so that we can clone it up later
        # save everything
        self.write_servers()
        return True

    def clone(self, replicaserver, reclone=False clonefrom=None):
        # use config master if not supplied
        if clonefrom:
            clomaster = clonefrom
        else:
            clomaster = self.get_master_name()
        # abort if this is already an active replica
        # and the user didn't call the reclone flag
        if reclone:
            if not self.shutdown(replicaserver):
                raise CustomError("REPLICATION","Unable to shut down replica, aborting reclone.","REPLICATION")
        else:
            if self.servers[replicaserver]["enabled"] and self.servers[replicaserver]["status"] in ("healthy","lagged")):
                raise CustomError("USER","You may not clone a running replica.  Try using Reclone instead.")
        # clone using clone_method
        clone = self.get_plugin(self.conf[replicaserver]["clone_method"])
        tryclone = clone(self.conf, self.servers, replicaserver, clomaster)
        if not tryclone:
            return False
        # write recovery.conf
        self.push_replica_conf(replicaserver)
        # start replica
        if self.restart(replicaserver):
            self.servers[replicaserver]["enabled"] = True
            self.servers[replicaserver]["status"] = "healthy"
            # update servers.save
            # report success
            self.write_servers()
            return True
        else:
            self.write_servers()
            return False

    def disable(self, replicaserver):
        # shutdown replica.  Don't check result, we don't really care
        self.shutdown(replicaserver)
        # disable from servers.save
        self.servers[replicaserver]["status"] = "down"
        self.servers[replicaserver]["enabled"] = False
        return True

    def remove(self, servername):
        # clean no-longer-used serve entry from table
        if self.servers[servername]["enabled"]:
            raise CustomError("USER","You many not remove a currently enabled server from configuration.")
        else:
            self.servers.pop(servername, None)
            return True

    def get_server_info(self, servername=None, verify=True):
        # returns JSON of all servers
        # if sync:
        if verify:
            # verify_servers
            if servername:
                self.verify_server(servername)
            else:
                self.verify_all()
        if servername:
            # otherwise return just the one
            serv = { servername : self.servers[servername] }
            return json.dumps(serv)
        else:
            # if all, return all servers
            return json.dumps(servers)

    def get_servers_by_role(self, serverrole, verify=True):
        # roles: master, replica
        # if sync:
        if verify:
            if servername:
                self.verify_server(servername)
            else:
                self.verify_all()
        # return master if master
        if serverrole = "master":
            master = get_master_name()
            mastdeets = { master, self.servers[master] }
            return json.dumps(mastdeets)
        else:
            # if replicas, return all running replicas
            reps = {}
            for rep, repdeets in self.servers.iteritems:
                if repdeets["enabled"] and repdeets["role"] == "replica":
                    reps[rep] = repdeets

            return json.dumps(reps)

    def merge_server_settings(self, servername, newdict=None):
        # does 3-way merge of server settings:
        # server_defaults, saved server settings
        # and any new supplied dict
        # make a dictionary copy
        sdict = dict(self.conf["server_defaults"])
        if servername in self.servers:
            sdict.update(self.servers[servername])
        if newdict:
            sdict.update(newdict)
        # finally, add status fields
        # and other defaults
        statusdef = { "status" : "unknown",
                    "status_no" : 0,
                    "status_ts" : ts_string(datetime.now()),
                    "status_message" : "",
                    "role" : "replica",
                    "enabled" : False,
                    "failover_priority" : 999}
        statusdef.update(sdict)
        return statusdef
                    

    def returnjson(self, result, message = None, detaildict=None):
        jdict = { "result" : result }
        if message:
            jdict.update({ "message" : message })
        if detaildict:
            jdict.update(detaildict)
            
        return json.dumps(jdict)


    def jsonfailed(self, jsonresult, successtring="OK"):
        if jsonresult:
            jdict = json.reads(jsonresult)
            if jdict["result"] = successtring:
                return False
            else:
                return True
        else:
            return True

    def validate_server_settings(self, servername, serverdict=None):
        # check all settings or prospective settings
        # for a server.  in the process, merge changed
        # settings with full set of settings
        # merge old or default settings into new dict
        # returns JSON
        newdict = self.merge_server_settings(servername, serverdict)
        # check that we have all required settings
        issues = {}
        if "hostname" not in newdict.keys():
            return { "result" : "FAIL", "details" : "hostname not provided" }
        # check ssh
        if not self.test_ssh_host(serverdict):
            issues.update({ "ssh" : "FAIL" })
        # check postgres connection
        try:
            tconn = self.adhoc_connection(dbhost=newdict["hostname"],dbport=newdict["port"],dbpass=newdict["pgpass"])
        except Exception as e:
            issues.update({ "psql" : "FAIL" })
        else:
            tconn.disconnect()
        # run test_new() methods for each named pluginred: TBD
        # not sure how to do this, since we haven't yet merged
        # the changes into .servers
        if not issues:
            return { "result" : "SUCCESS", "details" : "server verified" }
        else
            return issues.update({ "result" : "FAIL", "details" : "verification failed" })

    def alter_server_def(self, servername, **kwargs):
        # verify servers
        # validate new settings
        valids = self.validate_server_settings(servername, kwargs)
        if self.failed(valids):
            valids.update({ "result" : "FAIL", "details" : "server validation failed" })
            return valids
        # merge and sync server config
        self.servers[servername] = self.merge_server_settings(servername, kwargs)
        self.write_servers()
        # exit with success
        return { "result" : "SUCCESS" }

    def clean_archive(self, expire_hours=None):
        # are we archiving?
        archiveinfo = self.conf["archive"]
        if not archiveinfo["archiving"]:
            return { "result" : "SUCCESS",
                "details" : "archiving disabled" }
        # are we deleting?
        if not archiveinfo["archive_delete_hours"]:
            return { "result" : "SUCCESS",
                "details" : "cleanup disabled" }
        # delete files from archive which are older
        # than setting using the plugin method
        archrun = get_plugin(archiveinfo["archive_method"])
        return archrun.run()

    def push_replica_conf(self, replicaserver):
        # write new recovery.conf per servers.save
        servconf = self.servers[replicaserver]
        rectemp = servconf["recovery_template"]
        archconf = self.conf["archive"]
        recparam = { "archive_directory" : None,
            "archive_host" : None }
        #set archive recovery locations if we're using
        #archiving
        if archconf["archiving"]:
            recparam["archive_directory"] = archconf["archive_directory"]
            if archconf[archive_server] <> replicaserver:
                recparam["archive_host"] = servconf["hostname"]
        # build the connection string
        masterconf = self.servers[self.get_master_name()]
        recparam["replica_connection"] = "host=%s port=%s user=%s application_name=%s" % (masterconf["hostname"], masterconf["port"], servconf["replication_user"], replicaserver,)
        # set up fabric
        env.key_filename = self.servers[servername]["ssh_key"]
        env.user = self.servers[servername]["ssh_user"]
        env.disable_known_hosts = True
        env.host_string = self.servers[servername]["hostname"]
        # push the config
        try:
            upload_template( rectemp, servconf["replica_conf"], use_jinja=True, context=recparam, template_dir=self.conf["handyrep"]["templates_dir"], use_sudo=True, mode=700)
            sudo( "chown %s %s" % (self.conf["handyrep"]["postgres_user"], servconf["replica_conf"] )
        except:
            retdict = { "result" : "FAIL", "details" : "could not push new archive.sh executable" }
        else:
            retdict = { "result" : "SUCCESS", "details" : "pushed new archive.sh executable" }
        finally:
            disconnect_all()

        # restart the replica
        if self.failed(self.restart(replicaserver)):
            retdict.update({ "result" : "FAIL",
                "details" : "could not restart server"})

        return retdict
        

    def push_archive_script(self, servername):
        # write a wal_archive executable script
        # to the server
        archconf = self.conf["archiving"]
        # check config
        if archconf["push_archive_script"]:
            if not archconf["archive_template"]:
                return { "result" : "FAIL", "details" : "archive template not configured" }
        else:
            # if we're not pushing scripts, just return success
            return { "result" : "SUCCESS", "details" : "pushing archive script disabled" }
        # render the template and push it to 
        # the server.
        archtemp = archconf["archive_template"]
        if archconf["archive_server"]:
            archserv = self.servers[archconf["archive_server"]]
            archconf["archive_host"] = archserv["hostname"]
        else
            archconf["archive_host"] = "localhost"
        env.key_filename = self.servers[servername]["ssh_key"]
        env.user = self.servers[servername]["ssh_user"]
        env.disable_known_hosts = True
        env.host_string = self.servers[servername]["hostname"]
        try:
            upload_template( archtemp, archconf["archive_bin"], use_jinja=True, context=archconf, template_dir=self.conf["handyrep"]["templates_dir"], use_sudo=True, mode=755)
            sudo( "chown %s %s" % (self.conf["handyrep"]["postgres_user"], archconf["archive_bin"] )
        except:
            retdict = { "result" : "FAIL", "details" : "could not push new archive.sh executable" }
        else:
            retdict = { "result" : "SUCCESS", "details" : "pushed new archive.sh executable" }
        finally:
            disconnect_all()
            
        return retdict
            

    def update_archive_location(self):
        # pushes a new archive location to all servers
        # new location must be configured in the config
        # file first
        # not currently implemented
        # start with master
        # push archive.sh
        # for each replica
        # push archive.sh
        # push recovery.conf
        # exit

    def get_plugin(self, pluginname):
        # call method from the plugins class
        # if this errors, we return a class
        # which will fail whenever it's called
        try:
            getmodule = importlib.import_module("plugins.%s" % pluginname)
            getclass = getattr(getmodule, pluginname)
            getinstance = getclass(self.conf, self.servers)
        except:
            getinstance = failplugin(pluginname)

        return getinstance

    def connection(self, servername, autocommit=False):
        connect_string = "dbname=%s host=%s port=%s user=%s application_name=handyrep " % (self.conf["handyrep"]["handyrep_db"], self.servers[servername]["hostname"], self.servers[servername]["port"], self.conf["handyrep"]["handyrep_user"],)

        if self.conf["handyrep"]["handyrep_pw"]:
                connect_string += " password=%s " % self.conf["handyrep"]["handyrep_pw"]

        try:
            conn = psycopg2.connect( connect_string )
        except:
            raise CustomError("DBCONN","ERROR: Unable to connect to Postgres using the connections string %s" % connect_string)

        if autocommit:
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

        return conn

    def adhoc_connection(self, **kwargs):

        if "dbname" in kwargs:
            if kwargs["dbname"]:
                connect_string = " dbname=%s " % kwargs["dbhost"]
        else:
            connect_string = " dbname=%s " % self.conf["handyrep"]["handyrep_db"]

        if "dbhost" in kwargs:
            if kwargs["dbhost"]:
                connect_string += " host=%s " % kwargs["dbhost"]

        if "dbuser" in kwargs:
            if kwargs["dbuser"]:
                connect_string += " user=%s " % kwargs["dbuser"]
        else:
                connect_string += " user=%s " % self.conf["handyrep"]["handyrep_user"]

        if "dbpass" in kwargs:
            if kwargs["dbpass"]:
                connect_string += " password=%s " % kwargs["dbpass"]
        else:
            if self.conf["handyrep"]["handyrep_pw"]:
                connect_string += " password=%s " % self.conf["handyrep"]["handyrep_pw"]

        if "dbport" in kwargs:
            if kwargs["dbport"]:
                connect_string += " port=%s " % kwargs["dbport"]

        if "appname" in kwargs:
            if kwargs["appname"]:
                connect_string += " application_name=%s " % kwargs["appname"]
        else:
            connect_string += " application_name=handyrep "

        try:
            conn = psycopg2.connect( connect_string )
        except:
            raise CustomError("DBCONN","ERROR: Unable to connect to Postgres using the connections string %s" % connect_string)

        if "autocommit" in kwargs:
            if kwargs["autocommit"]:
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
        master = self.get_master_name()
        if not master:
            raise CustomError("CONFIG","No master server found in server configuration")
        
        try:
            mconn = self.connection(master, autocommit=False)
        except:
            raise CustomError("DBCONN","Unable to connect to configured master server.")

        reptest = is_replica(mconn.cursor())
        if reptest:
            mconn.disconnect()
            raise CustomError("CONFIG","Server configured as the master is actually a replica, aborting connection.")
        
        return mconn
        

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

    def remote_ls(self):
        run(self.conf["handyrep"]["test_ssh_command"])

    @task
    def test_ssh(self, servername):
        try:
            testit = execute(remote_ls,
                key_filename = self.servers[servername]["ssh_key"],
                user = self.servers[servername]["ssh_user"],
                disable_known_hosts = True,
                hosts = [self.servers[servername]["hostname"],])
        except:
            return False

        disconnect_all()
        return testit.succeeded

    @task
    def test_ssh_newhost(self, hostname, ssh_key, ssh_user ):
        try:
            testit = execute(remote_ls,
                key_filename = ssh_key
                user = ssh_user,
                disable_known_hosts = True,
                hosts = [hostname,])
        except:
            return False
            
        disconnect_all()
        return testit.succeeded

        