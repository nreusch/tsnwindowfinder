import getopt
import os
import sys

from optimizers.cp_optimizer import CPOptimizer
from optimizers.iterative_optimizer import IterativeOptimizer
from utility import input_parser, config_parser

def get_command_line_options(argv):
    '''
    Get configuration options from command line
    '''
    # Get values from command line
    file_name = argv[0]
    options = {}
    description = '''{} <input> -c <location of config.ini> [-t <wcdanalysis_timeout>]
    [-v] [-a] [-p] [-C <period/length/all/bahram>]'''.format(file_name)

    # Initialize dict
    options['wcdanalysis_timeout'] = 20
    options['visualize'] = False
    options['aggregate'] = False
    options['cp'] = None
    options['pickle'] = False

    # Check if input is specified.
    try:
        options['inputpath'] = argv[1]
    except IndexError:
        print(description)
        sys.exit(2)

    # Define command line options
    args = argv[2:]
    try:
        opts, _ = getopt.getopt(args, 'c:t:vapC:')
    except getopt.GetoptError:
        print(description)
        sys.exit(2)

    # Parse options
    for opt, arg in opts:
        if opt == '-c':
            options['configpath'] = arg
        elif opt == '-t':
            options['wcdanalysis_timeout'] = int(arg)
        elif opt == '-v':
            options['visualize'] = True
        elif opt == '-a':
            options['aggregate'] = True
        elif opt == '-p':
            options['pickle'] = True
        elif opt == '-C':
            options['cp'] = arg
    return options

def main():
    succesful_runs = 0

    # Parse options
    options = get_command_line_options(sys.argv)

    # Parse Config
    wcdtool_path, wcdtool_testcase_subpath = config_parser.parse_config(options['configpath'])

    # Determine Testcases
    test_case_paths = input_parser.find_testcase_filenames(options['inputpath'], recursive=True)

    # Determine Optimizer
    if options['cp'] is not None:
        optimizer = CPOptimizer()
    else:
        optimizer = IterativeOptimizer()

    # for each testcase
    for i, test_case_path in enumerate(test_case_paths):
        # Read testcase
        initial_testCase = input_parser.parse_testcase(test_case_path, wcdtool_path,
                                                       wcdtool_testcase_subpath)

        # Optimize
        if optimizer.run(initial_testCase, wcdtool_path, wcdtool_testcase_subpath, os.path.dirname(test_case_path)+'/output/',  options) is not None:
            succesful_runs += 1

    print('\nSUCCESFUL RUNS: {}/{}'.format(succesful_runs, len(test_case_paths)))


main()
