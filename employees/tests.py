from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse


from .models import Department, Employee


class EmployeeDepartmentTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(
            username='employee-test',
            password='test-password',
        )
        self.client.force_login(user)

    def test_add_employee_creates_and_assigns_department(self):
        response = self.client.post(
            reverse('add_employee'),
            {'name': 'Alice', 'department': 'HR', 'salary': '50000'},
        )

        self.assertRedirects(response, reverse('employee_list'))
        employee = Employee.objects.get(name='Alice')
        self.assertEqual(employee.department.name, 'HR')
        self.assertEqual(Department.objects.filter(name='HR').count(), 1)

    def test_edit_employee_updates_department_relation(self):
        old_department = Department.objects.create(name='Operations')
        employee = Employee.objects.create(
            name='Bob',
            department=old_department,
            salary=40000,
        )

        response = self.client.post(
            reverse('edit_employee', args=[employee.pk]),
            {'name': 'Bob', 'department': 'Finance', 'salary': '45000'},
        )

        self.assertRedirects(response, reverse('employee_list'))
        employee.refresh_from_db()
        self.assertEqual(employee.department.name, 'Finance')
        self.assertEqual(employee.salary, 45000)

    def test_legacy_add_route_uses_department_name_form(self):
        response = self.client.post(
            reverse('add_employee_model_form'),
            {'name': 'Carol', 'department': 'Research', 'salary': '60000'},
        )

        self.assertRedirects(response, reverse('employee_list'))
        self.assertEqual(
            Employee.objects.get(name='Carol').department.name,
            'Research',
        )

    def test_employee_list_searches_department_and_orders_results(self):
        department = Department.objects.create(name='Engineering')
        for name in ('Zoe', 'Amy', 'Mia', 'Ian', 'Leo', 'Eve'):
            Employee.objects.create(
                name=name,
                department=department,
                salary=50000,
            )

        response = self.client.get(
            reverse('employee_list'),
            {'search': 'Engineering'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [employee.name for employee in response.context['employees']],
            ['Zoe', 'Amy', 'Mia', 'Ian', 'Leo'],
        )
        self.assertContains(response, 'page=2')

    def test_homepage_links_to_employee_list(self):
        response = self.client.get(reverse('home'))

        self.assertContains(response, reverse('employee_list'))

class EmployeeModelTest(TestCase):

    def setUp(self):
        self.department = Department.objects.create(
            name="IT"
        )

        self.employee = Employee.objects.create(
            name="Ajay",
            department=self.department,
            salary=30000
        )

    def test_employee_creation(self):
        self.assertEqual(self.employee.name, "Ajay")
        self.assertEqual(self.employee.salary, 30000)

    def test_employee_department(self):
        self.assertEqual(self.employee.department.name, "IT")

class EmployeeAPITest(TestCase):

    def setUp(self):
        self.department = Department.objects.create(
            name="HR"
        )

        self.employee = Employee.objects.create(
            name="Rahul",
            department=self.department,
            salary=25000
        )

    def test_employee_api(self):
        response = self.client.get('/api/employees/')

        self.assertEqual(response.status_code, 200)

    def test_employee_detail_api(self):
        response = self.client.get(
            f'/api/employees/{self.employee.id}/'
        )

        self.assertEqual(response.status_code, 200)