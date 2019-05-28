from functools import reduce, partial
from . import utils
from .exceptions import UnresolvedDependencyError
from collections import deque

apply = lambda v, *args: (
    v(*args)            if callable(v) and args and len(utils.arglist(v)) == len(args) else
    partial(v, *args)   if callable(v) else
    v
)

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

def build(artifacts, allow_partial_functions=False):
    done = set()
    result = {}
    graph = utils.to_graph(artifacts)
    frontier = deque(utils.branes(graph))
    while frontier:
        node = frontier.popleft()
        result[node], unresolved = _resolve(node, artifacts)
        done.add(node)
        if not allow_partial_functions and unresolved:
            raise UnresolvedDependencyError("Cannot resolve {}".format(unresolved))
        for nxt in graph[node]:
            pending = set(k for k, v in graph.items() if nxt in v and k not in done)
            if not pending:
                frontier.append(nxt)

    return result
