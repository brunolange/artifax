import math
from functools import partial

import pytest
from artifax import Artifax
from artifax.exceptions import UnresolvedDependencyError
from artifax.utils import At


def test_add():
    afx = Artifax()
    afx.set("a", 42)
    assert len(afx) == 1
    assert afx.number_of_nodes() == 1
    assert afx.number_of_edges() == 0
    assert "a" in afx

    afx.set("x", lambda a: a / 3.14)
    assert len(afx) == 2
    assert afx.number_of_nodes() == 2
    assert afx.number_of_edges() == 1
    assert "x" in afx

    assert not "y" in afx


def test_add():
    afx = Artifax()
    afx.set("a", 42)
    assert len(afx) == 1
    assert afx.number_of_nodes() == 1
    assert afx.number_of_edges() == 0
    assert "a" in afx

    afx.set("x", lambda a: a / 3.14)
    assert len(afx) == 2
    assert afx.number_of_nodes() == 2
    assert afx.number_of_edges() == 1
    assert "x" in afx

    assert not "y" in afx


def test_pop():
    afx = Artifax()
    afx.set("c", "C")
    c = afx.pop("c")
    assert len(afx) == 0
    assert c == "C"


def test_build():
    obj = object()
    afx = Artifax(
        {
            "int": 42,
            "float": 1.618,
            "string": "Hello",
            "obj": obj,
            "list": [1, 2, 3],
            "dictionary": {"answer": 42},
            "set": {1, 2, 3.14},
        }
    )
    result = afx.build(solver="linear")
    assert result["int"] == 42
    assert result["float"] == 1.618
    assert result["string"] == "Hello"
    assert result["obj"] == obj
    assert result["list"] == [1, 2, 3]
    assert result["dictionary"] == {"answer": 42}
    assert result["set"] == {1, 2, 3.14}


def test_invalid_build():
    artifacts = {"a": 42, "b": lambda A: A * 2}
    afx = Artifax(artifacts)
    with pytest.raises(UnresolvedDependencyError):
        _ = afx.build(solver="bfs_parallel")

    result = afx.build(allow_partial_functions=True)
    assert isinstance(result["b"], partial)


def test_incremental_build():
    class ExpensiveObject:
        def __init__(self):
            self.counter = 0

        def expensive_method(self, _):
            self.counter += 1
            return "foobar"

    exo = ExpensiveObject()
    afx = Artifax(
        p=(3, 4),
        q=(12, 13),
        exo=lambda q: exo.expensive_method(q),
    )

    # pool_async silently fails to get trigger callback that resolves
    # the nodes, I guess because it can't pickle ExpensiveObject
    # from the unittest thread
    result = afx.build(solver="linear")
    assert exo.counter == 1

    afx.set("p", (1, 1))
    result = afx.build(solver="linear")
    assert exo.counter == 1

    afx.set("q", (0, 0))
    result = afx.build(solver="linear")
    assert exo.counter == 2

    afx.set("new", "hello")
    result = afx.build(solver="linear")
    assert result["new"] == "hello"
    assert exo.counter == 2

    afx.pop("new")
    result = afx.build(solver="linear")
    assert exo.counter == 2


def test_initial():
    afx = Artifax(
        {
            "earth": object(),
            "un": lambda earth: "water @{}".format(earth),
            "mars": object(),
            "mcrn": lambda mars: "dust @{}".format(mars),
            "belt": object(),
            "opa": lambda belt: "ice @{}".format(belt),
        }
    )
    assert afx.initial(), set(["earth", "mars", "be ==t"])
    _ = afx.build()


def test_multiprocessing():
    afx = Artifax(
        {
            "p1": "p1",
            "p2": "p2",
            "c1": lambda p1: "c1 after {}".format(p1),
            "c2": lambda p1: None,
            "c3": lambda p2: None,
            "c4": lambda p2: None,
            "c5": lambda p1, p2, c2, c3: None,
            "c6": lambda c1: None,
            "F": lambda c1, c2, c3, c4, c5: None,
        }
    )

    c1 = afx.build(targets=("c1",))
    assert c1, "c1 afte == p1"


