import matplotlib.pyplot as plt
import time


class Plotter(object):
    def __init__(self, graph_update_interval, start_cost, x_init, y_init):
        self.start_time = time.time()
        self.graph_update_interval = graph_update_interval

        plt.ion()
        fig = plt.figure()
        ax = fig.add_subplot(111)

        plt.ylim((0, start_cost + 100))
        plt.xlim((0, 50))

        self.line1, = ax.plot(x_init, y_init, 'r-')
        plt.draw()

    def plot(self, x, y):
        if time.time() - self.start_time > self.graph_update_interval:
            self.line1.set_xdata(x)
            self.line1.set_ydata(y)
            plt.draw()
            plt.pause(0.02)
