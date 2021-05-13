"""

"""
from entangle.logging.debug import logging
from entangle.process import process
from entangle.thread import thread
from entangle.ssh import ssh
from entangle.workflow import workflow
from entangle.scheduler import scheduler


scheduler_config = {'cpus': 3,
                    'impl': 'entangle.scheduler.DefaultScheduler'}


class MyResult:
    """

    """

    def __init__(self):
        self._result = None

    def set_result(self, result):
        self._result = result

    def get_result(self):
        return self._result


@scheduler(**scheduler_config)
@process
def add(a, b):
    v = int(a.get_result()) + int(b)
    logging.info("ADD: *"+str(v)+"*")
    return v


@ssh(user='darren', host='miko', key='/home/darren/.ssh/id_rsa.pub', python='/home/darren/venv/bin/python')
@scheduler(**scheduler_config)
@process
def two():
    logging.info("Returning 2")
    return 2


@ssh(user='darren', host='phoenix', key='/home/darren/.ssh/id_rsa.pub', python='/home/darren/miniconda3/bin/python')
@scheduler(**scheduler_config)
@thread
def three():
    logging.info("Returning 3")
    result = MyResult()
    result.set_result(3)
    return result


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
    print("WORKFLOW OBJ:", result)
    print("WORKFLOW RESULT:", result.get_result())
