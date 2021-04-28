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

"""

import logging
import six
from functools import partial


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

    def register(self, f):

        def schedule(f, *args):
            logging.debug("DefaultScheduler: args {}".format(str(args)))
            logging.debug("DefaultScheduler: before:")
            result = f(*args)
            logging.debug("DefaultScheduler: after")
            logging.debug("DefaultScheduler: return {}".format(result))
            return result

        return partial(schedule, f)


def scheduler(function=None,
              sclass=DefaultScheduler,
              cpus=12,
              algorithm='first_available',
              max_time=60*60):
    import importlib

    scheduler = import_string(sclass)()

    """

    :param function:
    :param image:
    :param sleep:
    :return:
    """
    def decorator(func):

        def wrapper(f, *args, **kwargs):
            import time
            logging.debug("scheduler: Calling function: {}".format(str(f)))
            logging.debug("Waiting 2 seconds...")
            time.sleep(2)
            return f(*args)

        logging.debug("scheduler: Registering function: {}".format(str(func)))
        sfunc = scheduler.register(func)
        logging.debug("scheduler: Returning function: {}".format(str(sfunc)))
        p = partial(wrapper, sfunc)

        """
        The decorator here delegates to sclass to wrap the function in a scheduler function
        that performs the necessary request, wait handling with the scheduler

        """

        p.__name__ = func.__name__

        return p

    if function is not None:
        return decorator(function)

    return decorator
