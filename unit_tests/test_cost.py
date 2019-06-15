from unittest import TestCase

import data_structures.TestCase
from data_structures.Node import Switch
from data_structures.OutputPort import OutputPort
from data_structures.TestCase import TestCase as TC

import cost_check
import numpy as np


class TestCost(TestCase):
    def test_multi_hop(self):
        p = OutputPort('SW2')
        p2 = OutputPort('ES2')

        M = np.array([
            [0, 10, 100],
            [10, 20, 100]
        ])
        
        M2 = np.array([
            [0, 10, 100],
            [10, 50, 100]
            ]
        )

        p._M_Windows = M
        p2._M_Windows = M2

        s1 = Switch('SW1')
        s2 = Switch('S2')

        s1.output_ports = {'SW2' : p}
        s2.output_ports = {'ES2' : p2}

        tc = TC({'SW1' : s1, 'SW2' : s2}, {}, '')

        cc = cost_check.CostChecker()
        self.assertEqual(cc.cost(tc), 20/100 + 50/100)

    def test_port_costs(self):
        p = OutputPort('SW2')
        p2 = OutputPort('ES2')

        M = np.array([
            [0, 10, 100],
            [10, 20, 100]
        ])

        M2 = np.array([
            [0, 10, 100],
            [10, 50, 100]
        ]
        )

        p._M_Windows = M
        p2._M_Windows = M2

        s1 = Switch('SW1')
        s2 = Switch('SW2')

        s1.output_ports = {'SW2': p}
        s2.output_ports = {'ES2': p2}

        tc = TC({'SW1': s1, 'SW2': s2}, {}, '')

        cc = cost_check.CostChecker()
        self.assertEqual(cc.cost(tc), 20 / 100 + 50 / 100)

        d = cc.port_costs(tc)
        self.assertEqual(True, d['SW1,SW2'] == 20/100)
        self.assertEqual(True, d['SW2,ES2'] == 50/100)

    def test_port_costs(self):
        p = OutputPort('SW2')


        M = np.array([
            [0, 20, 80],
            [20, 50, 90],
            [50, 70, 100]
        ])

        tl = 0
        hp = 3600
        for r in M:
            tl = tl + hp/r[2]*(r[1]-r[0])
        tp = tl/hp

        p._M_Windows = M


        s1 = Switch('SW1')


        s1.output_ports = {'ES2': p}

        tc = TC({'SW1': s1}, {}, '')

        cc = cost_check.CostChecker()
        cp = cc.cost(tc)
        self.assertEqual(True, cp < tp)
