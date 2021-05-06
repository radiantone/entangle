"""
scheduler.py - A shared memory scheduler that runs in a process within a workflow. nodes send requests to the scheduler queue
and then wait for a reply. the reply gives the node parameters to run its process such as what cpu to run it on. When a process is finished,
the node sends message to scheduler that its processed finished and the scheduler can then task another node.

The scheduler decorator is assigned to a @workflow node:

@workflow
@scheduler(
    cpus=12,
    max_time=60*60
    log='logs/log',
    class='my.Schedular',
    algorithm='first_available'
)
def myworkflow():
    return ()

workflow = myworkflow(
    funca(
        funcb()
    )
)


myworkflow will create a scheduler and pass its queue along to execution nodes in the workflow
The nodes will detect the scheduler queue and adjust their behavior accordingly.

All the schedulers are associated with each function. There is no single, central scheduler, rather
the schedulers coordinate their state using shared memory. This way, they act like one scheduler.

The first scheduler to run can put its CPU allocation in shared memory and assign one to itself. As it runs its process
and completes, it can free up its CPU allocation and then try to run another job by pulling a job off its queue.

Other schedulers will run and try to reserve a CPU from shared memory CPU map. If they are all taken, the scheduler will
use asyncio coroutine to monitor shared memory for available resource. if it finds a free CPU, then it occupies that CPU and
lets its process run using cpu affinity for it. then frees the CPU block in shared memory. The process runs until all the processes
needing CPUs have completed.
-----

Using shared memory, the first defaultscheduler to run will set up a shared memory list with all the CPU metadata in it.
And a queue.


"""

import logging
import threading
import six
import os
from functools import partial
from entangle.process import ProcessMonitor
from entangle.thread import ThreadMonitor

from multiprocessing import Queue
from multiprocessing import Condition

CPUS = []

queue = Queue()

cmd = "/usr/bin/lscpu -p=socket,cpu,online"
stream = os.popen(cmd)
output = stream.readlines()
for line in output:
    if(line[0] == '#'):
        continue
    cpu = line.strip().split(',')
    if cpu[2] == 'Y':
        CPUS += [cpu]
        # Put CPU cookie on queue
        queue.put(cpu)

logging.debug('CPUS: {}'.format(CPUS))


def import_string(dotted_path):
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed.
    """
    from importlib import import_module

    try:
        module_path, class_name = dotted_path.rsplit('.', 1)
    except ValueError:
        msg = "%s doesn't look like a module path" % dotted_path
        six.reraise(ImportError, ImportError(msg), sys.exc_info()[2])

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError:
        msg = 'Module "%s" does not define a "%s" attribute/class' % (
            module_path, class_name)
        six.reraise(ImportError, ImportError(msg), sys.exc_info()[2])


class DefaultScheduler(object):

    def register(self, f, cpus=12):

        def schedule(f, *args, **kwargs):
            import types

            logging.debug("DefaultScheduler: args {}".format(str(args)))
            logging.debug("DefaultScheduler: before:")

            logging.debug("DefaultScheduler: thread {}".format(
                threading.current_thread().name))

            logging.debug("Waiting on CPU")
            cpu_pending = True

            while cpu_pending:
                cpu = queue.get()
                if int(cpu[1]) >= int(cpus):
                    logging.debug(
                        "     CPU not within allocation: {} {}".format(cpu, cpus))
                    queue.put(cpu)
                else:
                    logging.debug("GRABBED CPU: {} {}".format(cpu, cpus))
                    break

            logging.debug("GOT CPU: {}".format(cpu))
            logging.debug(f)

            if type(f) is not types.FunctionType:
                kwargs['cpu'] = cpu[1]
                kwargs['scheduler'] = queue

            if cpu:
                pid = os.getpid()
                cpu_mask = [int(cpu[1])]
                logging.debug("Setting cpu_mask {}".format(cpu_mask))
                os.sched_setaffinity(pid, cpu_mask)

            result = f(*args, **kwargs)
            logging.debug("Putting cpu {} back on scheduler queue".format(cpu))

            queue.put(cpu)
            logging.debug("DefaultScheduler: after")
            logging.debug("DefaultScheduler: return {}".format(result))
            return result

        return partial(schedule, f)


def scheduler(function=None,
              impl=DefaultScheduler,
              cpus=12,
              algorithm='first_available',
              max_time=60*60):
    import importlib
    from functools import partial

    scheduler = import_string(impl)()

    logging.debug("scheduler: Requesting {} cpus".format(cpus))

    """

    :param function:
    :param image:
    :param sleep:
    :return:
    """
    def decorator(func, cpus=12):
        import inspect

        _func = func

        if type(func) is ProcessMonitor or type(func) is ThreadMonitor:
            _func = func.func

        if type(_func) is partial:

            def find_func(p):
                if type(p) is partial:
                    return find_func(p.func)
                return p

            _func = find_func(_func)

        source = inspect.getsource(_func)
        logging.debug("scheduler: source: {}".format(source))

        def wrapper(f, *args, **kwargs):
            import time
            logging.debug("scheduler: Calling function: {}".format(str(f)))
            logging.debug("Waiting 2 seconds...")
            # time.sleep(2)
            return f(*args, **kwargs)

        logging.debug("scheduler: decorator {} cpus".format(cpus))
        logging.debug("scheduler: Registering function: {}".format(str(func)))
        sfunc = scheduler.register(func, cpus=cpus)
        logging.debug("scheduler: Returning function: {}".format(str(sfunc)))
        p = partial(wrapper, sfunc)
        p.source = source
        """
        The decorator here delegates to impl to wrap the function in a scheduler function
        that performs the necessary request, wait handling with the scheduler

        """

        if type(func) is ProcessMonitor or type(func) is ThreadMonitor:
            p.__name__ = func.func.__name__
        else:
            p.__name__ = func.__name__

        return p

    import inspect

    if function is not None:
        d = decorator(function, cpus=cpus)
        return d

    p = partial(decorator, **{'cpus': cpus})
    logging.debug("scheduler: no source: ")

    return p
