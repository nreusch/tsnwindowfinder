class TestCase(object):
    """Represent a testcase and is used during optimization, where the windows in switches are manipulated"""
    def __init__(self, switches: dict, streams: dict, tc_name: str, nr_of_ES=0):
        """

        Args:
            switches (dict): Dict(switch_uid, Switch)
            streams (dict): Dict(stream_uid, Stream)
            tc_name (str): Name of the testcase
            nr_of_ES (int): Number of End-Systems
        """
        self.name = tc_name
        self.streams = streams
        self.switches = switches

        self.ESNr = nr_of_ES
        self.SWNr = len(switches)
        self.StreamNr = len(streams)