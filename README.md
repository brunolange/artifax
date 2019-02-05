# artifax

artifax is a Python package to evaluate nodes in a computation graph where
the dependencies associated with each node are extracted directly from their
function signatures.

A computation graph can be entirely encoded in a standard python dictionary.
Each key represents a node or an artifact, that will eventually be computed
once all of its dependecies have been calculated. The value associated with
each key can be any constant - a string, a number or an instance of a class,
or a function. In the latter case, the function arguments may map to other nodes
in the computation graph to establish a direct dependency between the nodes.

For example, the following dictionary:

```python
artifacts = {
    'A': 42,
    'B': lambda: 7,
    'C': lambda: 10,
    'AB': lambda A, B: A*B(),
    'C-B': lambda B, C: C() - B(),
    'greeting': 'Hello',
    'message': lambda greeting, A: '{} World! The answer is {}.'.format(greeting, A)
}
```
yields the following computation graph:

![Screenshot](sample-dag.png)

The `build` function evalutes the entire computation graph and returns a new dictionary
with the same keys as the original one and with the calculated values for each of the nodes
in the computation graph.

```python
from artifax import build

artifacts = {
    'A': 42,
    'B': lambda: 7,
    'C': lambda: 10,
    'AB': lambda A, B: A*B(),
    'C-B': lambda B, C: C() - B(),
    'greeting': 'Hello',
    'message': lambda greeting, A: '{} World! The answer is {}.'.format(greeting, A)
}
result = build(artifacts)

for k, v in result.items():
    print('{:<10}: {}'.format(k, v))
```
outputs
```shell
A         : 42
B         : functools.partial(<function <lambda> at 0x101db5e18>)
C         : functools.partial(<function <lambda> at 0x102c4fae8>)
AB        : 294
C-B       : 3
greeting  : Hello
message   : Hello World! The answer is 42.
```

# Artifax class

In addition to the `build` function, artifacts can be built by `Artifax` class
instances.

```python
from artifax import Artifax

afx = Artifax()
afx.set('a', 42)
afx.set('b', lambda a: a*2)
afx.set('c', lambda b: -b)

print(afx.get('c)) # prints -84
```

# Error handling

If the computation graph represented by the artifacts dictionary is not a DAG,
a `CircularDependencyError` exception is thrown.

```python
import artifax
try:
    _ = artifax.build({'x': lambda x: x+1})
except artifax.CircularDependencyError as err:
    print('Cannot build artifacts: {}'.format(err))
    # Cannot build artifacts: artifact graph is not a DAG
```