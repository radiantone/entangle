"""
workflow.py - Module that provides workflow decorator
"""


def workflow(func):
    def inner(*args, **kwargs):
        workflow = func(*args, **kwargs)
        # added QoS implementation here
        return workflow
    return inner