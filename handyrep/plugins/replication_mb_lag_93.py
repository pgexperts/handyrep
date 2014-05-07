# plugin which checks replication status
# and estimated MB of data lagged for each replica
# based on pg_stat_replication from PostgreSQL 9.3;
# may work with other versions, or not

# returns: success == ran successfully
# replication : am I replcating or not?
# lag : how much lag do I have?

from plugins.handyrepplugin import HandyRepPlugin

class replication_mb_lag_93(HandyRepPlugin):

    def run(self, replicaserver):
        master = self.get_master_name()
        if not master:
            return self.rd(False, "master not configured")
        else:
            try:
                mconn = self.connection(master)
            except:
                return self.rd(False, "could not connect to master")

        mcur = mconn.cursor()
        replag = self.get_one_val(mcur, """SELECT pg_xlog_location_diff(sent_location, replay_location)/(1024^2)
        FROM pg_stat_replication
        WHERE application_name = %s""", [replicaserver,])
        if replag is not None:
            self.servers[replicaserver]["lag"] = replag
            return self.rd(True, "server is replicatting", { "replicating" : True, "lag" : replag })
        else:
            return self.rd(True, "server %s is not currently in replication", { "replicating" : False, "lag" : 0 })

    def test(self, replicaserver):
        # test is the same as run
        return self.run(replicaserver)
