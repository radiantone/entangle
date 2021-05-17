# pylint: disable=locally-disabled, multiple-statements, no-value-for-parameter, invalid-name, too-many-function-args, unused-import, missing-function-docstring
"""
TBD
"""
import threading
import time
from entangle.logging.debug import logging
from entangle.dataflow import thread
from entangle.dataflow import process
from entangle.dataflow import dataflow


def triggered(func, result):
    print("triggered: {} {}".format(func.__name__, result))


@dataflow(callback=triggered)
@thread
def printx(x):
    print('printx: {}'.format(threading.current_thread().name))
    return "   X: {}".format(x)


@dataflow(callback=triggered)
@thread
def printy(y):
    print('printy: {}'.format(threading.current_thread().name))
    return "Y: {}".format(y)


@dataflow(callback=triggered)
@thread
def printz(z):
    print('printz: {}'.format(threading.current_thread().name))
    return "     Z: {}".format(z)


@dataflow(callback=triggered, maxworkers=3)
def emit(a):
    print('emit: {}'.format(threading.current_thread().name))
    return a+"!"


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

flow('emit')


time.sleep(2)
