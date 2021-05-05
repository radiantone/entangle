"""
tests.test_entangle.py
~~~~~~~~~~~~~~~~~~~~

"""
from entangle.process import process


class TestEntangle:
    """Test suite for entangle app class."""

    def test_example4(self):
        from entangle.examples.example4 import dopow, createvectors

        result = dopow(
            createvectors()
        )

        try:
            result()
            assert True
        except:
            assert False

    def test_example3(self):
        from entangle.examples.example3 import durations, dovectors1, dovectors2

        result = durations(
            dovectors1(),
            dovectors2()
        )

        try:
            result()
            assert True
        except:
            assert False
