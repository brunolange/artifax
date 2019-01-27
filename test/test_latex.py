import unittest
from artifax import io

class BuildTest(unittest.TestCase):

    def test_sample(self):
        artifacts = {
            'A': 42,
            'B': lambda: 7,
            'C': lambda: 10,
            'AB': lambda A, B: A + B(),
            'C minus B': lambda B, C: C() - B(),
            'greeting': 'Hello',
            'message': lambda greeting, A: '{} World! The answer is {}.'.format(greeting, A),
        }
        lines = io.tex(artifacts).split('\n')

        expected_nodes = [
            '\\node[state] ({}) {{${}$}};'.format(node, node)
            for node in artifacts
        ]

        expected_edges = [
            '(A) edge [mystyle] (AB)',
            '(B) edge [mystyle] (AB)',
            '(B) edge [mystyle] (C minus B)',
            '(C) edge [mystyle] (C minus B)',
            '(greeting) edge [mystyle] (message)'
        ]

        report = lambda l: 'missing line: [{}]'.format(l)
        for expected_line in expected_nodes + expected_edges:
            self.assertTrue(expected_line in lines, report(expected_line))
