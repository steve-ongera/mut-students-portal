from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import timedelta
from django.db.models import Max


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
        
        
# ============= AI CHATBOT SYSTEM =============
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.postgres.fields import JSONField  # For PostgreSQL
from django.db.models import JSONField  # For Django 3.1+
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import uuid


class AIKnowledgeBase(models.Model):
    """Central knowledge base for AI training data"""
    KNOWLEDGE_TYPES = (
        ('academic', 'Academic Information'),
        ('fees', 'Fee Structure & Payments'),
        ('hostel', 'Hostel & Accommodation'),
        ('library', 'Library Services'),
        ('registration', 'Registration & Enrollment'),
        ('timetable', 'Timetables & Schedules'),
        ('results', 'Results & Grades'),
        ('events', 'Events & Announcements'),
        ('mental_health', 'Mental Health & Wellness'),
        ('career', 'Career & Guidance'),
        ('technical', 'Technical Support'),
        ('policies', 'University Policies'),
        ('general', 'General Information'),
    )
    
    CONTENT_STATUS = (
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived'),
        ('needs_review', 'Needs Review'),
    )
    
    # Knowledge Details
    knowledge_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    category = models.CharField(max_length=20, choices=KNOWLEDGE_TYPES)
    subcategory = models.CharField(max_length=100, blank=True)
    
    # Content
    question = models.TextField(help_text="Common question or query pattern")
    answer = models.TextField(help_text="Detailed answer")
    keywords = models.JSONField(default=list, help_text="List of keywords for matching")
    alternative_questions = models.JSONField(default=list, 
                                            help_text="Alternative ways to ask the same question")
    
    # Context and Conditions
    requires_authentication = models.BooleanField(default=False)
    applicable_roles = models.JSONField(default=list, 
                                       help_text="User roles this applies to (empty = all)")
    academic_year = models.ForeignKey('AcademicYear', on_delete=models.SET_NULL, 
                                     null=True, blank=True,
                                     related_name='ai_knowledge')
    
    # Rich Content
    has_links = models.BooleanField(default=False)
    links = models.JSONField(default=list, help_text="Related links or resources")
    has_attachments = models.BooleanField(default=False)
    attachments = models.JSONField(default=list, help_text="File paths or URLs")
    
    # Training & Quality
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, default=100.00,
                                          validators=[MinValueValidator(0), MaxValueValidator(100)])
    usage_count = models.IntegerField(default=0)
    helpful_count = models.IntegerField(default=0)
    not_helpful_count = models.IntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=CONTENT_STATUS, default='active')
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='verified_knowledge')
    
    # Metadata
    created_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True,
                                  related_name='created_knowledge')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    version = models.IntegerField(default=1)

    def calculate_helpfulness_ratio(self):
        """Calculate helpfulness percentage"""
        total = self.helpful_count + self.not_helpful_count
        if total == 0:
            return 0
        return (self.helpful_count / total) * 100

    def __str__(self):
        return f"{self.category} - {self.question[:50]}"

    class Meta:
        db_table = 'ai_knowledge_base'
        ordering = ['-usage_count', '-helpful_count']
        indexes = [
            models.Index(fields=['category', 'status']),
            models.Index(fields=['requires_authentication']),
            models.Index(fields=['-usage_count']),
        ]


class ChatSession(models.Model):
    """Individual chat sessions"""
    SESSION_STATUS = (
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    )
    
    # Session Details
    session_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True,
                            related_name='chat_sessions')
    student = models.ForeignKey('Student', on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='chat_sessions')
    
    # Session Context
    is_authenticated = models.BooleanField(default=False)
    user_role = models.CharField(max_length=20, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_type = models.CharField(max_length=20, blank=True)  # mobile, tablet, desktop
    
    # Session Data
    context_data = models.JSONField(default=dict, 
                                   help_text="User-specific context (programme, year, etc.)")
    conversation_topics = models.JSONField(default=list, 
                                          help_text="Topics discussed in this session")
    
    # Session Metrics
    message_count = models.IntegerField(default=0)
    avg_response_time = models.DecimalField(max_digits=6, decimal_places=2, 
                                           default=0.00, help_text="Average in seconds")
    satisfaction_rating = models.IntegerField(null=True, blank=True,
                                             validators=[MinValueValidator(1), MaxValueValidator(5)])
    feedback_text = models.TextField(blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=SESSION_STATUS, default='active')
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(default=0)

    def update_duration(self):
        """Calculate session duration"""
        if self.ended_at:
            delta = self.ended_at - self.started_at
            self.duration_seconds = int(delta.total_seconds())
            self.save()

    def __str__(self):
        user_id = self.user.username if self.user else f"Anonymous-{self.session_id}"
        return f"{user_id} - {self.started_at}"

    class Meta:
        db_table = 'chat_sessions'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['session_id']),
            models.Index(fields=['-started_at']),
        ]


class ChatMessage(models.Model):
    """Individual messages in chat sessions"""
    MESSAGE_TYPES = (
        ('user', 'User Message'),
        ('ai', 'AI Response'),
        ('system', 'System Message'),
    )
    
    INTENT_CATEGORIES = (
        ('question', 'Question'),
        ('complaint', 'Complaint'),
        ('request', 'Request'),
        ('feedback', 'Feedback'),
        ('clarification', 'Clarification'),
        ('greeting', 'Greeting'),
        ('farewell', 'Farewell'),
        ('other', 'Other'),
    )
    
    # Message Details
    message_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, 
                               related_name='messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    
    # Content
    message_text = models.TextField()
    message_html = models.TextField(blank=True, help_text="Formatted HTML version")
    
    # AI Processing
    detected_intent = models.CharField(max_length=20, choices=INTENT_CATEGORIES, blank=True)
    detected_entities = models.JSONField(default=dict, 
                                        help_text="Extracted entities (dates, numbers, names, etc.)")
    matched_knowledge = models.ForeignKey(AIKnowledgeBase, on_delete=models.SET_NULL, 
                                         null=True, blank=True,
                                         related_name='messages')
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Response Quality (for AI messages)
    was_helpful = models.BooleanField(null=True, blank=True)
    required_human_intervention = models.BooleanField(default=False)
    escalated_to_staff = models.BooleanField(default=False)
    escalated_to = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='escalated_messages')
    
    # User Feedback
    user_rating = models.IntegerField(null=True, blank=True,
                                     validators=[MinValueValidator(1), MaxValueValidator(5)])
    user_feedback = models.TextField(blank=True)
    
    # Timing
    response_time = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                       help_text="Response time in seconds")
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Related Content
    suggested_actions = models.JSONField(default=list, 
                                        help_text="Quick action buttons shown to user")
    attached_files = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.message_type} - {self.message_text[:50]}"

    class Meta:
        db_table = 'chat_messages'
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['session', 'timestamp']),
            models.Index(fields=['message_type', 'detected_intent']),
        ]


class AIPersonalization(models.Model):
    """Store user-specific AI personalization data"""
    user = models.OneToOneField('User', on_delete=models.CASCADE, 
                                related_name='ai_personalization')
    student = models.OneToOneField('Student', on_delete=models.CASCADE, null=True, blank=True,
                                  related_name='ai_personalization')
    
    # Learning Preferences
    preferred_response_style = models.CharField(max_length=20, 
                                               choices=(
                                                   ('concise', 'Concise'),
                                                   ('detailed', 'Detailed'),
                                                   ('balanced', 'Balanced'),
                                               ), default='balanced')
    preferred_language = models.CharField(max_length=10, default='en')
    
    # Interaction Patterns
    common_queries = models.JSONField(default=list, 
                                     help_text="Frequently asked questions by this user")
    interaction_history = models.JSONField(default=dict, 
                                          help_text="Topic frequency and patterns")
    time_preferences = models.JSONField(default=dict, 
                                       help_text="When user typically asks questions")
    
    # Context Memory
    remembered_context = models.JSONField(default=dict, 
                                         help_text="User's ongoing situations/interests")
    follow_up_reminders = models.JSONField(default=list, 
                                          help_text="Things AI should follow up on")
    
    # Performance Tracking
    academic_alerts = models.JSONField(default=list, 
                                      help_text="Proactive alerts about academic performance")
    financial_alerts = models.JSONField(default=list, 
                                       help_text="Fee payment reminders")
    
    # Privacy Settings
    allow_proactive_messages = models.BooleanField(default=True)
    allow_performance_tracking = models.BooleanField(default=True)
    allow_personalization = models.BooleanField(default=True)
    
    # Usage Statistics
    total_sessions = models.IntegerField(default=0)
    total_messages = models.IntegerField(default=0)
    avg_satisfaction = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    last_interaction = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Personalization - {self.user.username}"

    class Meta:
        db_table = 'ai_personalization'


