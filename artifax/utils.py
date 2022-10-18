"""Utilities module
"""

import os
from functools import reduce
from inspect import signature

from . import exceptions

__author__ = "Bruno Lange"
__email__ = "blangeram@gmail.com"
__license__ = "MIT"


arglist = lambda v: (
    list(signature(v).parameters.keys()) if callable(v) else v.args() if isinstance(v, At) else []
)


def to_graph(artifacts):
    """returns a graph representation of the given artifacts"""
    af_args = {k: arglist(v) for k, v in artifacts.items()}
    return {key: [k for k, v in af_args.items() if key in v] for key in artifacts}


def topological_sort(graph):
    """returns a topological sorting of nodes from the given graph

    Throws artifax.CircularDependencyError
    if graph is not a Direct Acyclic Graph (DAG)
    """

    def _visit(node, temp, perm, tlist):
        if node in perm:
            return
        if node in temp:
            raise exceptions.CircularDependencyError("artifact graph is not a DAG")
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


def initial(graph):
    def to_mask(mask, node, graph, key):
        neighbors = graph[node]
        for neighbor in neighbors:
            mask[key[neighbor]] = 1
        return mask

    nodes = list(graph.keys())
    key = {nodes[i]: i for i in range(len(nodes))}
    mask = reduce(lambda m, n: to_mask(m, n, graph, key), nodes, [0] * len(nodes))

    return set(nodes[i] for i in range(len(mask)) if mask[i] == 0)


def pprint(*args, **kwargs):
    """Prepends message with process id information"""
    print("[{}]".format(os.getpid()), end=" ")
    print(*args, **kwargs)


class At:
    """The At class is but a wrapper for a tuple-like constructor
    that can be used to assign node values in a compact way without
    using lambda expressions.

    For example:
    {'a': lambda b, c: some_function(c, b)}

    can be rewritten as

    {'a': At('c', 'b', some_function)}
    """

    def __init__(self, *args):
        if len(args) < 2:
            raise ValueError("At constructor requires at least two arguments")
        self._args = args[:-1]
        self._value = args[-1]

    def args(self):
        """returns list of lambda arguments"""
        return self._args

    def value(self):
        """returns lambda"""
        return self._value
