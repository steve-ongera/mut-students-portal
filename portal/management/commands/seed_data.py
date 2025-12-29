"""
Django Management Command for Seeding Database
Save this file as: portal/management/commands/seed_data.py

Directory structure:
portal/
    management/
        __init__.py
        commands/
            __init__.py
            seed_data.py

Run with: python manage.py seed_data --clear
"""

from django.core.management.base import BaseCommand
from django.db import transaction
import random
from datetime import datetime, timedelta, date
from decimal import Decimal

from portal.models import *
from django.contrib.auth import get_user_model

User = get_user_model()

# Kenyan Names Data
KENYAN_FIRST_NAMES = [
    'Brian', 'Kevin', 'Dennis', 'Peter', 'John', 'James', 'David', 'Michael', 'Stephen',
    'Daniel', 'Samuel', 'Joseph', 'Isaac', 'Wesley', 'Emmanuel', 'Felix', 'Victor',
    'Martin', 'Nicholas', 'Edwin', 'Collins', 'Kenneth', 'Moses', 'Paul', 'Timothy',
    'Kelvin', 'Ian', 'Allan', 'Eric', 'Frank', 'George', 'Henry', 'Lewis',
    'Mary', 'Jane', 'Grace', 'Faith', 'Joy', 'Ann', 'Lucy', 'Sarah', 'Rebecca',
    'Ruth', 'Esther', 'Nancy', 'Christine', 'Catherine', 'Margaret', 'Rose', 'Alice',
    'Mercy', 'Beatrice', 'Violet', 'Carol', 'Diana', 'Elizabeth', 'Florence', 'Gladys',
    'Hannah', 'Irene', 'Janet', 'Joyce', 'Karen', 'Lilian', 'Monica', 'Naomi', 'Olive'
]

KENYAN_LAST_NAMES = [
    'Kamau', 'Mwangi', 'Otieno', 'Ochieng', 'Kimani', 'Njoroge', 'Wanjiku', 'Achieng',
    'Wambui', 'Nyambura', 'Mutua', 'Muthoni', 'Wairimu', 'Wangari', 'Kariuki', 'Kiprotich',
    'Kipchoge', 'Cheruiyot', 'Rotich', 'Koech', 'Chepkemoi', 'Jepkosgei', 'Njeri', 'Ndungu',
    'Ouma', 'Okoth', 'Akinyi', 'Onyango', 'Adhiambo', 'Awuor', 'Wekesa', 'Barasa', 'Nafula',
    'Simiyu', 'Juma', 'Mwende', 'Mutuku', 'Musyoka', 'Mueni', 'Kioko', 'Maina', 'Gathoni'
]

KENYAN_COUNTIES = [
    'Nairobi', 'Mombasa', 'Kisumu', 'Nakuru', 'Eldoret', 'Thika', 'Malindi', 'Kitale',
    'Garissa', 'Kakamega', 'Kisii', 'Nyeri', 'Meru', 'Machakos', 'Kiambu', 'Kajiado'
]


