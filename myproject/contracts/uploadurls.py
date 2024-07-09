from django.urls import path
from .uploadviews import uploadView

urlpatterns = [
    path('api/v1/contracts', uploadView.as_view(), name='upload'),
]