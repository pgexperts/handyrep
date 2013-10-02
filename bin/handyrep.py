

class HandyRep(Object):

    def __init__(config_file='handyrep.conf', server_file='servers.save'):
        # open the config file
        # validate the file
        # open the current servers file
            # create if not present
            # validate if present
        # open the handyrep table on the master
            # create if not present
            # if handyrep table more updated
            # use that
        # return a handyrep object

    def check_my_status(self):
        # check plugin method to see
        # return result

    def verify_servers(self):
        # check each server definition against
        # the reality
        # update server definitions if required
        # return error if serverdefs don't match
        # succes otherwise

    def sync_config(self):
        # open the handyrep table on the master
            # create if not present
        # if handyrep table more updated
            #supercede local servers.save
        # otherwise, save serverinfo to table
        # save all files
        # return true if changes synced

    def check_master(self):
        # check master using poll method
        # if false, try to restart master
        # otherwise, poll again after retry_interval
        # if failed retry_times, raise error

    def check_replica(self, replicaserver):
        # check replical using poll method
        # check that it's in replication
        # check that it's seen from master
        # check replica lag
        # if any checks fail, error
        # otherwise, return success

    def get_server_status(self, servername=None):
        # if no server given, loop through all
        # get master info
        # for each replica:
            # check that replica is up and replicating
            # if replica isn't replicating, raise error and change status
            # check replica lag
        # return all status info

    def failover_check(self):
        # check master
        # if failed, failover
        # return 

    def failover(self, newmaster=None, remaster=None):
        # if newmaster isnt set, poll replicas for new master
        # according to selection_method
        # if remaster not set, get from settings
        # attempt STONITH
            # if failed, abort and reset
        # attempt replica promotion
            # if failed, try to abort and reset
            # if success, update servers.save
        # if remastering, attempt to remaster
        # update servers.save
        # run post-failover scripts

    def stonith(self, oldmaster=None):
        # get master from serversettings if not supplied
        # test if we can ssh to master
            # check if PG is running
            # if so, run shutdown
            # if shutdown fails, error out
        # test if master IP is up

    def promote(self, newmaster):
        # test access to new master
        # can we ssh?
        # is it running?
        # is it a replica?
        # if all true, send promote command
        # return true if successful, otherwise error

    def remaster(self, replicaserver, newmaster=None):
        # use master from settings if not supplied
        # change replica config
        # restart replica
        # check for fail
        # sync server config

    def clone(self, replicadict, clonefrom=None):
        # use config master if not supplied
        # abort if this is already a replica
        # clone using clone_method
        # write recovery.conf
        # start replica
        # update servers.save
        # check replica status to make sure it's up
            # updates servers.save and fail if not
        # report success

    def reclone(self, replicaserver, clonefrom=None):
        # check server config
        # shutdown replica, if required
        # clone using clone_method, with delete flag if necessary
        # write recovery.conf
        # write servers.save
        # start up replica
        # check status
            # update servers.save on fail
        # return success

    def shutdown(self, servername):
        # shutdown server
        # poll for shut down

    def remove(self, replicaserver):
        # shutdown replica
        # remove from servers.save

    def get_server_info(self, servername=None, format="json", sync=True):
        # formats: json, yaml
        # if sync:
            # verify_servers
            # sync_config if changed
        # if all, return all servers
        # otherwise return just the one

    def get_server_role(self, serverrole, format="json", sync=True):
        # formats: json, yaml
        # roles: master, replicas
        # if sync:
            # verify_servers
            # sync_config if changed
        # return master if master
        # if replicas, return all replicas

    def validate_server_settings(self, servername, serverdict):
        # check each setting against the existing servers
        # check for possible, rather than current

    def change_server(self, servername, serverdict, isnew=false):
        # verify servers
        # validate new settings
        # check for settings we don't do, like recloning
        # check each setting against the existing settings for the server
        # for changed settings & new servers
            # does the setting need to be pushed to the server?
            # if so, push it to the server
            # check for success; error out on fail
        # sync server config
        # exit with success

    def clean_archive(self, expire_hours=None, archivedict=None):
        # if not archive details, then
        # use config
        # delete files from archive which are older
        # than setting

            


        