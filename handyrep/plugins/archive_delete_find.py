# plugin method for deleting files from an archive
# using the linux "find" commmand.

from plugins.handyrepplugin import HandyRepPlugin

class archive_delete_find(HandyRepPlugin):
    # plugin to delete old archive files from a shared archive
    # using linux "find" command

    def run(self):
        archiveinfo = self.conf["archive"]
        archiveserver = self.servers[archiveinfo["archive_server"]]
        find_delete = """find %s -regextype 'posix-extended' -maxdepth 1  -mmin +%d -regex '.*[0-9A-F]{24}' -delete""" % (archiveinfo["archive_directory"],archiveinfo["archive_delete_hours"} * 60,)
        adelete = self.sudorun(archiveserver,find_delete,archiveinfo["archive_owner"])
        if self.succeeded(adelete):
            return adelete
        else:
            return adelete.update( "details" : "archive cleaning failed due to error: %s", adelete["details"])

    def test(self, conf, servers, servername):
        # not defined yet
        return { "result" : "SUCCESS" }
