from django.urls import path
from .views import DocumentUploadView, DocumentView, DocumentAccessView
from .encryptionView import DocumentEncryptionUploadView
urlpatterns = [
    # document 업로드 api
    path('documents/', DocumentUploadView.as_view(), name='document_upload'),
    path('documents/<int:documentId>', DocumentView.as_view(), name='document_read'),
    path('documents/<int:documentId>/access', DocumentAccessView.as_view(), name='document_access'),
    path('encryption/test', DocumentEncryptionUploadView.as_view(), name='encryption_file_test')
] 