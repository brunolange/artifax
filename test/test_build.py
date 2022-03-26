import json
from functools import partial

import pytest

from artifax import At, build
from artifax.exceptions import UnresolvedDependencyError


def test_empty_build():
    assert build({}) == {}


def test_single_artifact_build():
    assert build({"a": 42}) == {"a": 42}


def test_artifact_immutability():
    artifacts = {"a": 42, "b": lambda a: a**2}

    results = build(artifacts, solver="async")

    assert isinstance(artifacts, dict)
    assert len(artifacts) == 2
    assert set(artifacts.keys()) == {"a", "b"}
    assert callable(artifacts["b"])
    assert not callable(results["b"])


def test_constant_artifacts_build():
    obj = object()
    artifacts = {
        "int": 42,
        "string": "Hello",
        "obj": obj,
        "list": [1, 2, 3],
        "dictionary": {"answer": 42},
        "set": set([1, 2, 3.14]),
    }
    result = build(
        artifacts, solver="linear"
    )  # async solver copies objects to subprocess!!
    assert result["obj"] is obj
    assert result == artifacts


def test_sample_build():
    artifacts = {
        "A": 42,
        "B": lambda: 7,
        "C": lambda: 10,
        "AB": lambda A, B: A + B,
        "C minus B": lambda B, C: C - B,
        "greet": "Hello",
        "msg": lambda greet, A: "{} World! The answer is {}.".format(greet, A),
    }
    result = build(artifacts)
    assert result["AB"] == 49
    assert result["C minus B"] == 3
    assert result["msg"] == "Hello World! The answer is 42."


def test_partial_build():
    artifacts = {
        "A": lambda x: x**2,
        "B": lambda A, x: A(x),
        "C": lambda A, x: "A(4)-{} is equal to {}".format(x, A(4) - x),
    }
    result = build(artifacts, allow_partial_functions=True)
    assert callable(result["A"])
    assert result["A"](4) == 16
    assert result["B"](-5) == 25
    assert result["C"](6), "A(4)-6 is equal to 10"


def test_build_with_partial_functions():
    artifacts = {"a": 42, "b": lambda A: A * 2}
    with pytest.raises(UnresolvedDependencyError):
        _ = build(artifacts, solver="linear")

    result = build(artifacts, allow_partial_functions=True)
    assert isinstance(result["b"], partial)


def test_at_constructor():
    def subtract(p, q):
        return p - q

    result = build(
        {
            "p": 3,
            "q": 5,
            "p - q": subtract,
            "q - p": lambda p, q: subtract(q, p),
        }
    )

    assert result["p - q"] == -2
    assert result["q - p"] == 2

    result = build(
        {
            "a": -11,
            "b": 7.5,
            "a - b": At("a", "b", subtract),
            "b - a": At("b", "a", subtract),
        }
    )

    assert result["a - b"] == -18.5
    assert result["b - a"] == 18.5


def test_deep_build():
    for solver in ["linear", "bfs", "bfs_parallel", "async"]:
        results = build(
            {
                "a": "a",
                "b": "b",
                "x": lambda a: "x",
                "c": lambda x, b: "c",
            },
            solver=solver,
        )

        assert results["c"] == "c"


def test_solvers():
    def subtract(p, q):
        return p - q

    solvers = ["linear", "bfs", "bfs_parallel", "async"]
    results = [
        build(
            {
                "a": -11,
                "b": 7.5,
                "a - b": At("a", "b", subtract),
                "b - a": At("b", "a", subtract),
            },
            solver=solver,
        )
        for solver in solvers
    ]

    # make sure we have as many results as there are solvers
    assert len(results) == len(solvers)

    # serialize results and add them to set
    # if results are the same, there should be only one element in the set
    result_set = set(json.dumps(result, sort_keys=True) for result in results)
    assert len(result_set) == 1

    result = json.loads(next(iter(result_set)))
    assert result["a - b"] == -18.5
    assert result["b - a"] == 18.5
