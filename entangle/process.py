"""
process.py - Module that provides native OS process implementation of function tasks with support for shared memory
"""
import asyncio
import logging
import sys
import os
import inspect
import multiprocessing
import time
import queue as que
from typing import Callable
from functools import partial
from multiprocessing import Queue, Process
from multiprocessing.shared_memory import SharedMemory
from multiprocessing.managers import SharedMemoryManager

SMM = SharedMemoryManager()
SMM.start()


def process(function=None,
            timeout=None,
            wait=None,
            cache=False,
            shared_memory=False,
            sleep=0) -> Callable:
    """

    :param function:
    :param timeout:
    :param cache:
    :param shared_memory:
    :param sleep:
    :return:
    """
    logging.debug("TIMEOUT: %s", timeout)

    def decorator(func) -> Callable:
        """
        Description
        :param func:
        :return:
        """
        def wrapper(f_func) -> Callable:
            """
            Description
            :param f_func:
            :return:
            """
            logging.debug(
                "ProcessMonitor: %s with wait %s", f_func, wait)
            return ProcessMonitor(f_func,
                                  timeout=timeout,
                                  wait=wait,
                                  shared_memory=shared_memory,
                                  cache=cache,
                                  sleep=sleep)

        return wrapper(func)

    if function is not None:
        return decorator(function)

    return decorator


class ProcessTerminatedException(Exception):
    """
    Description
    """
    pass


class ProcessTimeoutException(Exception):
    """
    Description
    """
    pass


