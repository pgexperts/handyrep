# generic failure plugin
# designed to substitute for a real plugin when
# the real plugin errors out
# this way we can hand a readable error message up the stack

from plugins.handyrepplugin import HandyRepPlugin

class failplugin(HandyRepPlugin):

    # override init so we can capture the plugin name
    def __init__(self, pluginname):
        self.pluginname = pluginname
        return

    def run(self, *args, **kwargs):
        return self.rd( False,"broken plugin called or no such plugin exists: %s" % self.pluginname )

    def test(self, *args, **kwargs):
        return self.rd( False,"broken plugin called or no such plugin exists: %s" % self.pluginname )

    def poll(self, *args, **kwargs):
        return self.rd( False,"broken plugin called or no such plugin exists: %s" % self.pluginname )

    def start(self, *args, **kwargs):
        return self.rd( False,"broken plugin called or no such plugin exists: %s" % self.pluginname )

    def stop(self, *args, **kwargs):
        return self.rd( False,"broken plugin called or no such plugin exists: %s" % self.pluginname )
