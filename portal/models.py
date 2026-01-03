from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import timedelta

# ============= USER MANAGEMENT =============
class User(AbstractUser):
    """Extended user model for all system users"""
    USER_ROLES = (
        ('student', 'Student'),
        ('lecturer', 'Lecturer'),
        ('hod', 'Head of Department'),
        ('hos', 'Head of School'),
        ('dean', 'Dean'),
        ('finance', 'Finance Officer'),
        ('procurement', 'Procurement Officer'),
        ('store', 'Store Manager'),
        ('librarian', 'Librarian'),
        ('ict_admin', 'ICT Admin'),
        ('hostel_warden', 'Hostel Warden'),
        ('registrar', 'Registrar'),
        ('vc', 'Vice Chancellor'),
    )
    role = models.CharField(max_length=20, choices=USER_ROLES)
    phone_number = models.CharField(max_length=15, blank=True)
    id_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    is_active_user = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['role', 'is_active_user']),
        ]

# ============= ACADEMIC STRUCTURE =============
class School(models.Model):
    """Schools/Faculties in the university (Computing & IT, Medicine, Law, etc.)"""
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=10, unique=True)
    dean = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='school_as_dean', 
                            limit_choices_to={'role': 'dean'})
    head_of_school = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='school_as_hos',
                                       limit_choices_to={'role': 'hos'})
    description = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    location = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        db_table = 'schools'
        ordering = ['name']

class Department(models.Model):
    """Departments within schools"""
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=10, unique=True)
    hod = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='department_as_hod',
                           limit_choices_to={'role': 'hod'})
    description = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    location = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        db_table = 'departments'
        ordering = ['school', 'name']

# ============= ACADEMIC YEAR & SEMESTER MANAGEMENT =============
class AcademicYear(models.Model):
    """Academic years (e.g., 2024/2025)"""
    name = models.CharField(max_length=20, unique=True)  # e.g., "2024/2025"
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def clean(self):
        # Ensure only one current academic year
        if self.is_current:
            if AcademicYear.objects.filter(is_current=True).exclude(pk=self.pk).exists():
                raise ValidationError('There can only be one current academic year.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'academic_years'
        ordering = ['-start_date']

class Semester(models.Model):
    """Semesters within academic years"""
    SEMESTER_NAMES = (
        ('1', 'Semester 1'),
        ('2', 'Semester 2'),
        ('3', 'Semester 3'),  # For tri-semester systems
    )
    
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='semesters')
    name = models.CharField(max_length=50)  # e.g., "Semester 1 - 2024/2025"
    semester_number = models.CharField(max_length=1, choices=SEMESTER_NAMES)
    start_date = models.DateField()
    end_date = models.DateField()
    registration_start_date = models.DateField()
    registration_end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}"

    def clean(self):
        # Ensure only one current semester
        if self.is_current:
            if Semester.objects.filter(is_current=True).exclude(pk=self.pk).exists():
                raise ValidationError('There can only be one current semester.')

    class Meta:
        db_table = 'semesters'
        unique_together = ('academic_year', 'semester_number')
        ordering = ['-academic_year__start_date', 'semester_number']

# ============= INTAKE MANAGEMENT =============
class Intake(models.Model):
    """Intake periods (September, January, May)"""
    INTAKE_MONTHS = (
        ('september', 'September'),
        ('january', 'January'),
        ('may', 'May'),
    )
    
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='intakes')
    name = models.CharField(max_length=100)  # e.g., "September 2024 Intake"
    month = models.CharField(max_length=10, choices=INTAKE_MONTHS)
    intake_number = models.CharField(max_length=10)  # e.g., "SEP/2024"
    start_date = models.DateField()
    application_deadline = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'intakes'
        unique_together = ('academic_year', 'month')
        ordering = ['-start_date']

# ============= PROGRAMME MANAGEMENT =============
class Programme(models.Model):
    """Degree/Diploma programmes"""
    PROGRAMME_TYPES = (
        ('certificate', 'Certificate'),
        ('diploma', 'Diploma'),
        ('degree', 'Degree'),
        ('masters', 'Masters'),
        ('phd', 'PhD'),
    )
    STUDY_MODES = (
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('evening', 'Evening'),
        ('weekend', 'Weekend'),
        ('online', 'Online'),
    )
    
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='programmes')
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    programme_type = models.CharField(max_length=20, choices=PROGRAMME_TYPES)
    study_mode = models.CharField(max_length=20, choices=STUDY_MODES, default='full_time')
    duration_years = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(7)])
    total_semesters = models.IntegerField(validators=[MinValueValidator(2), MaxValueValidator(14)])
    min_credit_hours = models.IntegerField(default=120)  # Minimum credits for graduation
    description = models.TextField(blank=True)
    accreditation_body = models.CharField(max_length=200, blank=True)
    accreditation_status = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        db_table = 'programmes'
        ordering = ['department', 'name']

# ============= UNITS/COURSES MANAGEMENT =============
class Unit(models.Model):
    """Course units"""
    UNIT_LEVELS = (
        ('100', 'Level 100'),
        ('200', 'Level 200'),
        ('300', 'Level 300'),
        ('400', 'Level 400'),
        ('500', 'Level 500'),
        ('600', 'Level 600'),
    )
    
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='units')
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    unit_level = models.CharField(max_length=3, choices=UNIT_LEVELS)
    credit_hours = models.IntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(6)])
    description = models.TextField(blank=True)
    prerequisites = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='required_for')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        db_table = 'units'
        ordering = ['code']

class ProgrammeUnit(models.Model):
    """Units assigned to specific programme, year, and semester"""
    UNIT_TYPES = (
        ('core', 'Core'),
        ('elective', 'Elective'),
        ('common', 'Common Unit'),
    )
    
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='programme_units')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='programme_assignments')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='programme_units')
    year_of_study = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(7)])
    semester_number = models.CharField(max_length=1, choices=Semester.SEMESTER_NAMES)
    unit_type = models.CharField(max_length=10, choices=UNIT_TYPES, default='core')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.programme.code} - Year {self.year_of_study} Sem {self.semester_number} - {self.unit.code}"

    class Meta:
        db_table = 'programme_units'
        unique_together = ('programme', 'unit', 'academic_year', 'year_of_study', 'semester_number')
        ordering = ['programme', 'year_of_study', 'semester_number']
        indexes = [
            models.Index(fields=['programme', 'year_of_study', 'semester_number']),
        ]

class UnitGradingSystem(models.Model):
    """Grading system for units (can vary by department/programme)"""
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='grading_rules')
    grade = models.CharField(max_length=2)  # A, A-, B+, B, etc.
    min_marks = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    max_marks = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    grade_point = models.DecimalField(max_digits=3, decimal_places=2)
    description = models.CharField(max_length=50, blank=True)  # e.g., "Excellent", "Very Good"
    is_pass = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.unit.code} - {self.grade} ({self.min_marks}-{self.max_marks})"

    class Meta:
        db_table = 'unit_grading_systems'
        ordering = ['unit', '-min_marks']

