from entangle.logging.debug import logging
from entangle.process import process


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


if __name__ == '__main__':
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