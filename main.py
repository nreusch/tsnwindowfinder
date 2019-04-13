import sys
import math
import random

import cost
import input_parser
import time
import numpy as np

from util import Plotter

WCDTOOL_PATH = cost.WCDTOOL_PATH
WCDTOOL_OUTPUTPATH = cost.WCDTOOL_OUTPUTPATH


def create_initial_solution(testCase):
    M_Windows = np.empty([0, 3], dtype=int)
    for switch in testCase.switches.values():
        # Set switch offset to current height of M
        switch.M_row_offset = M_Windows.shape[0]
        for port in switch.output_ports.values():

            total_stream_sending_time_in_port = port.total_stream_sending_time
            current_offset = 0
            for queuenr, queue_sending_time in port.queues_with_sending_time.items():
                # Find the percentage of sending time in window of overall sending time in port

                percentage = queue_sending_time / total_stream_sending_time_in_port

                # Find lowest stream period
                lowest_period = sys.maxsize
                for uid in port.queues_with_streams[queuenr]:
                    if testCase.streams[uid].period < lowest_period:
                        lowest_period = testCase.streams[uid].period

                # Set parameters
                offset = current_offset
                period = lowest_period
                length = int(percentage * period)  # Length = percentage of sending time * period
                M_Windows = np.append(M_Windows, [[offset, length, period]], axis=0)
                # TODO: Deal with different periods in different windows

                # Increase Offset for next window
                current_offset += length

    return [testCase, M_Windows]


def neighbour(s, maxiterations):
    switches = s[0].switches
    M = s[1]

    max_length_interval_factor = 0.1
    iter = 0
    first_iteration = True

    while (cost.check_solution(s) is False or first_iteration is True) and not iter > maxiterations:
        # Look for a feasible neighbour. Cancel after maxiterations
        iter += 1
        first_iteration = False

        r = random.randint(0, 1)
        if r < 1:
            # Change Length Pick random length in interval around current length (interval size =
            # 2*max_length_interval_factor*window.period)
            min = window.length - max_length_interval_factor * window.period
            if min < window.total_sending_time:
                min = window.total_sending_time

            max = window.length + max_length_interval_factor * window.period
            if max + window.offset > window.period:
                max = window.period - window.offset

            r = random.randint(min, max)

            window.length = r
        elif r < 0.66:
            pass
            # Change Period
        else:
            pass
            # Change Offset:

    if iter > maxiterations:
        return None
    else:
        s[0].switches = switches
        return s


def simulated_annealing(s, T, k, maxiterations):
    # Algorithm
    iter = 0
    old_cost = cost.cost(s)
    print("Cost of initial solution: " + str(old_cost))

    # Plotting
    plot_x = np.array([0])
    plot_y = np.array([old_cost])
    plotter = Plotter(2, old_cost, plot_x, plot_y)

    while iter < maxiterations:
        plot_x = np.append(plot_x, iter)
        plot_y = np.append(plot_y, old_cost)
        plotter.plot(plot_x, plot_y)

        # Algorithm
        s_new = neighbour(s, 50)

        if s_new is None:
            print("No feasible neighbour found. Abort")
            break

        # What does cost function need: Switches and their ports and their windows
        new_cost = cost.cost(s_new)
        print("Cost of new solution: " + str(new_cost))

        # TODO: move check to neighbour function?

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

    print(s)
    print("Found final solutian at cost of: " + str(old_cost))
    return s


def main():
    # TODO: Differentiate Solution Matrix and Topology necessary for initial solution, solution checking
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
        maxiterations = 50

        # Algorithm
        final_solution = simulated_annealing(s, T, k, maxiterations)


main()
