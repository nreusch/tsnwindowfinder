class TestCase(object):
    """Represent a testcase and is used during optimization, where the windows in switches are manipulated"""
    def __init__(self, switches: dict, streams: dict, tc_name: str):
        """

        Args:
            switches (dict): Dict(switch_uid, Switch)
            streams (dict): Dict(stream_uid, Stream)
            tc_name (str): Name of the testcase
        """
        self.name = tc_name
        self.streams = streams
        self.switches = switches
