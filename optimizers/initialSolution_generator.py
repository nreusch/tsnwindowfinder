import math
import time

from data_structures import TestCase


def create_initial_solution(testCase: TestCase):
    """

    Args:
        testCase (TestCase): initial testcase (without windows)

    Returns:
        Initial Solution as TestCase Object (with windows set)
    """
    timer = time.clock()
    for switch in testCase.switches.values():
        for port in switch.output_ports.values():
            max_port_period = 0

            # 1. Calculate Length & Period for each queue. Determine Max Period
            for queuenr in port.get_sorted_queuenrs():
                queue = port.queues[queuenr]

                length = queue.total_sending_time + queue.highest_sending_time
                period = math.floor(queue.total_sending_time * (1 / queue.window_percentage))

                if period < length:
                    period = math.ceil(queue.highest_sending_time/(1-queue.window_percentage))
                    length = period
                    queue.total_sending_time = period-queue.highest_sending_time

                if period > max_port_period:
                    max_port_period = period

                port.set_window(queuenr, 0, length, period)

            # 2. Scale all other queues to Max Period. Set Offsets
            current_offset = 0
            for queuenr in port.get_sorted_queuenrs():
                queue = port.queues[queuenr]
                period = port.get_window(queuenr)[2]

                scale_factor = max_port_period / period

                # Only the total sending time has to be scaled up
                length = math.ceil(queue.total_sending_time * scale_factor + queue.highest_sending_time)
                length = min(length, max_port_period-current_offset)
                period = max_port_period

                # If no space is left in queue set 0 period
                if length > 0:
                    port.set_window(queuenr, current_offset, length, period)
                else:
                    port.delete_queue(queuenr)
                current_offset += length

    runtime = time.clock() - timer
    print('Generate initial solution in {}s'.format(runtime))
    return testCase