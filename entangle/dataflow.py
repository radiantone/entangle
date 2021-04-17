"""
workflow.py - Module that provides workflow decorator
"""
import logging

from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import ProcessPoolExecutor

global _executor
_executor = None


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
        self.partial = partial(func, *self.args)
        print(self.partial)
        print("{} self.args".format(self.func.__name__), args)

    def __call__(self, *args, **kwargs):
        from functools import partial

        print("Inside dataflow: {} {}".format(self.func.__name__, *args))

        '''
        Get my return value
        spawn process for each arg from process pool passing my value to them
        '''
        print("Calling {}".format(self.partial))
        print("Self.Args {}".format(self.args))
        print("Args {}".format(args))

        if len(self.args) > 0 and type(self.args[0]) != DataflowNode:
            print("Calling partial")
            result = self.partial()
            print("Result {}".format(result))
            for arg in args:
                if type(arg) != DataflowNode:
                    print("Sending {} to {}".format(result, arg.func.__name__))

            for arg in args:
                print('   LAUNCHING: ', arg.func.__name__, result)
                _executor.submit(arg, result)
        else:
            print("Calling with args {} {}".format(self.func.__name__, *args))
            result = self.func(*args)
            print("Result {}".format(result))
            for arg in self.args:
                if type(arg) == DataflowNode:
                    print("Sending {} to {}".format(result, arg.func.__name__))

            for arg in self.args:
                print('   ARG Type:', type(arg), arg.func)
                print('   LAUNCHING: ', arg.func.__name__, result)
                _executor.submit(arg, result)

        return self


def dataflow(function=None,
             executor=ThreadPoolExecutor,
             maxworkers=3):
    global _executor

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

    _executor = exectype(max_workers=maxworkers)

    if function is not None:
        return decorator(function)

    return decorator
