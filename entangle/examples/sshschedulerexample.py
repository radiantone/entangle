from entangle.logging.debug import logging
from entangle.process import process
from entangle.http import request
from entangle.ssh import ssh
from entangle.workflow import workflow
from entangle.scheduler import scheduler


scheduler_config = {'cpus': 3,
                    'impl': 'entangle.scheduler.DefaultScheduler'}


class MyResult(object):

    def set_result(self, result):
        self._result = result

    def get_result(self):
        return self._result


@scheduler(**scheduler_config)
@process
def add(a, b):
    v = int(a) + int(b)
    logging.info("ADD: *"+str(v)+"*")
    return v


#@ssh(user='darren', host='phoenix', key='/home/darren/.ssh/id_rsa.pub', python='/home/darren/miniconda3/bin/python')
@scheduler(**scheduler_config)
@process
def two():
    logging.info("Returning 2")
    return 4


@scheduler(**scheduler_config)
@process
def three():
    logging.info("Returning 3")
    return 3


'''
@ssh instructs entangle to run the function on a remote server. Servers that want to participate with entangle workflows
must already have shared keys in place to allow passwordless ssh use. Also, the remote machine needs to have a virtualenv
setup with entangle installed as well.
'''
@ssh(user='darren', host='radiant', key='/home/darren/.ssh/id_rsa.pub', python='/home/darren/venv/bin/python')
@scheduler(**scheduler_config)
@process
def workflow2():

    _add = add(
        three(),
        two()
    )

    result = _add()
    my_result = MyResult()
    my_result.set_result(result)
    return my_result


if __name__ == '__main__':
    workflow = workflow2()
    result = workflow()
    print("WORKFLOW RESULT:", result.get_result())

