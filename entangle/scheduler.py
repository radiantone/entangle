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

from functools import partial


class DefaultScheduler(object):

    def register(self, f):

        def schedule(f, *args):
            print("DefaultScheduler: before: ",*args)
            result = f(*args)
            print("DefaultScheduler: after")
            print("DefaultScheduler: return {}".format(result))
            return result

        return partial(schedule, f)


def scheduler(function=None,
              sclass=DefaultScheduler,
              cpus=12,
              algorithm='first_available',
              max_time=60*60):

    scheduler = sclass()
    """

    :param function:
    :param image:
    :param sleep:
    :return:
    """
    def decorator(func):

        def wrapper(f, *args, **kwargs):

            print("scheduler: Calling function:", f)
            return f(*args)

        print("scheduler: Registering function:",func)
        sfunc = scheduler.register(func)
        print("scheduler: Returning function:", sfunc)
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
