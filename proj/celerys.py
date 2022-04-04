#!/usr/bin/python
# -*- coding: utf-8 -*-
from celery import Celery
# 实例化一个对象
app = Celery('celerys')
# 直接从本文件中取参数
app.config_from_object('celeryconfig')

# 在当前文件夹启动该线程
# >celery -A celerys worker --loglevel=INFO
# 使用专门的线程库
# >celery -A celerys worker --loglevel=INFO -P eventlet
# 可以直接使用 RabbitMQ 或 Redis 作为代理，那么您还可以指示工作人员在运行时为任务设置新的速率限制
# celery -A celerys control rate_limit celerys.add 10/m

if __name__ == '__main__':
    app.start()
