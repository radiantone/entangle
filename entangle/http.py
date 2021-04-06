"""
request.py - Module that provides http request tasks
"""
import requests
from functools import partial


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
            def invoke_request(_func, **kwargs):

                def make_request(url, method, data):

                    if method == 'GET':
                        response = requests.get(url=url, params=data)
                        return response.content

                response = make_request(url, method, kwargs)
                return _func(response)

            pfunc = partial(invoke_request, func)
            pfunc.__name__ = func.__name__
            return pfunc

        return wrapper(func)

    if function is not None:
        return decorator(function)

    return decorator


