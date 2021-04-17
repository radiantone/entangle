from entangle.dataflow import dataflow

import logging
logging.basicConfig(
    format='%(asctime)s : %(levelname)s : %(message)s', level=logging.DEBUG)


@dataflow
def printx(x):
    return("X: {}".format(x))


@dataflow
def printy(y):
    return("Y: {}".format(y))


@dataflow
def printz(z):
    return("Z: {}".format(z))


@dataflow
def echo(e):
    return "Echo! {}".format(e)


@dataflow(executor='thread', maxworkers=4)
def emit(a):
    print("Returning from emit")
    return a+"!"


# initial dataflow input
emit = emit('emit')
#printx = printx('PREPRINTX')

result = emit(
    printx(
        printz(
            echo()
        )
    ),
    printy(
        printz()
    )
)

print(result)
