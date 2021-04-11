from entangle.docker import docker
from entangle.process import process

import logging
logging.basicConfig(
    format='%(asctime)s : %(levelname)s : %(message)s', level=logging.DEBUG)


@process
@docker(image="tensorflow/tensorflow:latest-gpu")
def one():
    import tensorflow as tf
    return tf.reduce_sum(tf.random.normal([1000, 1000]))


o = one()
print(o())
