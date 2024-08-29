from typing import *
from ..result import Result


class Outputter:
    def set_up(self, param_name: Union[None, str]) -> None:
        pass

    def intro(self, backends: List[Tuple[str, str]], model_name: str,
              timeout: int, is_csp: bool, vars: List[str],
              param: Union[None, Tuple[str, int]],
              is_data_file_run: bool,
              extra_flags: List[Tuple[str, str]]) -> None:
        pass

    def pre_run(self, backend_id: str, backend_name: str, backend_index: int,
                num_backends: int, instance_index: int, num_instances: int,
                param: Union[None, Tuple[str, int]],
                data_file: Union[None, str]) -> None:
        pass

    def post_run(self, backend_id: str, backend_name: str, backend_index: int,
                 num_backends: int, instance_index: int, num_instances: int,
                 param: Union[None, Tuple[str, int]],
                 data_file: Union[None, str],
                 result: Result) -> None:
        pass

    def instance(self, results: List[Result],
                 param: Union[None, Tuple[str, int]],
                 data_file: Union[None, str]) -> None:
        pass

    def outro(self) -> None:
        pass

    def tear_down(self) -> None:
        pass

    def exception(self, e: Exception) -> None:
        pass
