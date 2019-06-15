import copy
import datetime
import math
import os
import pickle
import time

from graphviz import render

from cost_check import CostChecker
from data_structures import Stream
from data_structures.TestCase import TestCase
from optimizers.initialSolution_generator import create_initial_solution
from solution_check import SolutionChecker
from utility.output_serializer import OutputData, write_windows, write_statistics, append_to_collections, \
    render_bar_graph, render_network_topology, pickle_data, render_windows
from utility.window_visualizer import WindowVisualizer

DEBUG = True


def debug_print(s, end='\n'):
    if DEBUG:
        print(s, end=end)


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


def reset_ports_bounds_on_stream_route(solution: TestCase, stream: Stream):
    i = 1
    for node in stream.route[1:-1]:
        # Get switch object
        assert (node.type == 'SW')
        switch = solution.switches[node.uid]

        # Determine Port
        port_uid = stream.route[i + 1].uid
        port = switch.output_ports[port_uid]

        # RESET
        port.dq_reset()

        i = i + 1


def optimize_ports_for_stream(solution: TestCase, stream: Stream, solution_checker: SolutionChecker):
    lower = True
    reset_ports_bounds_on_stream_route(solution, stream)

    while True:
        print('.', end='', flush=True)
        # Iterate through ports on route (ES sliced out), decrease period
        i = 1
        end = True
        for node in stream.route[1:-1]:
            # Get switch object
            assert (node.type == 'SW')
            switch = solution.switches[node.uid]

            # Determine Port
            port_uid = stream.route[i + 1].uid
            port = switch.output_ports[port_uid]

            if port.dq_modify_period(lower):
                # If at least one port can still be modifed -> do not end
                end = False

            i = i + 1

        is_valid, _, exceeding_percentages, _, _ = solution_checker.check_solution(solution)
        assert is_valid

        lower = False
        for tuple in exceeding_percentages:
            if stream.uid == tuple[1]:
                lower = True

        if end:
            for tuple in exceeding_percentages:
                if stream.uid == tuple[1]:
                    print('\n!!! Stream ' + stream.uid + ' cannot be made feasible !!!')
            break

    return solution


def generate_iteration_data_tuple_and_output(exceeding_percentages, final_wcds, cost_checker, solution,
                                             infinite_streams):
    sum_ep = 0
    for t in exceeding_percentages:
        sum_ep = sum_ep + t[0]
    sum_wcd = 0
    for x in final_wcds.values():
        if not x.endswith('INF'):
            sum_wcd = sum_wcd + float(x)
    cost = cost_checker.cost(solution)
    solved_stream_number = len(solution.streams) - len(exceeding_percentages) - len(infinite_streams)
    print('\n' + str(len(infinite_streams)) + ' infinite streams')
    print(str(len(exceeding_percentages)) + ' streams to be solved')
    print(str(solved_stream_number) + ' solved streams')
    print('Exceeding percentage sum: ' + str(sum_ep))
    print('Worst-case delay sum: ' + str(sum_wcd))
    print('Cost: ' + str(cost))

    return (cost, sum_wcd, sum_ep, solved_stream_number)


def divideconquer_optimization(solution: TestCase, options: dict, cost_checker: CostChecker,
                               solution_checker: SolutionChecker):
    """

    Args:
        solution (TestCase): Initial Solution as TestCase object
        options (dict): directory of options specified by user
        cost_checker (CostChecker): CostChecker object
        solution_checker (SolutionChecker): SolutionChecker object

    Returns:
        Final Solution as TestCase object or None, if solution not solvable
    """
    initial_solution = copy.deepcopy(solution)
    print(
        '\n#########################\nTest Case: {} | Divide & Conquer Optimization\n#########################\n'.format(
            solution.name))

    print('Amount of streams: ' + str(len(initial_solution.streams)))
    t_start = time.clock()
    is_valid, is_feasible, exceeding_percentages, initial_wcds, infinite_streams = solution_checker.check_solution(
        solution)
    if not is_valid:
        print('\n----------------- Testcase invalid -----------------')
        return None

    if len(infinite_streams) > 0:
        print('\n----------------- Unsolvable streams found -----------------')
        for uid in infinite_streams:
            print(uid + ' ', end='')
        print('')

    initial_cost = cost_checker.cost(solution)
    initial_port_costs = cost_checker.port_costs(solution)
    final_wcds = initial_wcds
    iteration_data = []
    initial_nr_of_stream_tobesolved = len(exceeding_percentages)
    final_step_amount = 0
    sum = 0
    for tuple in exceeding_percentages:
        sum = sum + tuple[0]
    if len(exceeding_percentages) > 0:
        initial_ep_mean = sum / len(exceeding_percentages)
    else:
        initial_ep_mean = 0

    ##### 1. Algorithm #####
    if not is_feasible:
        # OUTPUT

        iteration_data.append(
            generate_iteration_data_tuple_and_output(exceeding_percentages, final_wcds, cost_checker, solution,
                                                     infinite_streams))
        i = 0
        # ALGORITHM
        for tuple in exceeding_percentages:
            print('Checking tuple ' + str(i))
            i = i + 1
            # STATISTICS
            # Check if stream still exceeding (Might have been fixed by fixing other stream)
            for t in exceeding_percentages:
                if t[1] == tuple[1]:
                    stream_uid = tuple[1]
                    print('Fixing ' + stream_uid + ': ', end='')

                    # Optimize Stream
                    stream = solution.streams[stream_uid]
                    solution = optimize_ports_for_stream(solution, stream, solution_checker)

                    # Check new solution
                    is_valid, is_feasible, exceeding_percentages, final_wcds, infinite_streams = solution_checker.check_solution(
                        solution)

                    # OUTPUT
                    iteration_data.append(
                        generate_iteration_data_tuple_and_output(exceeding_percentages, final_wcds, cost_checker,
                                                                 solution, infinite_streams))
                    break

            if is_feasible:
                break

    cost = cost_checker.cost(solution)
    final_port_costs = cost_checker.port_costs(solution)
    runtime = time.clock() - t_start
    final_step_amount = len(iteration_data)
    is_valid, is_feasible, exceeding_percentages, final_wcds, infinite_streams = solution_checker.check_solution(
        solution)
    print('\n----------------- Solved with cost: {} Infeasible streams: {} -----------------'.format(cost, len(
        infinite_streams + exceeding_percentages)))

    output_data = OutputData(initial_solution, solution, initial_wcds, final_wcds, runtime, initial_cost, cost,
                             initial_port_costs, final_port_costs, iteration_data, infinite_streams,
                             exceeding_percentages, initial_nr_of_stream_tobesolved, final_step_amount, initial_ep_mean)
    return output_data


