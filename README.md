# entangle
A python native parallel processing framework based on simple decorators.

An example of how entangle will be used (still in development)
```python

from entangle.process import process
from entangle.thread import thread
from entangle.task import task
from entangle.local import local
from entangle.aws import aws
from entangle.aws.ec2 import ec2
from entangle.aws.lmbda import lmbda

@process
@local(cpus=4)
def add(a, b):
    return a + b

@process
@aws(keys=[])
@ec2
def one():
    return 1

@lmbda(url='url')
@aws(keys=[])
def two():
    return 2

add = add(
    one(),
    two()
)

print(add())

```