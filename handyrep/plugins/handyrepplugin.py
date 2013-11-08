from fabric.api import sudo, run, env, local, settings
from fabric.network import disconnect_all
from fabric.contrib.files import upload_template
from fabric.context_managers import shell_env
from lib.error import CustomError
from lib.dbfunctions import get_one_val, get_one_row, execute_it, get_pg_conn
from lib.misc_utils import ts_string, string_ts, now_string, succeeded, failed, return_dict
import json
from datetime import datetime, timedelta
import logging
import time
import psycopg2
import psycopg2.extensions
from os.path import join

class HandyRepPlugin(object):

    def __init__(self, conf, servers):
        self.conf = conf
        self.servers = servers
        return

    def sudorun(self, servername, commands, runas):
        # generic function to run one or more commands
        # as a specific remote user.  returns the results
        # of the last command run.  aborts when any
        # command fails
        env.key_filename = self.servers[servername]["ssh_key"]
        env.user = self.servers[servername]["ssh_user"]
        env.disable_known_hosts = True
        env.host_string = self.servers[servername]["hostname"]
        rundict = return_dict(True, "no commands provided", {"return_code" : None })
        for command in commands:
            try:
                runit = sudo(command, user=runas, warn_only=True)
                rundict.update({ "details" : r ,
                    "return_code" : r.return_code })
                if r.succeeded:
                    rundict.update({"result":"SUCCESS"})
                else:
                    rundict.update({"result":"FAIL"})
                    break
            except:
                rundict = { "result" : "FAIL",
                    "details" : "connection failure",
                    "return_code" : None }
                break
        
        disconnect_all()
        return rundict

    def run_as_postgres(self, servername, commands):
        pguser = self.servers[servername]["postgres_superuser"]
        return self.sudorun(servername, commands, pguser)

    def run_as_root(self, servername, commands):
        return self.sudorun(servername, commands, "root")

    def run_as_handyrep(self, servername, commands):
        # runs a set of commands as the "handyrep" user
        # exiting when the first command fails
        # returns a dic with the results of the last command
        # run
        env.key_filename = self.servers[servername]["ssh_key"]
        env.user = self.servers[servername]["ssh_user"]
        env.disable_known_hosts = True
        env.host_string = self.servers[servername]["hostname"]
        rundict = { "result": "SUCCESS",
            "details" : "no commands provided",
            "return_code" : None }
        for command in commands:
            try:
                runit = run(command, warn_only=True)
                rundict.update({ "details" : r ,
                    "return_code" : r.return_code })
                if r.succeeded:
                    rundict.update({"result":"SUCCESS"})
                else:
                    rundict.update({"result":"FAIL"})
                    break
            except:
                rundict = { "result" : "FAIL",
                    "details" : "connection failure",
                    "return_code" : None }
                break

        disconnect_all()
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
                runit = local(command, capture=True)
                rundict.update({ "details" : runit ,
                    "return_code" : runit.return_code })
                if runit.succeeded:
                    rundict.update({"result":"SUCCESS"})
                else:
                    rundict.update({"result":"FAIL"})
                    break
            except:
                rundict = { "result" : "FAIL",
                    "details" : "connection failure",
                    "return_code" : None }
                break
        return rundict
        disconnect_all()

    def push_template(self, servername, templatename, destination, template_params, new_owner=None, file_mode=700):
        # renders a template file and pushes it to the
        # target location on an external server
        # not implemented for writing to localhost at this time
        env.key_filename = self.servers[servername]["ssh_key"]
        env.user = self.servers[servername]["ssh_user"]
        env.disable_known_hosts = True
        env.host_string = self.servers[servername]["hostname"]
        try:
            upload_template( templatename, destination, use_jinja=True, context=template_params, template_dir=self.conf["handyrep"]["templates_dir"], use_sudo=True, use_mode=file_mode )
            if new_owner:
                sudo("chown %s %s" % (new_owner, destination,))
        except:
            retdict = return_dict(False, "could not push template %s to server %s" % (templatename, servername,))
        else:
            retdict = return_dict(True, "pushed template")
        finally:
            disconnect_all()

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
        conf = get_conf("plugins",self.__class__.__name__,confkey)
        return conf

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

    def get_replica_list(self):
        reps = []
        reps.append(self.get_replicas_by_status("healthy"))
        reps.append(self.get_replicas_by_status("lagged"))
        return reps

    def get_master_name(self):
        for servname, servdata in self.servers.iteritems():
            if servdata["role"] == "master" and servdata["enabled"]:
                return servname
        # no master?  return None and let the calling function
        # handle it
        return None

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

    # the functions below are shell functions for stuff in
    # misc_utils and dbfunctions  they're created here so that
    # users don't need to reimport them when writing functions

    def ts_string(self, some_ts):
        return ts_string(some_ts)

    def string_ts(self, some_string):
        return string_ts(some_string)

    def now_string(self):
        return now_string()

    def succeeded(self, retdict);
        return succeeded(retdict)

    def failed(self, retdict):
        return failed(retdict)

    def rd(self, success, details, extra):
        return return_dict(success,details,extra)

    def get_one_val(cur, statement, params=[]):
        return get_one_val(cur, statement, params)

    def get_one_row(cur, statement, params=[]):
        return get_one_row(cur, statement, params)

    def execute_it(cur, statement, params=[]):
        return execute_it(cur, statement, params)
    