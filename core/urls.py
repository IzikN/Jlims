# core/urls.py

from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    path('batch/create/', views.create_batch, name='create_batch'),
    path('worksheet/create/', views.create_worksheet, name='create_worksheet'),
    path('equipment/log/', views.log_equipment_use, name='log_equipment_use'),
    path('coa/<int:client_id>/', views.view_coa, name='view_coa'),
    path('assign-test/<str:sample_id>/', views.assign_test, name='assign_test'),
    path('dashboard/manager/', views.manager_dashboard, name='manager_dashboard'),
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),
    path('test-request/', views.create_test_request, name='create_test_request'),
    path('assignment/<int:assignment_id>/submit/', views.submit_result, name='submit_result'),
    path('dashboard/cs/', views.cs_dashboard, name='cs_dashboard'),
    path('dashboard/analyst/', views.analyst_dashboard, name='analyst_dashboard'),

]

