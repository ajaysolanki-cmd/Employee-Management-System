from django.contrib import admin
from .models import Employee, Department, Attendance, LeaveRequest
from .models import Performance, Notification


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user', 'department', 'salary')
    list_filter = ('department',)
    search_fields = ('name', 'user__username', 'department__name')


admin.site.register(Department)


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'status', 'check_in', 'check_out')
    list_filter = ('status', 'date')
    search_fields = ('employee__name', 'employee__department__name')
    ordering = ('-date',)


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'start_date', 'end_date', 'status', 'applied_at')
    list_filter = ('status', 'start_date')
    search_fields = ('employee__name', 'reason')
    ordering = ('-applied_at',)


@admin.register(Performance)
class PerformanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'rating', 'review_date', 'created_at')
    list_filter = ('rating', 'review_date')
    search_fields = ('employee__name', 'feedback')
    ordering = ('-review_date',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'title', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('recipient__username', 'title', 'message')
    ordering = ('-created_at',)