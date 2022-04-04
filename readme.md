# celery分布式任务队列

官方网站地址：https://docs.celeryproject.org/

## 1.选择适合的消息中间件

[RabbitMQ](http://www.rabbitmq.com/)

对python而言比较友好的消息中间件。也是celery官方推荐的中间件。

两种安装方式，记得开放端口。

```
sudo apt-get install rabbitmq-server
docker run -d -p 5672:5672 rabbitmq
```

redis(https://redis.io/)

安装方式

```
sudo apt-get install redis
docker run -d -p 6379:6379 redis
```

## 2.简单用法

安装celery

```
pip install celery
```

这里我们采用redis作为celery的消息中间件。

```
文件结构:
proj/
	/main.py
	/celeryconfig.py
    /tasks.py
    /celerys.py
```

```
celery常用指令
celery worker --help
(multi命令不支持win32，仅支持macOS和linux)
celery multi start w1 -A proj -l INFO
celery  multi restart w1 -A proj -l INFO
celery multi stop w1 -A proj -l INFO
celery multi stopwait w1 -A proj -l INFO

通常日志文件会默认放在当前目录下
celery multi start w1 -A proj -l INFO --pidfile=/var/run/celery/%n.pid \
--logfile=/var/log/celery/%n%I.log

启动多个Queue 工作队列
celery multi start 10 -A proj -l INFO -Q:1-3 images,video -Q:4,5 data \
-Q default -L:4,5 debug

RabbitMQ (AMQP)、Redis 或 Qpid 作为代理,可以在运行时控制和检查工作程序
celery -A proj inspect active

可以使用该--destination选项指定一个或多个工作人员来处理请求。这是工作程序主机名的逗号分隔列表：
celery -A proj inspect active --destination=celery@example.com

celery inspect命令包含不会改变工作进程中任何内容的命令；它只返回有关工作人员内部发生的事情的信息和统计信息。对于可以执行的检查命令列表：

$ celery -A proj inspect --help
然后是celery 控制命令，其中包含在运行时实际更改工作器中的内容的命令：

$ celery -A proj control --help
例如，您可以强制工作人员启用事件消息（用于监视任务和工作人员）：

$ celery -A proj control enable_events
启用事件后，您可以启动事件转储程序以查看工作人员在做什么：

$ celery -A proj events --dump
或者你可以启动 curses 界面：

$ celery -A proj events
完成监视后，您可以再次禁用事件：

$ celery -A proj control disable_events
celery status命令还使用远程控制命令，并显示集群中的在线工作者列表：

$ celery -A proj status
```

## 2.1高级用法

### ★应用

1.内置面向对象的方法

2.自写task方法

```
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
```

### ★任务







异步操作必须设置超时

![image-20220405030741048](readme.assets/image-20220405030741048.png)

### 调用任务



### 画布：设计工作流程



### 工人指南



### 守护进程



### 定期任务



### 路由任务



### 监控和管理指南



### 安全



### 优化



### 调试



### 并发



### ★信号



### 用celery测试



### 扩展和引导



### 配置和默认值



### 使用 Sphinx 记录任务



## 3.django用法

```
Django目录如下:
- proj/
  - manage.py
  - app1/
    - tasks.py
    - models.py
  - app2/
    - tasks.py
    - models.py
  - proj/
    - __init__.py
    - settings.py
    - urls.py
    - celery.py
```

```
#!proj/proj/celery.py
import os

from celery import Celery

# 导入django的配置参数
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proj.settings')

app = Celery('proj')

# 从setting文件中读取以CELERY开头的老参数配置文件
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现django的app.tasks
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
```

```
#!proj/proj/__init__.py

# 初始化配置文件
from .celery import app as celery_app

__all__ = ('celery_app',)
```

```
#!proj/proj/setting.py

# 这里是老参数了，推荐使用proj/proj/celeryconfig.py用新参数配置
CELERY_TIMEZONE = "Australia/Tasmania"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
```

如果要使用django的ORM操作方式，还得下个库

```
pip install django-celery-results
```

```
#!proj/proj/setting.py
# 注册app

INSTALLED_APPS = (
    ...,
    'django_celery_results',
)


# 结果后端
CELERY_RESULT_BACKEND = 'django-db'
# 缓存后端
CELERY_CACHE_BACKEND = 'django-cache'
# 使用默认（json）
# CELERY_CACHE_BACKEND = 'default'

# 缓存配置(推荐redis)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'my_cache_table',
    }
}
```

```
# 生成对应的表
python manage.py migrate django_celery_results
```

django celery配置完毕！

## 4.flask用法

[**Flask-Celery**](https://pypi.org/project/Flask-Celery/)

该包已经不适用，推荐自写（上述普通和高级用法）即可。

## 5.其他用法（待补充）

dash：

FastAPI：

tornado：
