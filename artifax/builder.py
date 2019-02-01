from functools import reduce, partial
from . import utils

_apply = lambda v, *args: (
    v(*args) if callable(v) and len(args) and len(utils.arglist(v)) == len(args) else
    partial(v, *args) if callable(v) else
    v
)

def assemble(artifacts, nodes):
    def _reducer(result, node):
        value = result[node]
        keys = [utils.unescape(a) for a in utils.arglist(value)]
        args = [result[key] for key in keys if key in result]
        result[node] = _apply(value, *args)
        return result
    return reduce(_reducer, nodes, artifacts.copy())

def build(artifacts):
    """ build :: Dict a -> a -> a """
    graph = utils.to_graph(artifacts)
    nodes = utils.topological_sort(graph)
    return assemble(artifacts, nodes)
