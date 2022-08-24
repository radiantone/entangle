*This version: 0.2.3*

![logo](./images/logo.png)

*Current development version is here: [0.2.4](https://github.com/radiantone/entangle/tree/0.2.4)*

A lightweight (serverless) native python parallel processing framework based on simple decorators and call graphs, supporting both *control flow* and *dataflow* execution paradigms as well as de-centralized CPU & GPU scheduling. 

> For a quick look at what makes Entangle special, take a look at [Design Goals](#design-goals).

## New In This Release

- Bug fixes to process.py, ssh.py
- Distributed dataflow example
- Dataflow decorator re-write. Now works with ssh for distributed dataflow. Fixes prior issues with local dataflows.
- Retry usage example 
- Dockerfile provided for quick and easy experimentation.
- Workflows can now return the call graph structure upon completion. See [Graph Example](#graph-example)
- Support for workflow futures (if that's your thing) See [Workflow Future Example](#workflow-future-example)

## Quick Usage

With Entangle you can run simple, hardware parallelized code with conditional logic that looks like this.

```python
result = add(
            add(
                num(6),
                two() if False else one()
            ),
            subtract(
                five(),
                two()
            )
)
print(result())
```
or train two AI models in parallel using tensorflow container utilizing dedicated CPU and GPU usage.
```python
@process
@docker(image="tensorflow/tensorflow:latest-gpu", packages=['tensorflow_datasets'])
def train_modelA():
    # train it
    return

@process
@docker(image="tensorflow/tensorflow:latest-gpu", packages=['tensorflow_datasets'])
def train_modelB():
    # train it
    return

@workflow
def train_models(*args):
    # I'm training a bunch of models in parallel!
    return

workflow = train_models(
    train_modelA(),
    train_modelB()
)

result = workflow()
```
### Docker
To quickly get started with Entangle, build and run a docker container from the included Dockerfile.

```bash
$ docker build -t entangle .
$ docker run -it entangle:latest
root@9579336b3e34:/# python -m entangle.examples.example
```
Or if you have the [NVIDIA Docker Environment](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html#docker) setup you can test the numba GPU vector example.

```bash
$ docker run -it --gpus all entangle
root@13428af4a37b:/# python -m entangle.examples.example3
(0.2957176749914652, 0.41134210501331836)
```
[Click here](https://www.scaler.com/topics/what-is-docker/) to know more about Docker.

## Wiki Articles
- [How Does Entangle Compare to Other Parallel Compute Frameworks?](https://github.com/radiantone/entangle/wiki)
- [Development Roadmap & Contributions](https://github.com/radiantone/entangle/wiki/Development)

## Outline

* [Overview](#overview)
  * [What does "Entangle" mean?](#what-does-entangle-mean)
  * [Important Notes](#important-notes)
* [Installation](#installation)
* [Design Goals](#design-goals)  
* [Architecture](#architecture)
* [Declarative Infrastructure](#declarative-infrastructure)
* [Execution](#execution)  
* [Workflows](#workflows)  
* [Process Behavior](#process-behavior)  
* [Composition](#composition)  
  * [Decorator Composition](#decorator-composition)
  * [Workflow Composition](#workflow-composition)
* [Containers](#containers)  
* [Dataflows](#dataflows)
  * [Dataflow vs Workflows](#dataflows-vs-workflows)
  * [DAG Dataflow](#dag-dataflow)
  * [Results Comparison](#results-comparison)
  * [Advantages of Strict Dataflow](#advantages-of-strict-dataflow)
* [Schedulers](#schedulers)
* [Distributed Flows](#distributed-flows)  
* [Examples](#examples)
    * [GPU Example](#gpu-example)
    * [Shared Memory Example](#shared-memory-example)
    * [AI Example](#ai-example)
    * [Dataflow Examples](#dataflow-examples)
      * [Data-Driven Branching](#data-driven-branching)
      * [Distributed Dataflow](#distributed-dataflow)
    * [Docker Example](#docker-example)
    * [Scheduler Example](#scheduler-example)
    * [Graph Example](#graph-example)
    * [Workflow Future Example](#workflow-future-example)
* [Logging](#logging)
* [Design Tool](#design-tool)  

## Overview

Entangle is a *different* kind of parallel compute framework for multi-CPU/GPU environments. 
It allows for simple workflow design using *plain old python* and special decorators that control the type of parallel compute and infrastructure needed.

One key feature of entangle is fine-grained control over individual functions in a workflow. You could easily describe multiple functions running across multiple compute environments all interacting as if they were simple local python functions.
No central scheduler or workflow manager is needed allowing you to choose where and how functions operate with *declarative infrastructure*.

Another unique quality is the use of composition to build parallel workflows dynamically.

### What does "Entangle" mean?

The term is derived from a quantum physics phenomena called *[quantum entanglement](https://en.wikipedia.org/wiki/Quantum_entanglement#:~:text=Quantum%20entanglement%20is%20a%20physical,including%20when%20the%20particles%20are)* which involves the state of a pair or group of particles affecting one another *at a distance* instantaneously.

In this context, it is a metaphor for how tasks send data (particles) to one another in the context of a connected microflow.

### IMPORTANT NOTES!

Please keep in mind that Entangle is *in development* and is classified as `Pre-Alpha`. Some of the functionality shown here is incomplete. If you clone this repo and want to experiment be sure to update often as things break, improve, get fixed etc. quite frequently. The `main` branch will always contain the most current release. All development for the next version is done on the development branch for the next released listed at the top of this document.

## Installation

NOTE: At the moment entangle only works with python 3.8 due to how coroutines work there and also shared memory features.

From PyPi

```shell
$ pip install --upgrade py-entangle
$ python -m entangle.examples.example
```
From repo root

*python3.8*

```shell

$ virtualenv --python=python3.8 venv
$ source venv/bin/activate
(venv) $ python setup.py install
(venv) $ python -m entangle.examples.example
```

*miniconda3*
1. Install [miniconda3](https://docs.conda.io/projects/conda/en/latest/user-guide/install/linux.html) with python3.8 for linux
```shell
$ conda init   
$ python setup.py install
$ python -m entangle.examples.example
```

### Installing Numba

> NOTE: Numba package is disabled by default in `setup.py`. If you want this package, just uncomment it; however some OS specific steps might be required.

On some systems you might encounter the following error when trying to install  `numba`.
```bash
RuntimeError: Could not find a `llvm-config` binary.
```

Try the following remedy (for ubuntu systems)

```bash
$ sudo apt-get install -y --no-install-recommends  llvm-10 llvm-10-dev
$ export LLVM_CONFIG=/usr/bin/llvm-config-10
$ pip3 install numba
```

### Testing

```shell
$ pytest --verbose --color=yes --disable-pytest-warnings --no-summary --pyargs entangle.tests
```
or if you don't have GPU
```shell
$ pytest --verbose --color=yes --pyargs entangle.tests.test_entangle
```
or just do this
```shell
$ python setup.py test
```
### Cleaning
Clean all build files, directories, temp files and any files created by examples and tests.

```shell
$ python setup.py clean
```
### Miniconda

If you are planning to run or use GPU enabled code it is recommended to set up a [miniconda3](https://docs.conda.io/projects/conda/en/latest/user-guide/install/linux.html) virtualenv.

## Design Goals

* Small & Simple
* Easy to Understand
* API-less
* Plain Old Python
* True Parallelism
* Pluggable & Flexible
* Composition Based
* Shared-Nothing
* Serverless & Threadless
* True Dataflow Support
* CPU/GPU Scheduling
* Distributed Dataflow

## Architecture

Entangle is designed without a central scheduler or workflow manager. Rather, each function is decorated with special descriptors that turn them into their own workflow managers.
These *decorators* implement logic to parallelize and *gather* values from its dependent arguments, which are executed as separate processes. As each function is assigned a dedicated CPU, the workflow is thus an ensemble of parallel, independent micro-flows that resolve themselves and pass their values into queues until the workflow completes.

This offers an extreme *shared nothing* design that maximizes CPU usage in a multi-CPU environment.

Each function (or task) is given a process and scheduled to a CPU by the operating system. Since python Processes are native bound OS processes, this inherits the benefit of the operating system scheduler which is optimized for the underlying hardware.
Arguments that satisfy the function are run in parallel in the same fashion. The parent function then uses asyncio coroutines to monitor queues for the results from the processes. This keeps the CPU usage down while the dependent functions produce their results and eliminates the need for monitor threads.

As a workflow executes, it fans out over CPUs. Each process acting as it's own scheduler to spawn new processes and resolve arguments, while also monitoring queues for incoming results asynchronously.
This makes the workflow a truly emergent, dynamic computing construct vs a monolithic service managing all the pieces. Of course, this is not to say one approach is better, just that entangle takes a different approach based on its preferred tradeoffs.
![arch](./images/arch.png)

### Tradeoffs

Every design approach is a balance of tradeoffs. Entangle favors CPU utilization and *true* parallelism over resource managers, centralized (which is to say network centric) schedulers or other shared services.
It favors simplicity over behavior - leaving specific extensions to you, attempting to be minimal and un-opinionated. It tries to be *invisible* to the end user as much as possible. It strives for the basic principle that, *"if it looks like it should work, it should work."*

Entangle leans on the OS scheduler to prioritize processes based on the behavior of those processes and underlying resource utilizations. It therefore does not provide its own redundant (which is to say *centralized*) scheduler or task manager. Because of this, top-down visibility or control of workflow processes is not as easy as with centralized task managers.

Entangle prefers the non-API approach, where it looks like regular python expressions, over strict API's or invocation idioms. This makes it easier to pick up and use and plays well with 3rd party frameworks too.

### Use Cases

Because of these tradeoffs, there are certain use cases that align with entangle and others that probably do not.

If you want top-down visibility & control of workflows and tasks, Entangle is probably not ready for you.

If you have lots of CPUs, entangle could be for you! If you want easy python workflows that span local and remote cloud resources, entangle could be for you.
If you want to write custom handlers that enrich or execute code in custom ways for your needs, entangle makes this easy for you.

#### Orchestration

One focused use case for entangle is when you want to orchestrate across different compute nodes, remote APIs and other disparate endpoints in a single workflow, with inherent parallelism.

![workflow](./images/workflow.png)

Each step of the workflow has different parameters, needs and protocols used to communicate with it.
Such a workflow might simply look like:

```python
data = data_refinement(
    get_source_data()
)
result = measure_vectors(
    vector1(
        data("vector1")
    ),
    vector2(
        data("vector2")
    ),
    vector3(
        data("vector3")
    )
)
```

#### GPU Processing
Another use case is the need to run multiple parallel tasks that operate on matrix data using a GPU.
Entangle makes this quite easy as seen in [GPU Example](#gpu-example), [Docker Example](#docker-example) and [Shared Memory Example](#shared-memory-example)

#### DevOps
For devops use cases Entangle allows you to write simple, parallel workflow graphs using *plain old python*. This let's you write efficient parallel devops pipelines with ease. Build simple workflows that do powerful things like orchestrating across multiple clouds, services, repositories etc in an efficient dataflow parallel design.


### What Entangle is not
Here are some things entangle is not, *out-of-the-box*. This isn't to say entangle can't do these things. In fact, entangle is designed to be a low level framework for implementing these kinds of things.

* Entangle does not yet perform fail over (TBD)
* Entangle is not a batch process framework (TBD)
* Entangle is not map/reduce
* Entangle is not a centralized task manager

## Declarative Infrastructure

Entangle allows you to target specific infrastructure environments or needs using simple decorators.

For example, to specify a process run on local hardware you can use the @local decorator

```python
@process
@local
def myfunc():
    return
```

If you want to execute a function in AWS EC2 or fargate, you could write it as:

```python
@process
@aws(keys=[])
@ec2(ami='ami-12345')
def myfunc():
    return

@process
@aws(keys=[])
@fargate(ram='2GB', cpu='Xeon')
def myfunc():
    return
```

or using docker containers
```python
@process
@docker(image="tensorflow/tensorflow:latest-gpu")
def reduce_sum():
    import tensorflow as tf
    return tf.reduce_sum(tf.random.normal([1000, 1000]))
```
![infrastructure](./images/infrastructure.png)

If you have a custom on-prem environment you can write a simple decorator that deploys the task to that and use it alongside other infrastructure decorators.

### Where, What & How: Using Mixins

Entangle uses the concept of *mixins* to associate infrastructure needs (where) with compute (what) and concurrency needs (how). 
Thus, it allows you to mix and match combinations of these within a single workflow or dataflow.

For example, you might need to get data from `AWS Lambda`, run `GPU Algorithm on that data inside a container` then send those results to 10 CPUs in a `compute cloud` for *parallel analysis*, then gather those results and send them to a `web service` on your network for storage or rendering.
All these steps have different locations, infrastructure requirements, compute needs, processing times, and protocols.

## Execution

As we mentioned above, entangle workflows will fan out during execution and occupy CPUs throughout the workflow. The OS will determine the priority of processes based on their resource needs at the time of execution.
Here is a simple workflow and diagram showing how the parallel execution unfolds.

```python
result = add(
   mult(
      one(),
      two()
   ),
   three()
)
```

This execution order applies to workflows in entange. If you use `@dataflow` decorator the execution follows that of a dataflow compute model. Refer to the section [Dataflows](#dataflows) for more information.

![execution](./images/execution.png)


### Threads vs Processes

In Python, threads do not execute in parallel to one another, it only gives the illusion of such. Python handles the context switching between threads and is limited by the GIL.
Processes on the other hand, are not controlled by a GIL and can thus truly run in parallel. The host operating system governs the sheduling of processes and entangle is designed to exploit this benefit.


## Workflows

A workflow in Entangle is just a fancy term for a call graph of function processes. The example above in [Execution](#execution) is a simple workflow.
Workflows execute in *natural dependency ordering* that you'd expect from any python function call. The inner most dependencies are invoked first so they can return their values to parent functions.

Note that this paradigm is pretty much the way most imperative languages operate today, but it does differ from *dataflows* which we talk about down below [Dataflows](#dataflows).

### Imperative vs Structured Declaration

In Entangle, there are two ways you can write your workflows, depending which is more convenient for you. Both produce in the same execution sequence and results.

Let's look at the example below:

```python
result = add(
            add(
                num(6),
                two() if False else one()
            ),
            subtract(
                five(),
                two()
            )
)
```
This represents the *structured* paradigm, based off a more strict type of lambda math notation where functions invoke functions until the top-most value is produced.

We can also write this as a sequence of *imperative* declarations

```python
_five = five()
_two = two()
_sub = subtract(_five,_two)
_num = num(6)
_two2 = two() if False else one()
_add1 = add(_num,_two2)
result = add(_add1,_sub)
```

## Process Behavior

Keyword parameters on the `@process` decorator allow you to control some meta-behavior of the process.

### Wait

Wait indicates how long a function should wait before its arguments arrive. It is a sibling to *timeout* however it is different.
```python
@process(wait=20)
def values(*args):
    values = [arg for arg in args]

    return values


o = values(
    one(),
    train()
)
```
In the above example, it is saying that the `values` function will wait up to 20 seconds for *both* `one()` and `train()` functions to complete and return values otherwise it will throw a `ProcessTimeoutException`.
### Timeout

Timeout is more self-evident. It is the wait period in seconds, entangle will allow a process to run.

```python

# Wait at most, 3 seconds for this task to complete
@process(timeout=3)
def task():
    return True

# Wait indefinitely for this task to complete
@process
def taskB():
    return False
```

When a process times out, a `ProcessTimeoutException` will be thrown by Entangle and the process will be terminated if it is still alive.

## Composition

Entangle offers a couple different ways to use composition effectively: with *decorators* and with *workflows*.

### Decorator Composition

You can compose your tasks by combining process and infrastructure decorators.

Again, in the example below, we are declaring a *process* and *local* infrastructure for our task to run by composing two decorators together.
```python
@process
@local
def taskA():
    return
```
or, specifying that the task run as a process inside AWS fargate, unchanged.
```python
@process
@aws(keys=[])
@fargate(ram='2GB', cpu=4)
def taskA():
    return
```
### Workflow Composition
Composing workflows is just as simple. You can write code that itself constructs workflows on the fly easily.

```python
from entangle.process import process
from entangle.http import request
from entangle.workflow import workflow

@process
@request(url='https://datausa.io/api/data', method='GET')
def mydata(data):
    import json
    data = json.loads(data)
    return int(data['data'][0]['Year'])

@process
def two():
    return 2

@process
def add(a, b):
    v = int(a) + int(b)
    print("ADD: *"+str(v)+"*")
    return v

@workflow
def workflow1():
    return add(
        mydata(drilldowns='Nation', measures='Population'),
        two()
    )

@workflow
def workflow2(value):
    return add(
        value(),
        two()
    )

result = workflow2(workflow1)

print(result())
```

The key to making this work is the *deferring of execution* trait of Entangle which we will discuss in a later post.
But essentially it allows for separation of workflow *declaration* from *execution*. Doing this allows you to treat workflows as objects and pass them around anywhere a normal python function (or workflow) is expected. Prior to execution.

## Containers

Entangle supports two container technologies: *docker* and *singularity*(TBD). These are used with the associated decorators `@docker` and `@singularity`. 
Using containers allows you to run functions that have complex OS or python depdendencies not native to your hosting environment.

For a complete example, please see [Docker Example](#docker-example)

## Dataflows 


Entangle supports two kinds of execution flow, *dataflow*[[8]](#references) and *workflow* (or what is more traditionally called *control flow*). They both complete a DAG-based execution graph but in slightly different ways and with different advantages to the programmer.

As wikipedia states[[8]](#references):

> Dataflow is a software paradigm based on the idea of disconnecting computational actors into stages (pipelines) that can execute concurrently. Dataflow can also be called stream processing or reactive programming.[1]

However, Merriam-Webster's simple definition[[9]](#references) illuminates a key trait of dataflows - "...*as data becomes available*"

> : a computer architecture that utilizes multiple parallel processors to perform simultaneous operations as data becomes available

### Data Readiness

In many parallel data computations the arrival or readiness of some data might lag behind other data, perhaps coming from longer computations or farther away.
True dataflow models allow the computation to proceed on a parallel path *as far as it can go* with the currently available data.
This means dependent operations are not held up by control flow execution order in some cases and the overall computation is optimized.

![dataflow](./images/dataflow2.png)

### Dataflows vs Workflows

Author, slikts [[1]](#references), descibes these differences very nicely (from [[1]](#references)).

> Control flow refers to the path the point of execution takes in a program, and sequential programming that focuses on explicit control flow using control structures like loops or conditionals is called imperative programming. In an imperative model, data may follow the control flow, but the main question is about the order of execution.
>
>Dataflow abstracts over explicit control flow by placing the emphasis on the routing and transformation of data and is part of the declarative programming paradigm. In a dataflow model, control follows data and computations are executed implicitly based on data availability.
>
> Concurrency control refers to the use of explicit mechanisms like locks to synchronize interdependent concurrent computations. Dataflow is also used to abstract over explicit concurrency control.
### Simple Example
Let's start with a simple workflow example:

`A(B(),C())`

In traditional *control flow* or what I call *lambda based*[[10]](#references) execution, the programming language's *dependency analysis* will determine the order of execution. In this example `B()` and `C()` are dependencies of `A()` and thus need to complete *before* `A()` can be executed. In other words, they are *inputs* to `A()`. Basic stuff.

This means the execution of each compute function is aware of the specific dependent functions it must resolve first.
We call this *control depedency* [[2]](#references).

Let's say the dependency was reversed. Whereby, a value computed by `A()` was a dependency of *both* `B()` and `C()`. How would we write this in conventional *control flow*?

We might do something like this.

```python
B(A())
C(A())
```

Breaking our previous single expression into multiple expressions. However, in this case, `A()` is being invoked twice, which could produce different values.
So we might introduce a variable

```python
a = A()
B = B(a)
C = C(a)
```

Now we have 3 expressions that must run in a proper order. We have done some of the work by making a separate expression for our dependent value `a`. But for large dataflows this can be a bigger burden on the programmer to unravel all the dependencies and put them in proper order.

What if the execution of an expression was not computed using the traditional *dependency analysis* most languages use today but instead was defined by stricter *dataflow* semantics?

### DAG Dataflow
In dataflow, a DAG represents the flow of values from compute nodes where each node computes its value once and the value is *emitted* or sent to directionally connected nodes in the DAG.


![dataflow](./images/dataflow.png)

This paradigm makes it easier to express our intentions of sharing values from `A()` by computing it once and sending the results to `B()` and `C()`. Neither `B()` nor `C()` explicitly depend on `A()`. The dataflow DAG provides the dependency structure for all the compute nodes.

Now let's rewrite our expression if it were executed in strict *dataflow* order.

```python
A(
   B(),
   C()
)
```

Here, the dataflow engine executing this expression understands the intention to compute `A()` first, then *in parallel* compute `B()` and `C()` with the *same* result computed only once from `A()` as their input.
Written imperatively, this would equate to:

```python
a = A()
B(a)
C(a)
```
where `B(a)` and `C(a)` run in parallel.

**IMPORTANT!** The dataflow syntax provides the necessary graph structure for a dataflow engine to know explicitly which functions can operate in parallel.

### Results Comparison

So what are the differences in the results from our *workflow* version and our *dataflow* version? It should be clear that the workflow version takes as input 2 values (B(),C()) and produces 1 value, A().

However, our dataflow version is different. It takes as input 1 value A() and produces two results, B() and C(), in parallel. So the computations are different!

### Advantages of Strict Dataflow

As was pointed out in the intro to this section, dataflow provides declarative *data dependency* modelling for a computation. This is sometimes a more natural way of thinking about a problem for the human programmer.
It allows a clean separation between the initial state of a dataflow and various desired outcomes that would be more difficult to model using *control flow* programming, as the programmer will have to use multiple imperative steps to introduce the proper execution order and indicating which computations are parallel is unclear from linear ordering.

Dataflow has improved efficiencies when it comes to data-centric computations as well because it only computes nodes once per DAG execution.
This approach requires no *caching* or *variables* that might be required with imperative-based control flow.

#### Naturally Parallel

A dataflow DAG is a naturally and implicitly parallel model - by its declarative structure. For CPU-bound, data centric tasks it is simple and easy to understand for this reason.

#### Detailed Example

For a more detailed example of using `@dataflow` in entangle see [Dataflow Examples](#dataflow-examples).
### References

1. Concurrency Glossary - https://slikts.github.io/concurrency-glossary/
2. Dependency Graphs - https://en.wikipedia.org/wiki/Dependency_graph
3. Dataflow Programming - https://en.wikipedia.org/wiki/Dataflow_programming
4. Data-Flow vs Control-Flow for Extreme Level Computing - https://ieeexplore.ieee.org/document/6919190
5. Advances in Dataflow Programming Languages - https://futureofcoding.org/notes/dataflow/advances-in-dataflow-programming-langauges.html
6. Data dependency - https://en.wikipedia.org/wiki/Data_dependency
7. An introduction to a formal theory of dependence analysis - https://link.springer.com/article/10.1007/BF00128174
8. Dataflow - https://en.wikipedia.org/wiki/Dataflow
9. Dataflow - https://www.merriam-webster.com/dictionary/dataflow
10. Functional Programming/Lambda Calculus -https://www.tutorialspoint.com/functional_programming/functional_programming_lambda_calculus.htm

## Schedulers

Entangle supports a composition based mechanism for attaching schedulers to workflows and functions.
The scheduler class will control access to CPU resources based on its constraints. For example, if you want to run a workflow with potentially 20 parallel tasks, but only want to allocate 4 CPUs to execute the workflow, the scheduler class can ensure entangle doesn't spawn more processes than requested.
Schedulers wrap individual functions and pull CPU "cookies" off a scheduler queue to hand off to processes. Each cookie contains a CPU identifier that the process then binds to. When a cookie is placed on the queue by a process it means that CPU (id) is available for use.

Parallel processes thus use the queue mechanism to *self-organize* around the allocated CPUs by requesting cookies, assigning their CPU affinity to that cpu id, running their behaviors and returning the cookie to the queue when complete.
This approach requires no centralized scheduler server as the workfow processes all use the same multiprocessing.Queue to retrieve CPU cookies.

![scheduler](./images/scheduler.png)

### Pluggable Schedulers

Entangle allows you to provide your own scheduler class using the decorator.

```python
@scheduler(cpus=4,impl='my.package.MyScheduler'}
def myfunc():
    return
```
Currently, the scheduler class need only implement one method.

`def register(self, f, cpus=12):`

and return a `function` or `partial` that wraps the provided function with scheduler behavior.

To see the implementation of `DefaultScheduler` click [here](https://github.com/radiantone/entangle/blob/main/entangle/scheduler.py).

For a workflow example using scheduler see [Scheduler Example](#scheduler-example)  below.

## Distributed Flows

Entangle allows you to pass a workflow (or dataflow) to a remote machine for execution. When combined with `@scheduler` decorators this also forwards scheduler behavior to the remote machine where it manages the received workflow there.
This type of propagation requires no centralized (i.e. shared) scheduler or services and thus scales very well.

Moreover, parts of a workflow can be sent to different machines for a truly distributed workflow.

### SSH Decorator

Functions or flows (graph of functions) are remoted by using the `@ssh` decorator like the example below.

```python
@ssh(user='me', host='radiant', key='/home/me/.ssh/id_rsa.pub', python='/home/me/venv/bin/python')
@scheduler(**scheduler_config)
@thread
def workflow2():
    pass
```

In this example, we have declared a (contrived) workflow that adds the return values of 2 embedded functions and returns it.
The `@ssh` decorator indicates that this workflow is to be copied and executed on the remote server `myserver` as user `me` using the python executable at `/home/me/venv/bin/python`.
Entangle will marshall the codes to the remote server and execute them there. 

### Scheduler Propagation

If any dependent or subsequent functions are invoked on the remote server, any decorators that apply to those will be enforced.
If you use `@scheduler` then it will utilize the *scheduler queue* to request CPU cookies. If you also use another `@ssh` decorator then that dependent function will be shipped to a 3rd remote server and the process repeated there.

*diagram here*

Each time a workflow decorated with `@scheduler` is sent to a remote machine, that scheduler then manages its portion of the workflow and any dependent functions that it might resolve.
This pattern forms a sort of *distributed tree* of schedulers that work in parallel across multiple machines, yet fully resolve to complete the root workflow.

Let's take a closer look at this example, which uses 3 different machines to solve its workflow.

```python

@ssh(user='darren', host='miko', key='/home/darren/.ssh/id_rsa.pub', python='/home/darren/venv/bin/python')
@scheduler(**config)
@process
def two():
    # run some codes
    return 2

@ssh(user='darren', host='radiant', key='/home/darren/.ssh/id_rsa.pub', python='/home/darren/venv/bin/python')
@scheduler(**config)
@process
def three():
    # run some codes
    return 3

@scheduler(**config)
@process
def add(a, b):
    v = int(a.get_result()) + int(b)
    return v

@ssh(user='darren', host='phoenix', key='/home/darren/.ssh/id_rsa.pub', python='/home/darren/venv/bin/python')
@scheduler(**config)
@process
def workflow():

    _add = add(
        three(),
        two()
    )
    return _add()
```

In the above example, the `workflow()` is first sent to machine `phoenix` and executed there. It wraps the function `add` which also executes on `phoenix` because it has no `@ssh` decorator and the workflow is already there.

The `add()` function requires the functions `three()` and `two()` be solved first. These two functions are sent to machines `miko` and `radiant` to be solved.
The results are returned to the `add` function running on `phoenix` and the result of the `workflow()` is returned to the calling machine, or the machine where the workflow was executed on.

Once the `workflow()` reaches `phoenix` the `@scheduler` attached to the workflow manages the CPU's there according to its constraints.
Since the `add()` function has two dependencies that can run in parallel the `@schedular` can request 2 CPUs and run them in parallel.


*diagram*

## Examples

* [GPU Example](#gpu-example)
* [Shared Memory Example](#shared-memory-example)
* [AI Example](#ai-example)
* [Docker Example](#docker-example)
* [Dataflow Examples](#dataflow-examples)  
  * [Data-Driven Branching](#data-driven-branching)
  * [Distributed Dataflow](#distributed-dataflow)
* [Scheduler Example](#scheduler-example)  
* [Graph Example](#graph-example)
* [Workflow Future Example](#workflow-future-example)
* [Retry Example](#retry-example)
* [General Example](#general-example)

There are a variety of example workflows and dataflows you can run. In addition to the sample code provided below you can run these using the following commands.
```shell
$ python -m entangle.examples.example
$ python -m entangle.examples.example2
$ python -m entangle.examples.example3
$ python -m entangle.examples.example4
$ python -m entangle.examples.example5
$ python -m entangle.examples.example6
$ python -m entangle.examples.example_graph.py
$ python -m entangle.examples.example_graph_future.py
$ python -m entangle.examples.example_with_future.py
$ python -m entangle.examples.lambdaexample
$ python -m entangle.examples.listexample
$ python -m entangle.examples.listexample2
$ python -m entangle.examples.dataflowexample
$ python -m entangle.examples.dataflowexample2
$ python -m entangle.examples.dockerexample
$ python -m entangle.examples.aiexample
$ python -m entangle.examples.retry_example
$ python -m entangle.examples.schedulerexample
$ python -m entangle.examples.schedulerexample2
$ python -m entangle.examples.sshdatafloweexample
$ python -m entangle.examples.sshschedulerexample
$ python -m entangle.examples.timeoutexample
```
For a complete list of the examples source code and binders to run them please visit the wiki.

### GPU Example
This example assumes you have installed `nvidia-cuda-toolkit` and associated python packages along with `numba`.

In this example, two vectorized functions with different sized matrices are run in parallel, and their times are gathered.
```python
import numpy as np
from entangle.process import process
from timeit import default_timer as timer
from numba import vectorize

@process
def dovectors1():

    @vectorize(['float32(float32, float32)'], target='cuda')
    def pow(a, b):
        return a ** b

    vec_size = 100

    a = b = np.array(np.random.sample(vec_size), dtype=np.float32)
    c = np.zeros(vec_size, dtype=np.float32)

    start = timer()
    pow(a, b)
    duration = timer() - start
    return duration

@process
def dovectors2():

    @vectorize(['float32(float32, float32)'], target='cuda')
    def pow(a, b):
        return a ** b

    vec_size = 100000000

    a = b = np.array(np.random.sample(vec_size), dtype=np.float32)
    c = np.zeros(vec_size, dtype=np.float32)

    start = timer()
    pow(a, b)
    duration = timer() - start
    return duration

@process
def durations(*args):

    times = [arg for arg in args]

    return times

dp = durations(
    dovectors1(),
    dovectors2()
)

print(dp())

```
Which outputs something like
```python
[0.21504536108113825, 0.3445616390090436]
```

### Shared Memory Example

The default return value conduit in Entangle is the Queue. Task return values are marshalled back through queues where they are gathered and provided as function parameters to the parent process task.
This method is not desirable for very large data sets such as matrices in GPU computations. The below example shows how Entangle uses python 3.8's shared memory feature to implicitly share volatile memory across native parallel processes.


![sharedmemory](./images/memory.png)
```python
import numpy as np
from entangle.process import process
from timeit import default_timer as timer
from numba import vectorize

@process(shared_memory=True)
def dopow(names, smm=None, sm=None):
    (namea, nameb, shapea, shapeb, typea, typeb) = names

    start = timer()
    shma = sm(namea)
    shmb = sm(nameb)

    # Get matrixes from shared memory
    np_shma = np.frombuffer(shma.buf, dtype=typea)
    np_shmb = np.frombuffer(shmb.buf, dtype=typeb)

    @vectorize(['float32(float32, float32)'], target='cuda')
    def pow(a, b):
        return a ** b

    pow(np_shma, np_shmb)
    duration = timer() - start
    print("Powers Time: ", duration)

@process(shared_memory=True)
def createvectors(smm=None, sm=None):

    vec_size = 100000000

    start = timer()
    a = b = np.array(np.random.sample(vec_size), dtype=np.float32)
    c = np.zeros(vec_size, dtype=np.float32)

    # create shared memory for matrices
    shma = smm.SharedMemory(a.nbytes)
    shmb = smm.SharedMemory(b.nbytes)

    names = (shma.name, shmb.name, a.shape, b.shape, a.dtype, b.dtype)

    duration = timer() - start
    print("Create Vectors Time: ", duration)
    return names

dp = dopow(
    createvectors()
)

dp()
```

Outputs

```bash
Create Vectors Time:  0.8577492530457675
Powers Time:  0.8135421359911561
```

#### SharedMemoryManager & SharedMemory

In the example above, you will notice two special keywords being passed into the functions, 

`def createvectors(smm=None, sm=None):`

`smm` is a handle to the `SharedMemoryManager` being used for this workflow and `sm` is a handle to the `SharedMemory` class needed to acquire the shared memory segments by name.
If you set `shared_memory=True` then you *must* include these keyword arguments in your method or an error will occur.


---

Now, you might be asking yourself, if one of the design goals was *shared-nothing* then why are we talking about *shared memory*?
When we say "shared" (in shared-nothing) we refer to resources that have to be synchronized or locked when accessed by parallel processes, thereby creating bottlenecks in the execution.
The shared memory example here does not introduce any contention, rather, it is used in a pipeline fashion.
In this approach, a given shared memory address is only updated by one process at a time (e.g. using it to return its data to the waiting process). Multiple shared memory segments can be created during the course of a workflow
for parallel running processes.


### AI Example
Here is an example that uses tensorflow to train a model and return the summary.
```python
from entangle.logging.debug import logging
from entangle.docker import docker
from entangle.process import process

@process
@docker(image="tensorflow/tensorflow:latest-gpu", packages=['tensorflow_datasets'])
def train():
    import tensorflow as tf
    import tensorflow_datasets as tfds

    (ds_train, ds_test), ds_info = tfds.load(
        'mnist',
        split=['train', 'test'],
        shuffle_files=True,
        as_supervised=True,
        with_info=True,
    )

    def normalize_img(image, label):
        return tf.cast(image, tf.float32) / 255., label

    ds_train = ds_train.map(
        normalize_img, num_parallel_calls=tf.data.experimental.AUTOTUNE)
    ds_train = ds_train.cache()
    ds_train = ds_train.shuffle(ds_info.splits['train'].num_examples)
    ds_train = ds_train.batch(128)
    ds_train = ds_train.prefetch(tf.data.experimental.AUTOTUNE)

    ds_test = ds_test.map(
        normalize_img, num_parallel_calls=tf.data.experimental.AUTOTUNE)
    ds_test = ds_test.batch(128)
    ds_test = ds_test.cache()
    ds_test = ds_test.prefetch(tf.data.experimental.AUTOTUNE)

    model = tf.keras.models.Sequential([
        tf.keras.layers.Flatten(input_shape=(28, 28)),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dense(10)
    ])

    model.compile(
        optimizer=tf.keras.optimizers.Adam(0.001),
        loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
        metrics=[tf.keras.metrics.SparseCategoricalAccuracy()],
    )

    model.fit(
        ds_train,
        epochs=6,
        verbose=0,
        validation_data=ds_test,
    )

    return model.summary()

model = train()
print(model())

```

### Docker Example
In this example we are running a process that spawns the decorated function inside a docker container and waits for the result.
We compose this using the `@process` and `@docker` decorators to achieve the design. The function `reduce_sum` is run *inside* the docker container using image `tensorflow/tensorflow:latest-gpu` and the result is returned seamlessly to the workflow.
```python
from entangle.docker import docker
from entangle.process import process

import logging
logging.basicConfig(
    format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

@process
@docker(image="tensorflow/tensorflow:latest-gpu")
def reduce_sum():
    import tensorflow as tf
    return tf.reduce_sum(tf.random.normal([1000, 1000]))

rs = reduce_sum()
print(rs())

```

#### Tensorflow GPU Container

The above example launches a GPU enabled docker on the `nvidia docker` platform (running on your local machine). Tensorflow by default will consume the entire GPU for its processing, however if you want to run parallel GPU jobs that only consume GPU memory *as needed*, then you need to use:

`@docker(image="tensorflow/tensorflow:latest-gpu", consume_gpu=False)`

---

![docker](./images/docker.png)

### Dataflow Examples

The example below demonstrates the dataflow capability of Entangle. This is a different compute paradigm from workflows. Please read the section on [Dataflows vs Workflows](#dataflows-vs-workflows) for complete explanation of the difference.

> NOTE: We use threads as our execution unit in this example as it makes seeing the output possible. With `@process` you won't see the aggregate output on your console, instead it will be logged to `entangle.log` file.
> With Entangle you decide whether to use concurrency (threads) or parallelism (processes). Entangle is itself, threadless.
```python
import threading
import time
from entangle.logging.debug import logging
from entangle.dataflow import thread
from entangle.dataflow import process
from entangle.dataflow import dataflow

def triggered(func, result):
    print("triggered: {} {}".format(func.__name__, result))

@dataflow(callback=triggered)
@thread
def printx(x):
    print('printx: {}'.format(threading.current_thread().name))
    return("X: {}".format(x))

@dataflow(callback=triggered)
@thread
def printy(y):
    print('printy: {}'.format(threading.current_thread().name))
    return("Y: {}".format(y))

@dataflow(callback=triggered)
@thread
def printz(z):
    print('printz: {}'.format(threading.current_thread().name))
    return("Z: {}".format(z))

@dataflow(callback=triggered)
@thread
def echo(e):
    print('echo: {}'.format(threading.current_thread().name))
    return "Echo! {}".format(e)

@dataflow(executor='thread', callback=triggered, maxworkers=3)
def emit(a, **kwargs):
    print('emit: {}'.format(threading.current_thread().name))
    return a+"!"

# Create the dataflow graph 
flow = emit(
    printx(
        printz(
            echo()
        )
    ),
    printy(
        printz()
    ),
    printy()
)

# Invoke the dataflow graph with initial input
flow('emit')

time.sleep(2)

# Call flow again with different input value
flow('HELLO')
```
#### Data-Driven Branching

It's useful to have a data flow that routes to different paths depending on input data.
Entangle makes this relatively easy. The example below embeds a lambda expression directly in the dataflow structure that chooses either `printx()` or `printy()` as the next compute node depending on what the input value is - *after emit has generated the value*.

In the snippet below `emit` first produces a value based on some input, the result is emitted to either `printx()` or `printy()` depending on the value of the result.
Note that this is computed during the execution of the DAG, not at declaration time.
```python
flow = emit(
    lambda x: printx() if x == 'emit' else printy()
)

flow('emit')
```

![lambda](./images/lambda.png)

Full example:
```python
import threading
import time
from entangle.dataflow import thread
from entangle.dataflow import dataflow

def triggered(func, result):
    print("triggered: {} {}".format(func.__name__, result))

@dataflow(callback=triggered)
@thread
def printx(x):
    print('printx: {}'.format(threading.current_thread().name))
    return("X: {}".format(x))

@dataflow(callback=triggered)
@thread
def printy(y):
    print('printy: {}'.format(threading.current_thread().name))
    return("Y: {}".format(y))

@dataflow(executor='thread', callback=triggered, maxworkers=3)
def emit(a, **kwargs):
    print('emit: {}'.format(threading.current_thread().name))
    return a+"!"

# Create the dataflow graph 
# Defer whether we will forward to printx() or printy() depending
# on the result receive from emit. This won't be known until the data is ready.
flow = emit(
    lambda x: printx() if x == 'emit' else printy()
)

# Invoke the dataflow graph with initial input
flow('emit')

time.sleep(2)

# Call flow again with different input value
flow('HELLO')
```

Which outputs:

```text
   printx: emit MainThread
triggered: inner X: emit
printz: ThreadPoolExecutor-3_0
triggered: inner Z: X: emit
----------------------------
printy: MainThread
triggered: inner Y: HELLO
```
### Distributed Dataflow

In the example below, we combine `@dataflow` with `@ssh` to get instant distributed dataflow!

```python
import threading
import time

from entangle.logging.debug import logging
from entangle.ssh import ssh
from entangle.process import process
from entangle.dataflow import dataflow

def triggered(func, result):
    print("triggered: {} {}".format(func.__name__, result))

@dataflow(callback=triggered)
@ssh(user='darren', host='miko', key='/home/darren/.ssh/id_rsa.pub', python='/home/darren/venv/bin/python')
@process
def printz(z):
    print('printz: {}'.format(threading.current_thread().name))
    with open('/tmp/printz.out', 'w') as pr:
        pr.write("Z: {}".format(z))
    return "Z: {}".format(z)

@dataflow(callback=triggered)
@ssh(user='darren', host='radiant', key='/home/darren/.ssh/id_rsa.pub', python='/home/darren/venv/bin/python')
@process
def printx(x):
    print('printx: {}'.format(threading.current_thread().name))
    with open('/tmp/printx.out', 'w') as pr:
        pr.write("X: {}".format(x))
    return "X: {}".format(x)

@dataflow(callback=triggered)
@process
def printy(y):
    print('printy: {}'.format(threading.current_thread().name))
    return "Y: {}".format(y)

@dataflow(callback=triggered)
@ssh(user='darren', host='radiant', key='/home/darren/.ssh/id_rsa.pub', python='/home/darren/venv/bin/python')
@process
def echo(e):
    print('echo: {}'.format(threading.current_thread().name))
    with open('/tmp/echo.out', 'w') as pr:
        pr.write("Echo! {}".format(e))
    return "Echo! {}".format(e)

@dataflow(callback=triggered, maxworkers=3)
def emit(value):
    print('emit: {}'.format(threading.current_thread().name))
    return value+"!"

if __name__ == '__main__':
    results = []

    # Create the dataflow graph
    flow = emit(
        printx(
            printz(
                echo()
            )
        ),
        printy(
            printz()
        ),
        printy()
    )

    result = flow('emit')
```
### Scheduler Example

```python
from entangle.logging.debug import logging
from entangle.process import process
from entangle.http import request
from entangle.workflow import workflow
from entangle.scheduler import scheduler

scheduler_config = {'cpus': 2,
                    'impl': 'entangle.scheduler.DefaultScheduler'}

@scheduler(**scheduler_config)
@process
def two():
    return 2

@scheduler(**scheduler_config)
@process
def three():
    return 3

@scheduler(**scheduler_config)
@process
def add(a, b):
    print("add: {} {}".format(a,b))
    v = int(a) + int(b)
    print("ADD: *"+str(v)+"*")
    return v

@scheduler(**scheduler_config)
@workflow
def workflow2():
    return add(
        three(),
        two()
    )

result = workflow2()

print(result())
```

### Graph Example

The follow example code shows how we can collect the call graph trace for our workflow and display it.

```python
import json
import time
import asyncio
from entangle.logging.debug import logging
from entangle.process import process

@process
def one():
    return 1

@process
def two():
    return 2

@process
def five():
    return 5

@process
def num(n):
    return n

@process
def add(a, b):
    v = int(a) + int(b)
    print("ADD: *"+str(v)+"*")
    return v

@process
def subtract(a, b):
    return int(a) - int(b)

if __name__ == '__main__':

    workflow = add(
        add(
            num(6),
            two() if False else one()
        ),
        subtract(
            five(),
            add(
                subtract(
                    num(8),
                    two()
                ),
                one()
            )
        )
    )
    result = workflow()
    print(result)

    graph = workflow.graph(wait=True)
    print("GRAPH:",json.dumps(graph, indent=4))
```

Which outputs this graph structure

```python
GRAPH: {
    "add": [
        {
            "add": {
                "num": {
                    "6": []
                },
                "one": []
            }
        },
        {
            "subtract": {
                "five": [],
                "add": {
                    "subtract": {
                        "num": {
                            "8": []
                        },
                        "two": []
                    },
                    "one": []
                }
            }
        }
    ]
}
```

We can also use futures to wait for the graph data to arrive as a callback.

```python
future = workflow.graph(wait=False)

def show_graph(graph):
    print("GRAPH:", graph.result())

future.add_done_callback(show_graph)

future.entangle()
```

### Workflow Future Example

Entangle allows you to use future results for workflows if the blocking method doesn't meet your use case.
To do this, we alter the invocation of the workflow slightly.

```python
def callback(result):
    print("CALLBACK:", result.result())

# set up future callbacks
future = workflow.future(callback=callback)
print('Future:', future)

# Trigger workflow. Does not block
workflow(proc=True)

# Notify results when available
future.entangle() # Does not block
```
### Retry Example

To specify how many times a function should be retried before throwing an exception with a sleep value in seconds between retries.

```python
@process(retry=5. sleep=1)
def five():
    import time
    val = int(str(time.time()).split('.')[1]) % 5
    if val != 0:
        raise Exception("Not a FIVE!")
    return 5
```

### General Example
An example of how entangle will be used (still in development)
```python

from entangle.process import process
from entangle.thread import thread
from entangle.task import task
from entangle.local import local
from entangle.aws import ec2
from entangle.aws import lmbda
from entangle.http import request

@process(timeout=60)
@local(cpus=4)
def add(a, b):
    return a + b

@process(cache=True)
@aws(keys=[])
@ec2
def one():
    return 1

@thread
@local
def two():
    return 2

@lmbda(function='name')
@aws(keys=[])
def proxy():
    # lambda proxy
    pass

@process
def subtract(a, b):
    return int(a) - int(b)

@process
def five():
    return 5

@process
def num(n):
    return n

@process
@request(url='http://..../', method='POST')
def request(data):
    # Manipulate http response data here and return new result
    return data

# 1,2,3 get passed to lambda function and result returned
result = proxy(1,2,3)
# Pass key:value params and get result from your function
result = request(key1=value, key2=value )

# parallel workflow is just "plain old python"
result = add(
            add(
                num(6),
                two() if False else one()
            ),
            subtract(
                five(),
                two()
            )
        )

print(result())

```
## Logging

Logging in Entangle is intended to be convenient and provide some useful out-of-the-box defaults that "just work".

There are 3 default loggers you can import.

```python
from entangle.logging.info import logging
from entangle.logging.debug import logging
from entangle.logging.file import logging
```
And the details of each are:

*info*
```python
import logging

logging.basicConfig(
    format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
```

*debug*
```python
import logging

logging.basicConfig(
    format='%(asctime)s : %(levelname)s : %(message)s', level=logging.DEBUG)
```

*file*
```python
import logging

logging.basicConfig(filename='entangle.log',
                    format='%(asctime)s : %(levelname)s : %(message)s', level=logging.DEBUG)
```

You can of course provide your own logging configuration, but be sure to include it at the top of your file so the various entangle modules pick it up.
## Design Tool

A prototype visual design tool for Entangle is shown below. More details will be posted on thye wiki [here](https://github.com/radiantone/entangle/wiki/Design-Tool). 


![ui](./images/ui2.png)
