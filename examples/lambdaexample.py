import threading
import time
from entangle.dataflow import thread
from entangle.dataflow import process
from entangle.dataflow import dataflow

import logging
logging.basicConfig(filename='example.log',
                    format='%(asctime)s : %(levelname)s : %(message)s', level=logging.DEBUG)


def triggered(func, result):
    print("triggered: {} {}".format(func.__name__, result))


@dataflow(callback=triggered)
@thread
def printx(x):
    print('printx')
    print('printx: {}'.format(threading.current_thread().name))
    return("X: {}".format(x))


@dataflow(callback=triggered)
@thread
def printy(y):
    print('printy')
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
    print("a: ",a)
    return a+"!"


results = []

# Create the dataflow graph 
# Defer whether we will forward to printx() or printy() depending
# on the result receive from emit. This won't be known until the data is ready.
flow = emit(
    lambda x: printx() if x == 'emit' else printy()
    #printx()
)

# Invoke the dataflow graph with initial input
flow('emit')

time.sleep(2)

# Call flow again with different input value
flow('HELLO')
