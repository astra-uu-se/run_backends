# run_backends
This script is capable of running multiple MiniZinc instances on multiple MiniZinc backends (solvers) and outputs the results into a LaTeX table, .JSON file, or both.

## Requirements
* Python3
* The [minizinc-python](https://python.minizinc.dev) python package

## Installation
Install the requirements and clone this repository

## Usage
Run `python3 run_backends.py --help` in a terminal.

## Custom Outputters
To create your own outputter, create a python code file in the `src/outputters/` directory and create a class that inherits from the `src.outputters.outputter.Outputter` class. Use the `JsonOutputter` and `LatexOutputter` as a guide. You have to import your outputter in the `run_backends.py` file and append it to the `outputters` python variable, which is an argument to the `BackendRunner` class.