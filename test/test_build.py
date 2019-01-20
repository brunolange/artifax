import unittest
from artifax import build

class BuildTest(unittest.TestCase):

    def test_empty_build(self):
        artifacts = {}
        result = build(artifacts)
        self.assertEqual(result, {})

    def test_single_artifact_build(self):
        artifacts = {'a': lambda: 42}
        result = build(artifacts)
        self.assertEqual(len(result), 1)
        self.assertEqual(result, {'a': 42})

    def test_artifact_immutability(self):
        artifacts = {'a': lambda: 42}
        _ = build(artifacts)

        self.assertTrue(isinstance(artifacts, dict))
        self.assertEqual(len(artifacts), 1)
        self.assertEqual(list(artifacts.keys()), ['a'])
        self.assertTrue(callable(artifacts['a']))

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
        result = build(artifacts)
        for k in artifacts:
            self.assertEqual(result[k], artifacts[k])

    def test_sample_build(self):
        artifacts = {
            'A': 42,
            'B': lambda: 7,
            'C': lambda: 10,
            'AB': lambda A, B: A + B,
            'C minus B': lambda B, C: C - B,
            'greet': 'Hello',
            'msg': lambda greet, A: '{} World! The answer is {}.'.format(greet, A),
        }
        result = build(artifacts)
        self.assertEqual(result['AB'], 49)
        self.assertEqual(result['C minus B'], 3)
        self.assertEqual(result['msg'], 'Hello World! The answer is 42.')

if __name__ == '__main__':
    unittest.main()