class UnitAllocation(models.Model):
    """Lecturers assigned to units for specific semester"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved_hod', 'Approved by HOD'),
        ('approved_hos', 'Approved by HOS'),
        ('approved_dean', 'Approved by Dean'),
        ('rejected', 'Rejected'),
    )
    
    programme_unit = models.ForeignKey(ProgrammeUnit, on_delete=models.CASCADE, related_name='allocations')
    lecturer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='unit_allocations',
                                 limit_choices_to={'role': 'lecturer'})
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='unit_allocations')
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='allocations_made')
    approved_by_hod = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                        related_name='hod_unit_approvals')
    approved_by_hos = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='hos_unit_approvals')
    approved_by_dean = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                         related_name='dean_unit_approvals')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    max_students = models.IntegerField(null=True, blank=True)  # Maximum class size
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.programme_unit.unit.code} - {self.lecturer.get_full_name()} ({self.semester})"

    class Meta:
        db_table = 'unit_allocations'
        unique_together = ('programme_unit', 'semester', 'lecturer')
        ordering = ['-semester__academic_year__start_date', 'programme_unit']

# ============= STUDENT MANAGEMENT =============
class Student(models.Model):
    """Student profile"""
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    STUDENT_STATUS = (
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('deferred', 'Deferred'),
        ('graduated', 'Graduated'),
        ('discontinued', 'Discontinued'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    registration_number = models.CharField(max_length=20, unique=True)  # SC211/0530/2022
    programme = models.ForeignKey(Programme, on_delete=models.PROTECT, related_name='students')
    intake = models.ForeignKey(Intake, on_delete=models.PROTECT, related_name='students')
    current_year = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(7)])
    current_semester = models.CharField(max_length=1, choices=Semester.SEMESTER_NAMES)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    national_id = models.CharField(max_length=20, unique=True)
    passport_number = models.CharField(max_length=20, blank=True)
    admission_date = models.DateField()
    expected_graduation_date = models.DateField(null=True, blank=True)
    student_status = models.CharField(max_length=20, choices=STUDENT_STATUS, default='active')
    cumulative_gpa = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    total_credit_hours = models.IntegerField(default=0)
    # Emergency contact
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True)
    # Address
    permanent_address = models.TextField(blank=True)
    current_address = models.TextField(blank=True)
    # Guardian/Sponsor
    sponsor_name = models.CharField(max_length=200, blank=True)
    sponsor_phone = models.CharField(max_length=15, blank=True)
    sponsor_email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.registration_number} - {self.user.get_full_name()}"

    class Meta:
        db_table = 'students'
        ordering = ['registration_number']
        indexes = [
            models.Index(fields=['programme', 'current_year', 'current_semester']),
            models.Index(fields=['student_status']),
        ]

class StudentProgression(models.Model):
    """Track student progression through different programmes (diploma to degree)"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='progressions')
    previous_programme = models.ForeignKey(Programme, on_delete=models.PROTECT, 
                                          related_name='previous_students', null=True, blank=True)
    previous_registration_number = models.CharField(max_length=20, blank=True)
    new_programme = models.ForeignKey(Programme, on_delete=models.PROTECT, related_name='progressed_students')
    previous_academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, 
                                              related_name='progression_from', null=True)
    new_academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, 
                                         related_name='progression_to')
    progression_date = models.DateField()
    final_gpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    credits_transferred = models.IntegerField(default=0)
    remarks = models.TextField(blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'student_progressions'
        ordering = ['-progression_date']

# Reminder dont use this model i have deleted eat instead am using unitregistration model kindly
class UnitRegistration(models.Model):
    """Students registering for units in a specific semester"""
    REGISTRATION_STATUS = (
        ('registered', 'Registered'),
        ('dropped', 'Dropped'),
        ('withdrawn', 'Withdrawn'),
        ('completed', 'Completed'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='unit_registrations')
    programme_unit = models.ForeignKey(ProgrammeUnit, on_delete=models.CASCADE, related_name='registrations')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='unit_registrations')
    registration_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=REGISTRATION_STATUS, default='registered')
    is_retake = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"{self.student.registration_number} - {self.programme_unit.unit.code} ({self.semester})"

    class Meta:
        db_table = 'unit_registrations'
        unique_together = ('student', 'programme_unit', 'semester')
        ordering = ['-registration_date']
        indexes = [
            models.Index(fields=['student', 'semester']),
            models.Index(fields=['semester', 'status']),
        ]

# ============= ASSESSMENT & GRADING =============
class Assessment(models.Model):
    """CATs and Final Exams"""
    ASSESSMENT_TYPES = (
        ('cat1', 'CAT 1'),
        ('cat2', 'CAT 2'),
        ('cat3', 'CAT 3'),
        ('assignment', 'Assignment'),
        ('final', 'Final Exam'),
        ('practical', 'Practical'),
    )
    
    unit_allocation = models.ForeignKey(UnitAllocation, on_delete=models.CASCADE, related_name='assessments')
    assessment_type = models.CharField(max_length=15, choices=ASSESSMENT_TYPES)
    title = models.CharField(max_length=200)
    max_marks = models.DecimalField(max_digits=5, decimal_places=2, default=30.00)
    weight_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=30.00)  # % contribution to final
    date = models.DateField()
    duration_minutes = models.IntegerField(null=True, blank=True)
    venue = models.CharField(max_length=200, blank=True)
    instructions = models.TextField(blank=True)
    is_published = models.BooleanField(default=False)
    published_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.unit_allocation.programme_unit.unit.code} - {self.assessment_type} ({self.unit_allocation.semester})"

    class Meta:
        db_table = 'assessments'
        unique_together = ('unit_allocation', 'assessment_type')
        ordering = ['unit_allocation', 'date']

class StudentMarks(models.Model):
    """Individual student marks for assessments"""
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('submitted', 'Submitted to HOD'),
        ('approved_hod', 'Approved by HOD'),
        ('approved_hos', 'Approved by HOS'),
        ('approved_dean', 'Approved by Dean'),
        ('published', 'Published to Students'),
        ('rejected', 'Rejected'),
    )
    
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='student_marks')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='marks')
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, 
                                        validators=[MinValueValidator(0)])
    attendance = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='marks_submitted')
    approved_by_hod = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                        related_name='marks_approved_hod')
    approved_by_hos = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='marks_approved_hos')
    approved_by_dean = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                         related_name='marks_approved_dean')
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.registration_number} - {self.assessment} - {self.marks_obtained}/{self.assessment.max_marks}"

    class Meta:
        db_table = 'student_marks'
        unique_together = ('assessment', 'student')
        ordering = ['assessment', 'student']

class SemesterResults(models.Model):
    """Compiled semester results for each student per unit"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='semester_results')
    programme_unit = models.ForeignKey(ProgrammeUnit, on_delete=models.CASCADE, related_name='results')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='results')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='results')
    
    # Marks breakdown
    cat_marks = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    assignment_marks = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    exam_marks = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    total_marks = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Grading
    grade = models.CharField(max_length=2)
    grade_point = models.DecimalField(max_digits=3, decimal_places=2)
    credit_hours = models.IntegerField()
    quality_points = models.DecimalField(max_digits=6, decimal_places=2)  # grade_point * credit_hours
    
    # Status
    is_passed = models.BooleanField(default=False)
    is_supplementary = models.BooleanField(default=False)
    remarks = models.TextField(blank=True)
    
    # Approval workflow
    approved_by_hod = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='results_approved_hod')
    approved_by_hos = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='results_approved_hos')
    approved_by_dean = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='results_approved_dean')
    is_published = models.BooleanField(default=False)
    published_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.registration_number} - {self.programme_unit.unit.code} ({self.semester})"

    class Meta:
        db_table = 'semester_results'
        unique_together = ('student', 'programme_unit', 'semester')
        ordering = ['-semester__academic_year__start_date', 'student']
        indexes = [
            models.Index(fields=['student', 'semester']),
            models.Index(fields=['semester', 'is_published']),
        ]

class SemesterGPA(models.Model):
    """Student GPA per semester"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='semester_gpas')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='student_gpas')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='student_gpas')
    
    total_credit_hours = models.IntegerField()
    total_quality_points = models.DecimalField(max_digits=8, decimal_places=2)
    semester_gpa = models.DecimalField(max_digits=4, decimal_places=2)
    cumulative_credit_hours = models.IntegerField()
    cumulative_quality_points = models.DecimalField(max_digits=10, decimal_places=2)
    cumulative_gpa = models.DecimalField(max_digits=4, decimal_places=2)
    
    class_rank = models.IntegerField(null=True, blank=True)
    total_students = models.IntegerField(null=True, blank=True)
    
    remarks = models.TextField(blank=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.registration_number} - {self.semester} - GPA: {self.semester_gpa}"

    class Meta:
        db_table = 'semester_gpas'
        unique_together = ('student', 'semester')
        ordering = ['-semester__academic_year__start_date']

from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class FeeStructure(models.Model):
    """Fee structure for each programme, year, and semester"""
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='fee_structures')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='fee_structures')
    year_of_study = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(7)])
    semester_number = models.CharField(max_length=1, choices=Semester.SEMESTER_NAMES)
    
    # Fee components - USE Decimal('0.00') instead of 0.00
    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2)
    activity_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    examination_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    library_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    medical_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    technology_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    other_fees = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_fee = models.DecimalField(max_digits=10, decimal_places=2)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """Override save to calculate total fee"""
        # Auto-calculate total - ensure all values are Decimal
        self.total_fee = (
            (self.tuition_fee or Decimal('0.00')) + 
            (self.activity_fee or Decimal('0.00')) + 
            (self.examination_fee or Decimal('0.00')) + 
            (self.library_fee or Decimal('0.00')) + 
            (self.medical_fee or Decimal('0.00')) + 
            (self.technology_fee or Decimal('0.00')) + 
            (self.other_fees or Decimal('0.00'))
        )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.programme.code} - Year {self.year_of_study} Sem {self.semester_number} ({self.academic_year})"

    class Meta:
        db_table = 'fee_structures'
        unique_together = ('programme', 'academic_year', 'year_of_study', 'semester_number')
        ordering = ['-academic_year__start_date', 'programme']
        
