import math
import os
import re
import subprocess
import time
import numpy as np
import math

WCDTOOL_PATH = 'TSNNetCal_NoESWindows\\'
WCDTOOL_OUTPUTPATH = 'usecases\\generated\\'


def serialize_solution(s):
    switches = s[0].switches
    tc_name = s[0].tc_name
    M = s[1]

    # Write rate.txt if not existant
    if not os.path.exists("{}\\in\\{}".format(WCDTOOL_PATH + WCDTOOL_OUTPUTPATH + tc_name, 'rate.txt')):
        rate = open("{}\\in\\{}".format(WCDTOOL_PATH + WCDTOOL_OUTPUTPATH + tc_name, 'rate.txt'),
                    'w+')
        rate.write('# link rate, integrationMode, bandwidthFractionA, bandwidthFractionB\n1000')
        rate.close()

    # Write historySCHED1.txt if available
    while not os.path.exists("{}\\in\\{}".format(WCDTOOL_PATH + WCDTOOL_OUTPUTPATH + tc_name, 'historySCHED1.txt')):
        time.sleep(0.01)

    historySCHED1 = open(
        "{}\\in\\{}".format(WCDTOOL_PATH + WCDTOOL_OUTPUTPATH + tc_name, 'historySCHED1.txt'),
        'w+')
    lines = ['#open time, close time, period, priority\n']

    for switch in switches.values():
        # Extract switch matrix
        M_switch = M[switch.M_row_offset:switch.M_row_offset + switch.total_number_of_queues, :3]

        for dest_name in switch.output_ports.keys():
            port = switch.output_ports[dest_name]
            lines.append('{},{}\n'.format(switch.uid, dest_name))

            i = 0
            for priority in port.get_sorted_queuenrs():
                row = M_switch[i]
                offset = row[0]
                end = offset + row[1]
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

def read_wcd_output(tc_name):
    wce2edelay_list = []
    wcportdelay_list = []
    proc = subprocess.run(args=[WCDTOOL_PATH + 'TSNNetCal.exe', "{}".format(WCDTOOL_OUTPUTPATH + tc_name)],
                          stdout=subprocess.PIPE)
    if str(proc.stdout).startswith('b\'OK'):
        # SUCCESS
        wcportdelay_file_path = "{}\\out\\{}".format(WCDTOOL_PATH + WCDTOOL_OUTPUTPATH + tc_name, 'TmpWCPortDelay.txt')
        wce2edelay_file_path = "{}\\out\\{}".format(WCDTOOL_PATH + WCDTOOL_OUTPUTPATH + tc_name, 'WCEndtoEndDelay.txt')

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
        print(proc.stdout.decode("utf-8"))

    return wce2edelay_list, wcportdelay_list


def create_binary_matrix(M_switch, gcd, lcm):
    if int(gcd) != 0 and int(lcm) != 0:
        # DEBUG
        print("GCD: {}; LCM: {}; Total number of columns (lcm/gcd): {}".format(gcd, lcm, int(lcm / gcd)))

        M_binary = np.empty([0, int(lcm / gcd)], dtype=int)

        for row in M_switch:
            offset = row[0]
            length = row[1]
            period = row[2]

            a = np.zeros((int(offset / gcd)), dtype=bool)
            if len(a) > 0:
                a = np.concatenate((a, np.ones((int(length / gcd)), dtype=bool)), axis=0)
            else:
                a = np.ones((int(length / gcd)), dtype=bool)
            a = np.concatenate((a, np.zeros((int((period - offset - length) / gcd)), dtype=bool)), axis=0)
            a = np.tile(a, int(lcm / period))
            print('Resulting binary with length {}: '.format(len(a)))
            print(a)
            M_binary = np.append(M_binary, [a], 0)

            # DEBUG
            print('Window with offset {}, length {}, period {}'.format(offset, length, period))
            print('Resulting binary with length {}: '.format(len(a)))
            print(a)

        # DEBUG
        print('Final Binary Matrix: ')
        print(M_binary)
        return M_binary
    else:
        raise ValueError('Error. GCD or LCM equals zero. GCD: {} LCM {}'.format(gcd, lcm))


def matrix_lcm(M_switch):
    # DEBUG
    print('Calculating LCM of: ')
    print(M_switch[:, 2:])

    lc = np.lcm.reduce(M_switch[:, 2:])
    print('Result: ')
    print(lc)
    return lc[0]


# https://stackoverflow.com/questions/15569429/numpy-gcd-function
def matrix_gcd(M_switch):
    M_switch = M_switch.flatten()

    gcd = M_switch[0]
    for i in M_switch:
        gcd = math.gcd(i, gcd)
        if gcd == 1:
            return 1

    return gcd


def check_solution(s):
    streams = s[0].streams
    tc_name = s[0].tc_name
    M = s[1]

    # Serialize Solution & Run Tool
    written_lines = serialize_solution(s)
    wce2elist, wcportdelay_list = read_wcd_output(tc_name)

    error = False

    # Check that a valid result was returned
    if len(wce2elist) is 0 or len(wcportdelay_list) is 0:
        error = True
    else:
        # Check that wcd's are below deadlines
        for line in wce2elist:
            match = re.search('(.*),.*:(.*)', line)
            if match is not None:
                if match.group(2).endswith('INF'):
                    error = True
                else:
                    stream_uid = match.group(1)
                    wcd = float(match.group(2))
                    if streams[stream_uid].deadline < wcd:
                        error = True
    if error:
        # DEBUG
        print('### Matrix ###')
        print(M)
        print('### Written Window File ###')
        for l in written_lines:
            print(l, end='')
        print('### E2E Delays ###\n{}\n### Port Delays ###\n{}'.format(''.join(wce2elist), ''.join(wcportdelay_list)))
        return False
    else:
        return True


def cost(s):
    # Returns -1 if impossible solution
    switches = s[0].switches
    M = s[1]

    total_used_time = 0

    # Calculate Cost
    for switch in switches.values():
        # for each switch
        if switch.total_number_of_queues > 0:
            # Extract switch matrix
            M_switch = M[switch.M_row_offset:switch.M_row_offset + switch.total_number_of_queues, :3]

            # DEBUG
            print('Extracting matrix for switch {} at offset {} with {} rows'.format(switch.uid, switch.M_row_offset,
                                                                                     switch.total_number_of_queues))
            print('Result: ')
            print(M_switch)

            # Create binary matrix
            g = matrix_gcd(M_switch)  # length in us of one digit in binary
            l = matrix_lcm(M_switch)  # hyperperiod
            M_binary = create_binary_matrix(M_switch, g, l)

            result_binary = np.bitwise_or.reduce(M_binary, 0)

            used_time = np.count_nonzero(result_binary) * g
            total_used_time += used_time

    print('Cost: {}'.format(total_used_time))
    return total_used_time
