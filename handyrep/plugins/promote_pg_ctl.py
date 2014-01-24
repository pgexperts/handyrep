# plugin method for promoting a replica
# by running "pg_ctl promote" on the remote server
# does not do follow-up checks on promotion; those are
# done by the calling code

from plugins.handyrepplugin import HandyRepPlugin

class promote_pg_ctl(HandyRepPlugin):

    def get_pg_ctl_cmd(self, servername, runmode):
        cmd = self.get_conf("plugins", "promote_pg_ctl","pg_ctl_path")
        dbloc = self.servers[servername]["pgconf"]
        extra = self.get_conf("plugins", "promote_pg_ctl","pg_ctl_flags")
        if not cmd:
            cmd = "pg_ctl"
        return "%s -D %s %s %s" % (cmd, dbloc, extra, runmode,)

    def run(self, servername):
        startcmd = self.get_pg_ctl_cmd(servername, "promote")
        runit = self.run_as_postgres(servername, [startcmd,])
        return runit
        
    def test(self, servername):
        startcmd = self.get_pg_ctl_cmd(servername,j "status")
        runit = self.run_as_postgres(servername, [startcmd,])
        return runit