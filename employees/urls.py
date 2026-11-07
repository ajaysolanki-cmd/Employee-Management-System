from django.urls import path
from . import views

urlpatterns = [
path('', views.home, name='home'),
path('employees/', views.employee_list, name='employee_list'),
path('profile/', views.profile, name='profile'),
path('employees/add/', views.add_employee, name='add_employee'),
path('employees/model-form/', views.add_employee, name='add_employee_model_form'),
path('employees/edit/<int:id>/', views.edit_employee, name='edit_employee'),
path('employees/delete/<int:id>/', views.delete_employee, name='delete_employee'),
path('api/employees/', views.employee_api, name='employee_api'),
path('employees/<int:id>/',views.employee_detail,name='employee_detail'),
path('departments/', views.department_list, name='department_list'),
path('departments/add/', views.add_department, name='add_department'),
path(
    'setup-roles/',
    views.setup_user_roles,
    name='setup_user_roles'
),
path(
    'notifications/',
    views.notification_list,
    name='notification_list'
),

path(
    'notifications/<int:id>/read/',
    views.mark_notification_read,
    name='mark_notification_read'
),

path(
    'notifications/read-all/',
    views.mark_all_notifications_read,
    name='mark_all_notifications_read'
),
path(
    'performance/summary/',
    views.performance_summary,
    name='performance_summary'
),

path(
    'performance/employee/<int:id>/',
    views.employee_performance_history,
    name='employee_performance_history'
),
path(
    'performance/',
    views.performance_list,
    name='performance_list'
),

path(
    'performance/add/',
    views.add_performance,
    name='add_performance'
),
path(
    'leaves/',
    views.leave_list,
    name='leave_list'
),

path(
    'leaves/apply/',
    views.apply_leave,
    name='apply_leave'
),

path(
    'leaves/<int:id>/update/<str:status>/',
    views.update_leave_status,
    name='update_leave_status'
),
path(
    'attendance/',
    views.attendance_list,
    name='attendance_list'
),

path(
    'attendance/mark/',
    views.mark_attendance,
    name='mark_attendance'
),
path(
    'employees/import/',
    views.import_employees,
    name='import_employees'
),
path(
    'employees/export/csv/',
    views.export_employees_csv,
    name='export_employees_csv'
),

path(
    'employees/export/excel/',
    views.export_employees_excel,
    name='export_employees_excel'
),
path(
    'departments/edit/<int:id>/',
    views.edit_department,
    name='edit_department'
),

path(
    'departments/delete/<int:id>/',
    views.delete_department,
    name='delete_department'
),
path('api/employees/<int:id>/',views.employee_detail_api,name='employee_detail_api'),
]