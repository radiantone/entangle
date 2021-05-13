"""
docker.py - Module that provides docker support decorators for running tasks inside containers
"""
import logging
import inspect
import re
from functools import partial
import docker as dkr


client = dkr.from_env()


def docker(function=None,
           image=None,
           packages=None,
           consume_gpu=True):
    """

    :param function:
    :param image:
    :param sleep:
    :return:
    """
    def decorator(func):
        def wrapper(f_func):

            lines = inspect.getsource(f_func)
            logging.info("Running container: %s",image)
            lines = re.sub('@', '#@', lines)
            name = f_func.__name__

            installpackages = []
            for package in packages:
                installpackages += ["pip install -q {}".format(package)]

            code = "bash -c \"{}\npython <<HEREDOC {}\nprint({}())\"\nHEREDOC".format(
                ";".join(installpackages), lines, name)

            logging.debug(code)
            env = {}

            if not consume_gpu:
                env['TF_FORCE_GPU_ALLOW_GROWTH'] = True

            result = client.containers.run(
                image, code, environment=env)

            logging.debug(result)
            return result

        pfunc = partial(wrapper, func)
        pfunc.__name__ = func.__name__

        return pfunc

    if function is not None:
        return decorator(function)

    return decorator