class FeePayment(models.Model):
    """Student fee payments"""
    PAYMENT_METHODS = (
        ('mpesa', 'M-Pesa'),
        ('bank', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
        ('card', 'Card Payment'),
    )
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('reversed', 'Reversed'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_payments')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='fee_payments')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='fee_payments')
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.PROTECT, related_name='payments')
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    transaction_reference = models.CharField(max_length=100, unique=True)
    payment_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    receipt_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='payments_processed')
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.registration_number} - {self.amount} ({self.payment_date})"

    class Meta:
        db_table = 'fee_payments'
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['student', 'semester']),
            models.Index(fields=['status', 'payment_date']),
        ]

class FeeBalance(models.Model):
    """Track student fee balances per semester"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_balances')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='fee_balances')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='fee_balances')
    
    total_fees = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    last_payment_date = models.DateTimeField(null=True, blank=True)
    
    is_cleared = models.BooleanField(default=False)
    clearance_date = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.balance = self.total_fees - self.amount_paid
        self.is_cleared = self.balance <= 0
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.registration_number} - {self.semester} - Balance: {self.balance}"

    class Meta:
        db_table = 'fee_balances'
        unique_together = ('student', 'semester')
        ordering = ['-semester__academic_year__start_date']

# ============= LECTURER MANAGEMENT =============
class Lecturer(models.Model):
    """Lecturer profile"""
    DESIGNATION_CHOICES = (
        ('lecturer', 'Lecturer'),
        ('senior_lecturer', 'Senior Lecturer'),
        ('associate_professor', 'Associate Professor'),
        ('professor', 'Professor'),
        ('assistant_lecturer', 'Assistant Lecturer'),
        ('teaching_assistant', 'Teaching Assistant'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lecturer_profile')
    employee_number = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='lecturers')
    designation = models.CharField(max_length=30, choices=DESIGNATION_CHOICES)
    qualification = models.CharField(max_length=200)
    specialization = models.CharField(max_length=200, blank=True)
    office_location = models.CharField(max_length=100, blank=True)
    consultation_hours = models.TextField(blank=True)
    hire_date = models.DateField()
    contract_end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee_number} - {self.user.get_full_name()}"

    class Meta:
        db_table = 'lecturers'
        ordering = ['employee_number']

# ============= HOSTEL MANAGEMENT =============
class Hostel(models.Model):
    """Hostels"""
    GENDER_TYPES = (
        ('M', 'Boys'),
        ('F', 'Girls'),
        ('mixed', 'Mixed'),
    )
    
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    gender_type = models.CharField(max_length=10, choices=GENDER_TYPES)
    warden = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='hostels_managed',
                               limit_choices_to={'role': 'hostel_warden'})
    total_capacity = models.IntegerField()
    location = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    amenities = models.TextField(blank=True)  # WiFi, Kitchen, Laundry, etc.
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        db_table = 'hostels'
        ordering = ['name']

class HostelRoom(models.Model):
    """Rooms in hostels"""
    ROOM_TYPES = (
        ('single', 'Single'),
        ('double', 'Double'),
        ('triple', 'Triple'),
        ('quad', 'Quad'),
    )
    
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name='rooms')
    room_number = models.CharField(max_length=20)
    floor = models.IntegerField()
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES)
    capacity = models.IntegerField()
    has_bathroom = models.BooleanField(default=True)
    has_balcony = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.hostel.code} - Room {self.room_number}"

    class Meta:
        db_table = 'hostel_rooms'
        unique_together = ('hostel', 'room_number')
        ordering = ['hostel', 'floor', 'room_number']

class HostelBed(models.Model):
    """Beds in hostel rooms"""
    BED_STATUS = (
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('reserved', 'Reserved'),
        ('maintenance', 'Under Maintenance'),
    )
    
    room = models.ForeignKey(HostelRoom, on_delete=models.CASCADE, related_name='beds')
    bed_number = models.CharField(max_length=10)
    status = models.CharField(max_length=20, choices=BED_STATUS, default='available')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='hostel_beds')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.room.hostel.code} - Room {self.room.room_number} - Bed {self.bed_number}"

    class Meta:
        db_table = 'hostel_beds'
        unique_together = ('room', 'bed_number', 'academic_year')
        ordering = ['room', 'bed_number']

class HostelFeeStructure(models.Model):
    """Hostel fees per academic year"""
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name='fee_structures')
    room_type = models.CharField(max_length=10, choices=HostelRoom.ROOM_TYPES)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='hostel_fees')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='hostel_fees')
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2)
    booking_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.hostel.name} - {self.room_type} ({self.academic_year} - {self.semester})"

    class Meta:
        db_table = 'hostel_fee_structures'
        unique_together = ('hostel', 'room_type', 'academic_year', 'semester')
        ordering = ['-academic_year__start_date', 'hostel']

class HostelApplication(models.Model):
    """Hostel applications"""
    APPLICATION_STATUS = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='hostel_applications')
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name='applications')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='hostel_applications')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='hostel_applications')
    preferred_room_type = models.CharField(max_length=10, choices=HostelRoom.ROOM_TYPES)
    application_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=APPLICATION_STATUS, default='pending')
    booking_fee_paid = models.BooleanField(default=False)
    payment_reference = models.CharField(max_length=100, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                    related_name='hostel_approvals')
    approved_date = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.registration_number} - {self.hostel.name} ({self.academic_year})"

    class Meta:
        db_table = 'hostel_applications'
        unique_together = ('student', 'academic_year', 'semester')
        ordering = ['-application_date']

class HostelAllocation(models.Model):
    """Allocated hostel beds to students"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='hostel_allocations')
    bed = models.ForeignKey(HostelBed, on_delete=models.CASCADE, related_name='allocations')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='hostel_allocations')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='hostel_allocations')
    allocation_date = models.DateTimeField(auto_now_add=True)
    check_in_date = models.DateTimeField(null=True, blank=True)
    check_out_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    fee_paid = models.BooleanField(default=False)
    payment_reference = models.CharField(max_length=100, blank=True)
    allocated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='hostel_allocations_made')
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"{self.student.registration_number} - {self.bed} ({self.academic_year})"

    class Meta:
        db_table = 'hostel_allocations'
        unique_together = ('student', 'academic_year', 'semester')
        ordering = ['-allocation_date']

# ============= ENHANCED HOSTEL MANAGEMENT MODELS =============
# Add these models to your existing models.py file

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import uuid

class HostelImage(models.Model):
    """Images for hostels"""
    hostel = models.ForeignKey('Hostel', on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='hostel_images/')
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'hostel_images'
        ordering = ['display_order', '-is_primary']

    def __str__(self):
        return f"{self.hostel.name} - Image {self.id}"


class HostelRoomImage(models.Model):
    """Images for hostel rooms"""
    room = models.ForeignKey('HostelRoom', on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='room_images/')
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'hostel_room_images'
        ordering = ['-is_primary', '-created_at']

    def __str__(self):
        return f"{self.room.hostel.code} - Room {self.room.room_number} Image"


class BedReservation(models.Model):
    """Temporary bed reservations during booking process"""
    RESERVATION_STATUS = (
        ('pending', 'Pending Payment'),
        ('confirmed', 'Payment Confirmed'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    )
    
    reservation_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='bed_reservations')
    bed = models.ForeignKey('HostelBed', on_delete=models.CASCADE, related_name='reservations')
    application = models.ForeignKey('HostelApplication', on_delete=models.CASCADE, 
                                   related_name='bed_reservations', null=True)
    
    # Reservation details
    reserved_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # 15 minutes from reservation
    status = models.CharField(max_length=20, choices=RESERVATION_STATUS, default='pending')
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_phone = models.CharField(max_length=15)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """Validate that bed is available"""
        if self.bed.status != 'available':
            raise ValidationError(f'Bed {self.bed.bed_number} is not available.')
        
        # Check for existing active reservation
        existing = BedReservation.objects.filter(
            bed=self.bed,
            status='pending',
            expires_at__gt=timezone.now()
        ).exclude(pk=self.pk)
        
        if existing.exists():
            raise ValidationError('This bed is currently reserved by another student.')

    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Set expiration to 15 minutes from now
            self.expires_at = timezone.now() + timezone.timedelta(minutes=15)
        
        self.full_clean()
        
        # Update bed status
        if self.status == 'pending':
            self.bed.status = 'reserved'
            self.bed.save()
        elif self.status == 'confirmed':
            self.bed.status = 'occupied'
            self.bed.save()
        elif self.status in ['expired', 'cancelled']:
            self.bed.status = 'available'
            self.bed.save()
        
        super().save(*args, **kwargs)

    def is_expired(self):
        """Check if reservation has expired"""
        return timezone.now() > self.expires_at and self.status == 'pending'

    class Meta:
        db_table = 'bed_reservations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['bed', 'status']),
            models.Index(fields=['expires_at', 'status']),
        ]

    def __str__(self):
        return f"{self.student.registration_number} - {self.bed} - {self.status}"


