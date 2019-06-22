""" builder.py

This module hosts the core build function and the private functions that aid it.
"""

from functools import reduce, partial
from collections import deque
import operator
import pathos.multiprocessing as mp
from . import utils
from .exceptions import UnresolvedDependencyError, InvalidSolverError

# pylint: disable=C0103
_apply = lambda v, *args: (
    v(*args)            if callable(v) and args and len(utils.arglist(v)) == len(args) else
    partial(v, *args)   if callable(v) else
    v
)

def build(artifacts, allow_partial_functions=False, solver='linear', **kwargs):
    """ Core artifact building function. Given an input dictionary describing the
    computation graph where each vertex correspond to a key and edges can be extracted
    from the function signatures associated with each key, the build function returns
    a new dictionary where each key is mapped to its final value.

    Args:
        allow_partial_functions (bool, optional): Set to True if artifacts are
            allowed to be resolved to partial functions. Defaults to False.
        solver (str, optional): Choose artifax solver strategy. Pick between
            {'linear', 'bfs', 'bfs_parallel', 'async'}. Defaults to 'linear'.
        **kwargs: solver-specific keyword arguments.
    """
    solvers = {
        'linear':       _build_linear,
        'bfs':          _build_bfs,
        'bfs_parallel': _build_parallel_bfs,
        'async':        _build_async
    }
    if solver not in solvers:
        raise InvalidSolverError('unrecognized solver [{}]'.format(solver))

    return solvers[solver](
        artifacts.copy(),
        apf=allow_partial_functions,
        **kwargs
    )

def _build_linear(artifacts, apf=False):
    graph = utils.to_graph(artifacts)
    nodes = utils.topological_sort(graph)

    def _reducer(store, node):
        store[node] = _resolve(node, store, apf=apf)
        return store

    return reduce(_reducer, nodes, artifacts)

def _pendencies(graph, node, done):
    return {
        k for k, v in graph.items() if node in v and k not in done
    }

def _build_bfs(artifacts, apf=False):
    done = set()
    graph = utils.to_graph(artifacts)
    frontier = deque(utils.initial(graph))
    while frontier:
        node = frontier.popleft()
        artifacts[node] = _resolve(node, artifacts, apf=apf)
        done.add(node)
        frontier += [nxt for nxt in graph[node] if not _pendencies(graph, nxt, done)]

    return artifacts

def _build_parallel_bfs(artifacts, apf=False, processes=None):
    done = set()
    graph = utils.to_graph(artifacts)
    frontier = set(utils.initial(graph))
    pool = mp.Pool(processes=processes)
    while frontier:
        artifacts.update({
            node: pool.apply(_resolve, args=(node, artifacts))
            for node in frontier
        } if len(frontier) > 1 else {
            node: _resolve(node, artifacts, apf=apf)
            for node in frontier
        })
        done |= frontier
        frontier = reduce(lambda acc, curr: acc | curr, [
            {nxt for nxt in graph[node] if not _pendencies(graph, nxt, done)}
            for node in frontier
        ], set())

    pool.close()

    return artifacts

def _build_async(artifacts, apf=False, processes=None):
    graph = utils.to_graph(artifacts)
    frontier = utils.initial(graph)

    if not frontier:
        return {}

    done = set()
    pool = mp.Pool(
        processes=processes if processes is not None else min(mp.cpu_count(), len(frontier))
    )
    for node in frontier:
        pool.apply_async(partial(_resolve, apf=apf), args=(node, artifacts), callback=partial(
            _on_done,
            artifacts,
            graph,
            node,
            done,
            apf=apf,
        ))

    pool.close()
    pool.join()

    return artifacts

def _on_done(artifacts, graph, node, done, value, apf=False, **kwargs):
    done.add(node)
    artifacts[node] = value
    batch = [
        nxt for nxt in graph[node]
        if not _pendencies(graph, nxt, done)
    ]

    if not batch:
        return

    if len(batch) == 1:
        artifacts[batch[0]] = _resolve(batch[0], artifacts, apf=apf)
        return

    pool = mp.Pool(processes=min(mp.cpu_count(), len(batch)))
    for nxt in batch:
        pool.apply_async(_resolve, args=(nxt, artifacts), callback=partial(
            _on_done,
            artifacts,
            graph,
            nxt,
            done,
            apf=apf,
            **kwargs
        ))

    pool.close()
    pool.join()

def _resolve(node, store, apf=False):
    value = store[node]
    args = utils.arglist(value)
    if isinstance(value, utils.At):
        args = value.args()
        value = value.value()
    keys = [utils.unescape(a) for a in args]
    args = [store[key] for key in keys if key in store]
    unresolved = [key for key in keys if key not in store]
    if not apf and unresolved:
        raise UnresolvedDependencyError("Cannot resolve {}".format(unresolved))
    return _apply(value, *args)
