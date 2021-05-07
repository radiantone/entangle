"""
ssh.py - Run processes and schedulers on remote machines
"""
import logging
import hashlib
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
        '''
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        logging.debug("SSH: connecting {} {} {}".format(hostname,username,sshkey))
        ssh.connect(hostname=hostname, username=username,
                    key_filename=sshkey)

        # Execute command that runs the passed in decorator on remote machine
        command = 'ls /home/darren'
        stdin, stdout, stderr = ssh.exec_command(command)

        for line in stdout.read().splitlines():
            print(line)

        ssh.close()
        '''
        logging.debug("ssh: func: {}".format(func.func))
        logging.debug("ssh: func source:\n{}".format(func.source))
        _ast = ast.parse(func.source)
        decorators = _ast.body[0].decorator_list
        ssh_decorator = None

        # TODO: Here we probably want to remove all the decorators and just build our
        # ssh call to ensure the decorated behaviors are executed.
        # Or we have to embed the decorator configs in the new source so it is passed
        # to the remote machine.
        # We want the @scheduler and its child decorators to run on the remote machine
        # complete with configs intact.
        # Functions have to be completely self-contained (i.e. include all imports)

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
            import sys
            import re

            # Invoke function over ssh
            # Function will need to be copied to remote machine as a file then
            # executed

            if 'SOURCE' in os.environ:
                sourcefile = os.environ['SOURCE']
            else:
                sourcefile = sys.argv[0]

            if sourcefile[0] == '/':
                print("FILE:",sourcefile)
            else:
                print("FILE:", os.getcwd()+os.path.sep+sourcefile)

            print(sourcefile)
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

            "Resolve arguments"
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
                app.write("resultp = codecs.encode(pickle.dumps(result), \"base64\").decode()\n")
                app.write("print('===BEGIN===')\n")
                app.write("print(resultp)")
            

            # Resolve args and kwargs
            # Then invoke func.__name__ remotely from source script
            # and return result
            # use a process to run the remote ssh and block for result
            # then async to monitor queue for result
            #
            # e.g.
            # import appsource.py
            #
            # result = appname(arg1,arg2,kwarg1=kwval1, etc)
            # pickle and encode result then print it

            # Receiving side here in ssh.py gets the encoded pickle and unpickles
            # it then returns the value
            # 
            # pfunc is a paramiko function that copies the python app source
            # to remote machine and then invokes python 
            # return ProcessMonitor(pfunc,..,..,)

            #return f(*args, **kwargs)
            p = partial(f, *args, **kwargs)


            p.__name__ = f.__name__

            logging.debug("args: {}   kwargs: {}".format(args,kwargs))
            ''' 
            What we want to do here is resolve the dependencies for f. Then encode those
            in the above script output and send all that to remote machine to execute f(*args, **kwargs)

            Need a parameter execute=False that only resolves dependencies and returns a tuple (*args, **kwargs)
            '''
            def ssh_function(remotefunc, username, hostname, sshkey, appuuid, sourceuuid):
                files = [appuuid+".py", sourceuuid+".py"]
                logging.debug(
                    "SCP files: {} to {}@{}:{}".format(files, username, hostname, '/tmp'))
                _ssh = paramiko.SSHClient()
                _ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                _ssh.connect(hostname=hostname, username=username,
                            key_filename=sshkey)
                logging.debug("SSH FUNCTION: {}".format(remotefunc))
                scp = SCPClient(_ssh.get_transport())
                
                scp.put(files,
                        remote_path='/tmp')
                '''
                Copy sshapp*.py and sshsource*.py to remote host
                Execute sshapp*.py on remote machine, parse stdout for result pickle
                Unpickle result
                return result
                '''
                command = "export SOURCE={}.py; cd /tmp; {} /tmp/{}.py".format(sourceuuid,
                    python, appuuid)

                result = None
                #with open('/tmp/ssh.out','w') as sshout:
                logging.debug("SSH: executing {} {}@{}".format(command, username, hostname))
                sshout.write(
                    "SSH: executing {} {}@{}\n".format(command, username, hostname))
                stdin, stdout, stderr = _ssh.exec_command(command)

                result_next = False
                for line in stdout.read().splitlines():
                    logging.debug("SSH: command stdout: {}".format(line))
                    sshout.write("SSH: command stdout: {}\n".format(line))
                    if result_next:
                        result = pickle.loads(
                            codecs.decode(line.encode(), "base64"))
                        logging.debug("SSH: got result: {}".format(result))
                        break
                    if line == "===BEGIN===":
                        result_next = True

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
