from django.shortcuts import render, redirect,get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import EmployeeSerializer
from .models import Department, Employee, Attendance, LeaveRequest,Performance,Notification
from .forms import (
    EmployeeForm, DepartmentForm, AttendanceForm, LeaveRequestForm,
    PerformanceForm, EmployeeImportForm,
)
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.auth import logout
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
from rest_framework import status
from django.db.models import Avg, Count, Max
from functools import wraps
from django.http import HttpResponseForbidden
from django.contrib.auth.views import redirect_to_login
from django.contrib import messages
from django.utils import timezone
from django.db import IntegrityError
import csv
from openpyxl import load_workbook
from django.db import transaction
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from django.views.decorators.http import require_POST

def is_admin(user):
    return (
        user.is_authenticated
        and (
            user.is_superuser
            or user.groups.filter(name='Admin').exists()
        )
    )
def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())

        if not is_admin(request.user):
            return HttpResponseForbidden(
                "You do not have permission to access this page."
            )

        return view_func(request, *args, **kwargs)

    return wrapper

def is_employee(user):
    return (
        user.is_authenticated
        and user.groups.filter(name='Employee').exists()
    )

@login_required
def home(request):

    # Total employees
    total_employees = Employee.objects.count()

    # Total departments
    total_departments = Department.objects.count()

    # Average salary
    average_salary = Employee.objects.aggregate(
        avg_salary=Avg('salary')
    )['avg_salary'] or 0

    # Highest salary
    highest_salary = Employee.objects.aggregate(
        max_salary=Max('salary')
    )['max_salary'] or 0

    # Department-wise employee count
    department_data = Department.objects.annotate(
        employee_count=Count('employees')
    ).order_by('name')

    department_labels = [
        department.name for department in department_data
    ]

    department_counts = [
        department.employee_count for department in department_data
    ]

    # Salary distribution
    salary_data = Employee.objects.values(
        'salary'
    ).order_by('salary')

    salary_labels = [
        str(item['salary']) for item in salary_data
    ]

    salary_counts = [
        1 for item in salary_data
    ]

    context = {
        'total_employees': total_employees,
        'total_departments': total_departments,
        'average_salary': round(average_salary, 2),
        'highest_salary': highest_salary,
        'department_labels': department_labels,
        'department_counts': department_counts,
        'salary_labels': salary_labels,
        'salary_counts': salary_counts,
    }

    return render(request, 'employees/home.html', context)
@login_required
def profile(request):
    return render(
        request,
        'employees/profile.html',
        {'user': request.user}
    )
# Department List
@admin_required

def department_list(request):
    departments = Department.objects.annotate(
        employee_count=Count('employees')
    ).order_by('name')

    return render(
        request,
        'employees/department_list.html',
        {'departments': departments}
    )


# Add Department
@admin_required
def add_department(request):
    form = DepartmentForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            form.save()

            messages.success(
                request,
                'Department added successfully!'
            )

            return redirect('department_list')

        else:
            messages.error(
                request,
                'Please correct the errors below.'
            )

    return render(
        request,
        'employees/add_department.html',
        {'form': form}
    )


# Edit Department
@admin_required
def edit_department(request, id):
    department = get_object_or_404(Department, id=id)

    form = DepartmentForm(
        request.POST or None,
        instance=department
    )

    if request.method == 'POST':
        if form.is_valid():
            form.save()

            messages.success(
                request,
                'Department updated successfully!'
            )

            return redirect('department_list')

        else:
            messages.error(
                request,
                'Please correct the errors below.'
            )

    return render(
        request,
        'employees/edit_department.html',
        {
            'form': form,
            'department': department
        }
    )


# Delete Department
@admin_required
def delete_department(request, id):
    department = get_object_or_404(Department, id=id)

    if request.method == 'POST':

        # Check whether employees are assigned
        if department.employees.exists():

            messages.error(
                request,
                'Cannot delete this department because employees are assigned to it.'
            )

            return redirect('department_list')

        department.delete()

        messages.success(
            request,
            'Department deleted successfully!'
        )

        return redirect('department_list')

    return render(
        request,
        'employees/delete_department.html',
        {'department': department}
    )
