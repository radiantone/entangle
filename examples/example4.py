import numpy as np
from entangle.process import process
from timeit import default_timer as timer
from numba import vectorize


@process(shared_memory=True)
def dopow(names, smm=None, sm=None):
    print("Names:", names)
    (namea, nameb, shapea, shapeb, typea, typeb) = names

    start = timer()
    shma = sm(namea)
    shmb = sm(nameb)
    np_shma = np.frombuffer(shma.buf, dtype=typea)
    np_shmb = np.frombuffer(shmb.buf, dtype=typeb)

    @vectorize(['float32(float32, float32)'], target='cuda')
    def pow(a, b):
        return a ** b

    pow(np_shma, np_shmb)
    duration = timer() - start
    print("Powers Time: ", duration)


@process(shared_memory=True)
def createvectors(smm=None, sm=None):

    vec_size = 100000000

    start = timer()
    a = b = np.array(np.random.sample(vec_size), dtype=np.float32)
    c = np.zeros(vec_size, dtype=np.float32)

    # write matrices to shared memory
    shma = smm.SharedMemory(a.nbytes)
    shmb = smm.SharedMemory(b.nbytes)

    names = (shma.name, shmb.name, a.shape, b.shape, a.dtype, b.dtype)

    duration = timer() - start
    print("Create Vectors Time: ", duration)
    return names


dp = dopow(
    createvectors()
)

dp()
