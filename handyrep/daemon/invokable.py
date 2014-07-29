import daemon.daemonfunctions as hrdf

def read_log(numlines=20):
    return hrdf.read_log(numlines)

def set_verbose(verbose="True"):
    return hrdf.set_verbose(verbose)

def get_setting(category="handyrep", setting=None):
    return hrdf.get_setting(category, setting)

def verify_all():
    return hrdf.verify_all()

def verify_server(servername):
    return hrdf.verify_server(servername)

def reload_conf(config_file=None):
    return hrdf.reload_conf(config_file)

def get_master_name():
    return hrdf.get_master_name()

def poll(servername=None):
    return hrdf.poll(servername)

def poll_all():
    return hrdf.poll_all()

def poll_master():
    return hrdf.poll_master()

def get_status(check_type="cached"):
    return hrdf.get_status(check_type)

def get_server_info(servername=None, verify="False"):
    return hrdf.get_server_info(servername, verify)

def get_servers_by_role(serverrole="replica",verify="False"):
    return hrdf.get_servers_by_role(serverrole, verify)

def get_cluster_status(verify="False"):
    return hrdf.get_cluster_status(verify)

def restart_master(whichmaster=None):
    return hrdf.restart_master(whichmaster)

def manual_failover(newmaster=None, remaster=None):
    return hrdf.manual_failover(newmaster, remaster)

def shutdown(servername=None):
    return hrdf.shutdown(servername)

def startup(servername=None):
    return hrdf.startup(servername)

def restart(servername=None):
    return hrdf.restart(servername)

def promote(newmaster=None):
    return hrdf.promote(newmaster)

def remaster(replicaserver=None, newmaster=None):
    return hrdf.remaster(replicaserver, newmaster)

def clone(replicaserver=None,reclone="False",clonefrom=None):
    return hrdf.clone(replicaserver, reclone, clonefrom)

def disable(servername):
    return hrdf.disable(servername)

def enable(servername):
    return hrdf.enable(servername)

def remove(servername):
    return hrdf.remove(servername)

def alter_server_def(servername, **kwargs):
    return hrdf.alter_server_def(servername, **kwargs)

def add_server(servername, **kwargs):
    return hrdf.add_server(servername, **kwargs)

def connection_failover(newmaster=None):
    return hrdf.connection_failover(newmaster)

def connection_proxy_init():
    return hrdf.connection_proxy_init()

def start_archiving():
    return hrdf.start_archving()

def stop_archiving():
    return hrdf.stop_archiving()

def cleanup_archive():
    return hrdf.cleanup_archive()

INVOKABLE = {
    "read_log" : read_log,
    "get_setting" : get_setting,
    "set_verbose" : set_verbose,
    "verify_all" : verify_all,
    "verify_server" : verify_server,
    "reload_conf" : reload_conf,
    "get_master_name" : get_master_name,
    "poll" : poll,
    "poll_all" : poll_all,
    "poll_master" : poll_master,
    "get_status" : get_status,
    "get_server_info" : get_server_info,
    "get_servers_by_role" : get_servers_by_role,
    "get_cluster_status" : get_cluster_status,
    "restart_master" : restart_master,
    "manual_failover" : manual_failover,
    "shutdown" : shutdown,
    "startup" : startup,
    "restart" : restart,
    "promote" : promote,
    "remaster" : remaster,
    "add_server" : add_server,
    "clone" : clone,
    "disable" : disable,
    "enable" : enable,
    "remove" : remove,
    "alter_server_def" : alter_server_def,
    "add_server" : add_server,
    "connection_failover" : connection_failover,
    "connection_proxy_init" : connection_proxy_init,
    "start_archiving" : start_archiving,
    "stop_archiving" : stop_archiving,
    "cleanup_archive" : cleanup_archive
}

