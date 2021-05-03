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

# Create the dataflow graph 
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

# Invoke the dataflow graph with initial input
flow('emit')

time.sleep(2)

# Call flow again with different input value
flow('HELLO')