class AITrainingData(models.Model):
    """Collect data for continuous AI improvement"""
    TRAINING_STATUS = (
        ('pending', 'Pending Review'),
        ('approved', 'Approved for Training'),
        ('rejected', 'Rejected'),
        ('trained', 'Used in Training'),
    )
    
    # Source Information
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, 
                               related_name='training_data')
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, 
                               related_name='training_data')
    
    # Training Content
    original_query = models.TextField()
    ai_response = models.TextField()
    corrected_response = models.TextField(blank=True, 
                                         help_text="Human-corrected version if needed")
    
    # Quality Metrics
    was_correct = models.BooleanField(null=True, blank=True)
    user_satisfaction = models.IntegerField(null=True, blank=True,
                                           validators=[MinValueValidator(1), MaxValueValidator(5)])
    
    # Training Metadata
    category = models.CharField(max_length=20, 
                               choices=AIKnowledgeBase.KNOWLEDGE_TYPES)
    detected_issues = models.JSONField(default=list, 
                                      help_text="Issues detected (wrong info, unclear, etc.)")
    
    # Review Process
    status = models.CharField(max_length=20, choices=TRAINING_STATUS, default='pending')
    reviewed_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='training_data_reviewed')
    review_date = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    
    # Training Integration
    added_to_knowledge_base = models.BooleanField(default=False)
    knowledge_entry = models.ForeignKey(AIKnowledgeBase, on_delete=models.SET_NULL, 
                                       null=True, blank=True,
                                       related_name='training_sources')
    training_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Training Data - {self.category} - {self.status}"

    class Meta:
        db_table = 'ai_training_data'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'category']),
            models.Index(fields=['was_correct']),
        ]


class AIAnalytics(models.Model):
    """Daily analytics and metrics for AI performance"""
    # Time Period
    date = models.DateField(unique=True)
    academic_year = models.ForeignKey('AcademicYear', on_delete=models.CASCADE,
                                     related_name='ai_analytics')
    
    # Usage Metrics
    total_sessions = models.IntegerField(default=0)
    authenticated_sessions = models.IntegerField(default=0)
    anonymous_sessions = models.IntegerField(default=0)
    total_messages = models.IntegerField(default=0)
    avg_messages_per_session = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    
    # Performance Metrics
    avg_response_time = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    avg_confidence_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    successful_resolutions = models.IntegerField(default=0)
    escalated_to_human = models.IntegerField(default=0)
    
    # Quality Metrics
    avg_user_rating = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    helpful_responses = models.IntegerField(default=0)
    not_helpful_responses = models.IntegerField(default=0)
    
    # Topic Distribution
    topic_breakdown = models.JSONField(default=dict, 
                                      help_text="Count of questions per category")
    peak_hours = models.JSONField(default=list, 
                                 help_text="Hours with most activity")
    
    # User Engagement
    new_users = models.IntegerField(default=0)
    returning_users = models.IntegerField(default=0)
    avg_session_duration = models.IntegerField(default=0, help_text="In seconds")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AI Analytics - {self.date}"

    class Meta:
        db_table = 'ai_analytics'
        ordering = ['-date']


class ProactiveAIAlert(models.Model):
    """AI-generated proactive alerts for students"""
    ALERT_TYPES = (
        ('academic_risk', 'Academic Performance Risk'),
        ('fee_reminder', 'Fee Payment Reminder'),
        ('deadline_approaching', 'Deadline Approaching'),
        ('low_attendance', 'Low Attendance Alert'),
        ('registration_open', 'Registration Period Open'),
        ('results_available', 'Results Available'),
        ('event_reminder', 'Event Reminder'),
        ('mental_health', 'Mental Health Check-in'),
        ('career_opportunity', 'Career Opportunity'),
        ('library_overdue', 'Library Book Overdue'),
        ('hostel_payment', 'Hostel Payment Due'),
        ('id_card_ready', 'ID Card Ready for Pickup'),
    )
    
    PRIORITY_LEVELS = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    # Alert Details
    alert_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='ai_alerts')
    student = models.ForeignKey('Student', on_delete=models.CASCADE, null=True, blank=True,
                               related_name='ai_alerts')
    
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    
    # Content
    title = models.CharField(max_length=200)
    message = models.TextField()
    action_required = models.TextField(blank=True, help_text="What the student should do")
    action_links = models.JSONField(default=list, help_text="Links to relevant pages")
    
    # AI Context
    trigger_data = models.JSONField(default=dict, 
                                   help_text="Data that triggered this alert")
    ai_reasoning = models.TextField(blank=True, 
                                   help_text="Why AI generated this alert")
    
    # Related Objects (Generic relation)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, 
                                    null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')
    
    # Delivery
    sent_via_chat = models.BooleanField(default=True)
    sent_via_email = models.BooleanField(default=False)
    sent_via_sms = models.BooleanField(default=False)
    sent_via_push = models.BooleanField(default=False)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    is_dismissed = models.BooleanField(default=False)
    dismissed_at = models.DateTimeField(null=True, blank=True)
    action_taken = models.BooleanField(default=False)
    action_taken_at = models.DateTimeField(null=True, blank=True)
    
    # Feedback
    was_helpful = models.BooleanField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    
    # Scheduling
    scheduled_for = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.alert_type} - {self.user.username} - {self.priority}"

    class Meta:
        db_table = 'proactive_ai_alerts'
        ordering = ['-priority', '-sent_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['alert_type', 'priority']),
            models.Index(fields=['-sent_at']),
        ]


class AIModelVersion(models.Model):
    """Track different versions of AI models and their performance"""
    MODEL_TYPES = (
        ('intent_classification', 'Intent Classification'),
        ('entity_extraction', 'Entity Extraction'),
        ('response_generation', 'Response Generation'),
        ('sentiment_analysis', 'Sentiment Analysis'),
        ('recommendation', 'Recommendation Engine'),
    )
    
    # Version Details
    model_type = models.CharField(max_length=30, choices=MODEL_TYPES)
    version_number = models.CharField(max_length=20)
    version_name = models.CharField(max_length=100)
    
    # Model Information
    training_data_size = models.IntegerField(help_text="Number of training examples")
    training_date = models.DateTimeField()
    training_duration_hours = models.DecimalField(max_digits=8, decimal_places=2)
    
    # Model Architecture
    architecture_details = models.JSONField(default=dict)
    hyperparameters = models.JSONField(default=dict)
    
    # Performance Metrics
    accuracy = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    precision = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    recall = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    f1_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Deployment
    is_active = models.BooleanField(default=False)
    deployed_at = models.DateTimeField(null=True, blank=True)
    deployment_environment = models.CharField(max_length=20, default='production')
    
    # Monitoring
    total_predictions = models.IntegerField(default=0)
    successful_predictions = models.IntegerField(default=0)
    avg_inference_time = models.DecimalField(max_digits=8, decimal_places=2, default=0.00,
                                            help_text="In milliseconds")
    
    # Notes
    release_notes = models.TextField(blank=True)
    known_issues = models.TextField(blank=True)
    improvements = models.TextField(blank=True)
    
    created_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True,
                                  related_name='ai_model_versions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.model_type} - v{self.version_number}"

    class Meta:
        db_table = 'ai_model_versions'
        unique_together = ('model_type', 'version_number')
        ordering = ['-created_at']


class QuickAction(models.Model):
    """Predefined quick actions for common tasks"""
    ACTION_TYPES = (
        ('navigation', 'Navigate to Page'),
        ('form', 'Fill Form'),
        ('download', 'Download Document'),
        ('payment', 'Make Payment'),
        ('booking', 'Make Booking'),
        ('external_link', 'External Link'),
    )
    
    # Action Details
    name = models.CharField(max_length=100)
    description = models.TextField()
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    icon = models.CharField(max_length=50, blank=True)
    
    # Action Configuration
    target_url = models.CharField(max_length=500, blank=True)
    requires_authentication = models.BooleanField(default=False)
    applicable_roles = models.JSONField(default=list)
    
    # Pre-fill Data
    prefill_fields = models.JSONField(default=dict, 
                                     help_text="Fields to auto-fill when action is triggered")
    
    # Visibility
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    
    # Context
    related_categories = models.JSONField(default=list, 
                                         help_text="AI categories this action relates to")
    trigger_keywords = models.JSONField(default=list)
    
    # Usage Stats
    usage_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'quick_actions'
        ordering = ['display_order', 'name']
        
        
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class FAQ(models.Model):
    """Frequently Asked Questions"""
    CATEGORIES = (
        ('academic', 'Academic'),
        ('finance', 'Finance'),
        ('hostel', 'Hostel'),
        ('library', 'Library'),
        ('technical', 'Technical'),
        ('general', 'General'),
    )
    
    category = models.CharField(max_length=20, choices=CATEGORIES)
    question = models.TextField()
    answer = models.TextField()
    display_order = models.IntegerField(default=0)
    views_count = models.IntegerField(default=0)
    is_helpful_count = models.IntegerField(default=0)
    is_not_helpful_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'faqs'
        ordering = ['category', 'display_order', '-views_count']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'

    def __str__(self):
        return f"{self.category} - {self.question[:50]}"


class SupportTicket(models.Model):
    """Student support tickets/issues"""
    PRIORITY_LEVELS = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    TICKET_STATUS = (
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('waiting_response', 'Waiting for Response'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    )
    
    CATEGORIES = (
        ('academic', 'Academic Issue'),
        ('finance', 'Finance/Fees'),
        ('hostel', 'Hostel/Accommodation'),
        ('library', 'Library Services'),
        ('technical', 'Technical/Portal'),
        ('id_card', 'Student ID Card'),
        ('results', 'Results/Grades'),
        ('registration', 'Registration'),
        ('other', 'Other'),
    )
    
    ticket_number = models.CharField(max_length=50, unique=True)
    student = models.ForeignKey('Student', on_delete=models.CASCADE, 
                                related_name='support_tickets')
    category = models.CharField(max_length=20, choices=CATEGORIES)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    subject = models.CharField(max_length=300)
    description = models.TextField()
    attachment = models.FileField(upload_to='support_tickets/', null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=TICKET_STATUS, default='open')
    assigned_to = models.ForeignKey('User', on_delete=models.SET_NULL, 
                                    null=True, blank=True,
                                    related_name='assigned_tickets')
    
    resolution_notes = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey('User', on_delete=models.SET_NULL,
                                    null=True, blank=True,
                                    related_name='resolved_tickets')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'support_tickets'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.ticket_number} - {self.subject}"

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            # Generate ticket number: TICK-YYYY-NNNN
            from django.db.models import Max
            year = timezone.now().year
            last_ticket = SupportTicket.objects.filter(
                ticket_number__startswith=f'TICK-{year}-'
            ).aggregate(Max('id'))
            
            next_id = (last_ticket['id__max'] or 0) + 1
            self.ticket_number = f'TICK-{year}-{next_id:04d}'
        
        super().save(*args, **kwargs)


