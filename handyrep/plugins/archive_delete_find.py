# plugin method for deleting files from an archive
# using the linux "find" commmand.
# this only works if you have a configuration
# with a single archive server which is
# defined in the servers dictionary

from plugins.handyrepplugin import HandyRepPlugin

class archive_delete_find(HandyRepPlugin):
    # plugin to delete old archive files from a shared archive
    # using linux "find" command

    def run(self):
        archiveinfo = self.conf["archive"]
        myconf = self.get_myconf()
        delmin = (as_int(myconf["archive_delete_hours"]) * 60)
        archiveserver = self.get_archiveserver()
        if not archiveserver:
            return self.rd(False, "no archive server is defined")
        
        find_delete = """find %s -regextype 'posix-extended' -maxdepth 1  -mmin +%d -regex '.*[0-9A-F]{24}' -delete""" % (myconf["archive_directory"],delmin,)
        adelete = self.run_as_root(archiveserver,[find_delete,])
        if self.succeeded(adelete):
            return adelete
        else:
            adelete.update( {"details" : "archive cleaning failed due to error: %s" % adelete["details"]})
            return adelete

    def test(self):
        archserv = self.get_archiveserver()
        if not archserv:
            return self.rd(False, "no archive server is defined")

        if self.failed(self.test_plugin_conf("archive_delete_find", "archive_directory", "archive_delete_hours")):
            return self.rd(False, "archive_delete_find is not configured correctly")
        else:
            return self.rd(True, "archive_delete_find is configured")

    def get_archiveserver(self):
        # assumes that there's only one enabled archive server
        archservs = self.get_servers(role="archive")
        if archservs:
            return archservs[0]
        else:
            return None
