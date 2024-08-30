from typing import Union, List, Tuple
from ..result import Result
from .outputter import Outputter
from datetime import datetime
from os import path


def result_to_output(result: Result, best_result: Result,
                     single_result: bool,
                     monospace_font) -> str:
    em_dash = '-' if monospace_font else '--'
    separator = ',' if monospace_font else ', '

    if result.error:
        return f'ERR\t&\t{em_dash}'

    s = ''
    if result.vars is not None and len(result.vars) > 0:
        s = separator.join((str(val) for _, val in result.vars))
    elif result.is_csp:
        s = 'SAT' if result.sat else ('UNSAT' if result.unsat else em_dash)

    if result.is_cop:
        s = s + ((separator * min(len(s), 1)) +
                 (em_dash if not result.has_solution else
                 (f'\\textbf{{{result.objective}}}'
                  if result.compare(best_result) <= 0 and not single_result
                  else f'{result.objective}')))

    time = 't/o'
    if not result.timed_out:
        ms = int(result.time.total_seconds() * 1000)
        time = (f'\\textbf{{{ms}}}'
                if result.compare_time(best_result) <= 0 and not single_result
                else f'{ms}')

    return f'{s}\t&\t{time}'


class TexOutputter(Outputter):
    no_header: bool = False
    tex_file_path: Union[None, str] = None
    monospace_font: bool = True

    def __init__(self, no_header: bool = False,
                 tex_file_path: Union[None, str] = None,
                 monospace_font: bool = True):
        self.no_header = no_header
        self.tex_file_path = tex_file_path
        self.monospace_font = monospace_font

    def print(self, s: str) -> None:
        if self.tex_file_path is None:
            print(s)
            return
        with open(self.tex_file_path, 'a+') as output_file:
            output_file.write(s + '\n')

    def intro(self, backends: List[Tuple[str, str]], model_name: str,
              timeout: int, is_csp: bool, vars: List[str] = [],
              param: Union[None, Tuple[str, int]] = None,
              is_data_file_run: bool = False,
              extra_flags: List[Tuple[str, str]] = []) -> None:

        assert len(backends) > 0
        lines = [
            '% table generation started ' +
            datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
            f'% timeout: {timeout}ms',
            'Backend'
        ]

        lines += [f'\t& \\multicolumn{{2}}{{c}}{{{backend_name}}}'
                  for _, backend_name in backends]
        # Backend header rule line
        lines.append('\\\\'),
        lines += [f'\t\\cmidrule(lr){{{2 * i}-{(2 * i) + 1}}}'
                  for i in range(1, len(backends) + 1)]

        # Instance header line (instance or param = value)
        instance_caption = ''
        if param is not None:
            assert isinstance(param[0], str)
            instance_caption = '\\texttt{' + param[0].replace('_', '\\_') + '}'
        elif is_data_file_run:
            instance_caption = 'instance'
        lines.append(instance_caption)

        separator = ',' if self.monospace_font else ', '

        status = separator.join('\\texttt{' + name.replace('_', '\\_') + '}'
                                for name in vars)
        if not is_csp:
            status += (separator * min(len(status), 1)) + '\\texttt{obj}'
        elif len(status) == 0:
            status = '\\texttt{status}'
        lines += [f'\t& {status} & time' for _ in range(len(backends))]

        lines.append('\\\\\\midrule')

        lines = [line.rstrip() for line in lines]

        if self.no_header:
            lines = [line if line.startswith('%') else f'% {line}'
                     for line in lines]

        self.print('\n'.join(lines))

    def instance(self, results: List[Result],
                 param: Union[None, Tuple[str, int]],
                 data_file: Union[None, str]) -> None:
        if len(results) == 0:
            return

        lines: List[str] = []

        if param is not None:
            lines.append(f'${param[1]}$')
        elif data_file is not None:
            file_name = path.splitext(path.split(data_file)[1])[0]
            lines.append(file_name.replace('_', '\\_'))

        best_r: Union[None, Result] = None
        for r in results:
            if best_r is None:
                best_r = r
            if r.compare_obj(best_r) < 0:
                best_r = r
            elif r.compare_obj(best_r) == 0 and r.compare_time(best_r) < 0:
                best_r = r

        lines += ['\t& ' + result_to_output(r, best_r, len(results) == 1,
                                            self.monospace_font)
                  for r in results]

        lines.append('\\\\')

        self.print('\n'.join(lines))

    def outro(self) -> None:
        self.print('% table generation ended ' +
                   datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
