from django.urls import path
from .modifyViews import ContractModifyView, UpdatedContractReadView
from .checkViews import UploadView, ContractMainView, ContractToxinView
from .statusViews import TaskStatusView


urlpatterns = [
    path('contracts/<int:contractId>', ContractModifyView.as_view(), name='contract_modify'),
    path('contracts/<int:contractId>/result', UpdatedContractReadView.as_view(), name='get_modified_contract'),
    path('contracts', UploadView.as_view(), name='upload'),
    path('contracts/<int:contractId>/main', ContractMainView.as_view(), name='check_contract_main'),
    path('contracts/<int:contractId>/toxin', ContractToxinView.as_view(), name='check_contract_toxin'),
    path('task_status/<str:task_id>', TaskStatusView.as_view(), name='task_status'),
]