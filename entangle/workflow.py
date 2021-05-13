"""
workflow.py - Module that provides workflow decorator
"""
import logging


def workflow(func, **kwargs):
    """
    Desc
    :param func:
    :param kwargs:
    :return:
    """
    def inner(*args, **kwargs):
        """
        Desc
        :param args:
        :param kwargs:
        :return:
        """
        logging.debug("workflow args: %s %s",str(args), str(kwargs))

        if 'cpu' in kwargs:
            del kwargs['cpu']

        _workflow = func(*args, **kwargs)
        # added QoS implementation here
        logging.debug("Inside the workflow")
        return _workflow

    return inner
