"""
配置实例，方法一，对象传参
app.conf.task_serializer = 'json'

配置实例，方法二，实参传入
app.conf.update(
    task_serializer='json',
    accept_content=['json'],  # Ignore other content
    result_serializer='json',
    timezone='Europe/Oslo',
    enable_utc=True,
)
"""
"""
这里就是方法三，创建一个celeryconfig.py文件，专门用来存放参数。
"""

# 消息代理
broker_url = 'redis://127.0.0.1/5'
# 结果后端
result_backend = 'redis://127.0.0.1/5'
# 任务序列化
task_serializer = "json"
# 结果序列化
result_serializer = 'json'
# 默认序列化程序
accept_content = ['json']
# 时区
timezone = 'Asia/Shanghai'
# 开启UTC时区
enable_utc = True
# 手动导入tasks
include = ["tasks"]
# 结果存储日期
result_expires = 3600

# 全局消息确认
task_acks_late = False
# 设置每个worker要做的任务和准备的任务。默认为-c 10的倍数
worker_prefetch_multiplier = 1
# 消息无法确认时，会自动重新提交
task_reject_on_worker_lost = False

# 将特殊任务放入特殊队列中
task_routes = {
    'tasks.add': {
        'queue': 'hipri'
    },
}
# 对任务进行速率限制，而不是路由它，这样一分钟内只能处理 10 个这种类型的任务（10/m）
# task_annotations = {
#     'tasks.add': {'rate_limit': '10/m'}
# }
"""
推荐方法,将定时任务写在celeryconfig.py
celery是将定时任务beat和工人任务worker分离了
启动工人的同时
celery -A celerys worker --loglevel=INFO -P eventlet
又要启动定时任务
celery -A celerys beat -l INFO

这也就是为什么生产环境下，需要两份配置文件。
"""
from celery.schedules import crontab
import datetime

beat_schedule = {
    'add-every-30-seconds': {
        'task': 'tasks.test',
        'schedule': 3.0,
        'args': (datetime.datetime.now(), "定时测试", "\n")
    }
}
"""
老方法不推荐
"""
# from tasks import test
# @app.on_after_configure.connect
# def setup_periodic_tasks(sender, **kwargs):
# 通过装饰器，每十秒调用一次
# sender.add_periodic_task(1, test.s("hallo"), name='work_beat')

# 每三十秒调用一次
# sender.add_periodic_task(30.0, test.s('world'), expires=10)

# 每隔一周，的7：30调用一次
# sender.add_periodic_task(
#     crontab(hour=7, minute=30, day_of_week=1),
#     test.s('Happy Mondays!'),
# )
