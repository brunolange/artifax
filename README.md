# artifax

artifax is a Python package to evaluate nodes in a computation graph where
the dependencies associated with each node are extracted directly from their
function signatures.

# examples
```python
>>> from artifax import build
>>> artifacts = {
>>>     'A': 42,
>>>     'B': lambda: 7,
>>>     'C': lambda: 10,
>>>     'AB': lambda A, B: A*B(),
>>>     'C minus B': lambda B, C: C() - B(),
>>>     'greeting': 'Hello',
>>>     'message': lambda greeting, A: '{} World! The answer is {}.'.format(greeting, A),
>>> }
>>> result = build(artifacts)
>>> print(type(result))
<class 'dict'>
>>> _ = [print('{:<10}: {}'.format(k, v)) for k, v in result.items()]
A         : 42
B         : functools.partial(<function <lambda> at 0x102c34ea0>)
C minus B : 3
C         : functools.partial(<function <lambda> at 0x102d9d6a8>)
AB        : 294
greeting  : Hello
message   : Hello World! The answer is 42.
>>> print(result['message'])
Hello World! The answer is 42.