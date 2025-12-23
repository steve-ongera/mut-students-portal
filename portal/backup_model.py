# Add these models to your existing models.py

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
        
        # Check if unit is offered in this semester
        if not UnitAllocation.objects.filter(
            programme_unit=self.programme_unit,
            semester=self.semester,
            status='approved_dean'
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

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        
        # Create UnitRegistration if approved
        if self.status == 'approved':
            UnitRegistration.objects.get_or_create(
                student=self.student,
                programme_unit=self.programme_unit,
                semester=self.semester,
                defaults={
                    'status': 'registered',
                    'is_retake': self.enrollment_type in ['resit', 'retake'],
                    'approved_by': self.approved_by,
                }
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