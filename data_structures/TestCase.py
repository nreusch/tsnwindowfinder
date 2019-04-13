# Aggregate class for testcase parameters used in optimization
class TestCase(object):
    def __init__(self, switches, streams, tc_name):
        self.tc_name = tc_name
        self.streams = streams
        self.switches = switches
