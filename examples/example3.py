import logging

logging.basicConfig(filename='scheduler.log',
                    format='%(asctime)s : %(levelname)s : %(message)s', level=logging.DEBUG)
import numpy as np
from entangle.process import process
from entangle.scheduler import scheduler
from timeit import default_timer as timer
from numba import vectorize


scheduler_config = {'cpus': 3,
                    'sclass': 'entangle.scheduler.DefaultScheduler'}


#@scheduler(**scheduler_config)
@process
def dovectors1():

    @vectorize(['float32(float32, float32)'], target='cuda')
    def pow(a, b):
        return a ** b

    vec_size = 100

    a = b = np.array(np.random.sample(vec_size), dtype=np.float32)
    c = np.zeros(vec_size, dtype=np.float32)

    start = timer()
    matrix = pow(a, b)
    duration = timer() - start
    return duration


#@scheduler(**scheduler_config)
@process
def dovectors2():

    @vectorize(['float32(float32, float32)'], target='cuda')
    def pow(a, b):
        return a ** b

    vec_size = 100000000

    a = b = np.array(np.random.sample(vec_size), dtype=np.float32)
    c = np.zeros(vec_size, dtype=np.float32)

    start = timer()
    matrix = pow(a, b)
    duration = timer() - start
    return duration


#@scheduler(**scheduler_config)
@process
def durations(*args):

    times = [arg for arg in args]

    return times


dp = durations(
    dovectors1(),
    dovectors2()
)

print(dp())
