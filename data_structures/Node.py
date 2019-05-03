from collections import OrderedDict


# Any Node in the network
class Node(object):
    def __init__(self, uid: 'unique name'):
        self.uid = uid

        if self.uid.startswith('ES'):
            self.type = 'ES'
        else:
            self.type = 'SW'

    def __repr__(self):
        return 'Node({}, {})'.format(self.type, self.uid)


# A switch with output ports and queues (used in optimization)
class Switch(Node):
    def __init__(self, uid: 'unique name'):
        Node.__init__(self, uid)

        self.total_number_of_queues = 0  # equals the amount of lines in the window matrix
        self.M_row_offset = 0
        self.output_ports = OrderedDict()  # Output ports are kept in an ordered dict port_name -> Port, which establishes their order in the window-submatrix for switches

    def add_outputport_to(self, node_name):
        # Both Source-ES and switches have outputports
        if node_name not in self.output_ports.keys():
            self.output_ports[node_name] = Port(node_name)

    def associate_stream_to_queue(self, stream_uid, stream_length, stream_period, queuenr,
                                  nextnode_uid: 'The node the stream will go to after this one'):
        # gives the order to the ports function

        if nextnode_uid in self.output_ports.keys():
            # if the output port exists already

            if self.output_ports[nextnode_uid].associate_stream_to_queue(stream_uid, stream_length, stream_period, queuenr):
                # If the port didn't have this queue yet
                self.total_number_of_queues += 1
        else:
            self.add_outputport_to(nextnode_uid)
            self.output_ports[nextnode_uid].associate_stream_to_queue(stream_uid, stream_length, stream_period, queuenr)
            self.total_number_of_queues += 1


# A port of a switch containing metainformation like amount of streams and their percentages
class Port(object):
    def __init__(self, name):
        self.name = name
        self.stream_amount = 0
        self.queues_with_window_percentage = {}
        self.queues_with_streams = {}

    def associate_stream_to_queue(self, stream_uid, stream_length, stream_period, queuenr):
        self.stream_amount += 1

        if queuenr not in self.queues_with_window_percentage.keys():
            self.queues_with_window_percentage[queuenr] = stream_length / stream_period
            self.queues_with_streams[queuenr] = [stream_uid]
            return True
        else:
            self.queues_with_window_percentage[queuenr] += stream_length / stream_period
            self.queues_with_streams[queuenr].append(stream_uid)
            return False

    def get_sorted_queuenrs(self):
        return  sorted(self.queues_with_window_percentage)

    def get_minimum_window_percentage(self):
        return min(self.queues_with_window_percentage.values())