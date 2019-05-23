import math


class Stream(object):
    """Represents a TSN Stream with fixed deadline, route and priority"""

    def __init__(self, uid: str, size: int, deadline: int, period: int, priority: int, route: list):
        """

        Args:
            uid (str): Unique Name
            size (int): Byte Size
            deadline (int): Deadline in us
            period (int): Period in us
            priority (int): Priority. 0-7. 0 highest
            route (list): Ordered list of Nodes, from start ES to destionation ES
        """
        self.uid = uid
        self.size = size
        self.deadline = deadline
        self.route = route
        self.period = period
        self.priority = priority

        # 1 Byte takes 0.008us at 1000Mbits, 42bit header for ethernet packet. Round down.
        self.sending_time = math.ceil((self.size + 42) * 0.008)
        # TODO: If following Ethernet Specifications, each 1500 Byte block needs a 42 byte header
        # TODO: Check with Luxi how sending time is calculated

    def __repr__(self):
        rtstring = ''
        for node in self.route:
            rtstring += node.uid + '->'
        rtstring = rtstring[:-2]
        return 'Stream(UID: {}, DataSize: {}Byte, Deadline: {}us, Period: {}us, Priority: {}, Route:{})'.format(
            self.uid, self.size, self.deadline, self.period, self.priority, rtstring)
