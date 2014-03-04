# simplest handyrep master selector: makes the assumption
# that there is only one handyrep server in the system
# and always returns True

from plugins.handyrepplugin import HandyRepPlugin

class one_hr_master(HandyRepPlugin):

    def run(self, params=None):
        return self.rd( True, "only one HR server", {"is_master" : True} )

    def test(self, params=None):
        return self.rd( True, "", {"is_master" : True} )