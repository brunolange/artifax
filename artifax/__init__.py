"""artifax is a Python package to evaluate nodes in a computation graph where
the dependencies associated with each node are extracted directly from their
function signatures.
"""

__all__ = ['build']

from inspect import getfullargspec
from functools import reduce, partial

_arglist = lambda v: getfullargspec(v).args if callable(v) else []
_apply = lambda v, *args: (
    v(*args) if callable(v) and len(args) and len(_arglist(v)) == len(args) else
    partial(v, *args) if callable(v) else
    v
)

class CircularDependencyError(Exception):
    """ Exception to be thrown when artifacts can not be built due to the fact
    that there is at least one closed loop in its graph representation which
    means we can not determine an evaluation order for the artifact nodes"""
    pass

def _to_graph(artifacts):
    af_args = {k: _arglist(v) for k, v in artifacts.items()}
    return {
        key: [k for k, v in af_args.items() if key in v]
        for key in artifacts
    }

def _topological_sort(graph):
    def _visit(node, temp, perm, tlist):
        if node in perm:
            return
        if node in temp:
            raise CircularDependencyError('artifact graph is not a DAG')
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

def _build(artifacts, graph, nodes):
    def _reducer(result, node):
        value = result[node]
        args = [result[a] for a in _arglist(value) if a in result]
        result[node] = _apply(value, *args)
        return result

    return reduce(_reducer, nodes, artifacts.copy())

def build(artifacts):
    """ build :: Dict a -> a -> a """
    graph = _to_graph(artifacts)
    nodes = _topological_sort(graph)
    return _build(artifacts, graph, nodes)

