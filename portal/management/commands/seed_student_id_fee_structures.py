from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from datetime import date

from portal.models import (
    AcademicYear,
    StudentIDType,
    StudentIDFeeStructure
)


class Command(BaseCommand):
    help = "Seed Student ID Fee Structures for all academic years and ID types"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🚀 Seeding Student ID Fee Structures..."))

        academic_years = AcademicYear.objects.all()
        id_types = StudentIDType.objects.filter(is_active=True)

        if not academic_years.exists():
            self.stdout.write(self.style.ERROR("❌ No Academic Years found."))
            return

        if not id_types.exists():
            self.stdout.write(self.style.ERROR("❌ No active Student ID Types found."))
            return

        created_count = 0
        skipped_count = 0

        for academic_year in academic_years:
            for id_type in id_types:
                exists = StudentIDFeeStructure.objects.filter(
                    academic_year=academic_year,
                    id_type=id_type
                ).exists()

                if exists:
                    skipped_count += 1
                    continue

                # ----------------------------
                # Fee logic (editable anytime)
                # ----------------------------
                base_fee = Decimal("1000.00")

                if id_type.id_type == "digital":
                    base_fee = Decimal("500.00")
                elif id_type.id_type == "both":
                    base_fee = Decimal("1500.00")

                StudentIDFeeStructure.objects.create(
                    id_type=id_type,
                    academic_year=academic_year,
                    base_fee=base_fee,
                    rush_processing_fee=Decimal("300.00"),
                    replacement_fee=Decimal("700.00"),
                    digital_only_fee=Decimal("400.00") if id_type.id_type != "physical" else None,
                    is_active=True,
                    effective_from=academic_year.start_date
                    if hasattr(academic_year, "start_date")
                    else date(academic_year.year, 1, 1),
                    effective_to=academic_year.end_date
                    if hasattr(academic_year, "end_date")
                    else None,
                )

                created_count += 1

        self.stdout.write(self.style.SUCCESS("✅ Fee structure seeding complete"))
        self.stdout.write(
            self.style.SUCCESS(
                f"✔ Created: {created_count} | ⏭ Skipped: {skipped_count}"
            )
        )
