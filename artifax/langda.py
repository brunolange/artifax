from collections.abc import Iterable

def each(iterable, accept, *args, **kwargs):
    if not isinstance(iterable, Iterable):
        raise ValueError('need an iterable')
    if not callable(accept):
        raise ValueError('need a callable')
    for item in iterable:
        if isinstance(iterable, dict):
            _args = (item, iterable[item])
        elif isinstance(item, tuple):
            _args = item
        else:
            _args = (item,)
        _args += args
        accept(*_args, **kwargs)

flip = lambda f: lambda x: lambda y: f(y, x)