@admin_required
def employee_list(request):
    search_query = request.GET.get('search', '').strip()
    department_id = request.GET.get('department', '')
    min_salary = request.GET.get('min_salary', '').strip()
    max_salary = request.GET.get('max_salary', '').strip()
    sort_by = request.GET.get('sort', 'id')

    employees = Employee.objects.select_related('department').all()
    departments = Department.objects.order_by('name')

    # Search by employee name or department
    if search_query:
        employees = employees.filter(
            Q(name__icontains=search_query) |
            Q(department__name__icontains=search_query)
        )

    # Filter by department
    if department_id:
        employees = employees.filter(department_id=department_id)

    # Filter by minimum salary
    if min_salary:
        try:
            employees = employees.filter(salary__gte=int(min_salary))
        except ValueError:
            messages.error(request, 'Minimum salary must be a valid number.')
            min_salary = ''

    # Filter by maximum salary
    if max_salary:
        try:
            employees = employees.filter(salary__lte=int(max_salary))
        except ValueError:
            messages.error(request, 'Maximum salary must be a valid number.')
            max_salary = ''

    # Validate salary range
    if min_salary and max_salary:
        if int(min_salary) > int(max_salary):
            messages.error(
                request,
                'Minimum salary cannot be greater than maximum salary.'
            )
            min_salary = ''
            max_salary = ''

    # Allowed sorting fields
    sorting_options = {
        'name': 'name',
        '-name': '-name',
        'salary': 'salary',
        '-salary': '-salary',
        'department': 'department__name',
        '-department': '-department__name',
        'id': 'id',
        '-id': '-id',
    }

    # Apply sorting
    employees = employees.order_by(
        sorting_options.get(sort_by, 'id')
    )

    # Pagination
    paginator = Paginator(employees, 10)
    page_number = request.GET.get('page')
    employees = paginator.get_page(page_number)

    context = {
        'employees': employees,
        'departments': departments,
        'search_query': search_query,
        'selected_department': department_id,
        'min_salary': min_salary,
        'max_salary': max_salary,
        'sort_by': sort_by,
    }

    return render(request, 'employees/employee_list.html', context)

def get_export_employees(request):
    search_query = request.GET.get('search', '').strip()
    department_id = request.GET.get('department', '')
    min_salary = request.GET.get('min_salary', '').strip()
    max_salary = request.GET.get('max_salary', '').strip()
    sort_by = request.GET.get('sort', 'id')

    employees = Employee.objects.select_related('department').all()

    # Search by employee name or department
    if search_query:
        employees = employees.filter(
            Q(name__icontains=search_query) |
            Q(department__name__icontains=search_query)
        )

    # Filter by department
    if department_id.isdigit():
        employees = employees.filter(department_id=int(department_id))

    # Minimum salary
    if min_salary:
        try:
            employees = employees.filter(salary__gte=int(min_salary))
        except ValueError:
            pass

    # Maximum salary
    if max_salary:
        try:
            employees = employees.filter(salary__lte=int(max_salary))
        except ValueError:
            pass

    # Validate sorting options
    sorting_options = {
        'id': 'id',
        '-id': '-id',
        'name': 'name',
        '-name': '-name',
        'salary': 'salary',
        '-salary': '-salary',
        'department': 'department__name',
        '-department': '-department__name',
    }

    employees = employees.order_by(
        sorting_options.get(sort_by, 'id')
    )

    return employees

@admin_required
def export_employees_csv(request):
    employees = get_export_employees(request)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        'attachment; filename="employees.csv"'
    )

    writer = csv.writer(response)

    # Column headings
    writer.writerow([
        'Employee ID',
        'Employee Name',
        'Department',
        'Salary'
    ])

    # Employee records
    for employee in employees:
        writer.writerow([
            employee.id,
            employee.name,
            employee.department.name,
            employee.salary
        ])

    return response