class MpesaPayment(models.Model):
    """Track M-Pesa STK Push payments"""
    PAYMENT_STATUS = (
        ('initiated', 'Initiated'),
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )
    
    # Unique identifiers
    merchant_request_id = models.CharField(max_length=100, unique=True)
    checkout_request_id = models.CharField(max_length=100, unique=True)
    
    # Payment details
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='mpesa_payments')
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    account_reference = models.CharField(max_length=100)  # e.g., "HOSTEL-APP-123"
    transaction_desc = models.CharField(max_length=200)
    
    # Response from M-Pesa
    mpesa_receipt_number = models.CharField(max_length=100, blank=True)
    transaction_date = models.DateTimeField(null=True, blank=True)
    result_code = models.CharField(max_length=10, blank=True)
    result_desc = models.TextField(blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='initiated')
    
    # Relations
    bed_reservation = models.ForeignKey(BedReservation, on_delete=models.SET_NULL, 
                                       null=True, blank=True, related_name='mpesa_payments')
    hostel_application = models.ForeignKey('HostelApplication', on_delete=models.SET_NULL,
                                          null=True, blank=True, related_name='mpesa_payments')
    
    # Timestamps
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'mpesa_payments'
        ordering = ['-initiated_at']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['checkout_request_id']),
            models.Index(fields=['mpesa_receipt_number']),
        ]

    def __str__(self):
        return f"{self.student.registration_number} - {self.amount} - {self.status}"


class SMSNotification(models.Model):
    """Track SMS notifications sent to students"""
    SMS_TYPE = (
        ('booking_confirmation', 'Booking Confirmation'),
        ('payment_success', 'Payment Success'),
        ('payment_failed', 'Payment Failed'),
        ('allocation_notice', 'Allocation Notice'),
        ('reminder', 'Reminder'),
    )
    
    STATUS = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    )
    
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='sms_notifications')
    phone_number = models.CharField(max_length=15)
    sms_type = models.CharField(max_length=30, choices=SMS_TYPE)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    
    # External SMS service response
    message_id = models.CharField(max_length=100, blank=True)
    response = models.TextField(blank=True)
    
    # Relations
    mpesa_payment = models.ForeignKey(MpesaPayment, on_delete=models.SET_NULL, 
                                     null=True, blank=True, related_name='sms_notifications')
    hostel_allocation = models.ForeignKey('HostelAllocation', on_delete=models.SET_NULL,
                                         null=True, blank=True, related_name='sms_notifications')
    
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sms_notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.registration_number} - {self.sms_type} - {self.status}"


class HostelReview(models.Model):
    """Student reviews for hostels"""
    hostel = models.ForeignKey('Hostel', on_delete=models.CASCADE, related_name='reviews')
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='hostel_reviews')
    allocation = models.ForeignKey('HostelAllocation', on_delete=models.CASCADE, 
                                  related_name='reviews')
    
    # Ratings (1-5 stars)
    cleanliness_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    facilities_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    security_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    management_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    overall_rating = models.DecimalField(max_digits=3, decimal_places=2)
    
    # Review
    title = models.CharField(max_length=200)
    review = models.TextField()
    
    # Moderation
    is_approved = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Calculate overall rating
        self.overall_rating = (
            self.cleanliness_rating + 
            self.facilities_rating + 
            self.security_rating + 
            self.management_rating
        ) / 4.0
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'hostel_reviews'
        ordering = ['-created_at']
        unique_together = ('student', 'allocation')

    def __str__(self):
        return f"{self.student.registration_number} - {self.hostel.name} - {self.overall_rating}★"


class HostelMaintenanceRequest(models.Model):
    """Maintenance requests from students"""
    REQUEST_TYPE = (
        ('plumbing', 'Plumbing'),
        ('electrical', 'Electrical'),
        ('furniture', 'Furniture'),
        ('cleaning', 'Cleaning'),
        ('security', 'Security'),
        ('other', 'Other'),
    )
    
    STATUS = (
        ('pending', 'Pending'),
        ('acknowledged', 'Acknowledged'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    PRIORITY = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    request_number = models.CharField(max_length=50, unique=True)
    student = models.ForeignKey('Student', on_delete=models.CASCADE, 
                               related_name='maintenance_requests')
    allocation = models.ForeignKey('HostelAllocation', on_delete=models.CASCADE,
                                  related_name='maintenance_requests')
    
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPE)
    priority = models.CharField(max_length=10, choices=PRIORITY, default='medium')
    subject = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='maintenance_requests/', null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    assigned_to = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='assigned_maintenance_requests')
    
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    resolution_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.request_number:
            # Generate request number: MR-YYYY-NNNN
            from django.db.models import Max
            year = timezone.now().year
            last_request = HostelMaintenanceRequest.objects.filter(
                request_number__startswith=f'MR-{year}-'
            ).aggregate(Max('id'))
            
            next_id = (last_request['id__max'] or 0) + 1
            self.request_number = f'MR-{year}-{next_id:04d}'
        
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'hostel_maintenance_requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['status', 'priority']),
        ]

    def __str__(self):
        return f"{self.request_number} - {self.subject}"
    
