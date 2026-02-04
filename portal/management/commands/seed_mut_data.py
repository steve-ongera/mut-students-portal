"""
Management command to seed Muranga University of Technology (MUT) data
Run with: python manage.py seed_mut_data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import datetime, timedelta, date
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds database with Muranga University of Technology data'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting MUT data seeding...'))
        
        # Import models here to avoid app loading issues
        from portal.models import (
            School, Department, Programme, AcademicYear, Semester,
            SchoolBudget, BudgetAllocation, ExpenditureTracking, RevenueSource,
            Partnership, MOU, CollaborativeProject, AlumniRelation,
            StrategicGoal, PerformanceIndicator, AnnualPlan, AnnualPlanActivity,
            ProgressReport, DeanApproval, AdvisingNote, StudentSpecialNeed,
            UniversityCouncil, SenateSession, ManagementBoardMeeting,
            InternationalRanking, CapitalProject, RiskRegister,
            Lecturer, Student
        )
        
        # Clear existing data (optional - comment out if you want to keep existing data)
        self.stdout.write('Clearing existing data...')
        # Be careful with this - only use in development
        
        # Fetch existing Academic Years
        self.stdout.write('Fetching academic years...')
        academic_years = list(AcademicYear.objects.all().order_by('start_date'))
        self.stdout.write(f'  Found {len(academic_years)} academic years')
        
        if not academic_years:
            self.stdout.write(self.style.ERROR('  No academic years found! Please create academic years first.'))
            return
        
        current_ay = AcademicYear.objects.filter(is_current=True).first()
        if not current_ay:
            self.stdout.write(self.style.ERROR('  No current academic year found! Please set a current academic year.'))
            return
        
        # Fetch existing Semesters
        self.stdout.write('Fetching existing semesters...')
        semesters = Semester.objects.all()
        self.stdout.write(f'  Found {semesters.count()} semesters')
        
        current_semester = Semester.objects.filter(is_current=True).first()
        
        # Create admin user for relationships
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@mut.ac.ke',
                'first_name': 'System',
                'last_name': 'Administrator',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write('  Created admin user')
        
        # Fetch existing Schools, Departments, and Programmes
        self.stdout.write('Fetching existing schools, departments, and programmes...')
        schools = {school.code: school for school in School.objects.all()}
        self.stdout.write(f'  Found {len(schools)} schools')
        
        departments = {dept.code: dept for dept in Department.objects.all()}
        self.stdout.write(f'  Found {len(departments)} departments')
        
        programmes = {prog.code: prog for prog in Programme.objects.all()}
        self.stdout.write(f'  Found {len(programmes)} programmes')
        
        if not schools:
            self.stdout.write(self.style.ERROR('  No schools found! Please create schools first.'))
            return
        
        if not departments:
            self.stdout.write(self.style.ERROR('  No departments found! Please create departments first.'))
            return
        
        if not programmes:
            self.stdout.write(self.style.ERROR('  No programmes found! Please create programmes first.'))
            return
        
        # ============= FINANCIAL MANAGEMENT =============
        self.stdout.write('\nCreating financial data...')
        
        # Create School Budgets
        for school in schools.values():
            budget, created = SchoolBudget.objects.get_or_create(
                school=school,
                financial_year=current_ay,
                defaults={
                    'total_allocation': Decimal(random.randint(50000000, 200000000)),
                    'amount_spent': Decimal(random.randint(20000000, 80000000)),
                    'personnel_budget': Decimal(random.randint(20000000, 80000000)),
                    'operations_budget': Decimal(random.randint(10000000, 40000000)),
                    'development_budget': Decimal(random.randint(5000000, 20000000)),
                    'research_budget': Decimal(random.randint(3000000, 15000000)),
                    'status': 'active',
                    'submitted_by': admin_user,
                    'submitted_date': timezone.now() - timedelta(days=200),
                    'approved_by': admin_user,
                    'approval_date': timezone.now() - timedelta(days=180),
                }
            )
            if created:
                self.stdout.write(f'  Created budget for {school.code}')
                
                # Create Budget Allocations for departments
                for dept in Department.objects.filter(school=school):
                    allocation_amount = budget.total_allocation / Department.objects.filter(school=school).count()
                    BudgetAllocation.objects.create(
                        school_budget=budget,
                        department=dept,
                        allocation_amount=allocation_amount,
                        amount_utilized=allocation_amount * Decimal('0.65'),
                        personnel=allocation_amount * Decimal('0.5'),
                        operations=allocation_amount * Decimal('0.3'),
                        equipment=allocation_amount * Decimal('0.15'),
                        supplies=allocation_amount * Decimal('0.05'),
                        allocated_by=admin_user,
                        allocation_date=current_ay.start_date,
                    )
        
        # Create Expenditure Tracking
        self.stdout.write('Creating expenditure records...')
        for allocation in BudgetAllocation.objects.all()[:20]:  # Sample 20 allocations
            for i in range(random.randint(3, 8)):
                ExpenditureTracking.objects.create(
                    budget_allocation=allocation,
                    expenditure_type=random.choice(['personnel', 'operations', 'equipment', 'supplies']),
                    description=f'Payment for {random.choice(["office supplies", "equipment purchase", "staff allowances", "maintenance services"])}',
                    amount=Decimal(random.randint(50000, 500000)),
                    payee_name=f'Vendor {random.randint(1, 50)}',
                    transaction_date=current_ay.start_date + timedelta(days=random.randint(0, 200)),
                    status=random.choice(['paid', 'approved', 'pending']),
                    requested_by=admin_user,
                    approved_by=admin_user if random.random() > 0.3 else None,
                )
        
        # Create Revenue Sources
        self.stdout.write('Creating revenue sources...')
        revenue_types = ['government_grant', 'tuition_fees', 'research_grants', 'consultancy', 'donations']
        for school in schools.values():
            for rev_type in revenue_types:
                RevenueSource.objects.create(
                    school=school,
                    academic_year=current_ay,
                    revenue_type=rev_type,
                    source_name=f'{rev_type.replace("_", " ").title()} - {school.code}',
                    amount=Decimal(random.randint(5000000, 50000000)),
                    received_date=current_ay.start_date + timedelta(days=random.randint(0, 180)),
                    recorded_by=admin_user,
                )
        
        # ============= PARTNERSHIPS & LINKAGES =============
        self.stdout.write('\nCreating partnerships...')
        
        # Get list of schools for partnerships
        school_list = list(schools.values())
        
        partnerships_data = [
            {
                'partner_name': 'Microsoft East Africa',
                'partnership_type': 'industry',
                'country': 'Kenya',
                'contact_person': 'John Kamau',
                'contact_email': 'j.kamau@microsoft.com',
                'description': 'Partnership for curriculum development and student training in cloud computing',
                'areas_of_collaboration': 'Cloud computing, Azure certification, internships',
            },
            {
                'partner_name': 'Huawei Technologies',
                'partnership_type': 'industry',
                'country': 'China',
                'contact_person': 'Li Wei',
                'contact_email': 'li.wei@huawei.com',
                'description': 'ICT Academy partnership for training and certification',
                'areas_of_collaboration': '5G technology, networking, IoT',
            },
            {
                'partner_name': 'Kenya Urban Roads Authority (KURA)',
                'partnership_type': 'government',
                'country': 'Kenya',
                'contact_person': 'Eng. Peter Mundinia',
                'contact_email': 'p.mundinia@kura.go.ke',
                'description': 'Collaboration on road infrastructure projects and research',
                'areas_of_collaboration': 'Road design, materials testing, student attachments',
            },
            {
                'partner_name': 'International Centre of Insect Physiology and Ecology (ICIPE)',
                'partnership_type': 'research',
                'country': 'Kenya',
                'contact_person': 'Dr. Jane Wanjiru',
                'contact_email': 'j.wanjiru@icipe.org',
                'description': 'Research collaboration in biological sciences',
                'areas_of_collaboration': 'Entomology research, student projects, joint publications',
            },
            {
                'partner_name': 'KCB Bank Kenya',
                'partnership_type': 'industry',
                'country': 'Kenya',
                'contact_person': 'Mary Njeri',
                'contact_email': 'm.njeri@kcb.co.ke',
                'description': 'Partnership for entrepreneurship training and student internships',
                'areas_of_collaboration': 'Banking operations, financial literacy, entrepreneurship',
            },
            {
                'partner_name': 'Sarova Hotels',
                'partnership_type': 'industry',
                'country': 'Kenya',
                'contact_person': 'David Mwangi',
                'contact_email': 'd.mwangi@sarovahotels.com',
                'description': 'Student internship and training program',
                'areas_of_collaboration': 'Hotel operations, culinary arts, hospitality management',
            },
        ]
        
        partnerships = []
        for i, p_data in enumerate(partnerships_data):
            # Assign partnership to schools cyclically
            school = school_list[i % len(school_list)]
            
            partnership, created = Partnership.objects.get_or_create(
                partner_name=p_data['partner_name'],
                defaults={
                    **p_data,
                    'school': school,
                    'focal_person': admin_user,
                    'start_date': date(2020, 1, 1),
                    'status': 'active',
                }
            )
            partnerships.append(partnership)
            if created:
                self.stdout.write(f'  Created partnership: {partnership.partner_name} for {school.code}')
                
                # Create MOU for each partnership
                MOU.objects.create(
                    partnership=partnership,
                    title=f'MOU between MUT and {partnership.partner_name}',
                    mou_number=f'MOU-{partnership.id:04d}-{timezone.now().year}',
                    signing_date=date(2022, 3, 15),
                    effective_date=date(2022, 4, 1),
                    expiry_date=date(2027, 3, 31),
                    scope='Collaborative research, student training, and knowledge exchange',
                    deliverables='Joint research projects, student internships, staff exchange',
                    responsibilities='Both parties commit to resource sharing and regular communication',
                    status='active',
                    university_signatory='Prof. Romanus Odhiambo - Vice Chancellor',
                    partner_signatory=p_data['contact_person'],
                )
        
        # Create Collaborative Projects
        self.stdout.write('Creating collaborative projects...')
        # Fetch lecturers if they exist
        lecturers = list(Lecturer.objects.all()[:10]) if Lecturer.objects.exists() else []
        
        for partnership in partnerships[:3]:
            CollaborativeProject.objects.create(
                partnership=partnership,
                title=f'Innovation Project with {partnership.partner_name}',
                description='Joint research and development project focusing on innovative solutions',
                objectives='Develop cutting-edge solutions, train students, publish research',
                project_leader=lecturers[0] if lecturers else None,
                start_date=date(2024, 1, 1),
                end_date=date(2026, 12, 31),
                total_budget=Decimal(random.randint(2000000, 10000000)),
                university_contribution=Decimal(random.randint(500000, 3000000)),
                partner_contribution=Decimal(random.randint(500000, 3000000)),
                publications=random.randint(0, 5),
                students_trained=random.randint(10, 50),
                status='ongoing',
            )
        
        # Create Alumni Relations
        self.stdout.write('Creating alumni relations...')
        programme_list = list(programmes.values())
        for prog in programme_list[:min(5, len(programme_list))]:
            for i in range(random.randint(2, 5)):
                AlumniRelation.objects.create(
                    programme=prog,
                    alumni_name=f'Alumni {random.randint(1000, 9999)}',
                    graduation_year=random.randint(2015, 2023),
                    current_organization=random.choice(['Safaricom', 'KCB', 'Equity Bank', 'Microsoft', 'Deloitte']),
                    current_position=random.choice(['Software Engineer', 'Manager', 'Consultant', 'Analyst']),
                    engagement_type=random.choice(['mentorship', 'guest_lecture', 'sponsorship', 'internship']),
                    engagement_date=current_ay.start_date + timedelta(days=random.randint(0, 200)),
                    description='Engaged with students through mentorship and career guidance',
                    students_impacted=random.randint(10, 100),
                    coordinated_by=admin_user,
                )
        
        # ============= STRATEGIC PLANNING =============
        self.stdout.write('\nCreating strategic planning data...')
        
        # Create Strategic Goals
        goal_categories = [
            ('academic_excellence', 'Enhance Academic Excellence'),
            ('research_innovation', 'Promote Research and Innovation'),
            ('student_experience', 'Improve Student Experience'),
            ('infrastructure', 'Develop Modern Infrastructure'),
            ('partnerships', 'Strengthen Partnerships'),
        ]
        
        strategic_goals = []
        school_list = list(schools.values())
        for school in school_list[:min(3, len(school_list))]:
            for category, title in goal_categories:
                goal = StrategicGoal.objects.create(
                    school=school,
                    category=category,
                    title=f'{title} in {school.code}',
                    description=f'Strategic initiative to {title.lower()} within the school',
                    start_year=academic_years[-2],
                    target_year=academic_years[-1],
                    target_metric=random.choice(['Graduation rate', 'Research publications', 'Student satisfaction']),
                    baseline_value=Decimal(random.randint(50, 70)),
                    target_value=Decimal(random.randint(80, 95)),
                    current_value=Decimal(random.randint(60, 85)),
                    champion=admin_user,
                    status='active',
                    estimated_budget=Decimal(random.randint(1000000, 5000000)),
                )
                strategic_goals.append(goal)
        
        # Create Performance Indicators
        for goal in strategic_goals[:5]:
            for i in range(2):
                PerformanceIndicator.objects.create(
                    strategic_goal=goal,
                    indicator_code=f'KPI-{goal.id}-{i+1}',
                    indicator_name=f'Performance Indicator {i+1} for {goal.title[:30]}',
                    description='Measures progress towards strategic goal',
                    indicator_type='quantitative',
                    unit_of_measure='Percentage',
                    baseline_year=goal.start_year,
                    baseline_value=goal.baseline_value,
                    target_value=goal.target_value,
                    current_value=goal.current_value,
                    data_source='School Records',
                    collection_frequency='Quarterly',
                    responsible_person=admin_user,
                )
        
        # Create Annual Plans
        school_list = list(schools.values())
        for school in school_list[:min(3, len(school_list))]:
            plan = AnnualPlan.objects.create(
                school=school,
                academic_year=current_ay,
                title=f'{school.code} Annual Implementation Plan {current_ay.name}',
                description=f'Annual plan for achieving strategic objectives in {school.name}',
                key_priorities='Academic excellence, research output, student welfare, infrastructure',
                total_budget=Decimal(random.randint(10000000, 50000000)),
                allocated_budget=Decimal(random.randint(8000000, 40000000)),
                status='active',
                prepared_by=admin_user,
                approved_by=admin_user,
                approval_date=current_ay.start_date,
            )
            
            # Create Annual Plan Activities
            for i in range(5):
                AnnualPlanActivity.objects.create(
                    annual_plan=plan,
                    strategic_goal=strategic_goals[0] if strategic_goals else None,
                    activity_code=f'ACT-{plan.id}-{i+1:02d}',
                    activity_name=f'Activity {i+1}: {random.choice(["Curriculum Review", "Faculty Training", "Infrastructure Upgrade", "Research Workshop"])}',
                    description='Detailed description of the activity and expected outcomes',
                    start_date=current_ay.start_date + timedelta(days=i*60),
                    end_date=current_ay.start_date + timedelta(days=(i+1)*60),
                    budget_allocated=Decimal(random.randint(500000, 2000000)),
                    budget_utilized=Decimal(random.randint(200000, 1500000)),
                    responsible_person=admin_user,
                    status=random.choice(['in_progress', 'completed', 'not_started']),
                    completion_percentage=Decimal(random.randint(0, 100)),
                    expected_output='Detailed expected outcomes',
                )
        
        # Create Progress Reports
        for school in list(schools.values())[:2]:
            ProgressReport.objects.create(
                school=school,
                academic_year=current_ay,
                report_type='quarterly',
                title=f'Q1 Progress Report - {school.code}',
                reporting_period_start=current_ay.start_date,
                reporting_period_end=current_ay.start_date + timedelta(days=90),
                executive_summary='Overall progress has been satisfactory with most targets on track',
                achievements='Key milestones achieved include curriculum review and staff training',
                challenges='Budget constraints and delayed procurement processes',
                recommendations='Need for improved coordination and timely resource allocation',
                overall_progress_percentage=Decimal('67.5'),
                budget_utilization_percentage=Decimal('58.3'),
                status='published',
                prepared_by=admin_user,
                reviewed_by=admin_user,
                published_by=admin_user,
                published_date=timezone.now() - timedelta(days=30),
            )
        
        # Create Dean Approvals
        self.stdout.write('Creating dean approval requests...')
        for dept in list(departments.values())[:5]:
            for i in range(random.randint(1, 3)):
                DeanApproval.objects.create(
                    department=dept,
                    approval_type=random.choice(['budget', 'procurement', 'recruitment']),
                    title=f'Approval Request: {random.choice(["Equipment Purchase", "Staff Recruitment", "Budget Reallocation"])}',
                    description='Detailed justification for the approval request',
                    priority=random.choice(['medium', 'high', 'urgent']),
                    requested_by=admin_user,
                    status=random.choice(['pending', 'approved', 'rejected']),
                )
        
        # ============= STUDENT SUPPORT =============
        self.stdout.write('\nCreating student support data...')
        
        # Fetch students if they exist
        students = list(Student.objects.all()[:20]) if Student.objects.exists() else []
        
        if students and lecturers:
            # Create Advising Notes
            for student in students[:10]:
                for i in range(random.randint(1, 3)):
                    AdvisingNote.objects.create(
                        student=student,
                        lecturer=admin_user,
                        note_type=random.choice(['academic', 'performance', 'attendance']),
                        subject=f'Academic Advising Session {i+1}',
                        note='Discussed academic progress and course selection for next semester',
                        action_required=random.choice([True, False]),
                        is_confidential=False,
                        is_resolved=random.choice([True, False]),
                    )
            
            # Create Student Special Needs
            for student in students[:5]:
                StudentSpecialNeed.objects.create(
                    student=student,
                    need_type=random.choice(['physical', 'visual', 'learning']),
                    severity='moderate',
                    description='Requires special accommodation for examinations',
                    accommodations_required='Extra time, accessible venue, assistive technology',
                    reported_by=admin_user,
                    reported_date=current_ay.start_date,
                    is_active=True,
                    next_review_date=current_ay.end_date,
                )
        
        # ============= GOVERNANCE =============
        self.stdout.write('\nCreating governance data...')
        
        # Create University Council Members
        council_members = [
            {'name': 'Prof. Isaac Macharia', 'member_type': 'chairman', 'organization': 'MUT', 'position': 'Council Chairman'},
            {'name': 'Dr. Grace Wambui', 'member_type': 'vice_chairman', 'organization': 'Industry', 'position': 'Vice Chairman'},
            {'name': 'Prof. Romanus Odhiambo', 'member_type': 'ex_officio', 'organization': 'MUT', 'position': 'Vice Chancellor'},
            {'name': 'Mr. James Kariuki', 'member_type': 'member', 'organization': 'Alumni Association', 'position': 'Council Member'},
            {'name': 'Ms. Anne Muthoni', 'member_type': 'member', 'organization': 'Ministry of Education', 'position': 'Council Member'},
        ]
        
        for member_data in council_members:
            UniversityCouncil.objects.create(
                **member_data,
                appointment_date=date(2020, 1, 1),
                term_end_date=date(2025, 12, 31),
                email=f'{member_data["name"].replace(" ", ".").lower()}@mut.ac.ke',
                phone_number=f'+254 7{random.randint(10000000, 99999999)}',
                is_active=True,
            )
        
        # Create Senate Sessions
        for i in range(3):
            SenateSession.objects.create(
                session_number=f'SEN-{current_ay.name.replace("/", "-")}-{i+1:02d}',
                academic_year=current_ay,
                session_date=current_ay.start_date + timedelta(days=i*90),
                venue='Senate Chambers, Administration Block',
                agenda='Review of academic programs, examination results, quality assurance',
                minutes='Detailed minutes of senate deliberations and decisions',
                decisions='Approved new programs, reviewed examination irregularities',
                status='completed',
                chaired_by=admin_user,
            )
        
        # Create Management Board Meetings
        for i in range(4):
            ManagementBoardMeeting.objects.create(
                meeting_number=f'MB-{current_ay.name.replace("/", "-")}-{i+1:02d}',
                academic_year=current_ay,
                meeting_date=current_ay.start_date + timedelta(days=i*60),
                agenda='Financial reports, infrastructure projects, staff matters',
                decisions='Approved budget allocations and infrastructure projects',
                action_items='Follow up on procurement processes and staff recruitment',
            )
        
        # Create International Rankings
        ranking_data = [
            {'ranking_type': 'webometrics', 'year': 2024, 'overall_rank': 15, 'national_rank': 8, 'regional_rank': 45},
            {'ranking_type': 'webometrics', 'year': 2025, 'overall_rank': 12, 'national_rank': 6, 'regional_rank': 38},
            {'ranking_type': 'times', 'year': 2025, 'overall_rank': 1200, 'score': Decimal('45.2')},
        ]
        
        for rank_data in ranking_data:
            InternationalRanking.objects.create(
                **rank_data,
                category_scores={'research': 40, 'teaching': 50, 'citations': 35},
                analysis='Showing steady improvement in research output and international visibility',
            )
        
        # Create Capital Projects
        projects_data = [
            {
                'project_number': 'CAP-2024-001',
                'project_name': 'New SCIT Building',
                'location': 'Main Campus',
                'total_budget': Decimal('500000000'),
                'funding_source': 'Government Grant',
                'status': 'construction',
            },
            {
                'project_number': 'CAP-2024-002',
                'project_name': 'Library Expansion',
                'location': 'Central Library',
                'total_budget': Decimal('200000000'),
                'funding_source': 'Development Budget',
                'status': 'design',
            },
            {
                'project_number': 'CAP-2023-005',
                'project_name': 'Student Hostels Block C',
                'location': 'Student Residences',
                'total_budget': Decimal('350000000'),
                'funding_source': 'University Revenue',
                'status': 'completed',
            },
        ]
        
        for proj_data in projects_data:
            CapitalProject.objects.create(
                **proj_data,
                description=f'Construction/renovation project: {proj_data["project_name"]}',
                amount_spent=proj_data['total_budget'] * Decimal('0.6'),
                start_date=date(2023, 7, 1),
                expected_completion=date(2025, 12, 31),
                completion_percentage=Decimal(random.randint(30, 90)),
                project_manager=admin_user,
            )
        
        # Create Risk Register
        risks_data = [
            {
                'risk_category': 'financial',
                'risk_title': 'Budget Deficit',
                'likelihood': 'possible',
                'impact': 'major',
            },
            {
                'risk_category': 'operational',
                'risk_title': 'Staff Shortage',
                'likelihood': 'likely',
                'impact': 'moderate',
            },
            {
                'risk_category': 'compliance',
                'risk_title': 'Regulatory Changes',
                'likelihood': 'unlikely',
                'impact': 'minor',
            },
            {
                'risk_category': 'reputational',
                'risk_title': 'Quality Assurance Issues',
                'likelihood': 'possible',
                'impact': 'major',
            },
        ]
        
        for i, risk_data in enumerate(risks_data):
            # Calculate risk score (simple 1-5 scale)
            likelihood_score = {'rare': 1, 'unlikely': 2, 'possible': 3, 'likely': 4, 'almost_certain': 5}
            impact_score = {'insignificant': 1, 'minor': 2, 'moderate': 3, 'major': 4, 'catastrophic': 5}
            
            RiskRegister.objects.create(
                risk_number=f'RISK-{2025}-{i+1:03d}',
                **risk_data,
                risk_description=f'Detailed description of {risk_data["risk_title"]}',
                risk_score=likelihood_score[risk_data['likelihood']] * impact_score[risk_data['impact']],
                mitigation_strategy='Comprehensive mitigation plan with clear timelines and responsibilities',
                risk_owner=admin_user,
                review_date=date(2025, 12, 31),
                status='active',
            )
        
        self.stdout.write(self.style.SUCCESS('\n✅ MUT data seeding completed successfully!'))
        self.stdout.write(self.style.SUCCESS(f'   - Used {School.objects.count()} existing schools'))
        self.stdout.write(self.style.SUCCESS(f'   - Used {Department.objects.count()} existing departments'))
        self.stdout.write(self.style.SUCCESS(f'   - Used {Programme.objects.count()} existing programmes'))
        self.stdout.write(self.style.SUCCESS(f'   - Created {SchoolBudget.objects.count()} school budgets'))
        self.stdout.write(self.style.SUCCESS(f'   - Created {BudgetAllocation.objects.count()} budget allocations'))
        self.stdout.write(self.style.SUCCESS(f'   - Created {ExpenditureTracking.objects.count()} expenditure records'))
        self.stdout.write(self.style.SUCCESS(f'   - Created {RevenueSource.objects.count()} revenue sources'))
        self.stdout.write(self.style.SUCCESS(f'   - Created {Partnership.objects.count()} partnerships'))
        self.stdout.write(self.style.SUCCESS(f'   - Created {MOU.objects.count()} MOUs'))
        self.stdout.write(self.style.SUCCESS(f'   - Created {CollaborativeProject.objects.count()} collaborative projects'))
        self.stdout.write(self.style.SUCCESS(f'   - Created {AlumniRelation.objects.count()} alumni relations'))
        self.stdout.write(self.style.SUCCESS(f'   - Created {StrategicGoal.objects.count()} strategic goals'))
        self.stdout.write(self.style.SUCCESS(f'   - Created {PerformanceIndicator.objects.count()} performance indicators'))
        self.stdout.write(self.style.SUCCESS(f'   - Created {AnnualPlan.objects.count()} annual plans'))
        self.stdout.write(self.style.SUCCESS(f'   - Created {AnnualPlanActivity.objects.count()} plan activities'))
        self.stdout.write(self.style.SUCCESS(f'   - Created {ProgressReport.objects.count()} progress reports'))
        self.stdout.write(self.style.SUCCESS(f'   - Created {DeanApproval.objects.count()} dean approvals'))
        self.stdout.write(self.style.SUCCESS(f'   - Created {UniversityCouncil.objects.count()} council members'))
        self.stdout.write(self.style.SUCCESS(f'   - Created {SenateSession.objects.count()} senate sessions'))
        self.stdout.write(self.style.SUCCESS(f'   - Created {ManagementBoardMeeting.objects.count()} management board meetings'))
        self.stdout.write(self.style.SUCCESS(f'   - Created {InternationalRanking.objects.count()} international rankings'))
        self.stdout.write(self.style.SUCCESS(f'   - Created {CapitalProject.objects.count()} capital projects'))
        self.stdout.write(self.style.SUCCESS(f'   - Created {RiskRegister.objects.count()} risk items'))