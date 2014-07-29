from handyrep import HandyRep
import os
import sys
import json
import re

# startup function

def startup_hr():
    # get handyrep config location.  if not set,
    # default is in the local directory, which is almost never right
    # try argv
    global hr
    if len(sys.argv) > 1:
        hrloc = sys.argv[1]
    else:
        # try environment variable next
        hrloc = os.getenv("HANDYREP_CONFIG")

    if not hrloc:
        # need to go to handyrep base directory without relying on CWD
        # since CWD doesn't exist in webserver context
        hrloc = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))),"handyrep.conf")
    hr = HandyRep(hrloc)
    return True

# invokable functions

# helper function to interpret string True values
def is_true(bolval):
    if type(bolval) is bool:
        return bolval
    else:
        if bolval.lower() in ["true", "t", "on", "1", "yes"]:
            return True
        else:
            return False

def is_false(bolval):
    if type(bolval) is bool:
        return bolval == False
    else:
        if bolval.lower() in ["false", "f", "off", "0", "no"]:
            return True
        else:
            return False

def read_log(numlines=20):
    nlines = int(numlines)
    return hr.read_log(nlines)

def set_verbose(verbose="True"):
    vbs = is_true(verbose)
    return hr.set_verbose(vbs)

def get_setting(category="handyrep", setting=None):
    if not setting:
        return { "result" : "FAIL",
            "details" : "setting name is required" }
    else:
        return json.dumps(hr.get_setting([category, setting,]))

def verify_all():
    return hr.verify_all()

def verify_server(servername):
    return hr.verify_server(servername)

def reload_conf(config_file=None):
    return hr.reload_conf(config_file)

def get_master_name():
    return json.dumps(hr.get_master_name())

def poll(servername=None):
    if not servername:
        return { "result" : "FAIL",
            "details" : "server name required" }
    else:
        return hr.poll(servername)

def poll_all():
    return hr.poll_all()

def poll_master():
    return hr.poll_master()

def get_status(check_type="cached"):
    return hr.get_status(check_type)

def get_server_info(servername=None, verify="False"):
    vfy = is_true(verify)
    return hr.get_server_info(servername, vfy)

def get_servers_by_role(serverrole="replica",verify="False"):
    vfy = is_true(verify)
    return hr.get_servers_by_role(serverrole, vfy)

def get_cluster_status(verify="False"):
    vfy = is_true(verify)
    return hr.get_cluster_status(vfy)

def restart_master(whichmaster=None):
    return hr.restart_master(whichmaster)

def manual_failover(newmaster=None, remaster=None):
    return hr.manual_failover(newmaster, remaster)

def shutdown(servername=None):
    if not servername:
        return { "result" : "ERROR",
            "details" : "server name is required" }
    else:
        return hr.shutdown(servername)

def startup(servername=None):
    if not servername:
        return { "result" : "FAIL",
            "details" : "server name is required" }
    else:
        return hr.startup(servername)

def restart(servername=None):
    if not servername:
        return { "result" : "FAIL",
            "details" : "server name is required" }
    else:
        return hr.restart(servername)

def promote(newmaster):
    if not newmaster:
        return { "result" : "FAIL",
            "details" : "new master name is required" }
    else:
        return hr.promote(newmaster)

def remaster(replicaserver=None, newmaster=None):
    if not replicaserver:
        return { "result" : "FAIL",
            "details" : "replica name is required" }
    else:
        return hr.remaster(replicaserver, newmaster)

# dumb simple string-to-type kwargs converter for add_server and alter_server_def
# only supports strings, integers and booleans.
def map_server_args(sargs):
    nargs = {}
    for arg, val in sargs.iteritems():
        if arg in [ "port", "lag_limit", "failover_priority" ]:
            nargs[arg] = int(val)
        elif re.match(r'\d+$',val):
            nargs[arg] = int(val)
        elif val in ["true","True"]:
            nargs[arg] = True
        elif val in ["False","false"]:
            nargs[arg] = False
        else:
            nargs[arg] = val

    return nargs

def add_server(servername=None, **kwargs):
    if not servername:
        return { "result" : "FAIL",
            "details" : "server name is required" }
    else:
        margs = map_server_args(kwargs)
        return hr.add_server(servername, **margs)

def clone(replicaserver=None,reclone="False",clonefrom=None):
    recl = is_true(reclone)
    if not replicaserver:
        return { "result" : "FAIL",
            "details" : "replica name is required" }
    else:
        return hr.clone(replicaserver, recl, clonefrom)

def disable(servername):
    if not servername:
        return { "result" : "FAIL",
            "details" : "server name is required" }
    else:
        return hr.disable(servername)

def enable(servername):
    if not servername:
        return { "result" : "FAIL",
            "details" : "server name is required" }
    else:
        return hr.enable(servername)

def remove(servername):
    if not servername:
        return { "result" : "FAIL",
            "details" : "server name is required" }
    else:
        return hr.remove(servername)

def add_server(servername, **serverprops):
    if not servername:
        return { "result" : "FAIL",
            "details" : "server name is required" }
    else:
        margs = map_server_args(serverprops)
        return hr.add_server(servername, **margs)

def alter_server_def(servername, **serverprops):
    if not servername:
        return { "result" : "FAIL",
            "details" : "server name is required" }
    else:
        margs = map_server_args(serverprops)
        return hr.alter_server_def(servername, **margs)

def connection_failover(newmaster=None):
    if not newmaster:
        return { "result" : "FAIL",
            "details" : "new master name required" }
    else:
        return hr.connection_failover(newmaster)

def connection_proxy_init():
    return hr.connection_proxy_init()

def start_archiving():
    return hr.start_archiving()

def stop_archiving():
    return hr.stop_archiving()

def cleanup_archive():
    return hr.cleanup_archive()

# periodic

def failover_check(pollno=None):
    return hr.failover_check_cycle(pollno)


# authentication

def authenticate(username, userpass, funcname):
    return hr.authenticate_bool(username, userpass, funcname)
