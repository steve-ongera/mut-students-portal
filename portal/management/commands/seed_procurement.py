"""
Management command to seed procurement data.

Usage:
    python manage.py seed_procurement
    python manage.py seed_procurement --clear        # clears existing data first
    python manage.py seed_procurement --count 20     # custom number of requisitions

Place this file at:
    <your_app>/management/commands/seed_procurement.py

Make sure the management/commands/ directories both contain __init__.py files.
"""

import random
from decimal import Decimal
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction

# ── import every model that touches procurement ────────────────────────────
from portal.models import (   # adjust the app label to match yours
    # look-ups / dependencies
    AcademicYear,
    Department,
    # procurement-specific
    Supplier,
    ProcurementCategory,
    PurchaseRequisition,
    RequisitionItem,
)

User = get_user_model()


# ──────────────────────────────────────────────────────────────────────────────
#  Static seed data
# ──────────────────────────────────────────────────────────────────────────────

SUPPLIER_DATA = [
    {
        "name": "TechSupply Kenya Ltd",
        "supplier_code": "SUP-001",
        "contact_person": "Alice Mwangi",
        "email": "alice@techsupply.co.ke",
        "phone_number": "0722100001",
        "alternative_phone": "0733100001",
        "address": "Westlands Business Park, Nairobi",
        "tax_pin": "A001234567B",
        "bank_name": "Equity Bank",
        "bank_account": "0100123456789",
        "rating": Decimal("4.50"),
    },
    {
        "name": "Office Essentials EA",
        "supplier_code": "SUP-002",
        "contact_person": "Brian Otieno",
        "email": "brian@officeessentials.co.ke",
        "phone_number": "0722100002",
        "alternative_phone": "",
        "address": "Industrial Area, Nairobi",
        "tax_pin": "A002234567B",
        "bank_name": "KCB Bank",
        "bank_account": "1210123456",
        "rating": Decimal("3.80"),
    },
    {
        "name": "Greenfield Supplies",
        "supplier_code": "SUP-003",
        "contact_person": "Carol Njeri",
        "email": "carol@greenfield.co.ke",
        "phone_number": "0722100003",
        "alternative_phone": "0711100003",
        "address": "Mombasa Road, Nairobi",
        "tax_pin": "A003234567B",
        "bank_name": "Co-operative Bank",
        "bank_account": "0110102345678",
        "rating": Decimal("4.20"),
    },
    {
        "name": "BuildRight Hardware",
        "supplier_code": "SUP-004",
        "contact_person": "David Kamau",
        "email": "david@buildright.co.ke",
        "phone_number": "0722100004",
        "alternative_phone": "",
        "address": "Thika Road Mall, Nairobi",
        "tax_pin": "A004234567B",
        "bank_name": "Equity Bank",
        "bank_account": "0100234567890",
        "rating": Decimal("3.50"),
    },
    {
        "name": "MediCare Supplies Ltd",
        "supplier_code": "SUP-005",
        "contact_person": "Esther Wambui",
        "email": "esther@medicare.co.ke",
        "phone_number": "0722100005",
        "alternative_phone": "0733100005",
        "address": "Upper Hill, Nairobi",
        "tax_pin": "A005234567B",
        "bank_name": "Standard Chartered",
        "bank_account": "01234567890",
        "rating": Decimal("4.70"),
    },
    {
        "name": "SafariCom Business Solutions",
        "supplier_code": "SUP-006",
        "contact_person": "Francis Odhiambo",
        "email": "francis@safaribiz.co.ke",
        "phone_number": "0722100006",
        "alternative_phone": "",
        "address": "Waiyaki Way, Nairobi",
        "tax_pin": "A006234567B",
        "bank_name": "NCBA Bank",
        "bank_account": "1000123456",
        "rating": Decimal("4.00"),
    },
    {
        "name": "EduTech Resources",
        "supplier_code": "SUP-007",
        "contact_person": "Grace Achieng",
        "email": "grace@edutech.co.ke",
        "phone_number": "0722100007",
        "alternative_phone": "0700100007",
        "address": "Upperhill, Nairobi",
        "tax_pin": "A007234567B",
        "bank_name": "Absa Bank Kenya",
        "bank_account": "2040123456",
        "rating": Decimal("3.90"),
    },
    {
        "name": "CleanSpace Facilities",
        "supplier_code": "SUP-008",
        "contact_person": "Henry Muthama",
        "email": "henry@cleanspace.co.ke",
        "phone_number": "0722100008",
        "alternative_phone": "",
        "address": "South B, Nairobi",
        "tax_pin": "A008234567B",
        "bank_name": "Family Bank",
        "bank_account": "010012345678",
        "rating": Decimal("2.80"),
    },
    {
        "name": "PrintPro Kenya",
        "supplier_code": "SUP-009",
        "contact_person": "Irene Korir",
        "email": "irene@printpro.co.ke",
        "phone_number": "0722100009",
        "alternative_phone": "0733200009",
        "address": "Ngong Road, Nairobi",
        "tax_pin": "A009234567B",
        "bank_name": "Diamond Trust Bank",
        "bank_account": "0050123456",
        "rating": Decimal("4.10"),
    },
    {
        "name": "PowerTech Systems",
        "supplier_code": "SUP-010",
        "contact_person": "James Karanja",
        "email": "james@powertech.co.ke",
        "phone_number": "0722100010",
        "alternative_phone": "",
        "address": "Karen, Nairobi",
        "tax_pin": "A010234567B",
        "bank_name": "I&M Bank",
        "bank_account": "010012345",
        "rating": Decimal("4.60"),
    },
]

