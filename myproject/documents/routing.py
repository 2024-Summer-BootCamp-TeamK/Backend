# documents/routing.py

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path('ws/documents/<int:documentId>/', consumers.DocumentConsumer.as_asgi()),
]
