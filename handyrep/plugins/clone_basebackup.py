# generic failure plugin
# designed to substitute for a real plugin when
# the real plugin errors out
# this way we can hand a readable error message up the stack

from plugins.handyrepplugin import HandyRepPlugin

class clone_basebackup(HandyRepPlugin):

    def run(self, servername, clonefrom, reclone):
        # clear the remote directory if recloning
        if reclone:
            delcmd = "rm -rf %s/*" % self.servers[servername]["pgdata"]
            delit = self.run_as_root(servername, delcmd)
            if failed(delit):
                return self.rd(False, "Unable to clear PGDATA directory, aborting")

        # run pgbasebackup
        myconf = self.get_conf("plugins","clone_basebackup")
        if myconf:
            bbparam = { "path" : myconf["basebackup_path"],
                "extra" : myconf["extra_parameters"] }
            if not bbparam["extra"]:
                bbparam["extra"]=""
        else:
            bbparam = { "path" : "pg_basebackup", "extra" : "" }

        bbparam.update({ "pgdata" : self.servers[servername]["pgdata"],
            "host" : self.servers[clonefrom]["hostname"],
            "port" : self.servers[clonefrom]["port"],
            "user" : self.conf["handyrep"]["replication_user"],
            "pass" : self.conf["handyrep"]["replication_pass"]})
        pgbbcmd = "%(path)s -x -D %(pgdata)s -h %(host)s -p %(port)d -U %(user)s %(extra)s" % bbparam
        cloneit = self.run_as_replication(servername, [pgbbcmd,])
        return cloneit

    def test(self,servername):
        #check if we have a config
        if failed(self.test_plugin_conf("clone_basebackup","basebackup_path")):
            return self.rd(False, "clone_basebackup not properly configured")
        #check if the basebackup executable
        #is available on the server
        if failed(self.run_as_postgres(servername,"%s --help" % self.conf["plugins"]["clone_basebackup"]["basebackup_path"])):
            return self.rd(False, "pg_basebackup executable not found")

        return self.rd(True, "clone_basebackup works")
