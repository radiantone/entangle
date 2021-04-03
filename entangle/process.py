"""
process.py - Module that provides native OS process implementation of function tasks
"""
import asyncio


def process(function=None,
            timeout=None,
            sleep=None):
    """

    :param function:
    :param timeout:
    :param sleep:
    :return:
    """
    def decorator(func):
        def wrapper(f):
            return ProcessFuture(f,
                                 timeout=timeout,
                                 sleep=sleep,
                                 future=True)

        return wrapper(func)

    if function is not None:
        return decorator(function)

    return decorator


class ProcessFuture(object):
    """

    """
    def __init__(self, func, *args, **kwargs):
        """

        :param func:
        :param args:
        :param kwargs:
        """
        self.func = func

    def __call__(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        :return:
        """
        from functools import partial
        from multiprocessing import Queue, Process

        def invoke(func, *args, **kwargs):

            @asyncio.coroutine
            def get_result(q, func):
                import queue

                if hasattr(func, '__name__'):
                    name = func.__name__
                else:
                    name = func
                #print("Waiting on result {}".format(name))

                while True:
                    try:
                        yield #time.sleep(2)
                        _result = q.get_nowait()
                        print("Got result for[{}] ".format(
                            name), _result)
                        return _result
                    except queue.Empty:
                        import time
                        #print("Sleeping...{}".format(name))
                        yield #time.sleep(1)

            if len(args) == 0:
                #print("Fork Process:", self.func)
                pass
            else:
                asyncio.set_event_loop(asyncio.new_event_loop())
                loop = asyncio.get_event_loop()

                tasks = []
                processes = []
                for arg in args:
                    if hasattr(arg, '__name__'):
                        name = arg.__name__
                    else:
                        name = arg
                    # Create an async task that monitors the queue for that arg
                    queue = Queue()

                    if type(arg) == partial:
                        print("Process:", arg.__name__)
                        process = Process(target=arg, kwargs={'queue': queue})
                        processes += [process]
                        process.start()
                    else:
                        print("Value:", name)
                        queue.put(arg)

                    tasks += [get_result(queue, arg)]

                # Wait until all the processes report results
                tasks = asyncio.gather(*tasks)

                # Ensure we have joined all spawned processes
                [process.join() for process in processes]

                args = loop.run_until_complete(tasks)

            if 'queue' in kwargs:
                queue = kwargs['queue']
                del kwargs['queue']
                #print("Calling func with: ", args)
                print("Calling {}".format(func.__name__))
                result = func(*args, **kwargs)
                queue.put(result)
            else:
                #print("Calling func with: ", args)
                result = func(*args, **kwargs)

            return result

        p = partial(invoke, self.func, *args, **kwargs)
        p.__name__ = self.func.__name__
        return p

