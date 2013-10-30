# plugin method for start/stop/restart/reload of a postgresql
# server using pg_ctl and the data directory
# also works as a template plugin example

from plugins.handyrepplugin import HandyRepPlugin

class restart_pg_ctl(HandyRepPlugin):

    def run(self, servername, runmode):
        if runmode == "start":
            return self.start(servername)
        elif runmode == "stop":
            return self.stop(servername)
        elif runmode == "faststop":
            return self.stop(servername, True)
        elif runmode == "restart":
            return self.restart(servername)
        elif runmode == "reload":
            return self.reloadpg(servername)
        elif runmode == "status":
            return self.status(servername)
        else:
            return return_dict( False, "unsupported restart mode %s" % runmode }

    def test(self, servername):
        try:
            res = self.status(servername)
        except:
            return return_dict( False, "test of pg_ctl on server %s failed" % servername)
        
        return returndict( True, "test of pg_ctl on server %s passed" % servername)

    def get_pg_ctl_cmd(self, servername, runmode):
        cmd = self.get_conf(self.servers, "restart_parameters", "pg_ctl_path")
        dbloc = self.servers[servername]["pgdata"]
        extra = self.get_conf(self.servers, "restart_parameters", "pg_ctl_flags")
        if cmd:
            return "%s -D %s %s %s" % (cmd, pgloc, extra, runmode,)
        else:
            return "pg_ctl -D %s %s %s" % (pgloc, extra, runmode,)

    def start(self, servername):
        startcmd = get_pg_ctl_cmd(servername, "start")
        runit = self.run_as_postgres(servername, [startcmd,])
        return runit

    def stop(self, servername):
        startcmd = get_pg_ctl_cmd(servername, "-m fast stop")
        runit = self.run_as_postgres(servername, [startcmd,])
        return runit

    def faststop(self, servername):
        startcmd = get_pg_ctl_cmd(servername, "-m immediate stop")
        runit = self.run_as_postgres(servername, [startcmd,])
        return runit

    def restart(self, servername):
        startcmd = get_pg_ctl_cmd(servername, "-m fast restart")
        runit = self.run_as_postgres(servername, [startcmd,])
        return runit
        
    def reloadpg(self, servername):
        startcmd = get_pg_ctl_cmd(servername, "reload")
        runit = self.run_as_postgres(servername, [startcmd,])
        return runit

    def status(self, servername):
        startcmd = get_pg_ctl_cmd(servername, "status")
        runit = self.run_as_postgres(servername, [startcmd,])
        return runit