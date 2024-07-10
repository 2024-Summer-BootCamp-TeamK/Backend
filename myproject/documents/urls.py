from django.urls import path
from .views import DocumentUploadView, DocumentRead, DocumentAccessView

urlpatterns = [
    # document 업로드 api
    path('documents/', DocumentUploadView.as_view(), name='document_upload'),
    path('documents/<int:documentId>', DocumentRead.as_view(), name='document_read'),
    path('document/<int:documentId>/change/', DocumentChange().as_view(), name='document_change'),
    path('documents/<int:documentId>/access', DocumentAccessView.as_view(), name='document_access')
]