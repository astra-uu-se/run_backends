from typing import *
from ..result import Result
from ..plot import *
from .outputter import Outputter


class PlotOutputter(Outputter):
    plot: Union[None, Plot] = None
    plot_file_path: str = ''

    def __init__(self, plot_file_path: str):
        self.plot_file_path = plot_file_path

    def set_up(self, param_name: Union[None, str]) -> None:
        if param_name is None:
            self.plot: Plot = Plot()
        else:
            self.plot: Plot = Plot(param_name)

    def post_run(self, backend_id: str, backend_name: str, backend_index: int,
                 num_backends: int, instance_index: int, num_instances: int,
                 param: Union[None, Tuple[str, int]],
                 data_file: Union[None, str],
                 result: Result) -> None:
        name: str = ''
        if param is not None:
            name = str(param[1])
        elif data_file is not None:
            name = data_file
        self.plot.add_result(backend_name, name, result)

    def outro(self) -> None:
        self.plot.save_plt(self.plot_file_path)

    def tear_down(self) -> None:
        self.plot = None
