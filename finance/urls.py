from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='finance/login.html', redirect_authenticated_user=True), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
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