CATEGORY_DATA = [
    # (name, code, description, parent_code_or_None)
    ("Information Technology",        "IT",     "Computers, peripherals, and IT equipment",       None),
    ("Office Supplies & Stationery",  "OFF",    "Pens, paper, folders, and general stationery",   None),
    ("Furniture & Fittings",          "FURN",   "Desks, chairs, shelving, and fittings",          None),
    ("Laboratory Equipment",          "LAB",    "Scientific and lab-grade instruments",           None),
    ("Cleaning & Sanitation",         "CLEAN",  "Cleaning materials and sanitary products",       None),
    ("Maintenance & Repairs",         "MAINT",  "Spare parts and repair services",                None),
    ("Printing & Publications",       "PRINT",  "Printers, cartridges, and printed materials",    None),
    ("Medical & Healthcare",          "MED",    "First-aid kits, medicines, and medical gear",    None),
    ("Transport & Logistics",         "TRANS",  "Vehicle maintenance and logistics costs",        None),
    ("Electrical & Electronics",      "ELEC",   "Electrical fittings and electronic components", None),
    # Sub-categories
    ("Laptops & Desktops",            "IT-PC",  "Personal computers and laptops",                 "IT"),
    ("Networking Equipment",          "IT-NET", "Routers, switches, and cables",                  "IT"),
    ("Printers & Scanners",           "IT-PR",  "Printing and scanning devices",                  "IT"),
    ("Toner & Cartridges",            "PR-INK", "Ink cartridges and toner refills",               "PRINT"),
    ("Stationery - Paper",            "OFF-PA", "A4, A3 and other paper stock",                   "OFF"),
]

