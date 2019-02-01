from inspect import getfullargspec
from functools import reduce
from . import exceptions

_replaces = {
    '-': '_',
}

# make sure we can always undo a key replacement
assert len(_replaces) == len({v: k for k, v in _replaces.items()})

escape   = lambda v: reduce(lambda s, k: s.replace(k, _replaces[k]), _replaces.keys(), v)
unescape = lambda v: reduce(lambda s, k: s.replace(_replaces[k], k), _replaces.keys(), v)

arglist = lambda v: getfullargspec(v).args if callable(v) else []

def to_graph(artifacts):
    af_args = {k: arglist(v) for k, v in artifacts.items()}
    return {
        key: [k for k, v in af_args.items() if escape(key) in v]
        for key in artifacts
    }

def topological_sort(graph):
    def _visit(node, temp, perm, tlist):
        if node in perm:
            return
        if node in temp:
            raise exceptions.CircularDependencyError('artifact graph is not a DAG')
        temp.add(node)
        for neighbor in graph[node]:
            _visit(neighbor, temp, perm, tlist)
        perm.add(node)
        tlist.insert(0, node)

    unmarked = set(graph.keys())
    temp = set()
    perm = set()
    tlist = []
    while unmarked:
        node = unmarked.pop()
        _visit(node, temp, perm, tlist)
    return tlist
