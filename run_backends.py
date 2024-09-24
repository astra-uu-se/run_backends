import minizinc
import logging
from typing import List
from argparse import ArgumentParser, ArgumentTypeError
from glob import glob
from os import path
from json import load
from src.aux import set_minizinc_driver_path, filter_minizinc_backends
from src.outputters.outputter import Outputter
from src.outputters.json_outputter import JsonOutputter
from src.outputters.log_outputter import LogOutputter
# from src.outputters.plot_outputter import PlotOutputter
from src.outputters.tex_outputter import TexOutputter
from src.backend_runner import BackendRunner
from src.str_to_timedelta import StrToTimedelta

if __name__ == '__main__':
    def file_path(rel_path: str) -> None:
        abs_path = path.abspath(rel_path)
        if path.isfile(abs_path):
            return abs_path
        raise ArgumentTypeError(f"file_path: {rel_path} is not a valid path.")

    def dir_path(rel_path: str) -> None:
        abs_path = path.abspath(rel_path)
        if path.isdir(abs_path):
            return abs_path
        raise ArgumentTypeError(f"dir_path: {rel_path} is not a valid path.")

    def creatable_file(file_path: str) -> None:
        abs_path = path.abspath(file_path)
        if path.isfile(abs_path) or path.isdir(path.dirname(abs_path)):
            return abs_path
        raise ArgumentTypeError(
            f"creatable_file: {file_path} is not a valid path.")

    def is_int(s: str) -> bool:
        try:
            int(s)
            return True
        except ValueError:
            return False

    json_config_path = path.join(path.dirname(path.realpath(__file__)),
                                 'config.json')

    parser = ArgumentParser(
        description='Runs the MiniZinc CLI on a MiniZinc model for a set of '
        'instances for a set of backends (solvers) and outputs the results in '
        'a LaTeX table, where each best performing solver is highlighted in '
        'the LaTeX table')

    parser.add_argument(dest='model', metavar='<model>.mzn', type=file_path,
                        help='The MiniZinc model file.')

    parser.add_argument('-t', '--timeout', dest='timeout', metavar='<timeout>',
                        type=str, nargs='*',
                        help='The timeout in milliseconds or as one or more '
                        'space separated time units for each instance. For '
                        'example, "1h 2m03s 100ms".')

    parser.add_argument('--json-config', dest='json_config_path',
                        metavar='<json file>', type=file_path,
                        default=json_config_path,
                        help='The JSON configuration file for populating '
                        'default values for this script.')

    data_group = parser.add_mutually_exclusive_group()
    data_group.add_argument('-r', '--param', dest='param',
                            metavar=('<param>', '<start>', '<stop>', '<inc>'),
                            nargs=4, type=str,
                            help='The range the model is to be run on, where '
                            'parameter <param> is initially set to <start>, '
                            'then iteratively modifies <param> adding <inv> '
                            'until <param> reaches (or surpasses) <stop>. '
                            'Note that <inc> can be a negative value. '
                            'This flag is mutually exclusive with -d (--data)')

    data_group.add_argument('-d', '--data', dest='data_files',
                            metavar='<data file>.{dzn, json}', nargs='*',
                            type=str, help='The dzn or JSON instance file(s) '
                            'to run the model on. This flag is mutually '
                            'exclusive with -r (--param).')

    parser.add_argument('-o', '--output', dest='output',
                        metavar='<output file>', type=creatable_file,
                        help='The LaTeX file to write the output to; this '
                        'creates the file if it does not already exist, '
                        'otherwise the results are appended to the end of the '
                        'file. Note that this does not initially clear any '
                        'previous text/data of <output file>.')

    parser.add_argument('--json-output', dest='json_output',
                        metavar='<output file>', type=creatable_file,
                        help='The file to write statistics of the runs to. '
                        'For each found solution to any instance, outputs '
                        'data about the solver, time, and output variables. '
                        'Creates file <output file> if it does not already '
                        'exist.')

    parser.add_argument('--vars', dest='vars', metavar='<var>', type=str,
                        nargs='+', help='The name of each variable that is '
                        'to be included in the output LaTeX table. Note that '
                        'the objective value is included in the LaTeX table '
                        'automatically.')

    parser.add_argument('--backends', dest='backends', metavar='<backend>',
                        type=str, nargs='+', help='The set of solvers to run '
                        'the instances on.')

    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                        help='Enables verbose logging to stderr with '
                        'information about the runs.')

    parser.add_argument('--log-output', dest='log_output',
                        metavar='<output file>', type=creatable_file,
                        help='Writes all log messages also to the file '
                        '<output file>. Creates file <output file> if it does '
                        'not already exist.')

    parser.add_argument('--minizinc-path', dest='driver_path', type=dir_path,
                        help='The path to the MiniZinc CLI.')

    parser.add_argument('--no-header', dest='no_header', action='store_true',
                        help='Skip generating the latex table header.')

    parser.add_argument('--extra', dest='extra',
                        metavar='<flag 1> <flag 2> ...', type=str,
                        help='The extra flags without leading dashes that are '
                        'passed to the MiniZinc CLI.')

    # parser.add_argument('--plot-output', dest='plot_output',
    #                     metavar='<output file>', type=creatable_file,
    #                     help='saves the results also as a png plot using ' +
    #                     'matplotlib.')

    imported_test_creator = False
    try:
        from src.outputters.test_creator_outputter import TestCreatorOutputter
        parser.add_argument('--create-tests', dest='create_tests',
                            metavar='<output file>', type=creatable_file,
                            help='The file to write test JSON of the runs to; '
                            'this overwrites the contents of <output file>.')
        imported_test_creator = True
    except ImportError:
        pass

    with open(json_config_path, 'r') as json_file:
        config = load(json_file)

    if 'driver_path' in config:
        set_minizinc_driver_path(config['driver_path'])

    if 'backends' in config:
        _, backends = filter_minizinc_backends(config['backends'])
        parser.epilog = ('The default backends of this script are: ' +
                         ', '.join((b_name for _, b_name in backends)) +
                         '. To list more information on all backends and ' +
                         'their underlying solving technologies, run ' +
                         f'{minizinc.default_driver._executable} --solvers".')

    args = parser.parse_args()

    if args.driver_path is not None:
        set_minizinc_driver_path(args.driver_path)
    if args.timeout is None:
        args.timeout = config.get('timeout', None)
    try:
        timeout = StrToTimedelta.parse(args.timeout)
    except ArgumentTypeError as e:
        parser.error(e.args[0])
    if args.backends is None:
        args.backends = config.get('backends', None)

    backend_config = config.get('backend_config', dict())

    outputters: List[Outputter] = [
      TexOutputter(no_header=args.no_header, tex_file_path=args.output),
      LogOutputter(logging.INFO if args.verbose else logging.WARNING,
                   args.log_output)
    ]

    if args.json_output is not None:
        outputters.append(JsonOutputter(args.json_output))

    if imported_test_creator and args.create_tests is not None:
        outputters.append(TestCreatorOutputter(args.create_tests))

    # if args.plot_output is not None:
    #     outputters.append(PlotOutputter(args.plot_output))

    backend_runner = BackendRunner(
        args.model,
        timeout.total_seconds() * 1000,
        vars=args.vars,
        backends=args.backends,
        outputters=outputters,
        extra=args.extra,
        backend_config=backend_config)

    if args.param is not None:
        if any((not is_int(p) for p in args.param[1:])):
            parser.error("<start>, <stop>, and <inc> must be integers.")

        param_name = args.param[0]
        start, stop, increment = tuple((int(p) for p in args.param[1:]))

        if start < stop and increment <= 0:
            parser.error(
                f"the non-increasing param {param_name} is not lower bounded.")

        if start > stop and increment >= 0:
            parser.error(
                f"the non-decreasing param {param_name} is not upper bounded.")

        backend_runner.run_with_param(param_name, start, stop, increment)
    elif args.data_files is not None:
        data_files = []
        seen_data_files = set()
        for data_file in (fp for glob_list in args.data_files
                          for fp in glob(glob_list)):
            if data_file in seen_data_files:
                continue
            data_files.append(data_file)
            seen_data_files.add(data_file)
        backend_runner.run_with_data_files(data_files)
    else:
        backend_runner.run()
