from functools import reduce, partial
from . import utils
from . import exceptions

_apply = lambda v, *args: (
    v(*args)            if callable(v) and len(args) and len(utils.arglist(v)) == len(args) else
    partial(v, *args)   if callable(v) else
    v
)

def assemble(artifacts, nodes, allow_partial_functions=False):
    def _reducer(result, node):
        value = result[node]
        args = utils.arglist(value)
        if isinstance(value, utils.At):
            args = value.args
            value = value.value
        keys = [utils.unescape(a) for a in args]
        if not allow_partial_functions:
            unresolved = [key for key in keys if key not in result]
            if unresolved:
                raise exceptions.UnresolvedDependencyError("Cannot resolve {}".format(unresolved))
        args = [result[key] for key in keys if key in result]
        result[node] = _apply(value, *args)
        return result
    return reduce(_reducer, nodes, artifacts.copy())

def build(artifacts, allow_partial_functions=False):
    graph = utils.to_graph(artifacts)
    nodes = utils.topological_sort(graph)
    return assemble(artifacts, nodes, allow_partial_functions)
