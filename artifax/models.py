""" models.py

This module hosts classes that provided the object-oriented support to building
artifacts.
"""

from functools import reduce
import operator
from exos import each
from . import builder
from . import utils as u


def _fluent(cls, attr, *args):
    """ provides a fluent interface for any classes that choose to apply it. """
    if args:
        setattr(cls, attr, args[0])
        return cls
    return getattr(cls, attr)


class Artifax:
    """ The Artifax class enables artifacts to be built through a conventional
    object-oriented interface. Its stateful nature boasts additional capabilities
    like incremental builds and building of stale nodes only.
    """
    class Result:
        """ The Result class acts as an augmented dictionary to
        hold the artifax build products and any additional information
        deemed necessary or interesting. """
        def __init__(self, *args, **kwargs):
            self._data = {}
            self.update(*args, **kwargs)

        def __setitem__(self, key, item):
            self._data[key] = item

        def __getitem__(self, key):
            return self._data[key]

        def __repr__(self):
            return repr(self._data)

        def __len__(self):
            return len(self._data)

        def __delitem__(self, key):
            del self._data[key]

        def clear(self):
            """ Removes all items from result. """
            return self._data.clear()

        def copy(self):
            """ Returns a shallow copy of the result dictionary. """
            return self._data.copy()

        def has_key(self, k):
            """ Returns True if key k is part of the result and False otherwise.
            """
            return k in self._data

        def update(self, *args, **kwargs):
            """ R.update([E, ]**F) -> None.  Update R from dict/iterable E and F.
            If E is present and has a .keys() method, then does:  for k in E: R[k] = E[k]
            If E is present and lacks a .keys() method, then does:  for k, v in E: R[k] = v
            In either case, this is followed by: for k in F:  R[k] = F[k] """
            return self._data.update(*args, **kwargs)

        def keys(self):
            """ Returns a set-like object providing a view on D's keys. """
            return self._data.keys()

        def values(self):
            """ Returns an object providing a view on D's values. """
            return self._data.values()

        def items(self):
            """ Returns key, value pairs of data dictionary items. """
            return self._data.items()

        def pop(self, *args):
            """ pop(k, [,d]) -> v, remove specified key and return
            the corresponding value. If key is not found, d is returned
            if given, otherwise KeyError is raised """
            return self._data.pop(*args)

        def __cmp__(self, dict_):
            return self._data == dict_

        def __contains__(self, item):
            return item in self._data

        def __iter__(self):
            return iter(self._data)

    def __init__(self, dic=None, allow_partial_functions=False, **kwargs):
        if dic is None:
            dic = {}
        dic.update(kwargs)
        self._artifacts = dic.copy()
        self._graph = None
        self._update_graph()
        self._result = Artifax.Result()
        self._stale = set(self._artifacts.keys())
        self._allow_partial_functions = allow_partial_functions

    def _update_graph(self):
        self._graph = u.to_graph(self._artifacts)

    def set(self, *args, **kwargs):
        """ Sets node value. """
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
        """ Removes node from the artifacts. """
        if node in self._stale:
            self._stale.remove(node)
        item = self._artifacts.pop(node)
        self._update_graph()
        return item

    def _shipment(self, targets=None):
        nodes = (
            self._stale if targets is None else
            set(reduce(
                operator.iconcat,
                [self._dependencies(t) for t in targets] + [list(targets)],
                []
            ))
        )
        return {
            k: self._artifacts[k]
            for k in nodes
        }

    def _dependencies(self, node):
        def _moonwalk(node, graph, dependencies):
            for vertex, neighbors in graph.items():
                if node in neighbors:
                    dependencies.append(vertex)
                    _moonwalk(vertex, graph, dependencies)

        dependencies = []
        _moonwalk(node, self._graph, dependencies)
        return dependencies

    def build(self, targets=None, allow_partial_functions=None, solver='linear', **kwargs):
        """ Builds artifacts. Returns either a dictionary of resolved nodes or a tuple
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
                allow_partial_functions if allow_partial_functions is not None else
                self._allow_partial_functions
            ),
            **kwargs
        )

        self._stale = {k for k in self._stale if k not in shipment}
        self._result.update(result)

        if targets is None:
            return self._result

        payload = tuple([self._result[target] for target in targets])
        return payload if len(payload) > 1 else payload[0]

    def initial(self):
        """ Returns the initial objects of the artifacts graph, that is,
        the nodes that have no incoming edges, no dependencies."""
        return u.initial(self._graph)

    def number_of_edges(self):
        """ Returns the number of edges in the artifacts graph."""
        return sum([len(v) for v in self._graph.values()])

    def number_of_nodes(self):
        """ Returns the number of nodes in the artifacts graph."""
        return len(self._artifacts)

    def __len__(self):
        return self.number_of_nodes()

    def __contains__(self, node):
        return node in self._artifacts
