"""
process.py - Module that provides native OS process implementation of function tasks with support for shared memory
"""
import asyncio
import logging
from multiprocessing.shared_memory import SharedMemory
from multiprocessing.managers import SharedMemoryManager

from multiprocessing import resource_tracker

smm = SharedMemoryManager()


def process(function=None,
            timeout=None,
            cache=False,
            shared_memory=False,
            sleep=0):
    """

    :param function:
    :param timeout:
    :param shared_memory:
    :param sleep:
    :return:
    """

    def decorator(func):
        def wrapper(f):
            logging.debug("ProcessMonitor: {}".format(f))
            return ProcessMonitor(f,
                                  timeout=timeout,
                                  shared_memory=shared_memory,
                                  cache=cache,
                                  sleep=sleep)

        return wrapper(func)

    if function is not None:
        return decorator(function)

    return decorator


class ProcessTerminatedException(Exception):
    pass


class ProcessTimeoutException(Exception):
    pass


class ProcessMonitor(object):
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

    def __call__(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        :return:
        """
        from functools import partial
        from multiprocessing import Queue, Process

        logging.info("Process:invoke: {}".format(self.func.__name__))

        def invoke(func, *args, **kwargs):
            import time

            @asyncio.coroutine
            def get_result(q, func, sleep, now, process, timeout):
                import queue
                import time

                if hasattr(func, '__name__'):
                    name = func.__name__
                else:
                    name = func

                while True:
                    try:

                        if timeout is not None and (round(time.time() - now) > timeout):
                            if process.is_alive():
                                process.terminate()
                                raise ProcessTimeoutException()

                        yield time.sleep(sleep)

                        _result = q.get_nowait()

                        logging.debug("Got result for[{}] {}".format(
                            name, str(_result)))

                        return _result

                    except queue.Empty:
                        import time
                        if timeout and round(time.time() - now) > timeout:
                            if process.is_alive():
                                process.terminate()
                                raise ProcessTimeoutException()

                        if process and not process.is_alive():
                            raise ProcessTerminatedException()

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
                        if hasattr(arg, '__name__'):
                            name = arg.__name__
                        else:
                            name = arg

                        queue = Queue()
                        process = None

                        if type(arg) == partial:
                            logging.info("Process: {}".format(arg.__name__))

                            kargs = {}
                            kargs['queue'] = queue

                            # if shared memory, set the handles
                            if self.shared_memory:
                                kargs['smm'] = smm
                                kargs['sm'] = SharedMemory

                            process = Process(
                                target=arg, kwargs=kargs)
                            processes += [process]

                            process.start()
                        else:
                            logging.info("Value:".format(name))
                            queue.put(arg)

                        now = time.time()
                        # Create an async task that monitors the queue for that arg
                        _tasks += [get_result(queue, arg,
                                              self.sleep, now, process, self.timeout)]

                        # Wait until all the processes report results
                        tasks = asyncio.gather(*_tasks)

                    # Ensure we have joined all spawned processes

                    args = loop.run_until_complete(tasks)

                    [process.join() for process in processes]

                if 'queue' in kwargs:
                    queue = kwargs['queue']
                    # get the queue and delete the argument
                    del kwargs['queue']

                    # Pass in shared memory handles
                    if self.shared_memory:
                        kwargs['smm'] = smm
                        kwargs['sm'] = SharedMemory

                    logging.info("Calling {}".format(func.__name__))
                    result = func(*args, **kwargs)

                    if self.cache:
                        pass

                    queue.put(result)
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
