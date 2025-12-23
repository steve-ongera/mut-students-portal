
# ============= MANAGEMENT COMMAND =============
# Create management/commands/auto_create_enrollment_periods.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from portal.models import Semester, EnrollmentPeriod


class Command(BaseCommand):
    help = 'Automatically create enrollment periods for semesters'

    def handle(self, *args, **kwargs):
        semesters = Semester.objects.filter(is_active=True)
        
        for semester in semesters:
            # Check if enrollment period already exists
            if EnrollmentPeriod.objects.filter(semester=semester).exists():
                self.stdout.write(
                    self.style.WARNING(f'Enrollment period already exists for {semester}')
                )
                continue
            
            # Create enrollment period
            # Normal enrollment: 2 weeks before semester starts
            normal_start = semester.start_date - timedelta(days=14)
            normal_end = semester.start_date + timedelta(days=7)
            
            # Resit enrollment: 1 week after semester starts
            resit_start = semester.start_date + timedelta(days=7)
            resit_end = semester.start_date + timedelta(days=21)
            
            enrollment_period = EnrollmentPeriod.objects.create(
                semester=semester,
                start_date=normal_start,
                end_date=normal_end,
                resit_start_date=resit_start,
                resit_end_date=resit_end,
                is_active=True
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Created enrollment period for {semester}')
            )
        
        self.stdout.write(self.style.SUCCESS('Done!'))
