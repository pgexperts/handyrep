# plugin method for polling servers for uptime
# using 9.3's pg_isready utility.  requires PostgreSQL 9.3
# to be installed on the Handyrep server

# does do repeated polling per fail_retries, since we need to do different
# kinds of polling in different plugins

from plugins.handyrepplugin import HandyRepPlugin

class poll_isready(HandyRepPlugin):

    def get_pollcmd(self, servername):
        cmd = pluginconf("isready_path")
        serv = self.servers[servername]
        if not cmd:
            cmd = "pg_isready"
        return '%s -h %s -p %s -U %s -d %s -q' % (cmd, serv["hostname"], serv["port"], serv["postgres_superuser"], self.conf["handyrep"]["handrey_db"],)

    def run(self, servername):
        pollcmd = self.get_pollcmd(servername)
        runit = self.run_local(pollcmd)
        # did we have invalid parameters?
        if succeeded(runint):
            return self.rd(True, "poll succeeded")
        elif runit["return_code"] == 3 or runit["return_code"] is None:
            return self.rd(False, "invalid configuration for pg_isready")
        else:
            # got some other kind of failure, let's poll some more
            # we poll for fail_retries tries, with waits of fail_retry_interval
            retries = self.conf["failover"]["fail_retries"]
            for i in range(1,retries):
                self.failwait()
                runit = self.run_local(pollcmd)
                if succeeded(runit):
                    return self.rd(True, "poll succeeded")

            # if we've gotten here, then all polls have failed
            return self.rd(False, "polling failed after %d tries" % retries)
        
    def test(self):
        # just checks that we can run the poll command, not the result
        # find the master server, make sure we can poll it
        master = self.get_master_name()
        if not master:
            return self.rd(False, "master not configured, aborting")
        pollcmd = self.get_pollcmd(master)
        runit = self.run_local(pollcmd)
        if succeeded(runit) or if runit["return_code"] in [0,1,2]:
            return self.rd(True, "polling works")
        else:
            return self.rd(False, "invalid configuration for pg_isready")