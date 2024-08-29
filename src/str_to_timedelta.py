from datetime import timedelta
from re import compile, UNICODE
from typing import Union, List, Dict
from argparse import ArgumentTypeError


class StrToTimedelta:
    """
    Interprets a string as a timedelta for argument parsing.
    With no default unit:
    >>> tdtype = TimeDeltaType()
    >>> tdtype('5s')
    timedelta(0, 5)
    >>> tdtype('5.5s')
    timedelta(0, 5, 500000)
    >>> tdtype('5:06:07:08s')
    timedelta(5, 22028)
    >>> tdtype('5d06h07m08s')
    timedelta(5, 22028)
    >>> tdtype('5d')
    timedelta(5)
    With a default unit of minutes:
    >>> tdmins = TimeDeltaType('m')
    >>> tdmins('5s')
    timedelta(0, 5)
    >>> tdmins('5')
    timedelta(0, 300)
    >>> tdmins('6:05')
    timedelta(0, 21900)
    And some error cases:
    >>> tdtype('5')
    Traceback (most recent call last):
        ...
    ValueError: Cannot infer units for '5'
    >>> tdtype('5:5d')
    Traceback (most recent call last):
        ...
    ValueError: Colon not handled for unit 'd'
    >>> tdtype('5:5ms')
    Traceback (most recent call last):
        ...
    ValueError: Colon not handled for unit 'ms'
    >>> tdtype('5q')
    Traceback (most recent call last):
        ...
    ValueError: Unknown unit: 'q'
    """

    units = {'d', 'h', 'm', 's', 'ms'}
    unit_re = compile(r'(\d+\.?\d*)([A-Za-z]*)', UNICODE)
    default_unit: str = 'ms'

    @staticmethod
    def parse(str_vec: Union[int, float, str, List[str]]) -> timedelta:
        if isinstance(str_vec, float) or isinstance(str_vec, int):
            return __class__._dict_to_timedelta(
                {__class__.default_unit: str_vec})
        if isinstance(str_vec, str):
            str_vec = str_vec.split()
        str_vec = [num_val.strip() for num_val in str_vec]
        return __class__._dict_to_timedelta(__class__._parse(str_vec))

    @staticmethod
    def _parse(str_vec: List[str]) -> timedelta:
        pairs: Dict[str, Union[float, int]] = dict()

        for num_unit in str_vec:
            for match in __class__.unit_re.finditer(num_unit):
                if match is None:
                    raise ArgumentTypeError(
                      f'Cannot infer time unit for "{num_unit}"')
                num_s: str = match.group(1)
                try:
                    num = float(num_s) if '.' in num_s else int(num_s)
                except ValueError:
                    raise ArgumentTypeError(
                      f'Cannot parse number "{num_s}" in "{num_unit}"')
                if num < 0:
                    raise ArgumentTypeError(
                      f'Number "{num_s}" in "{num_unit}" must be non-negative')
                unit = match.group(2)
                unit = (__class__.default_unit
                        if len(unit) == 0 and len(str_vec) == 1
                        else unit)
                if len(unit) == 0:
                    raise ArgumentTypeError(
                      f'Cannot infer time unit for "{num_unit}"')
                if unit not in __class__.units:
                    raise ArgumentTypeError(f'Unknown time unit: "{unit}"')
                if unit in pairs:
                    raise ArgumentTypeError(
                      f'Cannot specify time unit "{unit}" twice')
                pairs[unit] = num
        return pairs

    @staticmethod
    def _dict_to_timedelta(d: Dict[str, Union[int, float]]) -> timedelta:
        return timedelta(days=d.get('d', 0),
                         hours=d.get('h', 0),
                         minutes=d.get('m', 0),
                         seconds=d.get('s', 0),
                         milliseconds=d.get('ms', 0))


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser(
        description='Helper for running your MiniZinc experiments.')
    parser.add_argument('-t', '--timeout', dest='timeout',
                        metavar='<timeout>', type=str,
                        nargs='*', help='The time-out.')

    args = parser.parse_args()
    try:
        timeout = StrToTimedelta.parse(args.timeout)
    except ArgumentTypeError as e:
        parser.error(e.args[0])
    print(timeout)
