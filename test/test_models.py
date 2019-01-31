import unittest
import math
from artifax import Artifax

class ModelTest(unittest.TestCase):

    def test_artifax_add(self):
        af = Artifax()
        af.set('a', 42)
        self.assertTrue(len(af) == 1)

        af.set('b', lambda a: a/3.14)
        self.assertTrue(len(af) == 2)

    def test_artifax_pop(self):
        af = Artifax()
        af.set('c', 'C')
        c = af.pop('c')
        self.assertEqual(c, 'C')

    def test_artifax_build(self):
        obj = object()
        af = Artifax({
            'int': 42,
            'float': 1.618,
            'string': 'Hello',
            'obj': obj,
            'list': [1,2,3],
            'dictionary': {'answer': 42},
            'set': set([1,2,3.14])
        })
        result = af.build()
        self.assertEqual(result['int'], 42)
        self.assertEqual(result['float'], 1.618)
        self.assertEqual(result['string'], 'Hello')
        self.assertEqual(result['obj'], obj)
        self.assertEqual(result['list'], [1,2,3])
        self.assertEqual(result['dictionary'], {'answer': 42})
        self.assertEqual(result['set'], set([1,2,3.14]))

    def test_artifax_incremental_build(self):
        class ExpensiveObject:
            def __init__(self):
                self.counter = 0
            def expensive_method(self, _):
                self.counter += 1
                return 'foobar'

        exo = ExpensiveObject()
        af = Artifax({
            'p': (3,4),
            'q': (12, 13),
            'exo': lambda q: exo.expensive_method(q),
        })
        _ = af.build()
        self.assertEqual(exo.counter, 1)

        af.set('p', (1,1))
        _ = af.build()
        self.assertEqual(exo.counter, 1)

        af.set('q', (0,0))
        _ = af.build()
        self.assertEqual(exo.counter, 2)

        af.set('new', 'hello')
        result = af.build()
        self.assertEqual(result['new'], 'hello')
        self.assertEqual(exo.counter, 2)

        af.pop('new')
        _ = af.build()
        self.assertEqual(exo.counter, 2)

if __name__ == '__main__':
    unittest.main()
