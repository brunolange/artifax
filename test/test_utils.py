from artifax.utils import arglist

def test_arglist():

    def f(foo, bar, bat):
        print(foo, bar, bat)

    def wrapper(*args):
        f(*args)

    import functools
    functools.update_wrapper(wrapper, f)

    assert set(arglist(f)) == set(arglist(wrapper))
