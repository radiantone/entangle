"""
tests.test_entangle.py
~~~~~~~~~~~~~~~~~~~~

"""


class TestEntangle:
    """Test suite for entangle app class."""

    def test_dataflowexample2(self):
        from entangle.logging.debug import logging
        from entangle.examples.dataflowexample2 import emit, printx, printy, printz, echo

        flow = emit(
            printx(
                printz(
                    echo()
                )
            ),
            printy(
                printz()
            ),
            printy()
        )
        try:
            flow('emit')
            assert True
        except:
            assert False


    def test_dataflowexample(self):
        from entangle.logging.debug import logging
        from entangle.examples.dataflowexample import emit, printx, printy, printz, echo


        flow = emit(
            printx(
                printz(
                    echo()
                )
            ),
            printy(
                printz()
            ),
            printy()
        )
        try:
            flow('emit')
            assert True
        except:
            assert False


    def test_schedulerexample2(self):
        from entangle.logging.info import logging
        from entangle.examples.schedulerexample2 import workflow2

        result = workflow2()
        try:
            result()
            assert True
        except:
            assert False


    def test_schedulerexample(self):
        from entangle.logging.info import logging
        from entangle.examples.schedulerexample import workflow2

        result = workflow2()
        try:
            result()
            assert True
        except:
            assert False


    def test_listexample2(self):
        from entangle.logging.info import logging
        from entangle.examples.listexample2 import emit, printx, printy, printz

        flow = emit(
            lambda x: list(map(lambda f: f(x), [
                lambda y: [printx(
                    printz()
                ) for _ in range(0, 10)],
                printy(
                    printz()
                )
            ]))[0]
        )

        try:
            flow('emit')
            assert True
        except:
            assert False


    def test_listexample(self):
        from entangle.logging.info import logging
        from entangle.examples.listexample import emit, printx, printy, printz

        flow = emit(
            lambda x: [printy(
                printz(
                    printx()
                )
            ) for _ in range(0, 10)]
        )

        try:
            flow('emit')
            assert True
        except:
            assert False

    def test_lambdaexample(self):
        from entangle.logging.info import logging
        from entangle.examples.lambdaexample import emit, printx, printy, printz

        flow = emit(
            lambda x: printx(
                printz()
            )
            if x == 'emit' else
            printy()
        )

        try:
            flow('emit')
            assert True
        except:
            assert False

    def test_example6(self):
        from entangle.logging.info import logging
        from entangle.examples.example6 import workflow1, workflow2

        result = workflow2(workflow1)

        try:
            result()
            assert True
        except:
            assert False

    def test_example5(self):
        from entangle.logging.info import logging
        from entangle.examples.example5 import workflow1, workflow2

        result = workflow2(workflow1)

        try:
            result()
            assert True
        except:
            import traceback
            print(traceback.format_exc())
            assert False

    def test_example2(self):
        from entangle.logging.debug import logging
        from entangle.examples.example2 import workflow1, workflow2

        result = workflow2(workflow1)

        try:
            result()
            assert True
        except:
            assert False

    def test_example(self):
        from entangle.logging.debug import logging
        from entangle.examples.example import add, num, one, two, five, subtract

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
