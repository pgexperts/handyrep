# plugin method for polling servers for uptime
# using 9.3's pg_isready utility.  requires PostgreSQL 9.3
# to be installed on the Handyrep server

# does do repeated polling per fail_retries, since we need to do different
# kinds of polling in different plugins

from plugins.handyrepplugin import HandyRepPlugin

class poll_isready(HandyRepPlugin):

    def get_pollcmd(self, servername):
        cmd = self.pluginconf("isready_path")
        serv = self.servers[servername]
        if not cmd:
            cmd = "pg_isready"
        return '%s -h %s -p %s -q' % (cmd, serv["hostname"], serv["port"],)

    def run(self, servername):
        pollcmd = self.get_pollcmd(servername)
        runit = self.run_local([pollcmd,])
        print runit
        # did we have invalid parameters?
        if self.succeeded(runit):
            return self.rd(True, "poll succeeded", {"return_code" : runit["return_code"]})
        elif runit["return_code"] == 3 or runit["return_code"] is None:
            return self.rd(False, "invalid configuration for pg_isready", {"return_code" : runit["return_code"]})
        else:
            # got some other kind of failure, let's poll some more
            # we poll for fail_retries tries, with waits of fail_retry_interval
            retries = self.conf["failover"]["fail_retries"]
            for i in range(1,retries):
                self.failwait()
                runit = self.run_local(pollcmd)
                if self.succeeded(runit):
                    return self.rd(True, "poll self.succeeded", {"return_code" : runit["return_code"]})

            # if we've gotten here, then all polls have self.failed
            return self.rd(False, "polling self.failed after %d tries" % retries)
        
    def test(self):
        # just checks that we can run the poll command, not the result
        # find the master server, make sure we can poll it
        master = self.get_master_name()
        if not master:
            return self.rd(False, "master not configured, aborting")
        pollcmd = self.get_pollcmd(master)
        runit = self.run_local(pollcmd)
        if self.succeeded(runit) or runit["return_code"] in [0,1,2]:
            return self.rd(True, "polling works")
        else:
            return self.rd(False, "invalid configuration for pg_isready")