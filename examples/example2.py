from entangle.process import process
from entangle.http import request
from entangle.workflow import workflow
import logging
logging.basicConfig(
    format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)


@process
@request(url='https://datausa.io/api/data', method='GET')
def mydata(data):
    import json
    data = json.loads(data)
    print('My function got the data! ', data)
    return int(data['data'][0]['Year'])


@process
def two():
    return 2


@process
def add(a, b):
    v = int(a) + int(b)
    print("ADD: *"+str(v)+"*")
    return v


@workflow
def workflow1():
    return add(
        mydata(drilldowns='Nation', measures='Population'),
        two()
    )


@workflow
def workflow2(value):
    return add(
        value(),
        two()
    )


result = workflow2(workflow1)

print(result())
