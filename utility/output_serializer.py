import math
import os
import pickle
import matplotlib.pyplot as plt
import numpy as np

from graphviz import render
from typing import NamedTuple
from data_structures.TestCase import TestCase
from utility.window_visualizer import WindowVisualizer


class OutputData(NamedTuple):
    """Immutable Tuple to store all the information needed to generate the output files"""
    initial_solution: TestCase
    final_solution: TestCase
    initial_wcds: dict  # Dict(Stream Name, wcd)
    final_wcds: dict  # Dict(Stream Name, wcd)
    runtime: float
    initial_cost: float
    final_cost: float
    initial_port_costs: dict  # Dict('SW1,SW2', 0.01)
    final_port_costs: dict  # Dict('SW1,SW2', 0.1)
    iteration_data: list  # (cost, sum_wcd, sum_ep, solved_stream_number)
    infinite_streams: list
    final_exceeding_percentages: dict
    initial_nr_of_stream_tobesolved: int
    final_step_amount: int
    initial_ep_mean: float

def render_windows(file: str, testCase: TestCase):
    w2 = WindowVisualizer(testCase)
    w2.export(file)

def write_windows(filename: str, switches: dict):
    """

    Args:
        filename (str): File to write to
        switches (dict): Switches dict

    """
    windows_file = open(filename, 'w+')
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

    windows_file.write(''.join(lines))
    windows_file.write('#')  # comment out last line, since no empty last line is allowed
    windows_file.close()


def render_bar_graph(filename: str, streams: dict, wcds: dict, final: bool):
    """

    Args:
        filename (str): File to write to
        streams (dict): Dict(Stream Name, Stream)
        wcds (dict): Dict(Stream Name, wcd)
        final (boolean): wcds of final(True) or initial solution?

    """
    n_groups = len(wcds.keys())
    label_list = []
    wcd_list = []
    ddl_list = []

    for stream_uid in wcds.keys():
        wcd_string = wcds[stream_uid]
        if wcd_string.endswith('INF'):
            wcd_list.append(0)
            # TODO: Visualize Infinity
        else:
            wcd = int(float(wcd_string))
        deadline = streams[stream_uid].deadline

        label_list.append(stream_uid)
        wcd_list.append(wcd)
        ddl_list.append(deadline)

    fig, ax = plt.subplots()

    index = np.arange(n_groups)
    bar_width = 0.35

    opacity = 0.4

    rects1 = ax.bar(index, ddl_list, bar_width,
                    alpha=opacity, color='r',
                    label='Deadline')

    rects2 = ax.bar(index + bar_width, wcd_list, bar_width,
                    alpha=opacity, color='b',
                    label='WCD')

    ax.set_xlabel('Streams')
    ax.set_ylabel('Deadlines & Worst Case Delays')
    if final:
        ax.set_title('Deadlines & Worst Case Delays for all streams - Final Solution')
    else:
        ax.set_title('Deadlines & Worst Case Delays for all streams - Initial Solution')
    ax.set_xticks(index + bar_width / 2)
    ax.set_xticklabels(wcds.keys())
    ax.legend()

    fig.tight_layout()
    plt.savefig(filename)


def render_network_topology(filename_without_ending: str, streams: dict):
    """
    Renders the network topology defined by the streams routes to a .dot and a .svg file.

    Args:
        filename_without_ending (str): File to write to, without file ending
        streams (dict): Dict(Stream Name, Stream)

    """
    nodes = {}

    # Add all nodes
    for stream in streams.values():
        color_counter = 0
        for node in stream.route:
            if node.uid not in nodes:
                # Create node if not existant
                nodes[node.uid] = []

            if color_counter > 0:
                # Except for first node add all nodes on routes as neighbours of previous node, if not there yet
                if node.uid not in nodes[stream.route[color_counter - 1].uid]:
                    nodes[stream.route[color_counter - 1].uid].append(node.uid)
            color_counter += 1

    colors = [
        '#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe',
        '#008080', '#e6beff', '#9a6324', '#fffac8', '#800000', '#aaffc3', '#808000', '#ffd8b1', '#000075', '#808080',
        '#000000'
    ]

    lines = []
    lines.append('digraph G {')
    lines.append('    forcelabels=true;')
    lines.append('    overlap=false;')
    lines.append('    layout="neato";')
    lines.append('    node [style="filled,bold"];')
    lines.append('    node [shape=circle];')

    # Nodes:
    lines.append('    ')
    lines.append('    /* NODES */')

    # Switch: color="#c53039"; fillcolor="#faced0"; shape="box"
    # ES: color="#143065"; fillcolor="#d2e6ff"

    for node in nodes.keys():
        if node.startswith("SW"):
            lines.append('    "{}" [label=<{}>; color="#c53039"; fillcolor="#faced0"; shape="box"];'.format(node, node))
        else:
            lines.append('    "{}" [label=<{}>; color="#143065"; fillcolor="#d2e6ff"];'.format(node, node))

    # Edges:
    lines.append('    ')
    lines.append('    /* EDGES */')

    # Physical Links - Edges
    # lines.append('    subgraph Rel1 {')
    # lines.append('        edge [dir=none, color=black]')
    # for node in nodes.keys():
    #    for neighbour in nodes[node]:
    #        lines.append('    "{}" -> "{}";'.format(node, neighbour))
    # lines.append('    }')

    # Streams - Edges
    color_counter = 0

    for stream in streams.values():
        j = 0
        for node in stream.route[:-1]:
            lines.append('    "{}" -> "{}" [color="{}"];'.format(node.uid,
                                                                 stream.route[j + 1].uid, colors[color_counter]))
            j += 1
        color_counter = color_counter + 1
        if color_counter >= 11:
            color_counter = 0

    # Footer:
    lines.append('}')

    graphviz_file = open(filename_without_ending + '.dot', 'w+')
    graphviz_file.write('\n'.join(lines))
    graphviz_file.close()

    render('neato', 'pdf', filename_without_ending + '.dot')


