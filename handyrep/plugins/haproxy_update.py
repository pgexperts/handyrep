# simple haproxy plugin for updating haproxy configuration.
# creates 3 pools - general, master & slaves
# this assumes defaults are set in /etc/haproxy/haproxy.conf

from plugins.handyrepplugin import HandyRepPlugin
from fabric.contrib.files import upload_template

class haproxy_update(HandyRepPlugin):

    def run(self, *args):
 
		myconf = self.get_conf("plugins","haproxy_update")

		haproxytemp = myconf["haproxy_template"]

		bbparam = { "hap_pg_cfg" : "/home/handyrep/haproxy_pg_conf.cfg" }		
		haproxycmd = "haproxy -f /etc/haproxy/haproxy.cfg -f %(hap_pg_cfg)s -p /var/run/haproxy.pid -st $(cat /var/run/haproxy.pid)" % bbparam
			
		haproxy_cfg = {}
		haproxy_cfg["pool_port"] = myconf["pool_port"] 
		haproxy_cfg["master_pool_port"] = myconf["master_pool_port"] 
		haproxy_cfg["slave_pool_port"] = myconf["slave_pool_port"] 
		haproxy_cfg["pg_port"] = self.get_conf("server_defaults","port") 
		haproxy_cfg["master_server"] = self.get_master_name() 
		haproxy_cfg["slave_servers"] = self.sorted_replicas()

		for haproxyserv in self.get_servers(role='haproxy'):			
			# upload_template to haproxy server		
			self.push_template(haproxyserv, haproxytemp, myconf["hap_pg_cfg"], haproxy_cfg, new_owner=None, file_mode=755)
			# update the haproxy memory configuration
				updated = self.run_as_root(haproxyserv, [haproxycmd,])
        return updated

    def test(self):
        #check if we have a config
        if self.failed(self.test_plugin_conf("haproxy_update","haproxy_template","hap_pg_cfg")):
            return self.rd(False, "haproxy_update not properly configured")
        #check if the basebackup executable
        #is available on the server
        #if self.failed(self.run_as_postgres(servername,"%s --help" % self.conf["plugins"]["clone_basebackup"]["basebackup_path"])):
        #    return self.rd(False, "pg_basebackup executable not found")

        return self.rd(True, "haproxy_update works")