# ============= LIBRARY MANAGEMENT =============
class BookCategory(models.Model):
    """Library book categories"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    parent_category = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                                       related_name='subcategories')

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        db_table = 'book_categories'
        verbose_name_plural = 'Book Categories'
        ordering = ['name']

class Book(models.Model):
    """Library books"""
    BOOK_STATUS = (
        ('available', 'Available'),
        ('borrowed', 'Borrowed'),
        ('reserved', 'Reserved'),
        ('maintenance', 'Under Maintenance'),
        ('lost', 'Lost'),
        ('damaged', 'Damaged'),
    )
    
    isbn = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=300)
    author = models.CharField(max_length=200)
    publisher = models.CharField(max_length=200, blank=True)
    publication_year = models.IntegerField(null=True, blank=True)
    edition = models.CharField(max_length=50, blank=True)
    category = models.ForeignKey(BookCategory, on_delete=models.PROTECT, related_name='books')
    total_copies = models.IntegerField(default=1)
    available_copies = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=BOOK_STATUS, default='available')
    shelf_location = models.CharField(max_length=50, blank=True)
    call_number = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='books/', null=True, blank=True)
    acquisition_date = models.DateField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.isbn} - {self.title}"

    class Meta:
        db_table = 'books'
        ordering = ['title']
        indexes = [
            models.Index(fields=['category', 'status']),
            models.Index(fields=['isbn']),
        ]

class BookBorrowing(models.Model):
    """Book borrowing records"""
    BORROWING_STATUS = (
        ('active', 'Active'),
        ('returned', 'Returned'),
        ('overdue', 'Overdue'),
        ('lost', 'Lost'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='book_borrowings')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='borrowings')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='book_borrowings')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='book_borrowings')
    borrow_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()  # 2 weeks from borrow date
    return_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=BORROWING_STATUS, default='active')
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    fine_paid = models.BooleanField(default=False)
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='book_issues',
                                  limit_choices_to={'role': 'librarian'})
    returned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                    related_name='book_returns', limit_choices_to={'role': 'librarian'})
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_fine(self):
        """Calculate fine for overdue books (KES 5 per day after due date)"""
        if self.return_date:
            days_overdue = (self.return_date.date() - self.due_date).days
        else:
            from django.utils import timezone
            days_overdue = (timezone.now().date() - self.due_date).days
        
        if days_overdue > 0:
            self.fine_amount = Decimal(days_overdue * 5)  # 5 KES per day
            self.status = 'overdue'
            self.save()

    def __str__(self):
        return f"{self.student.registration_number} - {self.book.title} ({self.borrow_date})"

    class Meta:
        db_table = 'book_borrowings'
        ordering = ['-borrow_date']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['due_date', 'status']),
        ]

# ============= TIMETABLE MANAGEMENT =============
class Timetable(models.Model):
    """Timetables for programmes per semester"""
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='timetables')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='timetables')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='timetables')
    year_of_study = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(7)])
    name = models.CharField(max_length=200)  # e.g., "BSC IT Year 1 Sem 1 - 2024/2025"
    is_published = models.BooleanField(default=False)
    published_date = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='timetables_created')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='timetables_approved')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.academic_year})"

    class Meta:
        db_table = 'timetables'
        unique_together = ('programme', 'academic_year', 'semester', 'year_of_study')
        ordering = ['-academic_year__start_date', 'programme']

class TimetableSlot(models.Model):
    """Individual timetable slots"""
    DAYS_OF_WEEK = (
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    )
    SLOT_TYPES = (
        ('lecture', 'Lecture'),
        ('practical', 'Practical'),
        ('tutorial', 'Tutorial'),
        ('lab', 'Lab'),
    )
    
    timetable = models.ForeignKey(Timetable, on_delete=models.CASCADE, related_name='slots')
    unit_allocation = models.ForeignKey(UnitAllocation, on_delete=models.CASCADE, related_name='timetable_slots')
    day_of_week = models.CharField(max_length=10, choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_type = models.CharField(max_length=15, choices=SLOT_TYPES, default='lecture')
    venue = models.CharField(max_length=100)
    venue_capacity = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.timetable.programme.code} - {self.day_of_week} {self.start_time}-{self.end_time}"

    class Meta:
        db_table = 'timetable_slots'
        ordering = ['timetable', 'day_of_week', 'start_time']

# ============= ATTENDANCE MANAGEMENT =============
class Attendance(models.Model):
    """Student attendance tracking"""
    ATTENDANCE_STATUS = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances')
    unit_allocation = models.ForeignKey(UnitAllocation, on_delete=models.CASCADE, related_name='attendances')
    timetable_slot = models.ForeignKey(TimetableSlot, on_delete=models.CASCADE, related_name='attendances', 
                                       null=True, blank=True)
    attendance_date = models.DateField()
    status = models.CharField(max_length=10, choices=ATTENDANCE_STATUS)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='attendances_marked')
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.registration_number} - {self.unit_allocation.programme_unit.unit.code} - {self.attendance_date}"

    class Meta:
        db_table = 'attendances'
        unique_together = ('student', 'unit_allocation', 'attendance_date')
        ordering = ['-attendance_date']

# ============= COMMUNICATION & MESSAGING =============
class Announcement(models.Model):
    """University announcements and news"""
    ANNOUNCEMENT_TYPES = (
        ('general', 'General'),
        ('academic', 'Academic'),
        ('event', 'Event'),
        ('urgent', 'Urgent'),
        ('deadline', 'Deadline'),
    )
    TARGET_AUDIENCE = (
        ('all', 'All Users'),
        ('students', 'All Students'),
        ('lecturers', 'All Lecturers'),
        ('staff', 'All Staff'),
        ('programme', 'Specific Programme'),
        ('school', 'Specific School'),
        ('year', 'Specific Year'),
    )
    
    title = models.CharField(max_length=300)
    content = models.TextField()
    announcement_type = models.CharField(max_length=20, choices=ANNOUNCEMENT_TYPES)
    target_audience = models.CharField(max_length=20, choices=TARGET_AUDIENCE)
    target_programme = models.ForeignKey(Programme, on_delete=models.CASCADE, null=True, blank=True, 
                                        related_name='announcements')
    target_school = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True, 
                                     related_name='announcements')
    target_year = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(7)])
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, null=True, blank=True,
                                     related_name='announcements')
    is_published = models.BooleanField(default=False)
    publish_date = models.DateTimeField(null=True, blank=True)
    expiry_date = models.DateTimeField(null=True, blank=True)
    is_pinned = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='announcements_created')
    attachments = models.FileField(upload_to='announcements/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.announcement_type})"

    class Meta:
        db_table = 'announcements'
        ordering = ['-is_pinned', '-created_at']

class Event(models.Model):
    """University events"""
    EVENT_TYPES = (
        ('academic', 'Academic'),
        ('social', 'Social'),
        ('sports', 'Sports'),
        ('cultural', 'Cultural'),
        ('career', 'Career'),
        ('workshop', 'Workshop'),
        ('seminar', 'Seminar'),
    )
    
    title = models.CharField(max_length=300)
    description = models.TextField()
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    venue = models.CharField(max_length=200)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='events')
    registration_required = models.BooleanField(default=False)
    max_participants = models.IntegerField(null=True, blank=True)
    organizer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='events_organized')
    is_published = models.BooleanField(default=False)
    banner = models.ImageField(upload_to='events/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.start_date})"

    class Meta:
        db_table = 'events'
        ordering = ['start_date']

class Message(models.Model):
    """Internal messaging system"""
    MESSAGE_STATUS = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    )
    CATEGORY = (
        ('academic', 'Academic'),
        ('finance', 'Finance'),
        ('hostel', 'Hostel'),
        ('library', 'Library'),
        ('technical', 'Technical'),
        ('general', 'General'),
    )
    
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages_sent')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages_received', 
                                  null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY)
    subject = models.CharField(max_length=300)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=MESSAGE_STATUS, default='pending')
    priority = models.BooleanField(default=False)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                    related_name='assigned_messages')
    parent_message = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                                      related_name='replies')
    is_read = models.BooleanField(default=False)
    read_date = models.DateTimeField(null=True, blank=True)
    attachments = models.FileField(upload_to='messages/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.subject} - {self.sender.username} to {self.recipient.username if self.recipient else 'Unassigned'}"

    class Meta:
        db_table = 'messages'
        ordering = ['-created_at']

# ============= PROCUREMENT & STORE MANAGEMENT =============
class Supplier(models.Model):
    """Suppliers for procurement"""
    name = models.CharField(max_length=200)
    supplier_code = models.CharField(max_length=20, unique=True)
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    alternative_phone = models.CharField(max_length=15, blank=True)
    address = models.TextField()
    tax_pin = models.CharField(max_length=20, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account = models.CharField(max_length=50, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00,
                                validators=[MinValueValidator(0), MaxValueValidator(5)])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.supplier_code} - {self.name}"

    class Meta:
        db_table = 'suppliers'
        ordering = ['name']

class ProcurementCategory(models.Model):
    """Categories for items"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    parent_category = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                                       related_name='subcategories')

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        db_table = 'procurement_categories'
        verbose_name_plural = 'Procurement Categories'
        ordering = ['name']

class PurchaseRequisition(models.Model):
    """Purchase requisitions"""
    REQUISITION_STATUS = (
        ('draft', 'Draft'),
        ('pending_hod', 'Pending HOD Approval'),
        ('approved_hod', 'Approved by HOD'),
        ('pending_hos', 'Pending HOS Approval'),
        ('approved_hos', 'Approved by HOS'),
        ('pending_procurement', 'Pending Procurement'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('processed', 'Processed'),
    )
    
    requisition_number = models.CharField(max_length=50, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='requisitions')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='requisitions')
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requisitions_made')
    purpose = models.TextField()
    status = models.CharField(max_length=30, choices=REQUISITION_STATUS, default='draft')
    approved_by_hod = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                       related_name='requisitions_approved_hod')
    approved_by_hos = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='requisitions_approved_hos')
    approved_by_procurement = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                               related_name='requisitions_approved_procurement')
    hod_approval_date = models.DateTimeField(null=True, blank=True)
    hos_approval_date = models.DateTimeField(null=True, blank=True)
    final_approval_date = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.requisition_number} - {self.department.code}"

    class Meta:
        db_table = 'purchase_requisitions'
        ordering = ['-created_at']

class RequisitionItem(models.Model):
    """Items in a requisition"""
    requisition = models.ForeignKey(PurchaseRequisition, on_delete=models.CASCADE, related_name='items')
    category = models.ForeignKey(ProcurementCategory, on_delete=models.PROTECT, related_name='requisition_items')
    item_description = models.TextField()
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_of_measure = models.CharField(max_length=50)  # pieces, kg, liters, etc.
    estimated_unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_estimated_price = models.DecimalField(max_digits=10, decimal_places=2)
    specifications = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        self.total_estimated_price = self.quantity * self.estimated_unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.requisition.requisition_number}"
    
    

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

