from entangle.logging.info import logging
from entangle.dataflow import thread
from entangle.dataflow import process
from entangle.dataflow import dataflow

import threading
import time

def triggered(func, result):
    print("triggered: {} {}".format(func.__name__, result))


@dataflow(callback=triggered)
@thread
def printx(x):
    print('   printx: {} {}'.format(x, threading.current_thread().name))
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
    return ("Z: {}".format(z))


@dataflow(executor='thread', callback=triggered, maxworkers=3)
def emit(a, **kwargs):
    print('emit: {}'.format(threading.current_thread().name))
    return a+"!"


# Create the dataflow graph
# Defer whether we will forward to printx() or printy() depending
# on the result receive from emit. This won't be known until the data is ready.
flow = emit(
    lambda x: printx(
        printz()
    )
    if x == 'emit' else
    printy()
)

# Invoke the dataflow graph with initial input
flow('emit')

time.sleep(2)
print("----------------------------")
# Call flow again with different input value
flow('HELLO')
