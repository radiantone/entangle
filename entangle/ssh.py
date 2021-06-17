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
import inspect
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
        hostname = kwargs['host']
        username = kwargs['user']
        sshkey = kwargs['key']
        python = kwargs['python'] if 'python' in kwargs else "python3.8"

        logging.debug("ssh: func: %s", func.func)
        if not func.source:
            func.source = inspect.getsource(func.func)
            func.func.userfunc = True
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
        logging.debug("ssh args: %s %s", str(args), str(kwargs))

        logging.debug("SSH: Calling function: %s", str(func))

        def wrapper(f_func, *args, **kwargs):
            """
            Description
            :param f:
            :param args:
            :param kwargs:
            :return:
            """
            def find_func(pfunc):
                logging.debug("find_func: %s", pfunc.__name__)
                if hasattr(pfunc, 'userfunc') and pfunc.userfunc:
                    return pfunc.userfunc
                elif isinstance(pfunc, partial):
                    return find_func(pfunc.func)
                return pfunc

            if 'SOURCE' in os.environ:
                sourcefile = os.environ['SOURCE']
            else:
                sourcefile = sys.argv[0]

            logging.debug("ssh: SOURCE:%s", sourcefile)
            with open(sourcefile) as source:
                logging.debug("ssh: SOURCE:%s", source.read())

            logging.debug("SSH: user:%s host:%s key: %s",
                          kwargs['user'], kwargs['host'], kwargs['key'])

            def setup_virtualenv(host, user, key, env):
                _ssh = paramiko.SSHClient()
                _ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                _ssh.connect(hostname=hostname, username=username,
                             key_filename=sshkey)
                command = "python3.8 -m venv {}; export LLVM_CONFIG=/usr/bin/llvm-config-10; {}/bin/pip install --upgrade py-entangle".format(
                    env, env)
                _, stdout, _ = _ssh.exec_command(command)
                for line in stdout.read().splitlines():
                    logging.debug("SSH: setup_virtualenv: stdout: %s", line)

            if 'env' in kwargs:
                # Set up virtualenv
                setup_virtualenv(
                    kwargs['host'], kwargs['user'], kwargs['key'], kwargs['env'])
                #python = "{}/bin/python".format(kwargs['env'])
                del kwargs['env']

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
                logging.debug("Parsing SOURCE")
                _ast = ast.parse(_source)

                funcdefs = [funcdef for funcdef in _ast.body if isinstance(
                    funcdef, ast.FunctionDef)]

                logging.debug("Removing decorators from SOURCE")
                for funcdef in funcdefs:
                    __funcname__ = funcdef.name
                    if __funcname__ == func.__name__:
                        decorators = funcdef.decorator_list
                        #ssh_decorator = None

                        remove_decorators = []
                        for decorator in decorators:
                            if hasattr(decorator, 'func') and (decorator.func.id == 'ssh' or decorator.func.id == 'dataflow'):
                                logging.debug("REMOVE SSH DECORATOR:")
                                remove_decorators += [decorator]

                        [decorators.remove(dec) for dec in remove_decorators]
                        #if ssh_decorator:
                        #    decorators.remove(ssh_decorator)
                '''
                for funcdef in funcdefs:
                    __funcname__ = funcdef.name
                    if __funcname__ == func.__name__:
                        try:

                            funcdef.decorator_list.clear()
                            pass
                        except:
                            import traceback
                            logging.error(traceback.format_exc())
                '''
                logging.debug("UNparsing SOURCE")
                _source = astunparse.unparse(_ast)
                logging.debug("Attempting to write SOURCE")
                with open('{}.py'.format(sourceuuid), 'w') as appsource:
                    appsource.write(_source)
                    logging.debug("Wrote SOURCE")

            appuuid = "sshapp"+hashlib.md5(uuid4().bytes).hexdigest()

            __func = find_func(func)

            with open('{}.py'.format(appuuid), 'w') as app:
                pargs = codecs.encode(pickle.dumps(vargs), "base64").decode()
                pargs = re.sub(r'\n', "", pargs).strip()
                app.write("import logging\n\n"
                          "logger=logging.getLogger()\n"
                          "logging.disabled=False\n"
                          "logger.disabled=False\n")
                app.write("import pickle, codecs, re\n")
                app.write("from {} import {}\n\n".format(
                    sourceuuid, __func.__name__))
                app.write("pargs = '{}'\n".format(pargs))
                app.write(
                    "args = pickle.loads(codecs.decode(pargs.encode(), \"base64\"))\n")
                app.write("print(\"ARGS: {}\".format(args))\n")
                app.write("result = {}(*args)()\n".format(__func.__name__))
                app.write("print(\"RESULT:\", result)\n")
                app.write(
                    "resultp = codecs.encode(pickle.dumps(result), \"base64\").decode()\n")
                app.write("print('===BEGIN===')\n")
                app.write("print(resultp)\n")

            p_func = partial(f_func, *args, **kwargs)

            p_func.__name__ = f_func.__name__

            logging.debug("args: %s   kwargs: %s", args, kwargs)

            def ssh_function(remotefunc, username, hostname, sshkey, appuuid, sourceuuid, *args):
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
                logging.debug("ssh_function: remote function args: %s", *args)
                files = [appuuid+".py", sourceuuid+".py"]
                logging.debug(
                    "SCP files: %s to %s@%s:%s", files, username, hostname, '/tmp')
                _ssh = paramiko.SSHClient()
                _ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                _ssh.connect(hostname=hostname, username=username,
                             key_filename=sshkey)
                logging.debug("SSH FUNCTION: %s", remotefunc)
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
                with open('/tmp/command', 'w') as cmd:
                    cmd.write(command)

                logging.debug("SSH: executing %s %s@%s",
                              command, username, hostname)
                _, stdout, _ = _ssh.exec_command(command)

                logging.debug("SSH: CWD %s", os.getcwd())
                logging.debug("SSH: importing module %s", sourceuuid)
                sys.path.append(os.getcwd())
                try:
                    importlib.import_module(sourceuuid)
                except Exception:
                    pass

                result_next = False
                resultlines = []
                for line in stdout.read().splitlines():
                    logging.debug("SSH: command stdout: %s", line)
                    if result_next:
                        if len(line.strip()) > 0:
                            resultlines += [line]
                            logging.debug("SSH: got result line: %s", line)
                    if line == b"===BEGIN===":
                        result_next = True

                logging.debug("Unpickle: %s", b"".join(resultlines))

                if len(resultlines) > 0:
                    result = pickle.loads(
                        codecs.decode(b"".join(resultlines), "base64"))
                else:
                    result = None

                # _ssh.exec_command("rm {}".format(
                #    " ".join(["/tmp/"+file for file in files])))
                _ssh.close()

                return result

            _p_func = find_func(p_func)

            logging.debug("_p_func: %s", _p_func)
            logging.debug("p_func: %s", p_func)
            ssh_p = partial(ssh_function, p_func, username,
                            hostname, sshkey, appuuid, sourceuuid)
            ssh_p.__name__ = p_func.__name__
            ssh_p.userfunc = f_func.func
            frame = sys._getframe(1)
            if 'dataflow' in frame.f_locals:
                logging.debug("DATAFLOW detected!")
                result = ssh_p()
            else:
                logging.debug("DATAFLOW NOT detected!")
                result = ProcessMonitor(ssh_p, timeout=None,
                                        wait=None,
                                        cache=False,
                                        shared_memory=False,
                                        sleep=0)

            if callable(result):
                _result = result()
            else:
                _result = result

            if isinstance(_result, ProcessMonitor):
                _result = _result()
            logging.debug("SSH RESULT2: %s", _result)

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
