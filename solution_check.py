import os
import re
import subprocess
import time
from collections import defaultdict, OrderedDict
from operator import itemgetter

from data_structures import TestCase

DEBUG = False


def debug_print(s, end='\n'):
    if DEBUG:
        print(s, end=end)


def is_actually_infinity(stream_uid, streams, infinite_queues):
    stream = streams[stream_uid]

    i = 0
    for node in stream.route[:-1]:
        portstring = "{} -> {}".format(node.uid, stream.route[i+1].uid)
        if portstring in infinite_queues:
            if stream.priority in infinite_queues[portstring]:
                return True

        i = i + 1
    return False

class SolutionChecker(object):
    """Checks solutions represented by TestCase objects and returns their feasibility and if infeasible the exceeding
    percentages of streams """

    def __init__(self, wcdtool_path: str, wcdtool_testcase_subpath: str, wcdanalysis_timeout: int):
        """

        Args:
            wcdtool_path (str): Path to WCDTool executable
            wcdtool_testcase_subpath (str): Relative path from WCDTool executable to testcase folder
            wcdanalysis_timeout (int): Timeout in seconds
        """
        self.wcdtool_testcase_subpath = wcdtool_testcase_subpath
        self.wcdtool_path = wcdtool_path
        self.timeout = wcdanalysis_timeout

    def serialize_solution(self, s: TestCase):
        """

        Args:
            s (TestCase): Solution to be serialized

        Returns:
            The lines written to historySCHED1 (GCL) file
        """
        switches = s.switches
        tc_name = s.name

        # Write rate.txt if not existant
        if not os.path.exists(
                "{}\\in\\{}".format(self.wcdtool_path + self.wcdtool_testcase_subpath + tc_name, 'rate.txt')):
            rate = open("{}\\in\\{}".format(self.wcdtool_path + self.wcdtool_testcase_subpath + tc_name, 'rate.txt'),
                        'w+')
            rate.write('# link rate, integrationMode, bandwidthFractionA, bandwidthFractionB\n1000')
            rate.close()

        # Write historySCHED1.txt if available
        historySCHED1 = open(
            "{}\\in\\{}".format(self.wcdtool_path + self.wcdtool_testcase_subpath + tc_name, 'historySCHED1.txt'),
            'w+')
        lines = ['#open time, close time, period, priority\n']

        for switch in switches.values():
            for dest_name in switch.output_ports.keys():
                port = switch.output_ports[dest_name]
                lines.append('{},{}\n'.format(switch.uid, dest_name))

                i = 0
                for priority in port.get_sorted_queuenrs():
                    row = port._M_Windows[i]
                    offset = row[0]
                    end = row[1]
                    period = row[2]
                    lines.append(
                        '{}\t{}\t{}\t{}\n'.format(offset, end, period,
                                                  priority))
                    i += 1

                lines.append('\n')

        historySCHED1.write(''.join(lines))
        historySCHED1.write('#')  # comment out last line, since no empty last line is allowed
        historySCHED1.close()
        return lines

    def read_wcd_output(self, tc_name: str, timeout: int):
        """

        Args:
            tc_name (str): Name of testcase
            timeout (int): timeout for waiting for result of wcd-analysis, in seconds

        Returns:
            List of worst-case E2E delay string, List of worst-case port delay strings
        """
        wce2edelay_list = []
        wcportdelay_list = []

        try:
            proc = subprocess.run(
                args=[self.wcdtool_path + 'TSNNetCal.exe', "{}".format(self.wcdtool_testcase_subpath + tc_name)],
                stdout=subprocess.PIPE, timeout=timeout)
            if str(proc.stdout).startswith('b\'OK') or str(proc.stdout).startswith('b\'Create object failed!'):
                # SUCCESS
                wcportdelay_file_path = "{}\\out\\{}".format(
                    self.wcdtool_path + self.wcdtool_testcase_subpath + tc_name,
                    'TmpWCPortDelay.txt')
                wce2edelay_file_path = "{}\\out\\{}".format(self.wcdtool_path + self.wcdtool_testcase_subpath + tc_name,
                                                            'WCEndtoEndDelay.txt')

                # Read Port Delays
                t = time.time()
                while not os.path.exists(wcportdelay_file_path) or time.time() - t > 15:
                    time.sleep(0.01)
                wcportdelay_file = open(wcportdelay_file_path, 'r')

                for line in wcportdelay_file:
                    wcportdelay_list.append(line)

                wcportdelay_file.close()

                # Read E2E Delays
                t = time.time()
                while not os.path.exists(wce2edelay_file_path) or time.time() - t > 15:
                    time.sleep(0.01)
                wce2edelay_file = open(wce2edelay_file_path, 'r')

                for line in wce2edelay_file:
                    wce2edelay_list.append(line)

                wce2edelay_file.close()
            else:
                print('TSNNetCal returned unexpected result')
                # print(proc.stdout.decode("utf-8"))
        except subprocess.TimeoutExpired:
            print('TSNNetCal Timeout')

        return wce2edelay_list, wcportdelay_list

    def check_solution(self, s: TestCase):
        """

        Args:
            s (TestCase): Solution to be checked
            timeout (int): timeout for waiting for result of wcd-analysis, in seconds

        Returns: isValid?,isFeasible?, decreasingly sorted exceeding percentages of all streams that missed their deadline stored in List of tuples
        (Percentage(float), stream uid(str)), OrderedDict(stream uid, wcd (e2e) as string)
        """
        streams = s.streams
        tc_name = s.name

        infeasible_streams_percentages = []
        wcd_dict = OrderedDict()
        infinite_streams = []
        infinite_queues = {} # Map(portstring, list of priorities)

        # Serialize Solution & Run Tool
        written_lines = self.serialize_solution(s)
        # DEBUG
        debug_print('Solution serialized')
        wce2elist, wcportdelay_list = self.read_wcd_output(tc_name, self.timeout)

        debug_print('Windows: ', end='')
        for sw in s.switches.values():
            for port_name in sw.output_ports.keys():
                debug_print('{},{}: {} '.format(sw.uid, port_name, str(sw.output_ports[port_name]._M_Windows)), end='')
        debug_print('')
        debug_print('Induced Port Delay: ', end='')
        for line in wcportdelay_list:
            match = re.search('(.*): (.*), priority (\d)', line)
            debug_print('{}; '.format(line[:-13]), end='')
            if match is not None:
                if match.group(2) is "0":
                    if match.group(1) in infinite_queues.keys():
                        infinite_queues[match.group(1)].append(int(match.group(3)))
                    else:
                        infinite_queues[match.group(1)] = [int(match.group(3))]


        debug_print('')
        debug_print('End-to-end Delay: ', end='')
        for line in wce2elist:
            debug_print('{}; '.format(line[:-1]), end='')
        debug_print('')
        valid = True
        feasible = True

        # Check that a valid result was returned
        if len(wce2elist) is 0 or len(wcportdelay_list) is 0:
            valid = False
            feasible = False
        else:
            # Check that wcd's are below deadlines
            for line in wce2elist:
                match = re.search('(.*),.*:(.*)', line)
                if match is not None:
                    if match.group(2).endswith('INF') or is_actually_infinity(match.group(1), streams, infinite_queues):
                        debug_print('!! (Infinite WCD found) !!')
                        infinite_streams.append(match.group(1))
                    else:
                        wcd_dict[match.group(1)] = match.group(2)
                        stream_uid = match.group(1)
                        wcd = float(match.group(2))
                        ddl = streams[stream_uid].deadline
                        if ddl < wcd:
                            feasible = False
                            percentage = (wcd - ddl) / ddl
                            infeasible_streams_percentages.append((percentage, stream_uid))
                            debug_print('!! Solution is infeasible (WCD > deadline found) !!')

        if not valid:
            # DEBUG
            debug_print('### Written Window File ###')
            for l in written_lines:
                debug_print(l, end='')
            debug_print(
                '### E2E Delays ###\n{}\n### Port Delays ###\n{}'.format(''.join(wce2elist), ''.join(wcportdelay_list)))
        else:
            debug_print('!! Solution is valid !!')

        infeasible_streams_percentages.sort(key=itemgetter(0), reverse=True)
        return valid, feasible, infeasible_streams_percentages, wcd_dict, infinite_streams
