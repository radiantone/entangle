"""
ssh.py - Run processes and schedulers on remote machines
"""
import logging
import hashlib
import sys
import os
import ast
import re
import codecs
import pickle
import importlib
from functools import partial
from ast import FunctionDef
from uuid import uuid4

import astunparse
import paramiko
from scp import SCPClient
from entangle.process import ProcessMonitor
from entangle.thread import ThreadMonitor


def ssh(function=None, **kwargs):
    """
    Description
    :param function:
    :param kwargs:
    :return:
    """
    def decorator(func, *args, **kwargs):
        """
        Description
        :param func:
        :param args:
        :param kwargs:
        :return:
        """

        def find_func(p_func):
            if isinstance(p_func, partial):
                return find_func(p_func.func)
            return p_func

        hostname = kwargs['host']
        username = kwargs['user']
        sshkey = kwargs['key']
        python = kwargs['python']

        logging.debug("ssh: func: %s", func.func)
        logging.debug("ssh: func source:\n%s", func.source)

        _ast = ast.parse(func.source)

        decorators = _ast.body[0].decorator_list
        ssh_decorator = None

        for decorator in decorators:
            if hasattr(decorator, 'func') and decorator.func.id == 'ssh':
                logging.debug("REMOVE SSH DECORATOR:")
                ssh_decorator = decorator

        if ssh_decorator:
            decorators.remove(ssh_decorator)

        logging.debug("ssh: func new source: %s", astunparse.unparse(_ast))
        logging.debug("ssh args: %s %s",str(args), str(kwargs))

        logging.debug("SSH: Calling function: %s",str(func))

        def wrapper(f_func, *args, **kwargs):
            """
            Description
            :param f:
            :param args:
            :param kwargs:
            :return:
            """
            def remove_ssh_decorator(fsource, username, hostname):
                """
                Description
                :param fsource:
                :param username:
                :param hostname:
                :return:
                """
                _ast = ast.parse(fsource)

                ssh_decorators = []

                for segment in _ast.body:
                    if isinstance(segment, FunctionDef):
                        decorators = segment.decorator_list
                        for decorator in decorators:
                            if hasattr(decorator, 'func') and decorator.func.id == 'ssh':
                                user_keyword = None
                                host_keyword = None
                                for keyword in decorator.keywords:
                                    if keyword.arg == 'user' and keyword.value.value == username:
                                        user_keyword = keyword
                                    if keyword.arg == 'host' and keyword.value.value == hostname:
                                        host_keyword = keyword
                                logging.debug("REMOVE SSH DECORATOR:")

                                if user_keyword and host_keyword:
                                    ssh_decorators += [decorator]

                for ssh_decorator in ssh_decorators:
                    logging.debug("SSH: Removing decorator: %s",ssh_decorator)
                    decorators.remove(ssh_decorator)

                return astunparse.unparse(_ast)

            if 'SOURCE' in os.environ:
                sourcefile = os.environ['SOURCE']
            else:
                sourcefile = sys.argv[0]

            with open(sourcefile) as source:
                logging.debug("SOURCE:%s",source.read())

            logging.debug("SSH: user:%s host:%s key: %s",
                kwargs['user'], kwargs['host'], kwargs['key'])

            del kwargs['user']
            del kwargs['host']
            del kwargs['key']

            logging.debug("Run function: %s(%s,%s)",
                func.__name__, args, kwargs)

            vargs = []

            for arg in args:
                if callable(arg):
                    vargs += [arg()]
                else:
                    vargs += [arg]

            sourceuuid = "sshsource"+hashlib.md5(uuid4().bytes).hexdigest()

            with open(sourcefile) as source:
                _source = source.read()
                _source = re.sub(r"@ssh\(user='{}', host='{}'".format(username,
                                 hostname), "#@ssh(user='{}', host='{}'".format(username,
                                 hostname), _source).strip()

                with open('{}.py'.format(sourceuuid), 'w') as appsource:
                    appsource.write(_source)

            appuuid = "sshapp"+hashlib.md5(uuid4().bytes).hexdigest()

            with open('{}.py'.format(appuuid),'w') as app:
                pargs = codecs.encode(pickle.dumps(vargs), "base64").decode()
                pargs = re.sub(r'\n', "", pargs).strip()
                app.write("import logging\n\n" \
                          "logger=logging.getLogger()\n" \
                          "logging.disabled=False\n" \
                          "logger.disabled=False\n")
                app.write("import pickle, codecs, re\n")
                app.write("from {} import {}\n\n".format(sourceuuid, func.__name__))
                app.write("pargs = '{}'\n".format(pargs))
                app.write("args = pickle.loads(codecs.decode(pargs.encode(), \"base64\"))\n")
                app.write("print(\"ARGS: {}\".format(args))\n")
                app.write("result = {}(*args)()\n".format(func.__name__))
                app.write("print(\"RESULT:\", result)\n")
                app.write(
                    "resultp = codecs.encode(pickle.dumps(result), \"base64\").decode()\n")
                app.write("print('===BEGIN===')\n")
                app.write("print(resultp)")

            p_func = partial(f_func, *args, **kwargs)

            p_func.__name__ = f_func.__name__

            logging.debug("args: %s   kwargs: %s",args,kwargs)

            def ssh_function(remotefunc, username, hostname, sshkey, appuuid, sourceuuid):
                """
                Description
                :param remotefunc:
                :param username:
                :param hostname:
                :param sshkey:
                :param appuuid:
                :param sourceuuid:
                :return:
                """
                files = [appuuid+".py", sourceuuid+".py"]
                logging.debug(
                    "SCP files: %s to %s@%s:%s", files, username, hostname, '/tmp')
                _ssh = paramiko.SSHClient()
                _ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                _ssh.connect(hostname=hostname, username=username,
                            key_filename=sshkey)
                logging.debug("SSH FUNCTION: %s",remotefunc)
                scp = SCPClient(_ssh.get_transport())

                try:
                    scp.put(files,
                            remote_path='/tmp')
                finally:
                    pass
                    #[os.remove(file) for file in files]

                command = "export SOURCE={}.py; cd /tmp; {} /tmp/{}.py".format(sourceuuid,
                    python, appuuid)

                result = None

                logging.debug("SSH: executing %s %s@%s",command, username, hostname)
                _, stdout, _ = _ssh.exec_command(command)

                logging.debug("SSH: CWD %s",os.getcwd())
                logging.debug("SSH: importing module %s",sourceuuid)
                sys.path.append(os.getcwd())
                try:
                    importlib.import_module(sourceuuid)
                except Exception:
                    pass

                result_next = False
                resultlines = []
                for line in stdout.read().splitlines():
                    logging.debug("SSH: command stdout: %s",line)
                    if result_next:
                        if len(line.strip()) > 0:
                            resultlines += [line]
                            logging.debug("SSH: got result line: %s",line)
                    if line == b"===BEGIN===":
                        result_next = True

                logging.debug("Unpickle: %s",b"".join(resultlines))

                result = pickle.loads(
                    codecs.decode(b"".join(resultlines), "base64"))

                _ssh.exec_command("rm {}".format(" ".join(["/tmp/"+file for file in files])))
                _ssh.close()

                return result

            ssh_p = partial(ssh_function, p_func, username,
                            hostname, sshkey, appuuid, sourceuuid)
            ssh_p.__name__ = p_func.__name__

            result = ProcessMonitor(ssh_p, timeout=None,
                                    wait=None,
                                    cache=False,
                                    shared_memory=False,
                                    sleep=0)

            if callable(result):
                _result = result()
            else:
                _result = result

            logging.debug("SSH RESULT: %s",_result)

            # files = [appuuid+".py", sourceuuid+".py"]
            # [os.remove(file) for file in files]
            return _result

        p_func = partial(wrapper, func, **kwargs)

        if isinstance(func, (ProcessMonitor, ThreadMonitor)):
            p_func.__name__ = func.func.__name__
        else:
            p_func.__name__ = func.__name__

        return p_func

    if function is not None:
        logging.debug("ssh: function source: %s", function.source)
        return decorator(function, **kwargs)

    return partial(decorator, **kwargs)