class ProcessMonitor:
    """
    Primary monitor class for processes. Creates and monitors queues and processes to resolve argument tasks.
    """

    def __init__(self, func, *args, **kwargs) -> Callable:
        """

        :param func:
        :param args:
        :param kwargs:
        """
        self.func = func
        self.shared_memory = kwargs['shared_memory']
        self.sleep = kwargs['sleep']
        self.cache = kwargs['cache']
        self.timeout = kwargs['timeout']
        self.wait = kwargs['wait']
        self.execute = kwargs['execute'] if 'execute' in kwargs else True

    def get_func(self):
        return self.func

    def __call__(self, *args, **kwargs) -> Callable:
        """

        :param args:
        :param kwargs:
        :return:
        """

        logging.info("Process:invoke: %s", self.func.__name__)
        _func = self.func
        if isinstance(self.func, partial):

            def find_func(pfunc):
                if isinstance(pfunc, partial):
                    return find_func(pfunc.func)
                return pfunc

            _func = find_func(self.func)

        self.source = inspect.getsource(_func)

        def assign_cpu(func, cpu, **kwargs):
            """
            Desc
            :param func:
            :param cpu:
            :param kwargs:
            :return:
            """
            pid = os.getpid()
            cpu_mask = [int(cpu)]
            os.sched_setaffinity(pid, cpu_mask)

            func(**kwargs)

        def invoke(func, *args, **kwargs):
            """

            :param func:
            :param args:
            :param kwargs:
            :return:
            """
            @asyncio.coroutine
            def get_result(_queue, func, sleep, now, process, event, wait, timeout):
                """

                :param q:
                :param func:
                :param sleep:
                :param now:
                :param process:
                :param timeout:
                :return:
                """

                if hasattr(func, '__name__'):
                    name = func.__name__
                else:
                    name = func

                logging.debug("get_result: started %s", now)
                while True:
                    logging.debug("Checking queue for result...")
                    try:
                        logging.debug(
                            "Waiting on event for %s with wait %s", name, self.wait)

                        if wait:
                            logging.debug(
                                "Wait event timeout in %s seconds.", wait)
                            event.wait(wait)
                            if not event.is_set():
                                if process.is_alive():
                                    process.terminate()
                                raise ProcessTimeoutException()
                        else:
                            logging.debug("Waiting until complete.")
                            event.wait()

                        logging.debug("Got event for %s", name)

                        logging.debug("Timeout is %s", timeout)
                        if timeout:
                            logging.debug(
                                "Pre get(timeout=%s)", timeout)
                            _result = _queue.get(timeout=timeout)
                            logging.debug(
                                "Post get(timeout=%s)", timeout)
                        else:
                            _result = _queue.get()

                        logging.debug("Got result for[%s] %s",
                                      name, str(_result))

                        yield

                        return _result
                    except multiprocessing.TimeoutError:
                        logging.debug("Timeout exception")
                        raise ProcessTimeoutException()
                    except que.Empty:
                        if process and not process.is_alive():
                            raise ProcessTerminatedException()

                        yield time.sleep(sleep)

            scheduler = None
            cpu = None

            if 'cpu' in kwargs:
                cpu = kwargs['cpu']
                del kwargs['cpu']

                if 'scheduler' in kwargs:
                    scheduler = kwargs['scheduler']
                    del kwargs['scheduler']

            if len(args) == 0:
                # Do nothing
                pass
            else:
                asyncio.set_event_loop(asyncio.new_event_loop())
                loop = asyncio.get_event_loop()

                _tasks = []
                processes = []

                for arg in args:

                    event = multiprocessing.Event()

                    if hasattr(arg, '__name__'):
                        name = arg.__name__
                    else:
                        name = arg

                    _queue = Queue()

                    # Need to pull a cpu off scheduler queue here

                    _process = None

                    if isinstance(arg, partial):
                        logging.info("Process: %s", arg.__name__)

                        kargs = {'queue': _queue, 'event': event}
                        # If not shared memory

                        # if shared memory, set the handles
                        if self.shared_memory:
                            kargs['smm'] = SMM
                            kargs['sm'] = SharedMemory

                        if cpu:
                            arg_cpu = scheduler.get()

                            # TODO: Fix. This bypasses the scheduler logic of capping the CPU #'s.
                            logging.debug(
                                'ARG CPU SET TO: %s', arg_cpu[1])
                            _process = Process(
                                target=assign_cpu, args=(
                                    arg, arg_cpu[1],), kwargs=kargs
                            )
                            _process.cookie = arg_cpu[1]
                        else:
                            logging.debug('NO CPU SET')
                            _process = Process(
                                target=arg, kwargs=kargs)

                        if self.shared_memory:
                            _process.shared_memory = True

                        processes += [_process]

                        _process.start()
                    else:
                        logging.info("Value: %s", name)
                        _queue.put(arg)
                        event.set()

                    now = time.time()

                    # Create an async task that monitors the queue for that arg
                    # It will wait for event set from this child process
                    _tasks += [get_result(_queue, arg,
                                          self.sleep, now, _process, event, self.wait, self.timeout)]

                    # Wait until all the processes report results
                    tasks = asyncio.gather(*_tasks)

                # Ensure we have joined all spawned processes

                args = loop.run_until_complete(tasks)

                _ = [process.join() for process in processes]

                # Put CPU cookie back on scheduler queue
                if scheduler:
                    for _process in processes:
                        logging.debug(
                            "Putting CPU: %s  back on scheduler queue.", _process.cookie)
                        scheduler.put(('0', _process.cookie, 'Y'))

            if cpu:
                pid = os.getpid()
                cpu_mask = [int(cpu)]
                os.sched_setaffinity(pid, cpu_mask)

            event = None
            if 'event' in kwargs:
                event = kwargs['event']
                del kwargs['event']

            if 'queue' in kwargs:
                queue = kwargs['queue']
                # get the queue and delete the argument
                del kwargs['queue']

                # Pass in shared memory handles
                if self.shared_memory:
                    kwargs['smm'] = SMM
                    kwargs['sm'] = SharedMemory

                logging.info("Calling %s", func.__name__)
                logging.debug(args)

                if not cpu and 'cpu' in kwargs:
                    cpu = kwargs['cpu']
                    del kwargs['cpu']

                if not scheduler and 'scheduler' in kwargs:
                    scheduler = kwargs['scheduler']
                    del kwargs['scheduler']

                try:
                    logging.debug("process: execute: %s", self.execute)
                    if self.execute:
                        result = func(*args, **kwargs)
                    else:
                        if event:
                            logging.debug(
                                "Setting event for %s", func.__name__)
                            event.set()
                        return (args, kwargs)
                finally:
                    # Put own cpu back on queue
                    if scheduler and cpu:
                        logging.debug(
                            "Putting CPU: %s back on scheduler queue.", cpu)

                        scheduler.put(['0', cpu, 'N'])

                if self.cache:
                    pass

                queue.put(result)

                if event:
                    logging.debug(
                        "Setting event for %s", func.__name__)
                    event.set()
            else:
                # Pass in shared memory handles
                if self.shared_memory:
                    kwargs['smm'] = SMM
                    kwargs['sm'] = SharedMemory

                logging.debug(
                    "Calling function %s with: %s", func.__name__, str(args))

                # Wrap with Process and queue with timeout
                #logging.debug("Executing function {} in MainThread".format(func))
                #result = func(*args, **kwargs)
                _mq = Queue()

                def func_wrapper(_wf, _wq):
                    logging.debug("func_wrapper: %s", _wf)
                    result = _wf()
                    logging.debug("func_wrapper: result: %s", result)

                    # Unwrap any partials built up by stacked decorators
                    if callable(result):
                        return func_wrapper(result, _wq)
                    try:
                        logging.debug("func_wrapper: putting result on queue")
                        _wq.put(result)
                        logging.debug("func_wrapper: done putting queue")
                    except Exception:
                        import traceback
                        with open('error.out', 'w') as errfile:
                            errfile.write(traceback.format_exc())

                    return None

                pfunc = partial(func, *args, **kwargs)

                logging.debug("process: execute: %s", self.execute)

                try:
                    if self.execute:
                        proc = multiprocessing.Process(
                            target=func_wrapper, args=(pfunc, _mq, ))
                        proc.start()

                        # Wait for 10 seconds or until process finishes
                        logging.debug(
                            "Executing function %s with timeout %s", func, self.timeout)
                        proc.join(self.timeout)
                    else:
                        if event:
                            logging.debug(
                                "Setting event for %s", func.__name__)
                            event.set()
                        return (args, kwargs)
                finally:
                    if scheduler and cpu:
                        logging.debug(
                            "Putting CPU: %s back on scheduler queue.", cpu)

                        scheduler.put(('0', cpu, 'Y'))

                logging.debug("process: waiting for result on queue")

                sys.path.append(os.getcwd())
                result = _mq.get()
                logging.debug("process: got result from queue")

                # If thread is still active
                if proc.is_alive():
                    proc.terminate()
                    proc.join()
                    raise ProcessTimeoutException()

            return result

        pfunc = partial(invoke, self.func, *args, **kwargs)

        if hasattr(self.func, '__name__'):
            pfunc.__name__ = self.func.__name__
        else:
            pfunc.__name__ = 'process'

        return pfunc