# ============= SEMESTER REPORTING =============
class SemesterReport(models.Model):
    """Track student semester reporting and progression"""
    REPORT_STATUS = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('deferred', 'Deferred'),
    )
    
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='semester_reports')
    from_academic_year = models.ForeignKey('AcademicYear', on_delete=models.PROTECT, 
                                          related_name='reports_from', null=True, blank=True)
    to_academic_year = models.ForeignKey('AcademicYear', on_delete=models.PROTECT, 
                                        related_name='reports_to')
    from_semester = models.ForeignKey('Semester', on_delete=models.PROTECT, 
                                     related_name='reports_from', null=True, blank=True)
    to_semester = models.ForeignKey('Semester', on_delete=models.PROTECT, 
                                   related_name='reports_to')
    
    # Progression tracking
    from_year_of_study = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(7)], 
                                            null=True, blank=True)
    to_year_of_study = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(7)])
    from_semester_number = models.CharField(max_length=1, choices=Semester.SEMESTER_NAMES, 
                                           null=True, blank=True)
    to_semester_number = models.CharField(max_length=1, choices=Semester.SEMESTER_NAMES)
    
    # Eligibility checks
    failed_units_count = models.IntegerField(default=0)
    is_eligible = models.BooleanField(default=False)
    eligibility_checked_at = models.DateTimeField(null=True, blank=True)
    eligibility_remarks = models.TextField(blank=True)
    
    # Financial clearance
    fee_balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    is_financially_cleared = models.BooleanField(default=False)
    financial_clearance_date = models.DateTimeField(null=True, blank=True)
    
    # Academic clearance
    previous_semester_gpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    cumulative_gpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    total_credits_earned = models.IntegerField(default=0)
    
    # Report details
    report_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=REPORT_STATUS, default='pending')
    approved_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='semester_reports_approved')
    approval_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    remarks = models.TextField(blank=True)
    
    # System tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """Validate semester reporting"""
        # Check if student has more than 2 failed units
        if self.failed_units_count > 2:
            raise ValidationError(
                f'Cannot report for semester. You have {self.failed_units_count} failed units. '
                'You must clear at least {self.failed_units_count - 2} failed unit(s) before reporting.'
            )
        
        # Check if there's a previous report for the same semester
        if SemesterReport.objects.filter(
            student=self.student,
            to_semester=self.to_semester,
            status='approved'
        ).exclude(pk=self.pk).exists():
            raise ValidationError('You have already reported for this semester.')

    def save(self, *args, **kwargs):
        # Set eligibility based on failed units
        self.is_eligible = self.failed_units_count <= 2
        self.eligibility_checked_at = timezone.now()
        
        if not self.is_eligible:
            self.eligibility_remarks = (
                f'Not eligible: {self.failed_units_count} failed units. '
                'Maximum allowed is 2 failed units.'
            )
        
        self.full_clean()
        super().save(*args, **kwargs)
        
        # Update student's current year and semester if approved
        if self.status == 'approved':
            self.student.current_year = self.to_year_of_study
            self.student.current_semester = self.to_semester_number
            self.student.save()

    def __str__(self):
        return (f"{self.student.registration_number} - "
                f"Y{self.from_year_of_study}S{self.from_semester_number} → "
                f"Y{self.to_year_of_study}S{self.to_semester_number}")

    class Meta:
        db_table = 'semester_reports'
        ordering = ['-report_date']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['to_semester', 'status']),
        ]


# ============= RESIT/SUPPLEMENTARY EXAM TRACKING =============
class ResitExam(models.Model):
    """Track resit/supplementary examinations for failed units"""
    RESIT_STATUS = (
        ('registered', 'Registered'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('missed', 'Missed'),
    )
    
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='resit_exams')
    original_result = models.ForeignKey('SemesterResults', on_delete=models.CASCADE, 
                                       related_name='resit_exams')
    resit_semester = models.ForeignKey('Semester', on_delete=models.CASCADE, 
                                      related_name='resit_exams')
    
    # Original attempt details
    original_semester = models.ForeignKey('Semester', on_delete=models.PROTECT, 
                                        related_name='original_resit_exams')
    original_marks = models.DecimalField(max_digits=5, decimal_places=2)
    original_grade = models.CharField(max_length=2)
    original_grade_point = models.DecimalField(max_digits=3, decimal_places=2)
    
    # Resit details
    resit_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    resit_grade = models.CharField(max_length=2, blank=True)
    resit_grade_point = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    
    # Fee payment
    resit_fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    fee_paid = models.BooleanField(default=False)
    payment_reference = models.CharField(max_length=100, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    
    # Status tracking
    registration_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=RESIT_STATUS, default='registered')
    approved_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='resit_exams_approved')
    approval_date = models.DateTimeField(null=True, blank=True)
    
    # Exam details
    exam_date = models.DateField(null=True, blank=True)
    exam_venue = models.CharField(max_length=200, blank=True)
    attendance = models.BooleanField(default=False)
    
    # Marking details
    marked_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='resit_exams_marked',
                                 limit_choices_to={'role': 'lecturer'})
    marking_date = models.DateTimeField(null=True, blank=True)
    
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """Validate resit exam registration"""
        # Check if unit is being offered in the resit semester
        programme_unit = self.original_result.programme_unit
        if not UnitAllocation.objects.filter(
            programme_unit=programme_unit,
            semester=self.resit_semester,
            status='approved_dean'
        ).exists():
            raise ValidationError(
                f'Unit {programme_unit.unit.code} is not offered in {self.resit_semester}. '
                'You can only register for resit when the unit is being offered.'
            )
        
        # Check if already registered for resit in this semester
        if ResitExam.objects.filter(
            student=self.student,
            original_result=self.original_result,
            resit_semester=self.resit_semester
        ).exclude(pk=self.pk).exists():
            raise ValidationError(
                'You have already registered for a resit of this unit in this semester.'
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        
        # Update original result if resit is completed
        if self.status == 'completed' and self.resit_marks is not None:
            self.original_result.total_marks = self.resit_marks
            self.original_result.grade = self.resit_grade
            self.original_result.grade_point = self.resit_grade_point
            self.original_result.is_passed = self.resit_grade_point >= 2.0  # Assuming pass grade is 2.0
            self.original_result.is_supplementary = True
            self.original_result.remarks = f'Resit completed in {self.resit_semester}. Original: {self.original_marks}'
            self.original_result.save()

    def calculate_resit_grade(self):
        """Calculate grade from resit marks"""
        if self.resit_marks is not None:
            # Get grading system for the unit
            grading = UnitGradingSystem.objects.filter(
                unit=self.original_result.programme_unit.unit,
                min_marks__lte=self.resit_marks,
                max_marks__gte=self.resit_marks
            ).first()
            
            if grading:
                self.resit_grade = grading.grade
                self.resit_grade_point = grading.grade_point
                self.save()

    def __str__(self):
        return (f"{self.student.registration_number} - "
                f"{self.original_result.programme_unit.unit.code} - "
                f"Resit in {self.resit_semester}")

    class Meta:
        db_table = 'resit_exams'
        ordering = ['-registration_date']
        unique_together = ('student', 'original_result', 'resit_semester')
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['resit_semester', 'status']),
        ]



# ============= UNIT ENROLLMENT =============
class UnitEnrollment(models.Model):
    """Track unit enrollment - students can only enroll after reporting for semester"""
    ENROLLMENT_STATUS = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('dropped', 'Dropped'),
    )
    ENROLLMENT_TYPE = (
        ('normal', 'Normal Enrollment'),
        ('resit', 'Resit/Supplementary'),
        ('retake', 'Retake'),
    )
    
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='unit_enrollments')
    semester_report = models.ForeignKey(SemesterReport, on_delete=models.CASCADE, 
                                       related_name='unit_enrollments')
    programme_unit = models.ForeignKey('ProgrammeUnit', on_delete=models.CASCADE, 
                                      related_name='enrollments')
    semester = models.ForeignKey('Semester', on_delete=models.CASCADE, related_name='enrollments')
    
    enrollment_type = models.CharField(max_length=20, choices=ENROLLMENT_TYPE, default='normal')
    enrollment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=ENROLLMENT_STATUS, default='pending')
    
    # Link to resit if applicable
    resit_exam = models.OneToOneField(ResitExam, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='enrollment')
    
    # Approval
    approved_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='enrollments_approved')
    approval_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """Validate enrollment"""
        # Check if student has reported for this semester
        if not self.semester_report or self.semester_report.status != 'approved':
            raise ValidationError(
                'You must report for the semester before enrolling in units.'
            )
        
        # Check if unit is offered in this semester (accept any approval level)
        if not UnitAllocation.objects.filter(
            programme_unit=self.programme_unit,
            semester=self.semester,
            status__in=['approved_hod', 'approved_hos', 'approved_dean']
        ).exists():
            raise ValidationError(
                f'Unit {self.programme_unit.unit.code} is not offered in {self.semester}.'
            )
    
        # Check if already enrolled
        if UnitEnrollment.objects.filter(
            student=self.student,
            programme_unit=self.programme_unit,
            semester=self.semester,
            status__in=['pending', 'approved']
        ).exclude(pk=self.pk).exists():
            raise ValidationError(
                f'You are already enrolled in {self.programme_unit.unit.code} for this semester.'
            )
    
        # For resit enrollments, check if there's a failed result
        if self.enrollment_type == 'resit':
            failed_result = SemesterResults.objects.filter(
                student=self.student,
                programme_unit=self.programme_unit,
                is_passed=False
            ).first()
            
            if not failed_result:
                raise ValidationError(
                    f'No failed result found for {self.programme_unit.unit.code}. '
                    'You can only enroll for resit if you have a failed result.'
                )

    def __str__(self):
        return (f"{self.student.registration_number} - "
                f"{self.programme_unit.unit.code} - "
                f"{self.get_enrollment_type_display()}")

    class Meta:
        db_table = 'unit_enrollments'
        ordering = ['-enrollment_date']
        unique_together = ('student', 'programme_unit', 'semester')
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['semester', 'status']),
            models.Index(fields=['semester_report']),
        ]


