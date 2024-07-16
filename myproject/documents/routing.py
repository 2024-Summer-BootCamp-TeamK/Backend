# documents/routing.py

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/documents/(?P<document_id>\d+)/$', consumers.DocumentConsumer.as_asgi()),
]
