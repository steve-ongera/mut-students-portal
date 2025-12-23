# MUT University Management System

A comprehensive Django-based University Management System designed for Murang'a University of Technology (MUT). This system handles all aspects of university operations including academic management, student services, hostel allocation, library management, and administrative workflows.

## 👨‍💻 Developer

**Name:** Tseve Ongera  
**Email:** steveongera001@gmail.com  
**Project Type:** Personal Project  
**Institution:** Murang'a University of Technology

## 🎯 Overview

This system provides a complete solution for managing university operations with role-based access control for different user types including students, lecturers, HODs, deans, and administrative staff.

## ✨ Key Features

### 👥 User Management
- Multi-role user system (Students, Lecturers, HOD, HOS, Dean, Finance, etc.)
- Role-based access control and permissions
- Profile management with photo upload

### 🎓 Academic Management
- Schools and Departments structure
- Programme management (Certificate, Diploma, Degree, Masters, PhD)
- Academic year and semester management
- Intake management (September, January, May)
- Unit/Course management with prerequisites
- Unit allocation to lecturers with approval workflow

### 📚 Student Services
- Student registration and profile management
- Unit registration per semester
- Programme progression tracking (Diploma to Degree)
- Academic transcripts and results

### 📊 Assessment & Grading
- Multiple assessment types (CAT 1, CAT 2, CAT 3, Assignments, Exams)
- Marks entry and approval workflow (Lecturer → HOD → HOS → Dean)
- GPA calculation (Semester and Cumulative)
- Results publication system
- Grading system configuration

### 💰 Finance Management
- Fee structure management per programme
- Fee payment tracking (M-Pesa, Bank, Cash, etc.)
- Fee balance monitoring
- Receipt generation

### 🏠 Hostel Management
- Hostel and room management
- Bed allocation system
- Hostel application and approval
- Hostel fee management

### 📖 Library Management
- Book cataloging with ISBN
- Book borrowing system
- Fine calculation for overdue books
- Book categories and search

### 🗓️ Timetable & Attendance
- Timetable creation and publishing
- Class scheduling with venue management
- Student attendance tracking
- Attendance reports

### 📢 Communication
- Announcements system
- Event management
- Internal messaging
- Category-based message routing

### 🛒 Procurement & Store
- Purchase requisition workflow
- Supplier management
- Item categorization
- Multi-level approval system

## 🛠️ Technology Stack

- **Framework:** Django 4.x+
- **Database:** PostgreSQL / MySQL / SQLite
- **Language:** Python 3.8+

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)
- Database (PostgreSQL recommended for production)

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd mut-university-system
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install django pillow
   # Add other dependencies as needed
   ```

4. **Configure database settings**
   
   Edit `settings.py` and configure your database:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'mut_db',
           'USER': 'your_username',
           'PASSWORD': 'your_password',
           'HOST': 'localhost',
           'PORT': '5432',
       }
   }
   ```

5. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Admin Panel: http://localhost:8000/admin/
   - Main Application: http://localhost:8000/

## 📁 Project Structure

```
mut-university-system/
├── manage.py
├── requirements.txt
├── README.md
├── app_name/
│   ├── models.py          # All database models
│   ├── admin.py           # Django admin configuration
│   ├── views.py           # View logic
│   ├── urls.py            # URL routing
│   ├── forms.py           # Form definitions
│   └── templates/         # HTML templates
└── media/
    ├── profiles/          # User profile pictures
    ├── books/             # Book covers
    ├── events/            # Event banners
    └── announcements/     # Announcement attachments
```

## 👤 User Roles

1. **Student** - Access to courses, results, fees, hostel, library
2. **Lecturer** - Unit management, marks entry, attendance
3. **HOD** - Department management, approvals
4. **HOS** - School-level management and approvals
5. **Dean** - Faculty oversight and final approvals
6. **Finance Officer** - Fee management and financial reports
7. **Procurement Officer** - Purchase requisitions and suppliers
8. **Store Manager** - Inventory management
9. **Librarian** - Library operations
10. **Hostel Warden** - Hostel management
11. **Registrar** - Student registration and records
12. **ICT Admin** - System administration
13. **Vice Chancellor** - Executive oversight

## 🔐 Security Features

- Role-based access control
- Multi-level approval workflows
- Secure password hashing
- User activity tracking
- Data validation and sanitization

## 📊 Key Workflows

### Marks Entry Workflow
1. Lecturer enters marks (Draft)
2. Submit to HOD for approval
3. HOD reviews and approves
4. HOS reviews and approves
5. Dean gives final approval
6. Results published to students

### Fee Payment Process
1. Student views fee structure
2. Makes payment (M-Pesa/Bank/Cash)
3. Finance officer verifies payment
4. Receipt generated
5. Fee balance updated

### Hostel Allocation
1. Student submits hostel application
2. Pays booking fee
3. Warden reviews application
4. Bed allocated if available
5. Student checks in

## 🤝 Contributing

This is a personal project, but suggestions and feedback are welcome. Please reach out via email for any inquiries.

## 📧 Contact

For questions, suggestions, or support:

**Tseve Ongera**  
Email: steveongera001@gmail.com

## 📝 License

This project is created as a personal academic project for Murang'a University of Technology.

## 🙏 Acknowledgments

- Murang'a University of Technology
- Django Documentation
- Python Community

---

**Note:** This system is under active development. Features and documentation may be updated regularly.