# pylint: disable=locally-disabled, not-callable, line-too-long, unused-argument, too-few-public-methods, no-self-use

"""
scheduler.py - A shared memory scheduler that runs in a process within a workflow. nodes send requests to the scheduler queue
and then wait for a reply. the reply gives the node parameters to run its process such as what cpu to run it on. When a process is finished,
the node sends message to scheduler that its processed finished and the scheduler can then task another node.

"""

from importlib import import_module
from multiprocessing import Queue
from functools import partial
import logging
import threading
import inspect
import os
import types
from typing import Callable
from entangle.process import ProcessMonitor
from entangle.thread import ThreadMonitor


CPUS = []

queue = Queue()

CMD = "/usr/bin/lscpu -p=socket,cpu,online"
stream = os.popen(CMD)
output = stream.readlines()
for line in output:
    if line[0] == '#':
        continue
    _cpu = line.strip().split(',')
    if _cpu[2] == 'Y':
        CPUS += [_cpu]
        # Put CPU cookie on queue
        queue.put(_cpu)

logging.debug('CPUS: %s',CPUS)


def import_string(dotted_path):
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed.
    """

    module_path, class_name = dotted_path.rsplit('.', 1)

    module = import_module(module_path)

    return getattr(module, class_name)


class FileLockScheduler:
    """
    Will implement de-centralized CPU binding using shared memory and lock files
    see: entangle/scratch/sheduler.py
    """
    def register(self, f_func, cpus=12):
        """
        Desc
        """
        pass

"""
import multiprocessing
import threading
import atexit
import time
from multiprocessing import shared_memory
from filelock import Timeout, FileLock

CPUS = multiprocessing.cpu_count()

global cpu_list

'''
The CPU bits (0 for unused, 1 for occupied) in the shared list are designed
to pre-empt load off the lockfiles and filesystem.
'''
try:
    cpu_list = shared_memory.ShareableList([0] * 4, name="cpus")
except:
    cpu_list = shared_memory.ShareableList(name="cpus")


def exit_handler():
    global cpu_list
    print("Closing sharedmemory")
    cpu_list.shm.close()
    cpu_list.shm.unlink()
    del cpu_list

atexit.register(exit_handler)

def grab_cpu():
    while True:
        cpus = shared_memory.ShareableList(name="cpus")
        for i in range(0, len(cpus)):
            cpu = cpus[i]
            print("Checking CPU{}:  {}".format(i, cpu))
            print(cpus)
            time.sleep(4)
            if cpu == 0:
                try:
                    lock = FileLock("/tmp/cpu{}.lock".format(i))
                    with lock.acquire(timeout=1):
                        print('===Occupy CPU{}: {}'.format(
                            i, threading.current_thread().name))

                        # Set the CPU BIT
                        cpus[i] = 1
                        print(cpus)

                        # DO SOME WORK HERE
                        time.sleep(13)

                        # Clear the CPU bit
                        cpus[i] = 0
                        print('===Release CPU{}: {}'.format(
                            i, threading.current_thread().name))
                except Timeout:
                    print("Thread {}: CPU {} Lock was held already, looking for another CPU.".format(
                        threading.current_thread().name, i))
                finally:
                    lock.release()
                    time.sleep(4)
            else:
                print("Taking a break")
                time.sleep(4)

def grab_cpus():
    x = threading.Thread(target=grab_cpu)
    x.start()


if __name__ == '__main__':
    print("Starting thread...")
    grab_cpus()
    grab_cpus()

"""


class DefaultScheduler:
    """
    Desc
    """
    def register(self, f_func, cpus=12):
        """
        Desc
        :param f:
        :param cpus:
        :return:
        """
        def schedule(_func, *args, **kwargs):
            """
            Desc
            :param f:
            :param args:
            :param kwargs:
            :return:
            """
            logging.debug("DefaultScheduler: args %s",str(args))
            logging.debug("DefaultScheduler: before:")

            logging.debug("DefaultScheduler: thread %s",
                threading.current_thread().name)

            logging.debug("Waiting on CPU")
            cpu_pending = True

            while cpu_pending:
                cpu = queue.get()
                if int(cpu[1]) >= int(cpus):
                    logging.debug(
                        "     CPU not within allocation: %s %s",cpu, cpus)
                    queue.put(cpu)
                else:
                    logging.debug("GRABBED CPU: %s %s",cpu, cpus)
                    break

            logging.debug("GOT CPU: %s",cpu)
            logging.debug(_func)

            if not isinstance(_func, types.FunctionType):
                kwargs['cpu'] = cpu[1]
                kwargs['scheduler'] = queue

            if cpu:
                pid = os.getpid()
                cpu_mask = [int(cpu[1])]
                logging.debug("Setting cpu_mask %s",cpu_mask)
                os.sched_setaffinity(pid, cpu_mask)

            result = _func(*args, **kwargs)
            logging.debug("Putting cpu %s back on scheduler queue",cpu)

            queue.put(cpu)
            logging.debug("DefaultScheduler: after")
            logging.debug("DefaultScheduler: return %s",result)
            return result

        return partial(schedule, f_func)


def scheduler(function=None,
              impl='entangle.scheduler.DefaultScheduler',
              cpus=12,
              algorithm='first_available',
              max_time=60*60) -> Callable:
    """
    Desc
    :param function:
    :param impl:
    :param cpus:
    :param algorithm:
    :param max_time:
    :return:
    """

    _scheduler = import_string(impl)()

    logging.debug("scheduler: Requesting %s cpus",cpus)

    def decorator(func, cpus=12) -> Callable:
        """
        Desc
        :param func:
        :param cpus:
        :return:
        """

        _func = func

        if isinstance(func, (ProcessMonitor, ThreadMonitor)):
            _func = func.func

        if isinstance(_func,partial):

            def find_func(pfunc):
                if isinstance(pfunc, partial):
                    return find_func(pfunc.func)
                return pfunc

            _func = find_func(_func)

        source = inspect.getsource(_func)
        logging.debug("scheduler: source: %s",source)

        def wrapper(_wfunc, *args, **kwargs) -> Callable:
            logging.debug("scheduler: Calling function: %s", str(_wfunc))
            logging.debug("Waiting 2 seconds...")
            # time.sleep(2)
            return _wfunc(*args, **kwargs)

        logging.debug("scheduler: decorator %s cpus",cpus)
        logging.debug("scheduler: Registering function: %s",str(func))
        sfunc = _scheduler.register(func, cpus=cpus)
        logging.debug("scheduler: Returning function: %s",str(sfunc))
        _pfunc = partial(wrapper, sfunc)
        _pfunc.source = source

        if isinstance(func, (ProcessMonitor, ThreadMonitor)):
            _pfunc.__name__ = func.func.__name__
        else:
            _pfunc.__name__ = func.__name__

        return _pfunc


    if function is not None:
        _decorator = decorator(function, cpus=cpus)
        return _decorator

    pfunc = partial(decorator, **{'cpus': cpus})
    logging.debug("scheduler: no source: ")

    return pfunc
