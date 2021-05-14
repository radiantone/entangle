# pylint: disable=locally-disabled, multiple-statements,  unexpected-keyword-arg, no-value-for-parameter, invalid-name, too-many-function-args, unused-import, missing-function-docstring
"""
TBD
"""
import json
from entangle.logging.debug import logging
from entangle.process import process
from entangle.http import request
from entangle.workflow import workflow


@process
@request(url='https://datausa.io/api/data', method='GET')
def mydata(data):
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


if __name__ == '__main__':
    result = workflow2(workflow1)

    print(result())