ITEM_DESCRIPTIONS = [
    ("Laptop Computer (Core i7, 16GB RAM, 512GB SSD)", "IT-PC",  Decimal("85000"),  "Pieces"),
    ("Desktop Computer (Core i5, 8GB RAM, 1TB HDD)",   "IT-PC",  Decimal("55000"),  "Pieces"),
    ("HP LaserJet Printer (Monochrome)",                "IT-PR",  Decimal("22000"),  "Pieces"),
    ("Network Switch 24-Port Managed",                  "IT-NET", Decimal("18500"),  "Pieces"),
    ("CAT6 Ethernet Cable (305m box)",                  "IT-NET", Decimal("6500"),   "Boxes"),
    ("Toner Cartridge HP 85A",                          "PR-INK", Decimal("3200"),   "Pieces"),
    ("A4 Printing Paper 80gsm (500 sheets)",            "OFF-PA", Decimal("650"),    "Reams"),
    ("Ballpoint Pens (Box of 50)",                      "OFF",    Decimal("420"),    "Boxes"),
    ("Office Chair (Ergonomic)",                        "FURN",   Decimal("12000"),  "Pieces"),
    ("Steel Filing Cabinet (4-drawer)",                 "FURN",   Decimal("18000"),  "Pieces"),
    ("Laboratory Microscope (Binocular)",               "LAB",    Decimal("45000"),  "Pieces"),
    ("Digital Weighing Balance (0.1g)",                 "LAB",    Decimal("28000"),  "Pieces"),
    ("Disinfectant Solution 5L",                        "CLEAN",  Decimal("1800"),   "Litres"),
    ("Cleaning Mop & Bucket Set",                       "CLEAN",  Decimal("1200"),   "Sets"),
    ("Electrical Extension Board (10-outlet)",          "ELEC",   Decimal("2500"),   "Pieces"),
    ("UPS 1KVA (Uninterruptible Power Supply)",         "ELEC",   Decimal("14000"),  "Pieces"),
    ("First Aid Kit (Standard)",                        "MED",    Decimal("3500"),   "Kits"),
    ("Paracetamol Tablets 500mg (100s)",                "MED",    Decimal("280"),    "Packets"),
    ("Vehicle Service (Oil Change & Filter)",           "TRANS",  Decimal("8500"),   "Services"),
    ("Tyre Replacement (195/65 R15)",                   "TRANS",  Decimal("9500"),   "Pieces"),
    ("Whiteboard Markers (Box of 10)",                  "OFF",    Decimal("480"),    "Boxes"),
    ("Staple Pins Box (5000 staples)",                  "OFF",    Decimal("150"),    "Boxes"),
    ("Projector (HDMI, 3500 lumens)",                   "IT",     Decimal("65000"),  "Pieces"),
    ("HDMI Cable 5m",                                   "IT",     Decimal("850"),    "Pieces"),
    ("Whiteboard (120x90cm)",                           "FURN",   Decimal("9500"),   "Pieces"),
]

REQUISITION_PURPOSES = [
    "Procurement of IT equipment for new computer lab",
    "Replenishment of office supplies for administration block",
    "Purchase of furniture for new staff offices",
    "Laboratory equipment for Chemistry department upgrade",
    "Cleaning and sanitation supplies for semester start",
    "Maintenance spares for electrical installations",
    "Printing materials for semester examination",
    "Medical supplies for student health centre",
    "Vehicle maintenance and spare parts",
    "Networking equipment for campus Wi-Fi expansion",
    "Stationery for academic registry office",
    "Audio-visual equipment for lecture halls",
    "Ergonomic furniture for library reading area",
    "Safety equipment for engineering workshops",
    "Annual procurement of consumables for biology labs",
]

REQUISITION_STATUSES = [
    "draft",
    "pending_hod",
    "approved_hod",
    "pending_hos",
    "approved_hos",
    "pending_procurement",
    "approved",
    "rejected",
    "processed",
]


# ──────────────────────────────────────────────────────────────────────────────
#  Helper utilities
# ──────────────────────────────────────────────────────────────────────────────

def _req_number(sequence: int) -> str:
    year = timezone.now().year
    return f"REQ-{year}-{sequence:04d}"


def _pick(lst):
    return random.choice(lst)


def _weighted_status():
    """Return a status weighted toward realistic distribution."""
    weights = {
        "draft":              5,
        "pending_hod":        10,
        "approved_hod":       8,
        "pending_hos":        6,
        "approved_hos":       5,
        "pending_procurement":15,
        "approved":           12,
        "rejected":           8,
        "processed":          31,
    }
    population = list(weights.keys())
    cumulative = list(weights.values())
    return random.choices(population, weights=cumulative, k=1)[0]


