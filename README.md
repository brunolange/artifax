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
>>>     'AB': lambda A, B: A + B,
>>>     'C minus B': lambda B, C: C - B,
>>>     'greet': 'Hello',
>>>     'msg': lambda greet, A: '{} World! The answer is {}.'.format(greet, A),
>>> }
>>> result = build(artifacts)
>>> print(type(result))
<class 'dict'>
>>> _ = [print('{}: {}'.format(k, v)) for k, v in result.items()]
A: 42
B: 7
C: 10
AB: 49
C minus B: 3
greet: Hello
msg: Hello World! The answer is 42.
>>> print(result['msg'])
Hello World! The answer is 42.