# Employee Management System

A web-based Employee Management System built using Python and Django. This application helps manage employee records, departments, attendance, leave requests, and performance.

## Features

- Employee Management – Add, edit, view, delete, and search employees.
- Department Management – Manage employee departments.
- Attendance Management – Mark and view employee attendance.
- Leave Management – Apply for leave and manage leave requests.
- Performance Management – Record and track employee performance.
- Employee Dashboard – Access employee management information.
- Employee Import – Import employee records using CSV.
- Notifications – View system notifications.
- User Authentication – Login and profile management.
- Responsive UI – Modern interface using Bootstrap and CSS.

## Technology Stack

- Python
- Django
- SQLite
- HTML5
- CSS3
- JavaScript
- Bootstrap
- Django REST Framework

## Project Structure

```text
django_project/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── employees/
│   ├── migrations/
│   ├── templates/
│   ├── static/
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   └── urls.py
│
├── manage.py
├── requirements.txt
└── README.md
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/ajaysolanki-cmd/Employee-Management-System.git
```

### 2. Navigate to the project directory

```bash
cd Employee-Management-System
```

### 3. Create a virtual environment

```bash
python -m venv venv
```

### 4. Activate the virtual environment

Windows:

```bash
venv\Scripts\activate
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure environment variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your_django_secret_key
DEBUG=True
```

Never upload your `.env` file to GitHub.

### 7. Apply database migrations

```bash
python manage.py migrate
```

### 8. Create a superuser

```bash
python manage.py createsuperuser
```

### 9. Run the development server

```bash
python manage.py runserver
```

Open your browser:

http://127.0.0.1:8000/

## Author

Ajay Solanki

GitHub: https://github.com/ajaysolanki-cmd

## License

This project is available for learning and educational purposes.