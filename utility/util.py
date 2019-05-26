import math

import matplotlib.pyplot as plt
import time
import numpy as np

DEBUG = False


def debug_print(s, end='\n'):
    if DEBUG:
        print(s, end=end)

class Plotter(object):
    def __init__(self, graph_update_interval, start_cost, x_init, y_init):
        self.start_time = time.time()
        self.graph_update_interval = graph_update_interval

        plt.ion()
        fig = plt.figure()
        ax = fig.add_subplot(111)

        plt.ylim((0, start_cost + 100))
        plt.xlim((0, 50))

        self.line1, = ax.plot(x_init, y_init, 'r-')
        plt.draw()

    def plot(self, x, y):
        if time.time() - self.start_time > self.graph_update_interval:
            self.line1.set_xdata(x)
            self.line1.set_ydata(y)
            plt.draw()
            plt.pause(0.02)

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

def list_lcm(V: list):
    '''

    Args:
        V (list): listof elements

    Returns:
        Least common multiple of list
    '''
    # DEBUG
    debug_print('Calculating LCM of: ')
    debug_print(V)

    lc = np.lcm.reduce(np.asarray(V))
    debug_print('Result: ')
    debug_print(lc)
    return lc


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