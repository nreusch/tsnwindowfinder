import math
import os
import re
import subprocess
import time
from collections import defaultdict

import numpy as np

# TODO: !!Relative Path!!
from data_structures import TestCase

WCDTOOL_PATH = 'E:\\Thesis_WCDTool\\'
WCDTOOL_TESTCASE_PATH = 'usecases\\generated\\'

DEBUG = True


class CostChecker(object):
    def __init__(self):
        pass

    def cost(self, s: TestCase):
        '''

        Args:
            s (TestCase): TestCase object

        Returns:
            Sum of occupation percentages of all ports of all switches in testcase
        '''
        switches = s.switches

        sum_of_occupation_percentages = 0

        for switch in switches.values():
            for port in switch.output_ports.values():
                sum_of_occupation_percentages += port.get_occupation_percentage()

        return sum_of_occupation_percentages


def debug_print(s, end='\n'):
    if DEBUG:
        print(s, end=end)
