from entangle.thread import thread
from entangle.http import request
from entangle.workflow import workflow
from entangle.scheduler import scheduler
import logging

logging.basicConfig(
    format='%(asctime)s : %(levelname)s : %(message)s', level=logging.DEBUG)


scheduler_config = {'cpus': 3,
                    'sclass': 'entangle.scheduler.DefaultScheduler'}


@scheduler(**scheduler_config)
@thread
def two():
    return 2


@scheduler(**scheduler_config)
@thread
def three():
    return 3


@scheduler(**scheduler_config)
@thread
def add(a, b):
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
