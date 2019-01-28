from . import builder
from . import utils

class Artifax:
    def __init__(self, dic={}):
        self._artifacts = dic
        self._graph = None
        self._result = None

    def set(self, node, value):
        if node in self._artifacts:
            self._revoke(node)
        self._artifacts[node] = value

    def _revoke(self, node):
        _ = self._result.pop(node)
        for k in self.graph()[node]:
            self._revoke(k)

    def pop(self, node):
        return self._artifacts.pop(node)

    def graph(self):
        return utils.to_graph(self._artifacts)

    def sort(self):
        return utils.topological_sort(self.graph())

    def build(self):
        nodes = self.sort()
        result = builder.assemble(self._artifacts, nodes, cache=self._result or {})
        self._result = result
        return result.copy()

    def __len__(self):
        return len(self._artifacts)
