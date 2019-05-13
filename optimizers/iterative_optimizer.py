import copy
import math
import os
import time
import matplotlib
import numpy as np
import matplotlib.pyplot as plt
from typing import NamedTuple

from cost_check import CostChecker
from solution_check import SolutionChecker
from data_structures.TestCase import TestCase


def create_initial_solution(testCase: TestCase):
    """

    Args:
        testCase (TestCase): initial testcase (without windows)

    Returns:
        Initial Solution as TestCase Object (with windows set)
    """
    for switch in testCase.switches.values():
        for port in switch.output_ports.values():
            max_port_period = 0

            # 1. Calculate Length & Period for each queue. Determine Max Period
            for queuenr in port.get_sorted_queuenrs():
                queue = port.queues[queuenr]

                length = queue.total_sending_time + queue.highest_sending_time
                period = math.floor(queue.total_sending_time * (1 / queue.window_percentage))

                if period > max_port_period:
                    max_port_period = period

                port.set_window(queuenr, 0, length, period)

            # 2. Scale all other queues to Max Period. Set Offsets
            current_offset = 0
            for queuenr in port.get_sorted_queuenrs():
                queue = port.queues[queuenr]
                period = port.get_window(queuenr)[2]

                scale_factor = max_port_period / period

                # Only the total sending time has to be scaled up
                length = queue.total_sending_time * scale_factor + queue.highest_sending_time
                period = max_port_period

                port.set_window(queuenr, current_offset, length, period)
                current_offset += length

    return testCase


def get_worst_stream(s: TestCase, exceeding_percentages: dict):
    """

    Args:
        s (TestCase): Current solution as TestCase object
        exceeding_percentages (dict): Exceeding percentages of all streams that missed their deadline stored in Dict(
        Percentage(float), stream uid(str))

    Returns:
        The stream with the highest exceeding percentage ("worst stream") as Stream object or None
    """

    # Sort the dict so highes exceeding percentage is first
    sorted_keys = sorted(exceeding_percentages.keys(), reverse=True)
    if len(sorted_keys) is 0:
        return None

    worst_stream_uid = exceeding_percentages[sorted_keys[0]][0]
    return s.streams[worst_stream_uid]


def iterative_optimization(solution: TestCase, p: float, cost_checker: CostChecker, solution_checker: SolutionChecker):
    """

    Args:
        solution (TestCase): Initial Solution as TestCase object
        p (float):  period adjustment percentage
        cost_checker (CostChecker): CostChecker object
        solution_checker (SolutionChecker): SolutionChecker object

    Returns:
        Final Solution as TestCase object
    """
    initial_solution = copy.deepcopy(solution)
    print('\n#########################\nTest Case: {}\n#########################\n'.format(solution.name))

    ##### 1. Algorithm #####
    t_start = time.process_time()
    is_feasible, exceeding_percentages, initial_wcds = solution_checker.check_solution(solution, 20)

    while not is_feasible:

        # 1. Get Worst Stream
        worst_stream = get_worst_stream(solution, exceeding_percentages)

        # 2. Optimize Worst Stream

        # Iterate through ports on route (ES sliced out), decrease period
        i = 1
        for node in worst_stream.route[1:-1]:
            print('.', end='', flush=True)
            # Get switch object
            assert (node.type == 'SW')
            switch = solution.switches[node.uid]

            # Determine Port
            port_uid = worst_stream.route[i + 1].uid
            port = switch.output_ports[port_uid]

            # Decrease Period
            port.multipy_period(p)

            # Check if solution/stream is feasible now. If yes break.
            is_feasible, exceeding_percentages, final_wcds = solution_checker.check_solution(solution, 20)
            if is_feasible:
                break
            elif not get_worst_stream(solution, exceeding_percentages) == worst_stream:
                break

            i += 1

    cost = cost_checker.cost_port(solution)
    runtime = time.process_time() - t_start
    print('\n----------------- Solved with cost: {} -----------------'.format(cost))

    ##### 2. Prepare Output Data & Return #####
    output_data = OutputData(initial_solution, solution, initial_wcds, final_wcds, runtime, cost)
    return output_data


class OutputData(NamedTuple):
    """Immutable Tuple to store all the information needed to generate the output files"""
    initial_solution: TestCase
    final_solution: TestCase
    initial_wcds: dict  # Dict(Stream Name, wcd)
    final_wcds: dict  # Dict(Stream Name, wcd)
    runtime: float
    cost: float


