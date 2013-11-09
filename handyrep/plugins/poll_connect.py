# plugin method for polling servers for uptime
# using a connection attempt to the database
# used for postgresql versions before 9.3.
# somewhat unreliable because we can't tell why
# we couldn't connect.
# for 9.3 and later use poll_isready instead

# does do repeated polling per fail_retries, since we need to do different
# kinds of polling in different plugins

from plugins.handyrepplugin import HandyRepPlugin

class poll_connect(HandyRepPlugin):

    def run(self, servername):
        retries = self.conf["failover"]["fail_retries"] + 1
        for i in range(1, retries):
            try:
                conn = self.connection(servername)
            except:
                pass
            else:
                conn.close()
                return(True, "poll succeeded")

        return(False, "could not connect to server in %d tries" % retries)
        
    def test(self):
        # checks that we can connect to the master
        # will fail if we can't, so this isn't a terribly good test
        # since it might just be that the master is down
        master = self.get_master_name()
        if not master:
            return self.rd(False, "master not configured, aborting")
        try:
            conn = self.connection(servername)
        except:
            return(False, "unable to connect to master for polling")
        else:
            conn.close()
            return(True, "poll succeeded")