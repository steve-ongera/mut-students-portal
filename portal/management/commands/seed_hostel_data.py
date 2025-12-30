"""
Django management command to seed hostel data
File: portal/management/commands/seed_hostel_data.py
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from portal.models import (
    Hostel, HostelRoom, HostelBed, HostelFeeStructure,
    AcademicYear, Semester, User
)
from decimal import Decimal


class Command(BaseCommand):
    help = 'Seeds hostel data with 4 hostels (2 boys, 2 girls), 150 rooms each, 4 beds per room'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing hostel data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing hostel data...'))
            HostelBed.objects.all().delete()
            HostelRoom.objects.all().delete()
            HostelFeeStructure.objects.all().delete()
            Hostel.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing data cleared.'))

        try:
            with transaction.atomic():
                self.stdout.write('Starting hostel data seeding...')
                
                # Get current academic year and semester
                current_academic_year = AcademicYear.objects.filter(is_current=True).first()
                current_semester = Semester.objects.filter(is_current=True).first()
                
                if not current_academic_year:
                    self.stdout.write(self.style.ERROR('No current academic year found. Please create one first.'))
                    return
                
                if not current_semester:
                    self.stdout.write(self.style.ERROR('No current semester found. Please create one first.'))
                    return
                
                self.stdout.write(f'Using Academic Year: {current_academic_year.name}')
                self.stdout.write(f'Using Semester: {current_semester.name}')
                
                # Get or create hostel warden (optional)
                warden = User.objects.filter(role='hostel_warden').first()
                
                # Define hostel configurations
                hostels_config = [
                    {
                        'name': 'Mt. Kenya Hostel',
                        'code': 'MTK',
                        'gender_type': 'M',
                        'location': 'North Campus',
                        'amenities': 'WiFi, Common Room, Kitchen, Laundry, Study Hall, 24/7 Security',
                        'description': 'Premier boys hostel with modern facilities and stunning views'
                    },
                    {
                        'name': 'Mt. Kilimanjaro Hostel',
                        'code': 'MTJ',
                        'gender_type': 'M',
                        'location': 'East Campus',
                        'amenities': 'WiFi, Games Room, Kitchen, Laundry, Gym, Reading Room',
                        'description': 'Spacious boys hostel with recreational facilities'
                    },
                    {
                        'name': 'Mt. Elgon Hostel',
                        'code': 'MTE',
                        'gender_type': 'F',
                        'location': 'South Campus',
                        'amenities': 'WiFi, Beauty Salon, Kitchen, Laundry, Library, Security',
                        'description': 'Comfortable girls hostel with excellent amenities'
                    },
                    {
                        'name': 'Mt. Longonot Hostel',
                        'code': 'MTL',
                        'gender_type': 'F',
                        'location': 'West Campus',
                        'amenities': 'WiFi, Common Room, Kitchen, Laundry, Study Areas, CCTV',
                        'description': 'Modern girls hostel with secure environment'
                    }
                ]
                
                # Room type distribution for 150 rooms
                room_distribution = [
                    {'type': 'single', 'count': 20, 'capacity': 1},
                    {'type': 'double', 'count': 40, 'capacity': 2},
                    {'type': 'triple', 'count': 50, 'capacity': 3},
                    {'type': 'quad', 'count': 40, 'capacity': 4},
                ]
                
                # Fee structure (per semester in KES)
                fee_structure = {
                    'single': {'fee': Decimal('35000.00'), 'booking': Decimal('5000.00'), 'deposit': Decimal('10000.00')},
                    'double': {'fee': Decimal('25000.00'), 'booking': Decimal('3500.00'), 'deposit': Decimal('7500.00')},
                    'triple': {'fee': Decimal('20000.00'), 'booking': Decimal('3000.00'), 'deposit': Decimal('6000.00')},
                    'quad': {'fee': Decimal('15000.00'), 'booking': Decimal('2500.00'), 'deposit': Decimal('5000.00')},
                }
                
                total_hostels = 0
                total_rooms = 0
                total_beds = 0
                
                # Create hostels
                for hostel_config in hostels_config:
                    self.stdout.write(f'\nCreating {hostel_config["name"]}...')
                    
                    # Create hostel
                    hostel = Hostel.objects.create(
                        name=hostel_config['name'],
                        code=hostel_config['code'],
                        gender_type=hostel_config['gender_type'],
                        warden=warden,
                        total_capacity=600,  # 150 rooms * 4 beds average
                        location=hostel_config['location'],
                        description=hostel_config['description'],
                        amenities=hostel_config['amenities'],
                        is_active=True
                    )
                    total_hostels += 1
                    self.stdout.write(self.style.SUCCESS(f'✓ Created {hostel.name}'))
                    
                    # Create rooms based on distribution
                    room_counter = 1
                    for floor in range(1, 6):  # 5 floors, 30 rooms per floor
                        for room_dist in room_distribution:
                            rooms_per_floor = room_dist['count'] // 5  # Distribute evenly across floors
                            
                            for _ in range(rooms_per_floor):
                                if room_counter > 150:
                                    break
                                
                                room_number = f"{hostel.code}{room_counter:03d}"
                                
                                # Create room
                                room = HostelRoom.objects.create(
                                    hostel=hostel,
                                    room_number=room_number,
                                    floor=floor,
                                    room_type=room_dist['type'],
                                    capacity=room_dist['capacity'],
                                    has_bathroom=True,
                                    has_balcony=(floor >= 3),  # Floors 3+ have balconies
                                    is_active=True
                                )
                                total_rooms += 1
                                
                                # Create beds for the room
                                for bed_num in range(1, room_dist['capacity'] + 1):
                                    bed = HostelBed.objects.create(
                                        room=room,
                                        bed_number=f"B{bed_num}",
                                        status='available',
                                        academic_year=current_academic_year,
                                        is_active=True
                                    )
                                    total_beds += 1
                                
                                room_counter += 1
                                
                                # Progress indicator
                                if room_counter % 30 == 0:
                                    self.stdout.write(f'  Created {room_counter} rooms...')
                    
                    self.stdout.write(self.style.SUCCESS(f'✓ Created {room_counter - 1} rooms for {hostel.name}'))
                    
                    # Create fee structures for each room type
                    for room_type, fees in fee_structure.items():
                        fee_struct = HostelFeeStructure.objects.create(
                            hostel=hostel,
                            room_type=room_type,
                            academic_year=current_academic_year,
                            semester=current_semester,
                            fee_amount=fees['fee'],
                            booking_fee=fees['booking'],
                            security_deposit=fees['deposit'],
                            is_active=True
                        )
                    
                    self.stdout.write(self.style.SUCCESS(f'✓ Created fee structures for {hostel.name}'))
                
                # Summary
                self.stdout.write('\n' + '='*70)
                self.stdout.write(self.style.SUCCESS('SEEDING COMPLETED SUCCESSFULLY!'))
                self.stdout.write('='*70)
                self.stdout.write(f'Total Hostels Created: {total_hostels}')
                self.stdout.write(f'Total Rooms Created: {total_rooms}')
                self.stdout.write(f'Total Beds Created: {total_beds}')
                self.stdout.write(f'Academic Year: {current_academic_year.name}')
                self.stdout.write(f'Semester: {current_semester.name}')
                self.stdout.write('='*70)
                
                # Detailed breakdown
                self.stdout.write('\nHostel Details:')
                for hostel in Hostel.objects.all():
                    rooms_count = hostel.rooms.count()
                    beds_count = HostelBed.objects.filter(room__hostel=hostel).count()
                    self.stdout.write(f'\n{hostel.name} ({hostel.code})')
                    self.stdout.write(f'  Gender: {"Boys" if hostel.gender_type == "M" else "Girls"}')
                    self.stdout.write(f'  Location: {hostel.location}')
                    self.stdout.write(f'  Rooms: {rooms_count}')
                    self.stdout.write(f'  Beds: {beds_count}')
                    self.stdout.write(f'  Capacity: {hostel.total_capacity}')
                    
                    # Room type breakdown
                    self.stdout.write('  Room Types:')
                    for room_type in ['single', 'double', 'triple', 'quad']:
                        count = hostel.rooms.filter(room_type=room_type).count()
                        if count > 0:
                            self.stdout.write(f'    - {room_type.capitalize()}: {count} rooms')
                
                self.stdout.write('\nFee Structure (per semester):')
                self.stdout.write('-' * 70)
                self.stdout.write(f'{"Room Type":<15} {"Hostel Fee":<15} {"Booking Fee":<15} {"Deposit":<15}')
                self.stdout.write('-' * 70)
                for room_type, fees in fee_structure.items():
                    self.stdout.write(
                        f'{room_type.capitalize():<15} '
                        f'KES {fees["fee"]:>10,.2f}  '
                        f'KES {fees["booking"]:>10,.2f}  '
                        f'KES {fees["deposit"]:>10,.2f}'
                    )
                self.stdout.write('-' * 70)
                
                self.stdout.write('\n' + self.style.SUCCESS('Hostel data seeded successfully!'))
                self.stdout.write(self.style.WARNING('\nNext steps:'))
                self.stdout.write('1. Verify hostel data in admin panel')
                self.stdout.write('2. Assign hostel wardens if not already done')
                self.stdout.write('3. Configure application deadlines')
                self.stdout.write('4. Open hostel applications for students')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nError during seeding: {str(e)}'))
            raise