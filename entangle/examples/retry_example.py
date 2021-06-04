# pylint: disable=locally-disabled, multiple-statements, no-value-for-parameter, invalid-name, too-many-function-args, unused-import, missing-function-docstring
"""
TBD
"""
from entangle.logging.file import logging
from entangle.process import process


@process
def one():
    return 1


@process
def two():
    return 2


@process(retry=5)
def five():
    import time
    val = int(str(time.time()).split('.')[1]) % 5
    if val != 0:
        raise Exception("Not a FIVE!")
    return 5


@process
def num(n):
    return n


@process
def add(a, b):
    print(a,b)
    v = int(a) + int(b)
    print("ADD: *"+str(v)+"*")
    return v


@process
def subtract(a, b):
    return int(a) - int(b)


if __name__ == '__main__':

    """
    _five = five()
    _two = two()
    _sub = subtract(_five,_two)
    _num = num(6)
    _two2 = two() if False else one()
    _add1 = add(_num,_two2)
    result = add(_add1,_sub)
    """
    workflow = add(
        add(
            num(6),
            two() if False else one()
        ),
        subtract(
            five(),
            add(
                subtract(
                    num(8),
                    two()
                ),
                one()
            )
        )
    )
    result = workflow()
    print(result)
