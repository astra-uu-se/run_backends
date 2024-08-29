
from typing import *
import minizinc
from ..backend_runner import BackendRunner
from ..result import Result


class BackendRunnerExt(BackendRunner):
    next_instance: Callable = None
    next_result: Callable = None

    def set_up(self, instance: minizinc.Instance, result: Result) -> None:
        self.next_instance = instance
        self.next_result = result

    def _get_instance(self, backend_id: str,
                      data_file: Union[None, str] = None) -> minizinc.Instance:
        return self.next_instance()

    def _get_result(self, backend_id: str, instance: minizinc.Instance,
                    param: Union[None, Tuple[str, int]] = None) -> Result:
        return self.next_result()
