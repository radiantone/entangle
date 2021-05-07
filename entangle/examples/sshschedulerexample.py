from entangle.logging.debug import logging
from entangle.thread import thread
from entangle.http import request
from entangle.ssh import ssh
from entangle.workflow import workflow
from entangle.scheduler import scheduler


scheduler_config = {'cpus': 3,
                    'impl': 'entangle.scheduler.DefaultScheduler'}


@scheduler(**scheduler_config)
@thread
def add(a, b):
    v = int(a) + int(b)
    print("ADD: *"+str(v)+"*")
    return v


@ssh(user='darren', host='phoenix', key='/home/darren/.ssh/id_rsa.pub', python='/home/darren/miniconda3/bin/python')
@scheduler(**scheduler_config)
@thread
def two():
    print("Returning 2")
    return 2


@scheduler(**scheduler_config)
@thread
def three():
    print("Returning 3")
    return 3


'''
@ssh instructs entangle to run the function on a remote server. Servers that want to participate with entangle workflows
must already have shared keys in place to allow passwordless ssh use. Also, the remote machine needs to have a virtualenv
setup with entangle installed as well.
'''
@ssh(user='darren', host='radiant', key='/home/darren/.ssh/id_rsa.pub', python='/home/darren/venv/bin/python')
@scheduler(**scheduler_config)
@thread
def workflow2():

    _add = add(
        three(),
        two()
    )

    return _add()


result = workflow2()

print(result())

