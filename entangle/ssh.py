"""
ssh.py - Run processes and schedulers on remote machines
"""
import logging
import hashlib
import sys
import os
from uuid import uuid4
from functools import partial
from entangle.process import ProcessMonitor
from entangle.thread import ThreadMonitor
from scp import SCPClient, SCPException


def ssh(function=None, **kwargs):

    def decorator(func, *args, **kwargs):
        import paramiko
        import ast
        import astunparse

        def find_func(p):
            if type(p) is partial:
                return find_func(p.func)
            return p

        """
        $ ssh-keygen -t rsa -b 4096 -C "darren@radiant"
        $ ls -l /home/darren/.ssh/id_rsa.pub
        $ ssh-copy-id darren@radiant

        """
        hostname = kwargs['host']
        username = kwargs['user']
        sshkey = kwargs['key']
        python = kwargs['python']

        logging.debug("ssh: func: {}".format(func.func))
        logging.debug("ssh: func source:\n{}".format(func.source))

        _ast = ast.parse(func.source)

        decorators = _ast.body[0].decorator_list
        ssh_decorator = None

        for decorator in decorators:
            if hasattr(decorator, 'func') and decorator.func.id == 'ssh':
                logging.debug("REMOVE SSH DECORATOR:")
                ssh_decorator = decorator

        if ssh_decorator:
            decorators.remove(ssh_decorator)

        logging.debug("ssh: func new source: {}".format(
            astunparse.unparse(_ast)))
        logging.debug("ssh args: {} {}".format(str(args), str(kwargs)))

        logging.debug("SSH: Calling function: {}".format(str(func)))

        def wrapper(f, *args, **kwargs):
            import time
            import inspect
            import os
            import re

            # Invoke function over ssh
            # Function will need to be copied to remote machine as a file then
            # executed

            def remove_ssh_decorator(fsource, username, hostname):
                from ast import FunctionDef
                _ast = ast.parse(fsource)
                
                ssh_decorators = []

                for segment in _ast.body:
                    if type(segment) == FunctionDef:
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
                    logging.debug("SSH: Removing decorator: {}".format(ssh_decorator))
                    decorators.remove(ssh_decorator)

                return astunparse.unparse(_ast)

            if 'SOURCE' in os.environ:
                sourcefile = os.environ['SOURCE']
            else:
                sourcefile = sys.argv[0]

            with open(sourcefile) as source:
                logging.debug("SOURCE:{}".format(source.read()))

            logging.debug("SSH: user:{} host:{} key: {}".format(
                kwargs['user'], kwargs['host'], kwargs['key']))

            del kwargs['user']
            del kwargs['host']
            del kwargs['key']

            logging.debug("Run function: {}({},{})".format(
                func.__name__, args, kwargs))

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
                import codecs
                import pickle
                import re

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
            

            p = partial(f, *args, **kwargs)

            p.__name__ = f.__name__

            logging.debug("args: {}   kwargs: {}".format(args,kwargs))

            def ssh_function(remotefunc, username, hostname, sshkey, appuuid, sourceuuid):
                import importlib

                files = [appuuid+".py", sourceuuid+".py"]
                logging.debug(
                    "SCP files: {} to {}@{}:{}".format(files, username, hostname, '/tmp'))
                _ssh = paramiko.SSHClient()
                _ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                _ssh.connect(hostname=hostname, username=username,
                            key_filename=sshkey)
                logging.debug("SSH FUNCTION: {}".format(remotefunc))
                scp = SCPClient(_ssh.get_transport())
                
                try:
                    scp.put(files,
                            remote_path='/tmp')
                finally:
                    pass
                    #[os.remove(file) for file in files]
                '''
                Copy sshapp*.py and sshsource*.py to remote host
                Execute sshapp*.py on remote machine, parse stdout for result pickle
                Unpickle result
                return result
                '''
                command = "export SOURCE={}.py; cd /tmp; {} /tmp/{}.py".format(sourceuuid,
                    python, appuuid)

                result = None

                logging.debug("SSH: executing {} {}@{}".format(command, username, hostname))
                stdin, stdout, stderr = _ssh.exec_command(command)

                logging.debug("SSH: CWD {}".format(os.getcwd()))
                logging.debug("SSH: importing module {}".format(sourceuuid))
                sys.path.append(os.getcwd())
                try:
                    importlib.import_module(sourceuuid)
                except:
                    pass

                result_next = False
                resultlines = []
                for line in stdout.read().splitlines():
                    logging.debug("SSH: command stdout: {}".format(line))
                    if result_next:
                        if len(line.strip()) > 0:
                            resultlines += [line]
                            logging.debug("SSH: got result line: {}".format(line))
                    if line == b"===BEGIN===":
                        result_next = True

                logging.debug("Unpickle: {}".format(b"".join(resultlines)))

                result = pickle.loads(
                    codecs.decode(b"".join(resultlines), "base64"))

                _ssh.exec_command("rm {}".format(" ".join(["/tmp/"+file for file in files])))
                _ssh.close()

                return result

            ssh_p = partial(ssh_function, p, username, hostname, sshkey, appuuid, sourceuuid)
            ssh_p.__name__ = p.__name__
            
            result = ProcessMonitor(ssh_p, timeout=None,
                                    wait=None,
                                    cache=False,
                                    shared_memory=False,
                                    sleep=0)
            
            if callable(result):
                _result = result()
            else:
                _result = result

            logging.debug("SSH RESULT: {}".format(_result))


            files = [appuuid+".py", sourceuuid+".py"]
            #[os.remove(file) for file in files]
            return _result

        p = partial(wrapper, func, **kwargs)

        if type(func) is ProcessMonitor or type(func) is ThreadMonitor:
            p.__name__ = func.func.__name__
        else:
            p.__name__ = func.__name__

        return p

    if function is not None:
        logging.debug("ssh: function source: {}".format(function.source))
        return decorator(function, **kwargs)

    return partial(decorator, **kwargs)
