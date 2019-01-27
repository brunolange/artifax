from . import builder
from . import utils

class Artifax:
    def __init__(self, dic={}):
        self._data = dic
        self._needs_refresh = True
        self._result = None
        self._graph = None
        self._sorting = None

    def _void(self):
        self._result = None
        self._graph = None
        self._sorting = None

    def add(self, node, value):
        self._data[node] = value
        self._void()

    def pop(self, node):
        self._void()
        return self._data.pop(node)

    def graph(self):
        graph = self._graph
        if graph is None:
            graph = utils.to_graph(self._data)
            self._graph = graph
        return graph

    def sort(self):
        sorting = self._sorting
        if sorting is None:
            sorting = utils.topological_sort(self.graph())
            self._sorting = sorting
        return sorting

    def _build(self):
        graph = self.graph()
        nodes = self.sort()
        return builder.assemble(self._data, graph, nodes)

    def build(self):
        result = self._result
        if result is None:
            result = self._build()
            self._result = result
        return result.copy()

    def __len__(self):
        return len(self._data)