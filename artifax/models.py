from . import builder
from . import utils

class Artifax:
    def __init__(self, dic={}):
        self._data = dic
        self._graph = None
        self._cache = {}

    def _revoke(self, node):
        _ = self._cache.pop(node)
        for k in self.graph()[node]:
            self._revoke(k)

    def set(self, node, value):
        if node in self._data:
            self._revoke(node)
        self._data[node] = value

    def pop(self, node):
        return self._data.pop(node)

    def graph(self):
        return utils.to_graph(self._data)

    def sort(self):
        return utils.topological_sort(self.graph())

    def _build(self):
        nodes = self.sort()
        return builder.assemble(self._data, nodes, cache=self._cache)

    def build(self):
        result = self._build()
        for k, v in result.items():
            if not callable(v):
                self._cache[k] = v
        return result

    def __len__(self):
        return len(self._data)
