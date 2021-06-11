# pylint: disable=locally-disabled, multiple-statements, no-value-for-parameter, invalid-name, too-many-function-args, unused-import, missing-function-docstring
"""
dataflowexamply.py
"""
import threading
import time

from entangle.logging.debug import logging
from entangle.ssh import ssh
from entangle.process import process
from entangle.dataflow import dataflow


def triggered(func, result):
    print("triggered: {} {}".format(func.__name__, result))


@dataflow(callback=triggered)
@ssh(user='darren', host='miko', key='/home/darren/.ssh/id_rsa.pub', python='/home/darren/venv/bin/python')
@process
def printz(z):
    print('printz: {}'.format(threading.current_thread().name))
    with open('/tmp/printz.out', 'w') as pr:
        pr.write("Z: {}".format(z))
    return "Z: {}".format(z)


@dataflow(callback=triggered)
@ssh(user='darren', host='radiant', key='/home/darren/.ssh/id_rsa.pub', python='/home/darren/venv/bin/python')
@process
def printx(x):
    print('printx: {}'.format(threading.current_thread().name))
    with open('/tmp/printx.out', 'w') as pr:
        pr.write("X: {}".format(x))
    return "X: {}".format(x)


@dataflow(callback=triggered)
@process
def printy(y):
    print('printy: {}'.format(threading.current_thread().name))
    return "Y: {}".format(y)


@dataflow(callback=triggered)
@ssh(user='darren', host='radiant', key='/home/darren/.ssh/id_rsa.pub', python='/home/darren/venv/bin/python')
@process
def echo(e):
    print('echo: {}'.format(threading.current_thread().name))
    with open('/tmp/echo.out', 'w') as pr:
        pr.write("Echo! {}".format(e))
    return "Echo! {}".format(e)


@dataflow(callback=triggered, maxworkers=3)
def emit(value):
    print('emit: {}'.format(threading.current_thread().name))
    return value+"!"


if __name__ == '__main__':
    results = []

    # Create the dataflow graph
    flow = emit(
        printx(),
        printz(
            echo()
        )
    )

    # Invoke the dataflow graph with initial input
    result = flow('emit')

    with open('result.out', 'w') as res:
        res.write(str(result))

    print("RESULT: ", result)

    time.sleep(2)
