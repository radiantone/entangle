"""
process.py - Module that provides native OS process implementation of function tasks with support for shared memory
"""
import asyncio
import logging
import sys
import os
import multiprocessing
from multiprocessing.shared_memory import SharedMemory
from multiprocessing.managers import SharedMemoryManager

global smm
smm = SharedMemoryManager()
smm.start()


def process(function=None,
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
                "ProcessMonitor: {} with wait {}".format(f, wait))
            return ProcessMonitor(f,
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
    A process pool that executes the workflow callgraph inside out so it
    can pool only the graph leaf nodes in a process pool executor.

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
            # results get gather before a new process function is given to the pool

            return pm

        return wrapper(func)

    if function is not None:
        return decorator(function)

    return decorator


class ProcessTerminatedException(Exception):
    """

    """
    pass


class ProcessTimeoutException(Exception):
    """

    """
    pass


class PoolMonitor(object):
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
        self.wait = kwargs['wait']
        self.execute = kwargs['execute'] if 'execute' in kwargs else True

    def __call__(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        :return:
        """
        from functools import partial
        from multiprocessing import Queue, Process
        import inspect

        logging.info("Process:invoke: {}".format(self.func.__name__))
        _func = self.func
        if type(self.func) is partial:

            def find_func(p):
                if type(p) is partial:
                    return find_func(p.func)
                return p

            _func = find_func(self.func)

        self.source = inspect.getsource(_func)

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

            global smm

            @asyncio.coroutine
            def get_result(q, func, sleep, now, process, event, wait, timeout):
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
                from multiprocessing import TimeoutError

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
                                raise ProcessTimeoutException()
                        else:
                            logging.debug("Waiting until complete.")
                            event.wait()

                        logging.debug("Got event for {}".format(name))

                        logging.debug("Timeout is {}".format(timeout))
                        if timeout:
                            logging.debug(
                                "Pre get(timeout={})".format(timeout))
                            _result = q.get(timeout=timeout)
                            logging.debug(
                                "Post get(timeout={})".format(timeout))
                        else:
                            _result = q.get()

                        logging.debug("Got result for[{}] {}".format(
                            name, str(_result)))

                        yield

                        return _result
                    except TimeoutError:
                        logging.debug("Timeout exception")
                        raise ProcessTimeoutException()
                    except queue.Empty:
                        import time

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

            # with smm:
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

                    # Need to pull a cpu off scheduler queue here

                    _process = None

                    if type(arg) == partial:
                        logging.info("Process: {}".format(arg.__name__))

                        kargs = {'queue': queue, 'event': e}
                        # If not shared memory

                        # if shared memory, set the handles
                        if self.shared_memory:
                            kargs['smm'] = smm
                            kargs['sm'] = SharedMemory

                        if cpu:
                            arg_cpu = scheduler.get()

                            # TODO: Fix. This bypasses the scheduler logic of capping the CPU #'s.
                            logging.debug(
                                'ARG CPU SET TO: {}'.format(arg_cpu[1]))
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
                        logging.info("Value:".format(name))
                        queue.put(arg)
                        e.set()

                    now = time.time()

                    # Create an async task that monitors the queue for that arg
                    # It will wait for event set from this child process
                    _tasks += [get_result(queue, arg,
                                          self.sleep, now, _process, e, self.wait, self.timeout)]

                    # Wait until all the processes report results
                    tasks = asyncio.gather(*_tasks)

                # Ensure we have joined all spawned processes

                args = loop.run_until_complete(tasks)

                [process.join() for process in processes]

                # Put CPU cookie back on scheduler queue
                if scheduler:
                    for process in processes:
                        logging.debug(
                            "Putting CPU: {}  back on scheduler queue.".format(process.cookie))
                        scheduler.put(('0', process.cookie, 'Y'))

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

                try:
                    logging.debug("process: execute: {}".format(self.execute))
                    if self.execute:
                        result = func(*args, **kwargs)
                    else:
                        if event:
                            logging.debug(
                                "Setting event for {}".format(func.__name__))
                            event.set()
                        return (args, kwargs)
                finally:
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

                # Wrap with Process and queue with timeout
                #logging.debug("Executing function {} in MainThread".format(func))
                #result = func(*args, **kwargs)
                mq = Queue()

                def func_wrapper(f, q):
                    logging.debug("func_wrapper: {}".format(f))
                    result = f()
                    logging.debug("func_wrapper: result: {}".format(result))

                    # Unwrap any partials built up by stacked decorators
                    if callable(result):
                        return func_wrapper(result, q)
                    try:
                        logging.debug("func_wrapper: putting result on queue")
                        q.put(result)
                        logging.debug("func_wrapper: done putting queue")
                    except:
                        import traceback
                        with open('error.out', 'w') as errfile:
                            errfile.write(traceback.format_exc())

                p = partial(func, *args, **kwargs)

                logging.debug("process: execute: {}".format(self.execute))

                try:
                    if self.execute:
                        p = multiprocessing.Process(
                            target=func_wrapper, args=(p, mq, ))
                        p.start()

                        # Wait for 10 seconds or until process finishes
                        logging.debug(
                            "Executing function {} with timeout {}".format(func, self.timeout))
                        p.join(self.timeout)
                    else:
                        if event:
                            logging.debug(
                                "Setting event for {}".format(func.__name__))
                            event.set()
                        return (args, kwargs)
                finally:
                    if scheduler and cpu:
                        logging.debug(
                            "Putting CPU: {}  back on scheduler queue.".format(cpu))

                        scheduler.put(('0', cpu, 'Y'))

                logging.debug("process: waiting for result on queue")

                sys.path.append(os.getcwd())
                result = mq.get()
                logging.debug("process: got result from queue")

                # If thread is still active
                if p.is_alive():
                    p.terminate()
                    p.join()
                    raise ProcessTimeoutException()

            return result

        p = partial(invoke, self.func, *args, **kwargs)

        if hasattr(self.func, '__name__'):
            p.__name__ = self.func.__name__
        else:
            p.__name__ = 'process'

        return p
