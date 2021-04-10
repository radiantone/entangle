"""
workflow.py - Module that provides workflow decorator
"""
import logging


def workflow(func, **kwargs):

    def inner(*args, **kwargs):
        _workflow = func(*args, **kwargs)
        # added QoS implementation here
        logging.debug("Inside the workflow")
        return _workflow

    return inner
