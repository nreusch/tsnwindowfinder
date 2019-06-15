import math

import numpy as np

from utility.util import matrix_gcd, create_binary_matrix, vector_lcm

DEBUG = False


def debug_print(s, end='\n'):
    if DEBUG:
        print(s, end=end)


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
        self._upper_bound = 0
        self._lower_bound = 0
        self._free_period = -1

        # TODO: CP
        self._M_WindowsVar = np.empty(
            shape=[0, 3])  # Window Matrix (<=8 Rows, 3 Columns), [[start0, end0, period0], ...]

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
            # TODO: CP
            self._M_WindowsVar = np.append(self._M_WindowsVar, [[{}, {}, {}]], axis=0)
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

    def delete_queue(self, priority: int):
        matrix_index = self.get_sorted_queuenrs().index(priority)
        np.delete(self._M_Windows, (matrix_index), axis=0)
        self.queues.pop(priority)

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

        self._M_Windows = np.matmul(self._M_Windows, factor_matrix).astype(int)

    def dq_reset(self):
        self._free_period = -1
        self._upper_bound = 0
        self._lower_bound = 0

    def dq_modify_period(self, lower: bool):
        '''

        Args:
            lower (bool): Lower or upper half?

        Returns:
            True, if period could still be modified
        '''

        # Free Period not set yet?
        if self._free_period is -1:
            # free_period = period - length of all windows (=end time of last window if they are ordered)
            self._free_period = self._M_Windows[0][2] - self._M_Windows[len(self.queues) - 1][1]
            self._upper_bound = self._free_period

        if lower:
            self._upper_bound = self._free_period
            self._free_period = math.floor(self._free_period - (self._upper_bound - self._lower_bound)/2)
            if self._free_period == self._upper_bound:
                # If free period doesnt change anymore
                return False
        else:
            self._lower_bound = self._free_period
            self._free_period = math.floor(self._free_period + (self._upper_bound - self._lower_bound) / 2)
            if self._free_period == self._lower_bound:
                # If free period doesnt change anymore
                return False

        self.set_period_for_all(self._M_Windows[len(self.queues) - 1][1] + self._free_period)
        return True

    def set_period_for_all(self, value):
        period_array = np.full(self._M_Windows.shape[0], value)
        self._M_Windows[:, 2] = period_array

    def get_occupation_percentage(self):
        """

        Returns:
            How much percent of hyperperiod of this port is occupied
        """
        # Calculate using binary matrix representing windows
        g = matrix_gcd(self._M_Windows)  # length in us of one digit in binary
        l = self.get_hyperperiod() # hyperperiod
        M_binary = create_binary_matrix(self._M_Windows, g, l)

        result_binary = np.bitwise_or.reduce(M_binary, 0)

        occupied_time = np.count_nonzero(result_binary)
        total_time = result_binary.shape[0]

        return occupied_time / total_time

    def get_hyperperiod(self):
        return int(vector_lcm(self._M_Windows[:, 2:]))

    def get_minimum_period_with_current_windows(self):
        max_end = 0
        for row in self._M_Windows:
            if row[1] > max_end:
                max_end = row[1]
        return int(max_end)

    def set_period_for_priority(self, value, priority):
        self.get_window(priority)[2] = value

    # TODO: CP

    def set_window_var(self, priority: int, offset, length, period):
        """
        Sets a window of a given priority. Should only be done if all desired priority queues already exist! (First add all streams, then set windows)

        Args:
            priority (int): Window Priority
            offset (int): Window Offset
            length (int):  Window Length
            period (int): Window Period

        """
        matrix_index = self.get_sorted_queuenrs().index(priority)
        self._M_WindowsVar[matrix_index] = [offset, length, period]

    def get_window_var(self, priority: int):
        """

        Args:
            priority (int): Window Priority

        Returns:
            [offset, offset+length, period] for window with given priority
        """
        matrix_index = self.get_sorted_queuenrs().index(priority)
        return self._M_WindowsVar[matrix_index]

    def get_maximium_period(self, priority: int):
        matrix_index = self.get_sorted_queuenrs().index(priority)
        return int(self._M_Windows[matrix_index][2])

    def get_minimium_period(self, priority: int):
        matrix_index = self.get_sorted_queuenrs().index(priority)
        return int(self._M_Windows[matrix_index][1]) #- self._M_Windows[matrix_index][0]

    def get_sum_of_window_lengths(self):
        return int(self._M_Windows[len(self.queues) - 1][1])

    def get_minimum_window_length(self, priority: int):
        return int(self.get_minimium_period(priority))

    def get_maximum_window_length(self, priority: int):
        return int(self.get_maximium_period(priority) - self.get_sum_of_window_lengths() + self.get_minimum_window_length(priority))

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



