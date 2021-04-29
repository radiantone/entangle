"""
process.py - Module that provides native OS process implementation of function tasks with support for shared memory
"""
import asyncio
import logging
import multiprocessing
from multiprocessing.shared_memory import SharedMemory
from multiprocessing.managers import SharedMemoryManager

from multiprocessing import resource_tracker

smm = SharedMemoryManager()


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
    print("TIMEOUT: ", timeout)

    def decorator(func):
        def wrapper(f):
            logging.debug(
                "ThreadMonitor: {} with wait {}".format(f, wait))
            return ThreadMonitor(f,
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
    pass


class ThreadTimeoutException(Exception):
    """

    """
    pass


class PoolMonitor(object):
    pass


class ThreadMonitor(object):
    """
    Primary monitor class for processes. Creates and monitors queues and processes to resolve argument tasks.
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

    def __call__(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        :return:
        """
        from functools import partial
        from multiprocessing import Queue
        from threading import Thread

        logging.info("Thread:invoke: {}".format(self.func.__name__))
        print("Thread kwargs:", *kwargs)

        def invoke(func, *args, **kwargs):
            """

            :param func:
            :param args:
            :param kwargs:
            :return:
            """
            import time

            @asyncio.coroutine
            def get_result(q, func, sleep, now, process, event, wait):
                """

                :param q:
                :param func:
                :param sleep:
                :param now:
                :param process:
                :param timeout:
                :return:
                """
                import queue
                import time

                if hasattr(func, '__name__'):
                    name = func.__name__
                else:
                    name = func

                while True:
                    logging.debug("Checking queue for result...")
                    try:
                        logging.debug(
                            "Waiting on event for {} with wait {}".format(name, self.wait))

                        if wait:
                            logging.debug(
                                "Wait event timeout in {} seconds.".format(wait))
                            event.wait(wait)
                            if not event.is_set():
                                if process.is_alive():
                                    process.terminate()
                                raise ThreadTimeoutException()
                        else:
                            logging.debug("Waiting until complete.")
                            event.wait()

                        logging.debug("Got event for {}".format(name))

                        _result = q.get()

                        logging.debug("Got result for[{}] {}".format(
                            name, str(_result)))

                        yield

                        return _result

                    except queue.Empty:
                        import time

                        if process and not process.is_alive():
                            raise ThreadTerminatedException()

                        yield time.sleep(sleep)

            with smm:
                if len(args) == 0:
                    # Do nothing
                    pass
                else:
                    asyncio.set_event_loop(asyncio.new_event_loop())
                    loop = asyncio.get_event_loop()

                    _tasks = []
                    processes = []

                    for arg in args:

                        e = multiprocessing.Event()

                        if hasattr(arg, '__name__'):
                            name = arg.__name__
                        else:
                            name = arg

                        queue = Queue()
                        _process = None

                        if type(arg) == partial:
                            logging.info("Thread: {}".format(arg.__name__))

                            kargs = {'queue': queue, 'event': e}
                            # If not shared memory

                            # if shared memory, set the handles
                            if self.shared_memory:
                                kargs['smm'] = smm
                                kargs['sm'] = SharedMemory

                            _process = Thread(
                                target=arg, kwargs=kargs)

                            if self.shared_memory:
                                _process.shared_memory = True

                            processes += [_process]

                            _process.start()
                        else:
                            logging.info("Value:".format(name))
                            queue.put(arg)
                            e.set()

                        now = time.time()

                        # Create an async task that monitors the queue for that arg
                        # It will wait for event set from this child process
                        _tasks += [get_result(queue, arg,
                                              self.sleep, now, _process, e, self.wait)]

                        # Wait until all the processes report results
                        tasks = asyncio.gather(*_tasks)

                    # Ensure we have joined all spawned processes

                    args = loop.run_until_complete(tasks)

                    [process.join() for process in processes]

                if 'cpu' in kwargs:
                        del kwargs['cpu']

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

                    logging.info("Calling {}".format(func.__name__))

                    result = func(*args, **kwargs)

                    if self.cache:
                        pass

                    queue.put(result)

                    if event:
                        logging.debug(
                            "Setting event for {}".format(func.__name__))
                        event.set()
                else:
                    # Pass in shared memory handles
                    if self.shared_memory:
                        kwargs['smm'] = smm
                        kwargs['sm'] = SharedMemory

                    logging.debug(
                        "Calling function with: {}".format(str(args)))
                    result = func(*args, **kwargs)

                return result

        p = partial(invoke, self.func, *args, **kwargs)

        if hasattr(self.func, '__name__'):
            p.__name__ = self.func.__name__
        else:
            p.__name__ = 'process'

        return p
