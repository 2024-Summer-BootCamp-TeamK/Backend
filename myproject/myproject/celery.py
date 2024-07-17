from __future__ import absolute_import, unicode_literals
from celery import Celery
# Django 프로젝트 설정을 위한 설정
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

app = Celery('myproject')

# Celery 설정을 Django 설정에서 불러옴
app.config_from_object('django.conf:settings', namespace='CELERY')

# Django 앱에서 task를 자동으로 발견
app.autodiscover_tasks()

#
# # celery.py 파일
# import logging
#
# # 기본 로그 설정
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
#
# # 콘솔 핸들러 설정
# console_handler = logging.StreamHandler()
# console_handler.setLevel(logging.DEBUG)
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# console_handler.setFormatter(formatter)
# logger.addHandler(console_handler)

