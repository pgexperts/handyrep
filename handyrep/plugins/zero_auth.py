# authentication plugin for zero authentication
# setups.  always succeeds

from plugins.handyrepplugin import HandyRepPlugin

class zero_auth(HandyRepPlugin):

    def run(self, username, userpass, funcname):
        return self.rd( True, "authenticated" )

    def test(self):
        return self.rd( True, "tested" )
