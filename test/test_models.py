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
        self.assertTrue(len(afx) == 1)
        self.assertTrue('a' in afx)

        afx.set('x', lambda a: a/3.14)
        self.assertTrue(len(afx) == 2)
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
        result = afx.build()
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
            _ = afx.build()

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
        afx = Artifax({
            'p': (3,4),
            'q': (12, 13),
            'exo': lambda q: exo.expensive_method(q),
        })
        result = afx.build()
        self.assertEqual(exo.counter, 1)
        self.assertEqual(len(result.sorting()), len(afx))

        afx.set('p', (1,1))
        result = afx.build()
        self.assertEqual(exo.counter, 1)
        self.assertListEqual(result.sorting(), ['p'])

        afx.set('q', (0,0))
        result = afx.build()
        self.assertEqual(exo.counter, 2)
        self.assertListEqual(result.sorting(), ['q', 'exo'])

        afx.set('new', 'hello')
        result = afx.build()
        self.assertEqual(result['new'], 'hello')
        self.assertEqual(exo.counter, 2)
        self.assertEqual(result.sorting(), ['new'])

        afx.pop('new')
        result = afx.build()
        self.assertEqual(exo.counter, 2)
        self.assertEqual(result.sorting(), [])

    def test_branes(self):
        afx = Artifax({
            'earth': object(),
            'un': lambda earth: 'dirt @{}'.format(earth),
            'mars': object(),
            'mcrn': lambda mars: 'dust @{}'.format(mars),
            'belt': object(),
            'opa': lambda belt: 'ice @{}'.format(belt)
        })
        self.assertEqual(afx.branes(), set(['earth', 'mars', 'belt']))

    def test_in_operator(self):
        afx = Artifax({
            'p': (3,4)
        })
        self.assertTrue('p' in afx)
        self.assertFalse('q' in afx)

        afx.pop('p')
        self.assertFalse('p' in afx)

        afx.set('q', (1,2))
        self.assertTrue('q' in afx)

    def test_result_info(self):
        afx = Artifax({
            'A': 42,
            'B': lambda: 7,
            'C': lambda: 10,
            'AB': lambda A, B: A + B(),
            'C minus B': lambda B, C: C() - B(),
            'greet': 'Hello',
            'msg': lambda greet, A: '{} World! The answer is {}.'.format(greet, A),
        })
        result = afx.build()
        sorting = result.sorting()
        index = lambda k: sorting.index(k)
        self.assertLess(index('A'), index('AB'))
        self.assertGreater(index('msg'), index('greet'))
        self.assertGreater(index('msg'), index('A'))

    def test_targeted_build(self):
        afx = Artifax({
            'name': 'World',
            'punctuation': '',
            'greeting': lambda name, punctuation: 'Hello, {}{}'.format(name, punctuation),
        })
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

        _ = afx.build()['counter']()
        self.assertEqual(C.counter, 1)

    def test_at_constructor(self):
        def subtract(p, q):
            return p - q

        afx = Artifax({
            'ab': At('a', 'b', subtract),
            'ba': At('b', 'a', subtract),
            'a': -11,
            'b': 7.5,
        })

        ab, ba = afx.build(targets=('ab', 'ba'))
        self.assertEqual(ab, -18.5)
        self.assertEqual(ba, 18.5)
