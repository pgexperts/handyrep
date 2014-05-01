import daemon.daemonfunctions as hrdf

def failover_check(poll_cycle):
    if poll_cycle is None:
        pollno = 1
    else:
        pollno = poll_cycle

    #print "failover check no. %d" % pollno

    # need to wrap this in try fail so that the failover
    # check doesn't go away if we hit a python bug
    try:
        pollresult = hrdf.failover_check(pollno)
    except Exception as e:
        pollresult = { "result" : "FAIL",
            "details" : "Failover check encountered error: %s" % repr(e) }

    return pollresult

PERIODIC = {
    'failover_check': failover_check,
}
