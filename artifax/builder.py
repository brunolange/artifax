from functools import reduce, partial
from . import utils
from .exceptions import UnresolvedDependencyError
from collections import deque
import operator
import pathos.multiprocessing as mp

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

def build(artifacts, allow_partial_functions=False, processes=None):
    callback = (
        _build if not processes else
        partial(_build_processes, processes)
    )
    return callback(artifacts, allow_partial_functions)

def _build(artifacts, allow_partial_functions):
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

def _build_processes(processes, artifacts, allow_partial_functions):
    done = set()
    result = {}
    graph = utils.to_graph(artifacts)
    frontier = set(utils.branes(graph))
    pool = mp.Pool(processes=processes)
    while frontier:
        batch = {
            node: pool.apply(_resolve, args=(node, artifacts))
            for node in frontier
        }
        for node, (payload, unresolved) in batch.items():
            if not allow_partial_functions and unresolved:
                raise UnresolvedDependencyError("Cannot resolve {}".format(unresolved))
            result[node] = payload
        done |= frontier
        frontier = set(reduce(operator.iconcat, [graph[n] for n in frontier], [])) - done

    return result
