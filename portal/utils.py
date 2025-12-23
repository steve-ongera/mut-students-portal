
# ============= UTILS.PY =============
# Create utils.py for helper functions

from django.db.models import Count, Sum, Q
from decimal import Decimal
from portal.models import (
    SemesterResults, ResitExam, UnitEnrollment,
    SemesterReport, Student
)


def get_student_failed_units_count(student, semester=None):
    """Get count of failed units for a student"""
    query = SemesterResults.objects.filter(
        student=student,
        is_passed=False
    )
    
    if semester:
        query = query.filter(semester=semester)
    
    return query.count()


def get_student_eligibility_for_reporting(student):
    """
    Check if student is eligible to report for next semester
    Returns: tuple (is_eligible, failed_count, message)
    """
    # Get failed units from current/previous semester
    failed_count = get_student_failed_units_count(student)
    
    if failed_count > 2:
        return (
            False,
            failed_count,
            f"You have {failed_count} failed units. Maximum allowed is 2. "
            f"You must clear {failed_count - 2} unit(s) through resit exams."
        )
    
    return (True, failed_count, "Eligible to report for next semester")


def calculate_next_semester_details(student):
    """
    Calculate what the next year and semester should be for a student
    Returns: dict with next_year, next_semester_number
    """
    current_year = student.current_year
    current_sem = int(student.current_semester)
    programme_total_sems = student.programme.total_semesters
    sems_per_year = 2  # Default to 2, adjust if programme uses 3
    
    # Check if programme uses tri-semester system
    if programme_total_sems % 3 == 0:
        sems_per_year = 3
    
    # Calculate next semester
    if current_sem < sems_per_year:
        next_semester_number = str(current_sem + 1)
        next_year = current_year
    else:
        next_semester_number = '1'
        next_year = current_year + 1
    
    return {
        'next_year': next_year,
        'next_semester_number': next_semester_number,
        'is_final_year': next_year > student.programme.duration_years,
    }


def get_units_available_for_enrollment(student, semester):
    """
    Get units available for enrollment for a student in a given semester
    """
    from portal.models import ProgrammeUnit, UnitAllocation
    
    # Get units for student's programme, year, and semester
    available_units = ProgrammeUnit.objects.filter(
        programme=student.programme,
        academic_year=semester.academic_year,
        year_of_study=student.current_year,
        semester_number=student.current_semester,
        is_active=True
    ).filter(
        # Must have lecturer allocated
        allocations__semester=semester,
        allocations__status='approved_dean'
    ).distinct()
    
    return available_units


def get_failed_units_for_resit(student, semester):
    """
    Get failed units that are offered in the given semester
    (eligible for resit registration)
    """
    from portal.models import UnitAllocation
    
    # Get all failed units
    failed_results = SemesterResults.objects.filter(
        student=student,
        is_passed=False
    ).select_related('programme_unit', 'programme_unit__unit')
    
    # Filter those offered this semester
    eligible_for_resit = []
    for result in failed_results:
        # Check if unit is offered this semester
        is_offered = UnitAllocation.objects.filter(
            programme_unit=result.programme_unit,
            semester=semester,
            status='approved_dean'
        ).exists()
        
        # Check if not already registered for resit
        already_registered = ResitExam.objects.filter(
            student=student,
            original_result=result,
            resit_semester=semester
        ).exists()
        
        if is_offered and not already_registered:
            eligible_for_resit.append(result)
    
    return eligible_for_resit


def create_semester_report(student, to_semester):
    """
    Create a semester report for a student
    Returns: (report, created, error_message)
    """
    from django.core.exceptions import ValidationError
    
    try:
        # Check if already reported
        existing = SemesterReport.objects.filter(
            student=student,
            to_semester=to_semester,
            status__in=['pending', 'approved']
        ).first()
        
        if existing:
            return (existing, False, "Already reported for this semester")
        
        # Get eligibility
        is_eligible, failed_count, message = get_student_eligibility_for_reporting(student)
        
        if not is_eligible:
            return (None, False, message)
        
        # Get next semester details
        next_details = calculate_next_semester_details(student)
        
        # Get fee balance
        from portal.models import FeeBalance
        fee_balance = FeeBalance.objects.filter(
            student=student,
            semester=to_semester
        ).first()
        
        # Get previous GPA
        from portal.models import SemesterGPA
        previous_gpa = SemesterGPA.objects.filter(
            student=student
        ).order_by('-semester__start_date').first()
        
        # Create report
        report = SemesterReport.objects.create(
            student=student,
            from_academic_year=to_semester.academic_year if student.current_year else None,
            to_academic_year=to_semester.academic_year,
            from_semester=None,  # Can be enhanced
            to_semester=to_semester,
            from_year_of_study=student.current_year if student.current_year else None,
            to_year_of_study=next_details['next_year'],
            from_semester_number=student.current_semester if student.current_semester else None,
            to_semester_number=next_details['next_semester_number'],
            failed_units_count=failed_count,
            fee_balance=fee_balance.balance if fee_balance else Decimal('0.00'),
            is_financially_cleared=fee_balance.is_cleared if fee_balance else True,
            previous_semester_gpa=previous_gpa.semester_gpa if previous_gpa else None,
            cumulative_gpa=student.cumulative_gpa,
            total_credits_earned=student.total_credit_hours,
        )
        
        return (report, True, None)
        
    except ValidationError as e:
        return (None, False, str(e))
    except Exception as e:
        return (None, False, f"Error creating report: {str(e)}")


