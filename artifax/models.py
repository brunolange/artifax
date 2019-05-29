from functools import reduce
import operator
from . import builder
from . import utils
from . import langda as ft

def fluent(cls, attr, *args):
    if args:
        setattr(cls, attr, args[0])
        return cls
    return getattr(cls, attr)

class Artifax:
    class Result:
        """ The Result class acts as an augmented dictionary to
        hold the artifax build products and any additional information
        deemed necessary or interesting. """
        def __init__(self, *args, **kwargs):
            self._data = {}
            self.update(*args, **kwargs)
            self._sorting = []

        def sorting(self, *args):
            return fluent(self, '_sorting', *args)

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
            return self._data.clear()

        def copy(self):
            return self._data.copy()

        def has_key(self, k):
            return k in self._data

        def update(self, *args, **kwargs):
            return self._data.update(*args, **kwargs)

        def keys(self):
            return self._data.keys()

        def values(self):
            return self._data.values()

        def items(self):
            return self._data.items()

        def pop(self, *args):
            return self._data.pop(*args)

        def __cmp__(self, dict_):
            return self._data == dict_

        def __contains__(self, item):
            return item in self._data

        def __iter__(self):
            return iter(self._data)

    def __init__(self, dic=None, allow_partial_functions=False):
        if dic is None:
            dic = {}
        self._artifacts = dic.copy()
        self._graph = None
        self._update_graph()
        self._result = Artifax.Result()
        self._stale = set(list(self._artifacts.keys()))
        self._allow_partial_functions = allow_partial_functions

    def _update_graph(self):
        self._graph = utils.to_graph(self._artifacts)

    def set(self, node, value):
        if node in self._artifacts:
            self._revoke(node)
        self._stale.add(node)
        self._artifacts[node] = value
        self._update_graph()

    def _revoke(self, node):
        self._stale.add(node)
        ft.each(self._graph[node], self._revoke)

    def pop(self, node):
        if node in self._stale:
            self._stale.remove(node)
        item = self._artifacts.pop(node)
        self._update_graph()
        return item

    def _shipment(self, targets=None):
        graph = utils.to_graph(self._artifacts)
        nodes = (
            self._stale if targets is None else
            set(reduce(
                operator.iconcat,
                [self._dependencies(graph, t) for t in targets] + [list(targets)],
                []
            ))
        )
        return {
            k: self._artifacts[k]
            for k in nodes
        }

    def _dependencies(self, graph, node):
        def _moonwalk(node, graph, dependencies):
            for vertex, neighbors in graph.items():
                if node in neighbors:
                    dependencies.append(vertex)
                    _moonwalk(vertex, graph, dependencies)

        dependencies = []
        _moonwalk(node, self._graph, dependencies)
        return dependencies

    def build(self, targets=None, allow_partial_functions=None, processes=None):
        targets = (targets,) if isinstance(targets, str) else targets
        if targets:
            for target in targets:
                if target not in self:
                    raise KeyError(target)

        shipment = self._shipment(targets)
        result = builder.build(
            shipment,
            allow_partial_functions=(
                allow_partial_functions if allow_partial_functions is not None else
                self._allow_partial_functions
            ),
            processes=processes
        )

        self._stale = {k for k in self._stale if k not in shipment}
        self._result.update(result)

        if targets is None:
            return self._result

        payload = tuple([
            self._result[target] for target in targets
        ])
        return payload if len(payload) > 1 else payload[0]

    def branes(self):
        return utils.branes(self._graph)

    def number_of_edges(self):
        return sum([len(v) for v in self._graph.values()])

    def number_of_nodes(self):
        return len(self._artifacts)

    def __len__(self):
        return self.number_of_nodes()

    def __contains__(self, node):
        return node in self._artifacts
