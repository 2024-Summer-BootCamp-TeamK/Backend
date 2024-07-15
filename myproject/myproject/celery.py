from __future__ import absolute_import, unicode_literals
from celery import Celery
from django.conf import settings
from celery.schedules import crontab

# Django 프로젝트 설정을 위한 설정
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

app = Celery('myproject')

# Celery 설정을 Django 설정에서 불러옴
app.config_from_object('django.conf:settings', namespace='CELERY')

# Django 앱에서 task를 자동으로 발견
# lambda 함수를 통해 Django 설정에서 설치된 모든 앱을 가져와
# 각 앱의 작업을 실행할 수 있도록 작업을 찾음
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.beat_schedule = {
    'delete_expired_files': {
        'task': 'myproject.tasks.delete_expired_file',
        'schedule': crontab(hour=0),
    },
}
