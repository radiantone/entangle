"""
docker.py - Module that provides docker support decorators for running tasks inside containers
"""
import docker
import logging

from functools import partial

client = docker.from_env()


def docker(function=None,
           image=None,
           packages=[],
           sleep=0):
    """

    :param function:
    :param image:
    :param sleep:
    :return:
    """
    def decorator(func):
        def wrapper(f):
            import inspect
            import re

            lines = inspect.getsource(f)
            logging.info("Running container: {}".format(image))
            lines = re.sub('@', '#@', lines)
            name = f.__name__

            installpackages = []
            for package in packages:
                installpackages += ["pip install -q {}".format(package)]

            code = "bash -c \"{}\npython <<HEREDOC {}\nprint({}())\"\nHEREDOC".format(
                ";".join(installpackages), lines, name)

            logging.debug(code)
            result = client.containers.run(
                image, code)
            logging.debug(result)
            return result

        p = partial(wrapper, func)
        p.__name__ = func.__name__

        return p

    if function is not None:
        return decorator(function)

    return decorator
