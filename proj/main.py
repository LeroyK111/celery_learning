#!/usr/bin/python
# -*- coding: utf-8 -*-
from time import sleep
from tasks import add, mul, xsum
"""
进行简单调用
"""


def group_text():
    from celery import group
    # 全组
    result = group(add.s(i, i) for i in range(10))().get()
    print(result)
    # 部分组
    s1 = group(add.s(i) for i in range(10))
    result = s1(10).get()
    print(result)


def chain_text():
    from celery import chain
    # 链式调用
    result = chain(add.s(4, 4) | mul.s(8))().get()
    print(result)
    # 部分链
    g = chain(add.s(4) | mul.s(8))
    print(g(4).get())
    # 简用|
    result = (add.s(4, 4) | mul.s(8))().get()
    print(result)


def demo() -> None:
    # 这里调用tasks时，直接异步执行去了，主进程继续往下执行
    result = add.delay(4, 4)
    # 测试
    sleep(1)
    print("等待一秒，查看线程执行状态:", result.ready())
    # get很少使用，因为它将异步调用转换为同步调用,propagate=False覆盖异常，result.traceback
    content = result.get(timeout=1, propagate=False)
    print(content)
    print("如果出错则报出纤细错误", result.traceback)


def demo1():
    # 使用高级的调用方式
    # result = add.apply_async((2, 2))
    # 任务将被发送到一个名为的队列lopri，并且该任务最早会在消息发送后 10 秒执行。
    result = add.apply_async((2, 2), queue='lopri', countdown=1)

    # win32启动时加入队列名称  celery -A proj worker -P eventlet -c 1000 -Q lopri
    content = result.get(timeout=1, propagate=False)
    print("任务id:", result.id)
    print("执行结果:", content)
    print("loser check：", result.failed(), "win check:", result.successful())
    # PENDING等待 -> STARTED开始 -> SUCCESS成功
    print("任务执行状态:", result.state)


def demo2():
    from celerys import app
    # 异步获取结果，方式一
    result = add.delay(4, 4)
    task_id = result.id
    res = app.AsyncResult(task_id)
    print(res.get())
    # PENDING -> STARTED -> RETRY重试 -> STARTED开始 -> RETRY -> STARTED -> SUCCESS
    print(res.state)


def demo3():
    # add.signature((2, 2), countdown=10)
    s1 = add.s(2, 2)
    # 执行
    result = s1.apply_async()
    # result = s1.delay()
    print(result.get())
    """
    # 又可以类似偏函数
    s1 = add.s(2, )
    result = s1.delay(2)
    print(result.get())
    """


def chord_text():
    from celery import chord, group
    # 带有回调的组(先形成列表，然后链式调用)
    result = chord((add.s(i, i) for i in range(10)), xsum.s())().get()
    print(result)
    # 等价于
    result = (group(add.s(i, i) for i in range(10)) | xsum.s())().get()
    print(result)


def demo4():
    from tasks import test
    test.delay("世界\n")

if __name__ == '__main__':
    # demo()
    # demo1()
    # demo2()
    # demo3()
    # group_text()
    # chain_text()
    # chord_text()
    demo4()
