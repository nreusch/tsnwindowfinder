import math

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


def get_worst_stream(s : TestCase, exceeding_percentages: dict):
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
    print('\n#########################\nTest Case: {}\n#########################\n'.format(solution.name))

    is_feasible, exceeding_percentages = solution_checker.check_solution(solution, 20)

    while not is_feasible:

        # 1. Get Worst Stream
        worst_stream = get_worst_stream(solution, exceeding_percentages)

        # 2. Optimize Worst Stream

        # Iterate through ports on route (ES sliced out), decrease period
        i = 1
        for node in worst_stream.route[1:-1]:
            print('.',end='',flush=True)
            # Get switch object
            assert (node.type == 'SW')
            switch = solution.switches[node.uid]

            # Determine Port
            port_uid = worst_stream.route[i + 1].uid
            port = switch.output_ports[port_uid]

            # Decrease Period
            port.multipy_period(p)

            # Check if solution/stream is feasible now. If yes break.
            is_feasible, exceeding_percentages = solution_checker.check_solution(solution, 20)
            if is_feasible:
                break
            elif not get_worst_stream(solution, exceeding_percentages) == worst_stream:
                break

            i += 1

    print('\n----------------- Solved with cost: {} -----------------'.format(cost_checker.cost_port(solution)))
    return solution


class IterativeOptimizer(object):
    """Finds a solution to the testcase by constructivly generating a good initial solution. Then proceeds to make
    all stream feasible (catch their deadline), by reducing the periods of the ports on their route """

    def run(self, testcase: TestCase, wcdtool_path: str, wcdtool_testcase_subpath: str, p: float):
        """

        Args:
            testcase (TestCase):  Testcase
            wcdtool_path (str): Path to WCDTool executable
            wcdtool_testcase_subpath (str): Relative path from WCDTool executable to testcase folder
            p (float): period adjustment percentage

        Returns:
            TestCase object for final solution
        """
        initial_solution = create_initial_solution(testcase)
        final_solution = iterative_optimization(initial_solution, p, CostChecker(),
                                                SolutionChecker(wcdtool_path, wcdtool_testcase_subpath))
        return final_solution
