from entangle.logging.file import logging
from entangle.process import process
from entangle.http import request
from entangle.workflow import workflow
from entangle.scheduler import scheduler

scheduler_config = {'cpus': 2,
                    'impl': 'entangle.scheduler.DefaultScheduler'}


@scheduler(**scheduler_config)
@process
def two():
    return 2


@scheduler(**scheduler_config)
@process
def three():
    return 3


@scheduler(**scheduler_config)
@process
def add(a, b):
    print("add: {} {}".format(a,b))
    v = int(a) + int(b)
    print("ADD: *"+str(v)+"*")
    return v


@scheduler(**scheduler_config)
@workflow
def workflow2():
    return add(
        three(),
        two()
    )


result = workflow2()

print(result())
