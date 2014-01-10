import daemon.daemonfunctions as hrdf

def failover_check(poll_cycle):
    if poll_cycle is None:
        pollno = 1
    else:
        pollno = poll_cycle

    print "poll num: %d" % pollno

    pollresult = hrdf.failover_check(pollno)

    print pollresult

    return pollresult

PERIODIC = {
    'failover_check': failover_check,
}