class IterativeOptimizer(object):
    """Finds a solution to the testcase by constructivly generating a good initial solution. Then proceeds to make
    all stream feasible (catch their deadline), by reducing the periods of the ports on their route """

    def run(self, testcase: TestCase, wcdtool_path: str, wcdtool_testcase_subpath: str, output_folder: str,
            options: dict):
        """

        Args:
            testcase (TestCase):  Testcase
            wcdtool_path (str): Path to WCDTool executable
            wcdtool_testcase_subpath (str): Relative path from WCDTool executable to testcase folder
            output_folder (str): Path to output folder
            options (dict): directory of options specified by user

        Returns:
            TestCase object for final solution or None, if no solution found
        """

        # Initial Solution
        initial_solution = create_initial_solution(testcase)

        # Optimization
        output_data = divideconquer_optimization(initial_solution, options, CostChecker(),
                                                 SolutionChecker(wcdtool_path, wcdtool_testcase_subpath, options['wcdanalysis_timeout']))

        # Output Results
        if output_data != None:
            self.generate_output(output_data, output_folder, 'IterativeOptimization', options)
            return copy.deepcopy(output_data.final_solution)
        else:
            return None

    def generate_output(self, output_data: OutputData, output_folder: str, optimization_type_string: str,
                        options: dict):
        """

        Args:
            output_data (OutputData): all the information needed to generate the output files
            output_folder (str): Path to output folder
            optimization_type_string (str): A string representing the optimization type
            options (dict): directory of options specified by user
        """
        tc_name = output_data.initial_solution.name
        subfolder = tc_name + '_' + datetime.datetime.now().strftime(
            '%Y-%m-%d_%H-%M') + '_' + optimization_type_string + '/'

        # Create output_folder if it doesn't exist yet
        if not os.path.exists(output_folder):
            os.makedirs(output_folder, exist_ok=True)

        # Create subfolder if it doesn't exist yet
        if not os.path.exists(output_folder + subfolder):
            os.makedirs(output_folder + subfolder, exist_ok=True)

        # Generate output
        write_windows(output_folder + subfolder + "{}.txt".format('windows_initial'),
                      output_data.initial_solution.switches)
        write_windows(output_folder + subfolder + "{}.txt".format('windows_final'),
                      output_data.final_solution.switches)
        write_statistics(output_folder + subfolder + "{}.txt".format('statistics'),
                         output_data)

        if options['aggregate'] is True:
            append_to_collections(output_folder, output_data)

        if options['visualize'] is True:
            render_bar_graph(output_folder + subfolder + "{}.png".format('INITIAL_deadline_and_wcd_graph'),
                             output_data.initial_solution.streams, output_data.initial_wcds, False)
            render_bar_graph(output_folder + subfolder + "{}.png".format('FINAL_deadline_and_wcd_graph'),
                             output_data.initial_solution.streams, output_data.final_wcds, True)
            render_network_topology(output_folder + subfolder + "{}".format('network_graph'),
                                    output_data.final_solution.streams)
            render_windows(output_folder + subfolder + "{}.svg".format('windows_initial'), output_data.initial_solution)
            render_windows(output_folder + subfolder + "{}.svg".format('windows_final'), output_data.final_solution)

        if options['pickle'] is True:
            pickle_data(output_folder + subfolder + "{}.pickle".format('output_data'), output_data)

        #
        print('Output Files written to: ' + output_folder + subfolder)
