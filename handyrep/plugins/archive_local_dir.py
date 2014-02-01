# archiving script plugin
# archives to locally mounted directory
# on master server; intended for use
# with SANs and similar setups

from plugins.handyrepplugin import HandyRepPlugin

class archive_local_dir(HandyRepPlugin):

    def run(self, servername):
        # pushes archive script
        # which is set up for two-server archiving
        archiveinfo = self.conf["archive"]
        myconf = self.get_myconf()
        
        archdict = { "archive_directory" : myconf["archive_directory"],
            "no_archive_file" : "stop_archiving_file"}
        pushit = self.push_template(servername, myconf["archive_script_template"], myconf["archive_script_path"], archdict, self.conf["handyrep"]["postgres_superuser"],
        700)
        return pushit

    def recoveryline(self):
        # returns archive recovery line for recovery.conf
        myconf = self.get_myconf()
        restcmd = "restore_command = cp %s" % myconf["archive_directory"]
        restcmd += "/%f %p\n\n"
        
        if self.is_true(myconf["cleanup_archive"]):
            restcmd += "archive_cleanup_command = '%s %s" % (myconf["archive_directory"], myconf["archivecleanup_path"],) + "%r'\n"
            
        return restcmd

    def poll(self):
        # does nothing
        return self.rd(True, "Nothing to poll")

    def stop(self):
        # halts archiving on the master
        # by pushing a noarchving file
        myconf = self.get_myconf()
        touchit = "touch %s" % myconf["stop_archiving_file"]
        disabled = self.run_as_postgres(self.get_master_name(),[touchit,])
        if succeeded(touchit):
            return self.rd(True, "Created noarchiving touch file")
        else:
            return self.rd(False, "Unable to create noarchiving file")

    def start(self):
        # push template first
        master = self.get_master_name()
        myconf = self.get_myconf()
        if failed(self.run(master)):
            return self.rd(False, "unable to update archving script")

        touchit = "rm -f %s" % myconf["stop_archiving_file"]
        disabled = self.run_as_postgres(master,[touchit,])
        if succeeded(touchit):
            return self.rd(True, "Removed noarchiving touch file")
        else:
            return self.rd(False, "Unable to remove noarchiving file")

    def test(self, conf, servers, servername):
        if self.failed(self.test_plugin_conf("archive_directory","archivecleanup_path","stop_archving_file","archive_script_template","archive_script_path")):
            return self.rd(False, "archive_local_dir is not configured")
        else:
            return self.rd(True, "archive_local_dir is configured")

