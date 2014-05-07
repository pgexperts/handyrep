# plugin method for failing over connections
# using pgbouncer
# rewrites the list of databases

# plugin for users running multiple pgbouncer servers
# requires that each pgbouncer server be in the servers dictionary
# as role "pgbouncer" and enabled.

# also intended to be run with the latest pgbouncer update which supports
# include files for pgbouncer, instead of writing directly to pgbouncer.ini;
# will not work correctly on standard pgbouncer
# this plugin expects you to configure pgbouncer.ini, and to set up the
# %include directives

# further, this plugin requires that the handyrep user, DB and password be set
# up on pgbouncer as a valid connection string.

# configuration:
'''
    [[multi_pgbouncer_bigip]]
        pgbouncerbin = "/usr/sbin/pgbouncer"
        dblist_template = pgbouncer_dblist.ini.template
        owner = postgres
        config_location = "/etc/pgbouncer/pgbouncer.ini"
        dblist_location = "/etc/pgbouncer/db_cluster1.ini"
        database_list = postgres, libdata, pgbench
        readonly_suffix = _ro
        all_replicas = False
        extra_connect_param =
'''

from plugins.handyrepplugin import HandyRepPlugin

class multi_pgbouncer_bigip(HandyRepPlugin):

    def run(self, newmaster=None):
        # used for failover of all pgbouncer servers
        if newmaster:
            master = newmaster
        else:
            master = self.get_master_name()
        blist = self.bouncer_list()
        faillist = []
        disablelist = []
        for bserv in blist:
            bpush = self.push_config(bserv, master)
            if self.failed(bpush):
                self.set_bouncer_status(bserv, "unavailable", 4, "unable to reconfigure pgbouncer server for failover")
                # bad bouncer, better disable it at BigIP
                if failed(self.disable_bouncer(bserv)):
                    faillist.append(bserv)
                else:
                    disablelist.append(bserv)

        if faillist:
            # report failure if we couldn't reconfigure any of the servers
            return self.rd(False, "some pgbouncer servers did not change their configuration at failover, and could not be removed from bigip: %s" % ','.join(faillist))
        elif disablelist:
            if ( len(disablelist) + len(faillist) ) == len(blist):
                return self.rd(False, "all pgbouncers not responding and disabled")
            else:
                return self.rd(True, "some pgbouncers failed over, but others had to be disabled in BigIP: %s" % ','.join(disablelist))
        else:
            return self.rd(True, "pgbouncer failover successful")

    def init(self, bouncerserver=None):
        # used to initialize proxy servers with the correct connections
        # either for just the supplied bouncer server, or for all of them
        if bouncerserver:
            blist = [bouncerserver,]
        else:
            blist = self.bouncer_list()

        master = self.get_master_name()
        faillist = []
        for bserv in blist:
            bpush = self.push_config(bserv, master)
            # if we can't push a config, then add this bouncer server to the list
            # of failed servers and mark it unavailable
            if self.failed(bpush):
                self.set_bouncer_status(bserv, "unavailable", 4, "unable to reconfigure pgbouncer server for failover")
                faillist.append(bserv)
            else:
                try:
                    pgbcn = self.connection(bserv)
                except:
                    self.set_bouncer_status(bserv, "unavailable", 4, "pgbouncer configured, but does not accept connections")
                    faillist.append(bserv)
                else:
                    pgbcn.close()
                    self.set_bouncer_status(bserv, "healthy", 1, "pgbouncer initialized")

        if faillist:
            # report failure if we couldn't reconfigure any of the servers
            return self.rd(False, "some pgbouncer servers could not be initialized: %s" % ','.join(faillist))
        else:
            return self.rd(True, "pgbouncer initialization successful")
        

    def set_bouncer_status(self, bouncerserver, status, status_no, status_message):
        self.servers[bouncerserver]["status"] = status
        self.servers[bouncerserver]["status_no"] = status_no
        self.servers[bouncerserver]["status_message"] = status_message
        self.servers[bouncerserver]["status_ts"] = self.now_string()
        return

    def push_config(self, bouncerserver, newmaster=None):
        # pushes a new config to the named pgbouncer server
        # and restarts it
        if newmaster:
            master = newmaster
        else:
            master = self.get_master_name()
        # get configuration
        dbsect = { "dbsection" : self.dbconnect_list(master) }
        # push new config
        myconf = self.get_myconf()
        writeconf = self.push_template(bouncerserver,myconf["dblist_template"],myconf["dblist_location"],dbsect,myconf["owner"])
        if self.failed(writeconf):
            return self.rd(False, "could not push new pgbouncer configuration to pgbouncer server")
        # restart pgbouncer
        restart_command = "%s -u %s -d -R %s" % (myconf["pgbouncerbin"],myconf["owner"],myconf["config_location"],)
        rsbouncer = self.run_as_root(bouncerserver,[restart_command,])
        if self.succeeded(rsbouncer):
            return self.rd(True, "pgbouncer configuration updated")
        else:
            return self.rd(False, "unable to restart pgbouncer")

    def bouncer_list(self):
        # gets a list of currently enabled pgbouncers
        blist = []
        for serv, servdeets in self.servers.iteritems():
            if servdeets["role"] == "pgbouncer" and servdeets["enabled"]:
                blist.append(serv)

        return blist


    def test(self):
        #check that we have all config variables required
        if self.failed( self.test_plugin_conf("multi_pgbouncer_bigip","pgbouncerbin","dblist_template","owner","config_location","dblist_location", "database_list","readonly_suffix","all_replicas","bigip_user","tmsh_path")):
            return self.rd(False, "multi-pgbouncer-bigip failover is not configured" )
        #check that we can connect to the pgbouncer servers
        blist = self.bouncer_list()
        if len(blist) == 0:
            return self.rd(False, "No pgbouncer servers defined")
        
        faillist = []
        for bserv in blist:
            if self.failed(self.run_as_root(bserv,self.conf["handyrep"]["test_ssh_command"])):
                faillist.append(bserv + ' SSH failed')

            if not "ip_address" in self.servers[bserv]:
                faillist.append(bserv + ' no IP address')
            else:
                if not self.servers[bserv]["ip_address"]:
                    faillist.append(bserv + ' no IP address')

        if failist:
            return self.rd(False, "some pgbouncer servers are incorrectly configured: %s" % ','.join(faillist))

        if not self.get_bigip():
            return self.rd(False, "BigIP server is not configured")
        
        return self.rd(True, "pgbouncer setup is correct")


    def get_bigip(self):
        # checkfor bigip server
        isbig = None
        for serv, servdeets in self.servers.iteritems():
            if servdeets["role"] == "bigip" and servdeets["enabled"]:
                isbig = serv

        return isbig

    def poll(self, bouncerserver=None):
        if bouncerserver:
            blist = [bouncerserver,]
        else:
            blist = self.bouncer_list()

        if len(blist) == 0:
            return self.rd(False, "No pgbouncer servers defined")

        faillist = []
        for bserv in blist:
            try:
                pgbcn = self.connection(bserv)
            except:
                self.set_bouncer_status(bserv, "unavailable", 4, "pgbouncer does not accept connections")
                faillist.append(bserv)
            else:
                pgbcn.close()
                self.set_bouncer_status(bserv, "healthy", 1, "pgbouncer responding")
                
        if faillist:
            # report failure if any previously enabled bouncers are down
            return self.rd(False, "some pgbouncer servers are not responding: %s" % ','.join(faillist))
        else:
            return self.rd(True, "all pgbouncers responding")

    def dbconnect_list(self, master):
        # creates the list of database aliases and target
        # servers for pgbouncer
        # build master string first
        myconf = self.get_myconf()
        dblist = myconf["database_list"]
        # add in the handyrep db if the user has forgotten it
        if self.conf["handyrep"]["handyrep_db"] not in dblist:
            dblist.append(self.conf["handyrep"]["handyrep_db"])
        constr = self.dbconnect_line(dblist, self.servers[master]["hostname"], self.servers[master]["port"], "", myconf["extra_connect_param"])
        replicas = self.sorted_replicas()
        if self.is_true(myconf["all_replicas"]):
            #if we're doing all replicas, we need to put them in as _ro0, _ro1, etc.
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
            if len(replicas) > 0:
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

    def disable_bouncer(self, bouncername):
        # calls BigIP via ssh to disable one or more pgbouncers
        # if that pgbouncer isn't responding during a failover
        myconf = self.conf["plugins"]["multi_pgbouncer_bigip"]
        disablecmd = "%s modify ltm node %s state user-down" % (myconf["tmsh_path"], self.servers[bouncername]["ip_address"],)
        bigserv = self.get_bigip()
        sshpasswd = self.get_conf("passwords","bigip_password")
        if bigserv:
            disableit = self.sudorun(bouncername,bigserv, [disablecmd,], myconf["bigip_user"], sshpass=sshpasswd)
            if self.succeeded(disableit):
                return self.rd(True, "bouncer %s disabled" % bouncername)
            else:
                return self.rd(False, "bouncer %s could not be disabled" % bouncername)
        else:
            return self.rd(False, "bouncer %s could not be disabled because bigip is not configured" % bouncername)
    