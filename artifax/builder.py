from functools import reduce, partial
from . import utils
from .exceptions import UnresolvedDependencyError, InvalidSolverError
from collections import deque
import operator
import pathos.multiprocessing as mp
import time
import os

apply = lambda v, *args: (
    v(*args)            if callable(v) and args and len(utils.arglist(v)) == len(args) else
    partial(v, *args)   if callable(v) else
    v
)

def build(artifacts, allow_partial_functions=False, solver='linear', **kwargs):
    solvers = {
        'linear':       _build_linear,
        'bfs':          _build_bfs,
        'bfs_parallel': _build_parallel_bfs,
        'async':        _build_async
    }
    if not solver in solvers:
        raise InvalidSolverError('unrecognized solver [{}]'.format(solver))

    return solvers[solver](
        artifacts.copy(),
        allow_partial_functions=allow_partial_functions,
        **kwargs
    )

def _build_linear(artifacts, allow_partial_functions=False):
    graph = utils.to_graph(artifacts)
    nodes = utils.topological_sort(graph)

    def _reducer(store, node):
        store[node] = _resolve(node, store, allow_partial_functions)
        return store

    return reduce(_reducer, nodes, artifacts)

def _build_bfs(artifacts, allow_partial_functions=False):
    done = set()
    result = {}
    graph = utils.to_graph(artifacts)
    frontier = deque(utils.initial(graph))
    while frontier:
        node = frontier.popleft()
        result[node] = _resolve(node, artifacts, allow_partial_functions=allow_partial_functions)
        done.add(node)
        for nxt in graph[node]:
            pending = set(k for k, v in graph.items() if nxt in v and k not in done)
            if not pending:
                frontier.append(nxt)

    return result

def _build_parallel_bfs(artifacts, allow_partial_functions=False, processes=None):
    done = set()
    result = {}
    graph = utils.to_graph(artifacts)
    frontier = set(utils.initial(graph))
    pool = mp.Pool(processes=processes)
    while frontier:
        batch = {
            node: pool.apply(_resolve, args=(node, artifacts))
            for node in frontier
        } if len(frontier) > 1 else {
            node: _resolve(node, artifacts, allow_partial_functions=allow_partial_functions)
            for node in frontier
        }
        for node, payload in batch.items():
            result[node] = payload
        done |= frontier
        frontier = set(reduce(operator.iconcat, [graph[n] for n in frontier], [])) - done

    pool.close()

    return result

def _build_async(artifacts, allow_partial_functions=False, processes=None):
    graph = utils.to_graph(artifacts)
    frontier = utils.initial(graph)

    if not frontier:
        return {}

    done = set()
    result = {}
    pool = mp.Pool(
        processes=processes if processes is not None else min(mp.cpu_count(), len(frontier))
    )
    for node in frontier:
        pool.apply_async(
            partial(_resolve, allow_partial_functions=allow_partial_functions),
            args=(node, artifacts),
            callback=partial(_handle_completion,
                artifacts, graph, result, node, done,
                allow_partial_functions=allow_partial_functions,
            )
        )

    pool.close()
    pool.join()

    return result

def _handle_completion(artifacts, graph, result, node, done, value, allow_partial_functions=False, **kwargs):
    done.add(node)
    result[node] = value
    batch = [
        nxt for nxt in graph[node]
        if not set(k for k, v in graph.items() if nxt in v and k not in done)
    ]

    if not batch:
        return

    if len(batch) == 1:
        result[batch[0]] = _resolve(
            batch[0],
            artifacts,
            allow_partial_functions=allow_partial_functions
        )
        return

    pool = mp.Pool(processes=min(mp.cpu_count(), len(batch)))
    for nxt in batch:
        pool.apply_async(_resolve,
            args=(nxt, artifacts),
            callback=partial(_handle_completion,
                artifacts, graph, result, nxt, done,
                allow_partial_functions=allow_partial_functions,
                **kwargs
            )
        )

    pool.close()
    pool.join()

def _resolve(node, store, allow_partial_functions=False):
    value = store[node]
    args = utils.arglist(value)
    if isinstance(value, utils.At):
        args = value.args()
        value = value.value()
    keys = [utils.unescape(a) for a in args]
    args = [store[key] for key in keys if key in store]
    unresolved = [key for key in keys if key not in store]
    if not allow_partial_functions and unresolved:
        raise UnresolvedDependencyError("Cannot resolve {}".format(unresolved))
    return apply(value, *args)