class TicketReply(models.Model):
    """Replies to support tickets"""
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE,
                               related_name='replies')
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    message = models.TextField()
    attachment = models.FileField(upload_to='ticket_replies/', null=True, blank=True)
    is_staff_reply = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ticket_replies'
        ordering = ['created_at']
        verbose_name_plural = 'Ticket Replies'

    def __str__(self):
        return f"Reply to {self.ticket.ticket_number}"


class SystemGuide(models.Model):
    """System guides and tutorials"""
    GUIDE_TYPES = (
        ('getting_started', 'Getting Started'),
        ('academic', 'Academic'),
        ('finance', 'Finance'),
        ('hostel', 'Hostel'),
        ('library', 'Library'),
        ('profile', 'Profile Management'),
        ('troubleshooting', 'Troubleshooting'),
    )
    
    title = models.CharField(max_length=200)
    guide_type = models.CharField(max_length=20, choices=GUIDE_TYPES)
    description = models.TextField()
    content = models.TextField()
    video_url = models.URLField(blank=True, help_text="YouTube or video link")
    pdf_file = models.FileField(upload_to='system_guides/', null=True, blank=True)
    display_order = models.IntegerField(default=0)
    views_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'system_guides'
        ordering = ['guide_type', 'display_order']

    def __str__(self):
        return self.title


class ContactInfo(models.Model):
    """Contact information for different departments"""
    department = models.CharField(max_length=100)
    email = models.EmailField()
    phone_primary = models.CharField(max_length=15)
    phone_secondary = models.CharField(max_length=15, blank=True)
    office_location = models.CharField(max_length=200, blank=True)
    office_hours = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'contact_info'
        ordering = ['display_order', 'department']
        verbose_name = 'Contact Information'
        verbose_name_plural = 'Contact Information'

    def __str__(self):
        return self.department
    
    
