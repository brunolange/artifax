import unittest
from functools import partial
import math
import json
from artifax import build, At
from artifax.exceptions import UnresolvedDependencyError

class BuildTest(unittest.TestCase):

    def test_empty_build(self):
        artifacts = {}
        result = build(artifacts)
        self.assertEqual(result, {})

    def test_single_artifact_build(self):
        artifacts = {'a': 42}
        result = build(artifacts)
        self.assertEqual(len(result), 1)
        self.assertEqual(result, {'a': 42})

    def test_artifact_immutability(self):
        artifacts = {
            'a': lambda: 42,
            'b': lambda a: a()**2
        }

        results = build(artifacts, solver='async')

        self.assertTrue(isinstance(artifacts, dict))
        self.assertEqual(len(artifacts), 2)
        self.assertEqual(set(artifacts.keys()), {'a', 'b'})
        self.assertTrue(callable(artifacts['b']))
        self.assertFalse(callable(results['b']))

    def test_constant_artifacts_build(self):
        obj = object()
        artifacts = {
            'int': 42,
            'string': 'Hello',
            'obj': obj,
            'list': [1,2,3],
            'dictionary': {'answer': 42},
            'set': set([1,2,3.14])
        }
        result = build(artifacts, solver='linear') # async solver copies objects to subprocess!!
        for k in artifacts:
            self.assertEqual(result[k], artifacts[k])

    def test_sample_build(self):
        artifacts = {
            'A': 42,
            'B': lambda: 7,
            'C': lambda: 10,
            'AB': lambda A, B: A + B(),
            'C minus B': lambda B, C: C() - B(),
            'greet': 'Hello',
            'msg': lambda greet, A: '{} World! The answer is {}.'.format(greet, A),
        }
        result = build(artifacts)
        self.assertEqual(result['AB'], 49)
        self.assertEqual(result['C minus B'], 3)
        self.assertEqual(result['msg'], 'Hello World! The answer is 42.')

    def test_partial_build(self):
        artifacts = {
            'A': lambda x: x**2,
            'B': lambda A, x: A(x),
            'C': lambda A, x: 'A(4)-{} is equal to {}'.format(x, A(4)-x)
        }
        result = build(artifacts, allow_partial_functions=True)
        self.assertTrue(callable(result['A']))
        self.assertEqual(result['A'](4), 16)
        self.assertEqual(result['B'](-5), 25)
        self.assertEqual(result['C'](6), 'A(4)-6 is equal to 10')

    def test_build_with_partial_functions(self):
        artifacts = {
            'a': 42,
            'b': lambda A: A*2
        }
        with self.assertRaises(UnresolvedDependencyError):
            _ = build(artifacts, solver='linear')

        result = build(artifacts, allow_partial_functions=True)
        self.assertIsInstance(result['b'], partial)

    # TODO: fix those!
    # def test_special_keys(self):
    #     artifacts = {
    #         'key-with-dash': 'a value',
    #         'bang': lambda key_with_dash: '{}!'.format(key_with_dash),
    #         '_underscore_key': lambda bang: '_{}_'.format(bang),
    #     }
    #     result = build(artifacts)
    #     self.assertEqual(result['key-with-dash'], 'a value')
    #     self.assertEqual(result['bang'], 'a value!')
    #     self.assertEqual(result['_underscore_key'], '_a value!_')

    def test_at_constructor(self):
        def subtract(p, q):
            return p - q

        result = build({
            'p': 3,
            'q': 5,
            'p - q': subtract,
            'q - p': lambda p, q: subtract(q, p),
        })

        self.assertEqual(result['p - q'], -2)
        self.assertEqual(result['q - p'], 2)

        result = build({
            'a': -11,
            'b': 7.5,
            'a - b': At('a', 'b', subtract),
            'b - a': At('b', 'a', subtract),
        })

        self.assertEqual(result['a - b'], -18.5)
        self.assertEqual(result['b - a'], 18.5)

    def test_deep_build(self):
        for solver in ['linear', 'bfs', 'bfs_parallel', 'async']:
            results = build({
                'a': 'a',
                'b': 'b',
                'x': lambda a: 'x',
                'c': lambda x, b: 'c',
            }, solver=solver)

            self.assertEqual(results['c'], 'c')

    def test_solvers(self):
        def subtract(p, q):
            return p - q

        solvers = ['linear', 'bfs', 'bfs_parallel', 'async']
        results = [build({
            'a': -11,
            'b': 7.5,
            'a - b': At('a', 'b', subtract),
            'b - a': At('b', 'a', subtract),
        }, solver=solver) for solver in solvers]

        # make sure we have as many results as there are solvers
        self.assertEqual(len(results), len(solvers))

        # serialize results and add them to set
        # if results are the same, there should be only one element in the set
        result_set = set([json.dumps(result, sort_keys=True) for result in results])
        self.assertEqual(len(result_set), 1)

        result = json.loads(next(iter(result_set)))
        self.assertEqual(result['a - b'], -18.5)
        self.assertEqual(result['b - a'], 18.5)
