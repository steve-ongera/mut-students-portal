from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Max
from decimal import Decimal

from portal.models import (
    Student,
    AcademicYear,
    StudentIDType,
    StudentIDFeeStructure,
    StudentIDApplication
)


class Command(BaseCommand):
    help = "Seed Student ID applications for existing students and academic years"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🚀 Seeding Student ID applications..."))

        # =========================
        # Fetch required base data
        # =========================
        students = Student.objects.all()
        academic_years = AcademicYear.objects.all()
        id_type = StudentIDType.objects.filter(is_active=True).first()

        if not students.exists():
            self.stdout.write(self.style.ERROR("❌ No students found."))
            return

        if not academic_years.exists():
            self.stdout.write(self.style.ERROR("❌ No academic years found."))
            return

        if not id_type:
            self.stdout.write(self.style.ERROR("❌ No active Student ID Type found."))
            return

        created_count = 0
        skipped_count = 0

        # =========================
        # Loop academic years & students
        # =========================
        for academic_year in academic_years:
            fee_structure = StudentIDFeeStructure.objects.filter(
                academic_year=academic_year,
                id_type=id_type,
                is_active=True
            ).first()

            if not fee_structure:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠ Skipping {academic_year.name} (no fee structure)"
                    )
                )
                continue

            for student in students:
                # Prevent duplicates
                exists = StudentIDApplication.objects.filter(
                    student=student,
                    fee_structure=fee_structure
                ).exists()

                if exists:
                    skipped_count += 1
                    continue

                # Generate application number safely
                year = timezone.now().year
                last_id = StudentIDApplication.objects.filter(
                    application_number__startswith=f"ID-{year}-"
                ).aggregate(max_id=Max("id"))["max_id"] or 0

                application_number = f"ID-{year}-{last_id + 1:04d}"

                # Create application
                StudentIDApplication.objects.create(
                    application_number=application_number,
                    student=student,
                    id_type=id_type,
                    fee_structure=fee_structure,
                    application_reason="new_student",
                    status="submitted",
                    amount_due=fee_structure.base_fee,
                    amount_paid=Decimal("0.00"),
                )

                created_count += 1

        # =========================
        # Summary
        # =========================
        self.stdout.write(self.style.SUCCESS("✅ Seeding completed"))
        self.stdout.write(
            self.style.SUCCESS(
                f"✔ Created: {created_count} | ⏭ Skipped: {skipped_count}"
            )
        )
