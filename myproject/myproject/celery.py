from __future__ import absolute_import, unicode_literals
from celery import Celery
from django.conf import settings
from celery.schedules import crontab
import sys
from kombu.utils import encoding
sys.modules['celery.utils.encoding'] = encoding
# Django 프로젝트 설정을 위한 설정
import os, django
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

app = Celery('myproject')

# Celery 설정을 Django 설정에서 불러옴
app.config_from_object('django.conf:settings', namespace='CELERY')

# Django 앱에서 task를 자동으로 발견
app.autodiscover_tasks()

app.conf.update(
    CELERY_TASK_SERIALIZER='json',
    CELERY_ACCEPT_CONTENT=['json'],
    CELERY_RESULT_SERIALIZER='json',
    CELERY_TIMEZONE='Asia/Seoul',
    CELERY_ENABLE_UTC=False,
    CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler',
)

django.setup()

if __name__ == '__main__':
    app.start()


