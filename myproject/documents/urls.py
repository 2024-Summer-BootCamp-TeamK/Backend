from django.urls import path
from .views import DocumentUploadView, DocumentRead, DocumentChange

urlpatterns = [
    # document 업로드 api
    path('api/v1/documents/', DocumentUploadView.as_view(), name='document_upload'),
    path('document/<int:documentId>', DocumentRead.as_view(), name='document_read'),
    path('document/<int:documentId>/change/', DocumentChange().as_view(), name='document_change'),
]