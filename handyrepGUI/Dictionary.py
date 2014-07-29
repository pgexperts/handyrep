__author__ = 'kaceymiriholston'

Functions = {
    'get_status': {'function_name': 'get_status','description': 'Returns all status information for the cluster.', 'short_description': 'Cluster status information',
        'params': [{'param_name': 'check_type', 'param_default': 'cached',
        'param_description': "allows you to specify that the server is to poll or fully verify all servers before "
                             "returning status information.", 'param_type': 'choice', 'required': False,
        'param_options': [{ 'option_name': 'poll', 'description': 'Specify that the server is to poll all servers before returning status information.'},
         {'option_name': 'cached', 'description': "Just return information from HandyRep's last check."},
         {'option_name': 'verify', 'description': 'Specify that the server is to fully verify all servers before returning status information.'}]}],
        'result_information': '<p>This function returns status at two levels: for the cluster as a whole, and for each individual '
                           'server. In both cases, status information consists of four fields:</p><h4>status</h4>'
                           '<p style="padding-left:2em">one of "unknown","healthy","lagged","warning","unavailable", or "down". see below '
                           'for explanation of these statuses.</p><h4>status_no</h4><p style="padding-left:2em">status number corresponding to above, '
                           'for creating alert thresholds.</p><h4>status_ts</h4><p style="padding-left:2em">the last timestamp when status '
                           'was checked, in unix standard format</p><h4>status_message</h4><p style="padding-left:2em">a message about the '
                           'last issue found which causes a change in status. May not be complete or representative.</p>'
                           '<h4>The individual servers also contain their name(hostname), their role(role) and if they are enabled'
                           '(enabled).</h4><h3>Status meaning</h3><h3 style="padding-left:1em">Cluster Status Data</h3>'
                           '<h4 style="padding-left:1.3em">0: "unknown"</h4><p style="padding-left:2em">status checks have not been run. This status '
                           'should only exist for a very short time.</p><h4 style="padding-left:1.3em">1 : "healthy"</h4><p style="padding-left:2em">cluster has a viable master, and all replicas are "healthy" or "lagged" '
                           '</p><h4 style="padding-left:1.3em">3 : "warning"</h4><p style="padding-left:2em">cluster has a viable master, but has one or more issues, including connnection problems, failure to fail over, or downed replicas.'
                           '</p><h4 style="padding-left:1.3em">5 : "down"</h4><p style="padding-left:2em">cluster has no working master, or is in an indeterminate state and requires administrator intervention'
                           '</p><h3 style="padding-left:1em">Individual Servers Status Data</h3>'
                           '<h4 style="padding-left:1.3em">0: "unknown"</h4><p style="padding-left:2em">server has not been checked yet.'
                           '</p><h4 style="padding-left:1.3em">1 : "healthy"</h4><p style="padding-left:2em">server is operating normally'
                           '</p><h4 style="padding-left:1.3em">2 : "lagged"</h4><p style="padding-left:2em">for replicas, indicates that the replica is running but has exceeded the configured lag threshold.'
                           '</p><h4 style="padding-left:1.3em">3 : "warning"</h4><p style="padding-left:2em">server is operating, but has one or more issues, such as inability to ssh, or out-of-connections.'
                           '</p><h4 style="padding-left:1.3em">4 : "unavailable"</h4><p style="padding-left:2em">cannot determine status of server because we cannot connect to it.'
                           '</p><h4 style="padding-left:1.3em">5 : "down"</h4><p style="padding-left:2em">.server is verified down'
                           '</p>'},

    'get_cluster_status':{ 'function_name': 'get_cluster_status','description': 'Returns the cluster status fields for the cluster. ',
        'short_description': 'Cluster status fields', 'params': [{'param_name': 'verify', 'param_default': False,
        'param_description': "A true value will verify all cluster data, a false value will just return cached data.", 'param_type': 'bool',
        'required': False,'param_options': None}],
        'result_information': '<p>This function returns status for the cluster as a whole. Status information consists of four fields:</p><h4>status</h4>'
                           '<p style="padding-left:2em">one of "unknown","healthy","lagged","warning","unavailable", or "down". see below '
                           'for explanation of these statuses.</p><h4>status_no</h4><p style="padding-left:2em">status number corresponding to above, '
                           'for creating alert thresholds.</p><h4>status_ts</h4><p style="padding-left:2em">the last timestamp when status '
                           'was checked, in unix standard format</p><h4>status_message</h4><p style="padding-left:2em">a message about the '
                           'last issue found which causes a change in status. May not be complete or representative.</p>'
                           '<h4>The individual servers also contain their name(hostname), their role(role) and if they are enabled'
                           '(enabled).</h4><h3>Status meaning</h3><h3 style="padding-left:1em">Cluster Status Data</h3>'
                           '<h4 style="padding-left:1.3em">0: "unknown"</h4><p style="padding-left:2em">status checks have not been run. This status '
                           'should only exist for a very short time.</p><h4 style="padding-left:1.3em">1 : "healthy"</h4><p style="padding-left:2em">cluster has a viable master, and all replicas are "healthy" or "lagged" '
                           '</p><h4 style="padding-left:1.3em">3 : "warning"</h4><p style="padding-left:2em">cluster has a viable master, but has one or more issues, including connnection problems, failure to fail over, or downed replicas.'
                           '</p><h4 style="padding-left:1.3em">5 : "down"</h4><p style="padding-left:2em">cluster has no working master, or is in an indeterminate state and requires administrator intervention'
                           '</p>'},

    'get_master_name': {'function_name': 'get_master_name','description': 'Returns the name of the current master.',
        'short_description': 'Current master\'s name', 'params': None, 'result_information': 'This function returns the name of the '
                    'current master. If there is no configured master, or the master has been disabled, it will return "None".'},

    'get_server_info':{'function_name': 'get_server_info', 'description': 'Returns server configuration and status details for the named server(s).',
        'short_description': 'Configuration & Status detail', 'params': [{'param_name': 'servername', 'param_default': 'None','param_description': 'The server whose data to return. If None, '
       'or blank, return all servers.', 'param_type': 'text', 'required': False, 'param_options': None},
                {'param_name': 'verify', 'param_default': False, 'param_description': 'A true value will verify all server data, a false value will just return cached data.',
                 'param_type': 'bool', 'required': False, 'param_options': None}], 'result_information': 'This function returns server configuration and status details for this server.'},

    'read_log': {'function_name': 'read_log','description': 'Retrieves the last N lines of the handyrep log and presents them as a list in reverse chonological order.',
        'short_description': 'handyrep log lines', 'params': [{'param_name': 'numlines', 'param_default': None, 'param_description': 'How many lines of the log to retrieve.', 'param_type':'text',
                'required': False, 'param_options': None}], 'result_information': "This function retrieves the last N lines of the handyrep log and presents them as a list in reverse chonological order." },

    'get_setting' :{'function_name': 'get_setting','description': 'Retrieves a single configuration setting. Can not retrieve nested settings.', 'short_description': 'A configuration setting', 'params': [{'param_name': 'category',
                'param_default': None, 'param_description': 'Section of the config the setting is in.', 'param_type':'text', 'required': False,
                'param_options': None},{'param_name': 'setting', 'param_default': None, 'param_description': 'The individual setting name.', 'param_type': 'text',
                'required': True, 'param_options': None}], 'result_information': "This function retrieves a single configuration setting."},

    'set_verbose':{ 'function_name': 'set_verbose','description': 'Toggles verbose logging.', 'short_description': 'Toggles verbose logging', 'params': [{'param_name': 'verbose',
        'param_default': True ,'param_description': 'True for verbose.', 'param_type': 'bool', 'required': False, 'param_options': None}],
                    'result_information': 'This function returns whether the toggle was successful.'},

    'poll_master':{ 'function_name': 'poll_master','description': 'Uses the configured polling method to check the master for availability. '
                    'Updates the status dictionary in the process. Can only determine up/down, and cannot determine if '
                    'the master has issues; as a result, will not change "warning" to "healthy". Also checks that the master '
                    'is actually a master and not a replica.', 'short_description': 'Check master availability', 'params': None,
            'result_information': '<p>This function returns a result, a human readable details line and a return_code linked to the sucess or failure of the function</p>'
                           '<h3>result</h3><h4 style="padding-left:1em">SUCCESS</h4><p style="padding-left:2em">The '
                           'current master is responding to polling.</p><h4 style="padding-left:1em">FAIL</h4><p style="padding-left:2em">The '
                           'current master is not responding to polling, or the handyrep or polling method configuration is wrong.</p>'},

    'poll':{'function_name': 'poll', 'description': 'Uses the configured polling method to check the designated server for '
                    'availability. Updates the status dictionary in the process. Can only determine up/down, and cannot '
                    'determine if the master has issues; as a result, will not change "warning" to "healthy".', 'short_description': 'Check server availability',
            'params': [{'param_name': 'servername', 'param_default': None, 'param_description': 'Server to poll.', 'param_type': 'text', 'required': False,
                 'param_options': None}], 'result_information': '<p>This function returns a result, a human readable details line and a return_code linked to the sucess or failure of the function</p>'
                           '<h3>result</h3><h4 style="padding-left:1em">SUCCESS</h4><p style="padding-left:2em">The '
                           'current master is responding to polling.</p><h4 style="padding-left:1em">FAIL</h4><p style="padding-left:2em">The '
                           'current master is not responding to polling, or the handyrep or polling method configuration is wrong.</p>'},

    'poll_all':{'function_name': 'poll_all', 'description': 'Polls all servers using the configured polling method. Also checks the '
                    'number of currently enabled and running masters and replicas. Updates the status dictionary.',
        'short_description': 'Check all servers availability', 'params': None,
        'result_information': '<p>This function returns information on the cluster and the servers. This information includes the'
                           'failover status, the results in human readable and boolean format and a details, human readable message.</p>'
                           '<h3>result</h3><h4 style="padding-left:1em">SUCCESS</h4><p style="padding-left:2em">The master is running.</p>'
                            '<h4 style="padding-left:1em">FAIL</h4><p style="padding-left:2em">The master is down, or no master is configured, or multiple masters are configured.</p>'
                            '<h4>failover_ok</h4><p style="padding-left:1em">Boolean field indicating whether it is OK to fail over. Basically a check that there is one master and at least one working replica.</p>'},

    'verify_server':{'function_name': 'verify_server', 'description': "Checks that the replica is running and is in replication, or "
                    "Checks the master server to make sure it's fully operating, including checking that we can connect, "
                    "we can write data, and that ssh and control commands are available. Updates the status dictionary.",
            'short_description': 'Verify a server',
            'params': [{'param_name': 'servername', 'param_default': None, 'param_description': 'Server name.', 'param_type': 'text', 'required': False,
                 'param_options': None}], 'result_information': '<p>This function results depends on if you are verifying a master or replica</p>'
                    '<h3>result</h3><h4 style="padding-left:1em">SUCCESS (master)</h4><p style="padding-left:2em">'
                    'The master is verified to be running, although it may have known non-fatal issues.</p>'
                    '<h4 style="padding-left:1em">SUCCESS (replica)</h4><p style="padding-left:2em">'
                    'The replica is verified to be running, although it may have known non-fatal issues.</p>'
                    '<h4 style="padding-left:1em">FAIL (master)</h4><p style="padding-left:2em">'
                    'The master is verified to be not running, unresponsive, or may be blocking data writes.</p>'
                    '<h4 style="padding-left:1em">FAIL (replica)</h4><p style="padding-left:2em">'
                    'The replica is verified to be not running, unresponsive, or may be running but not in replication.</p>'
                    '<h3>ssh (for both)</h3><p style="padding-left:1em">Text field, which, if it exists, shows an error '
                    'message from attempts to connect to the master via ssh.</p><h3>psql (for both)</h3><p style="padding-left:1em">'
                    'Text field which, if it exists, shows an error message from attempts to make a psql connection to the master.</p>'
                    '<h3>details</h3><p style="padding-left:1em"> Human readable message.</p>'},


    'verify_all':{'function_name': 'verify_all', 'description': 'Does complete check of all enabled servers in the server list. '
                    'Updates the status dictionary. Returns detailed check information about each server.',
            'short_description': 'Check all servers', 'params': None,
            'result_information': '<p>This function returns information about the cluster and each server.</p><h3>Cluster Information</h3>'
                           '<h4 style="padding-left:1em">failover_ok</h4><p style="padding-left:2em">'
                    'True means at least one replica is healthy and available for failover.</p>'
                    '<h4 style="padding-left:1em">result</h4><p style="padding-left:2em">'
                    'SUCCESS = the master is up and running. FAIL = the master is not running, or master configuration '
                    'is messed up (no masters, two masters, etc.)</p> <h4 style="padding-left:1em">details</h4><p style="padding-left:2em">'
                    'Human readable statement of what is going on.<h3>Server Information</h3>'
                           '<h4 style="padding-left:1em">psql</h4><p style="padding-left:2em">'
                    'Text field which, if it exists, shows an error message from attempts to make a psql connection to the master</p>'
                    '<h4 style="padding-left:1em">result</h4><p style="padding-left:2em">'
                    'SUCCESS = the master is up and running. FAIL = the master is not running, or master configuration '
                    'is messed up (no masters, two masters, etc.)</p> <h4 style="padding-left:1em">details</h4><p style="padding-left:2em">'
                    'Human readable statement of what is going on.'},

    'init_handyrep_db':{'function_name': 'init_handyrep_db', 'description': 'Creates the initial handyrep schema and table.',
                        'short_description':'Creates schema and table', 'params': None, 'result_information': 'This function returns'
                        'data related to the success of the creation of the schema and table.'
                        '<p>It fails if it cannot connect to the master, or does not have permissions to create schemas and tables, or if the cited database does not exist.</p>'},

    'reload_conf':{'function_name': 'reload_conf', 'description': 'Reload handyrep configuration from the handyrep.conf file. '
                'Allows changing of configuration files.', 'short_description': 'Reload configuration', 'params': [{'param_name': 'config_file', 'param_default': None, 'param_description':
        'File path location of the configuration file. Defaults to current config location.', 'param_type': 'text',
        'required': False, 'param_options': None}], 'result_information': 'This function returns'
                        'data related to the success of the creation of the schema and table.'},

    'shutdown':{'function_name': 'shutdown', 'description': 'Shut down the designated server. Checks to make sure that the server '
        'is actually down.', 'short_description': 'Shutdown server', 'params': [{'param_name': 'servername', 'param_default': None,'param_description': 'The name of the server to shut down', 'param_type': 'text',
        'required': True, 'param_options': None}], 'result_information': 'This function returns data related to the success '
        'of the shutdown of the server.<h3>result</h3><h4 style="padding-left:1em">SUCCESS</h4><p style="padding-left:2em">The server is shut down.</p><h4 style="padding-left:1em">FAIL</h4><p style="padding-left:2em">The server will not shut down. check details.</p>'},

     'startup':{'function_name': 'startup', 'description': 'Starts the designated server. Checks to make sure that the server is actually up.',
        'short_description': 'Startup server', 'params': [{'param_name': 'servername', 'param_default': None,'param_description': 'The name of the server to start.', 'param_type': 'text',
        'required': True, 'param_options': None}], 'result_information': 'This function returns data related to the success '
        'of the startup of the server.<h3>result</h3><h4 style="padding-left:1em">SUCCESS</h4><p style="padding-left:2em">The server is running.</p><h4 style="padding-left:1em">FAIL</h4><p style="padding-left:2em">The server will not start, check details.</p>'},

    'restart':{'function_name': 'restart', 'description': 'restarts the designated server. Checks to make sure that the server is actually up.',
     'short_description': 'Restart server', 'params': [{'param_name': 'servername', 'param_default': None,'param_description': 'The name of the server to start.', 'param_type': 'text',
        'required': True, 'param_options': None}], 'result_information': 'This function returns data related to the success '
        'of the restart of the server.<h3>result</h3><h4 style="padding-left:1em">SUCCESS</h4><p style="padding-left:2em">The server is running.</p><h4 style="padding-left:1em">FAIL</h4><p style="padding-left:2em">The server will not restart, check details.</p>'},


    'promote':{'function_name': 'promote', 'description': 'Promotes the designated replica to become a master or standalone. Does '
        'NOT do other failover procedures. Does not prevent creating two masters.', 'short_description': 'Promote replica', 'params': [{'param_name': 'newmaster',
        'param_default': None, 'param_description': 'The name of the server to start.', 'param_type': 'text','required': True, 'param_options': None}],
               'result_information': 'This function returns data related to the success '
        'of the promotion of the server.<h3>result</h3><h4 style="padding-left:1em">SUCCESS</h4><p style="padding-left:2em">The server has been promoted.</p><h4 style="padding-left:1em">FAIL</h4><p style="padding-left:2em">The server could not be promoted, check details.</p>'},

    'manual_failover':{'function_name': 'manual_failover', 'description': 'Fail over to a new master, presumably for planned downtimes, '
        'maintenance, or server migrations.', 'short_description': 'Fail over to new master', 'params': [{'param_name': 'newmaster', 'param_default': None, 'param_description': 'Server to fail '
        'over to. If not supplied, use the same master selection process as auto-failover.', 'param_type': 'text', 'required': False,
        'param_options': None}, {'param_name': 'remaster', 'param_default': None,'param_description': 'Whether or not to remaster '
        'all other servers to replicate from the new master. If not supplied, setting in handyrep.conf is used.', 'param_type': 'bool',
        'required': False, 'param_options': None}], 'result_information': 'This function returns data related to the success '
        'of the failover of the server.<h3>result</h3><h4 style="padding-left:1em">SUCCESS</h4><p style="padding-left:2em">'
        'The server failed over to the new master successfully. Check details in case postfailover commands failed.</p>'
        '<h4 style="padding-left:1em">FAIL</h4><p style="padding-left:2em">The server is unable to fail over to the new '
        'master. Cluster may have been left in an indeterminate state, check details.</p>'},

     'clone':{'function_name': 'clone', 'description': 'Create a clone from the master, and starts it up. Uses the configured '
        'cloning method and plugin.', 'short_description': 'Clone master and Start it', 'params': [{'param_name': 'replicaserver', 'param_default': None,
        'param_description': 'The new replica to clone to.', 'param_type': 'text', 'required': False, 'param_options': None},
        {'param_name': 'reclone', 'param_default': False, 'param_description': 'Whether to clone over an existing replica, if any. '
                'If set to False (the default), clone will abort if this server has an operational PostgreSQL on it.', 'param_type': 'bool',
        'required': False, 'param_options': None},
        {'param_name': 'clonefrom','param_default': 'current master', 'param_description': 'The server to clone from. Defaults to the current master.', 'param_type': 'text',
        'required': False, 'param_options': None}], 'result_information': 'This function returns data related to the success '
        'of the clone of the master.<h3>result</h3><h4 style="padding-left:1em">SUCCESS</h4><p style="padding-left:2em">'
        'The replica was cloned and is running.</p>'
        '<h4 style="padding-left:1em">FAIL</h4><p style="padding-left:2em">Either cloning or starting up the new replica '
        'failed, or you attempted to clone over an existing running server.</p>'},

    'enable':{'function_name': 'enable', 'description': 'Enable a server definition already created. Also verifies the server defintion.',
            'short_description': 'Enable server definition', 'params': [{'param_name': 'servername', 'param_default': None,
            'param_description': 'The server to enable.', 'param_type': 'text', 'required': False,'param_options': None}],
        'result_information': 'This function returns data related to the success of whether the server defination is enabled.'
        '<h3>result</h3><h4 style="padding-left:1em">SUCCESS</h4><p style="padding-left:2em">The server was enabled.</p>'
        '<h4 style="padding-left:1em">FAIL</h4><p style="padding-left:2em">The server definition failed to enable </p>'},

    'disable':{'function_name': 'disable', 'description': 'Mark an existing server disabled so that it is no longer checked. '
        'Also attempts to shut down the indicated server.', 'short_description': 'Disable server for checking', 'params': [{'param_name': 'servername',
        'param_default': None, 'param_description': 'The server to disable.', 'param_type': 'text', 'required': False, 'param_options': None}],
        'result_information': 'This function returns data related to the success of whether the server is disabled.'
        '<h3>result</h3><h4 style="padding-left:1em">SUCCESS</h4><p style="padding-left:2em">The server was disabled.</p>'
        '<h4 style="padding-left:1em">FAIL</h4><p style="padding-left:2em">The server was not disabled </p>'},

    'remove':{'function_name': 'remove', 'description': 'Delete the definition of a disabled server.', 'short_description': 'Delete server definition', 'params':
        [{'param_name': 'servername', 'param_default': None,'param_description': 'The server to disable.', 'param_type': 'text', 'required': False, 'param_options': None}],
              'result_information': 'This function returns data related to the success of whether the server was removed.'
        '<h3>result</h3><h4 style="padding-left:1em">SUCCESS</h4><p style="padding-left:2em">The server definition was deleted.</p>'
        '<h4 style="padding-left:1em">FAIL</h4><p style="padding-left:2em">The server definition is still enabled, so it can\'t be deleted. </p>'},

    'alter_server_def':{'function_name': 'alter_server_def', 'description': 'Change details of a server after initialization. Required '
        'because the .conf file is not considered the canonical information about servers once servers.save has been created.',
        'short_description': 'Change server details', 'params': [{'param_name': 'servername', 'param_default': None, 'param_description': 'The existing server whose details are to be changed.',
        'param_type': 'text', 'required': False,  'param_options': None}, {'param_name': 'serverprops', 'param_default': None, 'param_description': 'a set of '
        'key-value pairs for settings to change. Settings may be "changed" to the existing value, so it is permissible '
        'to pass in an entire dictionary of the server config with one changed setting.', 'param_type': 'text',
        'required': False, 'param_options': None}], 'result_information': 'This function returns data related to the current status of the server after it was altered.'
        '<h3>definition</h3><h4>The resulting new definition for the server.</h4><h3>result</h3><h4 style="padding-left:1em">SUCCESS</h4><p style="padding-left:2em">The server definition was altered.</p>'
        '<h4 style="padding-left:1em">FAIL</h4><p style="padding-left:2em">The server definition failed to change.</p>'},

    'add_server':{'function_name': 'add_server', 'description': 'Add a new server to a running handyrep. Needed because handyrep.conf is not considered the canonical source of server information once handyrep has been started.',
        'short_description': 'Add a server', 'params': [{'param_name': 'servername', 'param_default': None, 'param_description': 'The existing server whose details are to be changed.',
        'param_type': 'text', 'required': False, 'param_options': None}, {'param_name': 'serverprops', 'param_default': None, 'param_description': 'a set of key-value '
        'pairs for settings to change. Settings may be "changed" to the existing value, so it is permissible to pass in '
        'an entire dictionary of the server config with one changed setting.', 'param_type': 'text', 'required': False, 'param_options': None}],
        'result_information': 'This function returns data related to the current status of the server after it was added.'
        '<h3>definition</h3><h4>The resulting new definition for the server.</h4><h3>result</h3><h4 style="padding-left:1em">SUCCESS</h4><p style="padding-left:2em">The server was added.</p>'
        '<h4 style="padding-left:1em">FAIL</h4><p style="padding-left:2em">The server addition failed.</p>'},

    'cleanup_archive':{'function_name': 'cleanup_archive', 'description': 'Delete old WALs from a shared WAL archive, according to the '
        'expiration settings in handyrep.conf. Uses the configured archive deletion plugin.',
        'short_description': 'Delete old WALs', 'params': None, 'result_information': 'This function returns data related to the success of whether the WALs were deleted.'
        '<h3>result</h3><h4 style="padding-left:1em">SUCCESS</h4><p style="padding-left:2em">Archives deleted, or archiving is disabled so no action taken.</p>'
        '<h4 style="padding-left:1em">FAIL</h4><p style="padding-left:2em">Archives could not be deleted, possibly because of a permissions or configuration issue. </p>'},

    'connection_proxy_init':{'function_name': 'connection_proxy_init', 'description': 'Set up the connection proxy configuration according to the '
        'configured connection failover plugin. Not all connection proxy plugins support initialization.', 'short_description': 'Connection proxy config','params': None,
                              'result_information': 'This function returns data related to the success of whether the connection proxy configuration was initialized.'
        '<h3>result</h3><h4 style="padding-left:1em">SUCCESS</h4><p style="padding-left:2em">Proxy configuration pushed, or connection failover is not being used.</p>'
        '<h4 style="padding-left:1em">FAIL</h4><p style="padding-left:2em">Error in pushing new configuration, or proxy does not support initialization. </p>'},

    'start_archiving':{'function_name': 'start_archiving', 'description': "Start archiving on the master. This call will push an archive.sh script and remove any noarchiving file, if defined and present (all of this is via plugin methods). It does not set archiving=on in postgresql.conf, so if archiving has not begun after running this, that's the first thing to check.",
                       'short_description': 'Start archiving on the master.','params': None, 'result_information':'This function returns whether archiving was started successfully.'
                        '<p> <b>SUCCESS</b> means archiving should be enabled.</p><p><b>FAIL</b> means either archving is not configured, or was unable to modify the master.</p>'},

    'stop_archiving': {'function_name': 'stop_archiving', 'description': "Stops copying of WAL files on the master. Implemented via the archving plugin. Most archving plugins implement this via a noarchving touch file. This does mean that if the master's disk is 100% full, it will not work.",
                       'short_description': 'Stops copying of WAL files on the master.','params': None, 'result_information':"This function returns whether archiving was stopped successfully."
                        "<p> <b>SUCCESS</b> means noarchving flag is set, or archiving is otherwise disabled.</p><p><b>FAIL</b> means could not disable archiving, either because it is not configured, or because there's something wrong with the master.</p>"},
}

master = {True:("get_server_info", "poll", "verify_server", "alter_server_def", "disable", "restart", "shutdown"), False:("get_server_info", "alter_server_def", "enable", "clone", "remove")}
replica = {True:("get_server_info", "poll", "verify_server", "alter_server_def", "disable", "restart", "shutdown", "manual_failover", "promote", "clone"), False:("get_server_info", "alter_server_def", "enable", "clone", "remove")}
other = {True:("get_server_info", "alter_server_def", "disable"), False:("get_server_info", "alter_server_def", "enable", "remove")}
cluster_functions = ("get_status", "get_cluster_status", "get_master_name", "read_log", "get_setting", "set_verbose",
"verify_all", "poll_all", "init_handyrep_db", "add_server", "connection_proxy_init", "cleanup_archive", "start_archiving",
"stop_archiving", "reload_conf")