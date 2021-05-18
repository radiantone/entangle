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
import json
import traceback
import queue as que
import signal

from typing import Callable
from functools import partial
from multiprocessing import Queue, Process
from multiprocessing.shared_memory import SharedMemory
from multiprocessing.managers import SharedMemoryManager
from concurrent.futures import Future

SMM = SharedMemoryManager()
SMM.start()

graph_queue = Queue()

def handler(signum, frame):
    # Handle any cleanup here
    SMM.shutdown()


signal.signal(signal.SIGINT, handler)
signal.signal(signal.SIGTERM, handler)

# Get shared memory list for adding call graph tuples

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


class ProcessTimeoutException(Exception):
    """
    Description
    """


class ProcessMonitor:
    """
    Primary monitor class for processes. Creates and monitors queues and processes to resolve argument tasks.
    """
    source = None
    graph = {}

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
        self.source = None

    def get_func(self):
        """
        Desc
        """
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
            graphs = []
            json_graph = "{}"
            json_graphs = []

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
                            _response = _queue.get(timeout=timeout)
                            _result = _response['result']
                            logging.debug(
                                "Post get(timeout=%s)", timeout)
                        else:
                            _response = _queue.get()
                            _result = _response['result']

                        logging.debug("Got result for[%s] %s",
                                      name, str(_result))

                        yield

                        # Unwrap graph data list, and result (graph, result)

                        return _response
                    except multiprocessing.TimeoutError as ex:
                        logging.debug("Timeout exception")
                        raise ProcessTimeoutException() from ex
                    except que.Empty as ex:
                        if process and not process.is_alive():
                            raise ProcessTerminatedException() from ex

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
                        aname = arg.__name__
                    else:
                        aname = arg

                    _queue = Queue()

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

                            # Update sharedlist with func to arg names
                            _process = Process(
                                target=assign_cpu, args=(
                                    arg, arg_cpu[1],), kwargs=kargs
                            )
                            _process.cookie = arg_cpu[1]
                        else:
                            logging.debug('NO CPU SET')

                            # Update sharedlist with func to arg names
                            _process = Process(
                                target=arg, kwargs=kargs)

                        if self.shared_memory:
                            _process.shared_memory = True

                        processes += [_process]

                        _process.start()
                    else:
                        logging.info("Value: %s", aname)

                        _queue.put(
                            {'graph': [(func.__name__, aname)], 'result': arg})
                        event.set()

                    now = time.time()

                    # Create an async task that monitors the queue for that arg
                    # It will wait for event set from this child process
                    if hasattr(arg, '__name__'):
                        graphs += [(func.__name__, arg.__name__)]
                    else:
                        graphs += [(func.__name__, arg)]
                    _tasks += [get_result(_queue, arg,
                                          self.sleep, now, _process, event, self.wait, self.timeout)]

                    # Wait until all the processes report results
                    tasks = asyncio.gather(*_tasks)

                # Ensure we have joined all spawned processes

                _args = loop.run_until_complete(tasks)
                try:
                    args = [_arg['result'] for _arg in _args]
                    arg_graph = [_arg['graph'] for _arg in _args]
                    json_graphs = [_arg['json']
                               for _arg in _args if 'json' in _arg]
                except:
                    args = [_arg for _arg in _args]
                    arg_graph = []
                    json_graphs = []

                logging.debug("JSON GRAPHs: %s", json_graphs)
                logging.debug("ARG GRAPH: %s", arg_graph)

                def add_to_graph(gr, argr):
                    for item in argr:
                        if isinstance(item, list):
                            add_to_graph(gr,item)
                        elif isinstance(item, tuple):
                            gr += [item]

                    return gr

                logging.debug("GRAPH: %s",graphs)

                _G = {}
                _G[func.__name__] = {}
                G = _G[func.__name__]
                for node in graphs:
                    if len(node) < 2:
                        continue
                    if node[1] not in G:
                        G[node[1]] = []

                    for graphnode in json_graphs:
                        if node[1] in graphnode:
                            G[node[1]] = graphnode[node[1]]

                json_graph = json.dumps(_G, indent=4)
                logging.debug("JSON: %s", json_graph)
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

                logging.debug("PUT GRAPH [%s]: %s", func.__name__, graphs)
                logging.debug(
                    "PUT GRAPH JSON [%s]: %s", func.__name__, json_graph)
                queue.put(
                    {'graph': graphs, 'json': json.loads(json_graph), 'result': result})

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
                        # TODO: Put (graph,result) tuple here
                        _wq.put({'graph':[(func.__name__,_wf.__name__)], 'result':result})
                        logging.debug("func_wrapper: done putting queue")
                    except Exception:
                        with open('error.out', 'w') as errfile:
                            errfile.write(traceback.format_exc())

                    return None

                pfunc = partial(func, *args, **kwargs)
                pfunc.__name__ = func.__name__

                logging.debug("process: execute: %s", self.execute)

                try:
                    if self.execute:
                        proc = multiprocessing.Process(
                            target=func_wrapper, args=(pfunc, _mq, ))
                        proc.start()

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
                response = _mq.get()


                if len(json_graphs) > 0:
                    callgraph = {func.__name__: json_graphs}
                    graph_queue.put(callgraph)
                    self.graph = json.dumps(callgraph)

                result = response['result']
                logging.debug("process: got result from queue")

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
        
        def get_graph(wait=True):
            if wait:
                return graph_queue.get()
            else:
                @asyncio.coroutine
                def wait_for_graph():

                    logging.debug("wait_for_graph: looping")
                    while True:
                        try:
                            logging.debug("wait_for_graph: checking queue")
                            graph = graph_queue.get_nowait()
                            logging.debug("wait_for_graph: got result")
                            return graph
                        except:
                            logging.debug("wait_for_graph: yielding")
                            yield

                loop = asyncio.get_event_loop()
                task = loop.create_task(wait_for_graph())
                return task

        pfunc.graph = get_graph

        return pfunc
