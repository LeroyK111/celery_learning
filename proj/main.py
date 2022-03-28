#!/usr/bin/python
# -*- coding: utf-8 -*-
from tasks import add
"""
# 查询任务状态
result.state
检查任务成功还是失败
result.failed()
res.successful()
构造对象，触发delay时才调用任务
add.signature((2, 2), countdown=10)
add.s(2, 2)
======================================================
不常用部分
Groups分组检索
from celery import group
>>> group(add.s(i, i) for i in range(10))().get()
[0, 2, 4, 6, 8, 10, 12, 14, 16, 18]

>>> g = group(add.s(i) for i in range(10))
>>> g(10).get()
[10, 11, 12, 13, 14, 15, 16, 17, 18, 19]

===================================================
>>> from celery import chain
>>> from proj.tasks import add, mul
任务连锁
# (4 + 4) * 8
>>> chain(add.s(4, 4) | mul.s(8))().get()
64

>>> # (? + 4) * 8
>>> g = chain(add.s(4) | mul.s(8))
>>> g(4).get()
64

>>> (add.s(4, 4) | mul.s(8))().get()
64
==================================================
>>> from celery import chord
>>> from proj.tasks import add, xsum
带有回调的链式任务
>>> chord((add.s(i, i) for i in range(10)), xsum.s())().get()
90

>>> (group(add.s(i, i) for i in range(10)) | xsum.s())().get()
90
"""
result = add.delay(4, 4)
# 是否完成处理
print(result.ready())
# 这里会将异步变为同步,参数避免错误propagate=False,给个延时timeout=1
print(result.get())
# 找到任务ID
print(result.id)
# 错误回溯
print(result.traceback)
# 任务将被发送到一个名为的队列lopri，任务将在消息发送后最早 10 秒执行。
add.apply_async((2, 2), queue='lopri', countdown=10)
