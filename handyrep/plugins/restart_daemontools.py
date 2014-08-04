# plugin method for start/stop/restart/reload of a postgresql
# server using daemontools
# also works as a template plugin example

from plugins.handyrepplugin import HandyRepPlugin

class restart_daemontools(HandyRepPlugin):

    def run(self, servername, runmode):
        if runmode == "start":
            return self.start(servername)
        elif runmode == "stop":
            print "dt: stop"
            return self.stop(servername)
        elif runmode == "faststop":
            return self.faststop(servername)
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
            return self.rd( False, "test of daemontools service control on server %s failed" % servername)
        else:
            return self.rd( True, "test of daemontools service control on server %s passed" % servername)


    def get_service_cmd(self, servername, runmode):
        myconf = self.get_myconf()
        if myconf["service_name"]:
            return "svc %s /service/%s" % (runmode, myconf["service_name"], )
        else:
            return "svc %s /service/postgresql" % (runmode,)

    def get_status_cmd(self, servername):
        myconf = self.get_myconf()
        if myconf["service_name"]:
            return "svstat /service/%s" % (myconf["service_name"], )
        else:
            return "svstat /service/postgresql"

    def start(self, servername):
        startcmd = self.get_service_cmd(servername, "-u")
        runit = self.run_as_root(servername, [startcmd,])
        return runit

    def stop(self, servername):
        startcmd = self.get_service_cmd(servername, "-d")
        runit = self.run_as_root(servername, [startcmd,])
        return runit

    def faststop(self, servername):
        startcmd = self.get_service_cmd(servername, "-d -i")
        runit = self.run_as_root(servername, [startcmd,])
        return runit

    def restart(self, servername):
        startcmd = self.get_service_cmd(servername, "-t")
        runit = self.run_as_root(servername, [startcmd,])
        return runit
        
    def reloadpg(self, servername):
        startcmd = self.get_service_cmd(servername, "-h")
        runit = self.run_as_root(servername, [startcmd,])
        return runit

    def status(self, servername):
        startcmd = self.get_status_cmd(servername)
        runit = self.run_as_root(servername, [startcmd,])
        return runit