"""
Missing Models for Dean Functionality
Add these to your existing models.py file
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal


# ============= QUALITY ASSURANCE MODELS =============

class TeachingEvaluation(models.Model):
    """Student evaluations of teaching quality"""
    EVALUATION_STATUS = (
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('published', 'Published'),
    )
    
    unit_allocation = models.ForeignKey('UnitAllocation', on_delete=models.CASCADE, 
                                       related_name='teaching_evaluations')
    academic_year = models.ForeignKey('AcademicYear', on_delete=models.CASCADE, 
                                     related_name='teaching_evaluations')
    semester = models.ForeignKey('Semester', on_delete=models.CASCADE, 
                                 related_name='teaching_evaluations')
    
    # Evaluation period
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=EVALUATION_STATUS, default='open')
    
    # Results summary
    total_responses = models.IntegerField(default=0)
    total_enrolled = models.IntegerField(default=0)
    response_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Average ratings (1-5 scale)
    avg_content_delivery = models.DecimalField(max_digits=3, decimal_places=2, 
                                               default=0.00, validators=[MinValueValidator(0), MaxValueValidator(5)])
    avg_engagement = models.DecimalField(max_digits=3, decimal_places=2, 
                                        default=0.00, validators=[MinValueValidator(0), MaxValueValidator(5)])
    avg_assessment_fairness = models.DecimalField(max_digits=3, decimal_places=2, 
                                                  default=0.00, validators=[MinValueValidator(0), MaxValueValidator(5)])
    avg_availability = models.DecimalField(max_digits=3, decimal_places=2, 
                                          default=0.00, validators=[MinValueValidator(0), MaxValueValidator(5)])
    overall_rating = models.DecimalField(max_digits=3, decimal_places=2, 
                                        default=0.00, validators=[MinValueValidator(0), MaxValueValidator(5)])
    
    # Feedback
    positive_comments = models.TextField(blank=True)
    improvement_areas = models.TextField(blank=True)
    
    is_published = models.BooleanField(default=False)
    published_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.unit_allocation.programme_unit.unit.code} - {self.semester}"

    class Meta:
        db_table = 'teaching_evaluations'
        ordering = ['-created_at']
        unique_together = ('unit_allocation', 'semester')


class ProgrammeReview(models.Model):
    """Periodic reviews of academic programmes"""
    REVIEW_STATUS = (
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('published', 'Published'),
    )
    
    REVIEW_TYPE = (
        ('annual', 'Annual Review'),
        ('periodic', 'Periodic Review'),
        ('accreditation', 'Accreditation Review'),
        ('external', 'External Review'),
    )
    
    programme = models.ForeignKey('Programme', on_delete=models.CASCADE, 
                                  related_name='reviews')
    review_type = models.CharField(max_length=20, choices=REVIEW_TYPE)
    academic_year = models.ForeignKey('AcademicYear', on_delete=models.CASCADE, 
                                     related_name='programme_reviews')
    
    # Review details
    review_date = models.DateField()
    review_panel = models.TextField(help_text="Names and roles of review panel members")
    
    # Review findings
    strengths = models.TextField()
    weaknesses = models.TextField()
    opportunities = models.TextField()
    threats = models.TextField()
    
    # Recommendations
    recommendations = models.TextField()
    action_plan = models.TextField(blank=True)
    
    # Ratings
    curriculum_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    teaching_quality_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    resources_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    student_satisfaction_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    employability_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    overall_rating = models.DecimalField(max_digits=3, decimal_places=2)
    
    # Follow-up
    follow_up_date = models.DateField(null=True, blank=True)
    follow_up_notes = models.TextField(blank=True)
    
    status = models.CharField(max_length=20, choices=REVIEW_STATUS, default='scheduled')
    conducted_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, 
                                    related_name='programme_reviews_conducted')
    approved_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='programme_reviews_approved')
    
    report_document = models.FileField(upload_to='programme_reviews/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Calculate overall rating
        self.overall_rating = (
            self.curriculum_rating +
            self.teaching_quality_rating +
            self.resources_rating +
            self.student_satisfaction_rating +
            self.employability_rating
        ) / 5.0
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.programme.code} - {self.review_type} - {self.review_date}"

    class Meta:
        db_table = 'programme_reviews'
        ordering = ['-review_date']


class AuditReport(models.Model):
    """Quality audit reports"""
    AUDIT_TYPE = (
        ('internal', 'Internal Audit'),
        ('external', 'External Audit'),
        ('financial', 'Financial Audit'),
        ('academic', 'Academic Audit'),
        ('compliance', 'Compliance Audit'),
    )
    
    AUDIT_STATUS = (
        ('planned', 'Planned'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('closed', 'Closed'),
    )
    
    school = models.ForeignKey('School', on_delete=models.CASCADE, 
                              related_name='audit_reports', null=True, blank=True)
    department = models.ForeignKey('Department', on_delete=models.CASCADE, 
                                  related_name='audit_reports', null=True, blank=True)
    audit_type = models.CharField(max_length=20, choices=AUDIT_TYPE)
    academic_year = models.ForeignKey('AcademicYear', on_delete=models.CASCADE, 
                                     related_name='audit_reports')
    
    # Audit details
    audit_number = models.CharField(max_length=50, unique=True)
    audit_date = models.DateField()
    auditor_name = models.CharField(max_length=200)
    auditor_organization = models.CharField(max_length=200, blank=True)
    
    # Findings
    executive_summary = models.TextField()
    key_findings = models.TextField()
    non_conformities = models.TextField(blank=True)
    observations = models.TextField(blank=True)
    
    # Recommendations
    recommendations = models.TextField()
    management_response = models.TextField(blank=True)
    corrective_actions = models.TextField(blank=True)
    
    # Timeline
    implementation_deadline = models.DateField(null=True, blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=AUDIT_STATUS, default='planned')
    audit_document = models.FileField(upload_to='audit_reports/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.audit_number:
            year = timezone.now().year
            from django.db.models import Max
            last_audit = AuditReport.objects.filter(
                audit_number__startswith=f'AUD-{year}-'
            ).aggregate(Max('id'))
            next_id = (last_audit['id__max'] or 0) + 1
            self.audit_number = f'AUD-{year}-{next_id:04d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.audit_number} - {self.audit_type}"

    class Meta:
        db_table = 'audit_reports'
        ordering = ['-audit_date']


class ComplianceCheck(models.Model):
    """Compliance monitoring records"""
    COMPLIANCE_STATUS = (
        ('compliant', 'Compliant'),
        ('non_compliant', 'Non-Compliant'),
        ('partially_compliant', 'Partially Compliant'),
        ('under_review', 'Under Review'),
    )
    
    COMPLIANCE_AREA = (
        ('academic', 'Academic Standards'),
        ('financial', 'Financial Regulations'),
        ('health_safety', 'Health & Safety'),
        ('data_protection', 'Data Protection'),
        ('employment', 'Employment Laws'),
        ('accreditation', 'Accreditation Requirements'),
    )
    
    school = models.ForeignKey('School', on_delete=models.CASCADE, 
                              related_name='compliance_checks')
    compliance_area = models.CharField(max_length=20, choices=COMPLIANCE_AREA)
    academic_year = models.ForeignKey('AcademicYear', on_delete=models.CASCADE, 
                                     related_name='compliance_checks')
    
    # Check details
    check_date = models.DateField()
    requirement = models.TextField(help_text="Specific requirement being checked")
    criteria = models.TextField(help_text="Compliance criteria")
    
    # Status
    status = models.CharField(max_length=20, choices=COMPLIANCE_STATUS)
    evidence = models.TextField(help_text="Evidence of compliance")
    gaps = models.TextField(blank=True, help_text="Compliance gaps identified")
    
    # Actions
    action_required = models.BooleanField(default=False)
    action_plan = models.TextField(blank=True)
    responsible_person = models.ForeignKey('User', on_delete=models.SET_NULL, null=True,
                                          related_name='compliance_responsibilities')
    deadline = models.DateField(null=True, blank=True)
    
    # Follow-up
    is_resolved = models.BooleanField(default=False)
    resolution_date = models.DateField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    checked_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True,
                                  related_name='compliance_checks_conducted')
    supporting_documents = models.FileField(upload_to='compliance/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.school.code} - {self.compliance_area} - {self.check_date}"

    class Meta:
        db_table = 'compliance_checks'
        ordering = ['-check_date']


class QualityMetric(models.Model):
    """Quality metrics and KPIs tracking"""
    METRIC_TYPE = (
        ('academic', 'Academic Performance'),
        ('satisfaction', 'Student Satisfaction'),
        ('retention', 'Student Retention'),
        ('graduation', 'Graduation Rate'),
        ('employability', 'Graduate Employability'),
        ('research', 'Research Output'),
        ('teaching', 'Teaching Quality'),
    )
    
    MEASUREMENT_PERIOD = (
        ('semester', 'Semester'),
        ('annual', 'Annual'),
        ('quarterly', 'Quarterly'),
    )
    
    school = models.ForeignKey('School', on_delete=models.CASCADE, 
                              related_name='quality_metrics')
    programme = models.ForeignKey('Programme', on_delete=models.CASCADE, 
                                 related_name='quality_metrics', null=True, blank=True)
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPE)
    academic_year = models.ForeignKey('AcademicYear', on_delete=models.CASCADE, 
                                     related_name='quality_metrics')
    measurement_period = models.CharField(max_length=20, choices=MEASUREMENT_PERIOD)
    
    # Metric details
    metric_name = models.CharField(max_length=200)
    description = models.TextField()
    target_value = models.DecimalField(max_digits=10, decimal_places=2)
    actual_value = models.DecimalField(max_digits=10, decimal_places=2)
    unit_of_measure = models.CharField(max_length=50, help_text="%, number, rating, etc.")
    
    # Performance
    is_target_met = models.BooleanField(default=False)
    variance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    variance_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Analysis
    trend = models.CharField(max_length=20, choices=(
        ('improving', 'Improving'),
        ('declining', 'Declining'),
        ('stable', 'Stable'),
    ), default='stable')
    comments = models.TextField(blank=True)
    action_items = models.TextField(blank=True)
    
    measurement_date = models.DateField()
    recorded_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True,
                                   related_name='metrics_recorded')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Calculate variance and check if target met
        self.variance = self.actual_value - self.target_value
        if self.target_value != 0:
            self.variance_percentage = (self.variance / self.target_value) * 100
        self.is_target_met = self.actual_value >= self.target_value
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.metric_name} - {self.academic_year}"

    class Meta:
        db_table = 'quality_metrics'
        ordering = ['-measurement_date']


# ============= RESEARCH & INNOVATION MODELS =============

class ResearchProject(models.Model):
    """Research projects"""
    PROJECT_STATUS = (
        ('proposal', 'Proposal'),
        ('approved', 'Approved'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    PROJECT_TYPE = (
        ('basic', 'Basic Research'),
        ('applied', 'Applied Research'),
        ('collaborative', 'Collaborative Research'),
        ('consultancy', 'Consultancy'),
    )
    
    title = models.CharField(max_length=500)
    project_code = models.CharField(max_length=50, unique=True)
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPE)
    school = models.ForeignKey('School', on_delete=models.CASCADE, 
                              related_name='research_projects')
    department = models.ForeignKey('Department', on_delete=models.CASCADE, 
                                  related_name='research_projects')
    
    # Team
    principal_investigator = models.ForeignKey('Lecturer', on_delete=models.CASCADE,
                                              related_name='research_projects_pi')
    co_investigators = models.ManyToManyField('Lecturer', related_name='research_projects_co', blank=True)
    
    # Project details
    abstract = models.TextField()
    objectives = models.TextField()
    methodology = models.TextField()
    expected_outcomes = models.TextField()
    
    # Timeline
    start_date = models.DateField()
    end_date = models.DateField()
    duration_months = models.IntegerField()
    
    # Funding
    total_budget = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    funding_source = models.CharField(max_length=200, blank=True)
    funds_allocated = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    funds_utilized = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    status = models.CharField(max_length=20, choices=PROJECT_STATUS, default='proposal')
    
    # Outputs
    publications_count = models.IntegerField(default=0)
    patents_count = models.IntegerField(default=0)
    
    approved_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='research_projects_approved')
    approval_date = models.DateField(null=True, blank=True)
    
    proposal_document = models.FileField(upload_to='research/proposals/', null=True, blank=True)
    final_report = models.FileField(upload_to='research/reports/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project_code} - {self.title[:50]}"

    class Meta:
        db_table = 'research_projects'
        ordering = ['-created_at']


class ResearchGrant(models.Model):
    """Research grants and funding"""
    GRANT_STATUS = (
        ('applied', 'Application Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('active', 'Active'),
        ('completed', 'Completed'),
    )
    
    GRANT_TYPE = (
        ('internal', 'Internal Grant'),
        ('external', 'External Grant'),
        ('government', 'Government Grant'),
        ('private', 'Private Sector'),
        ('international', 'International'),
    )
    
    grant_title = models.CharField(max_length=500)
    grant_number = models.CharField(max_length=50, unique=True)
    grant_type = models.CharField(max_length=20, choices=GRANT_TYPE)
    funding_agency = models.CharField(max_length=200)
    
    # Applicants
    principal_applicant = models.ForeignKey('Lecturer', on_delete=models.CASCADE,
                                           related_name='grants_principal')
    co_applicants = models.ManyToManyField('Lecturer', related_name='grants_co', blank=True)
    school = models.ForeignKey('School', on_delete=models.CASCADE, 
                              related_name='research_grants')
    
    # Grant details
    amount_applied = models.DecimalField(max_digits=12, decimal_places=2)
    amount_awarded = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    application_date = models.DateField()
    decision_date = models.DateField(null=True, blank=True)
    
    # Project timeline
    project_start_date = models.DateField(null=True, blank=True)
    project_end_date = models.DateField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=GRANT_STATUS, default='applied')
    
    # Documents
    proposal_document = models.FileField(upload_to='grants/proposals/', null=True, blank=True)
    award_letter = models.FileField(upload_to='grants/awards/', null=True, blank=True)
    
    # Reporting
    progress_reports = models.TextField(blank=True)
    final_report_submitted = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.grant_number} - {self.grant_title[:50]}"

    class Meta:
        db_table = 'research_grants'
        ordering = ['-application_date']


class Publication(models.Model):
    """Academic publications"""
    PUBLICATION_TYPE = (
        ('journal', 'Journal Article'),
        ('conference', 'Conference Paper'),
        ('book', 'Book'),
        ('chapter', 'Book Chapter'),
        ('thesis', 'Thesis/Dissertation'),
        ('report', 'Technical Report'),
    )
    
    title = models.CharField(max_length=500)
    publication_type = models.CharField(max_length=20, choices=PUBLICATION_TYPE)
    
    # Authors
    authors = models.ManyToManyField('Lecturer', related_name='publications')
    corresponding_author = models.ForeignKey('Lecturer', on_delete=models.CASCADE,
                                            related_name='publications_corresponding')
    school = models.ForeignKey('School', on_delete=models.CASCADE, 
                              related_name='publications')
    
    # Publication details
    journal_name = models.CharField(max_length=300, blank=True)
    conference_name = models.CharField(max_length=300, blank=True)
    publisher = models.CharField(max_length=200, blank=True)
    isbn_issn = models.CharField(max_length=50, blank=True)
    doi = models.CharField(max_length=100, blank=True)
    
    # Date
    publication_date = models.DateField()
    year = models.IntegerField()
    
    # Quality metrics
    is_peer_reviewed = models.BooleanField(default=False)
    impact_factor = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    citations_count = models.IntegerField(default=0)
    
    # Links
    url = models.URLField(blank=True)
    pdf_file = models.FileField(upload_to='publications/', null=True, blank=True)
    
    # Research project link
    research_project = models.ForeignKey(ResearchProject, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='publications')
    
    abstract = models.TextField(blank=True)
    keywords = models.CharField(max_length=500, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title[:100]}"

    class Meta:
        db_table = 'publications'
        ordering = ['-publication_date']


class ResearchCenter(models.Model):
    """Research centers and institutes"""
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    school = models.ForeignKey('School', on_delete=models.CASCADE, 
                              related_name='research_centers')
    
    # Leadership
    director = models.ForeignKey('Lecturer', on_delete=models.SET_NULL, null=True,
                                 related_name='research_centers_directed')
    deputy_director = models.ForeignKey('Lecturer', on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='research_centers_deputy')
    
    # Details
    description = models.TextField()
    focus_areas = models.TextField(help_text="Main research focus areas")
    objectives = models.TextField()
    
    # Resources
    location = models.CharField(max_length=200, blank=True)
    facilities = models.TextField(blank=True)
    annual_budget = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Contact
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    website = models.URLField(blank=True)
    
    # Status
    establishment_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        db_table = 'research_centers'
        ordering = ['name']



# ============= HUMAN RESOURCES MODELS =============

class StaffRecruitment(models.Model):
    """Staff recruitment tracking"""
    POSITION_TYPE = (
        ('lecturer', 'Lecturer'),
        ('senior_lecturer', 'Senior Lecturer'),
        ('professor', 'Professor'),
        ('technician', 'Technician'),
        ('administrator', 'Administrator'),
        ('support_staff', 'Support Staff'),
    )
    
    RECRUITMENT_STATUS = (
        ('open', 'Open'),
        ('shortlisting', 'Shortlisting'),
        ('interviewing', 'Interviewing'),
        ('offer_made', 'Offer Made'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('closed', 'Closed'),
    )
    
    CONTRACT_TYPE = (
        ('permanent', 'Permanent & Pensionable'),
        ('contract', 'Contract'),
        ('part_time', 'Part-Time'),
        ('visiting', 'Visiting'),
    )
    
    recruitment_number = models.CharField(max_length=50, unique=True)
    school = models.ForeignKey('School', on_delete=models.CASCADE, 
                              related_name='staff_recruitments')
    department = models.ForeignKey('Department', on_delete=models.CASCADE, 
                                  related_name='staff_recruitments')
    academic_year = models.ForeignKey('AcademicYear', on_delete=models.CASCADE,
                                     related_name='staff_recruitments')
    
    # Position details
    position_title = models.CharField(max_length=200)
    position_type = models.CharField(max_length=20, choices=POSITION_TYPE)
    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPE, default='permanent')
    number_of_positions = models.IntegerField(default=1)
    salary_scale = models.CharField(max_length=100, blank=True)
    
    # Requirements
    qualifications_required = models.TextField()
    experience_required = models.TextField()
    responsibilities = models.TextField()
    key_competencies = models.TextField(blank=True)
    
    # Job details
    job_description = models.TextField(blank=True)
    reporting_to = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=200, blank=True)
    
    # Timeline
    advertised_date = models.DateField()
    application_deadline = models.DateField()
    shortlisting_date = models.DateField(null=True, blank=True)
    interview_date = models.DateField(null=True, blank=True)
    expected_start_date = models.DateField(null=True, blank=True)
    
    # Applications
    total_applications = models.IntegerField(default=0)
    shortlisted_candidates = models.IntegerField(default=0)
    interviewed_candidates = models.IntegerField(default=0)
    
    # Interview panel
    interview_panel_members = models.TextField(blank=True, 
                                              help_text="Names and titles of panel members")
    interview_venue = models.CharField(max_length=200, blank=True)
    
    # Selection
    status = models.CharField(max_length=20, choices=RECRUITMENT_STATUS, default='open')
    selected_candidate_name = models.CharField(max_length=200, blank=True)
    selected_candidate_email = models.EmailField(blank=True)
    selected_candidate_phone = models.CharField(max_length=20, blank=True)
    
    # Offer details
    offer_letter_sent = models.BooleanField(default=False)
    offer_sent_date = models.DateField(null=True, blank=True)
    offer_expiry_date = models.DateField(null=True, blank=True)
    offer_accepted_date = models.DateField(null=True, blank=True)
    
    # Contract details
    contract_start_date = models.DateField(null=True, blank=True)
    contract_end_date = models.DateField(null=True, blank=True)
    probation_period_months = models.IntegerField(null=True, blank=True)
    
    # Approvals
    approved_by_hod = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='recruitments_approved_hod')
    approved_by_dean = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='recruitments_approved_dean')
    approved_by_hr = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='recruitments_approved_hr')
    
    # Documents
    job_advertisement = models.FileField(upload_to='recruitments/ads/', null=True, blank=True)
    shortlisting_report = models.FileField(upload_to='recruitments/shortlist/', null=True, blank=True)
    interview_report = models.FileField(upload_to='recruitments/interviews/', null=True, blank=True)
    offer_letter = models.FileField(upload_to='recruitments/offers/', null=True, blank=True)
    
    # Notes and reasons
    recruitment_justification = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    closure_notes = models.TextField(blank=True)
    
    # Tracking
    initiated_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True,
                                    related_name='recruitments_initiated')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.recruitment_number:
            from django.db.models import Max
            # Generate recruitment number: REC-YYYY-SCHOOL-NNN
            year = timezone.now().year
            school_code = self.school.code
            last_recruitment = StaffRecruitment.objects.filter(
                recruitment_number__startswith=f'REC-{year}-{school_code}-'
            ).aggregate(Max('id'))
            next_id = (last_recruitment['id__max'] or 0) + 1
            self.recruitment_number = f'REC-{year}-{school_code}-{next_id:03d}'
        
        super().save(*args, **kwargs)

    def is_deadline_passed(self):
        """Check if application deadline has passed"""
        return timezone.now().date() > self.application_deadline

    def days_until_deadline(self):
        """Calculate days remaining until deadline"""
        if self.is_deadline_passed():
            return 0
        delta = self.application_deadline - timezone.now().date()
        return delta.days

    def __str__(self):
        return f"{self.recruitment_number} - {self.position_title}"

    class Meta:
        db_table = 'staff_recruitments'
        ordering = ['-advertised_date']
        indexes = [
            models.Index(fields=['school', 'status']),
            models.Index(fields=['application_deadline']),
        ]
    
class InnovationProject(models.Model):
    """Innovation and commercialization projects"""
    PROJECT_STATUS = (
        ('ideation', 'Ideation'),
        ('development', 'Development'),
        ('prototype', 'Prototype'),
        ('testing', 'Testing'),
        ('commercialization', 'Commercialization'),
        ('completed', 'Completed'),
    )
    
    title = models.CharField(max_length=500)
    project_code = models.CharField(max_length=50, unique=True)
    school = models.ForeignKey('School', on_delete=models.CASCADE, 
                              related_name='innovation_projects')
    
    # Team
    project_lead = models.ForeignKey('Lecturer', on_delete=models.CASCADE,
                                    related_name='innovation_projects_lead')
    team_members = models.ManyToManyField('Lecturer', related_name='innovation_projects', blank=True)
    
    # Project details
    description = models.TextField()
    problem_statement = models.TextField()
    solution = models.TextField()
    innovation_type = models.CharField(max_length=200, help_text="Product, Service, Process, etc.")
    
    # Development
    status = models.CharField(max_length=20, choices=PROJECT_STATUS, default='ideation')
    technology_readiness_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(9)],
        help_text="TRL 1-9"
    )
    
    # IP and Commercialization
    has_ip_protection = models.BooleanField(default=False)
    ip_type = models.CharField(max_length=100, blank=True, help_text="Patent, Copyright, Trademark, etc.")
    ip_reference = models.CharField(max_length=100, blank=True)
    
    market_potential = models.TextField(blank=True)
    target_market = models.CharField(max_length=300, blank=True)
    
    # Funding
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    funding_received = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    revenue_generated = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Timeline
    start_date = models.DateField()
    expected_completion = models.DateField()
    actual_completion = models.DateField(null=True, blank=True)
    
    # Documents
    business_plan = models.FileField(upload_to='innovation/business_plans/', null=True, blank=True)
    technical_document = models.FileField(upload_to='innovation/technical/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project_code} - {self.title[:50]}"

    class Meta:
        db_table = 'innovation_projects'
        ordering = ['-created_at']


# ============= HUMAN RESOURCES MODELS =============

class PerformanceAppraisal(models.Model):
    """Staff performance appraisals"""
    APPRAISAL_PERIOD = (
        ('annual', 'Annual'),
        ('mid_year', 'Mid-Year'),
        ('probation', 'Probation Review'),
        ('special', 'Special Review'),
    )
    
    PERFORMANCE_RATING = (
        ('outstanding', 'Outstanding (90-100%)'),
        ('exceeds', 'Exceeds Expectations (80-89%)'),
        ('meets', 'Meets Expectations (70-79%)'),
        ('needs_improvement', 'Needs Improvement (60-69%)'),
        ('unsatisfactory', 'Unsatisfactory (<60%)'),
    )
    
    lecturer = models.ForeignKey('Lecturer', on_delete=models.CASCADE, 
                                 related_name='performance_appraisals')
    academic_year = models.ForeignKey('AcademicYear', on_delete=models.CASCADE, 
                                     related_name='performance_appraisals')
    appraisal_period = models.CharField(max_length=20, choices=APPRAISAL_PERIOD)
    review_date = models.DateField()
    
    # Performance Areas (1-100 scale)
    teaching_quality = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    research_output = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    service_delivery = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    student_feedback = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    professional_development = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Calculated scores
    overall_score = models.DecimalField(max_digits=5, decimal_places=2)
    overall_rating = models.CharField(max_length=20, choices=PERFORMANCE_RATING)
    
    # Qualitative feedback
    strengths = models.TextField()
    areas_for_improvement = models.TextField()
    training_needs = models.TextField(blank=True)
    career_development_plan = models.TextField(blank=True)
    
    # Goals and objectives
    goals_set = models.TextField(help_text="Goals set for next period")
    previous_goals_achievement = models.TextField(blank=True)
    
    # Approvals
    self_assessment = models.TextField(blank=True)
    hod_comments = models.TextField(blank=True)
    hod_approved_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='appraisals_hod_approved')
    dean_comments = models.TextField(blank=True)
    dean_approved_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='appraisals_dean_approved')
    
    appraisal_document = models.FileField(upload_to='appraisals/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Calculate overall score (weighted average)
        self.overall_score = (
            self.teaching_quality * 0.30 +
            self.research_output * 0.25 +
            self.service_delivery * 0.20 +
            self.student_feedback * 0.15 +
            self.professional_development * 0.10
        )
        
        # Determine rating
        if self.overall_score >= 90:
            self.overall_rating = 'outstanding'
        elif self.overall_score >= 80:
            self.overall_rating = 'exceeds'
        elif self.overall_score >= 70:
            self.overall_rating = 'meets'
        elif self.overall_score >= 60:
            self.overall_rating = 'needs_improvement'
        else:
            self.overall_rating = 'unsatisfactory'
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.lecturer.employee_number} - {self.appraisal_period} {self.academic_year}"

    class Meta:
        db_table = 'performance_appraisals'
        unique_together = ('lecturer', 'academic_year', 'appraisal_period')
        ordering = ['-review_date']


class StaffPromotion(models.Model):
    """Staff promotion tracking"""
    PROMOTION_STATUS = (
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('recommended', 'Recommended by School'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('implemented', 'Implemented'),
    )
    
    lecturer = models.ForeignKey('Lecturer', on_delete=models.CASCADE, 
                                 related_name='promotions')
    current_designation = models.CharField(max_length=30)
    proposed_designation = models.CharField(max_length=30)
    academic_year = models.ForeignKey('AcademicYear', on_delete=models.CASCADE, 
                                     related_name='staff_promotions')
    
    # Application details
    application_date = models.DateField()
    years_in_current_position = models.IntegerField()
    
    # Qualifications
    highest_qualification = models.CharField(max_length=200)
    additional_qualifications = models.TextField(blank=True)
    
    # Performance metrics
    teaching_years = models.IntegerField()
    publications_count = models.IntegerField(default=0)
    research_grants_count = models.IntegerField(default=0)
    phd_supervisions = models.IntegerField(default=0)
    
    # Justification
    justification = models.TextField()
    supporting_documents = models.FileField(upload_to='promotions/', null=True, blank=True)
    
    # Review process
    hod_recommendation = models.TextField(blank=True)
    hod_recommended_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name='promotions_hod_recommended')
    hod_recommendation_date = models.DateField(null=True, blank=True)
    
    school_recommendation = models.TextField(blank=True)
    dean_recommended_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True,
                                           related_name='promotions_dean_recommended')
    dean_recommendation_date = models.DateField(null=True, blank=True)
    
    # Final decision
    status = models.CharField(max_length=20, choices=PROMOTION_STATUS, default='pending')
    final_decision = models.TextField(blank=True)
    decided_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='promotions_decided')
    decision_date = models.DateField(null=True, blank=True)
    
    # Implementation
    effective_date = models.DateField(null=True, blank=True)
    new_salary_scale = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.lecturer.employee_number} - {self.current_designation} to {self.proposed_designation}"

    class Meta:
        db_table = 'staff_promotions'
        ordering = ['-application_date']


class StaffTraining(models.Model):
    """Staff development and training"""
    TRAINING_TYPE = (
        ('workshop', 'Workshop'),
        ('seminar', 'Seminar'),
        ('conference', 'Conference'),
        ('short_course', 'Short Course'),
        ('certification', 'Certification'),
        ('degree_program', 'Degree Program'),
    )
    
    TRAINING_STATUS = (
        ('planned', 'Planned'),
        ('approved', 'Approved'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    lecturer = models.ForeignKey('Lecturer', on_delete=models.CASCADE, 
                                 related_name='trainings')
    training_type = models.CharField(max_length=20, choices=TRAINING_TYPE)
    title = models.CharField(max_length=300)
    organizer = models.CharField(max_length=200)
    venue = models.CharField(max_length=200)
    
    # Dates
    start_date = models.DateField()
    end_date = models.DateField()
    duration_days = models.IntegerField()
    
    # Financial
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    funding_source = models.CharField(max_length=200, blank=True)
    is_sponsored = models.BooleanField(default=False)
    
    # Outcomes
    skills_acquired = models.TextField(blank=True)
    certificate_obtained = models.BooleanField(default=False)
    certificate_file = models.FileField(upload_to='training_certificates/', null=True, blank=True)
    
    # Relevance
    relevance_to_role = models.TextField()
    expected_impact = models.TextField()
    
    # Approval
    status = models.CharField(max_length=20, choices=TRAINING_STATUS, default='planned')
    approved_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='trainings_approved')
    approval_date = models.DateField(null=True, blank=True)
    
    # Post-training
    completion_report = models.TextField(blank=True)
    report_submitted_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.lecturer.employee_number} - {self.title}"

    class Meta:
        db_table = 'staff_training'
        ordering = ['-start_date']


class DisciplinaryCase(models.Model):
    """Staff disciplinary matters"""
    CASE_STATUS = (
        ('reported', 'Reported'),
        ('under_investigation', 'Under Investigation'),
        ('hearing_scheduled', 'Hearing Scheduled'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('appealed', 'Appealed'),
    )
    
    SEVERITY = (
        ('minor', 'Minor'),
        ('moderate', 'Moderate'),
        ('serious', 'Serious'),
        ('gross_misconduct', 'Gross Misconduct'),
    )
    
    case_number = models.CharField(max_length=50, unique=True)
    lecturer = models.ForeignKey('Lecturer', on_delete=models.CASCADE, 
                                 related_name='disciplinary_cases')
    academic_year = models.ForeignKey('AcademicYear', on_delete=models.CASCADE, 
                                     related_name='disciplinary_cases')
    
    # Case details
    incident_date = models.DateField()
    reported_date = models.DateField()
    reported_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True,
                                   related_name='disciplinary_cases_reported')
    
    allegation = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY)
    evidence = models.TextField(blank=True)
    witness_statements = models.TextField(blank=True)
    
    # Investigation
    investigating_officer = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True,
                                             related_name='disciplinary_investigations')
    investigation_findings = models.TextField(blank=True)
    investigation_completed_date = models.DateField(null=True, blank=True)
    
    # Hearing
    hearing_date = models.DateField(null=True, blank=True)
    hearing_venue = models.CharField(max_length=200, blank=True)
    hearing_panel = models.TextField(blank=True)
    hearing_minutes = models.TextField(blank=True)
    
    # Decision
    status = models.CharField(max_length=25, choices=CASE_STATUS, default='reported')
    decision = models.TextField(blank=True)
    disciplinary_action = models.TextField(blank=True)
    decided_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='disciplinary_decisions')
    decision_date = models.DateField(null=True, blank=True)
    
    # Appeal
    is_appealed = models.BooleanField(default=False)
    appeal_details = models.TextField(blank=True)
    appeal_decision = models.TextField(blank=True)
    
    # Documents
    supporting_documents = models.FileField(upload_to='disciplinary/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.case_number:
            year = timezone.now().year
            last_case = DisciplinaryCase.objects.filter(
                case_number__startswith=f'DISC-{year}-'
            ).aggregate(Max('id'))
            next_id = (last_case['id__max'] or 0) + 1
            self.case_number = f'DISC-{year}-{next_id:04d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.case_number} - {self.lecturer.employee_number}"

    class Meta:
        db_table = 'disciplinary_cases'
        ordering = ['-reported_date']
        
        
        
# ============= FINANCIAL MANAGEMENT MODELS =============

class SchoolBudget(models.Model):
    """Budget allocation for schools"""
    BUDGET_STATUS = (
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('active', 'Active'),
        ('closed', 'Closed'),
    )
    
    school = models.ForeignKey('School', on_delete=models.CASCADE, related_name='budgets')
    financial_year = models.ForeignKey('AcademicYear', on_delete=models.CASCADE, 
                                       related_name='school_budgets')
    
    # Budget amounts
    total_allocation = models.DecimalField(max_digits=15, decimal_places=2)
    amount_spent = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Budget breakdown
    personnel_budget = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    operations_budget = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    development_budget = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    research_budget = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    status = models.CharField(max_length=20, choices=BUDGET_STATUS, default='draft')
    
    # Approval workflow
    submitted_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='budgets_submitted')
    submitted_date = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='budgets_approved')
    approval_date = models.DateTimeField(null=True, blank=True)
    
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Calculate balance
        self.balance = self.total_allocation - self.amount_spent
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.school.code} - {self.financial_year.name}"

    class Meta:
        db_table = 'school_budgets'
        unique_together = ('school', 'financial_year')
        ordering = ['-financial_year__start_date']


class BudgetAllocation(models.Model):
    """Budget allocation to departments"""
    school_budget = models.ForeignKey(SchoolBudget, on_delete=models.CASCADE, 
                                     related_name='allocations')
    department = models.ForeignKey('Department', on_delete=models.CASCADE, 
                                  related_name='budget_allocations')
    
    # Allocation details
    allocation_amount = models.DecimalField(max_digits=15, decimal_places=2)
    amount_utilized = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    utilization_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    # Breakdown by category
    personnel = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    operations = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    equipment = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    supplies = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # CHANGED: Use different related_name to avoid clash
    allocated_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True,
                                    related_name='budget_allocations_made')  # Changed from 'allocations_made'
    allocation_date = models.DateField()
    remarks = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Calculate balance and utilization percentage
        self.balance = self.allocation_amount - self.amount_utilized
        if self.allocation_amount > 0:
            self.utilization_percentage = (self.amount_utilized / self.allocation_amount) * 100
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.department.code} - {self.school_budget.financial_year.name}"

    class Meta:
        db_table = 'budget_allocations'
        unique_together = ('school_budget', 'department')
        ordering = ['department__name']


class ExpenditureTracking(models.Model):
    """Track department expenditures"""
    EXPENDITURE_TYPE = (
        ('personnel', 'Personnel'),
        ('operations', 'Operations'),
        ('equipment', 'Equipment'),
        ('supplies', 'Supplies'),
        ('travel', 'Travel'),
        ('maintenance', 'Maintenance'),
        ('utilities', 'Utilities'),
        ('other', 'Other'),
    )
    
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('rejected', 'Rejected'),
    )
    
    budget_allocation = models.ForeignKey(BudgetAllocation, on_delete=models.CASCADE,
                                         related_name='expenditures')
    
    # Transaction details
    transaction_number = models.CharField(max_length=50, unique=True)
    expenditure_type = models.CharField(max_length=20, choices=EXPENDITURE_TYPE)
    description = models.TextField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Vendor/Payee
    payee_name = models.CharField(max_length=200)
    invoice_number = models.CharField(max_length=100, blank=True)
    invoice_date = models.DateField(null=True, blank=True)
    
    # Dates
    transaction_date = models.DateField()
    payment_date = models.DateField(null=True, blank=True)
    
    # Approval
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    requested_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True,
                                    related_name='expenditures_requested')
    approved_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='expenditures_approved')
    
    # Supporting documents
    supporting_document = models.FileField(upload_to='expenditures/', null=True, blank=True)
    payment_voucher = models.CharField(max_length=100, blank=True)
    
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.transaction_number:
            year = timezone.now().year
            last_exp = ExpenditureTracking.objects.filter(
                transaction_number__startswith=f'EXP-{year}-'
            ).aggregate(Max('id'))
            next_id = (last_exp['id__max'] or 0) + 1
            self.transaction_number = f'EXP-{year}-{next_id:05d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.transaction_number} - {self.description[:50]}"

    class Meta:
        db_table = 'expenditure_tracking'
        ordering = ['-transaction_date']


class RevenueSource(models.Model):
    """Track revenue sources for schools"""
    REVENUE_TYPE = (
        ('government_grant', 'Government Grant'),
        ('tuition_fees', 'Tuition Fees'),
        ('research_grants', 'Research Grants'),
        ('consultancy', 'Consultancy'),
        ('donations', 'Donations'),
        ('partnerships', 'Partnerships'),
        ('short_courses', 'Short Courses'),
        ('other', 'Other'),
    )
    
    school = models.ForeignKey('School', on_delete=models.CASCADE, related_name='revenues')
    academic_year = models.ForeignKey('AcademicYear', on_delete=models.CASCADE,
                                     related_name='revenues')
    
    revenue_type = models.CharField(max_length=20, choices=REVENUE_TYPE)
    source_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    received_date = models.DateField()
    receipt_number = models.CharField(max_length=100, blank=True)
    
    recorded_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True,
                                   related_name='revenues_recorded')
    supporting_document = models.FileField(upload_to='revenues/', null=True, blank=True)
    
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.school.code} - {self.revenue_type} - {self.amount}"

    class Meta:
        db_table = 'revenue_sources'
        ordering = ['-received_date']
        
        
# ============= PARTNERSHIPS & LINKAGES MODELS =============

class Partnership(models.Model):
    """University partnerships"""
    PARTNERSHIP_TYPE = (
        ('industry', 'Industry Partnership'),
        ('international', 'International Partnership'),
        ('research', 'Research Collaboration'),
        ('community', 'Community Partnership'),
        ('government', 'Government Agency'),
    )
    
    PARTNERSHIP_STATUS = (
        ('prospective', 'Prospective'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('terminated', 'Terminated'),
    )
    
    school = models.ForeignKey('School', on_delete=models.CASCADE, related_name='partnerships')
    partner_name = models.CharField(max_length=300)
    partnership_type = models.CharField(max_length=20, choices=PARTNERSHIP_TYPE)
    
    # Partner details
    country = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=200)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, blank=True)
    
    # Partnership details
    description = models.TextField()
    areas_of_collaboration = models.TextField()
    benefits = models.TextField(blank=True)
    
    # Management
    focal_person = models.ForeignKey('User', on_delete=models.SET_NULL, null=True,
                                    related_name='partnerships_managed')
    
    # Timeline
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=PARTNERSHIP_STATUS, default='active')
    
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='partnerships/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.partner_name} - {self.partnership_type}"

    class Meta:
        db_table = 'partnerships'
        ordering = ['partner_name']


class MOU(models.Model):
    """Memoranda of Understanding"""
    MOU_STATUS = (
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
        ('renewed', 'Renewed'),
    )
    
    partnership = models.ForeignKey(Partnership, on_delete=models.CASCADE, related_name='mous')
    
    title = models.CharField(max_length=500)
    mou_number = models.CharField(max_length=50, unique=True)
    
    # Dates
    signing_date = models.DateField()
    effective_date = models.DateField()
    expiry_date = models.DateField()
    
    # Terms
    scope = models.TextField()
    deliverables = models.TextField()
    responsibilities = models.TextField()
    
    status = models.CharField(max_length=20, choices=MOU_STATUS, default='active')
    
    # Signatories
    university_signatory = models.CharField(max_length=200)
    partner_signatory = models.CharField(max_length=200)
    
    # Documents
    mou_document = models.FileField(upload_to='mous/')
    
    # Renewal tracking
    renewal_notice_sent = models.BooleanField(default=False)
    renewal_date = models.DateField(null=True, blank=True)
    
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.mou_number} - {self.title[:50]}"

    class Meta:
        db_table = 'mous'
        ordering = ['-signing_date']
        verbose_name = 'MOU'
        verbose_name_plural = 'MOUs'


class CollaborativeProject(models.Model):
    """Projects under partnerships"""
    PROJECT_STATUS = (
        ('planning', 'Planning'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('suspended', 'Suspended'),
    )
    
    partnership = models.ForeignKey(Partnership, on_delete=models.CASCADE,
                                   related_name='projects')
    
    title = models.CharField(max_length=500)
    description = models.TextField()
    objectives = models.TextField()
    
    # Team
    project_leader = models.ForeignKey('Lecturer', on_delete=models.SET_NULL, null=True,
                                      related_name='collaborative_projects_led')
    team_members = models.ManyToManyField('Lecturer', related_name='collaborative_projects', blank=True)
    
    # Timeline
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Budget
    total_budget = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    university_contribution = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    partner_contribution = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Outputs
    publications = models.IntegerField(default=0)
    students_trained = models.IntegerField(default=0)
    
    status = models.CharField(max_length=20, choices=PROJECT_STATUS, default='planning')
    
    # Reports
    progress_report = models.TextField(blank=True)
    final_report = models.FileField(upload_to='collaborative_projects/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title[:100]

    class Meta:
        db_table = 'collaborative_projects'
        ordering = ['-start_date']


class AlumniRelation(models.Model):
    """Alumni engagement tracking"""
    ENGAGEMENT_TYPE = (
        ('mentorship', 'Mentorship Program'),
        ('guest_lecture', 'Guest Lecture'),
        ('sponsorship', 'Sponsorship'),
        ('recruitment', 'Student Recruitment'),
        ('donation', 'Donation'),
        ('project_collaboration', 'Project Collaboration'),
        ('internship', 'Internship Placement'),
        ('other', 'Other'),
    )
    
    programme = models.ForeignKey('Programme', on_delete=models.CASCADE,
                                 related_name='alumni_relations')
    
    # Alumni details
    alumni_name = models.CharField(max_length=200)
    graduation_year = models.IntegerField()
    current_organization = models.CharField(max_length=300, blank=True)
    current_position = models.CharField(max_length=200, blank=True)
    
    # Engagement
    engagement_type = models.CharField(max_length=30, choices=ENGAGEMENT_TYPE)
    engagement_date = models.DateField()
    description = models.TextField()
    
    # Impact
    students_impacted = models.IntegerField(default=0)
    contribution_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Contact
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    
    coordinated_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True,
                                      related_name='alumni_relations_coordinated')
    
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.alumni_name} - {self.engagement_type}"

    class Meta:
        db_table = 'alumni_relations'
        ordering = ['-engagement_date']
        
        
# ============= STRATEGIC PLANNING MODELS =============

class StrategicGoal(models.Model):
    """Strategic goals for schools"""
    GOAL_CATEGORY = (
        ('academic_excellence', 'Academic Excellence'),
        ('research_innovation', 'Research & Innovation'),
        ('student_experience', 'Student Experience'),
        ('infrastructure', 'Infrastructure Development'),
        ('partnerships', 'Partnerships & Linkages'),
        ('financial_sustainability', 'Financial Sustainability'),
        ('quality_assurance', 'Quality Assurance'),
    )
    
    GOAL_STATUS = (
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('achieved', 'Achieved'),
        ('delayed', 'Delayed'),
        ('cancelled', 'Cancelled'),
    )
    
    school = models.ForeignKey('School', on_delete=models.CASCADE, related_name='strategic_goals')
    
    category = models.CharField(max_length=30, choices=GOAL_CATEGORY)
    title = models.CharField(max_length=500)
    description = models.TextField()
    
    # Timeline
    start_year = models.ForeignKey('AcademicYear', on_delete=models.PROTECT,
                                  related_name='goals_starting')
    target_year = models.ForeignKey('AcademicYear', on_delete=models.PROTECT,
                                   related_name='goals_targeting')
    
    # Targets
    target_metric = models.CharField(max_length=200)
    baseline_value = models.DecimalField(max_digits=10, decimal_places=2)
    target_value = models.DecimalField(max_digits=10, decimal_places=2)
    current_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Progress
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    # Responsibility
    champion = models.ForeignKey('User', on_delete=models.SET_NULL, null=True,
                                related_name='strategic_goals_championed')
    
    status = models.CharField(max_length=20, choices=GOAL_STATUS, default='active')
    
    # Budget
    estimated_budget = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.school.code} - {self.title[:50]}"

    class Meta:
        db_table = 'strategic_goals'
        ordering = ['category', 'start_year']


class PerformanceIndicator(models.Model):
    """Key Performance Indicators for strategic goals"""
    INDICATOR_TYPE = (
        ('quantitative', 'Quantitative'),
        ('qualitative', 'Qualitative'),
    )
    
    strategic_goal = models.ForeignKey(StrategicGoal, on_delete=models.CASCADE,
                                      related_name='indicators')
    
    indicator_code = models.CharField(max_length=20)
    indicator_name = models.CharField(max_length=300)
    description = models.TextField()
    indicator_type = models.CharField(max_length=20, choices=INDICATOR_TYPE)
    
    # Measurement
    unit_of_measure = models.CharField(max_length=50)
    baseline_year = models.ForeignKey('AcademicYear', on_delete=models.PROTECT,
                                     related_name='indicators_baseline')
    baseline_value = models.DecimalField(max_digits=10, decimal_places=2)
    target_value = models.DecimalField(max_digits=10, decimal_places=2)
    current_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    achievement_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    # Data collection
    data_source = models.CharField(max_length=200)
    collection_frequency = models.CharField(max_length=100)
    responsible_person = models.ForeignKey('User', on_delete=models.SET_NULL, null=True,
                                          related_name='indicators_managed')
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Calculate achievement percentage
        if self.target_value > 0:
            self.achievement_percentage = (self.current_value / self.target_value) * 100
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.indicator_code} - {self.indicator_name}"

    class Meta:
        db_table = 'performance_indicators'
        ordering = ['indicator_code']


class AnnualPlan(models.Model):
    """Annual implementation plans"""
    PLAN_STATUS = (
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('rolled_over', 'Rolled Over'),
    )
    
    school = models.ForeignKey('School', on_delete=models.CASCADE, related_name='annual_plans')
    academic_year = models.ForeignKey('AcademicYear', on_delete=models.CASCADE,
                                     related_name='annual_plans')
    
    title = models.CharField(max_length=300)
    description = models.TextField()
    
    # Priorities
    key_priorities = models.TextField()
    
    # Budget
    total_budget = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    allocated_budget = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    status = models.CharField(max_length=20, choices=PLAN_STATUS, default='draft')
    
    # Approval
    prepared_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True,
                                   related_name='annual_plans_prepared')
    approved_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='annual_plans_approved')
    approval_date = models.DateField(null=True, blank=True)
    
    plan_document = models.FileField(upload_to='annual_plans/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.school.code} - {self.academic_year.name}"

    class Meta:
        db_table = 'annual_plans'
        unique_together = ('school', 'academic_year')
        ordering = ['-academic_year__start_date']


class AnnualPlanActivity(models.Model):
    """Activities under annual plans"""
    ACTIVITY_STATUS = (
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('delayed', 'Delayed'),
        ('cancelled', 'Cancelled'),
    )
    
    annual_plan = models.ForeignKey(AnnualPlan, on_delete=models.CASCADE,
                                   related_name='activities')
    strategic_goal = models.ForeignKey(StrategicGoal, on_delete=models.SET_NULL,
                                      null=True, blank=True, related_name='activities')
    
    activity_code = models.CharField(max_length=20)
    activity_name = models.CharField(max_length=300)
    description = models.TextField()
    
    # Timeline
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Resources
    budget_allocated = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    budget_utilized = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Responsibility
    responsible_person = models.ForeignKey('User', on_delete=models.SET_NULL, null=True,
                                          related_name='activities_responsible')
    
    # Progress
    status = models.CharField(max_length=20, choices=ACTIVITY_STATUS, default='not_started')
    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    # Deliverables
    expected_output = models.TextField()
    actual_output = models.TextField(blank=True)
    
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.activity_code} - {self.activity_name}"

    class Meta:
        db_table = 'annual_plan_activities'
        ordering = ['annual_plan', 'activity_code']
        verbose_name_plural = 'Annual Plan Activities'


class ProgressReport(models.Model):
    """Progress reports for plans and goals"""
    REPORT_TYPE = (
        ('quarterly', 'Quarterly Report'),
        ('semi_annual', 'Semi-Annual Report'),
        ('annual', 'Annual Report'),
        ('project', 'Project Report'),
    )
    
    REPORT_STATUS = (
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('reviewed', 'Reviewed'),
        ('published', 'Published'),
    )
    
    school = models.ForeignKey('School', on_delete=models.CASCADE, related_name='progress_reports')
    academic_year = models.ForeignKey('AcademicYear', on_delete=models.CASCADE,
                                     related_name='progress_reports')
    annual_plan = models.ForeignKey(AnnualPlan, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='progress_reports')
    
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE)
    title = models.CharField(max_length=300)
    
    # Reporting period
    reporting_period_start = models.DateField()
    reporting_period_end = models.DateField()
    
    # Content
    executive_summary = models.TextField()
    achievements = models.TextField()
    challenges = models.TextField()
    recommendations = models.TextField()
    
    # Metrics
    overall_progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    budget_utilization_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    status = models.CharField(max_length=20, choices=REPORT_STATUS, default='draft')
    
    # Workflow
    prepared_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True,
                                   related_name='reports_prepared')
    reviewed_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='reports_reviewed')
    published_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='reports_published')
    published_date = models.DateTimeField(null=True, blank=True)
    
    report_document = models.FileField(upload_to='progress_reports/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.reporting_period_end}"

    class Meta:
        db_table = 'progress_reports'
        ordering = ['-reporting_period_end']


class DeanApproval(models.Model):
    """Track items requiring dean approval"""
    APPROVAL_TYPE = (
        ('budget', 'Budget Approval'),
        ('recruitment', 'Staff Recruitment'),
        ('procurement', 'Procurement'),
        ('research_grant', 'Research Grant'),
        ('partnership', 'Partnership Agreement'),
        ('programme_change', 'Programme Change'),
        ('other', 'Other'),
    )
    
    PRIORITY = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    APPROVAL_STATUS = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejecte'),
        ('deferred', 'Deferred'),
        )
    department = models.ForeignKey('Department', on_delete=models.CASCADE,
                              related_name='dean_approvals')
    approval_type = models.CharField(max_length=20, choices=APPROVAL_TYPE)

    title = models.CharField(max_length=300)
    description = models.TextField()

    priority = models.CharField(max_length=10, choices=PRIORITY, default='medium')

    # Request details
    requested_by = models.ForeignKey('User', on_delete=models.CASCADE,
                                    related_name='approval_requests')
    request_date = models.DateTimeField(auto_now_add=True)

    # Supporting documents
    supporting_document = models.FileField(upload_to='dean_approvals/', null=True, blank=True)

    # Approval
    status = models.CharField(max_length=20, choices=APPROVAL_STATUS, default='pending')
    approved_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='dean_approvals_made')
    decision_date = models.DateTimeField(null=True, blank=True)
    decision_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.approval_type} - {self.title[:50]}"

    class Meta:
        db_table = 'dean_approvals'
        ordering = ['-request_date']

# Add these models to your models.py

class AdvisingNote(models.Model):
    """Academic advising notes for students"""
    NOTE_TYPES = (
        ('academic', 'Academic Concern'),
        ('attendance', 'Attendance Issue'),
        ('performance', 'Performance Discussion'),
        ('personal', 'Personal Issue'),
        ('career', 'Career Guidance'),
        ('general', 'General Note'),
    )
    
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='advising_notes')
    lecturer = models.ForeignKey('User', on_delete=models.CASCADE, related_name='advising_notes_created')
    note_type = models.CharField(max_length=20, choices=NOTE_TYPES, default='general')
    subject = models.CharField(max_length=200)
    note = models.TextField()
    action_required = models.BooleanField(default=False)
    action_taken = models.TextField(blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    is_confidential = models.BooleanField(default=False)
    is_resolved = models.BooleanField(default=False)
    resolved_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.registration_number} - {self.subject}"

    class Meta:
        db_table = 'advising_notes'
        ordering = ['-created_at']


class StudentSpecialNeed(models.Model):
    """Track students with special needs"""
    NEED_TYPES = (
        ('physical', 'Physical Disability'),
        ('visual', 'Visual Impairment'),
        ('hearing', 'Hearing Impairment'),
        ('learning', 'Learning Disability'),
        ('medical', 'Medical Condition'),
        ('mental', 'Mental Health'),
        ('other', 'Other'),
    )
    
    SEVERITY_LEVELS = (
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
    )
    
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='special_needs')
    need_type = models.CharField(max_length=20, choices=NEED_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='moderate')
    description = models.TextField()
    accommodations_required = models.TextField(help_text="Special accommodations needed")
    support_provided = models.TextField(blank=True)
    
    # Documentation
    medical_certificate = models.FileField(upload_to='special_needs/', null=True, blank=True)
    
    # Tracking
    reported_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, 
                                   related_name='special_needs_reported')
    reported_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    # Review
    last_reviewed = models.DateField(null=True, blank=True)
    next_review_date = models.DateField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.registration_number} - {self.get_need_type_display()}"

    class Meta:
        db_table = 'student_special_needs'
        ordering = ['-created_at']