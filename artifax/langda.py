from collections.abc import Iterable

def each(xs, accept, *args, **kwargs):
    if not isinstance(xs, Iterable):
        raise ValueError('need an iterable')
    if not callable(accept):
        raise ValueError('need a callable')
    for x in xs:
        if isinstance(xs, dict):
            _args = (x, xs[x])
        elif isinstance(x, tuple):
            _args = x
        else:
            _args = (x,)
        _args += args
        accept(*_args, **kwargs)
