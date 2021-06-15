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
import builtins
from typing import Callable
from functools import partial
from multiprocessing import Queue, Process
from multiprocessing.shared_memory import SharedMemory
from multiprocessing.managers import SharedMemoryManager

SMM = SharedMemoryManager()
SMM.start()

graph_queue = Queue()


def handler():
    """
    Handle any cleanup here
    """
    SMM.shutdown()


signal.signal(signal.SIGINT, handler)
signal.signal(signal.SIGTERM, handler)


def process(function=None,
            timeout=None,
            wait=None,
            cache=False,
            retry=0,
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
                                  retry=retry,
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


class ProcessRetryException(Exception):
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
        self.result_queue = Queue()
        self.retry = kwargs['retry'] if 'retry' in kwargs else None
        self.__name__ = func.__name__

    def get_func(self):
        """
        Desc
        """
        return self.func

    def future(self, callback=None):
        """
        Desc
        """
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()

        @asyncio.coroutine
        def wait_for_done(future_queue):
            import time
            logging.debug(
                "wait_for_done: looping: result queue: %s", future_queue)
            while True:
                try:
                    logging.debug("wait_for_done: checking queue")
                    result = future_queue.get_nowait()
                    logging.debug("wait_for_done: got result")
                    return result
                except:
                    logging.debug("Waiting...")
                    time.sleep(2)
                    logging.debug("Yielding...")
                    yield

        _future = loop.create_task(wait_for_done(self.result_queue))

        def entangle():
            loop.run_until_complete(_future)

        _future.loop = loop
        _future.entangle = entangle

        if callback:
            _future.add_done_callback(callback)

        return _future

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
                if hasattr(pfunc, 'userfunc') and pfunc.userfunc:
                    return pfunc.userfunc
                elif isinstance(pfunc, partial):
                    return find_func(pfunc.func)
                #raise Exception()
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
            import time
            import datetime
            pid = os.getpid()
            cpu_mask = [int(cpu)]
            logging.debug("assign_cpu: setting affinity to %s", cpu_mask)
            os.sched_setaffinity(pid, cpu_mask)

            # TODO: Retry logic here
            try:
                start = time.time()
                if '_cpu' in kwargs:
                    _cpu = kwargs['_cpu']
                    del kwargs['_cpu']
                event = kwargs['event']
                del kwargs['event']
                func(**kwargs)
                end = time.time()
                duration = str(
                    datetime.timedelta(seconds=end-start))
                logging.debug(
                    "assign_cpu: DURATION: %s", duration)
                
                if 'scheduler' in kwargs:
                    logging.debug(
                        "assign_cpu: Putting CPU %s on queue", cpu_mask)
                    kwargs['scheduler'].put((0, int(cpu), 1))
                event.set()
            except Exception:
                with open('error3.out', 'a') as errfile:
                    errfile.write(traceback.format_exc())

        def invoke(func, retry, *args, **kwargs):
            """

            :param func:
            :param args:
            :param kwargs:
            :return:
            """
            graphs = []
            json_graph = "{}"
            json_graphs = []

            error_messages = []
            future_queue = kwargs['future_queue']

            del kwargs['future_queue']

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
                            try:
                                event.wait()
                            except:
                                logging.debug("process: event.wait() excepted")

                        logging.debug("Got event for %s", name)

                        logging.debug("Timeout is %s", timeout)
                        if timeout:
                            logging.debug(
                                "Pre get(timeout=%s)", timeout)
                            _response = _queue.get(timeout=timeout)

                            if not _response['result']:
                                raise Exception(_response['error'])

                            _result = _response['result']
                            logging.debug(
                                "Post get(timeout=%s)", timeout)
                        else:
                            _response = _queue.get()

                            if not _response['result']:
                                logging.error(_response['error'])
                                event.set()
                                print(_response['error'])
                                raise Exception(_response['error'])

                            else:
                                _result = _response['result']

                        logging.debug("Got result for[%s] %s",
                                      name, str(_result))

                        yield
                        event.set()
                        return _response
                    except multiprocessing.TimeoutError as ex:
                        logging.debug("ProcessTimeoutException exception")
                        raise ProcessTimeoutException() from ex
                    except que.Empty as ex:
                        if process and not process.is_alive():
                            logging.debug(
                                "ProcessTerminatedException exception")
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
                error = False

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
                                'ARG CPU SET TO: %s', arg_cpu)
                            kargs['event'] = event
                            kargs['scheduler'] = scheduler
                            # Update sharedlist with func to arg names
                            _process = Process(
                                target=assign_cpu, args=(
                                    arg, arg_cpu[1],), kwargs=kargs
                            )
                            _process.cookie = arg_cpu[1]
                        else:
                            logging.debug('NO CPU SET')

                            # Update sharedlist with func to arg names
                            # TODO: Wrap arg in retry function

                            def error_wrapper(arg, **kwargs):
                                try:
                                    arg(**kwargs)
                                except Exception as ex:
                                    with open('error2.out', 'a') as errfile:
                                        errfile.write(traceback.format_exc())
                                        errfile.write(str(arg))

                            _process = Process(
                                target=error_wrapper, args=(arg,), kwargs=kargs)

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
                        graphs += [(func.__name__, str(arg))]

                    try:
                        _tasks += [get_result(_queue, arg,
                                              self.sleep, now, _process, event, self.wait, self.timeout)]

                        # Wait until all the processes report results
                        tasks = asyncio.gather(*_tasks, return_exceptions=True)
                    except Exception as ex:
                        logging.error("Got exception during get_result gather")
                        error = True
                        break

                # Ensure we have joined all spawned processes
                if error:
                    raise Exception("Got exception during get_result gather")

                try:
                    logging.debug("Running loop.run_until_complete(tasks)")
                    _args = loop.run_until_complete(tasks)
                    logging.debug("loop.run_until_complete(tasks) Done")
                except Exception as ex:
                    logging.debug("Got an error")
                    logging.error(ex)
                    return

                try:
                    exceptions = [_arg['result'] for _arg in _args if not isinstance(_arg,Exception)]
                    args = [_arg['result'] for _arg in _args if _arg]
                    arg_graph = [_arg['graph'] for _arg in _args if _arg]
                    json_graphs = [_arg['json']
                                   for _arg in _args if _arg and 'json' in _arg]
                except:
                    import traceback
                    logging.debug("_ARGS: %s", _args)
                    logging.debug(
                        "ERROR: Exception building args: %s", traceback.format_exc())
                    for _arg in _args:
                        if isinstance(_arg, Exception):
                            raise _arg
                    args = [_arg for _arg in _args]
                    arg_graph = []
                    json_graphs = []

                logging.debug("JSON GRAPHs: %s", json_graphs)
                logging.debug("ARG GRAPH: %s", arg_graph)

                def add_to_graph(gr, argr):
                    for item in argr:
                        if isinstance(item, list):
                            add_to_graph(gr, item)
                        elif isinstance(item, tuple):
                            gr += [item]

                    return gr

                logging.debug("GRAPH: %s", graphs)

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

                logging.debug("Dumping graph json")
                try:
                    json_graph = json.dumps(_G, indent=4)
                except:
                    logging.debug("Error occurred")
                logging.debug("JSON: %s", json_graph)
                _ = [process.join() for process in processes]

                # This no longer needed because processes put their own cpu's back on the queue
                # when they have complete, individually
                
                if scheduler:
                    for _process in processes:
                        logging.debug(
                            "Putting CPU1: %s  back on scheduler queue.", _process.cookie)
                        scheduler.put(('0', _process.cookie, 'Y'))
                
            if cpu:
                pid = os.getpid()
                cpu_mask = [int(cpu)]
                os.sched_setaffinity(pid, cpu_mask)

            is_proc = False
            if 'proc' in kwargs and kwargs['proc'] is True:
                del kwargs['proc']
                is_proc = True

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

                result = None

                try:
                    if self.execute:
                        logging.debug("process: execute: %s", self.execute)

                        if is_proc:

                            logging.debug(
                                "self.execute: proc: creating process")
                            _mq = Queue()

                            def func_wrapper(_wf, _wq):
                                import time
                                import datetime

                                logging.debug("func_wrapper: %s", _wf)
                                start = time.time()
                                result = _wf()
                                end = time.time()
                                duration = str(
                                    datetime.timedelta(seconds=end-start))
                                logging.debug(
                                    "func_wrapper: DURATION: %s", duration)
                                logging.debug(
                                    "func_wrapper: result: %s", result)

                                # Unwrap any partials built up by stacked decorators

                                try:
                                    if callable(result):
                                        # TODO: Retry logic here
                                        return func_wrapper(result, _wq)
                                    logging.debug(
                                        "func_wrapper: putting result on queue")
                                    # TODO: Put (graph,result) tuple here
                                    _wq.put(
                                        {'graph': [(func.__name__, _wf.__name__)], 'result': result})
                                    logging.debug(
                                        "func_wrapper: done putting queue")
                                except Exception:
                                    with open('error4.out', 'a') as errfile:
                                        errfile.write(traceback.format_exc())

                                return None

                            _pfunc = partial(func, *args, **kwargs)
                            proc = multiprocessing.Process(
                                target=func_wrapper, args=(_pfunc, _mq, ))
                            proc.start()
                        else:
                            ex_msg = None
                            if retry and retry > 0:
                                for i in range(retry):
                                    logging.debug("RETRY: {}".format(i))
                                    try:
                                        result = func(*args, **kwargs)
                                        logging.debug("RESULT IS: %s", result)
                                        break
                                    except Exception as ex:
                                        import traceback
                                        ex_msg = str(ex)
                                        error_messages = [
                                            traceback.format_exc()]
                                        continue

                                if i == retry-1:
                                    event.set()
                                    error_messages += [
                                        "maximum retries reached {}".format(retry)]
                            else:
                                try:
                                    import datetime

                                    start = time.time()
                                    result = func(*args, **kwargs)
                                    end = time.time()
                                    duration = str(
                                        datetime.timedelta(seconds=end-start))
                                    logging.debug(
                                        "func: DURATION: %s", duration)
                                except Exception as ex:
                                    import traceback
                                    logging.debug(
                                        "GOT EXCEPTION: %s", traceback.format_exc())
                                    for msg in error_messages:
                                        logging.error(msg)
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
                            "Putting CPU2: %s back on scheduler queue.", cpu)

                        scheduler.put(['0', cpu, 'N'])

                    if len(error_messages) > 0:
                        logging.debug("GOT ERROR MESSAGES")
                        for msg in error_messages:
                            logging.error(msg)
                        result = None

                if self.cache:
                    pass

                logging.debug("PUT GRAPH [%s]: %s", func.__name__, graphs)
                logging.debug(
                    "PUT GRAPH JSON [%s]: %s", func.__name__, json_graph)

                if result is not None:
                    queue.put(
                        {'graph': graphs, 'json': json.loads(json_graph), 'result': result})
                else:
                    queue.put(
                        {'graph': graphs, 'json': json.loads(json_graph), 'result': None, 'error': ' '.join(error_messages)})

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
                    import time
                    import datetime
                    start = time.time()
                    logging.debug("func_wrapper: %s", _wf)
                    result = _wf()
                    logging.debug("func_wrapper: result: %s", result)
                    end = time.time()
                    duration = str(datetime.timedelta(seconds=end-start))
                    logging.debug(
                        "func_wrapper: DURATION: %s", duration)

                    # Unwrap any partials built up by stacked decorators
                    try:
                        if callable(result):
                            logging.debug(
                                "func_wrapper: return result of %s", result)
                            return func_wrapper(result, _wq)

                        logging.debug("func_wrapper: putting result on queue")

                        _wq.put(
                            {'graph': [(func.__name__, _wf.__name__)], 'result': result})

                        if is_proc:
                            future_queue.put(result)
                        logging.debug("func_wrapper: done putting queue")
                    except Exception:
                        import traceback
                        with open('error2.out', 'a') as errfile:
                            errfile.write(traceback.format_exc())

                    return None

                pfunc = partial(func, *args, **kwargs)
                pfunc.__name__ = func.__name__

                try:
                    import datetime

                    if self.execute:
                        logging.debug("process: execute2: %s", self.execute)
                        start = time.time()
                        proc = multiprocessing.Process(
                            target=func_wrapper, args=(pfunc, _mq,))
                        proc.start()

                        logging.debug(
                            "Executing function %s with timeout %s", func, self.timeout)
                        if not is_proc:
                            proc.join(self.timeout)
                            end = time.time()
                            duration = str(
                                datetime.timedelta(seconds=end-start))
                            logging.debug(
                                "proc: DURATION: %s", duration)
                    else:
                        if event:
                            logging.debug(
                                "Setting event for %s", func.__name__)
                            event.set()
                        return (args, kwargs)
                finally:
                    if scheduler and cpu:
                        logging.debug(
                            "Putting CPU3: %s back on scheduler queue.", cpu)

                        scheduler.put(('0', cpu, 'Y'))

                logging.debug("process: waiting for result on queue")

                sys.path.append(os.getcwd())

                if not is_proc:
                    logging.debug("process: not is_proc, getting response")
                    response = _mq.get()
                    logging.debug(
                        "process: not is_proc, got response %s", response)

                    if 'error' in response and not response['result']:
                        logging.debug("ERROR OCCURRED %s", response['error'])
                        raise Exception(response['error'])

                    logging.debug("process: result = response['result']")
                    result = response['result']

                if len(json_graphs) > 0:
                    callgraph = {func.__name__: json_graphs}
                    logging.debug("process: putting callgraph on graph_queue")
                    graph_queue.put(callgraph)
                    logging.debug(
                        "process: putting callgraph on graph_queue: done")
                    self.graph = json.dumps(callgraph)
                    logging.debug(
                        "process: putting dumping callgraph")

                logging.debug("process: got result from queue")

                if not is_proc and proc.is_alive():
                    logging.debug("process: Terminating process")
                    proc.terminate()
                    proc.join()
                    raise ProcessTimeoutException()

            logging.debug("process: is_proc %s", is_proc)
            if is_proc:
                # return future
                return True

            logging.debug(
                "process: putting result on future_queue: %s", result)
            future_queue.put(result)
            logging.debug("process: return result")
            return result

        # Need to pass in a queue here that the future coroutine can listen on
        kwargs['future_queue'] = self.result_queue
        pfunc = partial(invoke, self.func, self.retry, *args, **kwargs)

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
                            yield

                loop = asyncio.get_event_loop()
                task = loop.create_task(wait_for_graph())

                def entangle():
                    logging.debug("entangle: run_until_complete")
                    loop.run_until_complete(task)
                    logging.debug("entangle: run_until_complete done")

                task.entangle = entangle

                return task

        pfunc.graph = get_graph
        pfunc.future = self.future

        return pfunc  # InvokeProxy(pfunc)
