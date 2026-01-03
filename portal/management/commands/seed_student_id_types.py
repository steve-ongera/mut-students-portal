from django.core.management.base import BaseCommand
from decimal import Decimal

from portal.models import StudentIDType


class Command(BaseCommand):
    help = "Seed Student ID Types"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🚀 Seeding Student ID Types..."))

        id_types_data = [
            {
                "name": "Physical Student ID",
                "code": "PHY-ID",
                "id_type": "physical",
                "description": "Standard physical student ID card",
                "base_price": Decimal("1000.00"),
                "validity_period_months": 24,
                "processing_days": 7,
                "rush_processing_days": 3,
            },
            {
                "name": "Digital Student ID",
                "code": "DIG-ID",
                "id_type": "digital",
                "description": "Digital-only student ID",
                "base_price": Decimal("500.00"),
                "validity_period_months": 24,
                "processing_days": 3,
                "rush_processing_days": 1,
            },
            {
                "name": "Physical & Digital ID",
                "code": "BOTH-ID",
                "id_type": "both",
                "description": "Combined physical and digital student ID",
                "base_price": Decimal("1500.00"),
                "validity_period_months": 24,
                "processing_days": 7,
                "rush_processing_days": 3,
            },
        ]

        created = 0
        skipped = 0

        for data in id_types_data:
            obj, is_created = StudentIDType.objects.get_or_create(
                code=data["code"],
                defaults={**data, "is_active": True},
            )

            if is_created:
                created += 1
            else:
                skipped += 1

        self.stdout.write(self.style.SUCCESS("✅ Student ID Types seeding complete"))
        self.stdout.write(
            self.style.SUCCESS(f"✔ Created: {created} | ⏭ Skipped: {skipped}")
        )
