__author__ = 'kaceymiriholston'

Categories = [
    {'Category': 'Information', 'description': 'For functions designed to provide the administrator or monitoring software '
                                               'with information about the status of various cluster resources.'},
    {'Category': 'Availability', 'description': 'For maintaining uptime of the cluster. They include functions for '
                                                'polling servers and for failover.'},
    {'Category': 'Action', 'description': 'For management of your handyrep cluster.'}]


Information = [
    {'function_name': 'get_status', 'description': 'Returns all status information for the cluster.', 'short_description': 'Cluster status information',
     'params': [{'param_name': 'check_type',
        'param_description': "allows you to specify that the server is to poll or fully verify all servers before "
                             "returning status information. Defaults to \"cached\".", 'param_type': 'choice', 'required': False,
        'param_options': [{ 'option_name': 'poll', 'description': 'Specify that the server is to poll all servers before returning status information.'},
         {'option_name': 'cached', 'description': "Just return information from HandyRep's last check."},
         {'option_name': 'verify', 'description': 'Specify that the server is to fully verify all servers before returning status information.'}]}],
     'result_format': ''},
    {'function_name': 'get_cluster_status', 'description': 'Returns the cluster status fields for the cluster.',
     'short_description': 'Cluster status fields', 'params': [{'param_name': 'verify',
        'param_description': "A true value will verify all cluster data, a false value will just return cached data.", 'param_type': 'bool',
        'required': False,'param_options': None}],
     'result_format': ''},
    {'function_name': 'get_master_name', 'description': 'Returns the name of the current master.',
     'short_description': 'Current master\'s name', 'params': None, 'result_format': ''},
    {'function_name': 'get_server_info', 'description': 'Returns server configuration and status details for the named server(s).',
     'short_description': 'Configuration & Status detail', 'params': [{'param_name': 'servername', 'param_description': 'The server whose data to return. If None, '
       'return a dictionary of all servers.', 'param_type': 'text', 'required': False, 'param_options': None},
                {'param_name': 'verify', 'param_description': 'A true value will verify all server data, a false value will just return cached data.',
                 'param_type': 'bool', 'required': False, 'param_options': None}],
     'result_format': ''},
    {'function_name': 'read_log', 'description': 'Retrieves the last N lines of the handyrep log and presents them as a list in reverse chonological order.',
     'short_description': 'handyrep log lines', 'params': [{'param_name': 'numlines', 'param_description': 'How many lines of the log to retrieve.', 'param_type':'text',
                'required': False, 'param_options': None}],
     'result_format': ''},
    {'function_name': 'get_setting', 'description': 'Retrieves a single configuration setting.', 'short_description': 'A configuration setting', 'params': [{'param_name': 'category',
                'param_description': 'Section of the config the setting is in.', 'param_type':'text', 'required': False,
                'param_options': None},{'param_name': 'setting', 'param_description': 'The individual setting name.', 'param_type': 'text',
                'required': True, 'param_options': None}],
     'result_format': ''},
    {'function_name': 'set_verbose', 'description': 'Toggles verbose logging.', 'short_description': 'Toggles verbose logging', 'params': [{'param_name': 'verbose',
        'param_description': 'True for verbose.', 'param_type': 'bool', 'required': False, 'param_options': None}],
     'result_format': ''}

]

Availability = [
    {'function_name': 'poll_master', 'description': 'Uses the configured polling method to check the master for availability. '
                    'Updates the status dictionary in the process. Can only determine up/down, and cannot determine if '
                    'the master has issues; as a result, will not change "warning" to "healthy". Also checks that the master '
                    'is actually a master and not a replica.', 'short_description': 'Check master availability', 'params': None,
     'result_format': ''},
    {'function_name': 'poll', 'description': 'Uses the configured polling method to check the designated server for '
                    'availability. Updates the status dictionary in the process. Can only determine up/down, and cannot '
                    'determine if the master has issues; as a result, will not change "warning" to "healthy".', 'short_description': 'Check server availability',
     'params': [{'param_name': 'servername', 'param_description': 'Server to poll.', 'param_type': 'text', 'required': False,
                 'param_options': None}], 'result_format': ''},
    {'function_name': 'poll_all', 'description': 'Polls all servers using the configured polling method. Also checks the '
                    'number of currently enabled and running masters and replicas. Intended to be part of availablity checks. '
                    'Updates the status dictionary.', 'short_description': 'Check all servers availability', 'params': None,
     'result_format': ''},
    {'function_name': 'verify_server', 'description': "Checks that the replica is running and is in replication, or "
                    "Checks the master server to make sure it's fully operating, including checking that we can connect, "
                    "we can write data, and that ssh and control commands are available. Updates the status dictionary."
                    "Dependant on which role of the server", 'short_description': 'Verify a server',
     'params': [{'param_name': 'server', 'param_description': 'Server name.', 'param_type': 'text', 'required': False,
                 'param_options': None}], 'result_format': ''},
    {'function_name': 'verify_all', 'description': 'Does complete check of all enabled servers in the server list. '
                    'Updates the status dictionary. Returns detailed check information about each server.',
     'short_description': 'Check all servers', 'params': None,
     'result_format': ''}
]

