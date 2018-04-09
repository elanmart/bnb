import inspect

from attr import asdict
from attr.exceptions import NotAnAttrsClassError

from bnb.common import States


def nested_update(collection, *path, value, mode='replace'):

    assert mode in {'replace', 'append'}

    root      = collection
    path, key = path[:-1], path[-1]

    for p in path:
        root = root[p]

    if mode == 'replace':
        root[key] = value

    elif mode == 'append':
        if key not in root:
            root[key] = []
        root[key].append(value)


def capture_config(f, args, kwargs):

    argspec = inspect.getfullargspec(f)

    named_callargs = {k: v for k, v in zip(argspec.args, args)}
    named_callargs.update(kwargs)

    if len(named_callargs) == 0:
        return {}

    retval = {}

    for k, v in named_callargs.items():
        retval.update(_perhaps_extract(k, v))

    for k, v in retval.items():
        retval[k] = _as_string(v)

    return retval


def _perhaps_extract(k, v):

    try:
        return asdict(v)
    except NotAnAttrsClassError:
        return {k: v}


def _as_string(o):

    if callable(o):
        if hasattr(o, '__name__'):
            return o.__name__
        return o.__class__.__name__
        
    return str(o)
