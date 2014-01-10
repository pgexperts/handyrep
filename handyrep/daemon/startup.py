import daemon.daemonfunctions as hrdf

def startup():
    print "startup was run"
    hrdf.startup_hr()
    return True