#plugin for cloning via Rsync.
#currently deals with a linked WAL directory, but NOT with tablespaces.
#assumes passwordless rsync

from plugins.handyrepplugin import HandyRepPlugin
import os.path

class clone_rsync(HandyRepPlugin):

    def run(self, servername, clonefrom, reclone):
        # we assume that upstream has already checked that it is safe
        # to reclone, so we don't worry about it

        myconf = self.myconf()
        # issue pg_stop_backup() on the master
        mconn = self.master_connection(autocommit=True)
        if not mconn:
            return self.rd(False, "unable to connect to master server to start cloning")

        blabel = "hr_clone_%s" % servername
        mcur = mconn.connection()
        bstart = self.execute_it(mcur, "SELECT pg_start_backup(%s, TRUE)", [blabel,])
        mconn.close()
        if not bstart:
            return self.rd(False, "unable to start backup for cloning")

        # rsync PGDATA on the replica
        synccmd = self.rsync_command(servername, clonefrom, "pgdata")
        syncit = self.run_as_postgres(servername, synccmd)
        if self.failed(syncit):
            self.stop_backup(servername)
            return self.rd(False, "unable to rsync files")

        # wipe the replica's wal_location
        # we don't create this wal location, since there's
        # no reason for it to have been deleted.
        repwal = self.wal_path(servername)
        if self.file_exists(repwal):
            syncit = self.run_as_postgres(servername, ["rm -rf %s/*" % repwal,])
        else:
            syncit = self.run_as_postgres(servername, ["mkdir %s" % repwal,])

        # failed?  something's wrong
        if self.failed(syncit):
            self.stop_backup(servername)
            return self.rd(False, "unable to rsync files; WAL directory is missing or broken")

        # stop backup
        syncit = self.stop_backup(servername)
        
        # yay, done!
        if self.succeeded(syncit):
            return self.rd(True, "cloning succeeded")
        else:
            return self.rd(False, "cloning failed; could not stop backup")

    def wal_path(self, servername):
        myconf = self.myconf()
        if "wal_location" in self.servers[servername]:
            if self.servers[servername]["wal_location"]:
                return self.servers[servername]["wal_location"]

        return os.path.join(self.servers[servername]["pgdata"], "pg_xlog")

    def stop_backup(self, servername):
        
        mconn = self.master_connection(autocommit=True)
        if not mconn:
            return self.rd(False, "unable to connect to master server to stop backup")

        mcur = mconn.connection()
        bstart = self.execute_it(mcur, "SELECT pg_stop_backup()")
        mconn.close()
        
        if not bstart:
            return self.rd(False, "unable to stop backup")
        else:
            return self.rd(True, "backup stopped")

    def test(self,servername):
        #check if we have a config
        if self.failed(self.test_plugin_conf("clone_rsync","rsync_path")):
            return self.rd(False, "clone_rsync not properly configured")
        #check if the basebackup executable
        #is available on the server
        if self.failed(self.run_as_postgres(servername,"%s --help" % self.conf["plugins"]["clone_rsync"]["rsync_path"])):
            return self.rd(False, "rsync executable not found")

        return self.rd(True, "clone_rsync works")
