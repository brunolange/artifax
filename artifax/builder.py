from functools import reduce, partial
from . import utils
from .exceptions import UnresolvedDependencyError
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

def build(artifacts, solver='linear', **kwargs):
    solvers = {
        'linear':       _build_linear,
        'bfs':          _build_bfs,
        'bfs_parallel': _build_parallel_bfs,
        'async':        _build_async
    }
    return solvers[solver](artifacts, **kwargs)

def _build_linear(artifacts, allow_partial_functions=False):
    graph = utils.to_graph(artifacts)
    nodes = utils.topological_sort(graph)

    def _reducer(store, node):
        store[node], unresolved = _resolve(node, store)
        if not allow_partial_functions and unresolved:
            raise UnresolvedDependencyError("Cannot resolve {}".format(unresolved))
        return store

    return reduce(_reducer, nodes, artifacts.copy())

def _build_bfs(artifacts, allow_partial_functions=False):
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

def _build_parallel_bfs(artifacts, allow_partial_functions=False, processes=None):
    done = set()
    result = {}
    graph = utils.to_graph(artifacts)
    frontier = set(utils.branes(graph))
    pool = mp.Pool(processes=processes)
    while frontier:
        batch = {
            node: pool.apply(_resolve, args=(node, artifacts))
            for node in frontier
        } if len(frontier) > 1 else {
            node: _resolve(node, artifacts)
            for node in frontier
        }
        for node, (payload, unresolved) in batch.items():
            if not allow_partial_functions and unresolved:
                raise UnresolvedDependencyError("Cannot resolve {}".format(unresolved))
            result[node] = payload
        done |= frontier
        frontier = set(reduce(operator.iconcat, [graph[n] for n in frontier], [])) - done

    pool.close()

    return result

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

def _build_async(artifacts, allow_partial_functions=False, processes=None):
    graph = utils.to_graph(artifacts)
    frontier = utils.branes(graph)

    result = {}
    if len(frontier) <= 1:
        batch = {node: _resolve(node, artifacts) for node in frontier}
        for node, (payload, unresolved) in batch.items():
            if not allow_partial_functions and unresolved:
                raise UnresolvedDependencyError("Cannot resolve {}".format(unresolved))
            result[node] = payload
        return result

    done = set()
    result = {}
    pool = mp.Pool(
        processes=processes if processes is not None else min(mp.cpu_count(), len(frontier))
    )
    for node in frontier:
        pool.apply_async(
            _resolve,
            args=(node, artifacts),
            callback=partial(_handle_completion,
                artifacts, graph, result, node, done,
                allow_partial_functions=allow_partial_functions,
            )
        )

    pool.close()
    pool.join()

    return result

def _handle_completion(artifacts, graph, result, node, done, payload, **kwargs):
    out, unresolved = payload
    if not kwargs['allow_partial_functions'] and unresolved:
        raise UnresolvedDependencyError("Cannot resolve {}".format(unresolved))

    done.add(node)
    result[node] = out
    batch = [
        nxt for nxt in graph[node]
        if not set(k for k, v in graph.items() if nxt in v and k not in done)
    ]

    if not batch:
        return

    if len(batch) == 1:
        result[batch[0]] = _resolve(batch[0], artifacts)
        return

    pool = mp.Pool(processes=min(mp.cpu_count(), len(batch)))
    for nxt in batch:
        pool.apply_async(_resolve,
            args=(nxt, artifacts),
            callback=partial(_handle_completion,
                artifacts, graph, result, nxt, done,
                **kwargs
            )
        )

    pool.close()
    pool.join()
