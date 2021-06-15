"""
workflow.py - Module that provides workflow decorator
"""
import logging
import inspect
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
    inner.userfunc = func
    source = inspect.getsource(func)
    inner.source = source
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
        _result = func(*args, **kwargs)

        return _result

    inner.thread = True
    inner.func = func
    inner.userfunc = func
    source = inspect.getsource(func)
    inner.source = source
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
        import sys

        logging.debug("Inside dataflow: %s",
                      self.func.__name__)
        # TODO: Put arg loop here and check each arg for partial of DataflowNode

        # self.args if partials, get invoked passing *args, **kwargs to it
        # for each self.arg
        logging.debug("self.func %s",self.func)
        ff = self.func

        if hasattr(self.func,'dataflow'):
            frame = sys._getframe(0)
            frame.f_locals['dataflow'] = True
        result = self.func(*args, **kwargs)

        if len(self.args) == 0:
            logging.debug("Passing %s to myself %s", args, self.func)

            if self.callback:
                logging.debug('Calling callback %s', self.func.__name__)
                THREADPOOL.submit(self.callback, self.func, result)
        else:
            for _arg in self.args:
                logging.debug("Passing %s to %s", result, _arg)
                if (callable(_arg) and (hasattr(_arg, '__name__') and _arg.__name__ == "<lambda>")):
                    logging.debug("dataflow: Calling lambda %s", _arg)
                    result = _arg(*args)
                    logging.debug("dataflow: lambda result: %s", result)
                    if isinstance(result, list):
                        for _r in result:
                            _r.__name__ = 'lambda'
                            _df = DataflowNode(_r, *args)
                            _df(*args)
                        return self
                    else:
                        if result:
                            logging.debug(
                                "dataflow: Invoking result %s(%s)", result, args)
                            try:
                                _rr = result(*args)
                                logging.debug(
                                    "dataflow: got result(%s)", _rr)
                            except:
                                import traceback
                                print(traceback.format_exc())
                                logging.debug("RESULT EXCEPTION!")
                        return self
                else:
                    try:
                        if callable(_arg):
                            _rr = _arg(result, **kwargs)
                            logging.debug("_rr is %s", _rr)
                    except Exception as ex:
                        import traceback
                        logging.error(traceback.format_exc())
                        pass
                #PROCESSPOOL.submit(_arg, result)

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
            logging.debug("decorator: Calling decorator %s", f_func.__name__)
            logging.debug("decorator: dargs %s", str(dargs))

            def invoke(*args, **kwargs):
                import sys
                logging.debug("decorator: invoke f %s %s", f_func, args)
                kwargs['callback'] = callback
                kwargs['dataflow'] = True
                frame = sys._getframe(0)
                dataflow = True
                f_func.dataflow = True
                #frame.f_locals['dataflow'] = True
                return DataflowNode(f_func, *args, **kwargs)

            return invoke

        if hasattr(func,'func'):
            func.func.dataflow = True
        wrap = wrapper(func)
        wrap.dataflow = True
        try:
            print("decorator: WRAP FUNC:", func)
            wrap.func = func.func
            wrap.userfunc = func
            wrap.source = inspect.getsource(func.func)
        except:
            print("decorator: EXCEPT FUNC:", func)
            wrap.func = func
            wrap.userfunc = func
            wrap.source = inspect.getsource(func)

        return wrap

    try:
        PROCESSPOOL = ProcessPoolExecutor(max_workers=maxworkers)
        THREADPOOL = ThreadPoolExecutor(max_workers=maxworkers)

        if function is not None:
            dec = decorator(function)

            dec.func = function.func
            return dec

        return decorator
    finally:
        pass
