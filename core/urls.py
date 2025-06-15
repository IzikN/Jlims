# core/urls.py

from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from core.views import statistics_dashboard

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),
    path('worksheets/<int:pk>/', views.worksheet_detail, name='worksheet_detail'),
    path('worksheet/<int:worksheet_id>/entry/', views.worksheet_entry, name='worksheet_entry'),
    path('worksheet/<int:worksheet_id>/pdf/', views.worksheet_pdf, name='worksheet_pdf'),
    path('batch/<int:batch_id>/', views.batch_detail, name='batch_detail'),
    path('batches/create/', views.create_batch, name='create_batch'),
    path('batches/list/', views.batch_list, name='batch_list'),
    path('worksheet/create/', views.create_worksheet, name='create_worksheet'),
    path('worksheet/list/', views.worksheet_list, name='worksheet_list'),
    path('equipment/log/', views.log_equipment_use, name='log_equipment_use'),
    path('coa/<int:client_id>/', views.view_coa, name='view_coa'),
    path('assign-test/<str:sample_id>/', views.assign_test, name='assign_test'),
    path('dashboard/manager/', views.manager_dashboard, name='manager_dashboard'),
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),
    path('test-request/', views.create_test_request, name='create_test_request'),
    path('assignment/<int:assignment_id>/submit/', views.submit_result, name='submit_result'),
    path('dashboard/cs/', views.cs_dashboard, name='cs_dashboard'),
    path('dashboard/analyst/', views.analyst_dashboard, name='analyst_dashboard'),
    path('api/test-parameters/', views.api_get_test_parameters, name='api_get_test_parameters'),
    path('ajax/load-samples/', views.load_samples, name='load_samples'),
    path('ajax/get-samples/', views.get_samples_for_parameter, name='ajax_get_samples'),
    path('results/<str:token>/', views.view_client_results, name='client_results'),

    path('dashboard/manager/statistics/', statistics_dashboard, name='statistics_dashboard'),





]

