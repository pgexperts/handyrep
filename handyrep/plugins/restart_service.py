# plugin method for start/stop/restart/reload of a postgresql
# server using service and the data directory
# also works as a template plugin example

from plugins.handyrepplugin import HandyRepPlugin

class restart_service(HandyRepPlugin):

    def run(self, servername, runmode):
        if runmode == "start":
            return self.start(servername)
        elif runmode == "stop":
            return self.stop(servername)
        # there's no real faststop method with services
        elif runmode == "faststop":
            return self.stop(servername)
        elif runmode == "restart":
            return self.restart(servername)
        elif runmode == "reload":
            return self.reloadpg(servername)
        elif runmode == "status":
            return self.status(servername)
        else:
            return self.rd( False, "unsupported restart mode %s" % runmode )

    def test(self, servername):
        try:
            res = self.status(servername)
        except:
            return self.rd( False, "test of service control on server %s failed" % servername)
        else:
            return self.rd( True, "test of service control on server %s passed" % servername)


    def get_service_cmd(self, servername, runmode):
        myconf = self.get_myconf()
        if myconf["service_name"]:
            return "service %s %s" % (servicename, runmode,)
        else:
            return "service postgresql %s" % (runmode,)

    def start(self, servername):
        startcmd = self.get_service_cmd(servername, "start")
        runit = self.run_as_root(servername, [startcmd,])
        return runit

    def stop(self, servername):
        startcmd = self.get_service_cmd(servername, "stop")
        runit = self.run_as_root(servername, [startcmd,])
        return runit

    def restart(self, servername):
        startcmd = self.get_service_cmd(servername, "restart")
        runit = self.run_as_root(servername, [startcmd,])
        return runit
        
    def reloadpg(self, servername):
        startcmd = self.get_service_cmd(servername, "reload")
        runit = self.run_as_root(servername, [startcmd,])
        return runit

    def status(self, servername):
        startcmd = self.get_service_cmd(servername, "status")
        runit = self.run_as_root(servername, [startcmd,])
        return runit