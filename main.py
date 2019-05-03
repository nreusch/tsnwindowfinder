import sys
import math
import random

import cost
from utility import input_parser
import numpy as np

from utility.util import Plotter

import cProfile

WCDTOOL_PATH = cost.WCDTOOL_PATH
WCDTOOL_OUTPUTPATH = cost.WCDTOOL_OUTPUTPATH


def create_initial_solution(testCase):
    M_Windows = np.empty([0, 3], dtype=int)
    for switch in testCase.switches.values():
        # Set switch offset to current height of M
        switch.M_row_offset = M_Windows.shape[0]
        for port in switch.output_ports.values():
            current_offset = 0
            minimum_window_percentage = port.get_minimum_window_percentage()
            max_period = math.ceil(12 * (1 / minimum_window_percentage))
            first = False

            for queuenr in port.get_sorted_queuenrs():
                window_percentage = port.queues_with_window_percentage[queuenr]
                period = math.ceil(12 * (1 / window_percentage))

                scale_factor = max_period / period

                # Every window except the highest priority one has to be extended by 12us due to timely block
                if first:
                    length = math.ceil(12 * scale_factor)
                    first = False
                else:
                    length = math.ceil(12 * scale_factor) + 12

                period = max_period

                M_Windows = np.append(M_Windows, [[current_offset, current_offset+length, period]], axis=0)

                # Increase Offset for next window
                current_offset += length

    return [testCase, M_Windows]


def neighbour(s, maxiterations):
    switches = s[0].switches
    M = s[1]

    iter = 0
    first_iteration = True

    while (cost.check_solution(s) is False or first_iteration is True) and not iter > maxiterations:
        # Look for a feasible neighbour. Cancel after maxiterations
        iter += 1
        first_iteration = False

        # TODO: Manipulate M
        M_mul = np.array([
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1]
        ])
        M = np.matmul(M, M_mul)

    if iter > maxiterations:
        return None
    else:
        s[0].switches = switches
        s[1] = M
        return s


def simulated_annealing(s, T, k, maxiterations):
    if not cost.check_solution(s):
        raise ValueError('Initial Solution invalid')

    print('Initial Solution:')
    print(s[1])

    # Algorithm
    iter = 0
    old_cost = cost.cost(s)
    print("\nCost of initial solution: " + str(old_cost) + "\n")

    # Plotting
    plot_x = np.array([0])
    plot_y = np.array([old_cost])
    plotter = Plotter(2, old_cost, plot_x, plot_y)

    while iter < maxiterations:
        print('\n Iteration ' + str(iter))
        plot_x = np.append(plot_x, iter)
        plot_y = np.append(plot_y, old_cost)
        plotter.plot(plot_x, plot_y)

        # Algorithm
        s_new = neighbour(s, 50)

        if s_new is None:
            print("No feasible neighbour found. Abort")
            break

        new_cost = cost.cost(s_new)
        print("Cost of new solution: " + str(new_cost))

        if new_cost < old_cost:
            s = s_new
            old_cost = new_cost
        else:
            r = random.uniform(0, 1)
            delta = cost.cost(s_new) - cost.cost(s)
            if r < math.exp(-1 * delta / T):
                s = s_new
                old_cost = new_cost
                print("New Solution taken anyway")

        iter += 1
        T = T * k

    print('\nFinal Solution:')
    print(s[1])
    print("\nCost of final solution: " + str(old_cost) + "\n")
    return s


def main():
    testcases_path = sys.argv[1]
    test_cases = input_parser.find_testcases(testcases_path)

    # for each testcase
    for i, test_case in enumerate(test_cases):
        # read testcase
        tc_name, output_folder = input_parser.determine_and_create_output_directory(test_case)
        testCase = input_parser.parse_testcase(testcases_path, tc_name, WCDTOOL_PATH,
                                               WCDTOOL_OUTPUTPATH)

        # Initial parameters
        s = create_initial_solution(testCase)  # s = [TestCase, M_Windows]
        T = 1000
        k = 0.95
        maxiterations = 25

        print('\n#########################\nTest Case: {}\nT: {}\nk: {}\nMax Iterations: {}\n#########################\n'.format(tc_name,T,k,maxiterations))

        # Algorithm
        simulated_annealing(s, T, k, maxiterations)


main()
