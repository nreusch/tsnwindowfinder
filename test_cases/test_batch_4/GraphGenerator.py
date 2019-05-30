import pickle
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from optimizers.iterative_optimizer import OutputData


def plot_costvswcd(iteration_data, nr_of_ports):
    average_costs = []
    wcd_sum = []
    iterations = []

    i = 0
    for tuple in iteration_data:
        average_costs.append(round((tuple[0] / nr_of_ports) * 100, 2))
        wcd_sum.append(tuple[1])
        iterations.append(i)
        i = i + 1

    fig, ax = plt.subplots()

    ax.tick_params(axis='y', labelcolor='tab:red')
    ax.xaxis.set_ticks(range(0, len(iterations), 1))
    ax.plot(iterations, average_costs, color='tab:red')
    ax.set(xlabel='Iterations',
           title='')
    ax.set_ylabel('Average Cost (%)', color='tab:red')
    ax.grid()

    ax2 = ax.twinx()  # instantiate a second axes that shares the same x-axis

    ax2.tick_params(axis='y', labelcolor='tab:blue')
    ax2.plot(iterations, wcd_sum, color='tab:blue')
    ax2.set_ylabel('Sum of worst-case delays (us)', color='tab:blue')

    fig.savefig("test.png")
    plt.show()

def plot_solved_streams(iteration_data):
    solved_streams = []
    iterations = []
    i = 0
    for iteration in iteration_data:
        solved_streams.append(iteration[3])
        iterations.append(i)
        i = i + 1
    fig, ax = plt.subplots()

    ax.tick_params(axis='y', labelcolor='tab:blue')
    ax.xaxis.set_ticks(range(0, len(iterations), 5))
    ax.plot(iterations, solved_streams, color='tab:blue')
    ax.plot(iterations, iterations, color='tab:red')
    ax.set(xlabel='Iterations',
           title='')
    ax.set_ylabel('Streams solved', color='tab:blue')
    ax.grid()

    plt.show()

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
    # plt.xticks(rotation='vertical')
    #ax.set_xticks(index + bar_width / 2)
    plt.subplots_adjust(bottom=0.15)

    # ax.set_xticklabels(wcds.keys())
    ax.legend()

    fig.tight_layout()
    plt.savefig(filename)

def plot_boxplot(final_port_costs1, final_port_costs2, final_port_costs3):

    costs1 = []
    for c in final_port_costs1.values():
        costs1.append(round(c*100,2))

    costs2 = []
    for d in final_port_costs2.values():
        costs2.append(round(d * 100, 2))

    costs3 = []
    for e in final_port_costs3.values():
        costs3.append(round(e * 100, 2))

    fig, ax = plt.subplots()


    ax.boxplot([costs1, costs2, costs3], vert=False)
    ax.set_yticklabels(['General Motors', 'ORION', 'Complex Test 1'])
    ax.set(xlabel='Port Occupation (%)',
           title='')

    plt.show()


path = 'E:\\Dropbox\\Dropbox\\DTU\Master Thesis\\code\\TSNWindowFinder_Heuristic\\test_cases\\test_batch_4\\output\\'

input = ["general_motors_2019-05-30_12-03_DivideConquerOptimization\\", "orion_2019-05-30_12-39_DivideConquerOptimization\\", "complex_test_1_2019-05-30_12-00_DivideConquerOptimization\\"]

output_data = []

for s in input:
    output_data.append(pickle.load(open(path + s + 'output_data.pickle', "rb")))

# Plot cost and wcd sum

iteration_data = output_data[1][9]
plot_boxplot(output_data[0][8], output_data[1][8], output_data[2][8])


