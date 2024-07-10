from django.urls import path
from .modifyViews import ContractModifyView, UpdatedContractReadView
from .checkViews import UploadView, ContractDetailView


urlpatterns = [
    path('contracts/<int:contractId>', ContractModifyView.as_view(), name='contract_modify'),
    path('contracts/<int:contractId>/result', UpdatedContractReadView.as_view(), name='get_modified_contract'),
    path('contracts', UploadView.as_view(), name='upload'),
    path('contracts/<int:contractId>/test', ContractDetailView.as_view(), name='check_contract'),
]