import numpy as np


class OutputPort(object):
    """An output port on a switch. Contains up to 8 queues, each with one window. Windows are stored in matrix M for
    fast manipulation. """

    def __init__(self, node_uid: str):
        """

        Args:
            node_uid (str): Unique name of the node the output port leads to.
        """
        self.name = node_uid
        self.queues = {}  # Map(Priority(int), Queue)
        self._M_Windows = np.empty(shape=[0, 3],
                                   dtype=int)  # Window Matrix (<=8 Rows, 3 Columns), [[start0, end0, period0], ...]

    def associate_stream_to_queue(self, stream_uid: str, stream_length: int, stream_period: int,
                                  stream_priority: int):
        """
        Adds the stream to the queue with the right priority.

        Args:
            stream_uid (str): Unique name of stream.
            stream_length (int): Stream length (Byte size/Link Rate) in us
            stream_period (int): Stream period in us.
            stream_priority (int): Stream priority. 0-7. 0 highest

        Returns:
            True, if queue with stream_priority didn't exist yet
        """

        if stream_priority not in self.queues.keys():
            self.queues[stream_priority] = Queue()
            self.queues[stream_priority].add_stream(stream_uid, stream_length, stream_period)
            # Add Row in window matrix for this queue
            self._M_Windows = np.append(self._M_Windows, [[0, 0, 0]], axis=0)
            return True
        else:
            self.queues[stream_priority].add_stream(stream_uid, stream_length, stream_period)
            return False

    def get_sorted_queuenrs(self):
        """

        Returns:
            List of Queues, sorted by priority (highest(0) first)
        """
        return sorted(self.queues)

    def get_minimum_window_percentage(self):
        """

        Returns:
            The minimum window percentage of all queues
        """
        return min([q.window_percentage for q in self.queues.values()])

    def set_window(self, priority: int, offset: int, length: int, period: int):
        """
        Sets a window of a given priority. Should only be done if all desired priority queues already exist! (First add all streams, then set windows)

        Args:
            priority (int): Window Priority
            offset (int): Window Offset
            length (int):  Window Length
            period (int): Window Period

        """
        matrix_index = self.get_sorted_queuenrs().index(priority)
        self._M_Windows[matrix_index] = [offset, offset + length, period]

    def get_window(self, priority: int):
        """

        Args:
            priority (int): Window Priority

        Returns:
            [offset, offset+length, period] for window with given priority
        """
        matrix_index = self.get_sorted_queuenrs().index(priority)
        return self._M_Windows[matrix_index]

    def multipy_period(self, factor: float):
        """
        Multiplies all window period with factor. rounds down to next int.

        Args:
            factor (float): factor for multiplication

        """
        factor_matrix = np.array([
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, factor]
        ])

        self._M_Windows = np.floor(np.matmul(self._M_Windows, factor_matrix))

    def get_occupation_percentage(self):
        """

        Returns:
            How much percent of hyperperiod of this port is occupied
        """
        # Total Window Length = End of last Window
        total_length = self._M_Windows[len(self.queues) - 1][1]
        # Period = Period of any Window
        period = self._M_Windows[0][2]

        return total_length / period


class Queue(object):
    """A Queue on an output port. Keeps track of the streams associated to it."""

    def __init__(self):
        self.window_percentage = 0
        self.total_sending_time = 0
        self.highest_sending_time = 0
        self.stream_uids = []

    def add_stream(self, stream_uid: str, stream_length: int, stream_period: int):
        """

        Args:
            stream_uid (str): Unique name of stream.
            stream_length (int): Stream length (Byte size/Link Rate) in us
            stream_period (int): Stream period in us.

        Returns:

        """
        self.window_percentage += stream_length / stream_period
        self.total_sending_time += stream_length

        if stream_length > self.highest_sending_time:
            self.highest_sending_time = stream_length

        self.stream_uids.append(stream_uid)
