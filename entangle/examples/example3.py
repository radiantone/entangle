# pylint: disable=locally-disabled, multiple-statements, no-value-for-parameter, no-member, invalid-name, too-many-function-args, unused-import, missing-function-docstring
"""
TBD
"""
from timeit import default_timer as timer
import numpy as np
from numba import vectorize
from entangle.logging.file import logging
from entangle.process import process
from entangle.scheduler import scheduler


scheduler_config = {'cpus': 3,
                    'impl': 'entangle.scheduler.DefaultScheduler'}


#@scheduler(**scheduler_config)
@process
def dovectors1():
    # pylint: disable=locally-disabled, unused-variable

    @vectorize(['float32(float32, float32)'], target='cuda')
    def dopow(a, b):
        return a ** b

    vec_size = 100

    a = b = np.array(np.random.sample(vec_size), dtype=np.float32)
    c = np.zeros(vec_size, dtype=np.float32)

    start = timer()
    matrix = dopow(a, b)
    duration = timer() - start
    return duration


#@scheduler(**scheduler_config)
@process
def dovectors2():
    # pylint: disable=locally-disabled, unused-variable

    @vectorize(['float32(float32, float32)'], target='cuda')
    def dopow(a, b):
        return a ** b

    vec_size = 100000000

    a = b = np.array(np.random.sample(vec_size), dtype=np.float32)
    c = np.zeros(vec_size, dtype=np.float32)

    start = timer()
    matrix = dopow(a, b)
    duration = timer() - start
    return duration


#@scheduler(**scheduler_config)
@process
def durations(*args):

    return args


if __name__ == '__main__':
    dp = durations(
        dovectors1(),
        dovectors2()
    )

    print(dp())
