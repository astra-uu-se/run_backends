from typing import List, Tuple, Union, Dict
from .result import Result
import logging
import matplotlib.pyplot as plt
from math import log10


def int_to_marker(i: int) -> str:
    return ['*', 'o', 'v', 's', '+', 'x', 'D', '1', '^', '<', '>', '.', 'd'][
      min(0, max(12, i))]


class PlotLine:
    label: str
    marker: str
    data: List[Tuple[str, Result]]

    def __init__(self, label: str, marker: str):
        self.label: str = label
        self.marker: str = marker
        self.data: List[Tuple[str, Result]] = []

    @property
    def x_vals(self) -> List[str]:
        return [instance_name for instance_name, _ in self.data]

    @property
    def y_vals(self) -> List[Union[None, float]]:
        if len(self.data) == 0:
            return []
        if self.data[0][1].is_csp:
            return [None if r.unknown else r.time.total_seconds()
                    for _, r in self.data]
        return [None if r.unknown else r.objective for _, r in self.data]

    @property
    def min_y_val(self, default: float = float('+inf')) -> float:
        return min((v for v in self.y_vals if v is not None), default=default)

    @property
    def max_y_val(self, default: float = float('-inf')) -> float:
        return max((v for v in self.y_vals if v is not None), default=default)

    def add_result(self, instance: str, result: Result) -> None:
        self.data.append((instance, result))


class Plot:
    xlabel: str = ''
    plot_lines: Dict[str, PlotLine]

    def __init__(self, xlabel: str = '') -> None:
        self.xlabel: str = xlabel
        self.plot_lines: Dict[str, PlotLine] = dict()

    @property
    def min_y_val(self, default: float = float('+inf')) -> float:
        return min((pl.min_y_val for pl in self.plot_lines.values()),
                   default=default)

    @property
    def max_y_val(self, default: float = float('-inf')) -> float:
        return max((pl.max_y_val for pl in self.plot_lines.values()),
                   default=default)

    @property
    def ylabel(self) -> str:
        result: Union[Result, None] = next(
            (pl.data[0][1]
             for pl in self.plot_lines.values() if len(pl.data) > 0))
        if result is None:
            return ''
        if result.is_csp:
            return 'time (s)'
        return 'objective'

    def add_result(self, label: str, instance: str, result: Result) -> None:
        if label not in self.plot_lines:
            self.plot_lines[label] = PlotLine(
              label, int_to_marker(len(self.plot_lines)))
        self.plot_lines[label].add_result(instance, result)

    def save_plt(self, plot_filename: str) -> None:
        if len(self.plot_lines) == 0:
            return
        plt.rcParams['figure.figsize'] = (10, 4)
        if len(self.xlabel) > 0:
            plt.xlabel(self.xlabel, fontsize=10)
        if len(self.ylabel) > 0:
            plt.ylabel(self.ylabel, fontsize=10)

        for plot_line in sorted(self.plot_lines.values(),
                                key=lambda pl: pl.label):
            logging.info(f'label: {plot_line.label}')
            logging.info(f'x_vals: {plot_line.x_vals}')
            logging.info(f'y_vals: {plot_line.y_vals}')
            plt.plot(
                plot_line.x_vals,
                plot_line.y_vals,
                label=plot_line.label,
                marker=plot_line.marker,
                linestyle='-'
            )
        log_max_y_val = log10(max(0.01, self.max_y_val))
        log_min_y_val = log10(max(0.01, self.min_y_val))
        if log_max_y_val - log_min_y_val > 2:
            plt.yscale('log')
        plt.legend(ncol=2)
        plt.savefig(plot_filename, bbox_inches=0, pad_inches=0)
