# plugin to select a new replica based on the "priority"
# assigned by users in the server definitions
# as with all replica selection, it returns a LIST
# of replicas
# sorts replicas first by status ( healthy then lagged)
# then sorts them by priority

from plugins.handyrepplugin import HandyRepPlugin

class select_replica_priority(HandyRepPlugin):

    def run(self):
        # assemble a list of servers, their status
        # numbers and priorities
        self.sortsrv = {}
        for serv, servdeets in self.servers.iteritems():
            if servdeets["enabled"] and servdeets["status_no"] in ( 1, 2 ) and servdeets["role"] == "replica":
                self.sortsrv[serv] = { "priority" : servdeets["failover_priority"],
                    "status_sort" : servdeets["status_no"] }

        sortedreps = sorted(self.sortsrv, key=self.servsort)
        return sortedreps

    def servsort(self, key):
        return self.sortsrv[key]["status_sort"], self.sortsrv[key]["priority"]

    def test(self):
        return self.rd( True, "sort by priority always succeeds" )
