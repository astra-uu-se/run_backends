import minizinc
from typing import List, Tuple, Any, Union, Dict
from datetime import timedelta


class Result:
    method: minizinc.Method = None
    _result: minizinc.Result = None
    _all_solutions: bool = False
    vars: List[Tuple[str, Any]] = None

    @property
    def objective(self) -> Any: return self._result.objective

    @property
    def error(self) -> bool:
        return self._result.status == minizinc.result.Status.ERROR

    @property
    def unknown(self) -> bool:
        return self._result.status == minizinc.result.Status.UNKNOWN

    @property
    def unsat(self) -> bool:
        return self._result.status == minizinc.result.Status.UNSATISFIABLE

    @property
    def sat(self) -> bool:
        return self._result.status == minizinc.result.Status.SATISFIED or (
           not self._all_solutions and
           self.all_solutions and self._result.solution is not None)

    @property
    def all_solutions(self) -> bool:
        return self._result.status == minizinc.result.Status.ALL_SOLUTIONS

    @property
    def optimal_solution(self) -> bool:
        return self._result.status == minizinc.result.Status.OPTIMAL_SOLUTION

    @property
    def is_csp(self) -> bool:
        return self.method == minizinc.Method.SATISFY

    @property
    def is_cop(self) -> bool:
        return (self.method == minizinc.Method.MINIMIZE or
                self.method == minizinc.Method.MAXIMIZE)

    @property
    def timed_out(self) -> bool:
        if self.is_cop:
            return not self.optimal_solution
        if self._all_solutions:
            return not self.all_solutions
        return self.unknown

    @property
    def time(self) -> timedelta:
        if 'time' not in self._result.statistics:
            return timedelta(
              milliseconds=(int(pow(2, 32)) if self.timed_out else 0))
        time: Union[int, timedelta] = self._result.statistics['time']
        return timedelta(milliseconds=time) if isinstance(time, int) else time

    @property
    def has_solution(self) -> bool:
        return len(self._result) > 0

    def __init__(self, method: minizinc.Method, result: minizinc.Result,
                 all_solutions: bool, vars: List[Tuple[str, Any]]):
        self.method: minizinc.Method = method
        self._result: minizinc.Result = result
        self._all_solutions: bool = all_solutions
        self.vars: List[Tuple[str, Any]] = []
        if vars is not None:
            for var in vars:
                try:
                    val = result[var]
                except (KeyError, TypeError):
                    val = None
                if val is None:
                    val = '--'
                self.vars.append((var, val))

    def compare_time(self, other: 'Result') -> int:
        if self.timed_out and other.timed_out:
            return 0
        if other.timed_out:
            return -1
        if self.timed_out:
            return 1
        if self.time < other.time:
            return -1
        if self.time > other.time:
            return 1
        return 0

    def compare_obj(self, other: 'Result') -> int:
        assert self.is_csp == other.is_csp
        if self.is_csp and other.is_csp:
            return 0
        if self.objective is None and other.objective is None:
            return 0
        if other.objective is None:
            return -1
        if self.objective is None:
            return 1
        cmp = self.objective - other.objective
        if self.method == minizinc.Method.MAXIMIZE:
            cmp = -cmp
        return cmp

    def compare_csp(self, other: 'Result') -> int:
        assert self.is_csp and other.is_csp
        if self.unknown and other.unknown:
            return 0
        elif self.unknown != other.unknown:
            return -1 if other.unknown else 1
        return self.compare_time(other)

    def compare_cop(self, other: 'Result') -> int:
        return self.compare_obj(other)

    def compare(self, other: 'Result') -> int:
        if self.method != other.method:
            raise TypeError(
              'Compare expects both Results to have the same method.')
        if self.error and other.error:
            return 0
        elif self.error != other.error:
            return -1 if other.error else 1
        return (self.compare_csp(other) if self.is_csp else
                self.compare_cop(other))

    def all_vars(self) -> Dict[str, Any]:
        sol = {}
        if self._result.solution is not None:
            if isinstance(self._result.solution, list):
                if len(self._result.solution) > 0:
                    sol = next(self._result.solution).__dict__
            else:
                sol = self._result.solution.__dict__
        return {**sol, **{k: v for (k, v) in self.vars}}
