import unittest
from artifax import Artifax

class BuildTest(unittest.TestCase):

    def test_artifax_add(self):
        af = Artifax()
        af.add('a', 42)
        self.assertTrue(len(af) == 1)

        af.add('b', lambda a: a/3.14)
        self.assertTrue(len(af) == 2)

    def test_artifax_pop(self):
        af = Artifax()
        af.add('c', 'C')
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

if __name__ == '__main__':
    unittest.main()
