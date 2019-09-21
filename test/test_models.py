import unittest
import math
from functools import partial
from artifax import Artifax
from artifax.exceptions import UnresolvedDependencyError
from artifax.utils import At

class ModelTest(unittest.TestCase):

    def test_add(self):
        afx = Artifax()
        afx.set('a', 42)
        self.assertEqual(len(afx), 1)
        self.assertEqual(afx.number_of_nodes(), 1)
        self.assertEqual(afx.number_of_edges(), 0)
        self.assertTrue('a' in afx)

        afx.set('x', lambda a: a/3.14)
        self.assertEqual(len(afx), 2)
        self.assertEqual(afx.number_of_nodes(), 2)
        self.assertEqual(afx.number_of_edges(), 1)
        self.assertTrue('x' in afx)

        self.assertFalse('y' in afx)

    def test_pop(self):
        afx = Artifax()
        afx.set('c', 'C')
        c = afx.pop('c')
        self.assertTrue(len(afx) == 0)
        self.assertEqual(c, 'C')

    def test_build(self):
        obj = object()
        afx = Artifax({
            'int': 42,
            'float': 1.618,
            'string': 'Hello',
            'obj': obj,
            'list': [1,2,3],
            'dictionary': {'answer': 42},
            'set': set([1,2,3.14])
        })
        result = afx.build(solver='linear')
        self.assertEqual(result['int'], 42)
        self.assertEqual(result['float'], 1.618)
        self.assertEqual(result['string'], 'Hello')
        self.assertEqual(result['obj'], obj)
        self.assertEqual(result['list'], [1,2,3])
        self.assertEqual(result['dictionary'], {'answer': 42})
        self.assertEqual(result['set'], set([1,2,3.14]))

    def test_invalid_build(self):
        artifacts = {
            'a': 42,
            'b': lambda A: A*2
        }
        afx = Artifax(artifacts)
        with self.assertRaises(UnresolvedDependencyError):
            _ = afx.build(solver='bfs_parallel')

        result = afx.build(allow_partial_functions=True)
        self.assertIsInstance(result['b'], partial)

    def test_incremental_build(self):
        class ExpensiveObject:
            def __init__(self):
                self.counter = 0
            def expensive_method(self, _):
                self.counter += 1
                return 'foobar'

        exo = ExpensiveObject()
        afx = Artifax(
            p=(3,4),
            q=(12, 13),
            exo=lambda q: exo.expensive_method(q),
        )

        # pool_async silently fails to get trigger callback that resolves
        # the nodes, I guess because it can't pickle ExpensiveObject
        # from the unittest thread
        result = afx.build(solver='linear')
        self.assertEqual(exo.counter, 1)

        afx.set('p', (1,1))
        result = afx.build(solver='linear')
        self.assertEqual(exo.counter, 1)

        afx.set('q', (0,0))
        result = afx.build(solver='linear')
        self.assertEqual(exo.counter, 2)

        afx.set('new', 'hello')
        result = afx.build(solver='linear')
        self.assertEqual(result['new'], 'hello')
        self.assertEqual(exo.counter, 2)

        afx.pop('new')
        result = afx.build(solver='linear')
        self.assertEqual(exo.counter, 2)

    def test_initial(self):
        afx = Artifax({
            'earth': object(),
            'un': lambda earth: 'water @{}'.format(earth),
            'mars': object(),
            'mcrn': lambda mars: 'dust @{}'.format(mars),
            'belt': object(),
            'opa': lambda belt: 'ice @{}'.format(belt)
        })
        self.assertEqual(afx.initial(), set(['earth', 'mars', 'belt']))
        _ = afx.build()

    def test_multiprocessing(self):
        afx = Artifax({
            'p1': 'p1',
            'p2': 'p2',
            'c1': lambda p1: 'c1 after {}'.format(p1),
            'c2': lambda p1: None,
            'c3': lambda p2: None,
            'c4': lambda p2: None,
            'c5': lambda p1, p2, c2, c3: None,
            'c6': lambda c1: None,
            'F':  lambda c1, c2, c3, c4, c5: None,
        })

        c1 = afx.build(targets=('c1',))
        self.assertEqual(c1, 'c1 after p1')

    def test_in_operator(self):
        afx = Artifax(p=(3,4))
        self.assertTrue('p' in afx)
        self.assertFalse('q' in afx)

        afx.pop('p')
        self.assertFalse('p' in afx)

        afx.set('q', (1,2))
        self.assertTrue('q' in afx)

    def test_targeted_build(self):
        afx = Artifax(
            {'greeting': lambda name, punctuation: 'Hello, {}{}'.format(name, punctuation)},
            name='World',
            punctuation=''
        )
        greeting = afx.build(targets='greeting')
        self.assertEqual(greeting, 'Hello, World')

        afx.set('punctuation', '!')
        greeting, punctuation = afx.build(targets=('greeting', 'punctuation'))
        self.assertEqual(greeting, 'Hello, World!')
        self.assertEqual(punctuation, '!')

        result = afx.build()
        self.assertEqual(result['greeting'], 'Hello, World!')
        self.assertEqual(result['name'], 'World')
        self.assertEqual(result['punctuation'], '!')

    def test_stale(self):
        class C:
            counter = 0
            def __init__(self):
                C.counter += 1

        afx = Artifax({
            'a': 42,
            'b': lambda a: math.pow(a, 5),
            'counter': lambda: C(),
        })
        result = afx.build(targets='b')
        self.assertEqual(result, 130691232)

        # 'counter' node should not have been evaluated
        # and should still be stale
        self.assertEqual(C.counter, 0)

        # cannot use async solver here because C won't be
        # pickable from pyunit
        _ = afx.build()['counter']()
        self.assertEqual(C.counter, 1)

    def test_at_constructor(self):
        def subtract(p, q):
            return p - q

        afx = Artifax(
            ab=At('a', 'b', subtract),
            ba=At('b', 'a', subtract),
            a=-11,
            b=7.5,
        )

        ab, ba = afx.build(targets=('ab', 'ba'))
        self.assertEqual(ab, -18.5)
        self.assertEqual(ba, 18.5)
