from entangle.process import process
from entangle.http import request


@request(url='https://datausa.io/api/data', method='GET')
def request(data):
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


result = add(
    request(drilldowns='Nation', measures='Population'),
    two()
)

print(result())
