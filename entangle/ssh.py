"""
ssh.py - Run processes and schedulers on remote machines
"""
import codegen
import logging
from functools import partial
from entangle.process import ProcessMonitor
from entangle.thread import ThreadMonitor

def ssh(function=None, **kwargs):

    def decorator(func, *args, **kwargs):
        import paramiko
        import ast
        import astunparse



        """
        $ ssh-keygen -t rsa -b 4096 -C "darren@radiant"
        $ ls -l /home/darren/.ssh/id_rsa.pub
        $ ssh-copy-id darren@radiant

        """
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=kwargs['host'], username=kwargs['user'],
                    key_filename=kwargs['key'])

        # Execute command that runs the passed in decorator on remote machine
        command = 'ls /home/darren'
        stdin, stdout, stderr = ssh.exec_command(command)

        for line in stdout.read().splitlines():
            print(line)

        ssh.close()

        logging.debug("ssh: func source: {}".format(func.source))
        _ast = ast.parse(func.source)
        print(ast.dump(_ast, annotate_fields=True))
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

        logging.debug("ssh: func new source: {}".format(astunparse.unparse(_ast)))
        logging.debug("ssh args: {} {}".format(str(args), str(kwargs)))

        logging.debug("SSH: Calling function: {}".format(str(func)))
        def wrapper(f, *args, **kwargs):
            import time
            import inspect

            # Invoke function over ssh

            logging.debug("SSH: user:{} host:{} key: {}".format(kwargs['user'],kwargs['host'],kwargs['key']))
            del kwargs['user']
            del kwargs['host']
            del kwargs['key']

            return f(*args, **kwargs)

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
