from functools import reduce, partial
from . import utils
from .exceptions import UnresolvedDependencyError

apply = lambda v, *args: (
    v(*args)            if callable(v) and args and len(utils.arglist(v)) == len(args) else
    partial(v, *args)   if callable(v) else
    v
)

def assemble(artifacts, nodes, allow_partial_functions=False):
    def _resolve(node, store):
        value = store[node]
        args = utils.arglist(value)
        if isinstance(value, utils.At):
            args = value.args()
            value = value.value()
        keys = [utils.unescape(a) for a in args]
        args = [store[key] for key in keys if key in store]
        unresolved = [key for key in keys if key not in store]
        return apply(value, *args), unresolved

    def _reducer(store, node, graph, resolved):
        store[node], unresolved = _resolve(node, store)
        if not allow_partial_functions and unresolved:
            raise UnresolvedDependencyError("Cannot resolve {}".format(unresolved))

        return store

    resolved = set()
    graph = utils.to_graph(artifacts)

    return reduce(
        lambda store, node: _reducer(store, node, graph, resolved),
        nodes,
        artifacts.copy()
    )

def build(artifacts, allow_partial_functions=False):
    graph = utils.to_graph(artifacts)
    nodes = utils.topological_sort(graph)
    return assemble(artifacts, nodes, allow_partial_functions)
