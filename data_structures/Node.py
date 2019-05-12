from data_structures.OutputPort import OutputPort


class Node(object):
    """Any Node in the network, ES or SW"""

    def __init__(self, uid: str):
        """

        Args:
            uid (str): Unique name of the node. Should start with "ES" or "SW", depending on type
        """
        self.uid = uid

        if self.uid.startswith('ES'):
            self.type = 'ES'
        else:
            self.type = 'SW'

    def __repr__(self):
        return 'Node({}, {})'.format(self.type, self.uid)


class Switch(Node):
    """A switch with output ports and queues (used in optimization)"""

    def __init__(self, uid: str):
        """

        Args:
            uid (str): Unique name of the node. Should start with "ES" or "SW", depending on type
        """
        Node.__init__(self, uid)

        self.output_ports = {}  # Map(port_uid, port)

    def add_outputport_to(self, node_uid):
        """
        Adds an output port to a certain node to this switch

        Args:
            node_uid (str): Unique name of the node the output port leads to.
        """
        if node_uid not in self.output_ports.keys():
            self.output_ports[node_uid] = OutputPort(node_uid)

    def associate_stream_to_queue(self, stream_uid: str, stream_length: int, stream_period: int, stream_priority: int,
                                  nextnode_uid: str):
        """
        Adds the stream to the right port and queue. Creates port if not existant.

        Args:
            stream_uid (str): Unique name of stream.
            stream_length (int): Stream length (Byte size/Link Rate) in us
            stream_period (int): Stream period in us.
            stream_priority (int): Stream priority. 0-7. 0 highest
            nextnode_uid (str): The node the stream will go to after this one = Port Name

        Returns:

        """

        if nextnode_uid in self.output_ports.keys():
            # if the output port exists already
            self.output_ports[nextnode_uid].associate_stream_to_queue(stream_uid, stream_length, stream_period,
                                                                      stream_priority)
        else:
            self.add_outputport_to(nextnode_uid)
            self.output_ports[nextnode_uid].associate_stream_to_queue(stream_uid, stream_length, stream_period,
                                                                      stream_priority)
