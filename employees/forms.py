from django import forms
from .models import Department, Attendance, LeaveRequest, Performance 



class EmployeeForm(forms.Form):

    name = forms.CharField(
        max_length=100,
        strip=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter employee name'
        })
    )

    department = forms.ModelChoiceField(
        queryset=Department.objects.none(),
        empty_label='Select Department',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    salary = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter salary'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['department'].queryset = Department.objects.order_by('name')

    def clean_name(self):
        name = self.cleaned_data['name'].strip()

        if not name:
            raise forms.ValidationError(
                'Employee name cannot be empty.'
            )

        return name


class DepartmentForm(forms.ModelForm):

    class Meta:
        model = Department
        fields = ['name']

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter department name'
            })
        }

    def clean_name(self):
        name = self.cleaned_data['name'].strip()

        if not name:
            raise forms.ValidationError(
                'Department name cannot be empty.'
            )

        return name

class EmployeeImportForm(forms.Form):

    file = forms.FileField(
        label='Select CSV or Excel File',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx'
        })
    )

    def clean_file(self):
        uploaded_file = self.cleaned_data['file']

        allowed_extensions = ['.csv', '.xlsx']
        extension = uploaded_file.name.lower().rsplit('.', 1)

        if len(extension) != 2 or f'.{extension[-1]}' not in allowed_extensions:
            raise forms.ValidationError(
                'Only CSV and Excel (.xlsx) files are allowed.'
            )

        if uploaded_file.size > 5 * 1024 * 1024:
            raise forms.ValidationError(
                'File size cannot exceed 5 MB.'
            )

        return uploaded_file

from .models import Attendance


class AttendanceForm(forms.ModelForm):

    class Meta:
        model = Attendance

        fields = [
            'employee',
            'date',
            'status',
            'check_in',
            'check_out',
            'remarks',
        ]

        widgets = {
            'employee': forms.Select(attrs={
                'class': 'form-select'
            }),

            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),

            'status': forms.Select(attrs={
                'class': 'form-select'
            }),

            'check_in': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),

            'check_out': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),

            'remarks': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter remarks (optional)'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()

        status = cleaned_data.get('status')
        check_in = cleaned_data.get('check_in')
        check_out = cleaned_data.get('check_out')

        if status != 'Present' and (check_in or check_out):
            raise forms.ValidationError(
                'Check-in and check-out times are only allowed for Present employees.'
            )

        if check_in and check_out and check_out <= check_in:
            self.add_error(
                'check_out',
                'Check-out time must be later than check-in time.'
            )

        return cleaned_data

class LeaveRequestForm(forms.ModelForm):

    class Meta:
        model = LeaveRequest

        fields = [
            'employee',
            'start_date',
            'end_date',
            'reason',
        ]

        widgets = {
            'employee': forms.Select(attrs={
                'class': 'form-select'
            }),

            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),

            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),

            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter reason for leave'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()

        employee = cleaned_data.get('employee')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and end_date < start_date:
            self.add_error(
                'end_date',
                'End date cannot be earlier than start date.'
            )

        if employee and start_date and end_date:
            overlapping_leaves = LeaveRequest.objects.filter(
                employee=employee,
                status__in=['Pending', 'Approved'],
                start_date__lte=end_date,
                end_date__gte=start_date
            )

            if self.instance.pk:
                overlapping_leaves = overlapping_leaves.exclude(
                    pk=self.instance.pk
                )

            if overlapping_leaves.exists():
                raise forms.ValidationError(
                    'This employee already has a pending or approved '
                    'leave request during these dates.'
                )

        return cleaned_data

class PerformanceForm(forms.ModelForm):

    class Meta:
        model = Performance

        fields = [
            'employee',
            'rating',
            'feedback',
            'review_date'
        ]

        widgets = {
            'employee': forms.Select(attrs={
                'class': 'form-select'
            }),

            'rating': forms.Select(attrs={
                'class': 'form-select'
            }),

            'feedback': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter performance feedback'
            }),

            'review_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }