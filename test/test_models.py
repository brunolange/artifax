import unittest
import math
from functools import partial
from artifax import Artifax

class ModelTest(unittest.TestCase):

    def test_artifax_add(self):
        afx = Artifax()
        afx.set('a', 42)
        self.assertTrue(len(afx) == 1)
        self.assertTrue('a' in afx)

        afx.set('x', lambda a: a/3.14)
        self.assertTrue(len(afx) == 2)
        self.assertTrue('x' in afx)

        self.assertFalse('y' in afx)

    def test_artifax_pop(self):
        afx = Artifax()
        afx.set('c', 'C')
        c = afx.pop('c')
        self.assertTrue(len(afx) == 0)
        self.assertEqual(c, 'C')

    def test_artifax_build(self):
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
        with self.assertRaises(KeyError):
            _ = afx.build()

        result = afx.build(allow_partial_functions=True)
        self.assertIsInstance(result['b'], partial)

    def test_artifax_incremental_build(self):
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
        _ = afx.build()
        self.assertEqual(exo.counter, 1)

        afx.set('p', (1,1))
        _ = afx.build()
        self.assertEqual(exo.counter, 1)

        afx.set('q', (0,0))
        _ = afx.build()
        self.assertEqual(exo.counter, 2)

        afx.set('new', 'hello')
        result = afx.build()
        self.assertEqual(result['new'], 'hello')
        self.assertEqual(exo.counter, 2)

        afx.pop('new')
        _ = afx.build()
        self.assertEqual(exo.counter, 2)

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

if __name__ == '__main__':
    unittest.main()
