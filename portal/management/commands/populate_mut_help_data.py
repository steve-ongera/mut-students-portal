# management/commands/populate_mut_help_data.py
# Create: your_app/management/commands/populate_mut_help_data.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from portal.models import FAQ, SystemGuide, ContactInfo


class Command(BaseCommand):
    help = 'Populate Help & Support data for Murang\'a University of Technology'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('Populating MUT Help & Support Data'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        
        # Clear existing data
        self.stdout.write('\nClearing existing data...')
        FAQ.objects.all().delete()
        SystemGuide.objects.all().delete()
        ContactInfo.objects.all().delete()
        self.stdout.write(self.style.WARNING('✓ Cleared old data'))
        
        # Populate data
        faq_count = self.create_faqs()
        guide_count = self.create_guides()
        contact_count = self.create_contacts()
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 70))
        self.stdout.write(self.style.SUCCESS('SUMMARY'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS(f'✓ Created {faq_count} FAQs'))
        self.stdout.write(self.style.SUCCESS(f'✓ Created {guide_count} System Guides'))
        self.stdout.write(self.style.SUCCESS(f'✓ Created {contact_count} Department Contacts'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('✓ All data populated successfully!'))

    def create_faqs(self):
        """Create MUT-specific FAQs"""
        self.stdout.write('\nCreating FAQs...')
        
        faqs = [
            # ACADEMIC
            {
                'category': 'academic',
                'question': 'How do I register for units at MUT?',
                'answer': '''To register for units at Murang'a University of Technology:

1. Complete semester reporting first
2. Ensure you've paid at least 50% of semester fees
3. Go to Academic > Unit Registration on student portal
4. Select units for your year and semester
5. Submit registration

Requirements:
- Maximum 2 failed units from previous semester
- Financial clearance (50% minimum)
- Completed semester reporting

Registration period: First 2 weeks of each semester
Contact: academic@mut.ac.ke | +254 712 000 001''',
                'display_order': 1,
            },
            {
                'category': 'academic',
                'question': 'How do I check my GPA and results?',
                'answer': '''View your GPA and results:

1. Login to student portal
2. Dashboard shows current cumulative GPA
3. Go to Academic > Exam Results for detailed breakdown
4. Academic > Transcript for full academic history

Results Timeline:
- CATs: Published within 2 weeks
- Final Exams: Published 4-6 weeks after exam period
- Email notification when published

GPA Scale: A=5.0, A-=4.7, B+=4.3, B=4.0, B-=3.7, C+=3.3, C=3.0, C-=2.7, D+=2.3, D=2.0, E=0.0

Contact: academic@mut.ac.ke''',
                'display_order': 2,
            },
            {
                'category': 'academic',
                'question': 'What is semester reporting?',
                'answer': '''Semester reporting is your official continuation registration.

Process:
1. Go to Academic > Semester Reports
2. Review eligibility (max 2 failed units)
3. Submit report
4. Wait for approval (24-48 hours)

Requirements:
- Maximum 2 failed units
- Financial clearance
- No disciplinary holds

Must report before unit registration.
Reporting period: First week of each semester

Contact: registrar@mut.ac.ke | +254 712 000 002''',
                'display_order': 3,
            },
            {
                'category': 'academic',
                'question': 'How do I apply for resit/supplementary exams?',
                'answer': '''Apply for special exams if you failed a unit:

Requirements:
- Failed grade (E) in a unit
- Unit must be offered in current semester
- Maximum 2 failed units allowed

Process:
1. Academic > Special Unit
2. Select failed unit(s)
3. Pay resit fee: KES 1,500 per unit
4. Submit application

Payment: M-Pesa Paybill 400200
Account: Your Registration Number

Application deadline: First 2 weeks of semester
Contact: academic@mut.ac.ke''',
                'display_order': 4,
            },
            
            # FINANCE
            {
                'category': 'finance',
                'question': 'How do I check my fee balance?',
                'answer': '''Check your fee balance on the portal:

1. Login to student portal
2. Finance > Fee Statement
3. View total fees, payments, and balance

Statement shows:
- Total semester fees
- All payments made
- Current balance
- Transaction history

Update time: Payments reflect within 24-48 hours

Download PDF statement for records.

Contact: finance@mut.ac.ke | +254 712 000 003''',
                'display_order': 1,
            },
            {
                'category': 'finance',
                'question': 'What payment methods does MUT accept?',
                'answer': '''MUT accepts multiple payment methods:

M-Pesa (Recommended):
- Paybill: 400200
- Account: Your Registration Number
- Available 24/7

Bank Deposit/Transfer:
- Bank: KCB Murang'a Branch
- Account: Murang'a University of Technology
- Reference: Your Reg Number

Cash/Cheque:
- Finance Office, Admin Block
- Hours: 8 AM - 5 PM, Mon-Fri

Important:
- Always use your Registration Number
- Keep payment confirmations
- Allow 24-48 hours for processing

Contact: finance@mut.ac.ke''',
                'display_order': 2,
            },
            {
                'category': 'finance',
                'question': 'What are the fee payment deadlines?',
                'answer': '''Fee payment schedule per semester:

1st Installment (Registration):
- Minimum 50% of total fees
- Before unit registration

2nd Installment (Mid-Semester):
- 75% of total fees
- Before CAT 2 exams

Final Payment:
- 100% of fees
- Before final exams

Late payment penalties:
- Late registration: KES 1,000
- Cannot sit exams with outstanding fees

Payment Timeline:
- Sem 1 (Sept): Register by Week 2
- Sem 2 (Jan): Register by Week 2
- Sem 3 (May): Register by Week 2

Contact: finance@mut.ac.ke''',
                'display_order': 3,
            },
            
            # HOSTEL
            {
                'category': 'hostel',
                'question': 'How do I apply for hostel accommodation?',
                'answer': '''Apply for MUT hostel accommodation:

Process:
1. Hostels > Apply for Hostel
2. Select preferred hostel
3. Choose room type
4. Pay booking fee: KES 2,000
5. Wait for allocation (2-5 days)

Available Hostels:
- Mathioya (Boys)
- Kigumo (Boys)
- Kandara (Girls)
- Makuyu (Girls)
- Maragua (Mixed)

Room Types & Fees (per semester):
- Single: KES 15,000
- Double: KES 12,000
- Triple: KES 10,000
- Quad: KES 8,500

Application period: 2 weeks before semester
First-come-first-served basis

Contact: hostel@mut.ac.ke | +254 712 000 004''',
                'display_order': 1,
            },
            {
                'category': 'hostel',
                'question': 'What are MUT hostel rules?',
                'answer': '''MUT Hostel Regulations:

Curfew:
- Weekdays: 10:00 PM
- Weekends: 11:00 PM
- No entry after curfew

Visitors:
- Allowed 8 AM - 6 PM only
- Must sign in at reception
- No overnight visitors
- Opposite gender not in rooms

Prohibited:
- Alcohol and drugs
- Weapons
- Cooking appliances (except kettles)
- Pets
- Loud music after 10 PM

Penalties:
- Minor offenses: Warning
- Major offenses: Suspension/Expulsion

Report maintenance: Hostel > Maintenance Request

Contact Warden: hostel@mut.ac.ke''',
                'display_order': 2,
            },
            
            # LIBRARY
            {
                'category': 'library',
                'question': 'How do I borrow books from the library?',
                'answer': '''Borrow books from MUT Library:

Process:
1. Search for book in catalog
2. Present student ID at issue desk
3. Book is scanned and issued
4. Receive due date slip

Borrowing Limits:
- 3 books per undergraduate student
- 2 weeks borrowing period
- Renewable once (if no requests)

Fines:
- KES 5 per day for late returns
- KES 200 for lost library card

Library Hours:
- Mon-Fri: 7 AM - 10 PM
- Saturday: 8 AM - 6 PM
- Sunday: 9 AM - 5 PM

Services:
- Photocopying: KES 5/page
- Printing: KES 10/page
- Wi-Fi: Free

Contact: library@mut.ac.ke | +254 712 000 005''',
                'display_order': 1,
            },
            
            # TECHNICAL
            {
                'category': 'technical',
                'question': 'I forgot my portal password. How do I reset it?',
                'answer': '''Reset your MUT portal password:

Method 1 - Self Service:
1. Go to portal.mut.ac.ke
2. Click "Forgot Password"
3. Enter Registration Number
4. Check email for reset link
5. Create new password

Method 2 - ICT Help Desk:
- Visit ICT Block, Ground Floor
- Present student ID
- Immediate password reset
- Hours: 8 AM - 5 PM, Mon-Fri

Password Requirements:
- Minimum 8 characters
- Upper and lowercase letters
- At least one number
- At least one special character

Contact: ict@mut.ac.ke | +254 712 000 006''',
                'display_order': 1,
            },
            {
                'category': 'technical',
                'question': 'How do I connect to MUT Wi-Fi?',
                'answer': '''Connect to MUT Wi-Fi on campus:

Setup:
1. Enable Wi-Fi on device
2. Select "MUT-Students" network
3. Browser opens automatically
4. Login with:
   - Username: Registration Number
   - Password: Portal password

Connection Limits:
- 2 devices per student
- Unlimited data
- Speed: Up to 10 Mbps
- Auto-disconnect after 12 hours

Coverage:
- All lecture halls
- Library
- Hostels
- Admin block
- Cafeteria

Troubleshooting:
- Restart device
- Forget network and reconnect
- Clear browser cache
- Visit ICT Help Desk

Contact: ict@mut.ac.ke''',
                'display_order': 2,
            },
            
            # GENERAL
            {
                'category': 'general',
                'question': 'How do I apply for a student ID card?',
                'answer': '''Apply for MUT student ID card:

Process:
1. Student Services > Student ID Card
2. Upload passport photo
3. Verify your details
4. Pay ID card fee
5. Wait for processing

Fees:
- New ID: KES 500
- Replacement: KES 700
- Rush processing: +KES 300

Payment: M-Pesa Paybill 400200

Processing Time:
- Standard: 7-10 working days
- Rush: 3 working days

Collection:
- Student Services Office
- Admin Block, Room 105
- Bring student ID

Contact: students@mut.ac.ke | +254 712 000 007''',
                'display_order': 1,
            },
        ]
        
        count = 0
        for faq_data in faqs:
            FAQ.objects.create(**faq_data)
            count += 1
            self.stdout.write(f'  ✓ {faq_data["question"][:60]}...')
        
        return count

    def create_guides(self):
        """Create system guides"""
        self.stdout.write('\nCreating System Guides...')
        
        guides = [
            {
                'title': 'Getting Started with MUT Student Portal',
                'guide_type': 'getting_started',
                'description': 'Complete guide to accessing and navigating the MUT student portal for new students.',
                'content': '''# Getting Started with MUT Student Portal

Welcome to Murang'a University of Technology! This guide will help you get started with the student portal.

## Accessing the Portal

1. **Go to**: portal.mut.ac.ke
2. **Login with**:
   - Username: Your Registration Number (e.g., SC211/0530/2022)
   - Password: Provided during registration

## First Time Login

On your first login:
1. You'll be prompted to change your password
2. Create a strong password (min 8 characters)
3. Update your profile information
4. Add your email and phone number

## Portal Dashboard

Your dashboard shows:
- Current GPA
- Fee balance
- Upcoming deadlines
- Recent announcements
- Quick actions

## Main Features

### Academic Section
- Unit Registration
- View Timetable
- Check Results
- Download Transcript
- Apply for Resit Exams

### Finance Section
- View Fee Statement
- Payment History
- Download Receipts
- Fee Structure

### Personal Section
- Update Profile
- Change Password
- Upload Profile Photo
- Update Contact Details

## Important Tips

- Keep your login credentials safe
- Check portal daily for announcements
- Update your email and phone number
- Download the MUT Mobile app
- Report any issues to ICT support

## Need Help?

Contact ICT Help Desk:
- Email: ict@mut.ac.ke
- Phone: +254 712 000 006
- Location: ICT Block, Ground Floor''',
                'display_order': 1,
            },
            {
                'title': 'How to Register Units at MUT',
                'guide_type': 'academic',
                'description': 'Step-by-step guide on how to register for semester units online.',
                'content': '''# How to Register Units at MUT

This guide explains the unit registration process at Murang'a University of Technology.

## Prerequisites

Before you can register units:
1. Complete semester reporting
2. Pay at least 50% of semester fees
3. Have maximum 2 failed units
4. Check you're in the registration period

## Registration Process

### Step 1: Semester Reporting
1. Go to Academic > Semester Reports
2. Review your progression details
3. Submit your semester report
4. Wait for approval (24-48 hours)

### Step 2: Check Units Available
1. Go to Academic > Unit Registration
2. View units for your year and semester
3. See core and elective units
4. Check prerequisites

### Step 3: Select Units
1. Click on each unit to add
2. Review unit details
3. Check for any conflicts in timetable
4. Ensure you meet prerequisites

### Step 4: Submit Registration
1. Review your selected units
2. Check total credit hours
3. Click "Submit Registration"
4. Print confirmation slip

## Important Information

**Core Units**:
- Must register for all core units
- Cannot graduate without completing them
- No substitution allowed

**Elective Units**:
- Choose based on interest
- Subject to availability
- May have capacity limits

**Credit Hours**:
- Minimum per semester: 12 credit hours
- Maximum per semester: 21 credit hours
- Need at least 120 for graduation

## Registration Deadlines

- Week 1-2 of semester: Normal registration
- After Week 2: Late registration (KES 1,000 penalty)
- No registration after Week 3

## Common Issues

**"Cannot register"**: Check if you've reported for semester

**"Unit not available"**: May be full or not offered this semester

**"Prerequisites not met"**: Complete required units first

## Need Help?

Contact your Academic Advisor or:
- Email: academic@mut.ac.ke
- Phone: +254 712 000 001''',
                'display_order': 2,
            },
            {
                'title': 'Making Fee Payments to MUT',
                'guide_type': 'finance',
                'description': 'Complete guide on how to pay your fees using various payment methods.',
                'content': '''# Making Fee Payments to MUT

Learn how to pay your semester fees at Murang'a University of Technology.

## Payment Methods

### Method 1: M-Pesa (Recommended)

**Steps**:
1. Go to M-Pesa menu
2. Select "Lipa na M-Pesa"
3. Choose "Pay Bill"
4. Enter Paybill: **400200**
5. Account Number: **Your Registration Number**
6. Amount: Enter amount to pay
7. Enter PIN and confirm
8. Save confirmation message

**Example**:
- Paybill: 400200
- Account: SC211/0530/2022
- Amount: 25000

### Method 2: Bank Deposit

**Bank Details**:
- Bank: Kenya Commercial Bank (KCB)
- Branch: Murang'a Branch
- Account: Murang'a University of Technology
- Reference: Your Registration Number

**Steps**:
1. Visit any KCB branch
2. Fill deposit slip
3. Use your Reg Number as reference
4. Keep deposit slip as receipt

### Method 3: Direct Bank Transfer

Use mobile/online banking:
1. Add MUT as beneficiary
2. Use account details above
3. Reference: Your Reg Number
4. Confirm transfer
5. Save receipt

## After Payment

1. Keep payment confirmation
2. Wait 24-48 hours for processing
3. Check portal: Finance > Payment History
4. Download official receipt

## Payment Schedule

**1st Installment (50%)**:
- Pay before unit registration
- Required to register units

**2nd Installment (25%)**:
- Pay before CAT 2
- Required to sit for CATs

**Final Payment (25%)**:
- Pay before final exams
- Required to sit for exams

## Important Notes

- Always use YOUR Registration Number
- Keep ALL payment confirmations
- Check portal after 48 hours
- Get receipt from Finance Office if payment not showing

## Payment Issues?

Contact Finance Office:
- Email: finance@mut.ac.ke
- Phone: +254 712 000 003
- Visit: Admin Block, Finance Office
- Hours: 8 AM - 5 PM, Mon-Fri''',
                'display_order': 3,
            },
        ]
        
        count = 0
        for guide_data in guides:
            SystemGuide.objects.create(**guide_data)
            count += 1
            self.stdout.write(f'  ✓ {guide_data["title"]}')
        
        return count

    def create_contacts(self):
        """Create department contact information"""
        self.stdout.write('\nCreating Department Contacts...')
        
        contacts = [
            {
                'department': 'Academic Office',
                'email': 'academic@mut.ac.ke',
                'phone_primary': '+254 712 000 001',
                'phone_secondary': '+254 733 000 001',
                'office_location': 'Administration Block, Room 201',
                'office_hours': 'Mon-Fri: 8:00 AM - 5:00 PM',
                'description': 'For all academic matters including unit registration, results, transcripts, and academic queries.',
                'display_order': 1,
            },
            {
                'department': 'Finance Office',
                'email': 'finance@mut.ac.ke',
                'phone_primary': '+254 712 000 003',
                'phone_secondary': '+254 733 000 003',
                'office_location': 'Administration Block, Ground Floor',
                'office_hours': 'Mon-Fri: 8:00 AM - 5:00 PM',
                'description': 'For fee payments, fee statements, receipts, and all financial matters.',
                'display_order': 2,
            },
            {
                'department': 'Hostel Office',
                'email': 'hostel@mut.ac.ke',
                'phone_primary': '+254 712 000 004',
                'phone_secondary': '+254 733 000 004',
                'office_location': 'Hostel Administration Office',
                'office_hours': 'Mon-Sun: 8:00 AM - 10:00 PM',
                'description': 'For hostel applications, room allocations, maintenance requests, and hostel-related issues.',
                'display_order': 3,
            },
            {
                'department': 'Library Services',
                'email': 'library@mut.ac.ke',
                'phone_primary': '+254 712 000 005',
                'phone_secondary': '+254 733 000 005',
                'office_location': 'Main Library, Ground Floor',
                'office_hours': 'Mon-Fri: 7:00 AM - 10:00 PM, Sat: 8:00 AM - 6:00 PM, Sun: 9:00 AM - 5:00 PM',
                'description': 'For book borrowing, library fines, digital resources, and library services.',
                'display_order': 4,
            },
            {
                'department': 'ICT Support',
                'email': 'ict@mut.ac.ke',
                'phone_primary': '+254 712 000 006',
                'phone_secondary': '+254 733 000 006',
                'office_location': 'ICT Block, Ground Floor - Help Desk',
                'office_hours': 'Mon-Fri: 8:00 AM - 5:00 PM',
                'description': 'For portal issues, password resets, Wi-Fi problems, and all technical support.',
                'display_order': 5,
            },
            {
                'department': 'Student Affairs',
                'email': 'students@mut.ac.ke',
                'phone_primary': '+254 712 000 007',
                'phone_secondary': '+254 733 000 007',
                'office_location': 'Administration Block, Room 105',
                'office_hours': 'Mon-Fri: 8:00 AM - 5:00 PM',
                'description': 'For student ID cards, clearance certificates, student welfare, and general student services.',
                'display_order': 6,
            },
            {
                'department': 'Admissions Office',
                'email': 'admissions@mut.ac.ke',
                'phone_primary': '+254 712 000 008',
                'phone_secondary': '+254 733 000 008',
                'office_location': 'Administration Block, Room 102',
                'office_hours': 'Mon-Fri: 8:00 AM - 5:00 PM',
                'description': 'For new student admissions, programme information, and admission queries.',
                'display_order': 7,
            },
            {
                'department': 'Registrar',
                'email': 'registrar@mut.ac.ke',
                'phone_primary': '+254 712 000 002',
                'phone_secondary': '+254 733 000 002',
                'office_location': 'Administration Block, Room 210',
                'office_hours': 'Mon-Fri: 8:00 AM - 5:00 PM',
                'description': 'For registration matters, official transcripts, and academic records.',
                'display_order': 8,
            },
            {
                'department': 'Counseling Center',
                'email': 'counseling@mut.ac.ke',
                'phone_primary': '+254 712 000 009',
                'phone_secondary': '1190',
                'office_location': 'Student Center, 1st Floor',
                'office_hours': 'Mon-Fri: 8:00 AM - 8:00 PM',
                'description': 'Confidential counseling services, mental health support, and student wellness.',
                'display_order': 9,
            },
            {
                'department': 'Main Reception',
                'email': 'info@mut.ac.ke',
                'phone_primary': '+254 712 000 000',
                'phone_secondary': '+254 733 000 000',
                'office_location': 'Administration Block, Ground Floor',
                'office_hours': 'Mon-Fri: 8:00 AM - 5:00 PM',
                'description': 'General information, directions, and inquiries.',
                'display_order': 10,
            },
        ]
        
        count = 0
        for contact_data in contacts:
            ContactInfo.objects.create(**contact_data)
            count += 1
            self.stdout.write(f'  ✓ {contact_data["department"]}')
        
        return count