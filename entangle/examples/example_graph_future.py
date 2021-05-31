# pylint: disable=locally-disabled, multiple-statements, no-value-for-parameter, invalid-name, too-many-function-args, unused-import, missing-function-docstring
"""
TBD
"""
import json
import time
import asyncio
from entangle.logging.debug import logging
from entangle.process import process


@process
def one():
    return 1


@process
def two():
    return 2


@process
def five():
    return 5


@process
def num(n):
    return n


@process
def add(a, b):
    v = int(a) + int(b)
    print("ADD: *"+str(v)+"*")
    return v


@process
def subtract(a, b):
    return int(a) - int(b)


if __name__ == '__main__':

    """
    _five = five()
    _two = two()
    _sub = subtract(_five,_two)
    _num = num(6)
    _two2 = two() if False else one()
    _add1 = add(_num,_two2)
    result = add(_add1,_sub)
    """
    workflow = add(
        add(
            num(6),
            two() if False else one()
        ),
        subtract(
            five(),
            add(
                subtract(
                    num(8),
                    two()
                ),
                one()
            )
        )
    )
    result = workflow()
    print(result)

    future = workflow.graph(wait=False)

    def show_graph(graph):
        print("GRAPH:", graph.result())

    future.add_done_callback(show_graph)

    future.entangle()