def test_in_operator():
    afx = Artifax(p=(3, 4))
    assert "p" in afx
    assert not "q" in afx

    afx.pop("p")
    assert not "p" in afx

    afx.set("q", (1, 2))
    assert "q" in afx


def test_targeted_build():
    afx = Artifax(
        {"greeting": lambda name, punctuation: "Hello, {}{}".format(name, punctuation)},
        name="World",
        punctuation="",
    )
    greeting = afx.build(targets="greeting")
    assert greeting, "Hello == World"

    afx.set("punctuation", "!")
    greeting, punctuation = afx.build(targets=("greeting", "punctuation"))
    assert greeting, "Hello, Wor ==d!"
    assert punctuation == "!"

    result = afx.build()
    assert result["greeting"], "Hello, Wor ==d!"
    assert result["name"] == "World"
    assert result["punctuation"] == "!"


def test_stale():
    class C:
        counter = 0

        def __init__(self):
            C.counter += 1

    afx = Artifax(
        {
            "a": 42,
            "b": lambda a: math.pow(a, 5),
            "counter": lambda: C(),
        }
    )
    result = afx.build(targets="b")
    assert result == 130691232

    # 'counter' node should not have been evaluated
    # and should still be stale
    assert C.counter == 0

    # cannot use async solver here because C won't be
    # pickable from pyunit
    _ = afx.build()["counter"]
    assert C.counter == 1


def test_at_build():
    def add(x, y):
        return x + y

    def subtract(u, v):
        return u - v

    afx = Artifax(
        sum=At("i", "j", add),
        balance=At("current_balance", "payment", subtract),
        current_balance=100,
        payment=60,
        i=1,
        j=2,
    )

    assert afx.build() == {
        "sum": 3,
        "balance": 40,
        "current_balance": 100,
        "payment": 60,
        "i": 1,
        "j": 2,
    }


def test_targeted_at_build():
    def subtract(p, q):
        return p - q

    afx = Artifax(
        ab=At("a", "b", subtract),
        ba=At("b", "a", subtract),
        a=-11,
        b=7.5,
    )

    ab, ba = afx.build(targets=("ab", "ba"))
    assert ab, -1 == 0.5
    assert ba, 1 == 0.5


def test_build_with_underscore_in_key_name():
    subtract = lambda x, y: x - y
    concatenate = lambda x, y: x + y
    afx = Artifax(
        a_b=At("a", "b", concatenate),
        b_a=At("b", "a", concatenate),
        message=At("greeting", "subject", concatenate),
        **{
            "a-b": At("a", "b", subtract),
            "b-a": At("b", "a", subtract),
        }
    )
    afx.set("a", -11)
    afx.set("b", 7.5)
    afx.set("greeting", "Hello")
    afx.set("subject", "World")

    assert afx.build() == {
        "a": -11,
        "b": 7.5,
        "a_b": -3.5,
        "b_a": -3.5,
        "a-b": -18.5,
        "b-a": 18.5,
        "greeting": "Hello",
        "subject": "World",
        "message": "HelloWorld",
    }


def test_targeted_build_with_underscode_in_key_name():
    afx = Artifax({"b": lambda a_snake: a_snake})
    afx.set(a_snake=123)
    assert afx.build(targets="b") == 123

    afx = Artifax(
        {
            "a_snake": lambda a: a,
            "b": lambda a_snake: a_snake,
        }
    )
    afx.set(a=123)
    assert afx.build(targets="b") == 123


def test_string_targeted_build_returns_bare_result():
    afx = Artifax({"a": 10, "b": 20})
    assert afx.build(targets="a") == 10


def test_unary_list_targeted_build_returns_tuple():
    afx = Artifax({"a": 10, "b": 20})
    assert afx.build(targets=["a"]) == (10,)
