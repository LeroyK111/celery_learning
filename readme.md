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

您可以使用[`app.task()`](https://docs.celeryq.dev/en/stable/reference/celery.html#celery.Celery.task)装饰器轻松地从任何可调用项创建任务：

```
from .models import User

@app.task
def create_user(username, password):
    User.objects.create(username=username, password=password)
```

还可以为任务设置许多[选项](https://docs.celeryq.dev/en/stable/userguide/tasks.html#task-options)，这些可以指定为装饰器的参数：

```
@app.task(serializer='json')
def create_user(username, password):
    User.objects.create(username=username, password=password)
```

```
# django则可以使用shared_task
from celery import shared_task

@shared_task
def add(x, y):
    return x + y
```

```
# 多个装饰器时需要排最后一层
@app.task
@decorator2
@decorator1
def add(x, y):
    return x + y
```

```
# 绑定回调，可以使用self
@app.task(bind=True, default_retry_delay=30 * 60)  # 先设置三十分钟重试延迟
def add(self, x, y):
    try:
        something_raising()
    except Exception as exc:
        # 自定义重试延迟,覆盖设置为60s
        raise self.retry(exc=exc, countdown=60)
```

```
import celery
# 自定义Task
class MyTask(celery.Task):

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        print('{0!r} failed: {1!r}'.format(task_id, exc))

@app.task(base=MyTask)
def add(x, y):
    raise KeyError()
```

```
# 给任务加个名字
@app.task(name='sum-of-two-numbers')
def add(x, y):
    return x + y

>add.name
```

### ★调用任务

```
# 调用任务（链式调用）
add.apply_async((2, 2), link=add.s(16))

# 错误回调
@app.task
def error_handler(request, exc, traceback):
    print('Task {0} raised exception: {1!r}\n{2!r}'.format(
          request.id, exc, traceback))
可以使用link_error执行选项将其添加到任务中：
add.apply_async((2, 2), link_error=error_handler.s())
此外，link和link_error选项都可以表示为一个列表：
add.apply_async((2, 2), link=[add.s(16), other_task.s()])
然后将按顺序调用回调/错误返回，并且所有回调都将以父任务的返回值作为部分参数来调用。
```

```
# 使用延时时间
>>> result = add.apply_async((2, 2), countdown=3)
>>> result.get()    # this takes at least 3 seconds to return
20


# 设置一个延时时间
>>> from datetime import datetime, timedelta
>>> tomorrow = datetime.utcnow() + timedelta(days=1)
>>> add.apply_async((2, 2), eta=tomorrow)
```

```
# 任务过期
>>> # Task expires after one minute from now.
>>> add.apply_async((10, 10), expires=60)
# 任务过期时间
>>> # Also supports datetime
>>> from datetime import datetime, timedelta
>>> add.apply_async((10, 10), kwargs,
...                 expires=datetime.now() + timedelta(days=1)
```

```
# 行内写重试操作，也可以用上述的try进行错误捕捉重试
add.apply_async((2, 2), retry=True, retry_policy={
    'max_retries': 3,
    'interval_start': 0,
    'interval_step': 0.2,
    'interval_max': 0.2,
})
最大重试次数max_retries

放弃前的最大重试次数，在这种情况下，将引发导致重试失败的异常。

值None意味着它将永远重试。

默认为重试 3 次。

间隔开始interval_start

定义重试之间等待的秒数（浮点数或整数）。默认值为 0（第一次重试将是瞬时的）。

间隔步长interval_step

在每次连续重试时，此数字将被添加到重试延迟（浮点数或整数）中。默认值为 0.2。

间隔最大值interval_max

重试之间等待的最大秒数（浮点数或整数）。默认值为 0.2。
```

### 画布：设计工作流程

这里用的频率不高，建议看官方文档

```
# 使用签名
>>> from celery import signature
>>> signature('tasks.add', args=(2, 2), countdown=10)
tasks.add(2, 2)
# 签名可以覆盖
>>> s = add.signature((2, 2), countdown=10)
>>> s.apply_async(countdown=1)  # countdown is now 1
```

### 工人指南

涉及到集群部署方法。celery的集群架构

![image-20220405121605759](readme.assets/image-20220405121605759.png)https://docs.celeryq.dev/en/stable/userguide/workers.html

```
$ celery -A proj worker -l INFO
```

可以

```
$ celery worker --help
```

参数意义

--concurrency=10      启动10个线程          

-n worker1@%h         node的名字，worker1在守护进程中有讲解。%之后的字母时备注

```
$ celery -A proj worker --loglevel=INFO --concurrency=10 -n worker1@%h
$ celery -A proj worker --loglevel=INFO --concurrency=10 -n worker2@%h
$ celery -A proj worker --loglevel=INFO --concurrency=10 -n worker3@%h
```

这些值是为了更好的区分，节点的名字，并无意义。

> - `%h`: 域名
> - `%n`: 直接写名字
> - `%d`: 直接写后缀

例子

| Variable | Template     | Result                       |
| -------- | ------------ | ---------------------------- |
| `%h`     | `worker1@%h` | *worker1@george.example.com* |
| `%n`     | `worker1@%n` | *worker1@george*             |
| `%d`     | `worker1@%d` | *worker1@example.com*        |

### 守护进程

涉及到集群部署方法。

如何将celery可靠的运行在linux系统上

https://docs.celeryq.dev/en/stable/userguide/daemonizing.html#example-configuration

#### [初始化脚本：`celeryd`](https://docs.celeryq.dev/en/stable/userguide/daemonizing.html#id6)

- 用法

  /etc/init.d/celeryd {start|stop|restart|status}

- 配置文件

  `/etc/default/celeryd`

要配置此脚本以正确运行工作程序，您可能至少需要告诉它在启动时将目录更改到何处（以查找包含您的应用程序的模块或您的配置模块）。

守护进程脚本由文件配置`/etc/default/celeryd`。这是一个 shell ( **sh** ) 脚本，您可以在其中添加环境变量，如下面的配置选项。要添加影响工作人员的真实环境变量，您还必须导出它们（例如，**export DISPLAY=":0"**）

需要超级用户权限

init-scripts 只能由 root 使用，shell 配置文件也必须由 root 拥有。

非特权用户不需要使用 init-script，而是可以使用**celery multi**实用程序（或 **celery worker --detach**）：

multi不兼容win32

```
$ celery -A proj multi start worker1 \
    --pidfile="$HOME/run/celery/%n.pid" \
    --logfile="$HOME/log/celery/%n%I.log"

$ celery -A proj multi restart worker1 \
    --logfile="$HOME/log/celery/%n%I.log" \
    --pidfile="$HOME/run/celery/%n.pid

$ celery multi stopwait worker1 --pidfile="$HOME/run/celery/%n.pid"
```

#### [示例配置](https://docs.celeryq.dev/en/stable/userguide/daemonizing.html#id7)

这是 Python 项目的示例配置。

`/etc/default/celeryd`：

```
# 节点名字
CELERYD_NODES="worker1"
#   but you can also start multiple and configure settings
#   for each in CELERYD_OPTS
#CELERYD_NODES="worker1 worker2 worker3"
#   alternatively, you can specify the number of nodes to start:
#CELERYD_NODES=10

# 命令路径
CELERY_BIN="/usr/local/bin/celery"
#CELERY_BIN="/virtualenvs/def/bin/celery"

# 项目名称
CELERY_APP="proj"
# or fully qualified:
#CELERY_APP="proj.tasks:app"

# 启动进程
CELERYD_CHDIR="/opt/Myproject/"

# Extra command-line arguments to the worker
CELERYD_OPTS="--time-limit=300 --concurrency=8"
# Configure node-specific settings by appending node name to arguments:
#CELERYD_OPTS="--time-limit=300 -c 8 -c:worker2 4 -c:worker3 2 -Ofair:worker1"

# Set logging level to DEBUG
#CELERYD_LOG_LEVEL="DEBUG"

# %n will be replaced with the first part of the nodename.
CELERYD_LOG_FILE="/var/log/celery/%n%I.log"
CELERYD_PID_FILE="/var/run/celery/%n.pid"

# Workers should run as an unprivileged user.
#   You need to create this user manually (or you can choose
#   a user/group combination that already exists (e.g., nobody).
CELERYD_USER="celery"
CELERYD_GROUP="celery"

# If enabled pid and log directories will be created if missing,
# and owned by the userid/group configured.
CELERY_CREATE_DIRS=1
```

#### [使用登录外壳](https://docs.celeryq.dev/en/stable/userguide/daemonizing.html#id8)

`CELERYD_USER`您可以使用登录 shell继承环境：

```
CELERYD_SU_ARGS="-l"
```

请注意，不建议这样做，并且您应该仅在绝对必要时使用此选项。

定时脚本路径

#### [初始化脚本：`celerybeat`](https://docs.celeryq.dev/en/stable/userguide/daemonizing.html#id11)

- 用法

  /etc/init.d/celerybeat {start|stop|restart}

- 配置文件

  `/etc/default/celerybeat`或 `/etc/default/celeryd`。

#### [示例配置](https://docs.celeryq.dev/en/stable/userguide/daemonizing.html#id12)

这是 Python 项目的示例配置：

/etc/default/celerybeat：

```
# Absolute or relative path to the 'celery' command:
CELERY_BIN="/usr/local/bin/celery"
#CELERY_BIN="/virtualenvs/def/bin/celery"

# App instance to use
# comment out this line if you don't use an app
CELERY_APP="proj"
# or fully qualified:
#CELERY_APP="proj.tasks:app"

# Where to chdir at start.
CELERYBEAT_CHDIR="/opt/Myproject/"

# Extra arguments to celerybeat
CELERYBEAT_OPTS="--schedule=/var/run/celery/celerybeat-schedule"
```

### ★定期任务

#### 古老的定时方案（不推荐）

```
from celery import Celery
from celery.schedules import crontab

app = Celery()

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Calls test('hello') every 10 seconds.
    sender.add_periodic_task(10.0, test.s('hello'), name='add every 10')

    # Calls test('world') every 30 seconds
    sender.add_periodic_task(30.0, test.s('world'), expires=10)

    # Executes every Monday morning at 7:30 a.m.
    sender.add_periodic_task(
        crontab(hour=7, minute=30, day_of_week=1),
        test.s('Happy Mondays!'),
    )

@app.task
def test(arg):
    print(arg)

@app.task
def add(x, y):
    z = x + y
    print(z)
```

#### 普通的定时方案

```
app.conf.beat_schedule = {
    'add-every-30-seconds': {
        'task': 'tasks.add',
        'schedule': 30.0,
        'args': (16, 16)
    },
}
```

- task

  > 任务名

- schedule

  > 可以输入具体日期时间or默认秒

- args

  > 传入元组参数

- kwargs

  > 传入字典参数

- options

  >  [`apply_async()`](https://docs.celeryq.dev/en/stable/reference/celery.app.task.html#celery.app.task.Task.apply_async) 的字典参数

- relative

  > 设置频率，使用次数

#### [crontab 时间表](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html#id5)

如果您想更好地控制任务的执行时间，例如，一天中的特定时间或一周中的某一天，您可以使用[`crontab`](https://docs.celeryq.dev/en/stable/reference/celery.schedules.html#celery.schedules.crontab)schedule 类型：

```
from celery.schedules import crontab

app.conf.beat_schedule = {
    # Executes every Monday morning at 7:30 a.m.
    'add-every-monday-morning': {
        'task': 'tasks.add',
        'schedule': crontab(hour=7, minute=30, day_of_week=1),
        'args': (16, 16),
    },
}
```

这些 Crontab 表达式的语法非常灵活。

一些例子：

| **例子**                                                     | **意义**                                                     |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| `crontab()`                                                  | 每分钟执行一次。                                             |
| `crontab(minute=0, hour=0)`                                  | 每天午夜执行。                                               |
| `crontab(minute=0, hour='*/3')`                              | 每三个小时执行一次：午夜、凌晨 3 点、早上 6 点、早上 9 点、中午、下午 3 点、下午 6 点、晚上 9 点。 |
| `crontab(minute=0,``hour='0,3,6,9,12,15,18,21')`             | 和以前一样。                                                 |
| `crontab(minute='*/15')`                                     | 每 15 分钟执行一次。                                         |
| `crontab(day_of_week='sunday')`                              | 在星期日每分钟 (!) 执行一次。                                |
| `crontab(minute='*',``hour='*',` `day_of_week='sun')`        | 和以前一样。                                                 |
| `crontab(minute='*/10',``hour='3,17,22',` `day_of_week='thu,fri')` | 每十分钟执行一次，但仅在周四或周五的凌晨 3-4 点、下午 5-6 点和晚上 10-11 点之间执行。 |
| `crontab(minute=0, hour='*/2,*/3')`                          | 每隔偶数小时执行一次，并且每小时可以被三整除。这意味着：每个小时，*除了*：上午 1 点、上午 5 点、上午 7 点、上午 11 点、下午 1 点、下午 5 点、晚上 7 点、晚上 11 点 |
| `crontab(minute=0, hour='*/5')`                              | 执行小时可被 5 整除。这意味着它在下午 3 点触发，而不是下午 5 点（因为下午 3 点等于 24 小时制时钟值“15”，可被 5 整除）。 |
| `crontab(minute=0, hour='*/3,8-17')`                         | 每小时执行一次，可被 3 整除，并在办公时间（上午 8 点至下午 5 点）每小时执行一次。 |
| `crontab(0, 0, day_of_month='2')`                            | 每个月的第二天执行。                                         |
| `crontab(0, 0,``day_of_month='2-30/2')`                      | 在每个偶数日执行。                                           |
| `crontab(0, 0,``day_of_month='1-7,15-21')`                   | 在每月的第一周和第三周执行。                                 |
| `crontab(0, 0, day_of_month='11',``month_of_year='5')`       | 每年 5 月 11 日执行。                                        |
| `crontab(0, 0,``month_of_year='*/3')`                        | 在每个季度的第一个月每天执行。                               |

#### 根据太阳和经纬度来定时

```
from celery.schedules import solar
# 太阳能时间表
app.conf.beat_schedule = {
    # Executes at sunset in Melbourne
    'add-at-melbourne-sunset': {
        'task': 'tasks.add',
        'schedule': solar('sunset', -37.81753, 144.96715),
        'args': (16, 16),
    },
}
```

论据很简单：`solar(event, latitude, longitude)`

确保使用正确的纬度和经度符号：

| **标志** | **争论**    | **意义** |
| -------- | ----------- | -------- |
| `+`      | `latitude`  | 北       |
| `-`      | `latitude`  | 南       |
| `+`      | `longitude` | 东方     |
| `-`      | `longitude` | 西       |

可能的事件类型有：

| **事件**            | **意义**                                                     |
| ------------------- | ------------------------------------------------------------ |
| `dawn_astronomical` | 在天空不再完全黑暗的那一刻执行。这是太阳在地平线以下18度的时候。 |
| `dawn_nautical`     | 当地平线有足够的阳光和一些物体可以区分时执行；正式地，当太阳在地平线以下 12 度时。 |
| `dawn_civil`        | 当有足够的光线可以区分物体时执行，以便可以开始户外活动；正式地，当太阳在地平线以下 6 度时。 |
| `sunrise`           | 当早晨太阳的上边缘出现在东方地平线上时执行。                 |
| `solar_noon`        | 当天太阳在地平线以上最高时执行。                             |
| `sunset`            | 当晚上太阳的后缘消失在西方地平线上时执行。                   |
| `dusk_civil`        | 在公民暮光之城结束时执行，此时物体仍然可以区分并且一些恒星和行星是可见的。正式地，当太阳低于地平线 6 度时。 |
| `dusk_nautical`     | 在太阳低于地平线 12 度时执行。物体不再可分辨，地平线不再是肉眼可见的。 |
| `dusk_astronomical` | 在天空完全变暗的那一刻执行；正式地，当太阳在地平线以下 18 度时。 |



#### [启动定期任务的指令](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html#id7)

★启动定时任务时，必须先启动worker，不然定时任务没人干活

```
$ celery -A proj worker -l info -P eventlet
```

启动**celery beat**服务(需要配置*celerybeat*文件)：

```
$ celery -A proj beat
```

您还可以通过启用workers选项将beat[`-B`](https://docs.celeryq.dev/en/stable/reference/cli.html#cmdoption-celery-worker-B)嵌入worker中，如果您永远不会运行多个worker节点，这很方便，但它不常用，因此不建议用于生产：

```
$ celery -A proj worker -B
```

Beat 需要将任务的最后运行时间存储在本地数据库文件（默认命名为celerybeat-schedule）中，因此它需要访问当前目录的写入权限，或者您可以为该文件指定自定义位置：

```
$ celery -A proj beat -s /home/celery/var/run/celerybeat-schedule
```

#### [使用自定义调度器类](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html#id8)

可以在命令行（ [`--scheduler`](https://docs.celeryq.dev/en/stable/reference/cli.html#cmdoption-celery-beat-S)参数）上指定自定义调度程序类。

默认调度程序是，它只是在本地 数据库文件[`celery.beat.PersistentScheduler`](https://docs.celeryq.dev/en/stable/reference/celery.beat.html#celery.beat.PersistentScheduler)中跟踪上次运行时间。[`shelve`](https://docs.python.org/dev/library/shelve.html#module-shelve)

还有一个[django-celery-beat](https://pypi.python.org/pypi/django-celery-beat/)扩展，它将计划存储在 Django 数据库中，并提供了一个方便的管理界面来在运行时管理周期性任务。

要安装和使用此扩展程序：

1. 使用**pip**安装包：

   > ```
   > $ pip install django-celery-beat
   > ```

2. 将`django_celery_beat`模块添加到`INSTALLED_APPS`您的 Django 项目中' `settings.py`：

   ```
   INSTALLED_APPS = (
       ...,
       'django_celery_beat',
   )
   ```

   请注意，模块名称中没有破折号，只有下划线。

3. 应用 Django 数据库迁移，以便创建必要的表：

   > ```
   > $ python manage.py migrate
   > ```

4. 使用调度程序启动**celery beat**服务：`django_celery_beat.schedulers:DatabaseScheduler`

   > ```
   > $ celery -A proj beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler
   > ```

   注意：您也可以[`beat_scheduler`](https://docs.celeryq.dev/en/stable/userguide/configuration.html#std-setting-beat_scheduler)直接将其添加为设置。

5. 访问 Django-Admin 界面以设置一些周期性任务。

### 路由任务

官方推荐使用AMQP的路由模式（exchange交换机+queue队列）

https://docs.celeryq.dev/en/stable/userguide/routing.html#redis-message-priorities

### 监控和管理指南



```
# 节点装饰器
$ pip install flower
运行花命令将启动您可以访问的网络服务器：

$ celery -A proj flower
默认端口是http://localhost:5555，但您可以使用 –port参数更改它：

$ celery -A proj flower --port=5555
Broker URL 也可以通过 --broker参数传递：

$ celery flower --broker=amqp://guest:guest@localhost:5672//
or
$ celery flower --broker=redis://guest:guest@localhost:6379/0
然后，您可以在 Web 浏览器中访问 Flower：

$ open http://localhost:5555
Flower 具有比此处详述的更多功能，包括授权选项。查看官方文档了解更多信息。
```

### 安全

消息签名（一般不用）

https://docs.celeryq.dev/en/stable/userguide/security.html

### 优化

![image-20220405181053078](readme.assets/image-20220405181053078.png)

```
celeryconfig.py文件，开启消息确认
task_acks_late = True
他真正的意思是让工作人员只保留与工作进程一样多的任务（-c 10正在执行的任务 + 10个保留的任务）
worker_prefetch_multiplier = 1
```

### 调试

帮助开发者学习。

https://docs.celeryq.dev/en/stable/userguide/debugging.html

### 并发



```
使用celery本身进行并发操作
>celery -A proj worker -c 1000

使用eventlet库进行线程并发
>pip install eventlet
>celery -A proj worker -P eventlet -c 1000
```

### ★信号

跟rabbitMQ一样，celery也是全流程的解耦，消息的传递，任务的处理都可以拆分出来。

https://docs.celeryq.dev/en/stable/userguide/signals.html

基本用法

![image-20220405183133132](readme.assets/image-20220405183133132.png)

```
任务信号(常用来细化任务)

before_task_publish 在发布任务之前调度。与after_task_publish冲突，且after_task_publish级别高

after_task_publish  在将任务发送到代理时调度。

task_prerun         在执行任务之前调度。

task_postrun        在执行任务后调度。

task_retry          在重试任务时调度。(捕捉异常时用)

task_success        任务成功时调度。(可以异步获取结果return)

task_failure        任务失败时调度。

task_internal_error 在执行任务时发生内部 Celery 错误时调度。

task_received       当从代理接收到任务并准备好执行时调度。(worker接到任务时的对象)

task_revoked        当工作人员撤销/终止任务时调度。（queue->MQ->worker，某个环节被终止则触发）

task_unknown        当工作人员收到未注册任务的消息时调度。（自定义消费者）

task_rejected       当工作人员收到到其任务队列之一的未知类型的消息时调度。(自定义消费者)

应用信号

import_modules 当程序（worker、beat、shell）等请求导入include和imports 设置中的模块时，会发送此信号。

工人信号

celeryd_after_setup   设置队列

celeryd_init          这是celery worker启动时发送的第一个信号。设置 worker 特定的配置

worker_init           在工人启动之前调度。

worker_ready          当工人准备好接受工作时调度。

heartbeat_sent         当 Celery 发送工作人员心跳时调度。

worker_shutting_down     当工作人员开始关闭过程时调度。

worker_process_init      启动时在所有池子进程中调度。

worker_process_shutdown   就在它们退出之前在所有池子进程中调度。

worker_shutdown        当工人即将关闭时调度。

节拍信号

beat_init            在celery beat开始时调度

beat_embedded_init   当celery beat作为嵌入式进程启动时，除了发送beat_init信号外还调度。

小事件信号（eventlet线程池）

eventlet_pool_started        当 eventlet 池启动时发送。

eventlet_pool_preshutdown    当工作人员关闭时发送，就在请求事件池等待剩余工作人员之前。

eventlet_pool_postshutdown    当池已加入并且工作人员准备关闭时发送。

eventlet_pool_apply           每当将任务应用于池时发送。

记录信号(不推荐使用这里覆盖celery.config)

setup_logging     如果连接了此信号，Celery 将不会配置记录器，因此您可以使用它来完全覆盖您自己的记录配置。

after_setup_logger  在设置每个全局记录器（不是任务记录器）之后发送。用于扩充日志记录配置。

after_setup_task_logger   在设置每个任务记录器后发送。用于扩充日志记录配置。

命令信号(自定义命令)

user_preload_options   这个信号在任何 Celery 命令行程序完成解析用户预加载选项后发送。

```

### 用celery测试

https://docs.celeryq.dev/en/stable/userguide/testing.html

```
# 除了常规测试外，还有一个集成了pytest框架的celery插件
pip install pytest-celery
```

### 扩展和引导

记录了详细的celery的流程，二次开发需要这里。

https://docs.celeryq.dev/en/stable/userguide/extending.html#installing-bootsteps

![../_images/worker_graph_full.png](readme.assets/worker_graph_full.png)

Kombu 消息传递模块

Bootsteps

click8 组合式sheel

### 配置和默认值

/etc/default/celeryd					工作队列配置文件目录

/etc/default/celerybeat				定时队列配置目录

【两个配置文件】https://docs.celeryq.dev/en/stable/userguide/daemonizing.html

【配置文件的参数】https://docs.celeryq.dev/en/stable/userguide/configuration.html#std-setting-beat_schedule

### 使用 Sphinx 库，记录任务

https://docs.celeryq.dev/en/stable/userguide/sphinx.html

```
pip install Sphinx
```

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
