import minizinc
from typing import List, Tuple, Set


def set_minizinc_driver_path(driver_path: str) -> None:
    try:
        if driver_path is not None and minizinc.default_driver is None:
            driver = minizinc.Driver.find([driver_path], name='minizinc')
            driver.make_default()
    except AttributeError:
        driver = minizinc.Driver.find([driver_path], name='minizinc')
        driver.make_default()


def get_minizinc_backends() -> List[str]:
    available_backends = minizinc.default_driver.available_solvers()
    names = []
    for id, backends in available_backends.items():
        unique_ids = set()
        unique_backends = []
        for b in backends:
            if b.id not in unique_ids:
                unique_ids.add(b.id)
                unique_backends.append(b)
        if len(unique_backends) != 1:
            continue
        backend = unique_backends[0]
        if backend.isGUIApplication:
            continue
        id = backend.id.split('.')[-1]
        if len(id) == 0 or len(backend.name) == 0 or id == 'findmus':
            continue
        names.append((id, backend.name))
    return names


def filter_minizinc_backends(
        backends: List[str]) -> Tuple[Set[str], List[Tuple[str, str]]]:

    unique = set((b.lower() for b in backends))
    backends = []
    for backend_id, backend_name in get_minizinc_backends():
        if backend_name.lower() in unique or backend_id.lower() in unique:
            if backend_name.lower() in unique:
                unique.remove(backend_name.lower())
            if backend_id.lower() in unique:
                unique.remove(backend_id.lower())
            backends.append((backend_id, backend_name))
    return unique, backends
