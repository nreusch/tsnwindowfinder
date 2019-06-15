import pickle
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from optimizers.iterative_optimizer import OutputData


def plot_costvswcd(filename, output_data):
    average_costs = []
    wcd_sum = []
    iterations = []
    iteration_data = output_data[9]
    nr_of_ports = len(output_data[8].keys())

    i = 0
    for tuple in iteration_data:
        average_costs.append(round((tuple[0] / nr_of_ports) * 100, 2))
        wcd_sum.append(tuple[1])
        iterations.append(i)
        i = i + 1

    fig, ax = plt.subplots()
    plt.xticks(rotation='vertical')
    ax.tick_params(axis='y', labelcolor='tab:red')
    ax.xaxis.set_ticks(range(0, len(iterations), 1))
    ax.plot(iterations, average_costs, color='tab:red')
    ax.set(xlabel='Step',
           title='')
    ax.set_ylabel('Average Cost (%)', color='tab:red')
    ax.grid()

    ax2 = ax.twinx()  # instantiate a second axes that shares the same x-axis

    ax2.tick_params(axis='y', labelcolor='tab:blue')
    ax2.plot(iterations, wcd_sum, color='tab:blue')
    ax2.set_ylabel('Sum of worst-case delays (us)', color='tab:blue')

    fig.savefig(filename)
    #plt.show()

def plot_solved_streams(filename, output_data):
    iteration_data = output_data[9]
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
    ax.set(xlabel='Step',
           title='')
    ax.set_ylabel('Streams solved', color='tab:blue')
    ax.grid()

    fig.savefig(filename)
    #plt.show()

def render_bar_graph(filename: str, output_data, final: bool):
    """

    Args:
        filename (str): File to write to
        streams (dict): Dict(Stream Name, Stream)
        wcds (dict): Dict(Stream Name, wcd)
        final (boolean): wcds of final(True) or initial solution?

    """
    streams = output_data[0].streams
    wcds = output_data[2]
    if final:
        wcds = output_data[3]

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
    plt.xticks(rotation='vertical')
    ax.set_xticks(index + bar_width / 2)
    plt.subplots_adjust(bottom=0.15)

    ax.set_xticklabels(wcds.keys())
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

input = ["general_motors_2019-05-30_12-03_DivideConquerOptimization\\", "orion_2019-05-30_12"
                                                                        "-39_DivideConquerOptimization\\",
         "complex_test_1_2019-05-30_12-00_DivideConquerOptimization\\",
         "differenPeriodSameQueue_DifferentSource_test_2019-06-02_16-03_DivideConquerOptimization\\",
         "differenPeriodSameQueue_SameSource_test_2019-06-02_16-03_DivideConquerOptimization\\",
         "easy_test_1_2019-06-02_16-03_DivideConquerOptimization\\",
         "optimizeAlongRoute_OneRouteOneFlow_2019-06-02_16-03_DivideConquerOptimization\\",
         "optimizeAlongRoute_OneRouteThreeFlows_2019-06-02_16-03_DivideConquerOptimization\\",
         "optimizeAlongRoute_TwoIndependantRoutes_2019-06-02_16-03_DivideConquerOptimization\\",
         "optimizeAlongRoute_TwoIntersectingRoutes_OneContainsOther_2019-06-02_16-03_DivideConquerOptimization\\",
         "optimizeAlongRoute_TwoIntersectingRoutes_OneCrossesOther_2019-06-02_16-03_DivideConquerOptimization\\"]

names = ["gm", "orion", "complex", "differenPeriodSameQueue_DifferentSource", "differenPeriodSameQueue_SameSource",
         "easy_test_1", "optimizeAlongRoute_OneRouteOneFlow", "optimizeAlongRoute_OneRouteThreeFlows",
         "optimizeAlongRoute_TwoIndependantRoutes", "optimizeAlongRoute_TwoIntersectingRoutes_OneContainsOther", "optimizeAlongRoute_TwoIntersectingRoutes_OneCrossesOther"]
output_data = []

for s in input:
    output_data.append(pickle.load(open(path + s + 'output_data.pickle', "rb")))

# Plot cost and wcd sum

#iteration_data = output_data[1][9]
#plot_boxplot(output_data[0][8], output_data[1][8], output_data[2][8])

#render_bar_graph('bargraph_gm_initial', output_data[0], False)
#render_bar_graph('bargraph_gm_final', output_data[0], True)
render_bar_graph('bargraph_orion_initial', output_data[1], False)
render_bar_graph('bargraph_orion_final', output_data[1], True)


for i in range(len(names)):
    plot_costvswcd('costvswcd_' + names[i], output_data[i])

for i in range(len(names)):
    plot_solved_streams('solvedstreams_' + names[i], output_data[i])