def enroll_student_in_unit(student, programme_unit, semester, semester_report, enrollment_type='normal', resit_exam=None):
    """
    Enroll a student in a unit
    Returns: (enrollment, created, error_message)
    """
    from django.core.exceptions import ValidationError
    
    try:
        # Check if already enrolled
        existing = UnitEnrollment.objects.filter(
            student=student,
            programme_unit=programme_unit,
            semester=semester,
            status__in=['pending', 'approved']
        ).first()
        
        if existing:
            return (existing, False, "Already enrolled in this unit")
        
        # Create enrollment
        enrollment = UnitEnrollment.objects.create(
            student=student,
            semester_report=semester_report,
            programme_unit=programme_unit,
            semester=semester,
            enrollment_type=enrollment_type,
            resit_exam=resit_exam
        )
        
        return (enrollment, True, None)
        
    except ValidationError as e:
        return (None, False, str(e))
    except Exception as e:
        return (None, False, f"Error enrolling: {str(e)}")


def register_for_resit(student, semester_result, resit_semester, resit_fee=Decimal('2000.00')):
    """
    Register a student for a resit exam
    Returns: (resit_exam, created, error_message)
    """
    from django.core.exceptions import ValidationError
    
    try:
        # Check if already registered
        existing = ResitExam.objects.filter(
            student=student,
            original_result=semester_result,
            resit_semester=resit_semester
        ).first()
        
        if existing:
            return (existing, False, "Already registered for resit")
        
        # Create resit exam
        resit = ResitExam.objects.create(
            student=student,
            original_result=semester_result,
            resit_semester=resit_semester,
            original_semester=semester_result.semester,
            original_marks=semester_result.total_marks,
            original_grade=semester_result.grade,
            original_grade_point=semester_result.grade_point,
            resit_fee_amount=resit_fee
        )
        
        return (resit, True, None)
        
    except ValidationError as e:
        return (None, False, str(e))
    except Exception as e:
        return (None, False, f"Error registering for resit: {str(e)}")


def get_student_enrollment_summary(student, semester):
    """
    Get summary of student's enrollments for a semester
    Returns: dict with enrollment statistics
    """
    enrollments = UnitEnrollment.objects.filter(
        student=student,
        semester=semester
    )
    
    return {
        'total': enrollments.count(),
        'approved': enrollments.filter(status='approved').count(),
        'pending': enrollments.filter(status='pending').count(),
        'rejected': enrollments.filter(status='rejected').count(),
        'normal': enrollments.filter(enrollment_type='normal').count(),
        'resit': enrollments.filter(enrollment_type='resit').count(),
        'retake': enrollments.filter(enrollment_type='retake').count(),
    }


def get_student_progression_history(student):
    """
    Get student's progression history (all semester reports)
    """
    return SemesterReport.objects.filter(
        student=student
    ).order_by('-report_date').select_related(
        'from_academic_year',
        'to_academic_year',
        'from_semester',
        'to_semester',
        'approved_by'
    )


def check_enrollment_period_active(semester):
    """
    Check if enrollment period is active for a semester
    Returns: (is_active, is_resit_active, enrollment_period)
    """
    from portal.models import EnrollmentPeriod
    
    try:
        period = EnrollmentPeriod.objects.get(semester=semester)
        return (
            period.is_enrollment_open(),
            period.is_resit_enrollment_open(),
            period
        )
    except EnrollmentPeriod.DoesNotExist:
        return (False, False, None)

