from fabric.api import sudo, run, env, local, settings
from fabric.network import disconnect_all
from handyrep.lib.error import CustomError
import json
from datetime import datetime, timedelta
import logging
import time

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
        rundict = { "result": "SUCCESS"
            "details" : "no commands provided",
            "return_code" : None }
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
        
        diconnect_all()
        return rundict

    def run_as_postgres(self, servername, commands):
        pguser = self.servers[servername]["postgres_superuser"]
        return sudorun(servername, commands, pguser)

    def run_as_root(self, servername, commands):
        return sudorun(servername, commands, "root")

    def run_as_handyrep(self, servername, commands):
        # runs a set of commands as the "handyrep" user
        # exiting when the first command fails
        # returns a dic with the results of the last command
        # run
        env.key_filename = self.servers[servername]["ssh_key"]
        env.user = self.servers[servername]["ssh_user"]
        env.disable_known_hosts = True
        env.host_string = self.servers[servername]["hostname"]
        rundict = { "result": "SUCCESS"
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
        rundict = { "result": "SUCCESS"
            "details" : "no commands provided",
            "return_code" : None }
        for command in commands:
            try:
                runit = local(command, capture=True)
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
        return rundict
        disconnect_all()

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