@admin_required
def export_employees_excel(request):
    employees = get_export_employees(request)

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = 'Employees'

    # Column headings
    headers = [
        'Employee ID',
        'Employee Name',
        'Department',
        'Salary'
    ]

    worksheet.append(headers)

    # Style headings
    for cell in worksheet[1]:
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = PatternFill(
            start_color='1F4E78',
            end_color='1F4E78',
            fill_type='solid'
        )
        cell.alignment = Alignment(horizontal='center')

    # Employee records
    for employee in employees:
        worksheet.append([
            employee.id,
            employee.name,
            employee.department.name,
            employee.salary
        ])

    # Set column widths
    worksheet.column_dimensions['A'].width = 15
    worksheet.column_dimensions['B'].width = 25
    worksheet.column_dimensions['C'].width = 25
    worksheet.column_dimensions['D'].width = 18

    response = HttpResponse(
        content_type=(
            'application/vnd.openxmlformats-officedocument.'
            'spreadsheetml.sheet'
        )
    )

    response['Content-Disposition'] = (
        'attachment; filename="employees.xlsx"'
    )

    workbook.save(response)

    return response
@admin_required
def employee_detail(request, id):
    employee = get_object_or_404(Employee, id=id)

    context = {
        'employee': employee
    }

    return render(
        request,
        'employees/employee_detail.html',
        context
    )


@admin_required
def add_employee(request):
    form = EmployeeForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            Employee.objects.create(
                name=form.cleaned_data['name'],
                department=form.cleaned_data['department'],
                salary=form.cleaned_data['salary']
            )

            messages.success(request, 'Employee added successfully!')
            return redirect('employee_list')

        else:
            messages.error(request, 'Please correct the errors below.')

    return render(
        request,
        'employees/add_employee.html',
        {'form': form}
    )


@admin_required
def edit_employee(request, id):
    employee = get_object_or_404(Employee, id=id)

    form = EmployeeForm(
        request.POST or None,
        initial={
            'name': employee.name,
            'department': employee.department,
            'salary': employee.salary
        }
    )

    if request.method == 'POST':
        if form.is_valid():
            employee.name = form.cleaned_data['name']
            employee.department = form.cleaned_data['department']
            employee.salary = form.cleaned_data['salary']
            employee.save()

            messages.success(request, 'Employee updated successfully!')
            return redirect('employee_list')

        else:
            messages.error(request, 'Please correct the errors below.')

    return render(
        request,
        'employees/edit_employee.html',
        {'form': form, 'employee': employee}
    )

