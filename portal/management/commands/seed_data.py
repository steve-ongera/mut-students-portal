"""
Django management command to seed the database with sample data
Usage: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta, date
from decimal import Decimal
import random

from portal.models import (
    User, School, Department, AcademicYear, Semester, Intake,
    Programme, Unit, ProgrammeUnit, UnitGradingSystem, UnitAllocation,
    Student, StudentProgression, UnitRegistration, Assessment, StudentMarks,
    SemesterResults, SemesterGPA, FeeStructure, FeePayment, FeeBalance,
    Lecturer, Hostel, HostelRoom, HostelBed, HostelFeeStructure,
    HostelApplication, HostelAllocation, BookCategory, Book, BookBorrowing,
    Timetable, TimetableSlot, Attendance, Announcement, Event, Message,
    Supplier, ProcurementCategory, PurchaseRequisition, RequisitionItem
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds the database with sample data for MUT University Management System'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            self.clear_data()

        self.stdout.write(self.style.SUCCESS('Starting data seeding...'))

        # Seed data in order of dependencies
        self.seed_users()
        self.seed_academic_structure()
        self.seed_academic_years()
        self.seed_programmes()
        self.seed_units()
        self.seed_lecturers()
        self.seed_students()
        self.seed_fees()
        self.seed_hostels()
        self.seed_library()
        self.seed_timetables()
        self.seed_assessments()
        self.seed_communication()
        self.seed_procurement()

        self.stdout.write(self.style.SUCCESS('Database seeding completed successfully!'))

    def clear_data(self):
        """Clear all data from database"""
        models = [
            RequisitionItem, PurchaseRequisition, ProcurementCategory, Supplier,
            Message, Event, Announcement, Attendance, TimetableSlot, Timetable,
            BookBorrowing, Book, BookCategory, HostelAllocation, HostelApplication,
            HostelFeeStructure, HostelBed, HostelRoom, Hostel, FeeBalance,
            FeePayment, FeeStructure, SemesterGPA, SemesterResults, StudentMarks,
            Assessment, UnitRegistration, StudentProgression, Student, Lecturer,
            UnitAllocation, UnitGradingSystem, ProgrammeUnit, Unit, Programme,
            Intake, Semester, AcademicYear, Department, School
        ]
        
        for model in models:
            model.objects.all().delete()
        
        # Clear users except superuser
        User.objects.exclude(is_superuser=True).delete()

    def seed_users(self):
        """Create system users with different roles"""
        self.stdout.write('Seeding users...')

        users_data = [
            # Deans
            {'username': 'dean_computing', 'email': 'dean.computing@mut.ac.ke', 'first_name': 'John', 
             'last_name': 'Kamau', 'role': 'dean', 'password': 'password123'},
            {'username': 'dean_business', 'email': 'dean.business@mut.ac.ke', 'first_name': 'Mary', 
             'last_name': 'Wanjiru', 'role': 'dean', 'password': 'password123'},
            
            # Heads of School
            {'username': 'hos_computing', 'email': 'hos.computing@mut.ac.ke', 'first_name': 'Peter', 
             'last_name': 'Mutua', 'role': 'hos', 'password': 'password123'},
            
            # HODs
            {'username': 'hod_cs', 'email': 'hod.cs@mut.ac.ke', 'first_name': 'Jane', 
             'last_name': 'Njeri', 'role': 'hod', 'password': 'password123'},
            {'username': 'hod_it', 'email': 'hod.it@mut.ac.ke', 'first_name': 'David', 
             'last_name': 'Omondi', 'role': 'hod', 'password': 'password123'},
            
            # Administrative Staff
            {'username': 'finance_officer', 'email': 'finance@mut.ac.ke', 'first_name': 'Alice', 
             'last_name': 'Akinyi', 'role': 'finance', 'password': 'password123'},
            {'username': 'registrar', 'email': 'registrar@mut.ac.ke', 'first_name': 'Robert', 
             'last_name': 'Kiprotich', 'role': 'registrar', 'password': 'password123'},
            {'username': 'librarian', 'email': 'librarian@mut.ac.ke', 'first_name': 'Grace', 
             'last_name': 'Muthoni', 'role': 'librarian', 'password': 'password123'},
            {'username': 'hostel_warden', 'email': 'warden@mut.ac.ke', 'first_name': 'Paul', 
             'last_name': 'Kipchoge', 'role': 'hostel_warden', 'password': 'password123'},
            {'username': 'procurement', 'email': 'procurement@mut.ac.ke', 'first_name': 'Sarah', 
             'last_name': 'Chebet', 'role': 'procurement', 'password': 'password123'},
        ]

        for user_data in users_data:
            password = user_data.pop('password')
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults=user_data
            )
            if created:
                user.set_password(password)
                user.is_staff = True
                user.save()
                self.stdout.write(f'  Created user: {user.username}')

    def seed_academic_structure(self):
        """Create schools and departments"""
        self.stdout.write('Seeding academic structure...')

        # Schools
        dean_computing = User.objects.get(username='dean_computing')
        hos_computing = User.objects.get(username='hos_computing')
        
        school_computing, _ = School.objects.get_or_create(
            code='SCIT',
            defaults={
                'name': 'School of Computing and Information Technology',
                'dean': dean_computing,
                'head_of_school': hos_computing,
                'email': 'scit@mut.ac.ke',
                'phone_number': '0712345678',
                'location': 'Main Campus, Block A'
            }
        )

        dean_business = User.objects.get(username='dean_business')
        school_business, _ = School.objects.get_or_create(
            code='SBE',
            defaults={
                'name': 'School of Business and Economics',
                'dean': dean_business,
                'email': 'sbe@mut.ac.ke',
                'phone_number': '0712345679',
                'location': 'Main Campus, Block B'
            }
        )

        # Departments
        hod_cs = User.objects.get(username='hod_cs')
        hod_it = User.objects.get(username='hod_it')

        dept_cs, _ = Department.objects.get_or_create(
            code='CS',
            defaults={
                'school': school_computing,
                'name': 'Computer Science',
                'hod': hod_cs,
                'email': 'cs@mut.ac.ke',
                'phone_number': '0712345680',
                'location': 'Block A, Room 201'
            }
        )

        dept_it, _ = Department.objects.get_or_create(
            code='IT',
            defaults={
                'school': school_computing,
                'name': 'Information Technology',
                'hod': hod_it,
                'email': 'it@mut.ac.ke',
                'phone_number': '0712345681',
                'location': 'Block A, Room 301'
            }
        )

        self.stdout.write(f'  Created {School.objects.count()} schools')
        self.stdout.write(f'  Created {Department.objects.count()} departments')

    def seed_academic_years(self):
        """Create academic years, semesters, and intakes"""
        self.stdout.write('Seeding academic years and semesters...')

        # Academic Years
        ay_2024, _ = AcademicYear.objects.get_or_create(
            name='2024/2025',
            defaults={
                'start_date': date(2024, 9, 1),
                'end_date': date(2025, 8, 31),
                'is_current': True
            }
        )

        ay_2023, _ = AcademicYear.objects.get_or_create(
            name='2023/2024',
            defaults={
                'start_date': date(2023, 9, 1),
                'end_date': date(2024, 8, 31),
                'is_current': False
            }
        )

        # Semesters for 2024/2025
        sem1_2024, _ = Semester.objects.get_or_create(
            academic_year=ay_2024,
            semester_number='1',
            defaults={
                'name': 'Semester 1 - 2024/2025',
                'start_date': date(2024, 9, 1),
                'end_date': date(2024, 12, 20),
                'registration_start_date': date(2024, 8, 15),
                'registration_end_date': date(2024, 9, 15),
                'is_current': True
            }
        )

        sem2_2024, _ = Semester.objects.get_or_create(
            academic_year=ay_2024,
            semester_number='2',
            defaults={
                'name': 'Semester 2 - 2024/2025',
                'start_date': date(2025, 1, 15),
                'end_date': date(2025, 5, 15),
                'registration_start_date': date(2025, 1, 1),
                'registration_end_date': date(2025, 1, 30),
                'is_current': False
            }
        )

        # Intakes
        Intake.objects.get_or_create(
            academic_year=ay_2024,
            month='september',
            defaults={
                'name': 'September 2024 Intake',
                'intake_number': 'SEP/2024',
                'start_date': date(2024, 9, 1),
                'application_deadline': date(2024, 8, 15)
            }
        )

        Intake.objects.get_or_create(
            academic_year=ay_2024,
            month='january',
            defaults={
                'name': 'January 2025 Intake',
                'intake_number': 'JAN/2025',
                'start_date': date(2025, 1, 15),
                'application_deadline': date(2025, 1, 5)
            }
        )

        self.stdout.write(f'  Created {AcademicYear.objects.count()} academic years')
        self.stdout.write(f'  Created {Semester.objects.count()} semesters')
        self.stdout.write(f'  Created {Intake.objects.count()} intakes')

    def seed_programmes(self):
        """Create programmes"""
        self.stdout.write('Seeding programmes...')

        dept_cs = Department.objects.get(code='CS')
        dept_it = Department.objects.get(code='IT')

        programmes_data = [
            {
                'code': 'BSCCS',
                'name': 'Bachelor of Science in Computer Science',
                'department': dept_cs,
                'programme_type': 'degree',
                'study_mode': 'full_time',
                'duration_years': 4,
                'total_semesters': 8,
                'min_credit_hours': 120
            },
            {
                'code': 'BSCIT',
                'name': 'Bachelor of Science in Information Technology',
                'department': dept_it,
                'programme_type': 'degree',
                'study_mode': 'full_time',
                'duration_years': 4,
                'total_semesters': 8,
                'min_credit_hours': 120
            },
            {
                'code': 'DIPIT',
                'name': 'Diploma in Information Technology',
                'department': dept_it,
                'programme_type': 'diploma',
                'study_mode': 'full_time',
                'duration_years': 2,
                'total_semesters': 4,
                'min_credit_hours': 60
            },
        ]

        for prog_data in programmes_data:
            Programme.objects.get_or_create(
                code=prog_data['code'],
                defaults=prog_data
            )

        self.stdout.write(f'  Created {Programme.objects.count()} programmes')

    def seed_units(self):
        """Create units and programme units"""
        self.stdout.write('Seeding units...')

        dept_cs = Department.objects.get(code='CS')
        dept_it = Department.objects.get(code='IT')
        ay_2024 = AcademicYear.objects.get(name='2024/2025')

        units_data = [
            # Year 1 Semester 1 Units
            {'code': 'CSC101', 'name': 'Introduction to Computer Science', 'department': dept_cs, 
             'level': '100', 'credits': 3},
            {'code': 'CSC102', 'name': 'Programming Fundamentals', 'department': dept_cs, 
             'level': '100', 'credits': 4},
            {'code': 'MAT101', 'name': 'Calculus I', 'department': dept_cs, 
             'level': '100', 'credits': 3},
            {'code': 'CSC103', 'name': 'Digital Logic Design', 'department': dept_cs, 
             'level': '100', 'credits': 3},
            
            # Year 1 Semester 2 Units
            {'code': 'CSC104', 'name': 'Data Structures and Algorithms', 'department': dept_cs, 
             'level': '100', 'credits': 4},
            {'code': 'CSC105', 'name': 'Object Oriented Programming', 'department': dept_cs, 
             'level': '100', 'credits': 4},
            {'code': 'MAT102', 'name': 'Discrete Mathematics', 'department': dept_cs, 
             'level': '100', 'credits': 3},
            
            # Year 2 Units
            {'code': 'CSC201', 'name': 'Database Management Systems', 'department': dept_cs, 
             'level': '200', 'credits': 4},
            {'code': 'CSC202', 'name': 'Software Engineering', 'department': dept_cs, 
             'level': '200', 'credits': 3},
            {'code': 'CSC203', 'name': 'Computer Networks', 'department': dept_cs, 
             'level': '200', 'credits': 3},
            {'code': 'CSC204', 'name': 'Web Development', 'department': dept_cs, 
             'level': '200', 'credits': 3},
            
            # IT Units
            {'code': 'ITE101', 'name': 'Introduction to Information Technology', 'department': dept_it, 
             'level': '100', 'credits': 3},
            {'code': 'ITE102', 'name': 'Computer Hardware and Software', 'department': dept_it, 
             'level': '100', 'credits': 3},
            {'code': 'ITE201', 'name': 'Network Administration', 'department': dept_it, 
             'level': '200', 'credits': 4},
            {'code': 'ITE202', 'name': 'IT Project Management', 'department': dept_it, 
             'level': '200', 'credits': 3},
        ]

        for unit_data in units_data:
            unit, created = Unit.objects.get_or_create(
                code=unit_data['code'],
                defaults={
                    'name': unit_data['name'],
                    'department': unit_data['department'],
                    'unit_level': unit_data['level'],
                    'credit_hours': unit_data['credits']
                }
            )

            # Create grading system for each unit
            if created:
                grades = [
                    ('A', 70, 100, 4.0, 'Excellent', True),
                    ('B', 60, 69, 3.0, 'Very Good', True),
                    ('C', 50, 59, 2.0, 'Good', True),
                    ('D', 40, 49, 1.0, 'Pass', True),
                    ('E', 0, 39, 0.0, 'Fail', False),
                ]
                
                for grade, min_m, max_m, gp, desc, is_pass in grades:
                    UnitGradingSystem.objects.create(
                        unit=unit,
                        grade=grade,
                        min_marks=Decimal(str(min_m)),
                        max_marks=Decimal(str(max_m)),
                        grade_point=Decimal(str(gp)),
                        description=desc,
                        is_pass=is_pass
                    )

        # Assign units to programmes
        prog_cs = Programme.objects.get(code='BSCCS')
        prog_it = Programme.objects.get(code='BSCIT')

        # Year 1 Semester 1 for CS
        for unit_code in ['CSC101', 'CSC102', 'MAT101', 'CSC103']:
            unit = Unit.objects.get(code=unit_code)
            ProgrammeUnit.objects.get_or_create(
                programme=prog_cs,
                unit=unit,
                academic_year=ay_2024,
                year_of_study=1,
                semester_number='1',
                defaults={'unit_type': 'core'}
            )

        # Year 1 Semester 2 for CS
        for unit_code in ['CSC104', 'CSC105', 'MAT102']:
            unit = Unit.objects.get(code=unit_code)
            ProgrammeUnit.objects.get_or_create(
                programme=prog_cs,
                unit=unit,
                academic_year=ay_2024,
                year_of_study=1,
                semester_number='2',
                defaults={'unit_type': 'core'}
            )

        # Year 2 Semester 1 for CS
        for unit_code in ['CSC201', 'CSC202', 'CSC203']:
            unit = Unit.objects.get(code=unit_code)
            ProgrammeUnit.objects.get_or_create(
                programme=prog_cs,
                unit=unit,
                academic_year=ay_2024,
                year_of_study=2,
                semester_number='1',
                defaults={'unit_type': 'core'}
            )

        # Year 1 for IT
        for unit_code in ['ITE101', 'ITE102', 'CSC102']:
            unit = Unit.objects.get(code=unit_code)
            ProgrammeUnit.objects.get_or_create(
                programme=prog_it,
                unit=unit,
                academic_year=ay_2024,
                year_of_study=1,
                semester_number='1',
                defaults={'unit_type': 'core'}
            )

        self.stdout.write(f'  Created {Unit.objects.count()} units')
        self.stdout.write(f'  Created {ProgrammeUnit.objects.count()} programme units')

    def seed_lecturers(self):
        """Create lecturers"""
        self.stdout.write('Seeding lecturers...')

        dept_cs = Department.objects.get(code='CS')
        dept_it = Department.objects.get(code='IT')

        lecturers_data = [
            {'username': 'lec_njoroge', 'first_name': 'James', 'last_name': 'Njoroge', 
             'email': 'j.njoroge@mut.ac.ke', 'employee_number': 'LEC001', 
             'department': dept_cs, 'designation': 'senior_lecturer', 
             'qualification': 'PhD in Computer Science'},
            {'username': 'lec_wangari', 'first_name': 'Lucy', 'last_name': 'Wangari', 
             'email': 'l.wangari@mut.ac.ke', 'employee_number': 'LEC002', 
             'department': dept_cs, 'designation': 'lecturer', 
             'qualification': 'MSc in Software Engineering'},
            {'username': 'lec_otieno', 'first_name': 'Michael', 'last_name': 'Otieno', 
             'email': 'm.otieno@mut.ac.ke', 'employee_number': 'LEC003', 
             'department': dept_it, 'designation': 'lecturer', 
             'qualification': 'MSc in Information Technology'},
            {'username': 'lec_mwangi', 'first_name': 'Catherine', 'last_name': 'Mwangi', 
             'email': 'c.mwangi@mut.ac.ke', 'employee_number': 'LEC004', 
             'department': dept_cs, 'designation': 'assistant_lecturer', 
             'qualification': 'BSc in Computer Science'},
        ]

        for lec_data in lecturers_data:
            user, created = User.objects.get_or_create(
                username=lec_data['username'],
                defaults={
                    'first_name': lec_data['first_name'],
                    'last_name': lec_data['last_name'],
                    'email': lec_data['email'],
                    'role': 'lecturer',
                    'is_staff': True
                }
            )
            if created:
                user.set_password('password123')
                user.save()

            Lecturer.objects.get_or_create(
                user=user,
                defaults={
                    'employee_number': lec_data['employee_number'],
                    'department': lec_data['department'],
                    'designation': lec_data['designation'],
                    'qualification': lec_data['qualification'],
                    'hire_date': date(2020, 1, 1)
                }
            )

        # Allocate units to lecturers
        sem1_2024 = Semester.objects.get(academic_year__name='2024/2025', semester_number='1')
        lec_njoroge = User.objects.get(username='lec_njoroge')
        lec_wangari = User.objects.get(username='lec_wangari')
        hod_cs = User.objects.get(username='hod_cs')

        # Allocate CSC101 and CSC102 to lecturers
        prog_units = ProgrammeUnit.objects.filter(
            unit__code__in=['CSC101', 'CSC102', 'CSC103']
        )[:3]

        for i, prog_unit in enumerate(prog_units):
            lecturer = lec_njoroge if i % 2 == 0 else lec_wangari
            UnitAllocation.objects.get_or_create(
                programme_unit=prog_unit,
                semester=sem1_2024,
                lecturer=lecturer,
                defaults={
                    'assigned_by': hod_cs,
                    'status': 'approved_dean',
                    'max_students': 60
                }
            )

        self.stdout.write(f'  Created {Lecturer.objects.count()} lecturers')
        self.stdout.write(f'  Created {UnitAllocation.objects.count()} unit allocations')

    def seed_students(self):
        """Create students"""
        self.stdout.write('Seeding students...')

        prog_cs = Programme.objects.get(code='BSCCS')
        prog_it = Programme.objects.get(code='BSCIT')
        intake_sep = Intake.objects.get(intake_number='SEP/2024')
        sem1_2024 = Semester.objects.get(academic_year__name='2024/2025', semester_number='1')

        # Create sample students
        students_data = [
            {'reg_no': 'SC211/0530/2022', 'first_name': 'Brian', 'last_name': 'Ochieng', 
             'programme': prog_cs, 'year': 2, 'gender': 'M'},
            {'reg_no': 'SC211/0531/2022', 'first_name': 'Faith', 'last_name': 'Auma', 
             'programme': prog_cs, 'year': 2, 'gender': 'F'},
            {'reg_no': 'SC211/0532/2023', 'first_name': 'Kevin', 'last_name': 'Maina', 
             'programme': prog_cs, 'year': 1, 'gender': 'M'},
            {'reg_no': 'SC211/0533/2023', 'first_name': 'Susan', 'last_name': 'Nyambura', 
             'programme': prog_cs, 'year': 1, 'gender': 'F'},
            {'reg_no': 'IT211/0100/2024', 'first_name': 'John', 'last_name': 'Kiplagat', 
             'programme': prog_it, 'year': 1, 'gender': 'M'},
            {'reg_no': 'IT211/0101/2024', 'first_name': 'Mary', 'last_name': 'Wambui', 
             'programme': prog_it, 'year': 1, 'gender': 'F'},
        ]

        for std_data in students_data:
            user, created = User.objects.get_or_create(
                username=std_data['reg_no'].replace('/', '_').lower(),
                defaults={
                    'first_name': std_data['first_name'],
                    'last_name': std_data['last_name'],
                    'email': f"{std_data['reg_no'].replace('/', '_').lower()}@students.mut.ac.ke",
                    'role': 'student'
                }
            )
            if created:
                user.set_password('password123')
                user.save()

            student, created = Student.objects.get_or_create(
                registration_number=std_data['reg_no'],
                defaults={
                    'user': user,
                    'programme': std_data['programme'],
                    'intake': intake_sep,
                    'current_year': std_data['year'],
                    'current_semester': '1',
                    'gender': std_data['gender'],
                    'date_of_birth': date(2002, 1, 1),
                    'national_id': f"3000000{random.randint(100, 999)}",
                    'admission_date': date(2024, 9, 1),
                    'student_status': 'active',
                    'cumulative_gpa': Decimal('3.5')
                }
            )

            # Register students for units
            if student.current_year == 1:
                unit_codes = ['CSC101', 'CSC102', 'MAT101', 'CSC103']
            else:
                unit_codes = ['CSC201', 'CSC202', 'CSC203']

            for unit_code in unit_codes:
                prog_unit = ProgrammeUnit.objects.filter(
                    programme=student.programme,
                    unit__code=unit_code,
                    year_of_study=student.current_year
                ).first()

                if prog_unit:
                    UnitRegistration.objects.get_or_create(
                        student=student,
                        programme_unit=prog_unit,
                        semester=sem1_2024,
                        defaults={'status': 'registered'}
                    )

        self.stdout.write(f'  Created {Student.objects.count()} students')
        self.stdout.write(f'  Created {UnitRegistration.objects.count()} unit registrations')

    def seed_fees(self):
        """Create fee structures and payments"""
        self.stdout.write('Seeding fee structures and payments...')

        prog_cs = Programme.objects.get(code='BSCCS')
        ay_2024 = AcademicYear.objects.get(name='2024/2025')

        # Create fee structure
        for year in [1, 2, 3, 4]:
            for sem in ['1', '2']:
                FeeStructure.objects.get_or_create(
                    programme=prog_cs,
                    academic_year=ay_2024,
                    year_of_study=year,
                    semester_number=sem,
                    defaults={
                        'tuition_fee': Decimal('45000.00'),
                        'activity_fee': Decimal('5000.00'),
                        'examination_fee': Decimal('3000.00'),
                        'library_fee': Decimal('2000.00'),
                        'medical_fee': Decimal('2000.00'),
                        'technology_fee': Decimal('3000.00'),
                    }
                )

        # Create sample payments
        students = Student.objects.all()[:3]
        sem1_2024 = Semester.objects.get(academic_year__name='2024/2025', semester_number='1')
        finance_officer = User.objects.get(username='finance_officer')

        for student in students:
            fee_structure = FeeStructure.objects.filter(
                programme=student.programme,
                academic_year=ay_2024,
                year_of_study=student.current_year,
                semester_number='1'
            ).first()

            if fee_structure:
                # Create payment
                payment = FeePayment.objects.create(
                    student=student,
                    semester=sem1_2024,
                    academic_year=ay_2024,
                    fee_structure=fee_structure,
                    amount=Decimal('30000.00'),
                    payment_method='mpesa',
                    transaction_reference=f'MPE{random.randint(10000, 99999)}',
                    payment_date=timezone.now(),
                    status='completed',
                    receipt_number=f'REC{random.randint(1000, 9999)}',
                    processed_by=finance_officer
                )

                # Create fee balance
                FeeBalance.objects.create(
                    student=student,
                    semester=sem1_2024,
                    academic_year=ay_2024,
                    total_fees=fee_structure.total_fee,
                    amount_paid=Decimal('30000.00'),
                    last_payment_date=timezone.now()
                )

        self.stdout.write(f'  Created {FeeStructure.objects.count()} fee structures')
        self.stdout.write(f'  Created {FeePayment.objects.count()} fee payments')

    def seed_hostels(self):
        """Create hostels and allocations"""
        self.stdout.write('Seeding hostels...')

        warden = User.objects.get(username='hostel_warden')
        ay_2024 = AcademicYear.objects.get(name='2024/2025')
        sem1_2024 = Semester.objects.get(academic_year__name='2024/2025', semester_number='1')

        # Create hostels
        hostel_boys, _ = Hostel.objects.get_or_create(
            code='HB01',
            defaults={
                'name': 'MUT Boys Hostel Block A',
                'gender_type': 'M',
                'warden': warden,
                'total_capacity': 120,
                'location': 'Campus South',
                'amenities': 'WiFi, Kitchen, Laundry, Study Room'
            }
        )

        hostel_girls, _ = Hostel.objects.get_or_create(
            code='HG01',
            defaults={
                'name': 'MUT Girls Hostel Block B',
                'gender_type': 'F',
                'warden': warden,
                'total_capacity': 100,
                'location': 'Campus North',
                'amenities': 'WiFi, Kitchen, Laundry, Study Room'
            }
        )

        # Create rooms and beds
        for hostel in [hostel_boys, hostel_girls]:
            for floor in range(1, 4):  # 3 floors
                for room_num in range(1, 11):  # 10 rooms per floor
                    room, created = HostelRoom.objects.get_or_create(
                        hostel=hostel,
                        room_number=f'{floor}0{room_num}',
                        defaults={
                            'floor': floor,
                            'room_type': 'double',
                            'capacity': 2,
                            'has_bathroom': True
                        }
                    )

                    if created:
                        # Create beds for the room
                        for bed_num in ['A', 'B']:
                            HostelBed.objects.create(
                                room=room,
                                bed_number=bed_num,
                                academic_year=ay_2024,
                                status='available'
                            )

        # Create hostel fee structure
        for hostel in [hostel_boys, hostel_girls]:
            HostelFeeStructure.objects.get_or_create(
                hostel=hostel,
                room_type='double',
                academic_year=ay_2024,
                semester=sem1_2024,
                defaults={
                    'fee_amount': Decimal('15000.00'),
                    'booking_fee': Decimal('2000.00'),
                    'security_deposit': Decimal('3000.00')
                }
            )

        # Allocate some students to hostels
        male_students = Student.objects.filter(gender='M')[:5]
        female_students = Student.objects.filter(gender='F')[:5]

        for student in male_students:
            bed = HostelBed.objects.filter(
                room__hostel=hostel_boys,
                status='available',
                academic_year=ay_2024
            ).first()

            if bed:
                HostelAllocation.objects.create(
                    student=student,
                    bed=bed,
                    academic_year=ay_2024,
                    semester=sem1_2024,
                    check_in_date=timezone.now(),
                    is_active=True,
                    fee_paid=True,
                    allocated_by=warden
                )
                bed.status = 'occupied'
                bed.save()

        for student in female_students:
            bed = HostelBed.objects.filter(
                room__hostel=hostel_girls,
                status='available',
                academic_year=ay_2024
            ).first()

            if bed:
                HostelAllocation.objects.create(
                    student=student,
                    bed=bed,
                    academic_year=ay_2024,
                    semester=sem1_2024,
                    check_in_date=timezone.now(),
                    is_active=True,
                    fee_paid=True,
                    allocated_by=warden
                )
                bed.status = 'occupied'
                bed.save()

        self.stdout.write(f'  Created {Hostel.objects.count()} hostels')
        self.stdout.write(f'  Created {HostelRoom.objects.count()} rooms')
        self.stdout.write(f'  Created {HostelBed.objects.count()} beds')
        self.stdout.write(f'  Created {HostelAllocation.objects.count()} allocations')

    def seed_library(self):
        """Create library books and borrowings"""
        self.stdout.write('Seeding library...')

        # Create book categories
        cat_cs, _ = BookCategory.objects.get_or_create(
            code='CS',
            defaults={'name': 'Computer Science'}
        )
        cat_prog, _ = BookCategory.objects.get_or_create(
            code='PROG',
            defaults={'name': 'Programming', 'parent_category': cat_cs}
        )
        cat_db, _ = BookCategory.objects.get_or_create(
            code='DB',
            defaults={'name': 'Databases', 'parent_category': cat_cs}
        )

        # Create books
        books_data = [
            {'isbn': '978-0134685991', 'title': 'Effective Java', 'author': 'Joshua Bloch',
             'category': cat_prog, 'copies': 5},
            {'isbn': '978-0132350884', 'title': 'Clean Code', 'author': 'Robert C. Martin',
             'category': cat_prog, 'copies': 8},
            {'isbn': '978-0596009205', 'title': 'Head First Design Patterns', 
             'author': 'Eric Freeman', 'category': cat_cs, 'copies': 6},
            {'isbn': '978-0201633610', 'title': 'Design Patterns', 
             'author': 'Gang of Four', 'category': cat_cs, 'copies': 4},
            {'isbn': '978-0321573513', 'title': 'Database System Concepts', 
             'author': 'Abraham Silberschatz', 'category': cat_db, 'copies': 10},
            {'isbn': '978-0134757599', 'title': 'Database Management Systems', 
             'author': 'Raghu Ramakrishnan', 'category': cat_db, 'copies': 7},
        ]

        for book_data in books_data:
            Book.objects.get_or_create(
                isbn=book_data['isbn'],
                defaults={
                    'title': book_data['title'],
                    'author': book_data['author'],
                    'category': book_data['category'],
                    'total_copies': book_data['copies'],
                    'available_copies': book_data['copies'],
                    'publisher': 'Pearson Education',
                    'publication_year': 2020,
                    'shelf_location': f"A{random.randint(1, 50)}"
                }
            )

        # Create borrowings
        students = Student.objects.all()[:3]
        books = Book.objects.all()[:3]
        librarian = User.objects.get(username='librarian')
        ay_2024 = AcademicYear.objects.get(name='2024/2025')
        sem1_2024 = Semester.objects.get(academic_year__name='2024/2025', semester_number='1')

        for i, student in enumerate(students):
            book = books[i]
            BookBorrowing.objects.create(
                student=student,
                book=book,
                academic_year=ay_2024,
                semester=sem1_2024,
                due_date=date.today() + timedelta(days=14),
                status='active',
                issued_by=librarian
            )
            book.available_copies -= 1
            book.save()

        self.stdout.write(f'  Created {BookCategory.objects.count()} book categories')
        self.stdout.write(f'  Created {Book.objects.count()} books')
        self.stdout.write(f'  Created {BookBorrowing.objects.count()} borrowings')

    def seed_timetables(self):
        """Create timetables"""
        self.stdout.write('Seeding timetables...')

        prog_cs = Programme.objects.get(code='BSCCS')
        ay_2024 = AcademicYear.objects.get(name='2024/2025')
        sem1_2024 = Semester.objects.get(academic_year__name='2024/2025', semester_number='1')
        hod_cs = User.objects.get(username='hod_cs')

        # Create timetable
        timetable, _ = Timetable.objects.get_or_create(
            programme=prog_cs,
            academic_year=ay_2024,
            semester=sem1_2024,
            year_of_study=1,
            defaults={
                'name': 'BSC CS Year 1 Sem 1 - 2024/2025',
                'is_published': True,
                'published_date': timezone.now(),
                'created_by': hod_cs,
                'approved_by': hod_cs
            }
        )

        # Create timetable slots
        allocations = UnitAllocation.objects.filter(semester=sem1_2024)
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
        times = [
            ('08:00', '10:00'),
            ('10:00', '12:00'),
            ('14:00', '16:00'),
            ('16:00', '18:00')
        ]
        venues = ['LH1', 'LH2', 'Lab A', 'Lab B', 'Room 201']

        for i, allocation in enumerate(allocations[:5]):
            TimetableSlot.objects.get_or_create(
                timetable=timetable,
                unit_allocation=allocation,
                defaults={
                    'day_of_week': days[i % len(days)],
                    'start_time': times[i % len(times)][0],
                    'end_time': times[i % len(times)][1],
                    'slot_type': 'lecture',
                    'venue': venues[i % len(venues)],
                    'venue_capacity': 60
                }
            )

        self.stdout.write(f'  Created {Timetable.objects.count()} timetables')
        self.stdout.write(f'  Created {TimetableSlot.objects.count()} timetable slots')

    def seed_assessments(self):
        """Create assessments and marks"""
        self.stdout.write('Seeding assessments and marks...')

        allocations = UnitAllocation.objects.filter(
            semester__academic_year__name='2024/2025',
            semester__semester_number='1'
        )[:3]

        for allocation in allocations:
            # Create CAT 1
            cat1, _ = Assessment.objects.get_or_create(
                unit_allocation=allocation,
                assessment_type='cat1',
                defaults={
                    'title': f'CAT 1 - {allocation.programme_unit.unit.name}',
                    'max_marks': Decimal('30.00'),
                    'weight_percentage': Decimal('10.00'),
                    'date': date.today() + timedelta(days=30),
                    'duration_minutes': 60,
                    'venue': 'LH1',
                    'is_published': True
                }
            )

            # Create CAT 2
            cat2, _ = Assessment.objects.get_or_create(
                unit_allocation=allocation,
                assessment_type='cat2',
                defaults={
                    'title': f'CAT 2 - {allocation.programme_unit.unit.name}',
                    'max_marks': Decimal('30.00'),
                    'weight_percentage': Decimal('10.00'),
                    'date': date.today() + timedelta(days=60),
                    'duration_minutes': 60,
                    'venue': 'LH2',
                    'is_published': False
                }
            )

            # Create Final Exam
            final, _ = Assessment.objects.get_or_create(
                unit_allocation=allocation,
                assessment_type='final',
                defaults={
                    'title': f'Final Exam - {allocation.programme_unit.unit.name}',
                    'max_marks': Decimal('70.00'),
                    'weight_percentage': Decimal('70.00'),
                    'date': date.today() + timedelta(days=90),
                    'duration_minutes': 180,
                    'venue': 'Exam Hall',
                    'is_published': False
                }
            )

            # Create marks for students
            registrations = UnitRegistration.objects.filter(
                programme_unit=allocation.programme_unit,
                semester=allocation.semester
            )

            for registration in registrations:
                StudentMarks.objects.get_or_create(
                    assessment=cat1,
                    student=registration.student,
                    defaults={
                        'marks_obtained': Decimal(str(random.randint(15, 30))),
                        'attendance': True,
                        'status': 'published',
                        'submitted_by': allocation.lecturer
                    }
                )

        self.stdout.write(f'  Created {Assessment.objects.count()} assessments')
        self.stdout.write(f'  Created {StudentMarks.objects.count()} marks records')

    def seed_communication(self):
        """Create announcements, events, and messages"""
        self.stdout.write('Seeding communication...')

        registrar = User.objects.get(username='registrar')
        ay_2024 = AcademicYear.objects.get(name='2024/2025')

        # Create announcements
        announcements_data = [
            {
                'title': 'Semester Registration Deadline',
                'content': 'All students are required to complete their unit registration by September 15, 2024.',
                'announcement_type': 'deadline',
                'target_audience': 'students'
            },
            {
                'title': 'Library Opening Hours Extended',
                'content': 'The library will now be open until 10 PM on weekdays to accommodate students.',
                'announcement_type': 'general',
                'target_audience': 'all'
            },
            {
                'title': 'Fee Payment Reminder',
                'content': 'Students with pending fee balances are reminded to clear their fees by end of month.',
                'announcement_type': 'urgent',
                'target_audience': 'students'
            },
        ]

        for ann_data in announcements_data:
            Announcement.objects.get_or_create(
                title=ann_data['title'],
                defaults={
                    'content': ann_data['content'],
                    'announcement_type': ann_data['announcement_type'],
                    'target_audience': ann_data['target_audience'],
                    'academic_year': ay_2024,
                    'is_published': True,
                    'publish_date': timezone.now(),
                    'created_by': registrar,
                    'is_pinned': ann_data['announcement_type'] == 'urgent'
                }
            )

        # Create events
        events_data = [
            {
                'title': 'Freshers Orientation Week',
                'description': 'Welcome program for new students joining the university.',
                'event_type': 'academic',
                'venue': 'Main Auditorium',
                'start_date': timezone.now() + timedelta(days=7),
                'end_date': timezone.now() + timedelta(days=11)
            },
            {
                'title': 'Career Fair 2024',
                'description': 'Annual career fair featuring top employers in the tech industry.',
                'event_type': 'career',
                'venue': 'Sports Complex',
                'start_date': timezone.now() + timedelta(days=30),
                'end_date': timezone.now() + timedelta(days=32)
            },
            {
                'title': 'ICT Innovation Summit',
                'description': 'Showcase of student projects and innovations in technology.',
                'event_type': 'academic',
                'venue': 'SCIT Block',
                'start_date': timezone.now() + timedelta(days=45),
                'end_date': timezone.now() + timedelta(days=45)
            },
        ]

        for event_data in events_data:
            Event.objects.get_or_create(
                title=event_data['title'],
                defaults={
                    'description': event_data['description'],
                    'event_type': event_data['event_type'],
                    'venue': event_data['venue'],
                    'start_date': event_data['start_date'],
                    'end_date': event_data['end_date'],
                    'academic_year': ay_2024,
                    'registration_required': True,
                    'max_participants': 200,
                    'organizer': registrar,
                    'is_published': True
                }
            )

        # Create messages
        students = Student.objects.all()[:2]
        hod_cs = User.objects.get(username='hod_cs')

        for student in students:
            Message.objects.create(
                sender=student.user,
                recipient=hod_cs,
                category='academic',
                subject='Request for Unit Registration Extension',
                message='Dear HOD, I would like to request an extension for unit registration due to...',
                status='pending',
                priority=False
            )

        self.stdout.write(f'  Created {Announcement.objects.count()} announcements')
        self.stdout.write(f'  Created {Event.objects.count()} events')
        self.stdout.write(f'  Created {Message.objects.count()} messages')

    def seed_procurement(self):
        """Create procurement data"""
        self.stdout.write('Seeding procurement...')

        dept_cs = Department.objects.get(code='CS')
        ay_2024 = AcademicYear.objects.get(name='2024/2025')
        hod_cs = User.objects.get(username='hod_cs')

        # Create suppliers
        suppliers_data = [
            {
                'name': 'Tech Solutions Ltd',
                'supplier_code': 'SUP001',
                'contact_person': 'John Doe',
                'email': 'john@techsolutions.co.ke',
                'phone_number': '0700123456'
            },
            {
                'name': 'Office Supplies Co.',
                'supplier_code': 'SUP002',
                'contact_person': 'Jane Smith',
                'email': 'jane@officesupplies.co.ke',
                'phone_number': '0700123457'
            },
        ]

        for sup_data in suppliers_data:
            Supplier.objects.get_or_create(
                supplier_code=sup_data['supplier_code'],
                defaults={
                    'name': sup_data['name'],
                    'contact_person': sup_data['contact_person'],
                    'email': sup_data['email'],
                    'phone_number': sup_data['phone_number'],
                    'address': 'Nairobi, Kenya',
                    'rating': Decimal('4.5')
                }
            )

        # Create procurement categories
        cat_it, _ = ProcurementCategory.objects.get_or_create(
            code='IT',
            defaults={'name': 'IT Equipment'}
        )
        cat_office, _ = ProcurementCategory.objects.get_or_create(
            code='OFF',
            defaults={'name': 'Office Supplies'}
        )

        # Create purchase requisition
        requisition = PurchaseRequisition.objects.create(
            requisition_number=f'REQ/2024/{random.randint(100, 999)}',
            department=dept_cs,
            academic_year=ay_2024,
            requested_by=hod_cs,
            purpose='Purchase of computers for new computer lab',
            status='pending_hod'
        )

        # Create requisition items
        RequisitionItem.objects.create(
            requisition=requisition,
            category=cat_it,
            item_description='Desktop Computers (Intel Core i7, 16GB RAM, 512GB SSD)',
            quantity=30,
            unit_of_measure='pieces',
            estimated_unit_price=Decimal('75000.00'),
            specifications='HP ProDesk or equivalent'
        )

        RequisitionItem.objects.create(
            requisition=requisition,
            category=cat_it,
            item_description='27" LCD Monitors',
            quantity=30,
            unit_of_measure='pieces',
            estimated_unit_price=Decimal('15000.00'),
            specifications='Full HD, HDMI'
        )

        self.stdout.write(f'  Created {Supplier.objects.count()} suppliers')
        self.stdout.write(f'  Created {ProcurementCategory.objects.count()} categories')
        self.stdout.write(f'  Created {PurchaseRequisition.objects.count()} requisitions')
        self.stdout.write(f'  Created {RequisitionItem.objects.count()} requisition items')