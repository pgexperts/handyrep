# plugin method for start/stop/restart/reload of a postgresql
# server using pg_ctl and the data directory
# also works as a template plugin example

from plugins.handyrepplugin import HandyRepPlugin

class promote_pg_ctl(HandyRepPlugin):

    def get_pg_ctl_cmd(self, servername, runmode):
        cmd = self.get_conf("plugins", "restart_pg_ctl","pg_ctl_path")
        dbloc = self.servers[servername]["pgdata"]
        extra = cmd = self.get_conf("plugins", "restart_pg_ctl","pg_ctl_flags")
        if cmd:
            return "%s -D %s %s %s" % (cmd, dbloc, extra, runmode,)
        else:
            return "pg_ctl -D %s %s %s" % (dbloc, extra, runmode,)

    def run(self, servername):
        startcmd = self.get_pg_ctl_cmd(servername, "status")
        runit = self.run_as_postgres(servername, [startcmd,])
        return runit
        
    def test(self, servername):
        startcmd = self.get_pg_ctl_cmd(servername, "status")
        runit = self.run_as_postgres(servername, [startcmd,])
        return runit