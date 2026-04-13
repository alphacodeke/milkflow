from django.urls import path
from . import views

urlpatterns = [
    # Landing & Auth
    path('', views.landing, name='landing'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Farm
    path('farm/', views.farm_profile, name='farm_profile'),

    # Cows
    path('cows/', views.cow_list, name='cow_list'),
    path('cows/add/', views.cow_add, name='cow_add'),
    path('cows/<int:pk>/', views.cow_detail, name='cow_detail'),
    path('cows/<int:pk>/edit/', views.cow_edit, name='cow_edit'),
    path('cows/<int:pk>/delete/', views.cow_delete, name='cow_delete'),

    # Milk Records
    path('milk/', views.milk_list, name='milk_list'),
    path('milk/add/', views.milk_add, name='milk_add'),
    path('milk/<int:pk>/edit/', views.milk_edit, name='milk_edit'),
    path('milk/<int:pk>/delete/', views.milk_delete, name='milk_delete'),

    # Finances
    path('finances/', views.finance_list, name='finance_list'),
    path('finances/add/', views.finance_add, name='finance_add'),
    path('finances/<int:pk>/delete/', views.finance_delete, name='finance_delete'),

    # Health
    path('health/', views.health_list, name='health_list'),
    path('health/add/', views.health_add, name='health_add'),
    path('health/<int:pk>/edit/', views.health_edit, name='health_edit'),
    path('health/<int:pk>/delete/', views.health_delete, name='health_delete'),

    # Tasks
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/add/', views.task_add, name='task_add'),
    path('tasks/<int:pk>/edit/', views.task_edit, name='task_edit'),
    path('tasks/<int:pk>/complete/', views.task_complete, name='task_complete'),
    path('tasks/<int:pk>/delete/', views.task_delete, name='task_delete'),

    # Employees
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/add/', views.employee_add, name='employee_add'),
    path('employees/<int:pk>/edit/', views.employee_edit, name='employee_edit'),
    path('employees/<int:pk>/delete/', views.employee_delete, name='employee_delete'),

    # Reports
    path('reports/', views.reports, name='reports'),
    path('reports/milk/pdf/', views.report_milk_pdf, name='report_milk_pdf'),
    path('reports/milk/csv/', views.report_milk_csv, name='report_milk_csv'),
    path('reports/finance/pdf/', views.report_finance_pdf, name='report_finance_pdf'),
    path('reports/finance/csv/', views.report_finance_csv, name='report_finance_csv'),
    path('reports/health/pdf/', views.report_health_pdf, name='report_health_pdf'),

    # API
    path('api/milk/trend/', views.api_milk_trend, name='api_milk_trend'),
]
