
# ============= CONTEXT PROCESSORS =============
# Create context_processors.py to add data to all templates

def semester_reporting_context(request):
    """
    Add semester reporting context to all templates
    """
    if request.user.is_authenticated and hasattr(request.user, 'student_profile'):
        from portal.models import Semester, SemesterReport
        from .utils import get_student_eligibility_for_reporting
        
        student = request.user.student_profile
        current_semester = Semester.objects.filter(is_current=True).first()
        
        # Check if reported for current semester
        has_reported = SemesterReport.objects.filter(
            student=student,
            to_semester=current_semester,
            status__in=['pending', 'approved']
        ).exists() if current_semester else False
        
        # Check eligibility
        is_eligible, failed_count, message = get_student_eligibility_for_reporting(student)
        
        return {
            'current_semester': current_semester,
            'has_reported_current_semester': has_reported,
            'is_eligible_to_report': is_eligible,
            'failed_units_count': failed_count,
        }
    
    return {}


# Add to settings.py:
"""
TEMPLATES = [
    {
        'OPTIONS': {
            'context_processors': [
                # ... existing processors ...
                'your_app.context_processors.semester_reporting_context',
            ],
        },
    },
]
"""