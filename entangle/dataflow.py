"""
workflow.py - Module that provides workflow decorator
"""
import logging

from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import ProcessPoolExecutor

global processpool, threadpool
processpool = None
threadpool = None


def process(func, **kwargs):

    def inner(*args, **kwargs):
        _workflow = func(*args, **kwargs)
        return _workflow

    inner.thread = False
    inner.func = func
    return inner


def thread(func, **kwargs):

    def inner(*args, **kwargs):
        _workflow = func(*args, **kwargs)

        return _workflow

    inner.thread = True
    inner.func = func
    return inner


class DataflowNode(object):

    global _executor

    def __init__(self, func, *args, **kwargs):
        from functools import partial
        """

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
        logging.debug("{} self.args".format(self.args))

        # Build dataflow DAG here

    def __call__(self, *args, **kwargs):
        from functools import partial

        logging.debug("Inside dataflow: {} ".format(
            self.func.__name__))

        if len(self.args) > 0 and type(self.args[0]) != DataflowNode:
            logging.debug("Calling partial")

            if callable(self.args[0]) and self.args[0].__name__ == "<lambda>":
                result = self.args[0](*args)
                # TODO: What to do if result is a list of functions?
                if type(result) is list:
                    for r in result:
                        r.__name__ = 'lambda'
                        df = DataflowNode(r,*args)
                        df(*args)
                    return
                else:
                    result(*args)
                    return
            else:
                result = self.partial()

            logging.debug("Result {}".format(result))

            if self.callback:
                logging.debug('Calling callback {}'.format(self.partial.__name__))
                threadpool.submit(self.callback, self.partial.func, result)

            for arg in args:
                if type(arg) != DataflowNode:
                    if type(arg) == partial:
                        logging.debug("Sending {} to {}".format(
                            result, arg.func.__name__))

            for arg in args:

                if hasattr(arg,'func'):
                    logging.debug('   LAUNCHING: {} {}'.format(
                        arg.func.__name__, result))
                    logging.debug('     Thread: {}'.format(arg.thread))
                    logging.debug("Calling {}('{}')".format(
                        arg.func.__name__, result))

                if hasattr(arg,'thread') and arg.thread:
                    threadpool.submit(arg, result, **{'result': self.result})
                else:
                    processpool.submit(arg, result, **{'result': self.result})
        else:
            logging.debug("Calling with args {} {}".format(
                self.func.__name__, *args))

            result = self.func(*args)

            if self.callback:
                logging.debug('Calling callback {}'.format(self.func.__name__))
                threadpool.submit(self.callback, self.func, result)

            logging.debug("Result {}".format(result))
            for arg in self.args:
                if type(arg) == DataflowNode:
                    logging.debug("Sending {} to {}".format(
                        result, arg.func.__name__))

            for arg in self.args:
                logging.debug('   LAUNCHING: {} {}'.format(
                    arg.func.__name__, result))
                logging.debug('     Thread: {}'.format(arg.thread))
                logging.debug("Calling {}('{}')".format(
                    arg.func.__name__, result))

                if arg.thread:
                    threadpool.submit(arg, result)
                else:
                    processpool.submit(arg, result)

        return self


def dataflow(function=None,
             callback=None,
             executor=ThreadPoolExecutor,
             maxworkers=3):
    global _executor, processpool, threadpool

    def decorator(func):
        from functools import partial

        def wrapper(f, *dargs, **dkwargs):
            logging.debug("Calling decorator {}".format(f.__name__))
            logging.debug("dargs {}".format(str(dargs)))

            def invoke(*args, **kwargs):
                from functools import partial
                logging.debug("invoke f {} {}".format(f, args))
                kwargs['callback'] = callback
                return DataflowNode(f, *args, **kwargs)

            return invoke

        return wrapper(func)

    try:
        processpool = ProcessPoolExecutor(max_workers=maxworkers)
        threadpool = ThreadPoolExecutor(max_workers=maxworkers)

        if function is not None:
            return decorator(function)

        return decorator
    finally:
        pass
