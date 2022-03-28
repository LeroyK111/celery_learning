#!/usr/bin/python
# -*- coding: utf-8 -*-
from celery import Celery
"""
TODO 这是一种简单的应用
broker参数指定要使用的代理的 URL。
backend参数指定的结果后端使用。
include参数是模块列表导入的工人开始时。您需要在此处添加我们的任务模块，以便工作人员能够找到我们的任务。

标准案例
https://docs.celeryproject.org/en/stable/getting-started/next-steps.html
参考布局
proj/__init__.py
    /celery.py
    /tasks.py
"""
# 第一个参数是项目名称,第二个参数是消息代理
app = Celery('proj',
             broker='redis://127.0.0.1:6379/5',
             backend="redis://127.0.0.1:6379/5",
             include=["proj.tasks"])


@app.task
def add(x, y):
    return x + y
