from typing import List
import unittest
import minizinc
from ..result import Result
from .backend_runner_ext import BackendRunnerExt
from json import loads
from ..outputters.json_outputter import JsonOutputter
from ..outputters.log_outputter import LogOutputter
from ..outputters.tex_outputter import TexOutputter
from os import path
from glob import glob
import logging
from datetime import timedelta


class Solution:
    def __init__(self, d: dict):
        self.__dict__ = d


class BackendRunnerTester(unittest.TestCase):
    backend_runner: BackendRunnerExt = None
    instance_index = 0
    backend_index = 0
    json_data_files: List[str] = []
    json_data = dict()

    @property
    def root(self):
        return path.dirname(path.dirname(path.dirname(path.abspath(__file__))))

    @property
    def backends(self):
        return self.json_data['backends']

    @property
    def instances(self):
        return self.json_data['runs']

    def next_instance(self):
        instance = minizinc.Instance(None, None, None)
        self.assertIn('runs', self.json_data)
        self.assertGreater(len(self.json_data['runs']), 0)
        self.assertGreaterEqual(self.instance_index, 0)
        self.assertLess(self.instance_index, len(self.json_data['runs']))
        self.assertIn('results', self.json_data['runs'][self.instance_index])
        self.assertGreater(
          len(self.json_data['runs'][self.instance_index]['results']),
          0)
        self.assertIn(
          'method',
          self.json_data['runs'][self.instance_index]['results'][0])
        self.assertTrue(
          type(self.json_data['runs'][self.instance_index][
            'results'][0]['method']),
          str)
        instance._method_cache = minizinc.Method[
          self.json_data['runs'][self.instance_index]['results'][0]['method']]
        return instance

    def next_result(self):
        self.assertIn('runs', self.json_data)
        self.assertGreater(len(self.json_data['runs']), 0)
        self.assertGreaterEqual(self.instance_index, 0)
        self.assertLess(self.instance_index, len(self.json_data['runs']))
        self.assertIn('results', self.json_data['runs'][self.instance_index])
        self.assertGreater(
          len(self.json_data['runs'][self.instance_index]['results']),
          0)
        self.assertGreaterEqual(self.backend_index, 0)
        self.assertLess(
          self.backend_index,
          len(self.json_data['runs'][self.instance_index]['results']))

        result_data = self.json_data['runs'][self.instance_index][
          'results'][self.backend_index]

        self.assertIn('method', result_data)
        self.assertIn('_result', result_data)
        self.assertIn('_all_solutions', result_data)
        self.assertIn('vars', result_data)
        self.assertIn('status', result_data['_result'])
        self.assertIn('solution', result_data['_result'])
        self.assertIn('statistics', result_data['_result'])

        stats = result_data['_result']['statistics']

        for k in ['flatTime', 'time', 'initTime', 'solveTime']:
            if k in stats:
                self.assertIn(type(stats[k]), {int, float})
                stats[k] = timedelta(milliseconds=stats[k])

        self.backend_index += 1
        if self.backend_index == len(self.backends):
            self.backend_index = 0
            self.instance_index += 1

        solution = (None if result_data['_result']['solution'] is None else
                    Solution(result_data['_result']['solution']))

        return Result(
          minizinc.Method[result_data['method']],
          minizinc.Result(
            minizinc.Status[result_data['_result']['status']],
            solution,
            result_data['_result']['statistics']),
          result_data['_all_solutions'],
          self.json_data['vars'])

    def init_test_file(self, json_file_name: str):
        with open(json_file_name) as json_file:
            self.json_data = loads(json_file.read())

    def init_backend_runner(self, json_file_name: str):
        self.init_test_file(json_file_name)
        model_name = self.json_data['model_name']
        timeout = self.json_data['timeout']
        vars = self.json_data['vars']
        backends = [t[0] for t in self.json_data['backends']]
        model_file_name = path.split(model_name)[1]
        file_name = path.splitext(model_file_name)[0]

        json_file_path = path.join(
          self.root, 'test_results', f'{file_name}.json')
        open(json_file_path, 'w').close()
        json_outputter = JsonOutputter(json_file_path)
        self.assertEqual(json_outputter.json_file_path, json_file_path)

        log_file_path = path.join(
          self.root, 'test_results', f'{file_name}.txt')
        open(log_file_path, 'w').close()
        log_outputter = LogOutputter(logging.DEBUG, log_file_path)

        tex_file_path = path.join(
          self.root, 'test_results', f'{file_name}.tex')
        open(tex_file_path, 'w').close()
        tex_outputter = TexOutputter(False, tex_file_path)
        self.assertEqual(tex_outputter.tex_file_path, tex_file_path)

        self.backend_runner = BackendRunnerExt(
          model_name, timeout, vars, backends,
          [json_outputter, log_outputter, tex_outputter])

        self.instance_index = 0
        self.backend_index = 0
        self.backend_runner.set_up(self.next_instance, self.next_result)

    def setUp(self):
        json_file_glob_path = path.join(self.root, 'test_data', '*.json')
        self.json_data_files = [
          data_file for data_file in glob(json_file_glob_path)]

    def test_all(self):
        for i, json_file in enumerate(self.json_data_files):
            with self.subTest(instance=i):
                self.init_backend_runner(json_file)

                self.assertIn('runs', self.json_data)
                self.assertEqual(type(self.json_data['runs']), list)
                self.assertTrue(len(self.json_data['runs']) > 0)
                first_run = self.json_data['runs'][0]

                for run in self.json_data['runs']:
                    self.assertIn('data_file', run)
                    self.assertIn('param_name', run)
                    self.assertIn('param_value', run)

                has_data_file = first_run['data_file'] is not None
                has_param = first_run['param_name'] is not None
                self.assertFalse(has_data_file and has_param)
                if has_data_file:
                    for run in self.json_data['runs']:
                        self.assertIsNotNone(run['data_file'], run)
                    self.backend_runner.run_with_data_files(
                      [r['data_file'] for r in self.json_data['runs']])
                elif has_param:
                    for run in self.json_data['runs']:
                        self.assertIsNotNone(run['param_name'], run)
                        self.assertIsNotNone(run['param_value'], run)
                    param_name = first_run['param_name']
                    start = first_run['param_value']
                    stop = self.json_data['runs'][-1]['param_value']
                    increment = 1
                    if len(self.json_data['runs']) > 1:
                        increment = (
                          self.json_data['runs'][1]['param_value'] - start)
                    self.backend_runner.run_with_param(param_name, start,
                                                       stop, increment)
                else:
                    self.backend_runner.run()
