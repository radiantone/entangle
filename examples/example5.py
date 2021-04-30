import logging

logging.basicConfig(
    format='%(asctime)s : %(levelname)s : %(message)s', level=logging.DEBUG)

from entangle.thread import thread
from entangle.http import request
from entangle.workflow import workflow
from entangle.scheduler import scheduler

scheduler_config = {'cpus': 3,
                    'impl': 'entangle.scheduler.DefaultScheduler'}


@scheduler(**scheduler_config)
@thread
@request(url='https://datausa.io/api/data', method='GET')
def mydata(data):
    import json
    data = json.loads(data)
    print('My function got the data! ', data)
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
