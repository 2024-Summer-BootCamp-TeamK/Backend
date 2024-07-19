from django.urls import path
from .views import DocumentUploadView, DocumentView, DocumentAccessView, TestDownloadPDFView
urlpatterns = [
    # document 업로드 api
    path('documents/', DocumentUploadView.as_view(), name='document_upload'),
    path('documents/<int:documentId>', DocumentView.as_view(), name='document_read'),
    path('documents/<int:documentId>/access', DocumentAccessView.as_view(), name='document_access'),
    path('testPDF', TestDownloadPDFView.as_view(), name='test')
] 