from unittest import TestCase

from data_structures.Node import Node, Switch
from data_structures.Stream import Stream
from data_structures.TestCase import TestCase as TC

from optimizers.iterative_optimizer import IterativeOptimizer, dq_optimize_ports_for_stream
from solution_check import SolutionChecker
from utility import config_parser


class TestIterativeOptimizer(TestCase):
    def test_dq_optimizer_simple(self):
        wcdtool_path, wcdtool_testcase_subpath = config_parser.parse_config("config.ini")
        solution_checker = SolutionChecker(wcdtool_path, wcdtool_testcase_subpath)

        n1 = Node('ES1')
        n2 = Node('SW1')
        n3 = Node('ES2')
        stream1 = Stream('tt1', 1500, 100, 100, 0, [n1,n2,n3])
        streams = {'tt1' : stream1}

        sw1 = Switch('SW1')
        sw1.associate_stream_to_queue(stream1.uid, stream1.sending_time, stream1.period, stream1.priority, 'ES2')
        p = sw1.output_ports['ES2']
        p.set_window(stream1.priority, 0, 24, 100)
        switches = {'SW1' : sw1}

        solution = TC(switches, streams, 'TC1')

        is_valid, is_feasible, exceeding_percentages, wcds = solution_checker.check_solution(solution, 20)
        optimized_solution = dq_optimize_ports_for_stream(solution, stream1, solution_checker)

        is_valid, is_feasible, exceeding_percentages, wcds = solution_checker.check_solution(optimized_solution, 20)
        self.assertEqual(True, stream1.deadline > float(wcds[stream1.uid]))
        self.assertEqual(True, stream1.deadline < float(wcds[stream1.uid]) + 1)

    def test_dq_optimizer_simple_multihop(self):
        wcdtool_path, wcdtool_testcase_subpath = config_parser.parse_config("config.ini")
        solution_checker = SolutionChecker(wcdtool_path, wcdtool_testcase_subpath)

        n1 = Node('ES1')
        n2 = Node('SW1')
        n3 = Node('SW2')
        n4 = Node('ES2')
        stream1 = Stream('tt1', 1500, 200, 100, 0, [n1,n2,n3, n4])
        streams = {'tt1' : stream1}

        sw1 = Switch('SW1')
        sw1.associate_stream_to_queue(stream1.uid, stream1.sending_time, stream1.period, stream1.priority, 'SW2')
        p = sw1.output_ports['SW2']
        p.set_window(stream1.priority, 0, 24, 100)

        sw2 = Switch('SW2')
        sw2.associate_stream_to_queue(stream1.uid, stream1.sending_time, stream1.period, stream1.priority, 'ES2')
        p = sw2.output_ports['ES2']
        p.set_window(stream1.priority, 0, 24, 100)
        switches = {'SW1' : sw1, 'SW2' : sw2}

        solution = TC(switches, streams, 'TC2')

        is_valid, is_feasible, exceeding_percentages, wcds = solution_checker.check_solution(solution, 20)
        optimized_solution = dq_optimize_ports_for_stream(solution, stream1, solution_checker)

        is_valid, is_feasible, exceeding_percentages, wcds = solution_checker.check_solution(optimized_solution, 20)
        self.assertEqual(True, stream1.deadline > float(wcds[stream1.uid]))
        self.assertEqual(True, stream1.deadline < float(wcds[stream1.uid]) + 2)


