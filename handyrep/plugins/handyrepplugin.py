from fabric.api import sudo, run, env, local, settings, shell_env
from fabric.network import disconnect_all
from fabric.contrib.files import upload_template, exists
#from fabric.context_managers import shell_env
from lib.error import CustomError
from lib.dbfunctions import get_one_val, get_one_row, execute_it, get_pg_conn
from lib.misc_utils import ts_string, string_ts, now_string, succeeded, failed, return_dict, exstr, lock_fabric, fabric_unlock_all
import json
from datetime import datetime, timedelta
import logging
import time
import psycopg2
import psycopg2.extensions
from os.path import join
from subprocess import call
import re
import threading

class HandyRepPlugin(object):

    def __init__(self, conf, servers):
        self.conf = conf
        self.servers = servers
        return

    def sudorun(self, servername, commands, runas, passwd="", sshpass=None):
        # generic function to run one or more commands
        # as a specific remote user.  returns the results
        # of the last command run.  aborts when any
        # command fails
        lock_fabric()
        if sshpass:
            env.password = sshpass
        else:
            env.key_filename = self.servers[servername]["ssh_key"]
            
        env.user = self.servers[servername]["ssh_user"]
        env.disable_known_hosts = True
        env.host_string = self.servers[servername]["hostname"]
        rundict = return_dict(True, "no commands provided", {"return_code" : None })
        if passwd is None:
            pgpasswd = ""
        else:
            pgpasswd = passwd

        for command in commands:
            try:
                with shell_env(PGPASSWORD=pgpasswd):
                    runit = sudo(command, user=runas, warn_only=True,pty=False, quiet=True)
                rundict.update({ "details" : runit ,
                    "return_code" : runit.return_code })
                if runit.succeeded:
                    rundict.update({"result":"SUCCESS"})
                else:
                    rundict.update({"result":"FAIL"})
                    break
            except Exception as ex:
                rundict = { "result" : "FAIL",
                    "details" : "connection failure: %s" % self.exstr(ex),
                    "return_code" : None }
                break
        
        self.disconnect_and_unlock()
        return rundict

    def run_as_postgres(self, servername, commands):
        pguser = self.conf["handyrep"]["postgres_superuser"]
        pwd = self.conf["passwords"]["superuser_pass"]
        return self.sudorun(servername, commands, pguser, pwd)

    def run_as_replication(self, servername, commands):
        # we actually use the command-line superuser for this
        # since the replication user doesn't generally have a shell
        # account
        pguser = self.conf["handyrep"]["postgres_superuser"]
        pwd = self.conf["passwords"]["replication_pass"]
        return self.sudorun(servername, commands, pguser, pwd)

    def run_as_root(self, servername, commands):
        return self.sudorun(servername, commands, "root")

    def run_as_handyrep(self, servername, commands):
        # runs a set of commands as the "handyrep" user
        # exiting when the first command fails
        # returns a dic with the results of the last command
        # run
        lock_fabric()
        env.key_filename = self.servers[servername]["ssh_key"]
        env.user = self.servers[servername]["ssh_user"]
        env.disable_known_hosts = True
        env.host_string = self.servers[servername]["hostname"]
        rundict = { "result": "SUCCESS",
            "details" : "no commands provided",
            "return_code" : None }
        for command in commands:
            try:
                runit = run(command, warn_only=True, quiet=True)
                rundict.update({ "details" : runit ,
                    "return_code" : runit.return_code })
                if runit.succeeded:
                    rundict.update({"result":"SUCCESS"})
                else:
                    rundict.update({"result":"FAIL"})
                    break
            except Exception as ex:
                rundict = { "result" : "FAIL",
                    "details" : "connection failure: %s" % exstr(ex),
                    "return_code" : None }
                break

        self.disconnect_and_unlock()
        return rundict

    def run_local(self, commands):
        # run a bunch of commands on the local machine
        # as the handyrep user
        # exit on the first failure
        rundict = { "result": "SUCCESS",
            "details" : "no commands provided",
            "return_code" : None }
        for command in commands:
            try:
                runit = call(command, shell=True)
                rundict.update({ "details" : "ran command %s" % command ,
                    "return_code" : runit })
            except Exception as ex:
                rundict = { "result" : "FAIL",
                    "details" : "execution failure: %s" % self.exstr(ex),
                    "return_code" : None }
                break

        return rundict

    def file_exists(self, servername, filepath):
        # checks whether a particular file or directory path
        # exists
        # returns only true or false rather than RD
        env.key_filename = self.servers[servername]["ssh_key"]
        env.user = self.servers[servername]["ssh_user"]
        env.disable_known_hosts = True
        env.host_string = self.servers[servername]["hostname"]
        if exists(filepath, use_sudo=True):
            return True
        else:
            return False

    def push_template(self, servername, templatename, destination, template_params, new_owner=None, file_mode=700):
        # renders a template file and pushes it to the
        # target location on an external server
        # not implemented for writing to localhost at this time
        lock_fabric()
        env.key_filename = self.servers[servername]["ssh_key"]
        env.user = self.servers[servername]["ssh_user"]
        env.disable_known_hosts = True
        env.host_string = self.servers[servername]["hostname"]
        try:
            upload_template( templatename, destination, use_jinja=True, context=template_params, template_dir=self.conf["handyrep"]["templates_dir"], use_sudo=True )
            if file_mode:
                sudo("chmod %d %s" % (file_mode, destination,), quiet=True)
            if new_owner:
                sudo("chown %s %s" % (new_owner, destination,), quiet=True)
        except:
            retdict = return_dict(False, "could not push template %s to server %s" % (templatename, servername,))
        else:
            retdict = return_dict(True, "pushed template")
        finally:
            self.disconnect_and_unlock()

        return retdict

    def get_conf(self, *args):
        # a "safe" configuration reader
        # gets a single option or returns None if that option isn't set
        # instead of erroring
        myconf = self.conf
        for key in args:
            try:
                myconf = myconf[key]
            except:
                return None

        return myconf

    def pluginconf(self, confkey):
        # gets the config dictionary for the plugin
        # or returns an empty dict if none
        conf = self.get_conf("plugins",self.__class__.__name__,confkey)
        return conf

    def get_myconf(self):
        confname = self.__class__.__name__
        if confname in self.conf["plugins"]:
            return self.conf["plugins"][confname]
        else:
            return None

    def get_serverinfo(self, *args):
        # a "safe" configuration reader for server configuration
        # gets a single option or returns None if that option isn't set
        # instead of erroring
        myconf = self.servers
        for key in args:
            try:
                myconf = myconf[key]
            except:
                return None

        return myconf

    def log(self, category, message, iserror=False):
        if iserror:
            logging.error("%s: %s" % (category, message,))
        else:
            logging.info("%s: %s" % (category, message,))
        return

    def get_master_name(self):
        for servname, servdata in self.servers.iteritems():
            if servdata["role"] == "master" and servdata["enabled"]:
                return servname
        # no master?  return None and let the calling function
        # handle it
        return None

    def connection(self, servername, autocommit=False):
        # connects as the handyrep user to a remote database
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

        return mconn

    def failwait(self):
        time.sleep(self.conf["failover"]["fail_retry_interval"])
        return

    def sorted_replicas(self, maxstatus=2):
        # returns a list of currently enabled and running replicas
        # sorted by failover_priority
        goodreps = {}
        for serv, servdeets in self.servers.iteritems():
            if servdeets["enabled"] and servdeets["status_no"] <= maxstatus and servdeets["role"] == "replica":
                goodreps[serv] = servdeets["failover_priority"]

        sreps = sorted(goodreps,key=goodreps.get)
        return sreps

    def test_plugin_conf(self, pluginname, *args):
        # loops through the list of given parameters and
        # makes sure they all exist and are populated
        pconf = self.get_conf("plugins",pluginname)
        if not pconf:
            return self.rd(False, "configuration for %s not found" % pluginname)
        
        missing_params = []
        for param in args:
            if param in pconf:
                if not pconf[param]:
                    missing_params.append(param)
            else:
                missing_params.append(param)

        if len(missing_params) > 0:
            return self.rd(False, "missing parameters: %s" % ','.join(missing_params))
        else:
            return self.rd(True, "config passed")

    def get_servers(self, **kwargs):
        # loops through self.servers, returning
        # servers whose criteria match kwargs
        # returns a list of server names
        servlist = []
        # append "enabled" to criteria if not supplied
        if "enabled" not in kwargs:
            kwargs.update({ "enabled" : True })
        elif kwargs["enabled"] is None:
            # if None, then the user doesn't care
            # about enabled status
            del kwargs["enabled"]

        for serv, servdeets in self.servers.iteritems():
            if all((tag in servdeets and servdeets[tag] == val) for tag, val in kwargs.iteritems()):
                servlist.append(serv)

        return servlist

    # type conversion functions for config files

    def is_true(self, confstr):
        if confstr:
            if type(confstr) is bool:
                return confstr
            if confstr.lower() in ("1","on","true","yes"):
                return True
            else:
                return False
        else:
            return False

    def as_int(self, confstr):
        if confstr:
            if type(confstr) is int:
                return confstr
            else:
                if re.match(r'\d+$',confstr):
                    return int(confstr)
                else:
                    return None
        else:
            return None

    def disconnect_and_unlock(self):
        disconnect_all()
        lock_fabric(False)
        return True

    # the functions below are shell functions for stuff in
    # misc_utils and dbfunctions  they're created here so that
    # users don't need to reimport them when writing functions

    def ts_string(self, some_ts):
        return ts_string(some_ts)

    def string_ts(self, some_string):
        return string_ts(some_string)

    def now_string(self):
        return now_string()

    def succeeded(self, retdict):
        return succeeded(retdict)

    def failed(self, retdict):
        return failed(retdict)

    def rd(self, success, details, extra={}):
        return return_dict(success,details,extra)

    def get_one_val(self, cur, statement, params=[]):
        return get_one_val(cur, statement, params)

    def get_one_row(self, cur, statement, params=[]):
        return get_one_row(cur, statement, params)

    def execute_it(self, cur, statement, params=[]):
        return execute_it(cur, statement, params)

    def exstr(self, errorobj):
        return exstr(errorobj)

    