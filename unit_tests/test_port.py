from unittest import TestCase

from data_structures.Node import Port

class TestPort(TestCase):
    def test_name(self):
        name = 'port1'
        p = Port(name)

        self.assertEqual(p.name, name)

    def test_data_structure_assignment_different_q(self):
        p = Port('port1')

        s1_uid = 'tt1'
        s1_length = 20
        s1_period = 100

        s2_uid = 'tt2'
        s2_length = 50
        s2_period = 200

        self.assertEqual(p.associate_stream_to_queue(s1_uid, s1_length,s1_period, 0), True)
        self.assertEqual(p.associate_stream_to_queue(s2_uid,s2_length,s2_period, 1), True)
        self.assertIn(0, p.queues_with_window_percentage)
        self.assertIn(1, p.queues_with_window_percentage)
        self.assertIn(0, p.queues_with_streams)
        self.assertIn(1, p.queues_with_streams)

        self.assertEqual(p.queues_with_window_percentage[0],0.2)
        self.assertEqual(p.queues_with_window_percentage[1], 0.25)
        self.assertEqual(p.queues_with_streams[0], ['tt1'])
        self.assertEqual(p.queues_with_streams[1], ['tt2'])

    def test_data_structure_assignment_same_q(self):
        p = Port('port1')

        s1_uid = 'tt1'
        s1_length = 20
        s1_period = 100

        s2_uid = 'tt2'
        s2_length = 50
        s2_period = 200

        self.assertEqual(p.associate_stream_to_queue(s1_uid, s1_length,s1_period, 0), True)
        self.assertEqual(p.associate_stream_to_queue(s2_uid,s2_length,s2_period, 0), False)
        self.assertIn(0, p.queues_with_window_percentage)
        self.assertIn(0, p.queues_with_streams)

        self.assertEqual(p.queues_with_window_percentage[0],0.45)

        self.assertEqual(p.queues_with_streams[0], ['tt1', 'tt2'])

    def test_sorted_queuenrs(self):
        p = Port('port1')

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

        self.assertIn(5, p.queues_with_window_percentage)
        self.assertIn(2, p.queues_with_window_percentage)
        self.assertIn(7, p.queues_with_window_percentage)
        self.assertIn(4, p.queues_with_window_percentage)

        self.assertIn(5, p.queues_with_streams)
        self.assertIn(2, p.queues_with_streams)
        self.assertIn(7, p.queues_with_streams)
        self.assertIn(4, p.queues_with_streams)

        self.assertEqual(p.get_sorted_queuenrs(), [2, 4, 5, 7])

    def test_minimum_window_percentage(self):
        p = Port('port1')

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

        self.assertEqual(p.queues_with_window_percentage[0], 0.1)
        self.assertEqual(p.queues_with_window_percentage[1], 0.25)
        self.assertEqual(p.queues_with_window_percentage[2], 0.01)

        self.assertEqual(p.get_minimum_window_percentage(), 0.01)