from collections import deque, OrderedDict

from data_structures.TestCase import TestCase
from data_structures.Stream import Stream
from data_structures.Node import Node, Switch
import os
import re
from shutil import copyfile


def find_testcases(inputpath, recursive=False, output=True):
    """Returns a collection of testcase paths for every "*.network_description" file in the given input folder.
        :param str inputpath: path to testcase or testcase folder
        :param bool recursive: subfolders will be checked as well
        :param bool output: prints information about test cases
        """
    test_cases = []

    if os.path.isdir(inputpath):
        # Folder of testcases
        directories = deque([inputpath])
        while len(directories) > 0:
            directory = directories.popleft()
            if directory[-1] != '/':
                directory += '/'
            for filename in os.listdir(directory):
                if filename.endswith('.streams'):
                    test_cases.append(directory + filename)
                elif recursive and os.path.isdir(directory + filename) and filename[:5] != 'batch':
                    directories.append(directory + filename)
    else:
        test_cases.append(inputpath)

    if output:
        print('TEST CASES:')
        if len(test_cases) > 0:
            for test_case in test_cases:
                print('\t', test_case)
        else:
            print('\tNo test cases for "{}"'.format(inputpath))
        print('Total number of test cases: {}'.format(len(test_cases)))
        print()
    return test_cases


def determine_and_create_output_directory(test_case):
    name = os.path.basename(test_case)  # gets filename from path
    name = os.path.splitext(name)[0]  # removes file ending and dot

    output_folder = '{}/{}'.format(os.path.dirname(test_case), 'output')
    if output_folder != '' and not os.path.exists(output_folder):
        print('making dir')
        os.makedirs(output_folder)
    return name, output_folder


def parse_testcase(testcases_path, tc_name, WCDTOOL_PATH, WCDTOOL_OUTPUTPATH):
    streams = {}  # Map: Stream Name -> Stream
    _nodes = {}  # Map: Node Name -> Node
    switches = OrderedDict()  # OrderedMap: Switch Name -> Switch
    _routes = {}  # Map: VLS Name -> Route (Ordered List of Nodes)

    stream_file = open(testcases_path + tc_name + '.streams', 'r')
    vls_file = open(testcases_path + tc_name + '.vls', 'r')

    # Copy over stream and vls file for later use with wcd tool
    if not os.path.exists("{}\\in\\".format(WCDTOOL_PATH + WCDTOOL_OUTPUTPATH + tc_name)):
        os.makedirs("{}\\in\\".format(WCDTOOL_PATH + WCDTOOL_OUTPUTPATH + tc_name),
                    exist_ok=True)

    if not os.path.exists("{}\\out\\".format(WCDTOOL_PATH + WCDTOOL_OUTPUTPATH + tc_name)):
        os.makedirs("{}\\out\\".format(WCDTOOL_PATH + WCDTOOL_OUTPUTPATH + tc_name),
                    exist_ok=True)
    copyfile(stream_file.name, "{}\\in\\{}".format(WCDTOOL_PATH + WCDTOOL_OUTPUTPATH + tc_name, 'msg.txt'))
    copyfile(vls_file.name, "{}\\in\\{}".format(WCDTOOL_PATH + WCDTOOL_OUTPUTPATH + tc_name, 'vls.txt'))

    # Parsing VLS
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

    # Parsing Streams
    for line in stream_file:
        if not line.startswith('#'):
            m = re.search(r'([^\s,]+),\s?(\d+),\s?(\d+),\s?([^\s,]+),\s?(\w+),\s?(\d+),\s?(\d+)', line)
            if m is not None:
                s = Stream(m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(7)), int(m.group(6)),
                           _routes[m.group(4)])
                streams[m.group(1)] = s  # Add to list

                # Associate Stream with each switch on route (skip end systems)
                i = 1
                for node in s.route[1:-1]:
                    switches[node.uid].associate_stream_to_queue(s.uid, s.sending_time, s.priority, s.route[i + 1].uid)
                    i += 1

    return TestCase(switches, streams, tc_name)