# ============= ENROLLMENT PERIOD =============
class EnrollmentPeriod(models.Model):
    """Define enrollment periods for each semester"""
    semester = models.OneToOneField('Semester', on_delete=models.CASCADE, 
                                   related_name='enrollment_period')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    # Resit enrollment period
    resit_start_date = models.DateTimeField(null=True, blank=True)
    resit_end_date = models.DateTimeField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_enrollment_open(self):
        """Check if normal enrollment is open"""
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date

    def is_resit_enrollment_open(self):
        """Check if resit enrollment is open"""
        if not self.resit_start_date or not self.resit_end_date:
            return False
        now = timezone.now()
        return self.is_active and self.resit_start_date <= now <= self.resit_end_date

    def __str__(self):
        return f"{self.semester} - Enrollment Period"

    class Meta:
        db_table = 'enrollment_periods'
        ordering = ['-start_date']
        
        
# ============= TEACHING MATERIALS MANAGEMENT =============
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

class TeachingMaterial(models.Model):
    """Teaching materials uploaded by lecturers for their allocated units"""
    MATERIAL_TYPES = (
        ('notes', 'Lecture Notes'),
        ('slides', 'Presentation Slides'),
        ('assignment', 'Assignment'),
        ('tutorial', 'Tutorial'),
        ('reference', 'Reference Material'),
        ('video', 'Video Link'),
        ('other', 'Other'),
    )
    
    FILE_TYPES = (
        ('pdf', 'PDF Document'),
        ('word', 'Word Document'),
        ('image', 'Image'),
        ('link', 'External Link'),
    )
    
    unit_allocation = models.ForeignKey('UnitAllocation', on_delete=models.CASCADE, 
                                       related_name='teaching_materials')
    week_number = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(15)],
                                     help_text="Week number in the semester (1-15)")
    material_type = models.CharField(max_length=20, choices=MATERIAL_TYPES, default='notes')
    file_type = models.CharField(max_length=10, choices=FILE_TYPES, default='pdf')
    
    # Content details
    topic = models.CharField(max_length=300, help_text="Topic/Title of the material")
    description = models.TextField(blank=True, help_text="Brief description or instructions")
    
    # File upload - supports PDF, Word, Images
    file = models.FileField(
        upload_to='teaching_materials/%Y/%m/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'gif']
            )
        ],
        null=True,
        blank=True,
        help_text="Upload PDF, Word document, or Image"
    )
    
    # External link (for videos, external resources)
    external_link = models.URLField(blank=True, help_text="YouTube link or other external resource")
    
    # Tracking
    uploaded_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, 
                                   related_name='materials_uploaded')
    upload_date = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=True, help_text="Make visible to students")
    publish_date = models.DateTimeField(null=True, blank=True)
    
    # Download tracking
    download_count = models.IntegerField(default=0)
    view_count = models.IntegerField(default=0)
    
    # Metadata
    file_size = models.BigIntegerField(null=True, blank=True, help_text="File size in bytes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """Validate that either file or external_link is provided"""
        if not self.file and not self.external_link:
            raise ValidationError('Either upload a file or provide an external link.')
        
        if self.file and self.external_link:
            raise ValidationError('Provide either a file OR an external link, not both.')

    def save(self, *args, **kwargs):
        if self.is_published and not self.publish_date:
            self.publish_date = timezone.now()
        
        # Set file size if file is uploaded
        if self.file:
            try:
                self.file_size = self.file.size
            except:
                pass
        
        self.full_clean()
        super().save(*args, **kwargs)

    def get_file_extension(self):
        """Get file extension"""
        if self.file:
            return self.file.name.split('.')[-1].lower()
        return None

    def get_file_icon(self):
        """Get appropriate icon based on file type"""
        ext = self.get_file_extension()
        icon_map = {
            'pdf': 'ri-file-pdf-line',
            'doc': 'ri-file-word-line',
            'docx': 'ri-file-word-line',
            'jpg': 'ri-image-line',
            'jpeg': 'ri-image-line',
            'png': 'ri-image-line',
            'gif': 'ri-image-line',
        }
        return icon_map.get(ext, 'ri-file-line')

    def __str__(self):
        return f"{self.unit_allocation.programme_unit.unit.code} - Week {self.week_number} - {self.topic}"

    class Meta:
        db_table = 'teaching_materials'
        ordering = ['unit_allocation', 'week_number', '-upload_date']
        indexes = [
            models.Index(fields=['unit_allocation', 'week_number']),
            models.Index(fields=['is_published', 'publish_date']),
        ]


class MaterialDownload(models.Model):
    """Track student downloads/views of teaching materials"""
    material = models.ForeignKey(TeachingMaterial, on_delete=models.CASCADE, 
                                related_name='downloads')
    student = models.ForeignKey('Student', on_delete=models.CASCADE, 
                                related_name='material_downloads')
    download_date = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.student.registration_number} - {self.material.topic}"

    class Meta:
        db_table = 'material_downloads'
        ordering = ['-download_date']
        indexes = [
            models.Index(fields=['material', 'student']),
            models.Index(fields=['download_date']),
        ]


class MaterialComment(models.Model):
    """Student comments/questions on teaching materials"""
    material = models.ForeignKey(TeachingMaterial, on_delete=models.CASCADE, 
                                related_name='comments')
    student = models.ForeignKey('Student', on_delete=models.CASCADE, 
                                related_name='material_comments')
    comment = models.TextField()
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, 
                                      null=True, blank=True, related_name='replies')
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Comment by {self.student.registration_number} on {self.material.topic}"

    class Meta:
        db_table = 'material_comments'
        ordering = ['-created_at']
        
        
        

# ============= STUDENT ID CARD SYSTEM =============
class StudentIDType(models.Model):
    """Types of student ID cards available"""
    ID_TYPES = (
        ('physical', 'Physical ID Card'),
        ('digital', 'Digital ID Card'),
        ('both', 'Both Physical & Digital'),
    )
    
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    id_type = models.CharField(max_length=20, choices=ID_TYPES, default='physical')
    description = models.TextField(blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    validity_period_months = models.IntegerField(default=24)  # How long the ID is valid
    processing_days = models.IntegerField(default=7)  # Standard processing time
    rush_processing_days = models.IntegerField(default=3)  # Rush processing time
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        db_table = 'student_id_types'
        ordering = ['name']


class StudentIDFeeStructure(models.Model):
    """Fee structure for student ID cards including rush fees"""
    id_type = models.ForeignKey(StudentIDType, on_delete=models.CASCADE, 
                               related_name='fee_structures')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, 
                                     related_name='id_fee_structures')
    base_fee = models.DecimalField(max_digits=10, decimal_places=2)
    rush_processing_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    replacement_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    digital_only_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_total_fee(self, is_rush=False, is_replacement=False):
        """Calculate total fee based on options"""
        total = self.base_fee
        if is_rush:
            total += self.rush_processing_fee
        if is_replacement:
            total += self.replacement_fee
        return total

    def __str__(self):
        return f"{self.id_type.name} - {self.academic_year.name}"

    class Meta:
        db_table = 'student_id_fee_structures'
        ordering = ['-effective_from']
        unique_together = ('id_type', 'academic_year')


class StudentIDApplication(models.Model):
    """Student ID card applications"""
    APPLICATION_STATUS = (
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('payment_pending', 'Payment Pending'),
        ('payment_confirmed', 'Payment Confirmed'),
        ('in_production', 'In Production'),
        ('ready_for_pickup', 'Ready for Pickup'),
        ('delivered', 'Delivered (Digital)'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    )
    
    APPLICATION_REASON = (
        ('new_student', 'New Student'),
        ('lost', 'Lost ID Card'),
        ('damaged', 'Damaged ID Card'),
        ('expired', 'ID Card Expired'),
        ('change_details', 'Change of Details'),
        ('other', 'Other'),
    )
    
    # Application Details
    application_number = models.CharField(max_length=50, unique=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, 
                               related_name='id_applications')
    id_type = models.ForeignKey(StudentIDType, on_delete=models.PROTECT, 
                               related_name='applications')
    fee_structure = models.ForeignKey(StudentIDFeeStructure, on_delete=models.PROTECT, 
                                     related_name='applications')
    
    # Reason and Details
    application_reason = models.CharField(max_length=20, choices=APPLICATION_REASON)
    reason_details = models.TextField(blank=True)
    
    # Options
    is_rush_processing = models.BooleanField(default=False)
    is_replacement = models.BooleanField(default=False)
    
    # Photo Requirements
    photo = models.ImageField(upload_to='student_id_photos/%Y/%m/', 
                             help_text="Passport-size photo (2x2 inches)")
    photo_back = models.ImageField(upload_to='student_id_photos_back/%Y/%m/', 
                                  null=True, blank=True,
                                  help_text="Optional: Photo for back of ID")
    
    # Status Tracking
    status = models.CharField(max_length=20, choices=APPLICATION_STATUS, default='draft')
    application_date = models.DateTimeField(auto_now_add=True)
    submitted_date = models.DateTimeField(null=True, blank=True)
    
    # Payment Details
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_reference = models.CharField(max_length=100, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    
    # Processing
    estimated_completion_date = models.DateField(null=True, blank=True)
    actual_completion_date = models.DateField(null=True, blank=True)
    pick_up_location = models.CharField(max_length=200, blank=True)
    pick_up_code = models.CharField(max_length=20, blank=True)
    
    # Delivery (for digital IDs)
    digital_id_url = models.URLField(blank=True)
    digital_id_sent_date = models.DateTimeField(null=True, blank=True)
    
    # Approval
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='id_applications_reviewed')
    review_date = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.application_number:
            # Generate application number: ID-YYYY-NNNN
            year = timezone.now().year
            last_app = StudentIDApplication.objects.filter(
                application_number__startswith=f'ID-{year}-'
            ).aggregate(Max('id'))
            next_id = (last_app['id__max'] or 0) + 1
            self.application_number = f'ID-{year}-{next_id:04d}'
        
        # Calculate amount due
        if self.fee_structure:
            self.amount_due = self.fee_structure.get_total_fee(
                is_rush=self.is_rush_processing,
                is_replacement=self.is_replacement
            )
        
        # Set estimated completion date
        if self.status == 'payment_confirmed':
            processing_days = self.id_type.rush_processing_days if self.is_rush_processing else self.id_type.processing_days
            self.estimated_completion_date = timezone.now().date() + timedelta(days=processing_days)
        
        super().save(*args, **kwargs)

    @property
    def balance(self):
        return self.amount_due - self.amount_paid

    @property
    def is_paid(self):
        return self.amount_paid >= self.amount_due

    def __str__(self):
        return f"{self.application_number} - {self.student.registration_number}"

    class Meta:
        db_table = 'student_id_applications'
        ordering = ['-application_date']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['application_number']),
            models.Index(fields=['status', 'estimated_completion_date']),
        ]


class StudentIDCard(models.Model):
    """Issued student ID cards"""
    CARD_STATUS = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('lost', 'Lost'),
        ('damaged', 'Damaged'),
        ('expired', 'Expired'),
        ('replaced', 'Replaced'),
    )
    
    # Card Details
    card_number = models.CharField(max_length=50, unique=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, 
                               related_name='id_cards')
    application = models.OneToOneField(StudentIDApplication, on_delete=models.CASCADE,
                                      related_name='issued_card')
    
    # Validity
    issue_date = models.DateField()
    expiry_date = models.DateField()
    status = models.CharField(max_length=20, choices=CARD_STATUS, default='active')
    
    # Physical/Digital
    card_type = models.CharField(max_length=20, choices=StudentIDType.ID_TYPES)
    qr_code = models.ImageField(upload_to='id_qr_codes/', null=True, blank=True)
    barcode = models.CharField(max_length=100, blank=True)
    
    # Digital ID Specific
    digital_id_file = models.FileField(upload_to='digital_ids/', null=True, blank=True)
    digital_id_hash = models.CharField(max_length=64, blank=True)  # For verification
    
    # Pickup/Delivery
    picked_up_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='id_cards_collected')
    pick_up_date = models.DateTimeField(null=True, blank=True)
    received_signature = models.ImageField(upload_to='id_signatures/', null=True, blank=True)
    
    # Security
    security_features = models.TextField(blank=True)  # JSON string of security features
    last_verified = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.card_number:
            # Generate card number: CARD-YYYY-PROGRAM-NNN
            year = timezone.now().year
            program_code = self.student.programme.code.replace(' ', '').upper()[:6]
            last_card = StudentIDCard.objects.filter(
                card_number__startswith=f'CARD-{year}-{program_code}-'
            ).aggregate(Max('id'))
            next_id = (last_card['id__max'] or 0) + 1
            self.card_number = f'CARD-{year}-{program_code}-{next_id:03d}'
        
        # Set expiry date based on ID type validity period
        if self.issue_date and not self.expiry_date:
            id_type = self.application.id_type
            self.expiry_date = self.issue_date + timedelta(days=id_type.validity_period_months * 30)
        
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now().date() > self.expiry_date

    def __str__(self):
        return f"{self.card_number} - {self.student.registration_number}"

    class Meta:
        db_table = 'student_id_cards'
        ordering = ['-issue_date']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['card_number']),
            models.Index(fields=['expiry_date']),
        ]


class StudentIDPayment(models.Model):
    """Payments for student ID applications"""
    PAYMENT_METHODS = (
        ('mpesa', 'M-Pesa'),
        ('bank', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('card', 'Card Payment'),
    )
    
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('reversed', 'Reversed'),
    )
    
    # Payment Details
    payment_reference = models.CharField(max_length=100, unique=True)
    application = models.ForeignKey(StudentIDApplication, on_delete=models.CASCADE,
                                  related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    
    # Transaction Details
    transaction_id = models.CharField(max_length=100, blank=True)
    merchant_request_id = models.CharField(max_length=100, blank=True)  # For M-Pesa
    checkout_request_id = models.CharField(max_length=100, blank=True)  # For M-Pesa
    
    # M-Pesa Specific
    mpesa_receipt_number = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    payment_date = models.DateTimeField(auto_now_add=True)
    confirmed_date = models.DateTimeField(null=True, blank=True)
    
    # Response
    result_code = models.CharField(max_length=10, blank=True)
    result_description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.payment_reference:
            # Generate payment reference: PAY-ID-YYYYMMDD-HHMMSS-RANDOM
            import random
            import string
            timestamp = timezone.now().strftime('%Y%m%d-%H%M%S')
            random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            self.payment_reference = f'PAY-ID-{timestamp}-{random_str}'
        
        super().save(*args, **kwargs)
        
        # Update application payment status
        if self.status == 'completed':
            self.application.amount_paid += self.amount
            self.application.payment_reference = self.payment_reference
            self.application.payment_date = timezone.now()
            if self.application.amount_paid >= self.application.amount_due:
                self.application.status = 'payment_confirmed'
            self.application.save()

    def __str__(self):
        return f"{self.payment_reference} - {self.amount}"

    class Meta:
        db_table = 'student_id_payments'
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['application', 'status']),
            models.Index(fields=['payment_reference']),
            models.Index(fields=['status', 'payment_date']),
        ]


class IDCardNotification(models.Model):
    """Notifications for ID card applications"""
    NOTIFICATION_TYPES = (
        ('application_submitted', 'Application Submitted'),
        ('payment_request', 'Payment Request'),
        ('payment_confirmed', 'Payment Confirmed'),
        ('in_production', 'ID Card in Production'),
        ('ready_for_pickup', 'Ready for Pickup'),
        ('delivered', 'Digital ID Delivered'),
        ('status_update', 'Status Update'),
        ('reminder', 'Reminder'),
    )
    
    # Notification Details
    student = models.ForeignKey(Student, on_delete=models.CASCADE, 
                               related_name='id_notifications')
    application = models.ForeignKey(StudentIDApplication, on_delete=models.CASCADE,
                                  related_name='notifications', null=True, blank=True)
    
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Delivery
    sent_via_email = models.BooleanField(default=False)
    sent_via_sms = models.BooleanField(default=False)
    sent_via_portal = models.BooleanField(default=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_date = models.DateTimeField(null=True, blank=True)
    
    # Email/SMS tracking
    email_message_id = models.CharField(max_length=200, blank=True)
    sms_message_id = models.CharField(max_length=200, blank=True)
    
    sent_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.registration_number} - {self.notification_type}"

    class Meta:
        db_table = 'id_card_notifications'
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['student', 'is_read']),
            models.Index(fields=['notification_type', 'sent_at']),
        ]        
        