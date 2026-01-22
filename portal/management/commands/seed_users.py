from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from portal.models import School, Department
from django.utils.text import slugify
import random

User = get_user_model()


class Command(BaseCommand):
    help = "Seed system users (non-students, non-admins) with Kenyan usernames"

    DEFAULT_PASSWORD = "password123"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("🚀 Seeding users started..."))

        self.create_school_deans()
        self.create_department_hods()
        self.create_other_staff()

        self.stdout.write(self.style.SUCCESS("✅ User seeding completed successfully"))

    # -------------------------------------------------
    # Utility
    # -------------------------------------------------
    def create_user(self, username, role):
        if User.objects.filter(username=username).exists():
            return User.objects.get(username=username)

        user = User.objects.create_user(
            username=username,
            password=self.DEFAULT_PASSWORD,
            role=role,
            is_active=True
        )
        return user

    # -------------------------------------------------
    # 1. One Dean per School
    # -------------------------------------------------
    def create_school_deans(self):
        self.stdout.write("🎓 Creating Deans...")

        for school in School.objects.all():
            if school.dean:
                continue

            username = f"dean_{slugify(school.code)}"
            dean = self.create_user(username=username, role="dean")

            school.dean = dean
            school.save()

            self.stdout.write(f"  ✔ Dean created for {school.name}: {username}")

    # -------------------------------------------------
    # 2. One HOD (COD) per Department
    # -------------------------------------------------
    def create_department_hods(self):
        self.stdout.write("🏫 Creating Heads of Department (CODs)...")

        for dept in Department.objects.select_related("school"):
            if dept.hod:
                continue

            username = f"hod_{slugify(dept.code)}"
            hod = self.create_user(username=username, role="hod")

            dept.hod = hod
            dept.save()

            self.stdout.write(
                f"  ✔ HOD created for {dept.name} ({dept.school.code}): {username}"
            )

    # -------------------------------------------------
    # 3. Other University Staff
    # -------------------------------------------------
    def create_other_staff(self):
        self.stdout.write("🏢 Creating other system staff...")

        roles = [
            "finance",
            "procurement",
            "store",
            "librarian",
            "ict_admin",
            "hostel_warden",
            "registrar",
            "vc",
            "hos",
            "lecturer",
        ]

        for role in roles:
            username = f"{role}_kenya"
            user = self.create_user(username=username, role=role)

            self.stdout.write(f"  ✔ {role.upper()} created: {username}")