Action = [
    {'function_name': 'init_handyrep_db', 'description': 'Creates the initial handyrep schema and table.',
     'short_description': 'Create schema and table', 'params': None,
     'result_format': ''},
    {'function_name': 'reload_conf', 'description': 'Reload handyrep configuration from the handyrep.conf file. '
                'Allows changing of configuration files.', 'short_description': 'Reload configuration', 'params': [{'param_name': 'config_file', 'param_description':
        'File path location of the configuration file. Defaults to "handyrep.conf" in the working directory.', 'param_type': 'text',
        'required': False, 'param_options': None}],'result_format': ''},
    {'function_name': 'shutdown', 'description': 'Shut down the designated server. Checks to make sure that the server '
        'is actually down.', 'short_description': 'Shutdown server', 'params': [{'param_name': 'servername', 'param_description': 'The name of the server to shut down', 'param_type': 'text',
        'required': True, 'param_options': None}],
     'result_format': ''},
    {'function_name': 'startup', 'description': 'Starts the designated server. Checks to make sure that the server is actually up.',
     'short_description': 'Startup server', 'params': [{'param_name': 'servername', 'param_description': 'The name of the server to start.', 'param_type': 'text',
        'required': True, 'param_options': None}],
     'result_format': ''},
    {'function_name': 'restart', 'description': 'restarts the designated server. Checks to make sure that the server is actually up.',
     'short_description': 'Restart server', 'params': [{'param_name': 'servername', 'param_description': 'The name of the server to start.', 'param_type': 'text',
        'required': True, 'param_options': None}],
     'result_format': ''},
    {'function_name': 'promote', 'description': 'Promotes the designated replica to become a master or standalone. Does '
        'NOT do other failover procedures. Does not prevent creating two masters.', 'short_description': 'Promote replica', 'params': [{'param_name': 'severname',
        'param_description': 'The name of the server to start.', 'param_type': 'text','required': True, 'param_options': None}],
     'result_format': ''},
    {'function_name': 'manual_failover', 'description': 'Fail over to a new master, presumably for planned downtimes, '
        'maintenance, or server migrations.', 'short_description': 'Fail over to new master', 'params': [{'param_name': 'newmaster', 'param_description': 'Server to fail '
        'over to. If not supplied, use the same master selection process as auto-failover.', 'param_type': 'text',
        'param_options': None}, {'param_name': 'remaster', 'param_description': 'Whether or not to remaster '
        'all other servers to replicate from the new master. If not supplied, setting in handyrep.conf is used.', 'param_type': 'bool',
        'required': False, 'param_options': None}],
     'result_format': ''},
    {'function_name': 'clone', 'description': 'Create a clone from the master, and starts it up. Uses the configured '
        'cloning method and plugin.', 'short_description': 'Clone master and Start it', 'params': [{'param_name': 'replicaserver', 'param_description': 'The new replica '
        'to clone to.', 'param_type': 'text', 'required': False, 'param_options': None},
        {'param_name': 'reclone', 'param_description': 'Whether to clone over an existing replica, if any. '
                'If set to False (the default), clone will abort if this server has an operational PostgreSQL on it.', 'param_type': 'bool',
        'required': False, 'param_options': None},
        {'param_name': 'clonefrom', 'param_description': 'The server to clone from. Defaults to the current master.', 'param_type': 'text',
        'required': False, 'param_options': None}],
     'result_format': ''},
    {'function_name': 'enable', 'description': 'Enable a server definition already created. Also verifies the server defintion.',
     'short_description': 'Enable server definition', 'params': [{'param_name': 'servername', 'param_description': 'The server to enable.', 'param_type': 'text', 'required': False,
                 'param_options': None},], 'result_format': ''},
    {'function_name': 'disable', 'description': 'Mark an existing server disabled so that it is no longer checked. '
        'Also attempts to shut down the indicated server.', 'short_description': 'Disable server for checking', 'params': [{'param_name': 'servername',
        'param_description': 'The server to disable.', 'param_type': 'text', 'required': False, 'param_options': None}], 'result_format': ''},
    {'function_name': 'remove', 'description': 'Delete the definition of a disabled server.', 'short_description': 'Delete server definition', 'params':
        [{'param_name': 'servername', 'param_description': 'The server to disable.', 'param_type': 'text', 'required': False, 'param_options': None}],
     'result_format': ''},
    {'function_name': 'alter_server_def', 'description': 'Change details of a server after initialization. Required '
        'because the .conf file is not considered the canonical information about servers once servers.save has been created.',
     'short_description': 'Change server details', 'params': [{'param_name': 'servername', 'param_description': 'The existing server whose details are to be changed.',
        'param_type': 'text', 'required': False,  'param_options': None}, {'param_name': 'serverprops', 'param_description': 'a set of '
        'key-value pairs for settings to change. Settings may be "changed" to the existing value, so it is permissible '
        'to pass in an entire dictionary of the server config with one changed setting.', 'param_type': 'text',
        'required': False, 'param_options': None}], 'result_format': ''},
    {'function_name': 'add_server', 'description': 'Change details of a server after initialization. Required because '
        'the .conf file is not considered the canonical information about servers once servers.save has been created.',
        'short_description': 'Add a server', 'params': [{'param_name': 'servername', 'param_description': 'The existing server whose details are to be changed.',
        'param_type': 'text', 'required': False, 'param_options': None}, {'param_name': 'serverprops', 'param_description': 'a set of key-value '
        'pairs for settings to change. Settings may be "changed" to the existing value, so it is permissible to pass in '
        'an entire dictionary of the server config with one changed setting.', 'param_type': 'text', 'required': False, 'param_options': None}],
     'result_format': ''},
    {'function_name': 'cleanup_archive', 'description': 'Delete old WALs from a shared WAL archive, according to the '
        'expiration settings in handyrep.conf. Uses the configured archive deletion plugin.',
     'short_description': 'Delete old WALs', 'params': None,'result_format': ''},
    {'function_name': 'connection_proxy_init', 'description': 'Set up the connection proxy configuration according to the '
        'configured connection failover plugin. Not all connection proxy plugins support initialization.', 'short_description': 'Connection proxy config','params': None,
     'result_format': ''},
]
