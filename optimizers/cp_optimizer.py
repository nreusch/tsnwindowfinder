from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import copy
import datetime
import math
import os

from ortools.sat.python import cp_model

from cost_check import CostChecker
from optimizers import iterative_optimizer
from optimizers.iterative_optimizer import create_initial_solution, IterativeOptimizer
from solution_check import SolutionChecker
from data_structures.TestCase import TestCase


# You need to subclass the cp_model.CpSolverSolutionCallback class.
from utility.output_serializer import write_windows


class CPSolverBahram(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions."""

    def __init__(self, variables, testcase, cost_checker: CostChecker, solution_checker: SolutionChecker, model,
                 solver):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.__variables = variables
        self.__solution_count = 0
        self.test_case = testcase
        self.solutionChecker = solution_checker
        self.costChecker = cost_checker
        self.best_objective_value = 100000000
        self.last_cost = 100000000;
        self.model = model
        self.solver = solver

    def on_solution_callback(self):

        # Check if solution/stream is feasible now. If yes break.
        solution = self.get_testcase()

        cost = self.costChecker.cost(solution)
        # if cost < self.best_objective_value:
        #   print('Solution %i' % self.__solution_count)
        #   print('  objective value = %i' % cost)
        # for v in self.__variables:
        #            print('  %s = %i' % (v, self.Value(v)), end=' ')
        #            print()
        print('  objective value =' + str(cost) + " best:" + str(self.best_objective_value))

        if (self.best_objective_value - cost) > 0:

            _, is_feasible, _, _, infinite_streams = self.solutionChecker.check_solution(solution)
            self.last_cost = cost
            if is_feasible and len(infinite_streams) == 0:
                self.best_objective_value = cost
                print('Solution is feasible %i' % self.__solution_count)
                print('  objective value =' + str(cost))
                for v in self.__variables:
                    print('  %s = %i' % (v, self.Value(v)), end=' ')
                    print()
                self.__solution_count += 1

    def get_testcase(self):
        for switch in self.test_case.switches.values():
            for port in switch.output_ports.values():
                for queuenr in port.get_sorted_queuenrs():
                    values = port.get_window_var(queuenr)
                    port.set_window(queuenr, self.Value(values[0]), self.Value(values[1]), self.Value(values[2]))
                    # print('  %s = %i' % (values[0], self.Value(values[0])))
                    # print('  %s = %i' % (values[1], self.Value(values[1])))
                    # print('  %s = %i' % (values[2], self.Value(values[2])))
                    # print()
        return self.test_case

    def solution_count(self):
        return self.__solution_count

class CPSolverPeriod(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions."""

    def __init__(self, cpvars_p, testcase, cost_checker: CostChecker, solution_checker: SolutionChecker, model, solver,
                 iterative_cost, iterative_solution, total_possibilities):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.cpvars_p = cpvars_p
        self.__solution_count = 0
        self.test_case = testcase
        self.solutionChecker = solution_checker
        self.costChecker = cost_checker
        self.best_solution = copy.deepcopy(iterative_solution)
        self.lowest_cost = iterative_cost
        self.total_possibilities = total_possibilities
        self.model = model
        self.solver = solver
        for port in self.cpvars_p.keys():
            for tuple in self.cpvars_p[port]:
                v = tuple[1]

    def on_solution_callback(self):
        solution = self.test_case

        for port in self.cpvars_p.keys():
            for tuple in self.cpvars_p[port]:
                port.set_period_for_priority(self.Value(tuple[1]), tuple[0])
            print(port._M_Windows)
            print('')

        cost = self.costChecker.cost(solution)

        if cost < self.lowest_cost or self.lowest_cost == -1:
            _, is_feasible, _, _, infinite_streams = self.solutionChecker.check_solution(solution)
            if is_feasible and len(infinite_streams) == 0:
                self.lowest_cost = cost
                self.best_solution = copy.deepcopy(solution)
                print('New best solution with cost: ' + str(cost))

        self.__solution_count += 1
        print("Checked {} out of {} solutions".format(self.__solution_count, self.total_possibilities))

    def solution_count(self):
        return self.__solution_count


def create_cp_model_bahram(testCase: TestCase, output_folder:str, cost_checker: CostChecker, solution_checker: SolutionChecker,
                                   iterative_cost, iterative_solution):
    """

    Args:
        testCase (TestCase): initial testcase (without windows)

    Returns:
        Initial Solution as TestCase Object (with windows set)
    """
    model = cp_model.CpModel()

    # Creates the variables.
    vars = []
    othervars = []
    periodvars = []
    sum = model.NewIntVar(0, 0, 's')

    # Initial Solution
    for switch in testCase.switches.values():
        for port in switch.output_ports.values():
            max_port_period = 0
            # 1. Calculate Length & Period for each queue. Determine Max Period
            for queuenr in port.get_sorted_queuenrs():
                queue = port.queues[queuenr]

                length = queue.total_sending_time + queue.highest_sending_time
                period = math.floor(queue.total_sending_time * (1 / queue.window_percentage))

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
                length = queue.total_sending_time * scale_factor + queue.highest_sending_time
                period = max_port_period

                port.set_window(queuenr, current_offset, length, period)
                current_offset += length

    for switch in testCase.switches.values():
        for port in switch.output_ports.values():

            xoffset = 0;
            xlength = 0;
            pp = 100

            for priority in port.get_sorted_queuenrs():
                queue = port.queues[priority]
                window = port.get_window(priority)

                name = switch.uid + '_' + port.name + '_' + str(priority) + '_'
                offset = model.NewIntVar(0, port.get_maximium_period(priority), name + 'o')

                prang = port.get_maximium_period(priority) - port.get_minimium_period(priority)
                pmax = port.get_maximium_period(priority)
                pmin = port.get_minimium_period(priority)

                # length = model.NewIntVar(int( window[1]), port.get_maximium_period(priority), name+'l')
                length = model.NewIntVar(int(window[1] - window[0]), int(window[1] - window[0]), name + 'l')
                period = model.NewIntVar(pmin, pmax, switch.uid + '_' + port.name + '_p')
                periodp = model.NewIntVar(1, pp, switch.uid + '_' + port.name + '_pP')

                vars.append(offset)
                vars.append(length)
                # vars.append(period)
                vars.append(periodp)
                # sumvars.append(period-length)

                # min_length_ =  queue.total_sending_time * period + queue.highest_sending_time * xperiod_
                min_p = pmin * pp + periodp * prang
                model.Add(period * pp == min_p)
                model.Add(length <= period)
                model.Add((offset + length) <= period)
                model.Add(offset == (xoffset + xlength))
                xoffset = offset
                xlength = length

                port.set_window_var(priority, offset, length, period)
                # if i > 0:
                #    lastpriority = port.get_sorted_queuenrs()[i-1]
                #    x_window = port.get_window_var(lastpriority)
                #    #offset =  x_window[0] +x_window[1]
                #    model.Add (offset >= (x_window[0]+x_window[1]))
                # if i==0:
                #    #offset = 0
                #    model.Add (offset == 0)

                # i += 1

        # Total Window Length = End of last Window
        last_window = port._M_WindowsVar[len(port.queues) - 1]
        total_length = last_window[1]
        w_period = last_window[2]
        sum = sum + (w_period - total_length)

    vars.append(sum);
    # Creates the constraints.
    # model.Add(x != y)

    solver = cp_model.CpSolver()
    # model.Maximize(sum)
    # Creates a solver and solves.
    # model.AddDecisionStrategy(periodvars, cp_model.CHOOSE_FIRST,cp_model.SELECT_MAX_VALUE )
    # model.AddDecisionStrategy(othervars, cp_model.CHOOSE_FIRST,cp_model.SELECT_MIN_VALUE)

    solution_printer = CPSolverBahram(vars, testCase, cost_checker, solution_checker, model,
                                                           solver)
    status = solver.SearchForAllSolutions(model, solution_printer)
    print(testCase.name)
    print('Status = %s' % solver.StatusName(status))
    print('Number of solutions found: %i' % solution_printer.solution_count())
    #print('Best solution at cost: ' + str(solution_printer.lowest_cost))
    print('Best iterative solution at cost: ' + str(iterative_cost))

    #subfolder = solution_printer.best_solution.name + '_' + datetime.datetime.now().strftime(
    #    '%Y-%m-%d_%H-%M') + '_cp_bahram/'

    # Create output_folder if it doesn't exist yet
    #if not os.path.exists(output_folder):
    #    os.makedirs(output_folder, exist_ok=True)

    # Create subfolder if it doesn't exist yet
    #if not os.path.exists(output_folder + subfolder):
    #    os.makedirs(output_folder + subfolder, exist_ok=True)

    #write_windows(output_folder + subfolder + "{}.txt".format('windows_final'),
    #              solution_printer.best_solution.switches)

    #print('Output Files written to: ' + output_folder + subfolder)

    return None


def create_cp_model_variablePeriod(testCase: TestCase, output_folder:str, cost_checker: CostChecker, solution_checker: SolutionChecker,
                                   iterative_cost, iterative_solution):
    """

    Args:
        testCase (TestCase): initial testcase (without windows)

    Returns:
        Solution as TestCase Object (with windows set)
    """
    cpvars_period = {}  # Map(port, (priority, p))
    cp_vars = []
    model = cp_model.CpModel()
    initial_solution = create_initial_solution(testCase)
    total_possibilities = 0

    for switch in initial_solution.switches.values():
        for port in switch.output_ports.values():
            port_period = port.get_hyperperiod()
            port_min_period = port.get_minimum_period_with_current_windows()

            for priority in port.get_sorted_queuenrs():
                name = switch.uid + '_' + port.name + '_' + str(priority) + '_'
                p = model.NewIntVar(port_min_period, port_period, name + 'p')
                cp_vars.append(p)
                if port in cpvars_period:
                    cpvars_period[port].append((priority, p))
                else:
                    cpvars_period[port] = [(priority, p)]

            total_possibilities = total_possibilities + int(math.pow((port_period-port_min_period+1), len(port.get_sorted_queuenrs())))

    model.AddDecisionStrategy(cp_vars, cp_model.CHOOSE_FIRST, cp_model.SELECT_MIN_VALUE)

    solver = cp_model.CpSolver()
    solution_printer = CPSolverPeriod(cpvars_period, testCase, cost_checker, solution_checker,
                                      model,
                                      solver, iterative_cost, iterative_solution, total_possibilities)
    status = solver.SearchForAllSolutions(model, solution_printer)
    print('Number of solutions found: %i' % solution_printer.solution_count())
    print('Best solution at cost: ' + str(solution_printer.lowest_cost))
    print('Best iterative solution at cost: ' + str(iterative_cost))

    subfolder = solution_printer.best_solution.name + '_' + datetime.datetime.now().strftime(
        '%Y-%m-%d_%H-%M') + '_cp_period/'

    # Create output_folder if it doesn't exist yet
    if not os.path.exists(output_folder):
        os.makedirs(output_folder, exist_ok=True)

    # Create subfolder if it doesn't exist yet
    if not os.path.exists(output_folder + subfolder):
        os.makedirs(output_folder + subfolder, exist_ok=True)

    write_windows(output_folder + subfolder + "{}.txt".format('windows_final'),
                  solution_printer.best_solution.switches)

    print('Output Files written to: ' + output_folder + subfolder)

    return  solution_printer.best_solution


class CPOptimizer(object):
    """Finds a solution to the testcase by constructivly generating a good initial solution. Then proceeds to make
    all stream feasible (catch their deadline), by reducing the periods of the ports on their route """

    def run(self, testcase: TestCase, wcdtool_path: str, wcdtool_testcase_subpath: str, output_folder: str,
            options: dict):
        """

        Args:
            testcase (TestCase):  Testcase
            wcdtool_path (str): Path to WCDTool executable
            wcdtool_testcase_subpath (str): Relative path from WCDTool executable to testcase folder
            output_folder (str): Path to output folder
            options (dict): directory of options specified by user

        Returns:
            TestCase object for final solution or None, if no solution found
        """
        cost_checker = CostChecker()

        iterative_optimizer = IterativeOptimizer()
        iterative_solution = iterative_optimizer.run(testcase, wcdtool_path, wcdtool_testcase_subpath, output_folder,
                                                     options)
        iterative_cost = cost_checker.cost(iterative_solution)

        final_solution = None
        if options['cp'] == 'period':
            final_solution = create_cp_model_variablePeriod(testcase, output_folder, cost_checker,
                                           SolutionChecker(wcdtool_path, wcdtool_testcase_subpath,
                                                           options['wcdanalysis_timeout']),
                                           iterative_cost, iterative_solution)
        elif options['cp'] == 'length':
            pass
        elif options['cp'] == 'all':
            pass
        elif options['cp'] == 'bahram':
            final_solution = create_cp_model_bahram(testcase, output_folder, cost_checker,
                                                            SolutionChecker(wcdtool_path, wcdtool_testcase_subpath,
                                                                            options['wcdanalysis_timeout']),
                                                            iterative_cost, iterative_solution)

        return final_solution
