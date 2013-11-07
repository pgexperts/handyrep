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
            return return_dict( False, "unsupported restart mode %s" % runmode )

    def test(self, servername):
        try:
            res = self.status(servername)
        except:
            return return_dict( False, "test of service control on server %s failed" % servername)

        return returndict( True, "test of service control on server %s passed" % servername)


    def get_service_cmd(servername, runmode):
        servicename = self.get_conf(self.servers, "restart_parameters", "service_name")
        if servicename:
            return "service %s %s" % (servicename, runmode,)
        else:
            return "service postgresql %s" % (extra, runmode,)

    def start(servername):
        startcmd = get_service_cmd(servername, "start")
        runit = self.run_as_root(servername, [startcmd,])
        return runit

    def stop(servername):
        startcmd = get_service_cmd(servername, "stop")
        runit = self.run_as_root(servername, [startcmd,])
        return runit

    def restart(servername):
        startcmd = get_service_cmd(servername, "restart")
        runit = self.run_as_root(servername, [startcmd,])
        return runit
        
    def reloadpg(servername):
        startcmd = get_service_cmd(servername, "reload")
        runit = self.run_as_root(servername, [startcmd,])
        return runit

    def status(servername):
        startcmd = get_service_cmd(servername, "status")
        runit = self.run_as_root(servername, [startcmd,])
        return runit