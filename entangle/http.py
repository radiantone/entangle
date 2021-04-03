"""
process.py - Module that provides native OS process implementation of function tasks
"""
from process import ProcessFuture


def request(function=None,
            timeout=None,
            url=None,
            method='GET',
            sleep=None):
    """

    :param function:
    :param future:
    :param timeout:
    :param sleep:
    :return:
    """
    def decorator(func):
        def wrapper(f):

            # Build http request function here, get result
            # call func with result

            return ProcessFuture(f,
                                 timeout=timeout,
                                 sleep=sleep,
                                 future=True)

        return wrapper(func)

    if function is not None:
        return decorator(function)

    return decorator


