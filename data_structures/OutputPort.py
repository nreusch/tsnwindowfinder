import math

import numpy as np

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

        self._M_Windows = np.matmul(self._M_Windows, factor_matrix).astype(int)

    def get_occupation_percentage(self):
        """

        Returns:
            How much percent of hyperperiod of this port is occupied
        """
        # Calculate using binary matrix representing windows
        g = matrix_gcd(self._M_Windows)  # length in us of one digit in binary
        l = vector_lcm(self._M_Windows[:, 2:])  # hyperperiod
        M_binary = create_binary_matrix(self._M_Windows, g, l)

        result_binary = np.bitwise_or.reduce(M_binary, 0)

        occupied_time = np.count_nonzero(result_binary)
        total_time = result_binary.shape[0]

        return occupied_time / total_time


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


def create_binary_matrix(M_port: np.ndarray, gcd: int, lcm: int):
    '''

    Args:
        M_port (numpy.ndarray): Windows matrix (of a port) (start, end, period)
        gcd (int): Greates common divisor of all matrix element. Can be used to compress matrix if >1
        lcm (int): hyperperiod of the ports periods

    Returns:
        A matrix representing the windows in binary. ((0,5,10),(5,7,10)) -> ((1111100000),(0000011000))
    '''
    if int(gcd) != 0 and int(lcm) != 0:
        # DEBUG
        debug_print("GCD: {}; LCM: {}; Total number of columns (lcm/gcd): {}".format(gcd, lcm, int(lcm / gcd)))

        M_binary = np.empty([0, int(lcm / gcd)], dtype=int)

        for row in M_port:
            offset = row[0]
            length = row[1] - offset
            period = row[2]

            a = np.zeros((int(offset / gcd)), dtype=bool)
            if len(a) > 0:
                a = np.concatenate((a, np.ones((int(length / gcd)), dtype=bool)), axis=0)
            else:
                a = np.ones((int(length / gcd)), dtype=bool)
            a = np.concatenate((a, np.zeros((int((period - offset - length) / gcd)), dtype=bool)), axis=0)
            a = np.tile(a, int(lcm / period))
            debug_print('Resulting binary with length {}: '.format(len(a)))
            debug_print(a)
            M_binary = np.append(M_binary, [a], 0)

            # DEBUG
            debug_print('Window with offset {}, length {}, period {}'.format(offset, length, period))
            debug_print('Resulting binary with length {}: '.format(len(a)))
            debug_print(a)

        # DEBUG
        debug_print('Final Binary Matrix: ')
        debug_print(M_binary)
        return M_binary
    else:
        raise ValueError('Error. GCD or LCM equals zero. GCD: {} LCM {}'.format(gcd, lcm))


def vector_lcm(V: np.ndarray):
    '''

    Args:
        V (numpy.ndarray): vector (1d matrix) of elements

    Returns:
        Least common multiple of array
    '''
    # DEBUG
    debug_print('Calculating LCM of: ')
    debug_print(V)

    lc = np.lcm.reduce(V)
    debug_print('Result: ')
    debug_print(lc)
    return lc[0]


# https://stackoverflow.com/questions/15569429/numpy-gcd-function
def matrix_gcd(M: np.ndarray):
    '''

    Args:
        M (numpy.ndarray): Matrix

    Returns:
        Greates common divisor of all matrix elements
    '''
    M = M.flatten()

    gcd = M[0]
    for i in M:
        gcd = math.gcd(i, gcd)
        if gcd == 1:
            return 1

    return gcd
