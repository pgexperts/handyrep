import daemon.daemonfunctions as hrdf

def failover_check(poll_cycle):
    if poll_cycle is None:
        pollno = 1
    else:
        pollno = poll_cycle

    print "failover check no. %d" % pollno

    pollresult = hrdf.failover_check(pollno)

    return pollresult

PERIODIC = {
    'failover_check': failover_check,
}
