# Aggregate class for testcase parameters used in optimization
class TestCase(object):
    def __init__(self, switches, streams, name):
        self.name = name
        self.streams = streams
        self.switches = switches
