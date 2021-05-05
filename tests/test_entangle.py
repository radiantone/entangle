"""
tests.test_entangle.py
~~~~~~~~~~~~~~~~~~~~

"""
from entangle.process import process

class TestEntangle:
    """Test suite for entangle app class."""

    def test_example2(self):
        from entangle.examples.example2 import workflow1, workflow2

        result = workflow2(workflow1)

        try:
            result()
            assert True
        except:
            assert False

    def test_example(self):
        from entangle.examples.example import add,num,one,two,five, subtract

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
        assert result() == 10

