# plugin to select a new replica based receive position
# for each replica, with a maximum threshold of replay
# lag.
# requires PostgreSQL 9.2 or later.

from plugins.handyrepplugin import HandyRepPlugin

class select_replica_furthest_ahead(HandyRepPlugin):

    def run(self):
        # assemble a list of servers, and get their
        # current position and lag information
        self.sortsrv = {}
        myconf = self.get_myconf()
        for serv, servdeets in self.servers.iteritems():
            if servdeets["enabled"] and servdeets["status_no"] in ( 1, 2 ) and servdeets["role"] == "replica":
                # get lag and receive position
                repconn = connection(serv)
                repcur = repconn.cursor()
                reppos = self.get_one_row(repcur, """SELECT pg_xlog_location_diff(
                        pg_current_xlog_location(), '0/0000000'),
                        pg_xlog_location_diff(
                        pg_last_xlog_receive_location(),
                        pg_last_xlog_replay_location()
                        )/1000000""")
                repconn.close()
                if reppos[1] <= float(myconf["max_replay_lag"]):
                    self.sortsrv[serv] = { "position" : reppos,
                        "lagged" : 0 }
                else:
                    self.sortsrv[serv] = { "position" : reppos,
                        "lagged" : 1 }
        sortedreps = sorted(self.sortsrv, key=self.servsort, reverse=True)
        return sortedreps

    def servsort(self, key):
        return self.sortsrv[key]["status_sort"], self.sortsrv[key]["priority"]

    def test(self):
        if self.failed(self.test_plugin_conf("select_replica_priority","max_replay_lag"):
            return self.rd( False, "select_replica_futhest_ahead is not configured correctly" )
        else:
            return self.rd( True, "select_replica_furthest_ahead passes" )
