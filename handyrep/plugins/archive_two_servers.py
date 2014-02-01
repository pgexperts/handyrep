# archiving script plugin
# designed for systems with only two PostgreSQL servers
# where the archive logs are written to whichever server
# is the replica at the time
# this means that we give each server the other server
# as its replica target

# WARNING: Assumes that there's only two enabled servers
# in the configuration.  Will break if there are more
# than two!

# depending on settings, may automatically disable
# archive replication if the replica is down

from plugins.handyrepplugin import HandyRepPlugin

class archive_two_servers(HandyRepPlugin):

    def run(self, servername):
        # pushes archive script
        # which is set up for two-server archiving
        archiveinfo = self.conf["archive"]
        myconf = self.get_myconf()
        otherserv = self.other_server(servername)
        if not otherserv:
            return self.rd(False, "no other server configured for archving")
        
        archdict = { "archive_directory" : myconf["archive_directory"],
            "no_archive_file" : "stop_archiving_file",
            "archive_host" : otherserv }
        pushit = self.push_template(servername, myconf["archive_script_template"], myconf["archive_script_path"], archdict, self.conf["handyrep"]["postgres_superuser"],
        700)
        return pushit

    def recoveryline(self):
        # returns archive recovery line for recovery.conf
        myconf = self.get_myconf()
        restcmd = "restore_command = cp %s" % myconf["archive_directory"]
        restcmd += "/%f %p\n\n"
        restcmd += "archive_cleanup_command = '%s %s" % (myconf["archive_directory"], myconf["archivecleanup_path"],) + "%r'\n"
        return restcmd

    def poll(self):
        # doesn't actually poll archive server
        # what it does is checks to see if the
        # replica is unsshable
        # and then disables archiving depending
        # on settings via the stop archiving file
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
                    if failed(sshcheck):
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
        if self.failed(self.test_plugin_conf("archive_two_servers","archive_directory","archivecleanup_path","stop_archiving_file","archive_script_template","archive_script_path")):
            return self.rd(False, "archive_two_servers is not configured")
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
