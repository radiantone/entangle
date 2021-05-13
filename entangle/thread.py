"""
thread.py - Module that provides native OS thread implementation of function tasks with support for shared memory
"""
import asyncio
import logging
import sys
import os
import queue as que
import time
import multiprocessing

from functools import partial
import inspect
from threading import Thread
from multiprocessing import Queue
from multiprocessing.shared_memory import SharedMemory
from multiprocessing.managers import SharedMemoryManager

smm = SharedMemoryManager()
smm.start()


def thread(function=None,
           timeout=None,
           wait=None,
           cache=False,
           shared_memory=False,
           sleep=0):
    """

    :param function:
    :param timeout:
    :param cache:
    :param shared_memory:
    :param sleep:
    :return:
    """
    logging.debug("TIMEOUT: %s",timeout)

    def decorator(func):
        def wrapper(_func):
            logging.debug(
                "ThreadMonitor: %s with wait %s", _func, wait)
            return ThreadMonitor(_func,
                                 timeout=timeout,
                                 wait=wait,
                                 shared_memory=shared_memory,
                                 cache=cache,
                                 sleep=sleep)

        return wrapper(func)

    if function is not None:
        return decorator(function)

    return decorator



class ThreadTerminatedException(Exception):
    """

    """


class ThreadTimeoutException(Exception):
    """

    """


class ThreadMonitor:
    """
    Primary monitor class for threades. Creates and monitors queues and threades to resolve argument tasks.
    """

    def __init__(self, func, *args, **kwargs):
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

        if isinstance(self.func, partial):

            def find_func(pfunc):
                if isinstance(pfunc, partial):
                    return find_func(pfunc.func)
                return pfunc

            _func = find_func(self.func)
        else:
            _func = func

        self.source = inspect.getsource(_func)

    def __call__(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        :return:
        """

        logging.info("Thread:invoke: %s",self.func.__name__)
        _func = self.func

        logging.info("Thread:source: %s",self.source)

        def assign_cpu(func, cpu, **kwargs):
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
            def get_result(qfunc, func, sleep, now, _thread, event, wait):
                """

                :param q:
                :param func:
                :param sleep:
                :param now:
                :param thread:
                :param timeout:
                :return:
                """

                logging.debug("get_result: started %s", now)
                if hasattr(func, '__name__'):
                    name = func.__name__
                else:
                    name = func

                while True:
                    logging.debug("Checking queue for result...")
                    try:
                        logging.debug(
                            "Waiting on event for %s with wait %s",name, self.wait)

                        if wait:
                            logging.debug(
                                "Wait event timeout in %s seconds.",wait)
                            event.wait(wait)
                            if not event.is_set():
                                if _thread.is_alive():
                                    _thread.terminate()
                                raise ThreadTimeoutException()
                        else:
                            logging.debug("Waiting until complete.")
                            event.wait()

                        logging.debug("Got event for %s",name)

                        sys.path.append(os.getcwd())
                        _result = qfunc.get()

                        logging.debug("Got result for[%s] %s",
                            name, str(_result))

                        yield

                        return _result

                    except que.Empty as exc:
                        if _thread and not _thread.is_alive():
                            raise ThreadTerminatedException() from exc

                        yield time.sleep(sleep)

            scheduler = None
            cpu = None

            if 'cpu' in kwargs:
                cpu = kwargs['cpu']
                del kwargs['cpu']

                if 'scheduler' in kwargs:
                    scheduler = kwargs['scheduler']
                    del kwargs['scheduler']

            # with smm:
            if len(args) == 0:
                # Do nothing
                pass
            else:
                asyncio.set_event_loop(asyncio.new_event_loop())
                loop = asyncio.get_event_loop()

                _tasks = []
                threades = []

                for arg in args:

                    event = multiprocessing.Event()

                    if hasattr(arg, '__name__'):
                        name = arg.__name__
                    else:
                        name = arg

                    queue = Queue()

                    # Need to pull a cpu off scheduler queue here

                    _thread = None

                    if isinstance(arg, partial):
                        logging.info("Thread: %s",arg.__name__)

                        kargs = {'queue': queue, 'event': event}
                        # If not shared memory

                        # if shared memory, set the handles
                        if self.shared_memory:
                            kargs['smm'] = smm
                            kargs['sm'] = SharedMemory

                        if cpu:
                            arg_cpu = scheduler.get()
                            logging.debug(
                                'ARG CPU SET TO: %s',arg_cpu[1])
                            _thread = Thread(
                                target=assign_cpu, args=(
                                    arg, arg_cpu[1],), kwargs=kargs
                            )
                            _thread.cookie = arg_cpu[1]
                        else:
                            logging.debug('NO CPU SET')
                            _thread = Thread(
                                target=arg, kwargs=kargs)

                        if self.shared_memory:
                            _thread.shared_memory = True

                        threades += [_thread]

                        _thread.start()
                    else:
                        logging.info("Value: %s",name)
                        queue.put(arg)
                        event.set()

                    now = time.time()

                    # Create an async task that monitors the queue for that arg
                    # It will wait for event set from this child thread
                    _tasks += [get_result(queue, arg,
                                          self.sleep, now, _thread, event, self.wait)]

                    # Wait until all the threades report results
                    tasks = asyncio.gather(*_tasks)

                # Ensure we have joined all spawned threades

                args = loop.run_until_complete(tasks)

                _joins = [thread.join() for thread in threades]

                # Put CPU cookie back on scheduler queue
                if scheduler:
                    for thread in threades:
                        logging.debug(
                            "Putting CPU: %s  back on scheduler queue.",thread.cookie)
                        scheduler.put(('0', thread.cookie, 'Y'))

            if cpu:
                pid = os.getpid()
                cpu_mask = [int(cpu)]
                os.sched_setaffinity(pid, cpu_mask)

            if 'queue' in kwargs:
                queue = kwargs['queue']
                # get the queue and delete the argument
                del kwargs['queue']

                event = None
                if 'event' in kwargs:
                    event = kwargs['event']
                    del kwargs['event']

                # Pass in shared memory handles
                if self.shared_memory:
                    kwargs['smm'] = smm
                    kwargs['sm'] = SharedMemory

                logging.info("Calling %s",func.__name__)
                logging.debug(args)

                if not cpu and 'cpu' in kwargs:
                    cpu = kwargs['cpu']
                    del kwargs['cpu']

                if not scheduler and 'scheduler' in kwargs:
                    scheduler = kwargs['scheduler']
                    del kwargs['scheduler']

                result = func(*args, **kwargs)

                # Put own cpu back on queue
                if scheduler and cpu:
                    logging.debug(
                        "Putting CPU: %s  back on scheduler queue.",cpu)
                    scheduler.put(['0', cpu, 'N'])

                if self.cache:
                    pass

                queue.put(result)

                if event:
                    logging.debug(
                        "Setting event for %s",func.__name__)
                    event.set()
            else:
                # Pass in shared memory handles
                if self.shared_memory:
                    kwargs['smm'] = smm
                    kwargs['sm'] = SharedMemory

                logging.debug(
                    "Calling function %s with: %s",func.__name__, str(args))

                result = func(*args, **kwargs)

                if scheduler and cpu:
                    logging.debug(
                        "Putting CPU: %s  back on scheduler queue.",cpu)

                    scheduler.put((0, cpu, 'Y3'))

            return result

        pfunc = partial(invoke, self.func, *args, **kwargs)

        if hasattr(self.func, '__name__'):
            pfunc.__name__ = self.func.__name__
        else:
            pfunc.__name__ = 'thread'

        pfunc.source = self.source
        return pfunc