# ──────────────────────────────────────────────────────────────────────────────
#  The command
# ──────────────────────────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = "Seed procurement data: Suppliers, Categories, Requisitions, and Items."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing procurement data before seeding.",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=30,
            help="Number of purchase requisitions to create (default: 30).",
        )

    # ── entry point ────────────────────────────────────────────────────────
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\n🛒  Procurement Seeder Starting…\n"))

        if options["clear"]:
            self._clear_data()

        with transaction.atomic():
            academic_year = self._get_or_create_academic_year()
            departments   = self._get_departments()
            users         = self._get_procurement_users()

            if not departments:
                raise CommandError(
                    "No Department records found. "
                    "Please seed Departments before running this command."
                )
            if not users:
                raise CommandError(
                    "No User records found. "
                    "Please seed Users before running this command."
                )

            categories = self._seed_categories()
            suppliers  = self._seed_suppliers()
            self._seed_requisitions(
                count=options["count"],
                departments=departments,
                categories=categories,
                users=users,
                academic_year=academic_year,
            )

        self.stdout.write(self.style.SUCCESS("\n✅  Procurement data seeded successfully!\n"))

    # ── clear ──────────────────────────────────────────────────────────────
    def _clear_data(self):
        self.stdout.write(self.style.WARNING("  Clearing existing procurement data…"))
        RequisitionItem.objects.all().delete()
        PurchaseRequisition.objects.all().delete()
        Supplier.objects.all().delete()
        # Only delete non-parent categories first to respect FK constraints
        ProcurementCategory.objects.filter(parent_category__isnull=False).delete()
        ProcurementCategory.objects.all().delete()
        self.stdout.write(self.style.WARNING("  ✓ Cleared.\n"))

    # ── academic year ──────────────────────────────────────────────────────
    def _get_or_create_academic_year(self):
        year = AcademicYear.objects.filter(is_current=True).first()
        if not year:
            now = timezone.now()
            year, created = AcademicYear.objects.get_or_create(
                name=f"{now.year}/{now.year + 1}",
                defaults={
                    "start_date": now.date().replace(month=1, day=1),
                    "end_date":   now.date().replace(month=12, day=31),
                    "is_current": True,
                    "is_active":  True,
                },
            )
            if created:
                self.stdout.write(f"  Created AcademicYear: {year.name}")
        return year

    # ── departments & users ────────────────────────────────────────────────
    def _get_departments(self):
        depts = list(Department.objects.filter(is_active=True))
        self.stdout.write(f"  Found {len(depts)} active department(s).")
        return depts

    def _get_procurement_users(self):
        users = list(User.objects.filter(is_active=True))
        self.stdout.write(f"  Found {len(users)} active user(s).")
        return users

    # ── categories ─────────────────────────────────────────────────────────
    def _seed_categories(self):
        self.stdout.write("\n  Seeding Procurement Categories…")
        code_map = {}   # code → instance

        # First pass: top-level
        for name, code, desc, parent_code in CATEGORY_DATA:
            if parent_code is not None:
                continue
            obj, created = ProcurementCategory.objects.get_or_create(
                code=code,
                defaults={"name": name, "description": desc},
            )
            code_map[code] = obj
            tag = "  +" if created else "  ="
            self.stdout.write(f"{tag} {code}: {name}")

        # Second pass: sub-categories
        for name, code, desc, parent_code in CATEGORY_DATA:
            if parent_code is None:
                continue
            parent = code_map.get(parent_code)
            obj, created = ProcurementCategory.objects.get_or_create(
                code=code,
                defaults={"name": name, "description": desc, "parent_category": parent},
            )
            code_map[code] = obj
            tag = "  +" if created else "  ="
            self.stdout.write(f"{tag}   └─ {code}: {name}")

        self.stdout.write(self.style.SUCCESS(f"  ✓ {len(code_map)} categories ready."))
        return code_map

    # ── suppliers ──────────────────────────────────────────────────────────
    def _seed_suppliers(self):
        self.stdout.write("\n  Seeding Suppliers…")
        created_count = 0
        suppliers = []
        for data in SUPPLIER_DATA:
            obj, created = Supplier.objects.get_or_create(
                supplier_code=data["supplier_code"],
                defaults={k: v for k, v in data.items() if k != "supplier_code"},
            )
            suppliers.append(obj)
            if created:
                created_count += 1
                self.stdout.write(f"  + {obj.supplier_code}: {obj.name}")
            else:
                self.stdout.write(f"  = {obj.supplier_code}: {obj.name}")

        self.stdout.write(self.style.SUCCESS(
            f"  ✓ {created_count} new supplier(s) created, "
            f"{len(suppliers) - created_count} already existed."
        ))
        return suppliers

    # ── requisitions ───────────────────────────────────────────────────────
    def _seed_requisitions(self, count, departments, categories, users, academic_year):
        self.stdout.write(f"\n  Seeding {count} Purchase Requisition(s)…")

        category_list = list(categories.values())
        now           = timezone.now()

        # Build a quick lookup: category_code → ProcurementCategory instance
        cat_by_code = {c.code: c for c in category_list}

        # Map item descriptions to category instances (best-effort)
        item_pool = []
        for desc, cat_code, unit_price, uom in ITEM_DESCRIPTIONS:
            cat = cat_by_code.get(cat_code)
            if not cat:
                # Fall back to any available category
                cat = _pick(category_list)
            item_pool.append((desc, cat, unit_price, uom))

        created_count = 0

        for i in range(1, count + 1):
            req_number = _req_number(i)

            # Skip if already exists (idempotent re-runs)
            if PurchaseRequisition.objects.filter(requisition_number=req_number).exists():
                self.stdout.write(f"  = {req_number} already exists, skipping.")
                continue

            dept       = _pick(departments)
            requester  = _pick(users)
            status     = _weighted_status()
            purpose    = _pick(REQUISITION_PURPOSES)

            # Created-at spread over last 6 months
            days_ago   = random.randint(0, 180)
            created_at = now - timedelta(days=days_ago)

            # Build approval chain fields based on status
            kwargs = {
                "requisition_number": req_number,
                "department":         dept,
                "academic_year":      academic_year,
                "requested_by":       requester,
                "purpose":            purpose,
                "status":             status,
                "created_at":         created_at,   # overridden below via update
            }

            # Attach approver FKs where status implies they were set
            approver = _pick(users)
            if status in ("approved_hod", "pending_hos", "approved_hos",
                          "pending_procurement", "approved", "processed", "rejected"):
                kwargs["approved_by_hod"] = approver
                kwargs["hod_approval_date"] = created_at + timedelta(days=random.randint(1, 3))

            if status in ("approved_hos", "pending_procurement",
                          "approved", "processed", "rejected"):
                kwargs["approved_by_hos"] = approver
                kwargs["hos_approval_date"] = created_at + timedelta(days=random.randint(2, 5))

            if status in ("approved", "processed"):
                kwargs["approved_by_procurement"] = approver
                kwargs["final_approval_date"] = created_at + timedelta(days=random.randint(5, 10))

            if status == "rejected":
                kwargs["remarks"] = _pick([
                    "Budget not available for this period.",
                    "Items can be sourced through existing stock.",
                    "Specifications do not meet requirements.",
                    "Duplicate requisition — already processed.",
                    "Vendor not on approved supplier list.",
                ])

            req = PurchaseRequisition.objects.create(**kwargs)

            # Force created_at since auto_now_add ignores explicit value
            PurchaseRequisition.objects.filter(pk=req.pk).update(created_at=created_at)

            # ── Requisition Items ────────────────────────────────────────
            num_items = random.randint(1, 5)
            selected_items = random.sample(item_pool, min(num_items, len(item_pool)))

            for item_desc, item_cat, base_price, uom in selected_items:
                qty = random.randint(1, 20)
                # Add ±20% price variance
                variance   = Decimal(str(round(random.uniform(0.8, 1.2), 2)))
                unit_price = (base_price * variance).quantize(Decimal("0.01"))

                RequisitionItem.objects.create(
                    requisition=req,
                    category=item_cat,
                    item_description=item_desc,
                    quantity=qty,
                    unit_of_measure=uom,
                    estimated_unit_price=unit_price,
                    total_estimated_price=unit_price * qty,   # also set by model.save()
                    specifications=self._random_specs(item_desc),
                )

            created_count += 1
            self.stdout.write(
                f"  + {req_number} | {dept.code} | {status} | {num_items} item(s)"
            )

        self.stdout.write(self.style.SUCCESS(
            f"\n  ✓ {created_count} requisition(s) created."
        ))

    # ── helpers ────────────────────────────────────────────────────────────
    @staticmethod
    def _random_specs(item_desc: str) -> str:
        specs_pool = [
            "Must comply with university procurement standards.",
            "Warranty of at least 1 year required.",
            "Delivery within 14 working days of LPO issuance.",
            "Must be accompanied by original tax invoice.",
            "Brand: Any reputable manufacturer acceptable.",
            "Compatible with existing university infrastructure.",
            "Environmentally certified products preferred.",
            "Must include installation and commissioning.",
            "",  # blank is valid
            "",
        ]
        return _pick(specs_pool)