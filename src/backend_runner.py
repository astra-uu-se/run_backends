import minizinc
import logging
from typing import List, Dict, Any, Union, Tuple, Optional
from datetime import timedelta
from src.result import Result
from src.outputters.outputter import Outputter
from .aux import filter_minizinc_backends


class BackendRunner:
    logger: logging.Logger = None
    model_files: List[str] = []
    timeout: int = 0
    vars: List[str] = []
    backends: List[Tuple[str, str]] = []
    outputters: List[Outputter] = []
    extra: Dict[str, Union[str, bool]] = {}

    def get_extra(self, backend_id: str) -> Dict[str, str]:
        return dict(self.backend_config.get(backend_id, {}).get('extra', {}),
                    **self.extra)

    def __init__(self, model_files: Optional[List[str]], timeout: int,
                 vars: List[str] = [], backends: List[str] = None,
                 outputters: List[Outputter] = [],
                 extra: List[str] = [],
                 backend_config: Dict[str, Dict[str, Any]] = {}):
        self.logger = logging.getLogger('BackendRunner')
        self.model_files = model_files
        self.timeout = timeout
        self.outputters = outputters
        self.vars = [] if vars is None else vars
        self.extra = self.parse_extra(extra)
        self.backend_config = self.parse_backend_config(backend_config)

        if not isinstance(backends, list) or len(backends) == 0:
            self.logger.error("No backends submitted")
            exit(1)

        erronous_backends, self.backends = filter_minizinc_backends(backends)

        if len(erronous_backends) > 0:
            self.logger.error("Could not load the inputted backend(s): {" +
                              ', '.join(erronous_backends) + '}')
            exit(1)

    def parse_extra(self, extra: List[str]) -> Dict[str, Union[bool, str]]:
        if extra is None or len(extra) == 0:
            return {}
        extra_flags: Dict[str, Union[bool, str]] = {}
        i = 0

        while i < len(extra):
            flag = extra[i]
            i += 1
            value = True
            if i < len(extra) and not extra[i].startswith('-'):
                value = extra[i]
                i += 1
            extra_flags[flag] = value

        return extra_flags

    def parse_backend_config(self, backend_config: Dict[str, Dict[str, Any]]
                             ) -> Dict[str, Dict[str, Any]]:
        for config in backend_config.values():
            if 'extra' not in config:
                continue
            for flag, val in config['extra'].items():
                if type(val) not in {int, str, bool}:
                    raise TypeError(
                      "Backend config values must be of type int, str, or "
                      "bool")
                config['extra'][flag] = str(val)
        return backend_config

    def _get_instance(self, backend_id: str,
                      data_file: Optional[str] = None) -> minizinc.Instance:
        try:
            model = minizinc.Model(self.model_files)

            if data_file is not None:
                model.add_file(data_file)

            solver = minizinc.Solver.lookup(backend_id)
            return minizinc.Instance(solver, model)
        except Exception as e:
            for outputter in self.outputters:
                outputter.exception(e)
            exit(1)

    def _get_result(self, backend_id: str, instance: minizinc.Instance,
                    param: Optional[Tuple[str, int]] = None) -> Result:
        try:
            if isinstance(param, tuple):
                instance[param[0]] = param[1]
            kwargs = self.get_extra(backend_id)
            if '--all-solutions' in kwargs:
                kwargs['all_solutions'] = kwargs.pop('--all-solutions')
            if '--intermediate' in kwargs:
                kwargs['intermediate_solutions'] = kwargs.pop('--intermediate')
            kwargs['timeout'] = timedelta(milliseconds=self.timeout)
            mzn_result = instance.solve(**kwargs)
            return Result(instance.method, mzn_result,
                          '--all-solutions' in self.get_extra(backend_id),
                          self.vars)
        except Exception as e:
            for outputter in self.outputters:
                outputter.exception(e)
            exit(1)

    def _run_single(self, generate_intro: bool, backend_id: str,
                    backend_name: str, backend_index: int, instance_index: int,
                    num_instances: int,
                    param: Optional[Tuple[str, int]] = None,
                    data_file: Optional[str] = None) -> Result:
        instance = self._get_instance(backend_id, data_file=data_file)

        if generate_intro:
            backend_extra_flags = {
              id: self.backend_config.get(id, {}).get('extra', {})
              for id, _ in self.backends}
            for outputter in self.outputters:
                outputter.intro(
                  self.backends, self.model_files, self.timeout,
                  instance.method == minizinc.Method.SATISFY,
                  self.vars, param[0] if param is not None else None,
                  is_data_file_run=data_file is not None,
                  extra_flags=self.extra,
                  backend_extra_flags=backend_extra_flags)

        for outputter in self.outputters:
            outputter.pre_run(
              backend_id, backend_name, backend_index, len(self.backends),
              instance_index, num_instances, param, data_file)

        result = self._get_result(backend_id, instance, param=param)

        for outputter in self.outputters:
            outputter.post_run(
              backend_id, backend_name, backend_index, len(self.backends),
              instance_index, num_instances, param, data_file, result)

        return result

    def run(self) -> None:
        results: List[Result] = []

        for outputter in self.outputters:
            outputter.set_up(None)

        for b_index, (b_id, b_name) in enumerate(self.backends):
            results.append(self._run_single(b_index == 0, b_id,
                                            b_name, b_index, 0, 1))

        for outputter in self.outputters:
            outputter.instance(results, None, None)

        for outputter in self.outputters:
            outputter.outro()

        for outputter in self.outputters:
            outputter.tear_down()

    def run_with_param(self, param_name, start, stop, increment) -> None:
        increment = 1 if start == stop else increment
        stop = (stop - 1) if increment < 0 else (stop + 1)

        for outputter in self.outputters:
            outputter.set_up(param_name)

        values = list(range(start, stop, increment))
        for instance_index, param_value in enumerate(values):
            param = (param_name, param_value)
            results: List[Result] = []
            for b_index, (b_id, b_name) in enumerate(self.backends):
                results.append(self._run_single(
                  instance_index == 0 and b_index == 0,
                  b_id, b_name, b_index, instance_index, len(values),
                  param=param))

            if len(results) == 0:
                continue

            for outputter in self.outputters:
                outputter.instance(results, param, None)

        for outputter in self.outputters:
            outputter.outro()

    def run_with_data_files(self, data_files) -> None:
        for outputter in self.outputters:
            outputter.set_up(None)

        for instance_index, data_file in enumerate(data_files):
            results: List[Result] = []
            for b_index, (b_id, b_name) in enumerate(self.backends):
                results.append(self._run_single(
                  instance_index == 0 and b_index == 0,
                  b_id, b_name, b_index, instance_index, len(data_files),
                  data_file=data_file))

            if len(results) == 0:
                continue

            for outputter in self.outputters:
                outputter.instance(results, None, data_file)

        for outputter in self.outputters:
            outputter.outro()

        for outputter in self.outputters:
            outputter.tear_down()
