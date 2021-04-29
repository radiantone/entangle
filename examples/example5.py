from entangle.thread import thread
from entangle.http import request
from entangle.workflow import workflow
from entangle.scheduler import scheduler

import logging
logging.basicConfig(
    format='%(asctime)s : %(levelname)s : %(message)s', level=logging.DEBUG)


@thread
@request(url='https://datausa.io/api/data', method='GET')
@scheduler(cpus=10, sclass='entangle.scheduler.DefaultScheduler')
def mydata(data, **kwargs):
    import json
    data = json.loads(data)
    print('My function got the data! ', data)
    return int(data['data'][0]['Year'])


@thread
@scheduler(cpus=10, sclass='entangle.scheduler.DefaultScheduler')
def two(**kwargs):
    return 2


@thread
@scheduler(cpus=10, sclass='entangle.scheduler.DefaultScheduler')
def add(a, b, **kwargs):
    v = int(a) + int(b)
    print("ADD: *"+str(v)+"*")
    return v


@workflow
@scheduler(cpus=10, sclass='entangle.scheduler.DefaultScheduler')
def workflow1(**kwargs):
    return add(
        mydata(drilldowns='Nation', measures='Population'),
        two()
    )


@workflow
@scheduler(cpus=10, sclass='entangle.scheduler.DefaultScheduler')
def workflow2(value, **kwargs):
    return add(
        value(),
        two()
    )


result = workflow2(workflow1)

print(result())
