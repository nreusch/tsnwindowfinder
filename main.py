import os
import sys

from optimizers import iterative_optimizer
from optimizers.iterative_optimizer import IterativeOptimizer
from utility import input_parser, config_parser


def main():
    succesful_runs = 0

    # Parse Config
    wcdtool_path, wcdtool_testcase_subpath = config_parser.parse_config("config.ini")

    # Determine Testcases
    testcases_path = sys.argv[1]
    test_case_paths = input_parser.find_testcase_filenames(testcases_path, recursive=True)

    optimizer = IterativeOptimizer()

    # for each testcase
    for i, test_case_path in enumerate(test_case_paths):
        # Read testcase
        initial_testCase = input_parser.parse_testcase(test_case_path, wcdtool_path,
                                                       wcdtool_testcase_subpath)

        # Optimize
        p = 0.95  # period adjustment percentage
        if optimizer.run(initial_testCase, wcdtool_path, wcdtool_testcase_subpath, os.path.dirname(test_case_path)+'/output/',  p) is not None:
            succesful_runs += 1

    print('\nSUCCESFUL RUNS: {}/{}'.format(succesful_runs, len(test_case_paths)))


main()
