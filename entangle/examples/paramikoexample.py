import paramiko

"""
$ ssh-keygen -t rsa -b 4096 -C "darren@radiant"
$ ls -l /home/darren/.ssh/id_rsa.pub
$ ssh-copy-id darren@radiant

"""
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='radiant', username='darren',
            key_filename='/home/darren/.ssh/id_rsa.pub')

stdin, stdout, stderr = ssh.exec_command('ls /home/darren')

for line in stdout.read().splitlines():
    print(line)

ssh.close()
