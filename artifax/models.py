from . import builder
from . import utils

class Artifax:
    def __init__(self, dic={}):
        self._artifacts = dic
        self._result = {}
        self._stale = set(list(self._artifacts.keys()))

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

    def build(self):
        afx = builder.build({
            'ts': lambda _x: utils.topological_sort(_x),
            'tg': lambda _x: utils.to_graph(_x),
            'shipment': {
                k: self._artifacts[k]
                for k in self._stale
            },
            'nodes': lambda ts, tg, shipment: ts(tg(shipment)),
            'result': lambda shipment, nodes: builder.assemble(shipment, nodes)
        })
        self._stale = set()
        self._result.update(afx['result'])
        return self._result.copy()

    def __len__(self):
        return len(self._artifacts)

    def __contains__(self, node):
        return node in self._artifacts
