"""
tests.test_entangle.py
~~~~~~~~~~~~~~~~~~~~

"""
from entangle.process import (app)


@app
def one():
    return 1


@app
def two():
    return 2


@app
def five():
    return 5


@app
def num(n):
    return n


@app
def add(a, b):
    v = int(a) + int(b)
    print("ADD: *"+str(v)+"*")
    return v


@app
def subtract(a, b):
    return int(a) - int(b)


class TestEntangle:
    """Test suite for entangle app class."""

    def test_example(self):
        result = add(
            add(
                num(6),
                two()
            ),
            subtract(
                five(),
                two()
            )
        )
        assert result() == 11

