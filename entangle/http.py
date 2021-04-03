"""
request.py - Module that provides http request tasks
"""
from process import ProcessFuture
import requests


def request(function=None,
            timeout=None,
            url=None,
            method='GET',
            sleep=None):
    """

    :param function:
    :param timeout:
    :param url:
    :param method:
    :param sleep:
    :return:
    """
    def decorator(func):
        def wrapper(f):

            # Build http request function here, get result
            # call func with result
            # TBD

            return ProcessFuture(f,
                                 timeout=timeout,
                                 sleep=sleep,
                                 future=True)

        return wrapper(func)

    if function is not None:
        return decorator(function)

    return decorator


