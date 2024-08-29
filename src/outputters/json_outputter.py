from typing import List, Dict, Any, Union, Tuple
from ..result import Result
from .outputter import Outputter
from json import dump


class JsonOutputter(Outputter):
    json_data: List[Dict[str, Any]] = []
    json_file_path: Union[None, str] = None

    def __init__(self, json_file_path: Union[None, str] = None):
        self.json_file_path = json_file_path

    def set_up(self, param_name: Union[None, str]) -> None:
        self.json_data = []

    def post_run(self, backend_id: str, backend_name: str, backend_index: int,
                 num_backends: int, instance_index: int, num_instances: int,
                 param: Union[None, Tuple[str, int]],
                 data_file: Union[None, str],
                 result: Result) -> None:
        self.json_data.append({
          'backend_jd': backend_id,
          'backend_name': backend_name,
          'instance_index': instance_index,
          'data_file': data_file,
          'param': None if param is None else {param[0]: param[1]},
          'objective': result.objective,
          'error': result.error,
          'unknown': result.unknown,
          'unsat': result.unsat,
          'sat': result.sat,
          'all_solutions': result.all_solutions,
          'optimal_solution': result.optimal_solution,
          'is_csp': result.is_csp,
          'is_cop': result.is_cop,
          'timed_out': result.timed_out,
          'time': int(result.time.total_seconds() * 1000),
          'has_solution': result.has_solution,
          'vars': result.all_vars()
        })

    def outro(self) -> None:
        with open(self.json_file_path, 'w') as json_output_file:
            dump({'runs': self.json_data}, json_output_file, indent=2)

    def tear_down(self) -> None:
        self.json_data = []
