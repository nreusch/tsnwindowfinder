import sys

from optimizers.iterative_optimizer import IterativeOptimizer
from utility import input_parser, config_parser


def main():
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
        optimizer.run(initial_testCase, wcdtool_path, wcdtool_testcase_subpath, p)


main()