def write_statistics(filename: str, output_data: OutputData):
    """

    Args:
        filename (str): File to write to
        output_data (OutputData): All the output data

    """
    statistics_file = open(filename, 'w+')
    lines = []

    lines.append('Statistic for TestCase: ' + output_data.final_solution.name)
    lines.append('')
    lines.append('Feasible Streams: {} Infeasible Streams: {}'.format(
        len(output_data.final_wcds) - len(output_data.final_exceeding_percentages),
        len(output_data.infinite_streams) + len(output_data.final_exceeding_percentages)))
    lines.append(
        'ES: {};SW: {};Streams: {}'.format(output_data.initial_solution.ESNr, output_data.initial_solution.SWNr,
                                           output_data.initial_solution.StreamNr))
    lines.append(
        'Streams to be solved initially: {}; Steps it took: {}'.format(output_data.initial_nr_of_stream_tobesolved,
                                                                       output_data.final_step_amount))
    lines.append('')

    N = len(output_data.initial_port_costs)
    mean_initial = output_data.initial_cost / N
    su = 0
    for cost in output_data.initial_port_costs.values():
        su = su + math.pow(cost - mean_initial, 2)
    sigma_initial = math.sqrt(1 / N * su)
    lines.append('Initial Cost: ' + str(output_data.initial_cost))
    lines.append('Initial Cost (Mean): ' + str(output_data.initial_cost / len(output_data.initial_port_costs)))
    lines.append('Initial Cost (Standard Deviation): ' + str(sigma_initial))

    lines.append('')

    N = len(output_data.final_port_costs)
    mean_final = output_data.final_cost / N
    su = 0
    for cost in output_data.final_port_costs.values():
        su = su + math.pow(cost - mean_final, 2)
    sigma_final = math.sqrt(1 / N * su)
    lines.append('Final Cost: ' + str(output_data.final_cost))
    lines.append('Final Cost (Mean): ' + str(output_data.final_cost / len(output_data.final_port_costs)))
    lines.append('Final Cost (Standard Deviation): ' + str(sigma_final))

    lines.append('')

    i = 0
    sum = 0
    for wcd in output_data.final_wcds.values():
        if not wcd.endswith('INF'):
            sum = sum + float(wcd)
            i = i + 1
    lines.append('Mean E2E-Delay: ' + str(sum / i))
    lines.append('Optimization Runtime (s): ' + str(output_data.runtime))

    lines.append('')
    lines.append('Initial Port Costs (Port Occupation Percentages): ')
    for k, v in output_data.initial_port_costs.items():
        lines.append('{}: {}%'.format(k, str(round(v * 100, 2))))

    lines.append('')
    lines.append('Final Port Costs (Port Occupation Percentages): ')
    for k, v in output_data.final_port_costs.items():
        lines.append('{}: {}%'.format(k, str(round(v * 100, 2))))

    lines.append('')
    lines.append('For parsing: ')
    lines.append(str(output_data.initial_solution.ESNr))
    lines.append(str(output_data.initial_solution.SWNr))
    lines.append(str(output_data.initial_solution.StreamNr))
    lines.append(str(output_data.initial_nr_of_stream_tobesolved))
    lines.append(str(round(output_data.initial_ep_mean * 100, 2)))
    lines.append(str(output_data.final_step_amount))
    lines.append(str(round(mean_initial * 100, 2)))
    lines.append(str(round(mean_final * 100, 2)))
    lines.append(str(round(sigma_initial * 100, 2)))
    lines.append(str(round(sigma_final * 100, 2)))
    lines.append(str(round(output_data.runtime, 2)))

    statistics_file.write('\n'.join(lines))
    statistics_file.close()


def pickle_data(filename: str, output_data: OutputData):
    pickle_out = open(filename, "wb")
    pickle.dump(output_data, pickle_out)
    pickle_out.close()


def append_to_collections(output_folder, output_data):
    # Create collections if not existant
    if not os.path.exists(output_folder + "mean_e2e_delays.txt"):
        f = open(output_folder + "mean_e2e_delays.txt", 'w+')
        f.close()
        f = open(output_folder + "mean_occupation_percentage.txt", 'w+')
        f.close()
        f = open(output_folder + "calc_time.txt", 'w+')
        f.close()
        f = open(output_folder + "infeasible_streams.txt", 'w+')
        f.close()

    # Append data
    f = open(output_folder + "mean_e2e_delays.txt", 'a')
    i = 0
    sum = 0
    for wcd in output_data.final_wcds.values():
        if not wcd.endswith('INF'):
            sum = sum + float(wcd)
            i = i + 1
    f.write(str(round(sum / i)) + "\t" + output_data.initial_solution.name + '\n')
    f.close()

    f = open(output_folder + "mean_occupation_percentage.txt", 'a')
    f.write(str(round(output_data.final_cost / len(output_data.final_port_costs) * 100,
                      2)) + "\t" + output_data.initial_solution.name + '\n')
    f.close()

    f = open(output_folder + "calc_time.txt", 'a')
    f.write(str(round(output_data.runtime, 2)) + "\t" + output_data.initial_solution.name + '\n')
    f.close()

    f = open(output_folder + "infeasible_streams.txt", 'a')
    f.write(str(len(output_data.infinite_streams) + len(output_data.final_exceeding_percentages)) + "/" + str(
        output_data.initial_solution.StreamNr) + "\t" + output_data.initial_solution.name + '\n')
    f.close()
