import multiprocessing
import threading
import atexit
import time
from multiprocessing import shared_memory
from filelock import Timeout, FileLock

CPUS = multiprocessing.cpu_count()

global cpu_list

'''
The CPU bits (0 for unused, 1 for occupied) in the shared list are designed
to pre-empt load off the lockfiles and filesystem.
'''
try:
    cpu_list = shared_memory.ShareableList([0] * 4, name="cpus")
except:
    cpu_list = shared_memory.ShareableList(name="cpus")


def exit_handler():
    global cpu_list
    print("Closing sharedmemory")
    cpu_list.shm.close()
    cpu_list.shm.unlink()
    del cpu_list

atexit.register(exit_handler)

def grab_cpu():
    while True:
        cpus = shared_memory.ShareableList(name="cpus")
        for i in range(0, len(cpus)):
            cpu = cpus[i]
            print("Checking CPU{}:  {}".format(i, cpu))
            print(cpus)
            time.sleep(4)
            if cpu == 0:
                try:
                    lock = FileLock("/tmp/cpu{}.lock".format(i))
                    with lock.acquire(timeout=1):
                        print('===Occupy CPU{}: {}'.format(
                            i, threading.current_thread().name))
                            
                        # Set the CPU BIT
                        cpus[i] = 1
                        print(cpus)

                        # DO SOME WORK HERE
                        time.sleep(13)

                        # Clear the CPU bit
                        cpus[i] = 0
                        print('===Release CPU{}: {}'.format(
                            i, threading.current_thread().name))
                except Timeout:
                    print("Thread {}: CPU {} Lock was held already, looking for another CPU.".format(
                        threading.current_thread().name, i))
                finally:
                    lock.release()
                    time.sleep(4)
            else:
                print("Taking a break")
                time.sleep(4)

def grab_cpus():
    x = threading.Thread(target=grab_cpu)
    x.start()


if __name__ == '__main__':
    print("Starting thread...")
    grab_cpus()
    grab_cpus()
    
