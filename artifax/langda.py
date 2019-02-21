from collections.abc import Iterable

def each(xs, accept, *args, **kwargs):
    if not isinstance(xs, Iterable):
        raise ValueError('need an iterable')
    for x in xs:
        if isinstance(x, tuple):
            accept(*(x + args), **kwargs)
        else:
            accept(x, *args, **kwargs)
