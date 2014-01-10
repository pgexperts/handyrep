from fabric.api import execute, sudo, run, env, task, local, settings
from fabric.network import disconnect_all
from fabric.contrib.files import upload_template
from lib.config import ReadConfig
from lib.error import CustomError
from lib.dbfunctions import get_one_val, get_one_row, execute_it
import json
from datetime import datetime, timedelta
import logging
import time
import importlib
from plugins.failplugin import failplugin
from lib.misc_utils import ts_string, string_ts, now_string, succeeded, failed, return_dict, exstr, get_nested_val
import psycopg2
import psycopg2.extensions
import os

class HandyRep(object):

    def __init__(self,config_file='handyrep.conf'):
        # read and validate the config file
        config = ReadConfig(config_file)
        # need to figure out how to set the location for
        self.conf = config.read('config/handyrep-validate.conf')
        try:
            logging.basicConfig(filename=self.conf["handyrep"]["log_file"], datefmt="%Y-%m-%d %H:%M:%S", format="%(asctime)-12s %(message)s")
        except Exception as ex:
            raise CustomError("STARTUP","unable to open designated log file: %s" % exstr(ex))
        self.servers = {}
        self.tabname = """ "%s"."%s" """ % (self.conf["handyrep"]["handyrep_schema"],self.conf["handyrep"]["handyrep_table"],)
        self.status = { "status": "unknown",
            "status_no" : 0,
            "pid" : os.getpid(),
            "status_message" : "status not checked yet",
            "status_ts" : '1970-01-01 00:00:00' }
        self.sync_config(True)
        # return a handyrep object
        return None

    def log(self, category, message, iserror=False, alert_type=None):
        if iserror:
            logging.error("%s: %s" % (category, message,))
        else:
            if self.conf["handyrep"]["log_verbose"]:
                logging.info("%s: %s" % (category, message,))
            
        if alert_type:
            self.push_alert(alert_type, category, message)
        return True

    def read_log(self, numlines=20):
        # reads the last N lines of the log
        # uses byte position to make it more efficient
        lbytes = numlines * 100
        with open(self.conf["handyrep"]["log_file"], "r") as logf:
            logf.seek (0, 2)           # Seek @ EOF
            fsize = logf.tell()        # Get Size
            logf.seek (max (fsize-lbytes, 0), 0)
            lines = logf.readlines()       # Read to end

        lines = lines[-numlines:]    # Get last 10 lines
        return list(reversed(lines))

    def get_setting(self, setting_name):
        if type(setting_name) is list:
            # prevent getting passwords this way
            if setting_name[0] == "passwords":
                return None
            else:
                return get_nested_val(self.conf, *setting_name)
        else:
            # if category not supplied, then use "handyrep"
            return get_nested_val(self.conf, "handyrep", "setting_name")

    def set_verbose(self, verbose=True):
        self.conf["handyrep"]["log_verbose"] = verbose
        return verbose

    def push_alert(self, alert_type, category, message):
        if self.conf["handyrep"]["push_alert_method"]:
            alert = self.get_plugin(self.conf["handyrep"]["push_alert_method"])
            return alert.run(alert_type, category, message)
        else:
            return return_dict(True,"push alerts are disabled in config")

    def status_no(self, status):
        statdict = { "unknown" : 0,
                    "healthy" : 1,
                    "lagged" : 2,
                    "warning" : 3,
                    "unavailable" : 4,
                    "down" : 5 }
        return statdict[status]

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
                    "status_ts" : now_string(),
                    "status_message" : "no master server configured or found" }
                    
        masterstat = self.servers[mastername]
        if masterstat["status_no"] > 3:
            return { "status" : "down",
                    "status_no" : 5,
                    "status_ts" : now_string(),
                    "status_message" : "master is down or unavailable" }
        elif masterstat["status_no"] > 1:
            return { "status" : "warning",
                    "status_no" : 3,
                    "status_ts" : now_string(),
                    "status_message" : "master has one or more issues" }
        # now loop through the replicas, checking status
        replicacount = 0
        failedcount = 0
        for servname, servinfo in self.servers.iteritems():
            # enabled replicas only
            if servinfo["role"] == "replica" and servinfo["enabled"]:
                replicacount += 1
                if servinfo["status_no"] > 3:
                    failedcount += 1

        if failedcount:
            return { "status" : "warning",
                    "status_no" : 3,
                    "status_ts" : now_string(),
                    "status_message" : "%d replicas are down" % failedcount }
        elif replicacount == 0:
            return { "status" : "warning",
                    "status_no" : 3,
                    "status_ts" : now_string(),
                    "status_message" : "no configured replica for this cluster" }
        else:
            return { "status" : "healthy",
                    "status_no" : 1,
                    "status_ts" : now_string(),
                    "status_message" : "" }
        

    def status_update(self, servername, newstatus, newmessage=None):
        # function for updating server statuses
        # returns nothing, because we're not going to check it
        # check if server status has changed.
        # if not, update timestamp and exit
        servconf = self.servers[servername]
        if servconf["status"] == newstatus:
            servconf["status_ts"] = now_string()
            return
        # if status has changed, log the vector and quantity of change
        newstatno = self.status_no(newstatus)
        self.log(servername, "server status changed from %s to %s" % (servconf["status"],newstatus,))
        if newstatno > servconf["status"]:
            if self.is_server_recovery(servconf["status"],newstatus):
                # if it's a recovery, then let's log it
                self.log("RECOVERY", "server %s has recovered" % servername)
        else:
            if self.is_server_failure(servconf["status"],newstatus):
                self.log("FAILURE", "server %s has failed, details: %s" % (servername, newmessage,), True, "WARNING")

        # then update status for this server
        servconf.update({ "status" : newstatus,
                        "status_no": newstatno,
                        "status_ts" : now_string(),
                        "status_message" : newmessage })
                        
        # compute status for the whole cluster
        clusterstatus = self.status
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
        self.status.update({ "status" : "down",
                    "status_no" : 5,
                    "status_message" : "no configured and enabled master found",
                    "status_ts" : now_string()})
        self.log("CONFIG","No configured and enabled master found", True, "WARNING")
        return

    def cluster_status_update(self, newstatus, newstatus_message=""):
        # called during certain operations
        # such as failover in order to change
        self.log("STATUS", "cluster status changed to %s: %s", newstatus, newstatus_message)
        self.status.update({ "status" : newstatus,
            "status_no" : self.status_no(newstatus),
            "status_message" : newstatus_message,
            "status_ts" : now_string() })
        # don't return anything, we don't check it
        return

    def check_hr_master(self):
        # check plugin method to see
        hrs_method = self.get_plugin(self.conf["handyrep"]["master_check_method"])
        # return result
        hrstatus = hrs_method.run(*self.conf["handyrep"]["master_check_parameters"])
        return hrstatus

    def verify_servers(self):
        # check each server definition against
        # the reality
        allgood = True
        for someserver, servdetails in self.servers.iteritems():
            if servdetails["enabled"]:
                if servdetails["role"] == "master":
                    if not self.verify_master(someserver):
                        allgood = False
                else:
                    if not self.verify_replica(someserver):
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

    def failwait(self):
        time.sleep(self.conf["failover"]["fail_retry_interval"])
        return

    def init_handyrep_db(self):
        # initialize the handrep schema
        # per settings
        htable = self.conf["handyrep"]["handyrep_table"]
        hschema = self.conf["handyrep"]["handyrep_schema"]
        mconn = self.master_connection()
        mcur = mconn.cursor()
        has_tab = get_one_val(mcur, """SELECT count(*) FROM
            pg_stat_user_tables
            WHERE relname = %s and schemaname = %s""",(htable, hschema,))
        if not has_tab:
            # need schema test here for 9.2:
            has_schema = get_one_val(mcur, """SELECT count(*) FROM pg_namespace WHERE nspname = %s""",(htable,))
            if not has_schema:
                execute_it(mcur, """CREATE SCHEMA "%s" """ % hschema, [])

            execute_it(mcur, """CREATE TABLE %s ( updated timestamptz, config JSON, servers JSON, status JSON )""" % self.tabname, [])
            execute_it(mcur, "INSERT INTO" + self.tabname + " VALUES ( %s, %s, %s )""",(self.status["status_ts"], json.dumps(self.conf), json.dumps(self.servers),))

        # done
        mconn.commit()
        mconn.close()
        return True

    def check_pid(self, serverdata):
        # checks the PID kept in the servers.save file
        # on startup or any full config sync
        # if it doesn't match the current PID and the other PID
        # is actually running, exit with error
        oldpid = get_nested_val(serverdata, "status", "pid")
        newpid = os.getpid()
        #print "oldpid: %d, newpid: %d" % (oldpid, newpid,)
        if oldpid:
            if oldpid <> newpid:
                try:
                    os.kill(oldpid, 0)
                except OSError:
                    return newpid
                else:
                    raise CustomError("HANDYREP","Another HandyRep is running on this server with pid %d" % oldpid)
        else:
            return newpid

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
        # also checks the PID of the HR process stored in
        # servers.save in order to verify that we're not
        # running two HR daemons
        use_conf = "conf"
        if not self.conf["handyrep"]["override_server_file"]:
            serverdata = self.read_serverfile()
            if serverdata:
                self.check_pid(serverdata)
                servfiledate = serverdata["status"]["status_ts"]
            else:
                servfiledate = None
            # open the handyrep table on the master if possible
            try:
                sconn = self.best_connection()
                scur = sconn.cursor()
                dbconf = get_one_row(scur,"""SELECT updated, config, servers, status FROM %s """ % self.tabname)
            except:
                dbconf = None
                
            if dbconf:
                # we have both, check which one is more recent
                if serverdata:
                    if servfiledate > dbconf[0]:
                        use_conf = "file"
                    elif servfiledate < dbconf[0]:
                        use_conf = "db"
                else:
                    use_conf = "db"
            else:
                if servfiledate:
                    use_conf = "file"
        # by now, we should know which one to use:
        if use_conf == "conf":
            # merge server defaults and server config
            for server in self.conf["servers"].keys():
                # set self.servers to the merger of settings
                self.servers[server] = self.merge_server_settings(server)
                
            # populate self.status
            self.status = self.clusterstatus()

        elif use_conf == "file":
            # set self.servers to the file data
            self.servers = serverdata["servers"]
            # set self.status from the file
            self.status = serverdata["status"]
            
        elif use_conf == "db":
            # set self.servers to servers field
            self.servers = dbconf[2]
            # set self.status to status field
            self.servers = dbconf[3]

        # update the pid
        self.status["pid"] = os.getpid()
        # write all servers
        if write_servers:
            self.write_servers()
        # don't bother to return anything in particular
        # we don't check it
        return

    def reload_conf(self, config_file='handyrep.conf'):
        config = ReadConfig(config_file)
        self.conf = config.read('config/handyrep-validate.conf')
        return return_dict(True, 'configuration file reloaded')

    def write_servers(self):
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
                sconn = self.master_connection()
                scur = sconn.cursor()
            except Exception as ex:
                self.log("DBCONN","Unable to sync configuration to database due to failed connection to master: %s" % exstr(ex), True)
                sconn = None

            if sconn:
                dbconf = get_one_row(scur,"""SELECT * FROM %s """ % self.tabname)
                if dbconf:
                    if dbconf[0] < self.serv_updated:
                        try:
                            cur.execute("UPDATE " + tabname + """ SET updated = %s,
                            config = %s, servers = %s, status = %s""",(self.status["status_ts"], json.dumps(self.conf), json.dumps(self.servers),json.dumps(self.status),))
                        except Exception as e:
                                # something else is wrong, abort
                            sconn.close()
                            self.log("DBCONN","Unable to write HandyRep table to database for unknown reasons, please fix: %s" % e.pgerror, True)
                            return False
                else:
                    self.init_handyrep_db()
                sconn.commit()
                sconn.close()
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

    def poll(self, servername):
        # poll servers, according to role
        if self.is_master(servername):
            return self.poll_master()
        else:
            return self.poll_server(servername)

    def poll_master(self):
        # check master using poll method
        poll = self.get_plugin(self.conf["failover"]["poll_method"])
        master =self.get_master_name()
        if master:
            check = poll.run(master)
            if failed(check):
                self.status_update(master, "down", "master does not respond to polling")
            else:
                # if master was down, recover it
                # but don't eliminate warnings
                if self.servers[master]["status_no"] in [0,4,5,] :
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
        poll = self.get_plugin(self.conf["failover"]["poll_method"])
        check = poll.run(replicaserver)
        if succeeded(check):
            # if responding, improve the status if it's 
            if self.servers[replicaserver]["status"] in ["unknown","down","unavailable"]:
                self.status_update(replicaserver, "healthy", "server responding to polling")
            else:
                # update timestamp but don't change message/status
                self.status_update(replicaserver, self.servers[replicaserver]["status"])
        else:
            self.status_update(replicaserver, "unavailable", "server not responding to polling")
        return check

    def poll_all(self):
        # polls all servers.  fails if the master is
        # unavailable, doesn't really care about replicas
        # also returns whether or not it's OK
        # to fail over, as verify_all does
        master_count = 0
        rep_count = 0
        ret = return_dict(False, "no servers to poll", {"failover_ok" : False})
        for servname, servdeets in self.servers.iteritems():
            if servdeets["enabled"]:
                if servdeets["role"] == "master":
                    master_count += 1
                    pollrep = self.poll_master()
                    ret.update(pollrep)
                    ret[servname] = pollrep
                elif servdeets["role"] == "replica":
                    pollrep = self.poll_server(servname)
                    if succeeded(pollrep):
                        rep_count += 1
                        ret["failover_ok"] = True
                    ret[servname] = pollrep
                # other types of servers are ignored

        # check master count
        if master_count == 0:
            self.no_master_status()
            ret.update(return_dict(False, "No configured master found", {"failover_ok": False}))
        elif master_count > 1:
            # we don't allow more than one master
            self.cluster_status_update("down", "Multiple master servers found")
            ret.update(return_dict(False, "Multiple masters found", {"failover_ok" : False}))

        # do we have any good replicas?
        if rep_count == 0:
            ret.update({"details":ret["details"] + " and no working replica found","failover_ok":False})

        return ret
            

    def verify_master(self):
        # check that you can ssh
        issues = {}
        master = self.get_master_name()
        if not master:
            self.no_master_status()
            return return_dict(False, "No master configured")
        if not self.test_ssh(master):
            self.status_update(master, "warning","cannot SSH to master")
            issues["ssh"] = "cannot SSH to master"
        # connect to master
        try:
            mconn = self.master_connection()
        except Exception as ex:
            self.status_update(master, "warning","cannot psql to master")
            issues["psql"] = "cannot psql to master: %s" % exstr(ex)

        #if both psql and ssh down, we're down:
        if "ssh" in issues and "psql" in issues:
            self.status_update(master, "unavailable", "psql and ssh both failing")
            return return_dict(False, "master not responding", issues)
        # if we have ssh but not psql, see if we can check if pg is running
        elif "ssh" not in issues and "psql" in issues:
            # try polling first, maybe master is just full up on connections
            if succeeded(self.poll_master()):
                self.status_update(master, "warning", "master running but we cannot connect")
                return return_dict(True, "master running but we cannot connect", issues)
            else:
                # ok, let's ssh in and see if we can check the status
                checkpg = self.pg_service_status(master)
                if succeeded(checkpg):
                    # postgres is up, just misconfigured
                    self.status_update(master, "warning", "master running but we cannot connect")
                    return return_dict(True, "master running but we cannot connect", issues)
                else:
                    self.status_update(master, "down", "master is down")
                    return return_dict(False, "master is down", issues)
        # if we have psql, check writability
        else:
            mcur = mconn.cursor()
            # check that you can do a simple write
            try:
                self.conf["handyrep"]["handyrep_schema"]
                mcur.execute("""CREATE TEMPORARY TABLE handyrep_temptest ( testval text );""");
            except Exception as ex:
                mconn.close()
                self.status_update(master, "down","master running but cannot write to disk")
                return return_dict(False, "master is running by writes are frozen: %s" % exstr(ex))
            # return success,
            mconn.close()
            if issues:
                self.status_update(master, "warning", "passed verification check but no SSH access", issues)
            else:
                self.status_update(master, "healthy", "passed verification check")
            return return_dict(True, "master OK")

    def verify_replica(self, replicaserver):
        # replica verification for when the whole cluster
        # is running.  not for when in a failover state;
        # then you should use check_replica instead
        issues = {}
        if replicaserver not in self.servers:
            return return_dict(False, "Server %s not found in configuration" % replicaserver)
        
        if not self.test_ssh(replicaserver):
            self.status_update(replicaserver, "warning","cannot SSH to server")
            issues["ssh"] = "cannot SSH to server"
        
        try:
            rconn = self.connection(replicaserver)
        except Exception as ex:
            self.status_update(replicaserver, "warning", "cannot psql to server")
            issues["psql"] = "cannot psql to server: %s" % exstr(ex)

        # if we had any issues connecting ...
        if "ssh" in issues and "psql" in issues:
            self.status_update(replicaserver, "unavailable", "psql and ssh both failing")
            return return_dict(False, "server not responding", issues)
        # if we have ssh but not psql, see if we can check if pg is running
        elif "ssh" not in issues and "psql" in issues:
            # try polling first, maybe master is just full up on connections
            if succeeded(self.poll_server(replicaserver)):
                self.status_update(replicaserver, "warning", "server running but we cannot connect")
                return return_dict(True, "server running but we cannot connect", issues)
            else:
                # ok, let's ssh in and see if we can psql
                checkpg = self.pg_service_status(replicaserver)
                if succeeded(checkpg):
                    # postgres is up, just misconfigured
                    self.status_update(replicaserver, "warning", "server running but we cannot connect")
                    return return_dict(True, "server running but we cannot connect", issues)
                else:
                    self.status_update(replicaserver, "down", "server is down")
                    return return_dict(False, "server is down", issues)
                
        # if we have psql, check replication status
        else:
        # check that it's in replication
            rcur = rconn.cursor()
            isrep = self.is_replica(rcur)
            rconn.close()
            if not isrep:
                self.status_update(replicaserver, "warning", "replica is running but is not in replication")
                return return_dict(False, "replica is not in replication")
        # poll the replica status table
        # which lets us know status and lag
        repstatus = self.get_plugin(self.conf["failover"]["replication_status_method"])
        repinfo = repstatus.run(replicaserver)
        # if the above fails, we can't connect to the master
        if failed(repinfo):
            self.status_update(replicaserver, "warning", "cannot check replication status")
            return return_dict(True, "cannot check replication status")
        # check that we're in replication
        if not repinfo["replicating"]:
            self.status_update(replicaserver, "unavailable", "replica is not in replication")
            return return_dict(False, "replica is not in replication")
        # check replica lag
        if repinfo["lag"] > self.servers[replicaserver]["lag_limit"]:
            self.status_update(replicaserver, "lagged", "lagging %d %s" % repinfo["lag"], repinfo["lag_unit"])
            return return_dict(True, "replica is lagged but running")
        else:
        # otherwise, return success
            self.status_update(replicaserver, "healthy", "replica is all good")
            return return_dict(True, "replica OK")

    def verify_server(self, servername):
        if not self.servers[servername]["enabled"]:
            # disabled servers always return success
            # after all, they're supposed to be disabled
            return return_dict(True, "server disabled")
            
        if self.servers[servername]["role"] == "master":
            return self.verify_master()
        else:
            return self.verify_replica(servername)

    def verify_all(self):
        # verify all servers, preparatory to listing
        # information
        # returns success unless the master is down
        # also returns failover_ok, which tells us
        # if there's an OK failover situation
        vertest = return_dict(False, "no master found")
        master_count = 0
        rep_count = 0
        for server, servdetail in self.servers.iteritems():
            if servdetail["enabled"]:
                if servdetail["role"] == "master":
                    mcheck = self.verify_master()
                    master_count += 1
                    if succeeded(mcheck):
                        vertest.update({ "result" : "SUCCESS",
                            "details" : "master check passed",
                            "failover_ok" : True,
                            server : mcheck })
                    else:
                        vertest.update({ "result" : "FAIL",
                            "details" : "master check failed",
                            "failover_ok" : True,
                            server : mcheck })
                elif servdetail["role"] == "replica":
                    vertest[server] = self.verify_replica(server)
                    if succeeded(vertest[server]):
                        rep_count += 1

        # check masters
        if master_count == 0:
            self.no_master_status()
            vertest.update(return_dict(False, "No configured master found", {"failover_ok": False}))
        elif master_count > 1:
            # we don't allow more than one master
            self.cluster_status_update("down", "Multiple master servers found")
            vertest.update(return_dict(False, "Multiple masters found", {"failover_ok" : False}))

                # do we have any good replicas?
        if rep_count == 0:
            vertest.update({"details" : vertest["details"] + " and no working replica found","failover_ok":False})

        return vertest

    def check_replica(self, replicaserver):
        # replica check prior to failover
        # checks the replicas and sees if they're lagged
        # without connecting to the master
        # this is mostly like verify_replica, except
        # that failure criteria are different
        # if we can't psql, ssh, and confirm that it's
        # in replication, fail.
        # also return lag status
        
        # test control access
        checkpg = self.pg_service_status(replicaserver)
        if failed(checkpg):
            # update status if server not already down
            if self.servers[replicaserver]["status_no"] < 4:
                self.status_update(replicaserver, "warning", "no control connection to server")
            return return_dict(False, "no control connection to server")
        
        # test psql access
        try:
            rconn = self.connection(replicaserver)
        except Exception as e:
            # update status if not already down
            if self.servers[replicaserver]["status_no"] < 4:
                self.status_update(replicaserver, "warning", "cannot psql to server")
            return return_dict(False, "cannot psql to server")

        # check that it's in replication
        rcur = rconn.cursor()
        isrep = self.is_replica(rcur)
        rconn.close()
        if not isrep:
            self.status_update(replicaserver, "warning", "server is not in replication")
            return return_dict(False, "server not in replication")
        # looks like we're good
        # we're not going to check lag status, because
        # that's presumed to be part of the replica selection
        return return_dict(True, "replica OK")

    def is_master(self, servername):
        if self.servers[servername]["role"] == 'master' and self.servers[servername]["enabled"]:
            return True
        else:
            return False

    def is_available(self, servername):
        return ( self.servers[servername]["enabled"] and self.servers[servername]["status_no"] < 4 )
            

    def failover_check(self, verify=False):
        # core function of handyrep
        # periodic check of the master
        # to see if we need to initiate failover
        # if auto-failover
        # check if we're the hr master
        hrmaster = self.check_hr_master()
        if succeeded(hrmaster):
            if not hrmaster["is_master"]:
            # we're not the master, return success
            # and don't do anything
                return return_dict(True, "this server is not the Handyrep master, skipping")
        else:
            # we errored abort
            return return_dict(False, "hr master check errored, cannot proceed")
            
        # if not verify, try polling the master first
        # otherwise go straight to verify
        if not verify:
            vercheck = self.poll_all()
            # if the master poll failed, verify the master
            if failed(vercheck):
                mcheck = self.verify_master()
                if succeeded(mcheck):
                    vercheck.update(return_dict(True, "master poll failed, but master is running"))
        else:
            vercheck = self.verify_all()

        if failed(vercheck):
            # maybe restart it?  depends on config
            if self.conf["failover"]["restart_master"]:
                if succeeded(self.restart_master()):
                    self.write_servers()
                    return return_dict(True, "master restarted")
            
            # otherwise, check if autofailover is configured
            # and if it's OK to failover
            if self.conf["failover"]["auto_failover"] and vercheck["failover_ok"]:
                failit = self.auto_failover()
                if succeeded(failit):
                    self.write_servers()
                    return return_dict(True, "failed over to new master")
                else:
                    vercheck.update(return_dict(False, "master down, failover failed"))
                    self.write_servers()
                    return vercheck
            elif not self.conf["failover"]["auto_failover"]:
                vercheck.update(return_dict(False, "master down, auto_failover not enabled"))
                self.write_servers()
                return vercheck
            else:
                vercheck.update(return_dict(False, "master down or split-brain, auto_failover is unsafe"))
                self.write_servers()
                return vercheck
        else:
            self.write_servers()
            return vercheck

    def failover_check_cycle(self, poll_num):
        # same as failover check, only desinged to work with
        # hdaemons periodic in order to return the cycle information
        # periodic expects
        # check the poll cycle number
        if poll_num == 1:
            verifyit = True
        else:
            verifyit = False
        # do a failover check:
        fcheck = self.failover_check(verifyit)
        if succeeded(fcheck):
            # on success, increment the poll cycle
            poll_next = poll_num + 1
            if poll_next >= self.conf["failover"]["verify_frequency"]:
                poll_next = 1
        else:
            # on fail, do a full verify next time
            poll_next = 1
        # sleep for poll interval seconds
        return self.conf["failover"]["poll_interval"], poll_next

    def pg_service_status(self, servername):
        # check the service status on the master
        restart_cmd = self.get_plugin(self.servers[servername]["restart_method"])
        return restart_cmd.run(servername, "status")

    def restart_master(self, whichmaster=None):
        # attempt to restart the master on the
        # master server
        if whichmaster:
            master = whichmaster
        else:
            master = self.get_master_name()

        restart_cmd = self.get_plugin(self.servers[master]["restart_method"])
        restart_result = restart_cmd.run(master, "restart")
        if succeeded(restart_result):
            # wait recovery_wait for it to come up
            tries = (self.conf["failover"]["recovery_retries"])
            for mpoll in range(1,tries):
                if self.poll_server(master):
                    self.status_update(master, "healthy", "restarted successfully")
                    self.servers[master]["enabled"] = True
                    return return_dict(True, "restarted master successfully")
                else:
                    time.sleep(self.conf["failover"]["fail_retry_interval"])
        # no success yet?  then we're down
        self.status_update(master, "down", "unable to restart master")
        return return_dict(False, "unable to restart master")

    def auto_failover(self):
        oldmaster = self.get_master_name()
        oldstatus = self.status["status"]
        self.cluster_status_update("warning","failing over")
        # poll replicas for new master
        # according to selection_method
        replicas = self.select_new_master()
        if not replicas:
            # no valid masters found, abort
            self.cluster_status_update(oldstatus,"No viable replicas found, aborting failover")
            self.log("FAILOVER","Unable to fail over, no viable replicas", True, "CRITICAL")
            return return_dict(False, "Unable to fail over, no viable replicas")
            
        # find out if we're remastering
        remaster = self.conf["failover"]["remaster"]
        # attempt STONITH
        if failed(self.shutdown_old_master(oldmaster)):
            # if failed, try to rewrite connections instead:
                if self.conf["failover"]["connection_failover"]:
                    if succeeded(self.connection_failover(replicas[0])):
                        self.status_update(oldmaster, "unavailable", "old master did not shut down, changed connection config")
                    # and we can continue
                    else:
                    # we can't shut down the old master, reset and abort
                        self.connection_failover(oldmaster)
                        self.log("FAILOVER", "Could not shut down old master, aborting failover", True, "CRITICAL")
                        self.cluster_status_update(oldstatus, "Failover aborted: Unable to shut down old master")
                        return return_dict(False, "Failover aborted, shutdown failed")
                else:
                    self.log("FAILOVER", "Could not shut down old master, aborting failover", True, "CRITICAL")
                    self.cluster_status_update(oldstatus, "Failover aborted: Unable to shut down old master")
                    return return_dict(False, "Failover aborted, shutdown failed")

        # attempt replica promotion
        for replica in replicas:
            if succeeded(self.check_replica(replica)):
                if succeeded(self.promote(replica)):
                    # if remastering, attempt to remaster
                    if remaster:
                        for servername, servinfo in self.servers.iteritems():
                            if servinfo["role"] == "replica" and servinfo["enabled"]:
                                # don't check result, we do that in
                                # the remaster procedure
                                self.remaster(servname, newmaster)
                    # fail over connections:
                    if succeeded(self.connection_failover(replica)):
                        # update statuses
                        self.status = self.clusterstatus()
                        self.write_servers()
                        # run post-failover scripts
                        # we don't fail back if they fail, though
                        if failed(self.extra_failover_commands(replica)):
                            self.cluster_status_update("warning","postfailover commands failed")
                            return(True, "Failed over, but postfailover scripts did not succeed")
                            
                        return(True, "Failover to %s succeeded" % replica)
                    else:
                        # augh.  promotion succeeded but we can't fail over
                        # the connections.  abort
                        self.log("FAILOVER","Promoted new master but unable to fail over connections", True, "CRITICAL")
                        self.cluster_status_update("down","Promoted new master but unable to fail over connections")
                        return return_dict(False, "Promoted new master but unable to fail over connections")

        # if we've gotten to this point, then we've failed at promoting
        # any replicas, time to panic
        if succeeded(self.restart_master(oldmaster)):
            self.status_update(oldmaster, "warning", "attempted failover and did not succeed, please check servers")
        else:
            self.status_update(oldmaster, "down","Unable to promote any replicas")
            
        self.log("FAILOVER","Unable to promote any replicas",True, "CRITICAL")
        return return_dict(False, "Unable to promote any replicas")

    def manual_failover(self, newmaster=None, remaster=None):
        # attempt failover to a replica when requested
        # by user.  this is a bit different from auto-failover
        # because it's assumed that we have a known-good state
        # to revert to
        # get master name
        oldmaster = self.get_master_name()
        oldstatus = self.servers[oldmaster]["status"]
        self.status_update(oldmaster, "warning", "currently failing over")
        if not newmaster:
            # returns a list of potential new masters
            # this step should check all of them
            replicas = self.select_new_master()
            if not replicas:
                # no valid masters found, abort
                self.log("FAILOVER","No viable new masters found", True, "CRITICAL")
                self.status_update(oldmaster, oldstatus, "No viable replicas found, aborting failover and reverting")
                return return_dict(False, "No viable replicas found, aborting failover and reverting")
        else:
            if self.check_replica(newmaster):
                replicas = [newmaster,]
            else:
                self.log("FAILOVER","New master not operating", True)
                self.status_update(oldmaster, oldstatus, "New master not viable, aborting failover and reverting")
                return return_dict(False, "New master not viable, aborting failover and reverting")
        # if remaster not set, get from settings
        if not remaster:
            remaster = self.conf["failover"]["remaster"]
        # attempt STONITH
        if failed(self.shutdown_old_master(oldmaster)):
            # we can't shut down the old master, reset and abort
            if succeeded(self.restart_master()):
                return return_dict(False, "Unable to shut down old master, aborting and rolling back")
            else:
                self.log("FAILOVER","Unable to shut down or restart master", True, "CRITICAL")
                return return_dict(False, "Unable to shut down or restart old master")
        # attempt replica promotion
        for replica in replicas:
            if succeeded(self.check_replica(replica)):
                if succeeded(self.promote(replica)):
                    # if remastering, attempt to remaster
                    if remaster:
                        for servername, servinfo in self.servers.iteritems():
                            if servinfo["role"] == "replica" and servinfo["enabled"]:
                                # don't check result, we do that in
                                # the remaster procedure
                                self.remaster(servname, newmaster)
                    # fail over connections:
                    if succeeded(self.connection_failover(newmaster)):
                        # run post-failover scripts
                        # we don't fail back if they fail, though
                        if failed(self.extra_failover_commands(newmaster)):
                            self.cluster_status_update("warning","postfailover commands failed")
                            return(True, "Failed over, but postfailover scripts did not succeed")
                        else:
                            self.log("FAILOVER","Failover to %s completed" % newmaster)
                            self.servers[oldmaster]["enabled"] = False
                            self.status = self.clusterstatus()
                            return(True, "Failover completed")
                    else:
                        # augh.  promotion succeeded but we can't fail over
                        # the connections.  abort
                        self.log("FAILOVER","Promoted new master but unable to fail over connections", True, "CRITICAL")
                        self.cluster_status_update("down","Promoted new master but unable to fail over connections")
                        return (False, "Failed over master but unable to fail over connections")

        # if we've gotten to this point, then we've failed at promoting
        # any replicas -- reset an abort
        if succeeded(self.restart_master(oldmaster)):
            self.status_update(oldmaster, "warning", "attempted failover and did not succeed, please check servers")
        else:
            self.status_update(oldmaster, "down","Unable to promote any replicas")
        return return_dict(False, "Unable to promote any replicas")

    def shutdown_old_master(self, oldmaster):
        # test if we can ssh to master and run shutdown
        if self.shutdown(oldmaster):
            # if shutdown works, return True
            self.status_update(oldmaster, "down", "Master is shut down")
            self.servers[oldmaster]["enabled"] = False
            return return_dict(True, "Master is shut down")
        else:
            # we can't connect to the old master
            # by ssh, try PG
            try:
                dbconn = self.connection(oldmaster)
                dbconn.close()
            except Exception as e:
            # connection failed, looks like the
            # master is gone
                self.status_update(oldmaster, "unavailable", "Master cannot be reached for shutdown")
                self.servers[oldmaster]["enabled"] = False
                return return_dict(True, "master is not responding to connections")
            else:
                # we couldn't shut down the master, even
                # thought we can contact it -- failure
                self.log("SHUTDOWN","Attempted to shut down master server, shutdown failed", True, "CRITICAL")
                self.status_update(oldmaster, "warning", "attempted shutdown, master did not respond")
                return return_dict(False, "Cannot shut down master, postgres still running")

    def shutdown(self, servername):
        # shutdown server
        shutdown = self.get_plugin(self.servers[servername]["restart_method"])
        shut = shutdown.run(servername, "stop")
        if succeeded(shut):
            # update server info
            self.status_update(servername, "down", "server has been shut down")
            return return_dict(True, "shutdown succeeded")
        else:
            # poll for shut down
            is_shut = False
            for i in range(1,self.conf["failover"]["fail_retries"]):
                self.failwait()
                if failed(self.poll_server(servername)):
                    is_shut = True
                    break

            if is_shut:
                return return_dict(True, "shutdown succeeded")
            else:
                return return_dict(False, "server %s does not shut down" % servername)

    def startup(self, servername):
        # check if server is enabled
        if not self.servers[servername]["enabled"]:
            return return_dict(False, "server %s is disabled.  Please enable it before starting it")
        # start server
        startup = self.get_plugin(self.servers[servername]["restart_method"])
        started = startup.run(servername, "start")
        # poll to check availability
        if succeeded(started):
            if failed(self.poll(servername)):
                # not available?  wait a bit and try again
                time.sleep(10)
                if succeeded(self.poll(servername)):
                    self.status_update(servername, "healthy", "server started")
                    return return_dict(True, "server started")
                else:
                    self.status_update(servername, "unavailable", "server restarted, but does not respond")
                    return return_dict(False, "server restarted, but does not respond")
            else:
                self.status_update(servername, "healthy", "server started")
                return return_dict(True, "server started")
        else:
            self.status_update(servername, "down", "server does not start")
            return return_dict(False, "server does not start")

    def restart(self, servername):
        # start server
        # this method is a bit more complex
        if not self.servers[servername]["enabled"]:
            return return_dict(False, "server %s is disabled.  Please enable it before restarting it")
        # if restart fails, we see if the server is running, and try
        # a startup
        startup = self.get_plugin(self.servers[servername]["restart_method"])
        started = startup.run(servername, "restart")
        # poll to check availability
        if failed(started):
            # maybe we failed because PostgreSQL isn't running?
            if succeeded(self.poll(servername)):
                # failed abort
                # update status if server is known-good
                if self.servers[servername]["status_no"] < 3:
                    self.update_status(servername, "warning", "server does not respond to restart commands")
                return(False, "server does not respond to restart commands")
            else:
                # if not running, try a straight start command
                started = startup.run(servername, "start")

        if succeeded(started):
            if failed(self.poll_server(servername)):
                # not available?  wait a bit and try again
                time.sleep(10)
                if succeeded(self.poll_server(servername)):
                    self.status_update(servername, "healthy", "server started")
                    return return_dict(True, "server started")
                else:
                    self.status_update(servername, "unavailable", "server restarted, but does not respond")
                    return return_dict(False, "server restarted, but does not respond")
            else:
                self.status_update(servername, "healthy", "server started")
                return return_dict(True, "server started")
        else:
            self.status_update(servername, "down", "server does not start")
            return return_dict(False, "server does not start")


    def get_replicas_by_status(self, repstatus):
        reps = []
        for rep, repdetail in self.servers.iteritems():
            if repdetail["enabled"] and (repdetail["status"] == repstatus):
                reps.append(rep)
                
        return reps

    def promote(self, newmaster):
        # send promotion command
        promotion_command = self.get_plugin(self.servers[newmaster]["promotion_method"])
        promoted = promotion_command.run(newmaster)
        nmconn = None
        if succeeded(promoted):
            # check that we can still connect with the replica, error if not
            try:
                nmconn = self.connection(newmaster)
                nmcur = nmconn.cursor()
            except:
                nmconn = None
                # promoted, now we can't connect? oh-oh
                self.status_update(newmaster, "unavailable", "server promoted, now can't connect")
                return return_dict(False, "server promoted, now can't connect")

            # poll for out-of-replication
            for i in range(1,self.conf["failover"]["recovery_retries"]):
                repstat = get_one_val(nmcur, "SELECT pg_is_in_recovery()")
                if repstat:
                    time.sleep(self.conf["failover"]["fail_retry_interval"])
                else:
                    nmconn.close()
                    self.servers[newmaster]["role"] = "master"
                    self.servers[newmaster]["enabled"] = True
                    self.status_update(newmaster, "healthy", "promoted to new master")
                    return return_dict(True, "replica %s promoted to master" % newmaster)
                
        if nmconn:            
            nmconn.close()
        # if we get here, promotion failed, better re-verify the server
        self.verify_replica(newmaster)
        self.log("FAILOVER","Replica promotion of %s failed" % newmaster)
        return return_dict(False, "promotion failed")
            

    def get_replica_list(self):
        reps = []
        reps.append(self.get_replicas_by_status("healthy"))
        reps.append(self.get_replicas_by_status("lagged"))
        return reps

    def select_new_master(self):
        # first check all replicas
        selection = self.get_plugin(self.conf["failover"]["selection_method"])
        reps = selection.run()
        return reps

    def remaster(self, replicaserver, newmaster=None):
        # use master from settings if not supplied
        if not newmaster:
            newmaster = self.get_master_name()
        # change replica config
        remastered = self.push_replica_conf(replicaserver, newmaster)
        if succeeded(remastered):
            # restart replica
            remastered = self.restart(replicaserver)
            
        if failed(remastered):
            self.verify_server(replicaserver)
            self.log("REMASTER","remastering of server %s failed" % replicaserver, True, "WARNING")
            return return_dict(False, "remastering failed")
        else:
            self.log("REMASTER", "remastered %s" % replicaserver)
            return return_dict(True, "remastering succeeded")

    def add_server(self, servername, **serverprops):
        # add all of the data for a new server
        # hostname is required
        if "hostname" not in (serverprops):
            raise CustomError("USER","Hostname is required for new servers")
        # role defaults to "replica"
        if "role" not in (serverprops):
            serverprops["role"] = "replica"
        # this server will be added as enabled=False
        serverprops["enabled"] = False
        # so that we can clone it up later
        # add rest of settings
        self.servers[servername] = self.merge_server_settings(servername, serverprops)
        # save everything
        self.write_servers()
        return return_dict(True, "new server saved")

    def clone(self, replicaserver, reclone=False, clonefrom=None):
        # use config master if not supplied
        if clonefrom:
            clomaster = clonefrom
        else:
            clomaster = self.get_master_name()
        # abort if this is the master
        if replicaserver == self.get_master_name():
            return return_dict(False, "You may not clone over the master")
        # abort if this is already an active replica
        # and the user didn't call the reclone flag
        if reclone:
            if failed(self.shutdown(replicaserver)):
                self.log("CLONE","Unable to shut down replica, aborting reclone.", True, "WARNING")
                # reverify server
                self.verify_server(replicaserver)
                return return_dict(False, "Unable to shut down replica")

        elif self.servers[replicaserver]["enabled"] and self.servers[replicaserver]["status"] in ("healthy","lagged","warning","unknown"):
                return return_dict(False, "Cloning over a running server requires the Reclone flag")
        # clone using clone_method
        self.servers[replicaserver]["role"] = "replica"
        clone = self.get_plugin(self.servers[replicaserver]["clone_method"])
        tryclone = clone.run(replicaserver, clomaster, reclone)
        if failed(tryclone):
            return tryclone
        # write recovery.conf, assuming it's configured
        if failed(self.push_replica_conf(replicaserver)):
            self.log("CLONE","Cloning %s failed" % replicaserver, True)
            return return_dict(False, "cloning failed, could not push replica config")
        # same for archiving script
        if failed(self.push_archive_script(replicaserver)):
            self.log("CLONE","Cloning %s failed" % replicaserver, True)
            return return_dict(False, "cloning failed, could not push archiving config")
        # start replica
        self.servers[replicaserver]["enabled"] = True
        if succeeded(self.startup(replicaserver)):
            self.status_update(replicaserver, "healthy", "cloned successfully")
            self.log("CLONE","Successfully cloned to %s" % replicaserver)
            return return_dict(True, "cloning succeeded")
        else:
            self.servers[replicaserver]["enabled"] = False
            self.log("CLONE","Cloning %s failed" % replicaserver, True)
            return return_dict(False, "cloning failed, could not start replica")

    def disable(self, servername):
        # shutdown replica.  Don't check result, we don't really care
        self.shutdown(servername)
        # disable from servers.save
        self.servers[servername]["enabled"] = False
        self.write_servers()
        return return_dict(True, "server disabled")

    def enable(self, servername):
        # check for obvious conflicts
        if self.servers[servername]["role"] == "master":
            if self.get_master_name():
                return return_dict(False, "you may not start up a second master.  Disable the other master first")
        # update server data
        self.servers[servername]["enabled"] = True
        # check if we're up and update status
        if self.servers[servername]["role"] in ("master", "replica"):
            self.verify_server(servername)
            self.write_servers()
        else:
            self.write_servers()
        return return_dict(True, "server enabled")

    def remove(self, servername):
        # clean no-longer-used serve entry from table
        if self.servers[servername]["enabled"]:
            return return_dict(False, "You many not remove a currently enabled server from configuration.")
        else:
            self.servers.pop(servername, None)
            self.write_servers()
            return return_dict(True, "Server removed from configuration")

    def get_status(self, check_type="cached"):
        # returns status of all server resources
        if check_type == "poll":
            self.poll_all()
        elif check_type == "verify":
            self.verify_all()

        servall = {}
        for servname, servdeets in self.servers.iteritems():
            servin = {k:v for k,v in servdeets.iteritems() if k in ["hostname","status","status_no","status_message","enabled","status_ts", "role"]}
            servall[servname] = servin

        return { "cluster" : self.status,
            "servers" : servall }

    def postfailover_scripts(self, newmaster):
        pscripts = self.conf["extra_failover_commands"]

    def get_server_info(self, servername=None, verify=False):
        # returns config of all servers
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
            return serv
        else:
            # if all, return all servers
            return self.servers

    def get_servers_by_role(self, serverrole, verify=True):
        # roles: master, replica
        # if sync:
        if verify:
            if servername:
                self.verify_server(servername)
            else:
                self.verify_all()
        # return master if master
        if serverrole == "master":
            master =self.get_master_name()
            mastdeets = { master, self.servers[master] }
            return mastdeets
        else:
            # if replicas, return all running replicas
            reps = {}
            for rep, repdeets in self.servers.iteritems:
                if repdeets["enabled"] and repdeets["role"] == "replica":
                    reps[rep] = repdeets

            return reps

    def get_cluster_status(self, verify=False):
        if verify:
            self.verify_all()
        return self.status

    def merge_server_settings(self, servername, newdict=None):
        # does 3-way merge of server settings:
        # server_defaults, saved server settings
        # and any new supplied dict
        # make a dictionary copy
        sdict = dict(self.conf["server_defaults"])
        if servername in self.conf["servers"]:
            sdict.update(self.conf["servers"][servername])
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
            return return_dict(False, "hostname not provided")
        # check ssh
        if not self.test_ssh_newhost(newdict["hostname"], newdict["ssh_key"], newdict["ssh_user"]):
            issues.update({ "ssh" : "FAIL" })
        # check postgres connection
        try:
            tconn = self.adhoc_connection(dbhost=newdict["hostname"],dbport=newdict["port"],dbpass=newdict["pgpass"])
        except Exception as e:
            issues.update({ "psql" : "FAIL" })
        else:
            tconn.close()
        # run test_new() methods for each named pluginred: TBD
        # not sure how to do this, since we haven't yet merged
        # the changes into .servers
        if not issues:
            return return_dict(True, "server verified")
        else:
            return return_dict(False, "verification failed", issues)

    def alter_server_def(self, servername, **serverprops):
        # check for changes to server config which aren't allowed
        olddef = self.servers[servername]
        
        if "role" in serverprops:
            # can't change a replica to a master this way, or vice-versa
            # unless the server is already disabled
            newrole = serverprops["role"]
            if serverprops["role"] != olddef["role"] and olddef["enabled"] and (olddef["role"] in ("replica", "master") or serverprops["role"] in ("replica", "master"))
                return return_dict(False, "Changes to server role for enabled servers in replication not allowed.  Use promote, disable and/or clone instead")
        else:
            newrole = olddef["role"]

        if newrole in ("replica", "master"):
            inreplication = True

        if "status" in serverprops or "status_no" in serverprops or "status_ts" in serverprops:
            return return_dict(False, "You may not manually change server status")

        # verify servers
        # validate new settings
        # NOT currently validating settings
        # because of the insolvable catch-22 in doing so
        #valids = self.validate_server_settings(servername, serverprops)
        #if failed(valids):
        #    valids.update(return_dict(False, "the settings you supplied do not validate"))
        #    return valids
        # merge and sync server config
        self.servers[servername] = self.merge_server_settings(servername, serverprops)
        
        # enable servers
        if "enabled" in serverprops and inreplication:
            # are we enabling or disabling the server?
            if serverprops["enabled"] and not olddef["enabled"]:
                self.enable(servername)
            elif not serverprops["enabled"] and olddef["enabled"]:
                self.disable(servername)
        
        self.write_servers()
        # exit with success
        return return_dict(True, "Server definition changed", {"definition" : self.servers[servername]})

    def clean_archive(self, expire_hours=None):
        # are we archiving?
        archiveinfo = self.conf["archive"]
        if expire_hours:
            exphours = expire_hours
        else:
            exphours = self.conf["archive"]["archive_delete_hours"]
        # are we archving?
        if not archiveinfo["archiving"]:
            return return_dict(True, "archiving disabled")
        # are we deleting?
        if not exphours:
            return return_dict(True, "archive cleanup disabled")
        
        # delete files from archive which are older
        # than setting using the plugin method
        archrun = self.get_plugin(archiveinfo["archive_delete_method"])
        return archrun.run(expire_hours)

    def push_replica_conf(self, replicaserver, newmaster=None):
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
        if not newmaster:
            newmaster = self.get_master_name()
        masterconf = self.servers[newmaster]
        recparam["replica_connection"] = "host=%s port=%s user=%s application_name=%s" % (masterconf["hostname"], masterconf["port"], self.conf["handyrep"]["replication_user"], replicaserver,)
        # set up fabric
        env.key_filename = self.servers[replicaserver]["ssh_key"]
        env.user = self.servers[replicaserver]["ssh_user"]
        env.disable_known_hosts = True
        env.host_string = self.servers[replicaserver]["hostname"]
        # push the config
        try:
            upload_template( rectemp, servconf["replica_conf"], use_jinja=True, context=recparam, template_dir=self.conf["handyrep"]["templates_dir"], use_sudo=True)
            sudo( "chown %s %s" % (self.conf["handyrep"]["postgres_superuser"], servconf["replica_conf"] ))
            sudo( "chmod 700 %s" % (servconf["replica_conf"] ))
            
        except Exception as ex:
            disconnect_all()
            self.status_update(replicaserver, "warning", "could not change configuration file")
            return return_dict(False, "could not push new replication configuration: %s" % exstr(ex))
        
        disconnect_all()

        # restart the replica if it was running
        if self.is_available(replicaserver):
            if failed(self.restart(replicaserver)):
                self.status_update(replicaserver, "warning", "changed config but could not restart server")
                return return_dict(False, "changed config but could not restart server")

        self.log("CONFIG","Changed configuration for %s" % replicaserver)
        return return_dict(True, "pushed new replication configuration")
        

    def push_archive_script(self, servername):
        # write a wal_archive executable script
        # to the server
        archconf = self.conf["archive"]
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
        else:
            archconf["archive_host"] = "localhost"
        env.key_filename = self.servers[servername]["ssh_key"]
        env.user = self.servers[servername]["ssh_user"]
        env.disable_known_hosts = True
        env.host_string = self.servers[servername]["hostname"]
        try:
            upload_template( archtemp, archconf["archive_bin"], use_jinja=True, context=archconf, template_dir=self.conf["handyrep"]["templates_dir"], use_sudo=True, mode=755)
            sudo( "chown %s %s" % (self.conf["handyrep"]["postgres_user"], archconf["archive_bin"] ))
        except:
            retdict = return_dict(False, "could not push new archive.sh executable")
        else:
            retdict = return_dict(True, "pushed new archive.sh executable")
        finally:
            disconnect_all()
            
        return retdict

    def connection_failover(self, newmaster):
        # fail over connections as part of
        # automatic or manual failover
        # returns success if not configured
        confail_name = self.conf["failover"]["connection_failover_method"]
        if confail_name:
            confail = self.get_plugin(confail_name)
            confailed = confail.run(newmaster)
            if succeeded(confailed):
                self.log("FAILOVER","Connections failed over to new master %s" % newmaster)
            else:
                self.log("FAILOVER","Could not fail over new connections to new master %s" % newmaster, True, "WARNING")
            return confailed
        else:
            return return_dict(True, "no connection failover configured")

    def connection_proxy_init(self):
        # initialize connection configuration
        # as part of initial setup
        # requires connection failover to be set up in the first place
        # returns success if not configured in order to
        # avoid errors on automated processses
        confail_name = self.conf["failover"]["connection_failover_method"]
        if confail_name:
            confail = self.get_plugin(confail_name)
            confailed = confail.init()
            if succeeded(confailed):
                self.log("FAILOVER","Initialized connection proxy configuration")
            else:
                self.log("FAILOVER","Could not initialize connection configuration", True)
            return confailed
        else:
            return return_dict(True, "no connection failover configured")

    def extra_failover_commands(self, newmaster):
        # runs extra commands after failover, based on
        # the new server configuration
        # output of these commands is logged, but
        # no action is taken if they fail
        some_failed = False
        for fcmd, fdeets in self.conf["extra_failover_commands"].iteritems():
            failcall = self.get_plugin(fdeets["command"])
            failres = failcall.run(newmaster, *fdeets["parameters"])
            if failed(failres):
                some_failed = True
                self.log("FAILOVER","Post-failover command %s failed with error %s" % (fcmd, failres["details"],),True, "WARNING")

        if some_failed:
            return return_dict(False, "One or more post-failover commands failed")
        else:
            return return_dict(True, "Post-failover commands executed")
        

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
        return

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

        if self.conf["passwords"]["handyrep_db_pass"]:
                connect_string += " password=%s " % self.conf["passwords"]["handyrep_db_pass"]

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
        except Exception as ex:
            raise CustomError("QUERY","Unable to check replica status", ex)

        return reptest

    def master_connection(self, mautocommit=False):
        # connect to the master.  if unable to
        # or if it's not really the master, fail
        master = self.get_master_name()
        if not master:
            raise CustomError("CONFIG","No master server found in server configuration")
        
        try:
            mconn = self.connection(master, autocommit=mautocommit)
        except:
            raise CustomError("DBCONN","Unable to connect to configured master server.")

        reptest = self.is_replica(mconn.cursor())
        if reptest:
            mconn.close()
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

    def test_ssh(self, servername):
        try:
            env.key_filename = self.servers[servername]["ssh_key"]
            env.user = self.servers[servername]["ssh_user"]
            env.disable_known_hosts = True
            env.host_string = self.servers[servername]["hostname"]
            command = self.conf["handyrep"]["test_ssh_command"]
            testit = run(command, warn_only=True)
        except:
            return False

        result = testit.succeeded
        disconnect_all()
        return result

    def test_ssh_newhost(self, hostname, ssh_key, ssh_user ):
        try:
            env.key_filename = ssh_key
            env.user = ssh_user
            env.disable_known_hosts = True
            env.host_string = hostname
            command = self.conf["handyrep"]["test_ssh_command"]
            testit = run(command, warn_only=True)
        except Exception as ex:
            print exstr(ex)
            return False

        result = testit.succeeded
        disconnect_all()
        return result

    def authenticate(self, username, userpass, funcname):
        # simple authentication function which
        # authenticates the user against the passwords
        # set in handyrep.conf
        # should probably be replaced with something more sophisticated
        # you'll notice we ignore the username, for example
        
        # is this a readonly function?
        rofunclist = ["get_status","get_server_info","get_cluster_status","get_servers_by_role",]

        # try admin password
        if userpass == self.conf["passwords"]["admin_password"]:
            return return_dict(True, "password accepted")
        elif userpass == self.conf["passwords"]["read_password"]:
            if funcname in rofunclist:
                return return_dict(True, "password accepted")
            else:
                return return_dict(False, "That feature requires admin access")
        else:
            return return_dict(False, "password rejected")

    def authenticate_bool(self, username, userpass, funcname):
        # simple boolean response to the above for the web daemon
        return succeeded(self.authenticate(username, userpass, funcname))
        