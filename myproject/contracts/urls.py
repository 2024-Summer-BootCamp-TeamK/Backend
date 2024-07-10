from django.urls import path
from .modify_views import ContractModifyView, UpdatedContractRead


urlpatterns = [
    path('api/v1/contracts/<int:contractId>', ContractModifyView.as_view(), name='contract_modify'),
    path('api/v1/contracts/<int:contractId>/result', UpdatedContractRead.as_view(), name='get_modified_contract'),
]