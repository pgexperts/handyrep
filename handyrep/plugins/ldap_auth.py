# authenticates against an
# LDAP server.  all users are assumed to be in
# a specific LDAP group.  The below was tested to
# work with Microsoft AD/LDAP, so it might need changes
# to generically support other kinds of LDAP servers

# for this auth module, the user has to log in
# with their Canonical Name (CN), which may be different from
# their common user name

# requires python_ldap module

import ldap

from plugins.handyrepplugin import HandyRepPlugin

class ldap_auth(HandyRepPlugin):

    def run(self, username, userpass, funcname):

        myconf = self.get_myconf()
        # get list of readonly functions, if any
        rofunclist = myconf["ro_function_list"]

        # try admin password
        if userpass == self.conf["passwords"]["admin_password"]:
            return self.rd(True, "password accepted")
        elif userpass == self.conf["passwords"]["read_password"]:
            if funcname in rofunclist:
                return self.rd(True, "password accepted")
            else:
                return self.rd(False, "That feature requires admin access")
        else:
            return self.rd(False, "password rejected")

    def test(self):
        if self.failed(self.test_plugin_conf("ldap_auth","ro_function_list")):
            return self.rd(False, "plugin ldap_auth is not correctly configured")
        else:
            return self.rd(False, "passwords not set for simple_password_auth")

