import os
import re
from collections import deque
from shutil import copyfile

from data_structures.Node import Node, Switch
from data_structures.Stream import Stream
from data_structures.TestCase import TestCase


def find_testcase_filenames(inputpath: str, recursive=False, output=True):
    """

    Args:
        inputpath (str): .streams file or folder with them
        recursive (bool): If subfolders should be searched
        output (bool): If debug output should be printed

    Returns:
        List of paths to all testcases found
    """
    test_case_filenames = []

    # If folder of testcases
    if os.path.isdir(inputpath):
        directories = deque([inputpath])
        while len(directories) > 0:
            directory = directories.popleft()
            if directory[-1] != '/':
                directory += '/'
            for filename in os.listdir(directory):
                if filename.endswith('.streams'):
                    test_case_filenames.append(directory + filename)
                elif recursive and os.path.isdir(directory + filename):
                    directories.append(directory + filename)
    else:
        test_case_filenames.append(inputpath)

    if output:
        print('TEST CASES:')
        if len(test_case_filenames) > 0:
            for test_case in test_case_filenames:
                print('\t', test_case)
        else:
            print('\tNo test cases for "{}"'.format(inputpath))
        print('Total number of test cases: {}'.format(len(test_case_filenames)))
        print()
    return test_case_filenames


def parse_testcase(test_case_path: str, wcdtool_path: str, wcdtool_testcase_path: str):
    """

    Args:
        test_case_path (str): Path to .streams file
        wcdtool_path (str):  Path to wcdtool executable
        wcdtool_testcase_path (str): Path to wcdtool testcase folder

    Returns:
        TestCase object
    """

    ##### 1. Setup #####
    # Data Structures
    streams = {}  # Map: Stream Name -> Stream
    switches = {}  # Map: Switch Name -> Switch

    _nodes = {}  # Map: Node Name -> Node
    _routes = {}  # Map: VLS Name -> Route (Ordered List of Nodes)

    # Files
    stream_file = open(test_case_path, 'r')
    vls_file = open(test_case_path[:-7] + 'vls', 'r') # remove ".streams" ending and add ".vls" instead

    # Determine test case name from path
    tc_name = os.path.splitext(os.path.basename(test_case_path))[0]  # removes file ending and dot

    ##### 2. Copying #####
    # Copy over stream and vls file for later use with wcd tool
    if not os.path.exists("{}\\in\\".format(wcdtool_path + wcdtool_testcase_path + tc_name)):
        os.makedirs("{}\\in\\".format(wcdtool_path + wcdtool_testcase_path + tc_name),
                    exist_ok=True)

    if not os.path.exists("{}\\out\\".format(wcdtool_path + wcdtool_testcase_path + tc_name)):
        os.makedirs("{}\\out\\".format(wcdtool_path + wcdtool_testcase_path + tc_name),
                    exist_ok=True)
    copyfile(stream_file.name, "{}\\in\\{}".format(wcdtool_path + wcdtool_testcase_path + tc_name, 'msg.txt'))
    copyfile(vls_file.name, "{}\\in\\{}".format(wcdtool_path + wcdtool_testcase_path + tc_name, 'vls.txt'))

    ##### 3. Parsing #####
    # Parsing .vls file
    for line in vls_file:
        if not line.startswith('#'):
            # TODO: allow more chars
            m = re.findall(r'([a-zA-Z0-9_]+)\s?,\s?([a-zA-Z0-9_]+)', line)
            if m is not None:
                _routes[line.split(' ')[0]] = []  # Create Route with name of vl
                r = _routes[line.split(' ')[0]]

                first = True
                for tpl in m:
                    # For each link create nodes if not existent yet
                    n1_name = tpl[0]
                    n2_name = tpl[1]

                    if n1_name not in _nodes:
                        _nodes[n1_name] = Node(n1_name)
                        if _nodes[n1_name].type == 'SW':
                            switches[n1_name] = Switch(n1_name)

                    if n2_name not in _nodes:
                        _nodes[n2_name] = Node(n2_name)
                        if _nodes[n2_name].type == 'SW':
                            switches[n2_name] = Switch(n2_name)

                    # Add nodes to route
                    if first:
                        # first link -> add both nodes
                        r.append(_nodes[n1_name])
                        r.append(_nodes[n2_name])
                        first = False
                    else:
                        # add second node
                        r.append(_nodes[n2_name])

                    # Add output port to first node if it is a switch
                    if n1_name in switches.keys():
                        switches[n1_name].add_outputport_to(n2_name)

    # Parsing .streams file
    for line in stream_file:
        if not line.startswith('#'):
            m = re.search(r'([^\s,]+),\s?(\d+),\s?(\d+),\s?([^\s,]+),\s?([^\s,]+),\s?(\d+),\s?(\d+)', line)
            if m is not None:
                if m.group(5) != 'TT':
                    print('Warning. Unknow traffic class {} found. Will assume TT'.format(m.group(5)))
                s = Stream(m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(7)), int(m.group(6)),
                           _routes[m.group(4)])
                streams[m.group(1)] = s  # Add to list

                # Associate Stream with each switch on route (skip end systems)
                i = 1
                for node in s.route[1:-1]:
                    switches[node.uid].associate_stream_to_queue(s.uid, s.sending_time, s.period, s.priority, s.route[i + 1].uid)
                    i += 1

    ##### 4. Return TestCase #####
    return TestCase(switches, streams, tc_name, len(_nodes)-len(switches))