class Command(BaseCommand):
    help = 'Seeds the database with comprehensive test data for the University Management Portal'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing data before seeding',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('UNIVERSITY MANAGEMENT PORTAL - DATABASE SEEDING'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        
        if options['clear']:
            self.clear_database()
        
        try:
            with transaction.atomic():
                self.academic_years = self.create_academic_years()
                self.semesters = self.create_semesters()
                self.intakes = self.create_intakes()
                self.schools, self.departments = self.create_schools_and_departments()
                self.programmes = self.create_programmes()
                self.units = self.create_units()
                self.lecturers = self.create_lecturers()
                self.students = self.create_students()
                self.programme_units = self.create_programme_units()
                self.allocations = self.create_unit_allocations()
                self.registrations = self.create_unit_registrations()
                self.assessments, self.marks = self.create_assessments_and_marks()
                self.fee_structures = self.create_fee_structures()
                self.payments, self.balances = self.create_fee_payments()
            
            self.print_summary()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ ERROR: {str(e)}'))
            self.stdout.write(self.style.ERROR('Transaction rolled back. No changes were saved.'))
            raise

    def clear_database(self):
        """Clear all data from database"""
        self.stdout.write('\n[1/15] Clearing existing database...')
        
        # Delete in reverse order to avoid foreign key constraints
        models_to_clear = [
            UnitEnrollment, ResitExam, SemesterReport, EnrollmentPeriod,
            BookBorrowing, Book, BookCategory,
            HostelAllocation, HostelApplication, HostelBed, HostelRoom, 
            HostelFeeStructure, Hostel,
            Attendance, TimetableSlot, Timetable,
            SemesterGPA, SemesterResults, StudentMarks, Assessment,
            UnitRegistration, StudentProgression, Student,
            FeeBalance, FeePayment, FeeStructure,
            UnitAllocation, ProgrammeUnit, UnitGradingSystem, Unit,
            Lecturer, Programme, Department, School,
            Intake, Semester, AcademicYear,
        ]
        
        for model in models_to_clear:
            count = model.objects.count()
            if count > 0:
                model.objects.all().delete()
                self.stdout.write(f'  - Deleted {count} {model.__name__} records')
        
        # Delete users last (except superusers)
        user_count = User.objects.filter(is_superuser=False).count()
        if user_count > 0:
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(f'  - Deleted {user_count} User records')
        
        self.stdout.write(self.style.SUCCESS('  ✓ Database cleared'))

    def create_academic_years(self):
        """Create academic years 2020/2021 to 2025/2026"""
        self.stdout.write('\n[2/15] Creating Academic Years...')
        
        academic_years = []
        for year in range(2020, 2026):
            name = f"{year}/{year+1}"
            
            # Check if already exists
            existing = AcademicYear.objects.filter(name=name).first()
            if existing:
                academic_years.append(existing)
                marker = ' (Current)' if existing.is_current else ''
                self.stdout.write(f'  - Already exists: {existing.name}{marker}')
                continue
                
            ay = AcademicYear.objects.create(
                name=name,
                start_date=date(year, 9, 1),
                end_date=date(year+1, 8, 31),
                is_current=(year == 2024),
                is_active=True
            )
            academic_years.append(ay)
            marker = ' (Current)' if ay.is_current else ''
            self.stdout.write(f'  - Created: {ay.name}{marker}')
        
        return academic_years

    def create_semesters(self):
        """Create semesters for each academic year"""
        self.stdout.write('\n[3/15] Creating Semesters...')
        
        semesters = []
        for ay in self.academic_years:
            # Check if semesters already exist for this academic year
            existing_semesters = Semester.objects.filter(academic_year=ay)
            if existing_semesters.exists():
                semesters.extend(list(existing_semesters))
                self.stdout.write(f'  - Semesters already exist for {ay.name}')
                continue
            
            # Semester 1
            sem1 = Semester.objects.create(
                academic_year=ay,
                name=f"Semester 1 - {ay.name}",
                semester_number='1',
                start_date=ay.start_date,
                end_date=ay.start_date + timedelta(days=120),
                registration_start_date=ay.start_date - timedelta(days=14),
                registration_end_date=ay.start_date + timedelta(days=7),
                is_current=(ay.is_current and datetime.now().month >= 9),
                is_active=True
            )
            semesters.append(sem1)
            
            # Semester 2
            sem2 = Semester.objects.create(
                academic_year=ay,
                name=f"Semester 2 - {ay.name}",
                semester_number='2',
                start_date=sem1.end_date + timedelta(days=1),
                end_date=sem1.end_date + timedelta(days=121),
                registration_start_date=sem1.end_date - timedelta(days=7),
                registration_end_date=sem1.end_date + timedelta(days=7),
                is_current=(ay.is_current and datetime.now().month < 9),
                is_active=True
            )
            semesters.append(sem2)
            
            # Semester 3
            sem3 = Semester.objects.create(
                academic_year=ay,
                name=f"Semester 3 - {ay.name}",
                semester_number='3',
                start_date=sem2.end_date + timedelta(days=1),
                end_date=ay.end_date,
                registration_start_date=sem2.end_date - timedelta(days=7),
                registration_end_date=sem2.end_date + timedelta(days=7),
                is_current=False,
                is_active=True
            )
            semesters.append(sem3)
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ Created/Found {len(semesters)} semesters'))
        return semesters

    def create_intakes(self):
        """Create intakes"""
        self.stdout.write('\n[4/15] Creating Intakes...')
        
        intakes = []
        months_data = [
            ('september', 'SEP', 9),
            ('january', 'JAN', 1),
            ('may', 'MAY', 5)
        ]
        
        for ay in self.academic_years:
            for month, code, month_num in months_data:
                year = ay.start_date.year if month_num >= 9 else ay.start_date.year + 1
                start_date = date(year, month_num, 1)
                
                # Check if intake already exists
                intake_number = f"{code}/{year}"
                existing = Intake.objects.filter(intake_number=intake_number).first()
                if existing:
                    intakes.append(existing)
                    continue
                
                intake = Intake.objects.create(
                    academic_year=ay,
                    name=f"{month.capitalize()} {year} Intake",
                    month=month,
                    intake_number=intake_number,
                    start_date=start_date,
                    application_deadline=start_date - timedelta(days=30),
                    is_active=True
                )
                intakes.append(intake)
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {len(intakes)} intakes'))
        return intakes

    def create_schools_and_departments(self):
        """Create schools and departments"""
        self.stdout.write('\n[5/15] Creating Schools and Departments...')
        
        schools_data = [
            {
                'name': 'School of Computing and Information Technology',
                'code': 'SCIT',
                'departments': [
                    {'name': 'Computer Science', 'code': 'CS'},
                    {'name': 'Information Technology', 'code': 'IT'},
                    {'name': 'Software Engineering', 'code': 'SE'},
                ]
            },
            {
                'name': 'School of Engineering',
                'code': 'SENG',
                'departments': [
                    {'name': 'Civil Engineering', 'code': 'CE'},
                    {'name': 'Electrical Engineering', 'code': 'EE'},
                    {'name': 'Mechanical Engineering', 'code': 'ME'},
                ]
            },
            {
                'name': 'School of Medicine and Health Sciences',
                'code': 'SMHS',
                'departments': [
                    {'name': 'Medicine and Surgery', 'code': 'MED'},
                    {'name': 'Nursing', 'code': 'NUR'},
                    {'name': 'Public Health', 'code': 'PH'},
                ]
            },
            {
                'name': 'School of Education',
                'code': 'SEDU',
                'departments': [
                    {'name': 'Educational Management', 'code': 'EDM'},
                    {'name': 'Curriculum Studies', 'code': 'CUR'},
                ]
            },
            {
                'name': 'School of Law',
                'code': 'SLAW',
                'departments': [
                    {'name': 'Private Law', 'code': 'PRL'},
                    {'name': 'Public Law', 'code': 'PUL'},
                ]
            },
            {
                'name': 'School of Business and Economics',
                'code': 'SBE',
                'departments': [
                    {'name': 'Business Administration', 'code': 'BA'},
                    {'name': 'Economics', 'code': 'ECON'},
                ]
            }
        ]
        
        schools = []
        departments = []
        
        for school_data in schools_data:
            # Check if school exists
            school, created = School.objects.get_or_create(
                code=school_data['code'],
                defaults={
                    'name': school_data['name'],
                    'description': f"The {school_data['name']} offers world-class education and research.",
                    'is_active': True
                }
            )
            schools.append(school)
            
            if created:
                self.stdout.write(f"  - Created School: {school.code}")
            else:
                self.stdout.write(f"  - Found School: {school.code}")
            
            for dept_data in school_data['departments']:
                # Check if department exists
                dept, created = Department.objects.get_or_create(
                    code=dept_data['code'],
                    school=school,
                    defaults={
                        'name': dept_data['name'],
                        'description': f"Department of {dept_data['name']}",
                        'is_active': True
                    }
                )
                departments.append(dept)
                
                if created:
                    self.stdout.write(f"    • Created Department: {dept.code}")
                else:
                    self.stdout.write(f"    • Found Department: {dept.code}")
        
        return schools, departments

    def create_programmes(self):
        """Create 20 programmes across departments"""
        self.stdout.write('\n[6/15] Creating Programmes...')
        
        programmes_data = [
            # Computing & IT
            {'name': 'Bachelor of Science in Computer Science', 'code': 'BSCS', 'dept_code': 'CS', 'type': 'degree', 'years': 4, 'semesters': 8, 'mode': 'full_time'},
            {'name': 'Bachelor of Science in Information Technology', 'code': 'BSIT', 'dept_code': 'IT', 'type': 'degree', 'years': 4, 'semesters': 8, 'mode': 'full_time'},
            {'name': 'Diploma in Information Technology', 'code': 'DIT', 'dept_code': 'IT', 'type': 'diploma', 'years': 3, 'semesters': 9, 'mode': 'full_time'},
            {'name': 'Bachelor of Science in Software Engineering', 'code': 'BSSE', 'dept_code': 'SE', 'type': 'degree', 'years': 4, 'semesters': 8, 'mode': 'full_time'},
            
            # Engineering
            {'name': 'Bachelor of Engineering in Civil Engineering', 'code': 'BECE', 'dept_code': 'CE', 'type': 'degree', 'years': 5, 'semesters': 10, 'mode': 'full_time'},
            {'name': 'Bachelor of Engineering in Electrical Engineering', 'code': 'BEEE', 'dept_code': 'EE', 'type': 'degree', 'years': 5, 'semesters': 10, 'mode': 'full_time'},
            {'name': 'Diploma in Mechanical Engineering', 'code': 'DME', 'dept_code': 'ME', 'type': 'diploma', 'years': 3, 'semesters': 9, 'mode': 'full_time'},
            
            # Medicine
            {'name': 'Bachelor of Medicine and Surgery', 'code': 'MBCHB', 'dept_code': 'MED', 'type': 'degree', 'years': 5, 'semesters': 15, 'mode': 'full_time'},
            {'name': 'Bachelor of Science in Nursing', 'code': 'BSCN', 'dept_code': 'NUR', 'type': 'degree', 'years': 4, 'semesters': 12, 'mode': 'full_time'},
            {'name': 'Diploma in Nursing', 'code': 'DN', 'dept_code': 'NUR', 'type': 'diploma', 'years': 3, 'semesters': 9, 'mode': 'full_time'},
            {'name': 'Bachelor of Public Health', 'code': 'BPH', 'dept_code': 'PH', 'type': 'degree', 'years': 4, 'semesters': 8, 'mode': 'full_time'},
            
            # Education
            {'name': 'Bachelor of Education Arts', 'code': 'BEDA', 'dept_code': 'EDM', 'type': 'degree', 'years': 4, 'semesters': 8, 'mode': 'full_time'},
            {'name': 'Bachelor of Education Science', 'code': 'BEDS', 'dept_code': 'CUR', 'type': 'degree', 'years': 4, 'semesters': 8, 'mode': 'full_time'},
            {'name': 'Diploma in Education', 'code': 'DED', 'dept_code': 'EDM', 'type': 'diploma', 'years': 3, 'semesters': 9, 'mode': 'full_time'},
            
            # Law
            {'name': 'Bachelor of Laws', 'code': 'LLB', 'dept_code': 'PRL', 'type': 'degree', 'years': 4, 'semesters': 8, 'mode': 'full_time'},
            
            # Business
            {'name': 'Bachelor of Commerce', 'code': 'BCOM', 'dept_code': 'BA', 'type': 'degree', 'years': 4, 'semesters': 8, 'mode': 'full_time'},
            {'name': 'Bachelor of Business Administration', 'code': 'BBA', 'dept_code': 'BA', 'type': 'degree', 'years': 4, 'semesters': 8, 'mode': 'full_time'},
            {'name': 'Diploma in Business Management', 'code': 'DBM', 'dept_code': 'BA', 'type': 'diploma', 'years': 3, 'semesters': 9, 'mode': 'full_time'},
            {'name': 'Bachelor of Economics', 'code': 'BECON', 'dept_code': 'ECON', 'type': 'degree', 'years': 4, 'semesters': 8, 'mode': 'full_time'},
            {'name': 'Diploma in Economics', 'code': 'DECON', 'dept_code': 'ECON', 'type': 'diploma', 'years': 3, 'semesters': 9, 'mode': 'full_time'},
        ]
        
        programmes = []
        dept_dict = {dept.code: dept for dept in self.departments}
        
        for prog_data in programmes_data:
            dept = dept_dict[prog_data['dept_code']]
            
            # Check if programme exists
            programme, created = Programme.objects.get_or_create(
                code=prog_data['code'],
                department=dept,
                defaults={
                    'name': prog_data['name'],
                    'programme_type': prog_data['type'],
                    'study_mode': prog_data['mode'],
                    'duration_years': prog_data['years'],
                    'total_semesters': prog_data['semesters'],
                    'min_credit_hours': 120 if prog_data['type'] == 'diploma' else 180,
                    'is_active': True
                }
            )
            programmes.append(programme)
            
            if created:
                self.stdout.write(f"  - Created: {programme.code} - {programme.name}")
            else:
                self.stdout.write(f"  - Found: {programme.code} - {programme.name}")
        
        return programmes

    def create_units(self):
        """Create comprehensive units for each department"""
        self.stdout.write('\n[7/15] Creating Units...')
        
        units_data = {
            'CS': [  # Computer Science
                ('CS101', 'Introduction to Programming', '100', 3),
                ('CS102', 'Data Structures', '100', 3),
                ('CS201', 'Object Oriented Programming', '200', 3),
                ('CS202', 'Database Systems', '200', 3),
                ('CS301', 'Software Engineering', '300', 3),
                ('CS302', 'Computer Networks', '300', 3),
                ('CS401', 'Artificial Intelligence', '400', 3),
                ('CS402', 'Machine Learning', '400', 3),
            ],
            'IT': [  # Information Technology
                ('IT101', 'Introduction to Computing', '100', 3),
                ('IT102', 'Computer Applications', '100', 3),
                ('IT201', 'Web Development', '200', 3),
                ('IT202', 'System Analysis and Design', '200', 3),
                ('IT301', 'Network Administration', '300', 3),
                ('IT302', 'Cyber Security', '300', 3),
                ('IT401', 'Cloud Computing', '400', 3),
                ('IT402', 'IT Project Management', '400', 3),
            ],
            'SE': [  # Software Engineering
                ('SE101', 'Programming Fundamentals', '100', 3),
                ('SE201', 'Software Design Patterns', '200', 3),
                ('SE301', 'Agile Development', '300', 3),
                ('SE401', 'DevOps Practices', '400', 3),
            ],
            'CE': [  # Civil Engineering
                ('CE101', 'Engineering Mathematics I', '100', 3),
                ('CE201', 'Structural Analysis', '200', 3),
                ('CE301', 'Concrete Technology', '300', 3),
                ('CE401', 'Highway Engineering', '400', 3),
            ],
            'EE': [  # Electrical Engineering
                ('EE101', 'Circuit Analysis', '100', 3),
                ('EE201', 'Electrical Machines', '200', 3),
                ('EE301', 'Power Systems', '300', 3),
                ('EE401', 'Control Systems', '400', 3),
            ],
            'ME': [  # Mechanical Engineering
                ('ME101', 'Engineering Drawing', '100', 3),
                ('ME201', 'Thermodynamics', '200', 3),
                ('ME301', 'Fluid Mechanics', '300', 3),
                ('ME401', 'Machine Design', '400', 3),
            ],
            'MED': [  # Medicine
                ('MED101', 'Anatomy I', '100', 4),
                ('MED102', 'Physiology I', '100', 4),
                ('MED201', 'Pathology', '200', 4),
                ('MED301', 'Pharmacology', '300', 4),
                ('MED401', 'Clinical Medicine', '400', 4),
            ],
            'NUR': [  # Nursing
                ('NUR101', 'Introduction to Nursing', '100', 3),
                ('NUR102', 'Human Anatomy', '100', 3),
                ('NUR201', 'Medical Nursing', '200', 3),
                ('NUR301', 'Community Health Nursing', '300', 3),
                ('NUR401', 'Critical Care Nursing', '400', 3),
            ],
            'PH': [  # Public Health
                ('PH101', 'Introduction to Public Health', '100', 3),
                ('PH201', 'Epidemiology', '200', 3),
                ('PH301', 'Health Policy', '300', 3),
                ('PH401', 'Global Health', '400', 3),
            ],
            'EDM': [  # Education Management
                ('EDM101', 'Foundations of Education', '100', 3),
                ('EDM201', 'Educational Psychology', '200', 3),
                ('EDM301', 'Educational Management', '300', 3),
                ('EDM401', 'Educational Leadership', '400', 3),
            ],
            'CUR': [  # Curriculum Studies
                ('CUR101', 'Curriculum Development', '100', 3),
                ('CUR201', 'Teaching Methods', '200', 3),
                ('CUR301', 'Assessment and Evaluation', '300', 3),
                ('CUR401', 'Instructional Technology', '400', 3),
            ],
            'PRL': [  # Private Law
                ('LAW101', 'Introduction to Law', '100', 3),
                ('LAW201', 'Contract Law', '200', 3),
                ('LAW301', 'Property Law', '300', 3),
                ('LAW401', 'Family Law', '400', 3),
            ],
            'PUL': [  # Public Law
                ('LAW102', 'Constitutional Law', '100', 3),
                ('LAW202', 'Administrative Law', '200', 3),
                ('LAW302', 'Criminal Law', '300', 3),
                ('LAW402', 'International Law', '400', 3),
            ],
            'BA': [  # Business Administration
                ('BA101', 'Introduction to Business', '100', 3),
                ('BA102', 'Financial Accounting', '100', 3),
                ('BA201', 'Marketing Management', '200', 3),
                ('BA301', 'Human Resource Management', '300', 3),
                ('BA401', 'Strategic Management', '400', 3),
            ],
            'ECON': [  # Economics
                ('ECON101', 'Microeconomics', '100', 3),
                ('ECON102', 'Macroeconomics', '100', 3),
                ('ECON201', 'Econometrics', '200', 3),
                ('ECON301', 'Development Economics', '300', 3),
                ('ECON401', 'International Economics', '400', 3),
            ],
        }
        
        # Common units across all programmes
        common_units = [
            ('COM101', 'Communication Skills', '100', 3),
            ('COM102', 'Critical Thinking', '100', 2),
            ('MAT101', 'Mathematics for Sciences', '100', 3),
            ('STA101', 'Introduction to Statistics', '100', 3),
            ('LAN101', 'Kiswahili', '100', 2),
            ('HIV101', 'HIV/AIDS Education', '100', 1),
            ('ENT101', 'Entrepreneurship', '100', 2),
        ]
        
        units = []
        dept_dict = {dept.code: dept for dept in self.departments}
        
        # Create department-specific units
        for dept_code, unit_list in units_data.items():
            if dept_code in dept_dict:
                dept = dept_dict[dept_code]
                for code, name, level, credits in unit_list:
                    # Check if unit exists
                    unit, created = Unit.objects.get_or_create(
                        code=code,
                        department=dept,
                        defaults={
                            'name': name,
                            'unit_level': level,
                            'credit_hours': credits,
                            'is_active': True
                        }
                    )
                    units.append(unit)
        
        # Create common units (assign to first department)
        first_dept = self.departments[0]
        for code, name, level, credits in common_units:
            unit, created = Unit.objects.get_or_create(
                code=code,
                department=first_dept,
                defaults={
                    'name': name,
                    'unit_level': level,
                    'credit_hours': credits,
                    'is_active': True
                }
            )
            units.append(unit)
        
        self.stdout.write(f"  ✓ Created/Found {len(units)} units")
        return units

    def create_lecturers(self):
        """Create 40 lecturers"""
        self.stdout.write('\n[8/15] Creating Lecturers...')
        
        designations = ['lecturer', 'senior_lecturer', 'associate_professor', 'professor', 'assistant_lecturer']
        qualifications = [
            'PhD in Computer Science',
            'PhD in Engineering',
            'PhD in Medicine',
            'PhD in Education',
            'PhD in Law',
            'PhD in Business Administration',
            'MSc in Computer Science',
            'MSc in Engineering',
            'MSc in Nursing',
            'MSc in Economics'
        ]
        
        lecturers = []
        for i in range(40):
            first_name = random.choice(KENYAN_FIRST_NAMES)
            last_name = random.choice(KENYAN_LAST_NAMES)
            email = f"{first_name.lower()}.{last_name.lower()}@university.ac.ke"
            username = f"lec{i+1:03d}"
            
            # Check if user exists
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': 'lecturer',
                    'phone_number': f"+2547{random.randint(10000000, 99999999)}",
                    'id_number': f"{random.randint(10000000, 39999999)}",
                    'is_active_user': True
                }
            )
            
            if created:
                user.set_password('password123')
                user.save()
            
            # Check if lecturer exists
            lecturer, created = Lecturer.objects.get_or_create(
                user=user,
                defaults={
                    'employee_number': f"LEC{i+1:03d}",
                    'department': random.choice(self.departments),
                    'designation': random.choice(designations),
                    'qualification': random.choice(qualifications),
                    'specialization': f"Specialized in {random.choice(['Research', 'Teaching', 'Consultation'])}",
                    'office_location': f"Block {random.choice(['A', 'B', 'C'])}, Room {random.randint(101, 350)}",
                    'consultation_hours': f"Monday & Wednesday: {random.randint(14, 16)}:00 - {random.randint(16, 18)}:00",
                    'hire_date': date(random.randint(2010, 2020), random.randint(1, 12), random.randint(1, 28)),
                    'is_active': True
                }
            )
            lecturers.append(lecturer)
            
            if created and (i + 1) % 10 == 0:
                self.stdout.write(f"  - Created {i + 1}/40 lecturers")
        
        self.stdout.write(f"  ✓ Created/Found {len(lecturers)} lecturers")
        return lecturers

    def create_students(self):
        """Create 2000 students with proper registration numbers"""
        self.stdout.write('\n[9/15] Creating Students...')
        
        students = []
        intake_dict = {intake.intake_number: intake for intake in self.intakes}
        
        # Student distribution across years
        students_per_year = {
            2020: 300,  # Graduated or final year
            2021: 350,
            2022: 450,
            2023: 450,
            2024: 450
        }
        
        student_id = 1
        for year, count in students_per_year.items():
            for i in range(count):
                first_name = random.choice(KENYAN_FIRST_NAMES)
                last_name = random.choice(KENYAN_LAST_NAMES)
                programme = random.choice(self.programmes)
                
                # Registration number format: SC211/0530/2022 (School Code/Number/Year)
                school_code = programme.department.school.code[:2]
                reg_num = f"{school_code}{programme.code[:3].upper()}/{student_id:04d}/{year}"
                username = reg_num.replace('/', '_')
                
                # Check if user exists
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': f"{first_name.lower()}.{last_name.lower()}{year}@students.university.ac.ke",
                        'first_name': first_name,
                        'last_name': last_name,
                        'role': 'student',
                        'phone_number': f"+2547{random.randint(10000000, 99999999)}",
                        'id_number': f"{random.randint(20000000, 39999999)}",
                        'is_active_user': True
                    }
                )
                
                if created:
                    user.set_password('password123')
                    user.save()
                
                # Determine current year and semester
                years_since_admission = 2024 - year
                if programme.total_semesters == 8:  # Double semester
                    current_semester_index = min(years_since_admission * 2 + 1, programme.total_semesters)
                else:  # Tri-semester
                    current_semester_index = min(years_since_admission * 3 + 1, programme.total_semesters)
                
                current_year = min((current_semester_index // 2) + 1, programme.duration_years) if programme.total_semesters == 8 else min((current_semester_index // 3) + 1, programme.duration_years)
                current_sem = str(((current_semester_index - 1) % 2) + 1) if programme.total_semesters == 8 else str(((current_semester_index - 1) % 3) + 1)
                
                # Student status
                if years_since_admission >= programme.duration_years:
                    status = 'graduated'
                elif random.random() < 0.05:
                    status = random.choice(['deferred', 'suspended'])
                else:
                    status = 'active'
                
                # Check if student exists
                student, created = Student.objects.get_or_create(
                    user=user,
                    defaults={
                        'registration_number': reg_num,
                        'programme': programme,
                        'intake': intake_dict.get(f"SEP/{year}", self.intakes[0]),
                        'current_year': current_year,
                        'current_semester': current_sem,
                        'gender': random.choice(['M', 'F']),
                        'date_of_birth': date(year - random.randint(18, 25), random.randint(1, 12), random.randint(1, 28)),
                        'national_id': user.id_number,
                        'admission_date': date(year, 9, 1),
                        'expected_graduation_date': date(year + programme.duration_years, 12, 15),
                        'student_status': status,
                        'cumulative_gpa': Decimal(str(random.uniform(2.0, 4.0))),
                        'total_credit_hours': random.randint(30, 120),
                        'emergency_contact_name': f"{random.choice(KENYAN_FIRST_NAMES)} {random.choice(KENYAN_LAST_NAMES)}",
                        'emergency_contact_phone': f"+2547{random.randint(10000000, 99999999)}",
                        'emergency_contact_relationship': random.choice(['Parent', 'Guardian', 'Sibling', 'Spouse']),
                        'permanent_address': f"{random.randint(1, 9999)} {random.choice(KENYAN_COUNTIES)}, Kenya",
                        'current_address': f"Room {random.randint(1, 500)}, Campus Hostel, Nairobi",
                    }
                )
                students.append(student)
                student_id += 1
                
                if created and student_id % 200 == 0:
                    self.stdout.write(f"  - Created {student_id}/2000 students")
        
        self.stdout.write(f"  ✓ Created/Found {len(students)} students")
        return students

    def create_programme_units(self):
        """Assign units to programmes by year and semester"""
        self.stdout.write('\n[10/15] Creating Programme Units...')
        
        programme_units = []
        
        # Get units by department
        units_by_dept = {}
        for unit in self.units:
            dept_code = unit.department.code
            if dept_code not in units_by_dept:
                units_by_dept[dept_code] = []
            units_by_dept[dept_code].append(unit)
        
        # Get common units
        common_units = [u for u in self.units if u.code.startswith('COM') or u.code.startswith('MAT') or 
                        u.code.startswith('STA') or u.code.startswith('LAN') or u.code.startswith('HIV') or 
                        u.code.startswith('ENT')]
        
        for programme in self.programmes:
            dept_code = programme.department.code
            dept_units = units_by_dept.get(dept_code, [])
            
            # Determine semester structure
            if programme.total_semesters == 8:  # Double semester - 4 years
                sems_per_year = 2
            elif programme.total_semesters == 9:  # Tri-semester diploma - 3 years
                sems_per_year = 3
            elif programme.total_semesters == 10:  # Double semester - 5 years
                sems_per_year = 2
            elif programme.total_semesters == 12:  # Tri-semester - 4 years
                sems_per_year = 3
            else:  # 15 semesters - 5 years tri-semester (Medicine)
                sems_per_year = 3
            
            for academic_year in self.academic_years:
                year_of_study = 1
                semester_count = 0
                
                while semester_count < programme.total_semesters:
                    semester_num = str((semester_count % sems_per_year) + 1)
                    
                    # Assign 5-6 units per semester
                    units_to_assign = []
                    
                    # Year 1 Semester 1: Include common units
                    if year_of_study == 1 and semester_num == '1':
                        units_to_assign.extend(random.sample(common_units, min(3, len(common_units))))
                        if dept_units:
                            units_to_assign.extend(random.sample(dept_units, min(3, len(dept_units))))
                    else:
                        if dept_units:
                            units_to_assign.extend(random.sample(dept_units, min(5, len(dept_units))))
                    
                    for unit in units_to_assign:
                        # Check if programme unit exists
                        pu, created = ProgrammeUnit.objects.get_or_create(
                            programme=programme,
                            unit=unit,
                            academic_year=academic_year,
                            year_of_study=year_of_study,
                            semester_number=semester_num,
                            defaults={
                                'unit_type': 'core' if unit not in common_units else 'common',
                                'is_active': True
                            }
                        )
                        programme_units.append(pu)
                    
                    semester_count += 1
                    if semester_count % sems_per_year == 0:
                        year_of_study += 1
        
        self.stdout.write(f"  ✓ Created/Found {len(programme_units)} programme units")
        return programme_units

    def create_unit_allocations(self):
        """Allocate lecturers to units"""
        self.stdout.write('\n[11/15] Creating Unit Allocations...')
        
        allocations = []
        
        # Group programme units by semester
        for semester in self.semesters[-6:]:  # Last 2 academic years (6 semesters)
            semester_pus = [pu for pu in self.programme_units if pu.academic_year == semester.academic_year]
            
            for pu in semester_pus[:200]:  # Allocate a subset
                # Find lecturer from same department
                dept_lecturers = [l for l in self.lecturers if l.department == pu.unit.department]
                if not dept_lecturers:
                    dept_lecturers = self.lecturers[:5]  # Fallback
                
                lecturer = random.choice(dept_lecturers)
                
                # Check if allocation exists
                allocation, created = UnitAllocation.objects.get_or_create(
                    programme_unit=pu,
                    semester=semester,
                    defaults={
                        'lecturer': lecturer.user,
                        'status': random.choice(['approved_dean', 'approved_hos', 'approved_hod']),
                        'max_students': random.randint(40, 100),
                    }
                )
                allocations.append(allocation)
        
        self.stdout.write(f"  ✓ Created/Found {len(allocations)} unit allocations")
        return allocations

    def create_unit_registrations(self):
        """Create unit registrations for students"""
        self.stdout.write('\n[12/15] Creating Unit Registrations...')
        
        registrations = []
        current_semester = [s for s in self.semesters if s.is_current]
        if current_semester:
            current_semester = current_semester[0]
        else:
            current_semester = self.semesters[-1]
        
        # Register active students in current semester
        active_students = [s for s in self.students if s.student_status == 'active'][:500]
        
        for student in active_students:
            # Get units for student's programme, year, and semester
            student_pus = [
                pu for pu in self.programme_units 
                if pu.programme == student.programme and
                pu.year_of_study == student.current_year and
                pu.semester_number == student.current_semester and
                pu.academic_year == current_semester.academic_year
            ]
            
            for pu in student_pus[:6]:  # Register for 6 units
                # Check if registration exists
                reg, created = UnitRegistration.objects.get_or_create(
                    student=student,
                    programme_unit=pu,
                    semester=current_semester,
                    defaults={
                        'status': 'registered',
                        'is_retake': random.random() < 0.05
                    }
                )
                registrations.append(reg)
        
        self.stdout.write(f"  ✓ Created/Found {len(registrations)} unit registrations")
        return registrations

    def create_assessments_and_marks(self):
        """Create assessments and student marks"""
        self.stdout.write('\n[13/15] Creating Assessments and Marks...')
        
        assessments = []
        marks = []
        
        # Create assessments for recent allocations
        for allocation in self.allocations[:100]:
            # CAT 1
            cat1, created = Assessment.objects.get_or_create(
                unit_allocation=allocation,
                assessment_type='cat1',
                defaults={
                    'title': f"CAT 1 - {allocation.programme_unit.unit.code}",
                    'max_marks': Decimal('30.00'),
                    'weight_percentage': Decimal('20.00'),
                    'date': allocation.semester.start_date + timedelta(days=30),
                    'duration_minutes': 60,
                    'venue': f"Room {random.randint(101, 350)}",
                    'is_published': True
                }
            )
            if created:
                assessments.append(cat1)
            
            # CAT 2
            cat2, created = Assessment.objects.get_or_create(
                unit_allocation=allocation,
                assessment_type='cat2',
                defaults={
                    'title': f"CAT 2 - {allocation.programme_unit.unit.code}",
                    'max_marks': Decimal('30.00'),
                    'weight_percentage': Decimal('20.00'),
                    'date': allocation.semester.start_date + timedelta(days=60),
                    'duration_minutes': 60,
                    'venue': f"Room {random.randint(101, 350)}",
                    'is_published': True
                }
            )
            if created:
                assessments.append(cat2)
            
            # Final Exam
            final, created = Assessment.objects.get_or_create(
                unit_allocation=allocation,
                assessment_type='final',
                defaults={
                    'title': f"Final Exam - {allocation.programme_unit.unit.code}",
                    'max_marks': Decimal('70.00'),
                    'weight_percentage': Decimal('60.00'),
                    'date': allocation.semester.end_date - timedelta(days=14),
                    'duration_minutes': 180,
                    'venue': f"Hall {random.randint(1, 5)}",
                    'is_published': True
                }
            )
            if created:
                assessments.append(final)
            
            # Create marks for students registered in this unit
            programme = allocation.programme_unit.programme
            registered_students = [s for s in self.students if s.programme == programme and s.student_status == 'active'][:30]
            
            for student in registered_students:
                # CAT 1 marks
                mark1, created = StudentMarks.objects.get_or_create(
                    assessment=cat1,
                    student=student,
                    defaults={
                        'marks_obtained': Decimal(str(random.uniform(15, 30))),
                        'attendance': random.random() > 0.05,
                        'status': 'published'
                    }
                )
                if created:
                    marks.append(mark1)
                
                # CAT 2 marks
                mark2, created = StudentMarks.objects.get_or_create(
                    assessment=cat2,
                    student=student,
                    defaults={
                        'marks_obtained': Decimal(str(random.uniform(15, 30))),
                        'attendance': random.random() > 0.05,
                        'status': 'published'
                    }
                )
                if created:
                    marks.append(mark2)
                
                # Final marks
                mark3, created = StudentMarks.objects.get_or_create(
                    assessment=final,
                    student=student,
                    defaults={
                        'marks_obtained': Decimal(str(random.uniform(35, 70))),
                        'attendance': random.random() > 0.02,
                        'status': 'published'
                    }
                )
                if created:
                    marks.append(mark3)
        
        self.stdout.write(f"  ✓ Created/Found {len(assessments)} assessments and {len(marks)} marks")
        return assessments, marks

    def create_fee_structures(self):
        """Create fee structures"""
        self.stdout.write('\n[14/15] Creating Fee Structures...')
        
        fee_structures = []
        
        for programme in self.programmes:
            for academic_year in self.academic_years:
                # Determine number of semesters per year
                if programme.total_semesters in [8, 10]:
                    sems_per_year = 2
                elif programme.total_semesters in [9, 12, 15]:
                    sems_per_year = 3
                else:
                    sems_per_year = 2
                
                for year_of_study in range(1, programme.duration_years + 1):
                    for sem_num in range(1, sems_per_year + 1):
                        # Different fees based on programme type
                        if programme.programme_type == 'diploma':
                            tuition = Decimal('45000.00')
                        elif programme.programme_type == 'degree':
                            if 'Medicine' in programme.name or 'Engineering' in programme.name:
                                tuition = Decimal('120000.00')
                            elif 'Law' in programme.name:
                                tuition = Decimal('95000.00')
                            else:
                                tuition = Decimal('75000.00')
                        else:
                            tuition = Decimal('60000.00')
                        
                        fs, created = FeeStructure.objects.get_or_create(
                            programme=programme,
                            academic_year=academic_year,
                            year_of_study=year_of_study,
                            semester_number=str(sem_num),
                            defaults={
                                'tuition_fee': tuition,
                                'activity_fee': Decimal('5000.00'),
                                'examination_fee': Decimal('3000.00'),
                                'library_fee': Decimal('2000.00'),
                                'medical_fee': Decimal('1500.00'),
                                'technology_fee': Decimal('2500.00'),
                                'other_fees': Decimal('1000.00'),
                                'is_active': True
                            }
                        )
                        fee_structures.append(fs)
        
        self.stdout.write(f"  ✓ Created/Found {len(fee_structures)} fee structures")
        return fee_structures

    def create_fee_payments(self):
        """Create fee payments for students"""
        self.stdout.write('\n[15/15] Creating Fee Payments and Balances...')
        
        payments = []
        balances = []
        
        current_semester = [s for s in self.semesters if s.is_current]
        if current_semester:
            current_semester = current_semester[0]
        else:
            current_semester = self.semesters[-1]
        
        for student in self.students[:500]:  # First 500 students
            # Find fee structure
            fs = FeeStructure.objects.filter(
                programme=student.programme,
                academic_year=current_semester.academic_year,
                year_of_study=student.current_year,
                semester_number=student.current_semester
            ).first()
            
            if fs:
                # Create partial or full payment
                payment_amount = fs.total_fee * Decimal(str(random.uniform(0.5, 1.0)))
                
                payment, created = FeePayment.objects.get_or_create(
                    student=student,
                    semester=current_semester,
                    academic_year=current_semester.academic_year,
                    fee_structure=fs,
                    defaults={
                        'amount': payment_amount,
                        'payment_method': random.choice(['mpesa', 'bank', 'card']),
                        'transaction_reference': f"TXN{random.randint(100000, 999999)}",
                        'payment_date': datetime.now() - timedelta(days=random.randint(1, 60)),
                        'status': 'completed',
                        'receipt_number': f"RCP{random.randint(100000, 999999)}"
                    }
                )
                if created:
                    payments.append(payment)
                
                # Create balance
                balance, created = FeeBalance.objects.get_or_create(
                    student=student,
                    semester=current_semester,
                    academic_year=current_semester.academic_year,
                    defaults={
                        'total_fees': fs.total_fee,
                        'amount_paid': payment_amount,
                        'last_payment_date': payment.payment_date if payment else datetime.now()
                    }
                )
                if created:
                    balances.append(balance)
        
        self.stdout.write(f"  ✓ Created/Found {len(payments)} payments and {len(balances)} balances")
        return payments, balances
    
    def print_summary(self):
        """Print final summary"""
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.SUCCESS('DATABASE SEEDING COMPLETED!'))
        self.stdout.write('=' * 80)
        self.stdout.write('\nSummary:')
        self.stdout.write(f'  • Academic Years: {AcademicYear.objects.count()}')
        self.stdout.write(f'  • Semesters: {Semester.objects.count()}')
        self.stdout.write(f'  • Schools: {School.objects.count()}')
        self.stdout.write(f'  • Departments: {Department.objects.count()}')
        self.stdout.write(f'  • Programmes: {Programme.objects.count()}')
        self.stdout.write(f'  • Units: {Unit.objects.count()}')
        self.stdout.write(f'  • Lecturers: {Lecturer.objects.count()}')
        self.stdout.write(f'  • Students: {Student.objects.count()}')
        self.stdout.write(f'  • Programme Units: {ProgrammeUnit.objects.count()}')
        self.stdout.write(f'  • Unit Allocations: {UnitAllocation.objects.count()}')
        self.stdout.write(f'  • Unit Registrations: {UnitRegistration.objects.count()}')
        self.stdout.write(f'  • Assessments: {Assessment.objects.count()}')
        self.stdout.write(f'  • Student Marks: {StudentMarks.objects.count()}')
        self.stdout.write(f'  • Fee Structures: {FeeStructure.objects.count()}')
        self.stdout.write(f'  • Fee Payments: {FeePayment.objects.count()}')
        self.stdout.write(f'  • Fee Balances: {FeeBalance.objects.count()}')
        self.stdout.write('\nAll non-superuser accounts password: password123')
        self.stdout.write('=' * 80)