# simple authentication using just the two
# passwords saved in the "passwords" section of handyrep.conf
# defines a read-only vs. admin role
# ignores the username

from plugins.handyrepplugin import HandyRepPlugin

class simple_password_auth(HandyRepPlugin):

    def run(self, username, userpass, funcname):

        myconf = self.get_myconf()
        # get list of readonly functions, if any
        rofunclist = myconf["ro_function_list"]
        if rofunclist is None:
            rofunclist = ["no_such_function",]

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
        if self.failed(self.test_plugin_conf("simple_password_auth","ro_function_list")):
            return self.rd(False, "plugin simple_password_auth is not correctly configured")
        else:
            if self.get_conf("passwords","admin_password") and self.get_conf("passwords","read_password"):
                return self.rd(True, "plugin passes")
            else:
                return self.rd(False, "passwords not set for simple_password_auth")

