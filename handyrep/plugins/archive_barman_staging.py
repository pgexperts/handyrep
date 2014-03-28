# archiving script plugin
# designed for systems with only two PostgreSQL servers
# where the archive logs are written to whichever server
# is the replica at the time, and a separate barman server
# wal files are copied to an additional staging directory
# before being copied off to the barman server by the poll()
# method.

# this means that we give each server the other server
# as its replica target

# WARNING: Assumes that there's only two enabled servers
# in the configuration.  Will break if there are more
# than two!

# depending on settings, may automatically disable
# archive replication if the replica is down

from plugins.handyrepplugin import HandyRepPlugin

class archive_barman_staging(HandyRepPlugin):

    def run(self, servername):
        # pushes archive script
        # which is set up for two-server archiving
        self.log("ARCHIVE","pushing archive script")
        archiveinfo = self.conf["archive"]
        myconf = self.get_myconf()
        otherserv = self.other_server(servername)
        if not otherserv:
            return self.rd(False, "no other server configured for archving")
        
        archdict = { "archive_directory" : myconf["archive_directory"],
            "no_archive_file" : "stop_archiving_file",
            "archive_host" : otherserv,
            "staging_dir" : myconf["barman_staging_dir"] }
        pushit = self.push_template(servername, myconf["archive_script_template"], myconf["archive_script_path"], archdict, self.conf["handyrep"]["postgres_superuser"],
        700)
        if self.failed(pushit):
            return pushit

        pushit = self.push_template(servername, myconf["copy_script_template"], myconf["copy_script_location"], archdict, self.conf["handyrep"]["postgres_superuser"], 700)
        if self.failed(pushit):
            return pushit

        # if that worked, let's make sure the rest of the setup is complete
        # make archive directory
        if not self.file_exists(otherserv, myconf["archive_directory"]):
            createcmd = "mkdir %s" % myconf["archive_directory"]
            self.run_as_postgres(otherserv, [createcmd,])
        # make barman directory
        if not self.file_exists(servername, myconf["barman_staging_dir"]):
            createcmd = "mkdir %s" % myconf["barman_staging_dir"]
            self.run_as_postgres(servername, [createcmd,])

        return self.rd(True, "archive script pushed")

    def recoveryline(self):
        # returns archive recovery line for recovery.conf
        myconf = self.get_myconf()
        restcmd = """restore_command = 'cp %s""" % myconf["archive_directory"]
        restcmd += "/%f %p'\n\n"
        restcmd += "archive_cleanup_command = '%s %s" % (myconf["archivecleanup_path"], myconf["archive_directory"],) + " %r'\n"
        return restcmd

    def poll(self):
        # what it does is checks to see if the
        # replica is unsshable
        # and then disables archiving depending
        # on settings via the stop archiving file
        self.log("ARCHIVE","Polling Archving")

        # first, though, we need to spool wal logs off to
        # the barman server
        # try the currently enabled barman server
        master = self.get_master()
        
        for barman_target in self.get_barman_hosts():
            barspool = "%s %s %s" % ( myconf["copy_script_location"], barman_target, myconf["barman_incoming_dir"] )
            barspooled = self.run_as_postgres(master, myconf["barman_copy_script"], [barspool,])

            # if it failed, try the alternate barman server
            # and change which one is enabled
            if self.failed(barspooled):
                self.
                self.log("ARCHIVE","Barman host %s failed.  Trying new barman host.", True)
            else:
                
            barman_target = self.get_barman_host(replace=True)
            if barman_target:
                barspool = "%s %s %s" % ( myconf["copy_script_location"], barman_target, myconf["barman_incoming_dir"] )
                barspooled = self.run_as_postgres(master, myconf["barman_copy_script"], [barspool,])

        # if both failed, log error and proceed
        self.get_barman_host(failed=True)
        self.log("ARCHIVE","All Barman hosts failed", True)

        repservs = self.get_servers(role="replica")
        myconf = self.get_myconf()
        if not repservs:
            return self.rd("False","no currently configured replica")
        else:
            if myconf["disable_on_fail"]:
                repstat = self.servers[repservs[0]]["status_no"]
                if not self.get_master_name():
                    return self.rd(False, "no configured master")
                
                if repstat > 3:
                    # replica is down, check that we can ssh to it
                    sshcheck = self.run_as_handyrep(repservs[0], [self.conf["handyrep"]["test_ssh_command"],])
                    if self.failed(sshcheck):
                        touchit = "touch %s" % myconf["stop_archiving_file"]
                        disabled = self.run_as_postgres(self.get_master_name(),[touchit,])
                        if succeeded(disabled):
                            self.log("ARCHIVE","Archiving disabled due to replica failure", True)
                            return self.rd(True, "disabled archiving")
                        else:
                            self.log("ARCHIVE","Unable to disable archiving despite replica failure", True)
                            return self.rd(False, "Unable to disable archiving")
                    else:
                        return self.rd(True, "replica responds to ssh")
            else:
                return self.rd(True, "auto-disable not configured")

    def stop(self):
        # halts archiving on the master
        # by pushing a noarchving file
        myconf = self.get_myconf()
        touchit = "touch %s" % myconf["stop_archiving_file"]
        disabled = self.run_as_postgres(self.get_master_name(),[touchit,])
        if self.succeeded(disabled):
            return self.rd(True, "Created noarchiving touch file")
        else:
            return self.rd(False, "Unable to create noarchiving file")

    def start(self):
        # push template first
        myconf = self.get_myconf()
        master = self.get_master_name()
        if self.failed(self.run(master)):
            return self.rd(False, "unable to update archving script")

        touchit = "rm -f %s" % myconf["stop_archiving_file"]
        enabled = self.run_as_postgres(master,[touchit,])
        if self.succeeded(enabled):
            return self.rd(True, "Removed noarchiving touch file")
        else:
            return self.rd(False, "Unable to remove noarchiving file")

    def test(self):
        if self.failed(self.test_plugin_conf("archive_barman_staging","archive_directory","archivecleanup_path","stop_archiving_file","archive_script_template","archive_script_path","barman_staging_dir")):
            return self.rd(False, "archive_barman_staging is not configured")
        else:
            if self.failed(self.run_as_postgres(self.get_master_name(), [self.conf["handyrep"]["test_ssh_command"],])):
                return self.rd(False, "cannot ssh as postgres to master")
            else:
                return self.rd(True, "archive_two_servers configured")

    def other_server(self, servername):
        # returns the name of the other server
        for serv, servdeets in self.servers.iteritems():
            if servdeets["enabled"] and serv <> servername and servdeets["role"] in ["master","replica",]:
                return serv

        return None

    def get_barman_host(self, replace=False, failed=False):
        if failed:
            barmen = get_servers(role="barman")
            for bserv in barmen:
                self.servers[bserv]["status_no"] = 5
                self.servers[bserv]["status"] = "down"
            return None
            
        if replace:
            barmen = get_servers(role="barman")
            retbar = ""
            for bserv in barmen:
                if self.servers[bserv]["status_no"] = 1:
                    self.servers[bserv]["status_no"] = 5
                    self.servers[bserv]["status"] = "down"
                else:
                    retbar = bserv
            return None


        
