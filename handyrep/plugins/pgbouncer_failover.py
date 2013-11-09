# plugin method for failing over connections
# using pgbouncer
# rewrites the list of databases

from plugins.handyrepplugin import HandyRepPlugin

class pgbouncer_failover(HandyRepPlugin):

    def run(self, newmaster=None):
        #writes a new pgbouncer file and then restarts
        #pgbouncer using pgbouncers own methods
        if newmaster:
            master = newmaster
        else:
            master = self.get_master_name()
        # get configuration
        dbsect = { "dbsection" : dbconnect_list(master) }
        # push new config
        myconf = self.conf["plugins"]["pgbouncer_failover"]
        writeconf = self.push_template(myconf["server"],myconf["template"],myconf["config_location"],dbsect,myconf["owner"])
        if failed(writeconf):
            return self.rd(False, "could not push new pgbouncer configuration to pgbouncer server")
        # restart pgbouncer
        rsbouncer = self.run_as_root(myconf["server"],[myconf["restart_command"],])
        if succeeded(rsbouncer):
            return self.rd(True, "pgbouncer configuration updated")
        else:
            return self.rd(False, "unable to restart pgbouncer")

    def setup(self):
        return self.run()

    def test(self):
        #check that we have all config variables required
        #check that we can connect to the pgbouncer server
        #and check status
        return return_dict(True, "pgbouncer failover works")

    def dbconnect_list(self, master):
        # creates the list of database aliases and target
        # servers for pgbouncer
        # build master string first
        myconf = self.conf["plugins"]["pgbouncer_failover"]
        constr = dbconnect_line(myconf["database_list"], self.servers[master]["hostname"], self.servers[master]["port"], "", myconf["extra_connect_param"])
        replicas = self.sorted_replicas()
        if self.conf["plugins"]["pgbouncer_failover"]["all_replicas"]:
            #if we're doing all replicas, we need to put them in as _ro0, _ro1, etc.
            repno = 0
            for rep in replicas:
                if not rep == master:
                    rsuff = "%s%d" % (myconf["readonly_suffix"],repno,)
                    constr += dbconnect_line(myconf["database_list"], self.servers[rep]["hostname"], self.servers[rep]["port"], rsuff, myconf["extra_connect_param"])
                    repno += 1
        else:
            # only one readonly replica, setting it up with _ro
            if replicas[0] = master:
                # avoid the master
                replicas.pop(0)
            if len(replicas) > 0:
                constr += dbconnect_line(myconf["database_list"], self.servers[replicas[0]]["hostname"], self.servers[replicas[0]]["port"], myconf["readonly_suffix"], myconf["extra_connect_param"])

        return constr

    def dbconnect_line(self, database_list, hostname, portno, suffix, extra):
        confout = ""
        if extra:
            nex = extra
        else:
            nex = ""
        for dbname in database_list:
            confout += "%s%s = dbname=%s host=%s port=%s %s \n" % (dbname, suffix, dbname, hostname, portno, nex,)

        return confout

    