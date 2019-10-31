import os
from functools import reduce, partial
import operator

from jinja2 import Template

from . import utils

__author__ = 'Bruno Lange'
__email__ = 'blangeram@gmail.com'
__license__ = 'MIT'


def tex(artifacts):
    graph = utils.to_graph(artifacts)
    nodes = utils.topological_sort(graph)

    with open(os.path.join(os.path.dirname(__file__), 'templates', 'dag.tex.j2')) as handle:
        template = Template(handle.read())

    def pairs(item):
        key, values = item
        return [(key, v) for v in values]

    edge_reducer = lambda g: reduce(
        operator.iconcat,
        map(pairs, g.items()),
        []
    )

    nodes = list(artifacts.keys())
    edges = edge_reducer(graph)
    return template.render(nodes=nodes, edges=edges)
