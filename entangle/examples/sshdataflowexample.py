from entangle.logging.debug import logging
from entangle.dataflow import process
from entangle.dataflow import dataflow
from entangle.ssh import ssh
from entangle.scheduler import scheduler

import threading
import time


def triggered(func, result):
    print("triggered: {} {}".format(func.__name__, result))


scheduler_config = {'cpus': 2,
                    'impl': 'entangle.scheduler.DefaultScheduler'}


@scheduler(**scheduler_config)
@dataflow(callback=triggered)
@process
def printx(x):
    print('printx: {}'.format(threading.current_thread().name))
    return("X: {}".format(x))


@scheduler(**scheduler_config)
@dataflow(callback=triggered)
@process
def printy(y):
    print('printy: {}'.format(threading.current_thread().name))
    return("Y: {}".format(y))

@ssh(user='darren', host='radiant', key='/home/darren/.ssh/id_rsa.pub', python='/home/darren/venv/bin/python')
@scheduler(**scheduler_config)
@dataflow(callback=triggered)
@process
def printz(z):
    print('printz: {}'.format(threading.current_thread().name))
    return("Z: {}".format(z))


@scheduler(**scheduler_config)
@dataflow(callback=triggered)
@process
def echo(e):
    print('echo: {}'.format(threading.current_thread().name))
    return "Echo! {}".format(e)


@scheduler(**scheduler_config)
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

