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
        delmin = (as_int(self.conf["plugins"]["archive_delete_find"]["archive_delete_hours"]) * 60)
        archiveserver = self.servers[archiveinfo["archive_server"]]
        find_delete = """find %s -regextype 'posix-extended' -maxdepth 1  -mmin +%d -regex '.*[0-9A-F]{24}' -delete""" % (archiveinfo["archive_directory"],delmin,)
        adelete = self.sudorun(archiveserver,find_delete,archiveinfo["archive_owner"])
        if self.succeeded(adelete):
            return adelete
        else:
            return adelete.update( {"details" : "archive cleaning failed due to error: %s" % adelete["details"]})

    def test(self, conf, servers, servername):
        # not defined yet
        return { "result" : "SUCCESS" }
