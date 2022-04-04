#!/usr/bin/python
# -*- coding: utf-8 -*-
from celerys import app
"""
TODO 这是一种简单的应用
标准案例
https://docs.celeryproject.org/en/stable/getting-started/next-steps.html
参考布局
proj/__init__.py
    /celery.py
    /tasks.py
    /celeryconfig.py
"""
"""
broker：celery消息代理中间件。
backend：指定结果后端后，可以输出存放线程执行结果，一般是ORM or RabbitMQ。也有有其他别的存储方式（SQLAlchemy / Django ORM、 MongoDB、Memcached、Redis、RPC ( RabbitMQ /AMQP)，自定义）。
include参数是模块列表导入的工人开始时。您需要在此处添加我们的任务模块，以便工作人员能够找到我们的任务。

对于RabbitMQ，您可以使用amqp://localhost，或者对于 Redis，您可以使用redis://localhost。
如果有用户名和密码则可以这样
redis://username:password@localhost:port/db0
"""


# 添加一个任务(并开启跟踪)
@app.task(track_started=True)
def add(x, y):
    return x + y


# 默认关闭消息确认，如果开启则遇到失败，则会重复执行
@app.task(acks_late=False)
def mul(self, x, y):
    try:
        result = x * y
    except Exception:
        # 遇到错误就手动重试
        self.retry()
    return result


# 关闭结果反馈
@app.task(ignore_result=True)
def xsum(numbers):
    return sum(numbers)


from celery import Task
"""
重写Task方法,然后使用base
"""


class DebugTask(Task):
    # 指定队列
    # queue = 'hipri'

    def __call__(self, *args, **kwargs):
        print('TASK STARTING: {0.name}[{0.request.id}]'.format(self))
        return self.run(*args, **kwargs)


@app.task(base=DebugTask)
def add2(x, y):
    return x + y


@app.task(queue='hipri')
# 指定队列执行
def hello(to):
    return 'hello {0}'.format(to)


"""
直接更改默认task
>>> from celery import Celery, Task

>>> app = Celery()

>>> class MyBaseTask(Task):
...    queue = 'hipri'

>>> app.Task = MyBaseTask
>>> app.Task
<unbound MyBaseTask>

>>> @app.task
... def add(x, y):
...     return x + y

>>> add
<@task: __main__.add>

>>> add.__class__.mro()
[<class add of <Celery __main__:0x1012b4410>>,
 <unbound MyBaseTask>,
 <unbound Task>,
 <type 'object'>]
"""