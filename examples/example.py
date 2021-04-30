from entangle.process import process
from entangle.containers import singularity

import logging
logging.basicConfig(
    format='%(asctime)s : %(levelname)s : %(message)s', level=logging.DEBUG)


@process
def one():
    return 1


@process
def two():
    return 2


@process
def five():
    return 5


@process
def num(n):
    return n


@process
def add(a, b):
    v = int(a) + int(b)
    print("ADD: *"+str(v)+"*")
    return v


@process
def subtract(a, b):
    return int(a) - int(b)


result = add(
            add(
                num(6),
                two() if False else one()
            ),
            subtract(
                five(),
                two()
            )
)

print(result())
