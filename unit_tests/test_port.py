from unittest import TestCase

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