"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.contrib.auth import views as auth_views
from employees import views



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('employees.urls')),

    # Authentication
    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='employees/login.html'
        ),
        name='login'
    ),

    path(
        'logout/',
        auth_views.LogoutView.as_view(),
        name='logout'
    ),

    # Employee Management
    path('', views.home, name='home'),
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/add/', views.add_employee, name='add_employee'),
    path(
        'employees/model-form/',
        views.add_employee,
        name='add_employee_model_form',
    ),

    path(
        'employees/edit/<int:id>/',
        views.edit_employee,
        name='edit_employee'
    ),

    path(
        'employees/delete/<int:id>/',
        views.delete_employee,
        name='delete_employee'
    ),
    

]
