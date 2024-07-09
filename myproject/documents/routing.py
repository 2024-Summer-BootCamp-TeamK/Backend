from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/documents/<str:document_id>/', consumers.DocumentConsumer.as_asgi()),
]
