"""
workflow.py - Module that provides workflow decorator
"""
import logging

from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import ProcessPoolExecutor

global _executor
_executor = None

global processpool, threadpool
processpool = None
threadpool = None
# Add logging to file


def process(func, **kwargs):

    def inner(*args, **kwargs):
        _workflow = func(*args, **kwargs)
        return _workflow

    inner.thread = False
    return inner


def thread(func, **kwargs):

    def inner(*args, **kwargs):
        _workflow = func(*args, **kwargs)

        return _workflow

    inner.thread = True
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
        print(self.partial)
        print("{} self.args".format(self.func.__name__), args)

    def __call__(self, *args, **kwargs):
        from functools import partial

        print("Inside dataflow: {} {}".format(self.func.__name__, *args))

        '''
        Get my return value
        spawn process for each arg from process pool passing my value to them
        '''

        if len(self.args) > 0 and type(self.args[0]) != DataflowNode:
            print("Calling partial")
            result = self.partial()
            print("Result {}".format(result))
            for arg in args:
                if type(arg) != DataflowNode:
                    print("Sending {} to {}".format(result, arg.func.__name__))

            for arg in args:
                print('   LAUNCHING: ', arg.func.__name__, result)
                print('     Thread:', arg.thread)
                print("Calling {}('{}')".format(arg.func.__name__, result))
                if arg.thread:
                    threadpool.submit(arg, result, **{'result': self.result})
                else:
                    processpool.submit(arg, result, **{'result': self.result})
        else:
            print("Calling with args {} {}".format(self.func.__name__, *args))
            result = self.func(*args)
            print("Result {}".format(result))
            for arg in self.args:
                if type(arg) == DataflowNode:
                    print("Sending {} to {}".format(result, arg.func.__name__))

            for arg in self.args:
                print('   ARG Type:', type(arg), arg.func)
                print('     Thread:', arg.thread)
                print('   LAUNCHING: ', arg.func.__name__, result)
                print("Calling {}('{}')".format(arg.func.__name__, result))

                if arg.thread:
                    threadpool.submit(arg, result)
                else:
                    processpool.submit(arg, result)

        return self


def dataflow(function=None,
             executor=ThreadPoolExecutor,
             maxworkers=3):
    global _executor, processpool, threadpool

    def decorator(func):
        from functools import partial

        def wrapper(f, *dargs, **dkwargs):
            print("Calling decorator {}".format(f.__name__))
            print("dargs {}".format(str(dargs)))

            def invoke(*args, **kwargs):
                from functools import partial
                print("invoke f ", f, args)
                return DataflowNode(f, *args, **kwargs)

            return invoke

        def invokepm(pm, *pargs, **pkwargs):
            return pm(*pargs, **pkwargs)

        print('Type func: ', type(func))

        return wrapper(func)

    exectype = ThreadPoolExecutor

    if executor == 'process':
        exectype = ProcessPoolExecutor

    #_executor = exectype(max_workers=maxworkers)
    processpool = ProcessPoolExecutor(max_workers=maxworkers)
    threadpool = ThreadPoolExecutor(max_workers=maxworkers)

    if function is not None:
        return decorator(function)

    return decorator
