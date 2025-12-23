# ============= SIGNALS.PY (Optional but recommended) =============
# Create signals.py to handle automatic updates

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ResitExam, SemesterReport, Student

@receiver(post_save, sender=ResitExam)
def update_resit_completion(sender, instance, **kwargs):
    """Automatically update original result when resit is completed"""
    if instance.status == 'completed' and instance.resit_marks is not None:
        instance.calculate_resit_grade()


@receiver(post_save, sender=SemesterReport)
def update_student_progression(sender, instance, created, **kwargs):
    """Update student's current year and semester when report is approved"""
    if instance.status == 'approved' and not created:
        student = instance.student
        student.current_year = instance.to_year_of_study
        student.current_semester = instance.to_semester_number
        student.save(update_fields=['current_year', 'current_semester'])

