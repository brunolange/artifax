""" models.py

This module hosts classes that provided the object-oriented support to building
artifacts.
"""

import operator
from functools import reduce

from exos import each

from . import builder
from . import utils as u

__author__ = "Bruno Lange"
__email__ = "blangeram@gmail.com"
__license__ = "MIT"


def _fluent(cls, attr, *args):
    """provides a fluent interface for any classes that choose to apply it."""
    if args:
        setattr(cls, attr, args[0])
        return cls
    return getattr(cls, attr)


class Artifax:
    """The Artifax class enables artifacts to be built through a conventional
    object-oriented interface. Its stateful nature boasts additional capabilities
    like incremental builds and building of stale nodes only.
    """

    def __init__(self, dic=None, allow_partial_functions=False, **kwargs):
        if dic is None:
            dic = {}
        dic.update(kwargs)
        self._artifacts = dic.copy()
        self._graph = None
        self._update_graph()
        self._result = {}
        self._stale = set(self._artifacts.keys())
        self._allow_partial_functions = allow_partial_functions

    def _update_graph(self):
        self._graph = u.to_graph(self._artifacts)

    def set(self, *args, **kwargs):
        """Sets node value."""
        if kwargs:
            for key, value in kwargs.items():
                self.set(key, value)
            return
        node, value = args[0], args[1]
        if node in self._artifacts:
            self._revoke(node)
        self._stale.add(node)
        self._artifacts[node] = value
        self._update_graph()

    def _revoke(self, node):
        self._stale.add(node)
        each(self._revoke, self._graph[node])

    def pop(self, node):
        """Removes node from the artifacts."""
        if node in self._stale:
            self._stale.remove(node)
        item = self._artifacts.pop(node)
        self._update_graph()
        return item

    def _shipment(self, targets=None):
        nodes = (
            self._stale
            if targets is None
            else set(
                reduce(
                    operator.iconcat,
                    [self._dependencies(t) for t in targets] + [list(targets)],
                    [],
                )
            )
        )
        return {k: self._artifacts[k] for k in nodes}

    def _dependencies(self, node):
        def _moonwalk(node, graph, dependencies):
            for vertex, neighbors in graph.items():
                if node in neighbors:
                    dependencies.append(vertex)
                    _moonwalk(vertex, graph, dependencies)

        dependencies = []
        _moonwalk(node, self._graph, dependencies)
        return dependencies

    def build(
        self, targets=None, allow_partial_functions=None, solver="linear", **kwargs
    ):
        """Builds artifacts. Returns either a dictionary of resolved nodes or a tuple
        where each item corresponds to one of the defined targets.

        Args:
            targets (:obj:`string or tuple`, optional): Defines specific targets
                to be built. Either a tuple of node names or a string for single
                targets.
            allow_partial_functions (bool, optional): Set to True if artifacts are
                allowed to be resolved to partial functions. Defaults to False.
            solver (str, optional): Choose artifax solver strategy. Pick between
                {'linear', 'bfs', 'bfs_parallel', 'async'}. Defaults to 'linear'.
                Throws InvalidSolverError if solver is not among the available options.
            **kwargs: Arbitrary keyword arguments that are solver-specific.
        """
        return_bare_result = isinstance(targets, str)
        targets = (targets,) if isinstance(targets, str) else targets
        if targets:
            for target in targets:
                if target not in self:
                    raise KeyError(target)

        shipment = self._shipment(targets)
        result = builder.build(
            shipment,
            solver=solver,
            allow_partial_functions=(
                allow_partial_functions
                if allow_partial_functions is not None
                else self._allow_partial_functions
            ),
            **kwargs
        )

        self._stale = {k for k in self._stale if k not in shipment}
        self._result.update(result)

        if targets is None:
            return self._result

        payload = tuple(self._result[target] for target in targets)
        return payload[0] if return_bare_result else payload

    def initial(self):
        """Returns the initial objects of the artifacts graph, that is,
        the nodes that have no incoming edges, no dependencies."""
        return u.initial(self._graph)

    def number_of_edges(self):
        """Returns the number of edges in the artifacts graph."""
        return sum(len(v) for v in self._graph.values())

    def number_of_nodes(self):
        """Returns the number of nodes in the artifacts graph."""
        return len(self._artifacts)

    def __len__(self):
        return self.number_of_nodes()

    def __contains__(self, node):
        return node in self._artifacts
