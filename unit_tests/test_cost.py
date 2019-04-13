from unittest import TestCase

import data_structures
from data_structures.Node import Node, Switch
from data_structures.TestCase import TestCase as TC

import cost
import numpy as np


class TestCost(TestCase):
    '''
    def test_complex(self):
        switches = {}

        s1 = Switch('SW1')
        s1.add_outputport_to('ES2')
        s1.associate_stream_to_queue('tt1', 5, 0, 'ES2')
        s1.associate_stream_to_queue('tt2', 5, 1, 'ES2')
        s1.associate_stream_to_queue('tt3', 5, 2, 'ES2')
        s1.associate_stream_to_queue('tt4', 5, 3, 'ES2')
        s1.associate_stream_to_queue('tt5', 5, 4, 'ES2')
        s1.associate_stream_to_queue('tt6', 5, 5, 'ES2')
        s1.associate_stream_to_queue('tt7', 5, 6, 'ES2')
        s1.M_row_offset = 0

        M = np.array([
            [10, 10, 50],
            [30, 10, 85],
            [200, 50, 333],
            [0, 10, 65],
            [350, 55, 800],
            [1000, 300, 1700],
            [5555, 222, 8000],
        ])

        switches['SW1'] = s1

        s = [TC(switches, None, None), M]

        self.assertEqual(cost.matrix_lcm(M), 588744000)
        self.assertEqual(cost.cost(s), 20)
    '''

    def test_different_period_overlap_later(self):
        switches = {}

        s1 = Switch('SW1')
        s1.add_outputport_to('ES2')
        s1.associate_stream_to_queue('tt1', 5, 0, 'ES2')
        s1.associate_stream_to_queue('tt2', 5, 1, 'ES2')
        s1.M_row_offset = 0

        M = np.array([
            [0, 10, 50],
            [10, 10, 65]
        ])

        switches['SW1'] = s1

        s = [TC(switches, None, None), M]

        self.assertEqual(cost.cost(s), 130 + 100 - 20)
        self.assertEqual(cost.matrix_lcm(M), 650)

    def test_multi_hop(self):
        switches = {}

        s1 = Switch('SW1')
        s2 = Switch('SW2')
        s1.add_outputport_to('SW2')
        s2.add_outputport_to('ES2')

        s1.associate_stream_to_queue('tt1', 5, 0, 'ES2')
        s1.associate_stream_to_queue('tt2', 5, 1, 'ES2')
        s2.associate_stream_to_queue('tt1', 5, 0, 'ES2')
        s2.associate_stream_to_queue('tt2', 5, 1, 'ES2')

        s1.M_row_offset = 0
        s2.M_row_offset = s1.total_number_of_queues

        M = np.array([
            [0, 10, 100],
            [10, 10, 100],
            [0, 10, 100],
            [10, 50, 100]
        ])

        switches['SW1'] = s1
        switches['SW2'] = s2

        s = [TC(switches, None, None), M]

        self.assertEqual(cost.cost(s), 80)
        self.assertEqual(cost.matrix_lcm(M), 100)

    def test_different_period_overlap(self):
        switches = {}

        s1 = Switch('SW1')
        s1.add_outputport_to('ES2')
        s1.associate_stream_to_queue('tt1', 5, 0, 'ES2')
        s1.associate_stream_to_queue('tt2', 5, 1, 'ES2')
        s1.M_row_offset = 0

        M = np.array([
            [0, 10, 50],
            [0, 10, 65]
        ])

        switches['SW1'] = s1

        s = [TC(switches, None, None), M]

        self.assertEqual(cost.cost(s), 130 + 100 - 20)
        self.assertEqual(cost.matrix_lcm(M), 650)

    def test_different_period_no_overlap(self):
        switches = {}

        s1 = Switch('SW1')
        s1.add_outputport_to('ES2')
        s1.associate_stream_to_queue('tt1', 5, 0, 'ES2')
        s1.associate_stream_to_queue('tt2', 5, 1, 'ES2')
        s1.M_row_offset = 0

        M = np.array([
            [0, 10, 100],
            [10, 10, 200]
        ])

        switches['SW1'] = s1

        s = [TC(switches, None, None), M]

        self.assertEqual(cost.cost(s), 30)
        self.assertEqual(cost.matrix_lcm(M), 200)

    def test_same_period(self):
        switches = {}

        s1 = Switch('SW1')
        s1.add_outputport_to('ES2')
        s1.associate_stream_to_queue('tt1', 5, 0, 'ES2')
        s1.associate_stream_to_queue('tt2', 5, 1, 'ES2')
        s1.M_row_offset = 0

        M = np.array([
            [0,10,100],
            [10,10,100]
        ])

        switches['SW1'] = s1

        s = [TC(switches, None, None), M]

        self.assertEqual(cost.cost(s), 20)
        self.assertEqual(cost.matrix_lcm(M), 100)

    def test_same_period_overlap(self):
        switches = {}

        s1 = Switch('SW1')
        s1.add_outputport_to('ES2')
        s1.associate_stream_to_queue('tt1', 5, 0, 'ES2')
        s1.associate_stream_to_queue('tt2', 5, 1, 'ES2')
        s1.M_row_offset = 0

        M = np.array([
            [0, 20, 100],
            [10, 10, 100]
        ])

        switches['SW1'] = s1

        s = [TC(switches, None, None), M]

        self.assertEqual(cost.cost(s), 20)
        self.assertEqual(cost.matrix_lcm(M), 100)

    def test_same_period_full(self):
        switches = {}

        s1 = Switch('SW1')
        s1.add_outputport_to('ES2')
        s1.associate_stream_to_queue('tt1', 5, 0, 'ES2')
        s1.associate_stream_to_queue('tt2', 5, 1, 'ES2')
        s1.M_row_offset = 0

        M = np.array([
            [0, 100, 100],
            [0, 100, 100]
        ])

        switches['SW1'] = s1

        s = [TC(switches, None, None), M]

        self.assertEqual(cost.cost(s), 100)
        self.assertEqual(cost.matrix_lcm(M), 100)

    def test_same_period_empty_but_period(self):
        switches = {}

        s1 = Switch('SW1')
        s1.add_outputport_to('ES2')
        s1.associate_stream_to_queue('tt1', 5, 0, 'ES2')
        s1.associate_stream_to_queue('tt2', 5, 1, 'ES2')
        s1.M_row_offset = 0

        M = np.array([
            [0, 0, 100],
            [0, 0, 100]
        ])

        switches['SW1'] = s1

        s = [TC(switches, None, None), M]

        self.assertEqual(cost.cost(s), 0)
        self.assertEqual(cost.matrix_lcm(M), 100)

    def test_empty_windows(self):
        switches = {}

        s1 = Switch('SW1')
        s1.add_outputport_to('ES2')
        s1.associate_stream_to_queue('tt1', 5, 0, 'ES2')
        s1.associate_stream_to_queue('tt2', 5, 1, 'ES2')
        s1.M_row_offset = 0

        M = np.array([
            [0, 0, 0],
            [0, 0, 0]
        ])

        switches['SW1'] = s1

        s = [TC(switches, None, None), M]

        with self.assertRaises(ValueError) as e:
            cost.cost(s)


    def test_no_windows(self):
        switches = {}

        s1 = Switch('SW1')
        s1.add_outputport_to('ES2')
        s1.M_row_offset = 0

        M = np.empty([0,3],dtype=int)

        switches['SW1'] = s1

        s = [TC(switches, None, None), M]

        self.assertEqual(cost.cost(s), 0)