def write_windows(filename: str, switches: dict):
    """

    Args:
        filename (str): File to write to
        switches (dict): Switches dict

    """
    windows_file = open(filename, 'w+')
    lines = ['#open time, close time, period, priority\n']

    for switch in switches.values():
        for dest_name in switch.output_ports.keys():
            port = switch.output_ports[dest_name]
            lines.append('{},{}\n'.format(switch.uid, dest_name))

            i = 0
            for priority in port.get_sorted_queuenrs():
                row = port._M_Windows[i]
                offset = row[0]
                end = row[1]
                period = row[2]
                lines.append(
                    '{}\t{}\t{}\t{}\n'.format(offset, end, period,
                                              priority))
                i += 1

            lines.append('\n')

    windows_file.write(''.join(lines))
    windows_file.write('#')  # comment out last line, since no empty last line is allowed
    windows_file.close()


def render_bar_graph(filename: str, streams: dict, wcds: dict):
    """

    Args:
        filename (str): File to write to
        streams (dict): Dict(Stream Name, Stream)
        wcds (dict): Dict(Stream Name, wcd)

    """
    n_groups = len(wcds.keys())
    label_list = []
    wcd_list = []
    ddl_list = []

    for stream_uid in wcds.keys():
        wcd_string = wcds[stream_uid]
        if wcd_string.endswith('INF'):
            wcd_list.append(0)
            # TODO: Visualize Infinity
        else:
            wcd = int(float(wcd_string))
        deadline = streams[stream_uid].deadline

        label_list.append(stream_uid)
        wcd_list.append(wcd)
        ddl_list.append(deadline)

    fig, ax = plt.subplots()

    index = np.arange(n_groups)
    bar_width = 0.35

    opacity = 0.4

    rects1 = ax.bar(index, ddl_list, bar_width,
                    alpha=opacity, color='r',
                    label='Deadline')

    rects2 = ax.bar(index + bar_width, wcd_list, bar_width,
                    alpha=opacity, color='b',
                    label='WCD')

    ax.set_xlabel('Streams')
    ax.set_ylabel('Deadlines & Worst Case Delays')
    ax.set_title('Deadlines & Worst Case Delays for all streams')
    ax.set_xticks(index + bar_width / 2)
    ax.set_xticklabels(('A', 'B', 'C', 'D', 'E'))
    ax.legend()

    fig.tight_layout()
    plt.savefig(filename)


class IterativeOptimizer(object):
    """Finds a solution to the testcase by constructivly generating a good initial solution. Then proceeds to make
    all stream feasible (catch their deadline), by reducing the periods of the ports on their route """

    def run(self, testcase: TestCase, wcdtool_path: str, wcdtool_testcase_subpath: str, output_folder: str, p: float):
        """

        Args:
            testcase (TestCase):  Testcase
            wcdtool_path (str): Path to WCDTool executable
            wcdtool_testcase_subpath (str): Relative path from WCDTool executable to testcase folder
            output_folder (str): Path to output folder
            p (float): period adjustment percentage

        Returns:
            TestCase object for final solution
        """
        initial_solution = create_initial_solution(testcase)
        output_data = iterative_optimization(initial_solution, p, CostChecker(),
                                             SolutionChecker(wcdtool_path, wcdtool_testcase_subpath))
        self.generate_output(output_data, output_folder)
        return output_data.final_solution

    def generate_output(self, output_data: OutputData, output_folder: str):
        """

        Args:
            output_data (OutputData): all the information needed to generate the output files
            output_folder (str): Path to output folder

        """
        tc_name = output_data.initial_solution.name
        subfolder = tc_name + '/'

        # Create output_folder if it doesn't exist yet
        if not os.path.exists(output_folder):
            os.makedirs(output_folder, exist_ok=True)

        # Create subfolder if it doesn't exist yet
        if not os.path.exists(output_folder + subfolder):
            os.makedirs(output_folder + subfolder, exist_ok=True)

        # Write windows
        write_windows(output_folder + subfolder + "{}_{}.txt".format(tc_name, 'windows'), output_data.final_solution.switches)
        render_bar_graph(output_folder + subfolder + "{}_{}.png".format(tc_name, 'INITIAL_deadline_and_wcd_graph'), output_data.initial_solution.streams, output_data.initial_wcds)
        render_bar_graph(output_folder + subfolder + "{}_{}.png".format(tc_name, 'FINAL_deadline_and_wcd_graph'),
                         output_data.initial_solution.streams, output_data.final_wcds)
