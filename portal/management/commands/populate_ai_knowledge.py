# management/commands/populate_ai_knowledge.py
# Create this file at: your_app/management/commands/populate_ai_knowledge.py

from django.core.management.base import BaseCommand
from portal.models import AIKnowledgeBase, QuickAction, AcademicYear


class Command(BaseCommand):
    help = 'Populate AI Knowledge Base with initial data'

    def handle(self, *args, **options):
        self.stdout.write('Populating AI Knowledge Base...')
        
        # Get current academic year
        current_year = AcademicYear.objects.filter(is_current=True).first()
        
        # Knowledge Base Data
        knowledge_data = [
            # Academic Information
            {
                'category': 'academic',
                'question': 'How do I register for units?',
                'answer': 'To register for units:\n1. First complete your semester report\n2. Go to Academic > Unit Registration\n3. Select your units for the semester\n4. Submit your registration\n\nNote: You must have reported for the semester and paid at least 50% of your fees before registering units.',
                'keywords': ['register', 'units', 'enrollment', 'courses', 'unit registration'],
                'alternative_questions': [
                    'How can I enroll in units?',
                    'What is the unit registration process?',
                    'How do I select my courses?'
                ],
                'requires_authentication': True,
                'confidence_score': 95.00,
                'links': [
                    {'url': '/student/unit-enrollment/', 'label': 'Unit Registration', 'icon': 'ri-book-mark-line'}
                ]
            },
            {
                'category': 'academic',
                'question': 'How do I check my GPA?',
                'answer': 'You can view your GPA in several ways:\n1. Dashboard - Shows your current cumulative GPA\n2. Academic > Exam Results - View detailed semester results\n3. Academic > Transcript - View complete academic history\n\nYour GPA is calculated based on all your completed units and is updated after each semester.',
                'keywords': ['gpa', 'grade', 'performance', 'grades', 'results'],
                'alternative_questions': [
                    'What is my current GPA?',
                    'How can I see my grades?',
                    'Where do I find my academic performance?'
                ],
                'requires_authentication': True,
                'confidence_score': 95.00,
                'links': [
                    {'url': '/student/transcript/', 'label': 'View Transcript', 'icon': 'ri-file-list-line'}
                ]
            },
            
            # Fee Information
            {
                'category': 'fees',
                'question': 'How do I check my fee balance?',
                'answer': 'To check your fee balance:\n1. Go to Finance > Fee Statement\n2. Your current balance will be displayed\n3. You can also view payment history and download receipts\n\nYour fee balance includes tuition, activity fees, examination fees, and other charges. {user_name}, make sure to clear your fees on time to avoid penalties.',
                'keywords': ['fee', 'balance', 'payment', 'tuition', 'financial'],
                'alternative_questions': [
                    'What is my current fee balance?',
                    'How much do I owe?',
                    'Check my fees'
                ],
                'requires_authentication': True,
                'confidence_score': 95.00,
                'links': [
                    {'url': '/student/fees/statement/', 'label': 'Fee Statement', 'icon': 'ri-file-text-line'},
                    {'url': '/student/fees/payment/', 'label': 'Make Payment', 'icon': 'ri-money-dollar-circle-line'}
                ]
            },
            {
                'category': 'fees',
                'question': 'What payment methods are accepted?',
                'answer': 'MUT accepts the following payment methods:\n\n1. M-Pesa - Paybill Number: 123456\n2. Bank Transfer - Account details in Fee Statement\n3. Direct Bank Deposit\n4. Cheque payments at the Finance Office\n\nAfter payment, your account is updated within 24-48 hours. Always keep your payment receipts.',
                'keywords': ['payment', 'mpesa', 'bank', 'paybill', 'pay fees'],
                'alternative_questions': [
                    'How can I pay my fees?',
                    'What is the M-Pesa paybill?',
                    'Payment options available'
                ],
                'requires_authentication': False,
                'confidence_score': 90.00
            },
            
            # Results & Examinations
            {
                'category': 'results',
                'question': 'When are exam results released?',
                'answer': 'Exam results are typically released:\n- CATs: 2 weeks after the exam\n- Final Exams: 4-6 weeks after the exam period\n\nYou will receive a notification when your results are published. Check Academic > Exam Results to view your marks.',
                'keywords': ['results', 'marks', 'exam', 'grades', 'release'],
                'alternative_questions': [
                    'When will I see my results?',
                    'How long until results are out?',
                    'Results publication date'
                ],
                'requires_authentication': False,
                'confidence_score': 85.00
            },
            {
                'category': 'results',
                'question': 'How do I apply for special exams (resit)?',
                'answer': 'To apply for special exams:\n1. Go to Academic > Special Unit\n2. Select the units you failed\n3. Pay the resit examination fee\n4. Submit your application\n\nNote: You can only register for resit when the unit is being offered in the current semester. Maximum of 2 failed units allowed to progress.',
                'keywords': ['resit', 'special exam', 'supplementary', 'retake', 'failed unit'],
                'alternative_questions': [
                    'How do I retake a failed unit?',
                    'Register for supplementary exam',
                    'Failed unit registration'
                ],
                'requires_authentication': True,
                'confidence_score': 90.00,
                'links': [
                    {'url': '/student/resit-registration/', 'label': 'Register Resit', 'icon': 'ri-file-edit-line'}
                ]
            },
            
            # Hostel & Accommodation
            {
                'category': 'hostel',
                'question': 'How do I apply for hostel accommodation?',
                'answer': 'To apply for hostel accommodation:\n1. Go to Hostels > Apply for Hostel\n2. Select your preferred hostel and room type\n3. Pay the booking fee\n4. Wait for approval\n5. Complete payment and get your allocation\n\nHostel applications open at the beginning of each semester. Apply early as spaces are limited.',
                'keywords': ['hostel', 'accommodation', 'booking', 'room', 'residence'],
                'alternative_questions': [
                    'How do I book a hostel room?',
                    'Hostel application process',
                    'Student accommodation'
                ],
                'requires_authentication': True,
                'confidence_score': 92.00,
                'links': [
                    {'url': '/student/hostel/apply/', 'label': 'Apply for Hostel', 'icon': 'ri-hotel-line'}
                ]
            },
            
            # Library Services
            {
                'category': 'library',
                'question': 'How do I borrow books from the library?',
                'answer': 'To borrow library books:\n1. Search for books in Library > Search Books\n2. Visit the library with your student ID\n3. Present the book to the librarian\n4. Books are issued for 2 weeks\n\nYou can borrow up to 3 books at a time. Late returns attract a fine of KES 5 per day.',
                'keywords': ['library', 'borrow', 'books', 'issue', 'lending'],
                'alternative_questions': [
                    'How can I get books from library?',
                    'Library borrowing process',
                    'Book loan procedure'
                ],
                'requires_authentication': True,
                'confidence_score': 88.00
            },
            
            # Registration & Enrollment
            {
                'category': 'registration',
                'question': 'What is semester reporting?',
                'answer': 'Semester reporting is the process of officially registering your continuation in the university for a new semester. You must:\n\n1. Complete reporting before unit enrollment\n2. Have maximum 2 failed units from previous semester\n3. Be financially cleared (or have paid minimum required amount)\n\nReport for semester through Academic > Semester Reports.',
                'keywords': ['semester report', 'reporting', 'continuation', 'registration'],
                'alternative_questions': [
                    'How do I report for semester?',
                    'What is semester continuation?',
                    'Register for new semester'
                ],
                'requires_authentication': True,
                'confidence_score': 93.00,
                'links': [
                    {'url': '/student/semester-report/', 'label': 'Semester Report', 'icon': 'ri-file-chart-line'}
                ]
            },
            
            # Student Services
            {
                'category': 'general',
                'question': 'How do I apply for a student ID card?',
                'answer': 'To apply for a student ID card:\n1. Go to Student Services > Student ID Card\n2. Upload your passport photo\n3. Pay the ID card fee via M-Pesa\n4. Wait for processing (7-10 days)\n5. Collect from Student Services office\n\nRush processing is available for an extra fee (3 days).',
                'keywords': ['id card', 'student card', 'identification', 'id'],
                'alternative_questions': [
                    'How can I get my ID card?',
                    'Student ID application',
                    'ID card process'
                ],
                'requires_authentication': True,
                'confidence_score': 91.00,
                'links': [
                    {'url': '/student/id-card/', 'label': 'Apply for ID', 'icon': 'ri-bank-card-line'}
                ]
            },
            
            # Mental Health
            {
                'category': 'mental_health',
                'question': 'I am feeling stressed and overwhelmed. Where can I get help?',
                'answer': 'Your mental health matters! Here are resources available:\n\n1. University Counseling Center\n   - Location: Administration Block, 2nd Floor\n   - Tel: 0712-345-678\n   - Email: counseling@mut.ac.ke\n\n2. Student Wellness Program\n   - Peer support groups\n   - Mental health workshops\n\n3. 24/7 Crisis Helpline: 1190 (Kenya)\n\nAll counseling services are confidential and free. Don\'t hesitate to reach out!',
                'keywords': ['stress', 'mental health', 'depression', 'anxiety', 'counseling', 'help'],
                'alternative_questions': [
                    'I need someone to talk to',
                    'Mental health support',
                    'Feeling depressed',
                    'Need counseling'
                ],
                'requires_authentication': False,
                'confidence_score': 95.00
            },
            
            # Technical Support
            {
                'category': 'technical',
                'question': 'I forgot my portal password. How do I reset it?',
                'answer': 'To reset your password:\n1. Click "Forgot Password" on the login page\n2. Enter your registration number or email\n3. Check your email for reset link\n4. Click the link and create a new password\n\nIf you don\'t receive the email:\n- Check spam folder\n- Contact ICT Help Desk: ict@mut.ac.ke\n- Visit ICT office with your ID',
                'keywords': ['password', 'reset', 'forgot', 'login', 'access'],
                'alternative_questions': [
                    'Can\'t login to portal',
                    'Forgot my password',
                    'Reset password',
                    'Login problems'
                ],
                'requires_authentication': False,
                'confidence_score': 92.00
            },
            
            # Contact Information
            {
                'category': 'general',
                'question': 'Who can I contact for help?',
                'answer': 'Contact information for different departments:\n\n📚 Academic Issues: academic@mut.ac.ke\n💰 Finance/Fees: finance@mut.ac.ke\n🏨 Hostel: hostel@mut.ac.ke\n📖 Library: library@mut.ac.ke\n💻 ICT Support: ict@mut.ac.ke\n🎓 Student Affairs: students@mut.ac.ke\n\nMain Reception: 0712-000-000\nEmergency: 0700-111-222',
                'keywords': ['contact', 'email', 'phone', 'help', 'support'],
                'alternative_questions': [
                    'Contact details',
                    'Phone numbers',
                    'How do I reach support?'
                ],
                'requires_authentication': False,
                'confidence_score': 94.00
            }
        ]
        
        # Create knowledge base entries
        created_count = 0
        for data in knowledge_data:
            obj, created = AIKnowledgeBase.objects.get_or_create(
                question=data['question'],
                defaults={
                    **data,
                    'academic_year': current_year,
                    'is_verified': True,
                    'status': 'active'
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created: {data["question"][:50]}...'))
        
        # Quick Actions
        quick_actions = [
            {
                'name': 'Fee Statement',
                'description': 'View your current fee balance and payment history',
                'action_type': 'navigation',
                'icon': 'ri-file-text-line',
                'target_url': '/student/fees/statement/',
                'requires_authentication': True,
                'applicable_roles': ['student'],
                'related_categories': ['fees'],
                'trigger_keywords': ['fee', 'balance', 'payment'],
                'display_order': 1
            },
            {
                'name': 'My Results',
                'description': 'Check your examination results and grades',
                'action_type': 'navigation',
                'icon': 'ri-file-list-line',
                'target_url': '/student/results/',
                'requires_authentication': True,
                'applicable_roles': ['student'],
                'related_categories': ['results', 'academic'],
                'trigger_keywords': ['results', 'marks', 'grades'],
                'display_order': 2
            },
            {
                'name': 'Timetable',
                'description': 'View your class timetable',
                'action_type': 'navigation',
                'icon': 'ri-calendar-line',
                'target_url': '/student/timetable/',
                'requires_authentication': True,
                'applicable_roles': ['student'],
                'related_categories': ['academic'],
                'trigger_keywords': ['timetable', 'schedule', 'classes'],
                'display_order': 3
            },
            {
                'name': 'Unit Registration',
                'description': 'Register for semester units',
                'action_type': 'navigation',
                'icon': 'ri-book-mark-line',
                'target_url': '/student/unit-enrollment/',
                'requires_authentication': True,
                'applicable_roles': ['student'],
                'related_categories': ['registration', 'academic'],
                'trigger_keywords': ['register', 'units', 'enrollment'],
                'display_order': 4
            },
            {
                'name': 'Hostel Booking',
                'description': 'Apply for hostel accommodation',
                'action_type': 'navigation',
                'icon': 'ri-hotel-line',
                'target_url': '/student/hostel/apply/',
                'requires_authentication': True,
                'applicable_roles': ['student'],
                'related_categories': ['hostel'],
                'trigger_keywords': ['hostel', 'accommodation', 'room'],
                'display_order': 5
            },
            {
                'name': 'Help Desk',
                'description': 'Contact support for assistance',
                'action_type': 'external_link',
                'icon': 'ri-customer-service-line',
                'target_url': 'mailto:support@mut.ac.ke',
                'requires_authentication': False,
                'applicable_roles': [],
                'related_categories': ['general', 'technical'],
                'trigger_keywords': ['help', 'support', 'contact'],
                'display_order': 6
            }
        ]
        
        actions_count = 0
        for action_data in quick_actions:
            obj, created = QuickAction.objects.get_or_create(
                name=action_data['name'],
                defaults=action_data
            )
            if created:
                actions_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created quick action: {action_data["name"]}'))
        
        self.stdout.write(self.style.SUCCESS(
            f'\nSuccessfully created {created_count} knowledge base entries '
            f'and {actions_count} quick actions!'
        ))