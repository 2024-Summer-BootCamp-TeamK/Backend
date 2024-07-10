from django.urls import path
from .uploadviews import UploadView, ContractDetailView

urlpatterns = [
    path('api/v1/contracts', UploadView.as_view(), name='upload'),
    path('api/v1/contracts/<int:contractId>', ContractDetailView.as_view(), name='upload'),
]