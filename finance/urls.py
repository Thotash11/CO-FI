from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('login/', RedirectView.as_view(pattern_name='dashboard', permanent=False), name='login'),
    path('logout/', RedirectView.as_view(pattern_name='dashboard', permanent=False), name='logout'),
    path('', views.dashboard_view, name='dashboard'),
    path('transactions/', views.transaction_list, name='transactions'),
    path('transactions/create/', views.transaction_create, name='transaction_create'),
    path('transactions/<int:pk>/update/', views.transaction_update, name='transaction_update'),
    path('transactions/<int:pk>/delete/', views.transaction_delete, name='transaction_delete'),
    path('reports/', views.reports_view, name='reports'),
    path('export/transactions/', views.export_transactions_csv, name='export_transactions'),
    path('export/reports/', views.export_reports_csv, name='export_reports'),
    
    path('unit-buyers/', views.unit_buyer_list, name='unit_buyers'),
    path('unit-buyers/add/', views.unit_buyer_create, name='unit_buyer_create'),
    path('unit-buyers/<int:pk>/', views.unit_buyer_detail, name='unit_buyer_detail'),
    path('unit-buyers/<int:pk>/add-transaction/', views.unit_buyer_add_transaction, name='unit_buyer_add_transaction'),
    path('unit-buyers/<int:pk>/edit/', views.unit_buyer_update, name='unit_buyer_update'),
    path('unit-buyers/<int:pk>/delete/', views.unit_buyer_delete, name='unit_buyer_delete'),
    path('unit-buyer-transaction/<int:pk>/edit/', views.unit_buyer_transaction_update, name='unit_buyer_transaction_update'),
    path('unit-buyer-transaction/<int:pk>/delete/', views.unit_buyer_transaction_delete, name='unit_buyer_transaction_delete'),
]
