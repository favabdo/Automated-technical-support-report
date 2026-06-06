from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports_list, name='reports_list'),
    path('agents/', views.agents_list, name='agents_list'),
    path('agents/<int:agent_id>/', views.agent_detail, name='agent_detail'),
    path('customers/', views.customers_list, name='customers_list'),
    path('customers/<int:customer_id>/', views.customer_detail, name='customer_detail'),
    path('monthly/', views.monthly, name='monthly'),
]
