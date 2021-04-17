from entangle.dataflow import dataflow
from entangle.dataflow import process
from entangle.dataflow import thread
import threading

import logging
logging.basicConfig(
    format='%(asctime)s : %(levelname)s : %(message)s', level=logging.DEBUG)


@dataflow
@thread
def printx(x):
    print('printx: ', threading.current_thread().name)
    return("X: {}".format(x))


@dataflow
@thread
def printy(y):
    print('printy: ', threading.current_thread().name)
    return("Y: {}".format(y))


@dataflow
@thread
def printz(z):
    print('printz: ', threading.current_thread().name)
    return("Z: {}".format(z))


@dataflow
@thread
def echo(e):
    print('echo: ', threading.current_thread().name)
    return "Echo! {}".format(e)


@dataflow(executor='thread', maxworkers=1)
def emit(a, **kwargs):
    print("Returning from emit")
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

print(result)

import time
time.sleep(2)
