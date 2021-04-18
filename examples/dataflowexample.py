import threading
from entangle.dataflow import thread
from entangle.dataflow import process
from entangle.dataflow import dataflow
import time

import logging
logging.basicConfig(filename='example.log',
                    format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)


def triggered(func, result):
    print("triggered: {} {}".format(func.__name__, result))


@dataflow(callback=triggered)
@thread
def printx(x):
    print('printx: {}'.format(threading.current_thread().name))
    return("X: {}".format(x))


@dataflow(callback=triggered)
@thread
def printy(y):
    print('printy: {}'.format(threading.current_thread().name))
    return("Y: {}".format(y))


@dataflow(callback=triggered)
@thread
def printz(z):
    print('printz: {}'.format(threading.current_thread().name))
    return("Z: {}".format(z))


@dataflow(callback=triggered)
@thread
def echo(e):
    print('echo: {}'.format(threading.current_thread().name))
    return "Echo! {}".format(e)


@dataflow(executor='thread', callback=triggered, maxworkers=3)
def emit(a, **kwargs):
    print('emit: {}'.format(threading.current_thread().name))
    return a+"!"


results = []

# initial dataflow input
emit = emit('emit', result=results)
#printx = printx('PREPRINTX')

result = emit(
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


time.sleep(2)
