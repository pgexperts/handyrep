# generic success plugin
# designed to substitute for a real plugin when
# we don't care about the result, we always want
# to return success
# accepts and ignores args and kwargs so that we can
# swap it in for real plugins

from plugins.handyrepplugin import HandyRepPlugin

class successplugin(HandyRepPlugin):

    def run(self, *args, **kwargs):
        return self.rd( True, "success plugin always succeeds" )

    def test(self, *args, **kwargs):
        return self.rd( True, "success plugin always succeeds" )
