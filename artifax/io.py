from . import _to_graph, _topological_sort
from functools import reduce
from jinja2 import Template
import os

def tex(artifacts):
    graph = _to_graph(artifacts)
    nodes = _topological_sort(graph)

    def _edge_reducer(pairs, key):
        for value in graph[key]:
            pairs.append((key, value))
        return pairs

    path = lambda *args: os.path.join(*args)
    with open(path(os.path.dirname(__file__), 'templates', 'dag.tex.j2')) as handle:
        template = Template(handle.read())

    nodes = list(artifacts.keys())
    edges = reduce(_edge_reducer, graph.keys(), [])
    return template.render(nodes=nodes, edges=edges)
