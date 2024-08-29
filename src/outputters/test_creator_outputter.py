from typing import *
from ..result import Result
from .outputter import Outputter
from json import dump
from datetime import timedelta
from minizinc import Method, Status


class TestCreatorOutputter(Outputter):
    json_data: Dict[str, Any] = []
    json_file_path: Union[None, str] = None

    @property
    def runs(self) -> List[Dict[str, Any]]:
        return self.json_data['runs']

    @property
    def last_run(self) -> Dict[str, Any]:
        return self.json_data['runs'][-1]

    def __init__(self, json_file_path: Union[None, str] = None):
        self.json_file_path = json_file_path

    def set_up(self, param_name: Union[None, str]) -> None:
        self.json_data = dict()

    def intro(self, backends: List[Tuple[str, str]], model_name: str,
              timeout: int, is_csp: bool, vars: List[str],
              param: Union[None, Tuple[str, int]],
              is_data_file_run: bool,
              extra_flags: List[Tuple[str, str]]) -> None:
        self.json_data['backends'] = backends.copy()
        self.json_data['model_name'] = model_name
        self.json_data['timeout'] = timeout
        self.json_data['is_csp'] = is_csp
        self.json_data['vars'] = vars.copy()
        self.json_data['param'] = param
        self.json_data['is_data_file_run'] = is_data_file_run
        self.json_data['extra_flags'] = extra_flags.copy()
        self.json_data['runs'] = []
        self.json_data['num_instances'] = 0
        self.json_data['num_backends'] = len(backends)

    def pre_run(self, backend_id: str, backend_name: str, backend_index: int,
                num_backends: int, instance_index: int, num_instances: int,
                param: Union[None, Tuple[str, int]],
                data_file: Union[None, str]) -> None:
        self.json_data['num_instances'] = num_instances
        if backend_index == 0:
            assert len(self.runs) == instance_index
        else:
            assert len(self.runs) == instance_index + 1
        if backend_index == 0:
            self.runs.append({
              'instance_index': instance_index,
              'param_name': None if param is None else param[0],
              'param_value': None if param is None else param[1],
              'data_file': data_file,
              'results': []})

    def instance(self, results: List[Result],
                 param: Union[None, Tuple[str, int]],
                 data_file: Union[None, str]) -> None:
        pn, pv = param if param is not None else (None, None)
        assert self.last_run['param_name'] == pn
        assert self.last_run['param_value'] == pv
        assert self.last_run['data_file'] == data_file

        results_data = []
        for result in results:
            results_data.append(result.__dict__)
            res_data = results_data[-1]
            assert type(res_data['method']) == Method
            res_data['method'] = res_data['method'].name
            if result._result is None:
                continue
            res_data['_result'] = res_data['_result'].__dict__
            inner = res_data['_result']
            assert 'status' in inner and type(inner['status']) == Status
            inner['status'] = inner['status'].name
            if inner.get('solution', None) is not None:
                inner['solution'] = inner['solution'].__dict__
            if inner.get('statistics', None) is None:
                continue
            stats: Dict[str, Any] = inner['statistics']
            for key, value in stats.items():
                if type(value) == timedelta:
                    stats[key] = value.total_seconds() * 1000

        self.last_run['results'] = results_data

    def outro(self) -> None:
        with open(self.json_file_path, 'w') as json_output_file:
            dump(self.json_data, json_output_file, indent=2)

    def tear_down(self) -> None:
        self.json_data = dict()
