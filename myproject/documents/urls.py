from django.urls import path
from .views import DocumentUploadView

urlpatterns = [
    # document 업로드 api
    path('api/v1/documents/', DocumentUploadView.as_view(), name='document_upload')
]