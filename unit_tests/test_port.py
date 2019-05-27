from unittest import TestCase

import data_structures
from data_structures.OutputPort import OutputPort

import numpy as np

class TestPort(TestCase):
    def test_name(self):
        name = 'port1'
        p = OutputPort(name)

        self.assertEqual(p.name, name)

    def test_data_structure_assignment_different_q(self):
        p = OutputPort('port1')

        s1_uid = 'tt1'
        s1_length = 20
        s1_period = 100

        s2_uid = 'tt2'
        s2_length = 50
        s2_period = 200

        self.assertEqual(p.associate_stream_to_queue(s1_uid, s1_length,s1_period, 0), True)
        self.assertEqual(p.associate_stream_to_queue(s2_uid,s2_length,s2_period, 1), True)
        self.assertIn(0, p.queues)
        self.assertIn(1, p.queues)
        self.assertIn(0, p.queues)
        self.assertIn(1, p.queues)

        self.assertEqual(p.queues[0].window_percentage,0.2)
        self.assertEqual(p.queues[1].window_percentage, 0.25)
        self.assertEqual(p.queues[0].stream_uids, ['tt1'])
        self.assertEqual(p.queues[1].stream_uids, ['tt2'])

    def test_data_structure_assignment_same_q(self):
        p = OutputPort('port1')

        s1_uid = 'tt1'
        s1_length = 20
        s1_period = 100

        s2_uid = 'tt2'
        s2_length = 50
        s2_period = 200

        self.assertEqual(p.associate_stream_to_queue(s1_uid, s1_length,s1_period, 0), True)
        self.assertEqual(p.associate_stream_to_queue(s2_uid,s2_length,s2_period, 0), False)
        self.assertIn(0, p.queues)

        self.assertEqual(p.queues[0].window_percentage,0.45)

        self.assertEqual(p.queues[0].stream_uids, ['tt1', 'tt2'])

    def test_sorted_queuenrs(self):
        p = OutputPort('port1')

        s1_uid = 'tt1'
        s1_length = 20
        s1_period = 100

        s2_uid = 'tt2'
        s2_length = 50
        s2_period = 200

        s3_uid = 'tt3'
        s3_length = 50
        s3_period = 200

        s4_uid = 'tt4'
        s4_length = 50
        s4_period = 200

        self.assertEqual(p.associate_stream_to_queue(s1_uid, s1_length,s1_period, 5), True)
        self.assertEqual(p.associate_stream_to_queue(s2_uid,s2_length,s2_period, 2), True)
        self.assertEqual(p.associate_stream_to_queue(s3_uid, s3_length, s3_period, 7), True)
        self.assertEqual(p.associate_stream_to_queue(s4_uid, s4_length, s4_period, 4), True)

        self.assertIn(5, p.queues)
        self.assertIn(2, p.queues)
        self.assertIn(7, p.queues)
        self.assertIn(4, p.queues)

        self.assertEqual(p.get_sorted_queuenrs(), [2, 4, 5, 7])

    def test_minimum_window_percentage(self):
        p = OutputPort('port1')

        s1_uid = 'tt1'
        s1_length = 10
        s1_period = 100

        s2_uid = 'tt2'
        s2_length = 50
        s2_period = 200

        s3_uid = 'tt3'
        s3_length = 10
        s3_period = 1000

        self.assertEqual(p.associate_stream_to_queue(s1_uid, s1_length, s1_period, 0), True)
        self.assertEqual(p.associate_stream_to_queue(s2_uid, s2_length, s2_period, 1), True)
        self.assertEqual(p.associate_stream_to_queue(s3_uid, s3_length, s3_period, 2), True)

        self.assertEqual(p.queues[0].window_percentage, 0.1)
        self.assertEqual(p.queues[1].window_percentage, 0.25)
        self.assertEqual(p.queues[2].window_percentage, 0.01)

        self.assertEqual(p.get_minimum_window_percentage(), 0.01)

    def test_set_window_and_period_multiplication(self):
        p = OutputPort('port1')

        s1_uid = 'tt1'
        s1_length = 10
        s1_period = 100

        s2_uid = 'tt2'
        s2_length = 50
        s2_period = 200

        s3_uid = 'tt3'
        s3_length = 10
        s3_period = 1000

        self.assertEqual(p.associate_stream_to_queue(s1_uid, s1_length, s1_period, 0), True)
        self.assertEqual(p.associate_stream_to_queue(s2_uid, s2_length, s2_period, 1), True)
        self.assertEqual(p.associate_stream_to_queue(s3_uid, s3_length, s3_period, 2), True)

        self.assertEqual(p._M_Windows.shape[0], 3)

        p.set_window(1, 10, 50, 200)
        p.set_window(0, 0, 10, 100)
        p.set_window(2, 60, 10, 1000)

        M = np.array([
            [0, 10, 100],
            [10, 60, 200],
            [60, 70, 1000]
        ])

        self.assertEqual(np.array_equal(p._M_Windows, M), True)

        M_expected = np.array([
            [0, 10, 300],
            [10, 60, 600],
            [60, 70, 3000]
        ])

        p.multipy_period(3)

        self.assertEqual(np.array_equal(p._M_Windows, M_expected), True)

    def test_occupation_percentage_same_period(self):
        p = OutputPort('port1')

        s1_uid = 'tt1'
        s1_length = 10
        s1_period = 100

        s2_uid = 'tt2'
        s2_length = 50
        s2_period = 100

        s3_uid = 'tt3'
        s3_length = 10
        s3_period = 100

        # Test Queue Association
        self.assertEqual(p.associate_stream_to_queue(s1_uid, s1_length, s1_period, 0), True)
        self.assertEqual(p.associate_stream_to_queue(s2_uid, s2_length, s2_period, 1), True)
        self.assertEqual(p.associate_stream_to_queue(s3_uid, s3_length, s3_period, 2), True)

        # Test initial window creation
        self.assertEqual(p._M_Windows.shape[0], 3)

        # Test window assignment
        p.set_window(0, 0 , 10, 100)
        p.set_window(1, 10, 50, 100)
        p.set_window(2, 60, 10, 100)

        M = np.array([
            [0, 10, 100],
            [10, 60, 100],
            [60, 70, 100]
        ])

        self.assertEqual(np.array_equal(p._M_Windows, M), True)

        # Test occupation percentage
        self.assertEqual(p.get_occupation_percentage(), 7/10)

    def test_different_period_overlap_later(self):
        switches = {}

        p = OutputPort('port1')
        p.associate_stream_to_queue('tt1', 0, 50, 0)
        p.associate_stream_to_queue('tt2', 0, 65, 1)

        M = np.array([
            [0, 10, 50],
            [10, 10, 65]
        ])

        p.set_window(0, 0, 10, 50)
        p.set_window(1, 10, 10, 65)

        self.assertEqual(p.get_occupation_percentage(), 210/650)

    def test_different_period_overlap(self):
        p = OutputPort('SW1')

        M = np.array([
            [0, 10, 50],
            [0, 10, 65]
        ])

        p._M_Windows = M

        self.assertEqual(p.get_occupation_percentage(), 210/650)

    def test_different_period_no_overlap(self):
        p = OutputPort('SW1')

        M = np.array([
            [0, 10, 100],
            [10, 20, 200]
        ])

        p._M_Windows = M

        self.assertEqual(p.get_occupation_percentage(), 30 / 200)


    def test_same_period(self):
        p = OutputPort('SW1')

        M = np.array([
            [0, 10, 100],
            [10, 20, 100]
        ])

        p._M_Windows = M

        self.assertEqual(p.get_occupation_percentage(), 20 / 100)


    def test_same_period_overlap(self):
        p = OutputPort('SW1')

        M = np.array([
            [0, 20, 100],
            [10, 20, 100]
        ])

        p._M_Windows = M

        self.assertEqual(p.get_occupation_percentage(), 20 / 100)

    def test_same_period_full(self):
        p = OutputPort('SW1')

        M = np.array([
            [0, 100, 100],
            [0, 100, 100]
        ])

        p._M_Windows = M

        self.assertEqual(p.get_occupation_percentage(), 100 / 100)

    def test_same_period_empty_but_period(self):
        p = OutputPort('SW1')

        M = np.array([
            [0, 0, 100],
            [0, 0, 100]
        ])

        p._M_Windows = M

        self.assertEqual(p.get_occupation_percentage(), 0 / 100)

    def test_empty_windows(self):
        p = OutputPort('SW1')

        M = np.array([
            [0, 0, 0],
            [0, 0, 0]
        ])

        p._M_Windows = M

        with self.assertRaises(ValueError) as e:
            p.get_occupation_percentage()

    def test_dq_period_lower(self):
        p = OutputPort('SW1')

        p._free_period = 100

        p.dq_modify_period(True)
        self.assertEqual(p._free_period, 50)
        p.dq_modify_period(True)
        self.assertEqual(p._free_period, 25)
        p.dq_modify_period(True)
        self.assertEqual(p._free_period, 12)
        p.dq_modify_period(True)
        self.assertEqual(p._free_period, 6)
        p.dq_modify_period(True)
        self.assertEqual(p._free_period, 3)
        p.dq_modify_period(True)
        self.assertEqual(p._free_period, 1)
        p.dq_modify_period(True)
        self.assertEqual(p._free_period, 0)
        p.dq_modify_period(True)
        self.assertEqual(p._free_period, 0)
        self.assertEqual(p.dq_modify_period(True), False)

    def test_dq_period_normal(self):
        p = OutputPort('SW1')

        p._free_period = 100

        p.dq_modify_period(True)
        self.assertEqual(p._free_period, 50)
        p.dq_modify_period(False)
        self.assertEqual(p._free_period, 75)
        p.dq_modify_period(True)
        self.assertEqual(p._free_period, 62)
        p.dq_modify_period(True)
        self.assertEqual(p._free_period, 56)
        p.dq_modify_period(False)
        self.assertEqual(p._free_period, 59)
        self.assertEqual(p.dq_modify_period(True), True)

    def test_dq_period_unevenstart(self):
        p = OutputPort('SW1')

        p._free_period = 1337

        p.dq_modify_period(True)
        self.assertEqual(p._free_period, 668)

    def test_dq_period_zero(self):
        p = OutputPort('SW1')

        p._free_period = 0

        ret = p.dq_modify_period(True)
        self.assertEqual(p._free_period, 0)
        self.assertEqual(ret, False)

        ret = p.dq_modify_period(False)
        self.assertEqual(p._free_period, 0)
        self.assertEqual(ret, False)

    def test_dq_period_higheratstart(self):
        p = OutputPort('SW1')
        s1_uid = 'tt1'
        s1_length = 10
        s1_period = 100

        s2_uid = 'tt2'
        s2_length = 50
        s2_period = 100

        s3_uid = 'tt3'
        s3_length = 10
        s3_period = 100

        # Test Queue Association
        self.assertEqual(p.associate_stream_to_queue(s1_uid, s1_length, s1_period, 0), True)
        self.assertEqual(p.associate_stream_to_queue(s2_uid, s2_length, s2_period, 1), True)
        self.assertEqual(p.associate_stream_to_queue(s3_uid, s3_length, s3_period, 2), True)

        # Test initial window creation
        self.assertEqual(p._M_Windows.shape[0], 3)

        # Test window assignment
        p.set_window(0, 0, 10, 100)
        p.set_window(1, 10, 50, 100)
        p.set_window(2, 60, 10, 100)

        ret = p.dq_modify_period(False)
        self.assertEqual(p._free_period, 30)
        self.assertEqual(ret, False)
