from __future__ import absolute_import, unicode_literals
from celery import Celery

# Django 프로젝트 설정을 위한 설정
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

app = Celery('myproject')

# Celery 설정을 Django 설정에서 불러오기
app.config_from_object('django.conf:settings', namespace='CELERY')

# Django 앱에서 task를 자동으로 발견하기
app.autodiscover_tasks()
