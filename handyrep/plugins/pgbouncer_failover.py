# plugin method for failing over connections
# using pgbouncer
# rewrites the list of databases

# this plugin handles having only a single pgbouncer server
# whose server location is predetermined.

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
        dbsect = { "dbsection" : self.dbconnect_list(master) }
        # push new config
        myconf = self.conf["plugins"]["pgbouncer_failover"]
        writeconf = self.push_template(myconf["server"],myconf["template"],myconf["config_location"],dbsect,myconf["owner"])
        if self.failed(writeconf):
            return self.rd(False, "could not push new pgbouncer configuration to pgbouncer server")
        # restart pgbouncer
        if myconf["refresh_method"] == "pause":
            rsbouncer = self.pause_reload()
        else:
            restart_command = "%s -u %s -d -R %s" % (myconf["pgbouncerbin"],myconf["owner"],myconf["config_location"],)
            rsbouncer = self.run_as_root(myconf["server"],[restart_command,])
        if self.succeeded(rsbouncer):
            return self.rd(True, "pgbouncer configuration updated")
        else:
            return self.rd(False, "unable to restart pgbouncer")

    def init(self):
        return self.run()

    def test(self):
        #check that we have all config variables required
        if self.failed( self.test_plugin_conf("pgbouncer_failover","server","pgbouncerbin","template","owner","config_location","database_list","readonly_suffix","all_replicas")):
            return self.rd(False, "pgbouncer failover is not configured" )
        #check that we can connect to the pgbouncer server
        if self.failed(self.run_as_root(self.conf["plugins"]["pgbouncer_failover"]["server"],self.conf["handyrep"]["test_ssh_command"])):
            return self.rd(False, "unable to ssh to pgbouncer server")
        
        return self.rd(True, "pgbouncer failover works")

    def poll(self, bouncerserver=None):
        # ignore bouncerserver param, since there's only one
        myconf = self.conf["pgbouncer_failover"]
        bserv = myconf["server"]
        
        try:
            pgbcn = self.connection(bserv)
        except:
            self.set_bouncer_status(bserv, "unavailable", 4, "pgbouncer does not accept connections")
            faillist.append(bserv)
            return self.rd(False, "cannot connect to pgbouncer server")
        else:
            pgbcn.close()
            self.set_bouncer_status(bserv, "healthy", 1, "pgbouncer responding")
            return self.rd(True, "pgbouncer responding")

    def dbconnect_list(self, master):
        # creates the list of database aliases and target
        # servers for pgbouncer
        # build master string first
        myconf = self.conf["plugins"]["pgbouncer_failover"]
        constr = self.dbconnect_line(myconf["database_list"], self.servers[master]["hostname"], self.servers[master]["port"], "", myconf["extra_connect_param"])
        replicas = self.sorted_replicas()
        if is_true(myconf["all_replicas"]):
            #if we're doing all replicas, we need to put them in as _ro0, _ro1, etc.
            repno = 0
            # if there's no replicas, set ro1 to go to the master:
            if len(replicas) == 0 or (len(replicas) == 1 and master in replicas):
                rsuff = "%s%d" % (myconf["readonly_suffix"],1,)
                constr += self.dbconnect_line(myconf["database_list"], self.servers[master]["hostname"], self.servers[master]["port"], rsuff, myconf["extra_connect_param"])
            else:
                for rep in replicas:
                    if not rep == master:
                        rsuff = "%s%d" % (myconf["readonly_suffix"],repno,)
                        constr += self.dbconnect_line(myconf["database_list"], self.servers[rep]["hostname"], self.servers[rep]["port"], rsuff, myconf["extra_connect_param"])
                        repno += 1
        else:
            # only one readonly replica, setting it up with _ro
            if replicas[0] == master:
                # avoid the master
                replicas.pop(0)
            if len(replicas) > 0:
                constr += self.dbconnect_line(myconf["database_list"], self.servers[replicas[0]]["hostname"], self.servers[replicas[0]]["port"], myconf["readonly_suffix"], myconf["extra_connect_param"])
            else:
                # if no replicas, read-only connections should go to the master
                constr += self.dbconnect_line(myconf["database_list"], self.servers[master]["hostname"], self.servers[master]["port"], myconf["readonly_suffix"], myconf["extra_connect_param"])

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

    def set_bouncer_status(self, bouncerserver, status, status_no, status_message):
        self.servers[bouncerserver]["status"] = status
        self.servers[bouncerserver]["status_no"] = status_no
        self.servers[bouncerserver]["status_message"] = status_message
        self.servers[bouncerserver]["status_ts"] = self.now_string
        return

    