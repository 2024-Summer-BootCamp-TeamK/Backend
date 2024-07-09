from django.urls import path
from .uploadviews import uploadView

urlpatterns = [
    path('api/vi/contracts', uploadView.as_view(), name='upload'),
]