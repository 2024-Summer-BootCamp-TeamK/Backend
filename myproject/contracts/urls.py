from django.urls import path
from .modify_views import ContractModifyView


urlpatterns = [
    path('api/v1/contracts/<int:contractId>', ContractModifyView.as_view(), name='contract_modify'),
]