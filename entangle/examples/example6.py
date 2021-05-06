from entangle.logging.debug import logging
from entangle.scheduler import scheduler
from entangle.workflow import workflow
from entangle.http import request
from entangle.thread import thread

scheduler_config = {'cpus': 10, 'impl': 'entangle.scheduler.DefaultScheduler'}


@scheduler(**scheduler_config)
@thread
@request(url='https://datausa.io/api/data', method='GET')
def mydata(data, **kwargs):
    import json
    data = json.loads(data)
    print('*********************My function got the data! ', data)
    return int(data['data'][0]['Year'])


@scheduler(**scheduler_config)
@thread
def two():
    return 2


@scheduler(**scheduler_config)
@thread
def add(a, b):
    v = int(a) + int(b)
    print("ADD: *"+str(v)+"*")
    return v


@scheduler(**scheduler_config)
@workflow
def workflow1():
    return add(
        mydata(drilldowns='Nation', measures='Population'),
        two()
    )


@scheduler(**scheduler_config)
@workflow
def workflow2(value):
    return add(
        value(),
        two()
    )


result = workflow2(workflow1)

print(result())

