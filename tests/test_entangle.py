"""
tests.test_entangle.py
~~~~~~~~~~~~~~~~~~~~

"""
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

