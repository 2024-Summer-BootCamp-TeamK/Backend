from django.urls import path
from .views import DocumentUploadView, DocumentReadView, DocumentAccessView, DocumentChangeView

urlpatterns = [
    # document 업로드 api
    path('documents/', DocumentUploadView.as_view(), name='document_upload'),
    path('documents/<int:documentId>', DocumentReadView.as_view(), name='document_read'),
    path('documents/<int:documentId>/change', DocumentChangeView.as_view(), name='document_change'),
    path('documents/<int:documentId>/access', DocumentAccessView.as_view(), name='document_access')
] 