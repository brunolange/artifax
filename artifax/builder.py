""" builder.py

This module hosts the core build function and the private functions that aid it.
"""

from functools import reduce, partial
from collections import deque
import pathos.multiprocessing as mp
from exos import compose, each
from . import utils as u
from .exceptions import UnresolvedDependencyError, InvalidSolverError

# pylint: disable=C0103
_apply = lambda v, *args: (
    v(*args) if callable(v) and args and len(u.arglist(v)) == len(args) else
    partial(v, *args) if callable(v) else
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
        'linear': _build_linear,
        'bfs': _build_bfs,
        'bfs_parallel': _build_parallel_bfs,
        'async': _build_async
    }
    if solver not in solvers:
        raise InvalidSolverError('unrecognized solver [{}]'.format(solver))

    return solvers[solver](
        artifacts.copy(),
        apf=allow_partial_functions,
        **kwargs
    )


def _build_linear(artifacts, apf=False):

    def _reducer(store, node):
        store[node] = _resolve(node, store, apf=apf)
        return store

    nodes = compose(u.topological_sort, u.to_graph)(artifacts)
    return reduce(_reducer, nodes, artifacts)


def _pendencies(graph, node, done):
    return {
        k for k, v in graph.items() if node in v and k not in done
    }


def _build_bfs(artifacts, apf=False):
    done = set()
    graph = u.to_graph(artifacts)
    frontier = deque(u.initial(graph))
    while frontier:
        node = frontier.popleft()
        artifacts[node] = _resolve(node, artifacts, apf=apf)
        done.add(node)
        frontier += [nxt for nxt in graph[node] if not _pendencies(graph, nxt, done)]

    return artifacts


def _build_parallel_bfs(artifacts, apf=False, processes=None):
    done = set()
    graph = u.to_graph(artifacts)
    frontier = set(u.initial(graph))
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
    graph = u.to_graph(artifacts)
    frontier = u.initial(graph)

    if not frontier:
        return {}

    done, rem = set(), set()
    if processes is None:
        processes = min(max(1, mp.cpu_count() - 1), len(frontier))
    pool = mp.Pool(processes=processes)

    each(lambda node: pool.apply_async(
        partial(_resolve, apf=apf),
        args=(node, artifacts),
        callback=partial(_on_done, artifacts, graph, node, done, rem, apf=apf)
    ), frontier)

    pool.close()
    pool.join()

    artifacts.update({
        n: _resolve(n, artifacts, apf=apf)
        for n in rem
    })

    return artifacts


def _on_done(artifacts, graph, node, done, rem, value, apf=False, **kwargs):
    done.add(node)
    artifacts[node] = value

    frontier = rem | set(graph[node])
    batch = {n for n in frontier if not _pendencies(graph, n, done)}
    rem = frontier - batch

    if not batch:
        return

    pool = mp.Pool(processes=min(max(1, mp.cpu_count() - 1), len(batch)))

    each(lambda node: pool.apply_async(
        _resolve,
        args=(node, artifacts),
        callback=partial(_on_done, artifacts, graph, node, done, rem, apf=apf, **kwargs)
    ), batch)

    pool.close()
    pool.join()


def _resolve(node, store, apf=False):
    value = store[node]
    args = u.arglist(value)
    if isinstance(value, u.At):
        args = value.args()
        value = value.value()
    keys = [u.unescape(a) for a in args]
    args = [store[key] for key in keys if key in store]
    unresolved = [key for key in keys if key not in store]
    if not apf and unresolved:
        raise UnresolvedDependencyError("Cannot resolve {}".format(unresolved))
    return _apply(value, *args)