@admin_required
def delete_employee(request, id):
    employee = get_object_or_404(Employee, id=id)

    if request.method == 'POST':
        employee.delete()

        messages.success(request, 'Employee deleted successfully!')
        return redirect('employee_list')

    return render(
        request,
        'employees/delete_employee.html',
        {'employee': employee}
    )

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')

    return redirect('employee_list')

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def employee_api(request):

    # GET: Retrieve employees
    if request.method == 'GET':

        if is_admin(request.user):
            employees = Employee.objects.all()

        elif is_employee(request.user):
            try:
                employee = request.user.employee_profile
            except Employee.DoesNotExist:
                return Response(
                    {"error": "No employee profile linked to your account."},
                    status=status.HTTP_403_FORBIDDEN
                )

            employees = Employee.objects.filter(id=employee.id)

        else:
            return Response(
                {"error": "You do not have permission."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = EmployeeSerializer(employees, many=True)
        return Response(serializer.data)

    # POST: Create a new employee
    elif request.method == 'POST':

        if not is_admin(request.user):
            return Response(
                {"error": "Only Admin can create employees."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = EmployeeSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def employee_detail_api(request, id):

    try:
        employee = Employee.objects.get(id=id)

    except Employee.DoesNotExist:
        return Response(
            {"error": "Employee not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    # Employee can access only their own record
    if is_employee(request.user) and not is_admin(request.user):

        try:
            own_employee = request.user.employee_profile

        except Employee.DoesNotExist:
            return Response(
                {"error": "No employee profile linked to your account."},
                status=status.HTTP_403_FORBIDDEN
            )

        if employee.id != own_employee.id:
            return Response(
                {"error": "You cannot access another employee's record."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Employees have read-only access
        if request.method != 'GET':
            return Response(
                {"error": "Employees cannot modify employee records."},
                status=status.HTTP_403_FORBIDDEN
            )

    # Only Admin can perform API modifications
    elif not is_admin(request.user):
        return Response(
            {"error": "You do not have permission."},
            status=status.HTTP_403_FORBIDDEN
        )

    if request.method == 'GET':

        serializer = EmployeeSerializer(employee)
        return Response(serializer.data)

    elif request.method == 'PUT':

        serializer = EmployeeSerializer(employee, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    elif request.method == 'PATCH':

        serializer = EmployeeSerializer(
            employee,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    elif request.method == 'DELETE':

        employee.delete()

        return Response(
            {"message": "Employee deleted successfully"},
            status=status.HTTP_200_OK
        )

@admin_required
def import_employees(request):
    form = EmployeeImportForm(request.POST or None, request.FILES or None)

    if request.method == 'POST':
        if form.is_valid():
            uploaded_file = form.cleaned_data['file']
            filename = uploaded_file.name.lower()

            try:
                # Read CSV file
                if filename.endswith('.csv'):
                    content = uploaded_file.read().decode('utf-8-sig')
                    reader = csv.DictReader(content.splitlines())
                    rows = list(reader)

                # Read Excel file
                else:
                    workbook = load_workbook(
                        uploaded_file,
                        read_only=True,
                        data_only=True
                    )

                    worksheet = workbook.active
                    data = list(worksheet.iter_rows(values_only=True))

                    if not data:
                        raise ValueError('The uploaded file is empty.')

                    headers = [
                        str(value).strip() if value is not None else ''
                        for value in data[0]
                    ]

                    rows = [
                        dict(zip(headers, row))
                        for row in data[1:]
                    ]

                    workbook.close()

                if not rows:
                    raise ValueError('The uploaded file contains no employee records.')

                imported_count = 0
                errors = []

                # Import employee records
                for row_number, row in enumerate(rows, start=2):

                    # Normalize column names
                    normalized_row = {
                        str(key).strip().lower(): value
                        for key, value in row.items()
                        if key is not None
                    }

                    name = normalized_row.get('employee name')
                    department_name = normalized_row.get('department')
                    salary = normalized_row.get('salary')

                    # Validate employee name
                    if name is None or not str(name).strip():
                        errors.append(
                            f'Row {row_number}: Employee name is missing.'
                        )
                        continue

                    # Validate department
                    if department_name is None or not str(department_name).strip():
                        errors.append(
                            f'Row {row_number}: Department is missing.'
                        )
                        continue

                    department = Department.objects.filter(
                        name__iexact=str(department_name).strip()
                    ).first()

                    if department is None:
                        errors.append(
                            f'Row {row_number}: Department '
                            f'"{department_name}" does not exist.'
                        )
                        continue

                    # Validate salary
                    try:
                        salary = int(salary)

                        if salary < 0:
                            raise ValueError

                    except (ValueError, TypeError):
                        errors.append(
                            f'Row {row_number}: Salary must be a '
                            f'non-negative whole number.'
                        )
                        continue

                    # Create employee
                    Employee.objects.create(
                        name=str(name).strip(),
                        department=department,
                        salary=salary
                    )

                    imported_count += 1

                if imported_count:
                    messages.success(
                        request,
                        f'{imported_count} employee(s) imported successfully!'
                    )

                if errors:
                    request.session['import_errors'] = errors

                return redirect('import_employees')

            except (UnicodeDecodeError, csv.Error, ValueError, KeyError) as error:
                messages.error(
                    request,
                    f'Unable to import file: {error}'
                )

    import_errors = request.session.pop('import_errors', [])

    return render(
        request,
        'employees/import_employees.html',
        {
            'form': form,
            'import_errors': import_errors
        }
    )
@login_required
def attendance_list(request):

    if is_admin(request.user):
        attendance_records = Attendance.objects.select_related(
            'employee',
            'employee__department'
        ).all()

    else:
        try:
            employee = request.user.employee_profile
        except Employee.DoesNotExist:
            return HttpResponseForbidden(
                "No employee profile is linked to your account."
            )

        attendance_records = Attendance.objects.filter(
            employee=employee
        ).select_related('employee', 'employee__department')

    selected_date = request.GET.get('date', '')
    search_query = request.GET.get('search', '').strip()
    selected_status = request.GET.get('status', '')

    if selected_date:
        attendance_records = attendance_records.filter(
            date=selected_date
        )

    if search_query:
        attendance_records = attendance_records.filter(
            employee__name__icontains=search_query
        )

    if selected_status in ['Present', 'Absent', 'On Leave']:
        attendance_records = attendance_records.filter(
            status=selected_status
        )

    context = {
        'attendance_records': attendance_records,
        'selected_date': selected_date,
        'search_query': search_query,
        'selected_status': selected_status,
    }

    return render(
        request,
        'employees/attendance_list.html',
        context
    )

@admin_required
def mark_attendance(request):

    form = AttendanceForm(request.POST or None)

    if request.method == 'POST':

        if form.is_valid():

            try:
                with transaction.atomic():
                    form.save()

                messages.success(
                    request,
                    'Attendance marked successfully!'
                )

                return redirect('attendance_list')

            except IntegrityError:
                messages.error(
                    request,
                    'Attendance for this employee and date already exists.'
                )

        else:
            messages.error(
                request,
                'Please correct the errors below.'
            )

    return render(
        request,
        'employees/mark_attendance.html',
        {'form': form}
    )
@login_required
def leave_list(request):

    if is_admin(request.user):
        leave_requests = LeaveRequest.objects.select_related(
            'employee',
            'employee__department'
        ).all()

    else:
        try:
            employee = request.user.employee_profile
        except Employee.DoesNotExist:
            return HttpResponseForbidden(
                "No employee profile is linked to your account."
            )

        leave_requests = LeaveRequest.objects.filter(
            employee=employee
        ).select_related('employee', 'employee__department')

    search_query = request.GET.get('search', '').strip()
    selected_status = request.GET.get('status', '')

    if search_query:
        leave_requests = leave_requests.filter(
            employee__name__icontains=search_query
        )

    if selected_status in ['Pending', 'Approved', 'Rejected']:
        leave_requests = leave_requests.filter(
            status=selected_status
        )

    context = {
        'leave_requests': leave_requests,
        'search_query': search_query,
        'selected_status': selected_status,
    }

    return render(
        request,
        'employees/leave_list.html',
        context
    )
@login_required
def apply_leave(request):

    # Admin can apply leave for any employee
    if is_admin(request.user):
        employee = None

    else:
        # Find the employee connected to the logged-in user
        try:
            employee = request.user.employee_profile
        except Employee.DoesNotExist:
            return HttpResponseForbidden(
                "No employee profile is linked to your account."
            )

    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)

    else:
        form = LeaveRequestForm()

    # Employees cannot choose another employee
    if employee is not None:
        form.fields['employee'].initial = employee
        form.fields['employee'].disabled = True

    if request.method == 'POST' and form.is_valid():

        leave_request = form.save(commit=False)

        if employee is not None:
            leave_request.employee = employee

        leave_request.status = 'Pending'
        leave_request.save()

        # Notify administrators
        User = get_user_model()

        administrators = User.objects.filter(
            is_staff=True,
            is_active=True
        )

        notifications = [
            Notification(
                recipient=admin,
                title='New Leave Request',
                message=(
                    f'{leave_request.employee.name} has applied '
                    f'for leave from {leave_request.start_date} '
                    f'to {leave_request.end_date}.'
                )
            )
            for admin in administrators
        ]

        Notification.objects.bulk_create(notifications)

        messages.success(
            request,
            'Leave request submitted successfully!'
        )

        return redirect('leave_list')

    return render(
        request,
        'employees/apply_leave.html',
        {'form': form}
    )
@admin_required
@require_POST
def update_leave_status(request, id, status):

    leave_request = get_object_or_404(LeaveRequest, id=id)

    if status not in ['Approved', 'Rejected']:
        messages.error(request, 'Invalid leave status.')
        return redirect('leave_list')

    if leave_request.status != 'Pending':
        messages.warning(request, 'This leave request has already been reviewed.')
        return redirect('leave_list')

    if status == 'Approved':
        overlapping_leaves = LeaveRequest.objects.filter(
            employee=leave_request.employee,
            status='Approved',
            start_date__lte=leave_request.end_date,
            end_date__gte=leave_request.start_date
        ).exclude(id=leave_request.id)

        if overlapping_leaves.exists():
            messages.error(
                request,
                'Another approved leave request already exists for these dates.'
            )
            return redirect('leave_list')

    leave_request.status = status
    leave_request.reviewed_at = timezone.now()
    leave_request.save()

    messages.success(
        request,
        f'Leave request {status.lower()} successfully.'
    )

    return redirect('leave_list')
@admin_required
def add_performance(request):

    if request.method == 'POST':
        form = PerformanceForm(request.POST)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                'Performance review added successfully!'
            )

            return redirect('performance_list')

    else:
        form = PerformanceForm()

    return render(
        request,
        'employees/add_performance.html',
        {'form': form}
    )
@login_required
def performance_list(request):

    if is_admin(request.user):
        performances = Performance.objects.select_related(
            'employee',
            'employee__department'
        ).all()

    else:
        try:
            employee = request.user.employee_profile
        except Employee.DoesNotExist:
            return HttpResponseForbidden(
                "No employee profile is linked to your account."
            )

        performances = Performance.objects.filter(
            employee=employee
        ).select_related('employee', 'employee__department')

    return render(
        request,
        'employees/performance_list.html',
        {'performances': performances}
    )

@admin_required
def performance_summary(request):

    employees = Employee.objects.annotate(
        average_rating=Avg('performance_reviews__rating')
    ).order_by('name')

    return render(
        request,
        'employees/performance_summary.html',
        {'employees': employees}
    )
@login_required
def employee_performance_history(request, id):

    if is_admin(request.user):
        employee = get_object_or_404(Employee, id=id)

    else:
        try:
            employee = request.user.employee_profile
        except Employee.DoesNotExist:
            return HttpResponseForbidden(
                "No employee profile is linked to your account."
            )

        if employee.id != id:
            return HttpResponseForbidden(
                "You cannot access another employee's performance."
            )

    performances = employee.performance_reviews.all()

    average_rating = performances.aggregate(
        average=Avg('rating')
    )['average']

    return render(
        request,
        'employees/employee_performance_history.html',
        {
            'employee': employee,
            'performances': performances,
            'average_rating': average_rating
        }
    )

@login_required
def notification_list(request):

    notifications = Notification.objects.filter(
        recipient=request.user
    )

    unread_count = notifications.filter(is_read=False).count()

    return render(
        request,
        'employees/notification_list.html',
        {
            'notifications': notifications,
            'unread_count': unread_count
        }
    )
@login_required
@require_POST
def mark_notification_read(request, id):

    notification = get_object_or_404(
        Notification,
        id=id,
        recipient=request.user
    )

    notification.is_read = True
    notification.save(update_fields=['is_read'])

    messages.success(request, 'Notification marked as read.')

    return redirect('notification_list')
@login_required
@require_POST
def mark_all_notifications_read(request):

    Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True)

    messages.success(request, 'All notifications marked as read.')

    return redirect('notification_list')


@admin_required
def setup_user_roles(request):

    if not request.user.is_superuser:
        messages.error(
            request,
            'Only superusers can initialize user roles.'
        )
        return redirect('home')

    Group.objects.get_or_create(name='Admin')
    Group.objects.get_or_create(name='Employee')

    messages.success(
        request,
        'Admin and Employee groups created successfully!'
    )

    return redirect('home')