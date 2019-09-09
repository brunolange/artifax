from functools import reduce
import os
from . import utils

def tex(artifacts):
    from jinja2 import Template
    graph = utils.to_graph(artifacts)
    nodes = utils.topological_sort(graph)

    def _edge_reducer(pairs, key):
        for value in graph[key]:
            pairs.append((key, value))
        return pairs

    with open(os.path.join(os.path.dirname(__file__), 'templates', 'dag.tex.j2')) as handle:
        template = Template(handle.read())

    nodes = list(artifacts.keys())
    edges = reduce(_edge_reducer, graph.keys(), [])
    return template.render(nodes=nodes, edges=edges)
