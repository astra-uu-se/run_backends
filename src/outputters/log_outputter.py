from typing import *
from ..result import Result
from .outputter import Outputter
import logging
from sys import stderr


class LogOutputter(Outputter):
    logger: logging.Logger = None

    def __init__(self, level: int, log_file_path: Union[None, str] = None):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(level)
        self.logger.propagate = False

        formatter = logging.Formatter('%(message)s')
        for handler in self.logger.handlers:
            handler.close()
        self.logger.handlers.clear()

        stderr_handler = logging.StreamHandler(stderr)
        stderr_handler.setLevel(level)
        stderr_handler.setFormatter(formatter)
        self.logger.addHandler(stderr_handler)

        if log_file_path is not None:
            with open(log_file_path, 'a+') as _:
                pass
            file_handler = logging.FileHandler(log_file_path)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(logging.Formatter(
              '%(asctime)s | %(message)s', '%Y-%m-%d %H:%M:%S'))
            self.logger.addHandler(file_handler)

    def intro(self, backends: List[Tuple[str, str]], model_name: str,
              timeout: int, is_csp: bool, vars: List[str] = [],
              param: Union[None, Tuple[str, int]] = None,
              is_data_file_run: bool = False,
              extra_flags: List[Tuple[str, str]] = []) -> None:
        entries = [
          ('model', model_name),
          ('problem type', ('Constraint Satisfaction Problem (CSP)' if is_csp
                            else 'Constrained Optimisation Problem (COP)')),
          ('timeout', f'{timeout}ms')
        ]
        label_padding = 2 + max((len(label) for label, _ in entries),
                                default=0)
        for label, v in entries:
            self.logger.info(f'{label}:'.ljust(label_padding) + v)

        if len(extra_flags) == 0:
            return

        self.logger.info(f'extra flags ({len(extra_flags)}):')
        flag_padding = 1 + max((len(f) for f, _ in extra_flags),
                               default=0)

        for flag, val in extra_flags:
            self.logger.info(
              f'  flag: ' + f'{flag}:'.ljust(flag_padding) + f'value: {val}')

    def pre_run(self, backend_id: str, backend_name: str, backend_index: int,
                num_backends: int, instance_index: int, num_instances: int,
                param: Union[None, Tuple[str, int]],
                data_file: Union[None, str]) -> None:
        if backend_index == 0:
            header_suffix = (
              '' if num_instances == 0
              else f' ({instance_index + 1} of {num_instances})')

            if param is not None:
                self.logger.info(
                  f'instance: {param[0]} = {param[1]}{header_suffix}')
            elif data_file is not None:
                self.logger.info(f'instance: {data_file}{header_suffix}')
        run_suffix = ('' if num_backends == 0
                      else f' ({backend_index + 1} of {num_backends})')

        self.logger.info(f'  backend: {backend_name}{run_suffix}')

    def post_run(self, backend_id: str, backend_name: str, backend_index: int,
                 num_backends: int, instance_index: int, num_instances: int,
                 param: Union[None, Tuple[str, int]],
                 data_file: Union[None, str],
                 result: Result) -> None:
        padding = '    '
        for var, val in result.vars:
            self.logger.info(f'{padding}{var}: {val}')
        if result.timed_out:
            time = 't/o'
        else:
            time = f'{int(result.time.total_seconds() * 1000)}ms'
        self.logger.info(f'{padding}time: {time}')
        if result.is_csp:
            if result.sat:
                s = 'SAT'
            elif result.unsat:
                s = 'UNSAT'
            else:
                s = 'UNKNOWN'
            self.logger.info(f'{padding}{s}')
        else:
            if result.optimal_solution:
                result_suffix = ' (proven optimum)'
            else:
                result_suffix = ''
            self.logger.info(
                f'{padding}obj:  {result.objective}{result_suffix}')

    def exception(self, e: Exception) -> None:
        self.logger.exception(e)
