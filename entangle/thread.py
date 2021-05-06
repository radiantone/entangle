"""
thread.py - Module that provides native OS thread implementation of function tasks with support for shared memory
"""
import asyncio
import logging
import multiprocessing
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
    logging.debug("TIMEOUT: {}".format(timeout))

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


def pool(function=None,
         timeout=None,
         wait=None,
         cache=False,
         shared_memory=False,
         sleep=0):
    """
    A thread pool that executes the workflow callgraph inside out so it
    can pool only the graph leaf nodes in a thread pool executor.

    :param function:
    :param timeout:
    :param cache:
    :param shared_memory:
    :param sleep:
    :return:
    """

    def decorator(func):
        def wrapper(f):

            class poolmonitor():

                def __init__(self, func, *args, **kwargs):

                    self.func = func

                def __call__(self, *args, **kwargs):
                    from functools import partial
                    # return partial here
                    logging.debug("FUNC: {}".format(self.func.__name__))
                    logging.debug("ARGS: {}".format(str(args)))

                    if len(args) > 0:
                        logging.debug("POOL: {}".format(str(args)))
                        # Only send partial functions to the pol

                    p = partial(self.func)
                    p.__name__ = self.func.__name__
                    p.pargs = args
                    p.pkwargs = kwargs
                    return p

            pm = poolmonitor(f)

            # Once we have the poolmonitor call graph, we need to traverse
            # it and invert the calling sequence and ensure that argument
            # results get gather before a new thread function is given to the pool

            return pm

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
    Primary monitor class for threades. Creates and monitors queues and threades to resolve argument tasks.
    """

    def __init__(self, func, *args, **kwargs):
        """

        :param func:
        :param args:
        :param kwargs:
        """
        from functools import partial
        import inspect

        self.func = func
        self.shared_memory = kwargs['shared_memory']
        self.sleep = kwargs['sleep']
        self.cache = kwargs['cache']
        self.timeout = kwargs['timeout']
        self.wait = kwargs['wait']

        if type(self.func) is partial:

            def find_func(p):
                if type(p) is partial:
                    return find_func(p.func)
                return p

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
        from functools import partial
        from multiprocessing import Queue
        from threading import Thread

        logging.info("Thread:invoke: {}".format(self.func.__name__))
        _func = self.func

        logging.info("Thread:source: {}".format(self.source))

        def assign_cpu(func, cpu, **kwargs):
            import os

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
            import time
            import os

            @asyncio.coroutine
            def get_result(q, func, sleep, now, thread, event, wait):
                """

                :param q:
                :param func:
                :param sleep:
                :param now:
                :param thread:
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
                                if thread.is_alive():
                                    thread.terminate()
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

                        if thread and not thread.is_alive():
                            raise ThreadTerminatedException()

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

                    e = multiprocessing.Event()

                    if hasattr(arg, '__name__'):
                        name = arg.__name__
                    else:
                        name = arg

                    queue = Queue()

                    # Need to pull a cpu off scheduler queue here

                    _thread = None

                    if type(arg) == partial:
                        logging.info("Thread: {}".format(arg.__name__))

                        kargs = {'queue': queue, 'event': e}
                        # If not shared memory

                        # if shared memory, set the handles
                        if self.shared_memory:
                            kargs['smm'] = smm
                            kargs['sm'] = SharedMemory

                        if cpu:
                            arg_cpu = scheduler.get()
                            logging.debug(
                                'ARG CPU SET TO: {}'.format(arg_cpu[1]))
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
                        logging.info("Value:".format(name))
                        queue.put(arg)
                        e.set()

                    now = time.time()

                    # Create an async task that monitors the queue for that arg
                    # It will wait for event set from this child thread
                    _tasks += [get_result(queue, arg,
                                          self.sleep, now, _thread, e, self.wait)]

                    # Wait until all the threades report results
                    tasks = asyncio.gather(*_tasks)

                # Ensure we have joined all spawned threades

                args = loop.run_until_complete(tasks)

                [thread.join() for thread in threades]

                # Put CPU cookie back on scheduler queue
                if scheduler:
                    for thread in threades:
                        logging.debug(
                            "Putting CPU: {}  back on scheduler queue.".format(thread.cookie))
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

                logging.info("Calling {}".format(func.__name__))
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
                        "Putting CPU: {}  back on scheduler queue.".format(cpu))
                    scheduler.put(['0', cpu, 'N'])

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
                    "Calling function {} with: {}".format(func.__name__, str(args)))

                result = func(*args, **kwargs)

                if scheduler and cpu:
                    logging.debug(
                        "Putting CPU: {}  back on scheduler queue.".format(cpu))

                    scheduler.put((0, cpu, 'Y3'))

            return result

        p = partial(invoke, self.func, *args, **kwargs)

        if hasattr(self.func, '__name__'):
            p.__name__ = self.func.__name__
        else:
            p.__name__ = 'thread'

        p.source = self.source
        return p
