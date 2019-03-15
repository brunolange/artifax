from . import builder
from . import utils

class Artifax:
    def __init__(self, dic={}, allow_partial_functions=False):
        self._artifacts = dic.copy()
        self._result = {}
        self._stale = set(list(self._artifacts.keys()))
        self._allow_partial_functions = allow_partial_functions

    def set(self, node, value):
        if node in self._artifacts:
            self._revoke(node, utils.to_graph(self._artifacts))
        self._stale.add(node)
        self._artifacts[node] = value

    def _revoke(self, node, graph):
        self._stale.add(node)
        for neighbor in graph[node]:
            self._revoke(neighbor, graph)

    def pop(self, node):
        if node in self._stale:
            self._stale.remove(node)
        return self._artifacts.pop(node)

    def build(self, allow_partial_functions=None):
        afx = builder.build({
            'ts': lambda _x: utils.topological_sort(_x),
            'tg': lambda _x: utils.to_graph(_x),
            'shipment': {
                k: self._artifacts[k]
                for k in self._stale
            },
            'nodes': lambda ts, tg, shipment: ts(tg(shipment)),
            'result': lambda shipment, nodes: builder.assemble(
                shipment,
                nodes,
                allow_partial_functions=(
                    allow_partial_functions if allow_partial_functions is not None else
                    self._allow_partial_functions
                )
            )
        }, allow_partial_functions=True)
        self._stale = set()
        self._result.update(afx['result'])
        return self._result.copy()

    def __len__(self):
        return len(self._artifacts)

    def __contains__(self, node):
        return node in self._artifacts
