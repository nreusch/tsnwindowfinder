from unittest import TestCase

from data_structures.Node import Node, Switch
from data_structures.Stream import Stream
from data_structures.TestCase import TestCase as TC

from optimizers.iterative_optimizer import IterativeOptimizer, optimize_ports_for_stream, create_initial_solution
from solution_check import SolutionChecker
from utility import config_parser


class TestIterativeOptimizer(TestCase):
    def test_dq_optimizer_simple(self):
        wcdtool_path, wcdtool_testcase_subpath = config_parser.parse_config("config.ini")
        solution_checker = SolutionChecker(wcdtool_path, wcdtool_testcase_subpath, 20)

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

        is_valid, is_feasible, exceeding_percentages, wcds, infinite_streams = solution_checker.check_solution(solution)
        optimized_solution = optimize_ports_for_stream(solution, stream1, solution_checker)

        is_valid, is_feasible, exceeding_percentages, wcds, infinite_streams = solution_checker.check_solution(optimized_solution)
        self.assertEqual(True, stream1.deadline > float(wcds[stream1.uid]))
        self.assertEqual(True, stream1.deadline < float(wcds[stream1.uid]) + 1)

    def test_dq_optimizer_simple_multihop(self):
        wcdtool_path, wcdtool_testcase_subpath = config_parser.parse_config("config.ini")
        solution_checker = SolutionChecker(wcdtool_path, wcdtool_testcase_subpath, 20)

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

        is_valid, is_feasible, exceeding_percentages, wcds, infinite_streams = solution_checker.check_solution(solution)
        optimized_solution = optimize_ports_for_stream(solution, stream1, solution_checker)

        is_valid, is_feasible, exceeding_percentages, wcds, infinite_streams = solution_checker.check_solution(optimized_solution)
        self.assertEqual(True, stream1.deadline > float(wcds[stream1.uid]))
        self.assertEqual(True, stream1.deadline < float(wcds[stream1.uid]) + 2)

    def test_dq_optimizer_simple_multi_streams_same_port(self):
        wcdtool_path, wcdtool_testcase_subpath = config_parser.parse_config("config.ini")
        solution_checker = SolutionChecker(wcdtool_path, wcdtool_testcase_subpath, 20)

        n1 = Node('ES1')
        n2 = Node('SW1')
        n3 = Node('SW2')
        n4 = Node('ES2')
        stream1 = Stream('tt1', 1500, 300, 100, 0, [n1,n2,n3, n4])
        stream2 = Stream('tt2', 1500, 100, 100, 3, [n1, n3, n4])
        streams = {'tt1' : stream1, 'tt2' : stream2}

        sw1 = Switch('SW1')
        sw1.associate_stream_to_queue(stream1.uid, stream1.sending_time, stream1.period, stream1.priority, 'SW2')
        p = sw1.output_ports['SW2']
        p.set_window(stream1.priority, 0, 24, 100)

        sw2 = Switch('SW2')
        sw2.associate_stream_to_queue(stream1.uid, stream1.sending_time, stream1.period, stream1.priority, 'ES2')
        sw2.associate_stream_to_queue(stream2.uid, stream2.sending_time, stream2.period, stream2.priority, 'ES2')
        p = sw2.output_ports['ES2']
        p.set_window(stream1.priority, 0, 24, 100)
        p.set_window(stream2.priority, 24, 24, 100)
        switches = {'SW1' : sw1, 'SW2' : sw2}

        solution = TC(switches, streams, 'TC3')

        is_valid, is_feasible, exceeding_percentages, wcds, infinite_streams = solution_checker.check_solution(solution)
        optimized_solution = optimize_ports_for_stream(solution, stream1, solution_checker)
        optimized_solution = optimize_ports_for_stream(solution, stream2, solution_checker)

        is_valid, is_feasible, exceeding_percentages, wcds, infinite_streams = solution_checker.check_solution(optimized_solution)
        self.assertEqual(True, is_feasible)

        self.assertEqual(True, optimized_solution.switches['SW2'].output_ports['ES2'].get_hyperperiod() == 49)

    def test_infinite_stream(self):
        wcdtool_path, wcdtool_testcase_subpath = config_parser.parse_config("config.ini")
        solution_checker = SolutionChecker(wcdtool_path, wcdtool_testcase_subpath, 20)

        n1 = Node('ES1')
        n2 = Node('SW1')
        n3 = Node('ES2')
        stream1 = Stream('tt1', 7500, 300, 100, 1, [n1,n2,n3])
        stream2 = Stream('tt2', 3000, 100, 100, 2, [n1, n2, n3])
        streams = {'tt1' : stream1, 'tt2' : stream2}

        sw1 = Switch('SW1')
        sw1.associate_stream_to_queue(stream1.uid, stream1.sending_time, stream1.period, stream1.priority, 'ES2')
        sw1.associate_stream_to_queue(stream2.uid, stream2.sending_time, stream2.period, stream2.priority, 'ES2')
        switches = {'SW1': sw1}

        tc = TC(switches, streams, 'TC4')
        initial_solution = create_initial_solution(tc)

        is_valid, is_feasible, exceeding_percentages, wcds, infinite_streams = solution_checker.check_solution(initial_solution)
        self.assertEqual(True, is_feasible)
        self.assertEqual(True, is_valid)
        self.assertEqual(True, stream2.uid in infinite_streams)

    def test_infinite_stream2(self):
        wcdtool_path, wcdtool_testcase_subpath = config_parser.parse_config("config.ini")
        solution_checker = SolutionChecker(wcdtool_path, wcdtool_testcase_subpath, 20)

        n1 = Node('ES1')
        n2 = Node('SW1')
        n3 = Node('ES2')
        stream1 = Stream('tt1', 7500, 300, 100, 1, [n1,n2,n3])
        stream3 = Stream('tt3', 3000, 300, 100, 1, [n1, n2, n3])
        stream2 = Stream('tt2', 3000, 100, 100, 2, [n1, n2, n3])
        streams = {'tt1' : stream1, 'tt2' : stream2, 'tt3' : stream3}

        sw1 = Switch('SW1')
        sw1.associate_stream_to_queue(stream1.uid, stream1.sending_time, stream1.period, stream1.priority, 'ES2')
        sw1.associate_stream_to_queue(stream3.uid, stream3.sending_time, stream3.period, stream3.priority, 'ES2')
        sw1.associate_stream_to_queue(stream2.uid, stream2.sending_time, stream2.period, stream2.priority, 'ES2')
        switches = {'SW1': sw1}

        tc = TC(switches, streams, 'TC5')
        initial_solution = create_initial_solution(tc)

        is_valid, is_feasible, exceeding_percentages, wcds, infinite_streams = solution_checker.check_solution(initial_solution)
        self.assertEqual(False, is_feasible)
        self.assertEqual(True, is_valid)
        self.assertEqual(True, stream2.uid in infinite_streams)
        self.assertEqual(True, stream1.uid not in infinite_streams and stream3.uid not in infinite_streams)




