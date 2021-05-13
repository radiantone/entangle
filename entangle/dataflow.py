"""
workflow.py - Module that provides workflow decorator
"""
import logging

from functools import partial
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import ProcessPoolExecutor

global PROCESSPOOL, THREADPOOL
PROCESSPOOL = None
THREADPOOL = None   


def process(func):
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
        _workflow = func(*args, **kwargs)
        return _workflow

    inner.thread = False
    inner.func = func
    return inner


def thread(func):
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
        _workflow = func(*args, **kwargs)

        return _workflow

    inner.thread = True
    inner.func = func
    return inner


class DataflowNode:
    """
    Desc
    """

    def __init__(self, func, *args, **kwargs):
        """
        Desc
        :param func:
        :param args:
        :param kwargs:
        """
        self.func = func
        self.args = args

        self.thread = func.thread if hasattr(func, 'thread') else True
        self.partial = partial(func, *self.args)
        self.partial.__name__ = func.__name__

        self.result = kwargs['result'] if 'result' in kwargs else []
        self.callback = kwargs['callback'] if 'callback' in kwargs else None

        logging.debug(self.partial)
        logging.debug("%s self.args", self.args)

        # Build dataflow DAG here

    def __call__(self, *args, **kwargs):

        logging.debug("Inside dataflow: %s",
            self.func.__name__)

        if len(self.args) > 0 and isinstance(self.args[0], DataflowNode):
            logging.debug("Calling partial")

            if callable(self.args[0]) and self.args[0].__name__ == "<lambda>":
                result = self.args[0](*args)
                if isinstance(result, list):
                    for _r in result:
                        _r.__name__ = 'lambda'
                        _df = DataflowNode(_r,*args)
                        _df(*args)
                    return self
                else:
                    result(*args)
                    return self
            else:
                result = self.partial()

            logging.debug("Result %s",result)

            if self.callback:
                logging.debug('Calling callback %s',self.partial.__name__)
                THREADPOOL.submit(self.callback, self.partial.func, result)

            for arg in args:
                if isinstance(arg, DataflowNode):
                    if isinstance(arg, partial):
                        logging.debug("Sending %s to %s",
                            result, arg.func.__name__)

            for arg in args:

                if hasattr(arg,'func'):
                    logging.debug('   LAUNCHING: %s %s',
                        arg.func.__name__, result)
                    logging.debug('     Thread: %s',arg.thread)
                    logging.debug("Calling %s('%s')",
                        arg.func.__name__, result)

                if hasattr(arg,'thread') and arg.thread:
                    THREADPOOL.submit(arg, result, **{'result': self.result})
                else:
                    PROCESSPOOL.submit(arg, result, **{'result': self.result})
        else:
            logging.debug("Calling with args %s %s",
                self.func.__name__, *args)

            result = self.func(*args)

            if self.callback:
                logging.debug('Calling callback %s',self.func.__name__)
                THREADPOOL.submit(self.callback, self.func, result)

            logging.debug("Result %s",result)
            for arg in self.args:
                if isinstance(arg,DataflowNode):
                    logging.debug("Sending %s to %s",
                        result, arg.func.__name__)

            for arg in self.args:
                logging.debug('   LAUNCHING: %s %s',
                    arg.func.__name__, result)
                logging.debug('     Thread: %s',arg.thread)
                logging.debug("Calling %s('%s')",
                    arg.func.__name__, result)

                if arg.thread:
                    THREADPOOL.submit(arg, result)
                else:
                    PROCESSPOOL.submit(arg, result)

        return self


def dataflow(function=None,
             callback=None,
             maxworkers=3):
    """
    Desc
    :param function:
    :param callback:
    :param maxworkers:
    :return:
    """
    global PROCESSPOOL, THREADPOOL

    def decorator(func):
        def wrapper(f_func, *dargs, **dkwargs):
            logging.debug("Calling decorator %s", f_func.__name__)
            logging.debug("dargs %s",str(dargs))

            def invoke(*args, **kwargs):
                logging.debug("invoke f %s %s", f_func, args)
                kwargs['callback'] = callback
                return DataflowNode(f_func, *args, **kwargs)

            return invoke

        return wrapper(func)

    try:
        PROCESSPOOL = ProcessPoolExecutor(max_workers=maxworkers)
        THREADPOOL = ThreadPoolExecutor(max_workers=maxworkers)

        if function is not None:
            return decorator(function)

        return decorator
    finally:
        pass
