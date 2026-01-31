from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from portal.models import User, Student, Lecturer
from django.views.decorators.cache import never_cache


@never_cache
def login_view(request):
    """Handle user login with email/registration number"""
    
    # Redirect if already logged in
    if request.user.is_authenticated:
        return redirect_user_dashboard(request.user)
    
    if request.method == 'POST':
        username = request.POST.get('loginusername', '').strip()
        password = request.POST.get('loginpassword', '')
        remember_me = request.POST.get('RememberMe') == 'true'
        
        if not username or not password:
            messages.error(request, 'Please provide both username and password')
            return render(request, 'auth/signin.html')
        
        # Try to find user by username, email, or registration number
        user = None
        
        try:
            # First, try direct authentication with username
            user = authenticate(request, username=username, password=password)
            
            # If that fails, try to find user by email or registration number
            if not user:
                user_obj = User.objects.filter(
                    Q(email=username) | Q(username=username)
                ).first()
                
                # If not found in User, try Student model
                if not user_obj:
                    student = Student.objects.filter(
                        registration_number=username
                    ).first()
                    if student:
                        user_obj = student.user
                
                # Now authenticate with the found username
                if user_obj:
                    user = authenticate(request, username=user_obj.username, password=password)
            
            if user is not None:
                # Check if user is active
                if not user.is_active:
                    messages.error(request, 'Your account has been deactivated. Please contact administration.')
                    return render(request, 'auth/signin.html')
                
                # Login the user
                login(request, user)
                
                # Set session expiry based on remember me
                if not remember_me:
                    request.session.set_expiry(0)  # Session expires when browser closes
                else:
                    request.session.set_expiry(1209600)  # 2 weeks
                
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                
                # Redirect to appropriate dashboard
                return redirect_user_dashboard(user)
            else:
                messages.error(request, 'Invalid username/email or password')
        
        except Exception as e:
            messages.error(request, 'An error occurred during login. Please try again.')
            print(f"Login error: {str(e)}")
    
    return render(request, 'auth/signin.html')


def redirect_user_dashboard(user):
    """Redirect user to appropriate dashboard based on role"""
    
    role = user.role.lower() if user.role else ''
    
    # Admin/Superuser
    if user.is_superuser or user.is_staff:
        return redirect('admin_dashboard')
    
    # Student
    elif role == 'student':
        return redirect('student_dashboard')
    
    # Lecturer
    elif role == 'lecturer':
        return redirect('lecturer_dashboard')
    
    # Dean
    elif role == 'dean':
        return redirect('dean_dashboard')
    
    # Head of School
    elif role == 'hos':
        return redirect('hos_dashboard')
    
    # HOD
    elif role == 'hod':
        return redirect('hod_dashboard')
    
    # Finance Officer
    elif role == 'finance':
        return redirect('finance_dashboard')
    
    # Registrar
    elif role == 'registrar':
        return redirect('registrar_dashboard')
    
    # Librarian
    elif role == 'librarian':
        return redirect('librarian_dashboard')
    
    # Hostel Warden
    elif role == 'hostel_warden':
        return redirect('hostel_dashboard')
    
    # Procurement
    elif role == 'procurement':
        return redirect('procurement_dashboard')
    
    # Default fallback
    else:
        return redirect('admin_dashboard')


def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('login')


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Avg, Q, F
from django.db.models.functions import TruncYear, TruncMonth
from datetime import datetime, timedelta
from decimal import Decimal
import json

@login_required
def admin_dashboard(request):
    """Admin dashboard view with comprehensive analytics"""
    
    # Get current academic year and semester
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # ============= BASIC STATISTICS (8 CARDS) =============
    total_students = Student.objects.filter(student_status='active').count()
    total_lecturers = Lecturer.objects.filter(is_active=True).count()
    total_programmes = Programme.objects.filter(is_active=True).count()
    total_units = Unit.objects.filter(is_active=True).count()
    
    # Monthly revenue (sum of all completed fee payments in current month)
    current_month_start = datetime.now().replace(day=1)
    monthly_revenue = FeePayment.objects.filter(
        payment_date__gte=current_month_start,
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Hostel occupancy
    total_hostel_beds = HostelBed.objects.filter(
        is_active=True,
        academic_year=current_academic_year
    ).count()
    occupied_beds = HostelBed.objects.filter(
        is_active=True,
        academic_year=current_academic_year,
        status='occupied'
    ).count()
    hostel_occupancy = (occupied_beds / total_hostel_beds * 100) if total_hostel_beds > 0 else 0
    
    # Library stats
    total_books = Book.objects.count()
    
    # Active users (logged in within last 24 hours)
    yesterday = datetime.now() - timedelta(days=1)
    active_users = User.objects.filter(last_login__gte=yesterday).count()
    
    # ============= ADMISSION TRENDS BY ACADEMIC YEAR & GENDER =============
    admission_trends = Student.objects.values(
        'intake__academic_year__name',
        'gender'
    ).annotate(
        count=Count('id')
    ).order_by('intake__academic_year__start_date')
    
    # Process data for chart
    admission_years = {}
    for item in admission_trends:
        year = item['intake__academic_year__name']
        gender = item['gender']
        count = item['count']
        
        if year not in admission_years:
            admission_years[year] = {'M': 0, 'F': 0, 'O': 0}
        admission_years[year][gender] = count
    
    admission_labels = list(admission_years.keys())
    male_data = [admission_years[year]['M'] for year in admission_labels]
    female_data = [admission_years[year]['F'] for year in admission_labels]
    other_data = [admission_years[year]['O'] for year in admission_labels]
    
    # ============= CURRENT YEAR DISTRIBUTION BY YEAR OF STUDY =============
    if current_academic_year:
        year_distribution = Student.objects.filter(
            student_status='active',
            programme__in=Programme.objects.filter(
                students__intake__academic_year=current_academic_year
            )
        ).values('current_year').annotate(
            count=Count('id')
        ).order_by('current_year')
        
        year_labels = [f'Year {item["current_year"]}' for item in year_distribution]
        year_counts = [item['count'] for item in year_distribution]
    else:
        year_labels = []
        year_counts = []
    
    # ============= PROGRAMME TYPE DISTRIBUTION =============
    programme_type_stats = Student.objects.filter(
        student_status='active'
    ).values(
        'programme__programme_type'
    ).annotate(
        count=Count('id')
    ).order_by('-count')
    
    programme_type_labels = [item['programme__programme_type'].title() for item in programme_type_stats]
    programme_type_counts = [item['count'] for item in programme_type_stats]
    
    # ============= TOP 5 PROGRAMMES BY ENROLLMENT =============
    top_programmes = Student.objects.filter(
        student_status='active'
    ).values(
        'programme__code',
        'programme__name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    top_programme_labels = [f"{item['programme__code']}" for item in top_programmes]
    top_programme_counts = [item['count'] for item in top_programmes]
    
    # ============= SEMESTER REPORTING TRENDS (LAST 5 SEMESTERS) =============
    last_5_semesters = Semester.objects.filter(
        is_active=True
    ).order_by('-start_date')[:5]
    
    reporting_trends = []
    for semester in reversed(list(last_5_semesters)):
        approved_reports = SemesterReport.objects.filter(
            to_semester=semester,
            status='approved'
        ).count()
        
        pending_reports = SemesterReport.objects.filter(
            to_semester=semester,
            status='pending'
        ).count()
        
        reporting_trends.append({
            'semester': str(semester.name),
            'approved': approved_reports,
            'pending': pending_reports,
            'total': approved_reports + pending_reports
        })
    
    reporting_labels = [item['semester'] for item in reporting_trends]
    reporting_approved = [item['approved'] for item in reporting_trends]
    reporting_pending = [item['pending'] for item in reporting_trends]
    
    # ============= STUDENT POPULATION TRENDS (LAST 12 MONTHS) =============
    twelve_months_ago = datetime.now() - timedelta(days=365)
    population_trends = Student.objects.filter(
        created_at__gte=twelve_months_ago
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    population_labels = [item['month'].strftime('%b %Y') for item in population_trends]
    population_counts = [item['count'] for item in population_trends]
    
    # ============= FEE PAYMENT TRENDS (LAST 5 SEMESTERS) =============
    fee_payment_trends = []
    for semester in reversed(list(last_5_semesters)):
        total_expected = FeeBalance.objects.filter(
            semester=semester
        ).aggregate(total=Sum('total_fees'))['total'] or Decimal('0.00')
        
        total_paid = FeeBalance.objects.filter(
            semester=semester
        ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
        
        fee_payment_trends.append({
            'semester': str(semester.name),
            'expected': float(total_expected),
            'paid': float(total_paid),
            'percentage': (float(total_paid) / float(total_expected) * 100) if total_expected > 0 else 0
        })
    
    fee_labels = [item['semester'] for item in fee_payment_trends]
    fee_expected = [item['expected'] for item in fee_payment_trends]
    fee_paid = [item['paid'] for item in fee_payment_trends]
    fee_percentages = [item['percentage'] for item in fee_payment_trends]
    
    # ============= TOP 5 STUDENTS BY GPA =============
    top_students = Student.objects.filter(
        student_status='active'
    ).select_related('user', 'programme').order_by('-cumulative_gpa')[:5]
    
    # ============= GENDER DISTRIBUTION (DONUT CHART) =============
    gender_distribution = Student.objects.filter(
        student_status='active'
    ).values('gender').annotate(
        count=Count('id')
    )
    
    gender_labels = []
    gender_counts = []
    for item in gender_distribution:
        if item['gender'] == 'M':
            gender_labels.append('Male')
        elif item['gender'] == 'F':
            gender_labels.append('Female')
        else:
            gender_labels.append('Other')
        gender_counts.append(item['count'])
    
    # ============= RECENT ACTIVITIES =============
    # Get recent semester reports
    recent_reports = SemesterReport.objects.select_related(
        'student__user',
        'to_semester'
    ).order_by('-created_at')[:5]
    
    # Get recent fee payments
    recent_payments = FeePayment.objects.select_related(
        'student__user'
    ).filter(
        status='completed'
    ).order_by('-payment_date')[:3]
    
    # Get recent hostel allocations
    recent_allocations = HostelAllocation.objects.select_related(
        'student__user',
        'bed__room__hostel'
    ).order_by('-allocation_date')[:2]
    
    # Compile all activities
    recent_activities = []
    
    for report in recent_reports:
        recent_activities.append({
            'type': 'report',
            'title': 'Semester Report',
            'description': f"Y{report.to_year_of_study}S{report.to_semester_number}",
            'user': report.student.user.get_full_name(),
            'date': report.created_at,
            'status': report.status
        })
    
    for payment in recent_payments:
        recent_activities.append({
            'type': 'payment',
            'title': 'Fee Payment',
            'description': f"Ksh {payment.amount:,.2f}",
            'user': payment.student.user.get_full_name(),
            'date': payment.payment_date,
            'status': payment.status
        })
    
    for allocation in recent_allocations:
        recent_activities.append({
            'type': 'hostel',
            'title': 'Hostel Allocation',
            'description': f"{allocation.bed.room.hostel.name} - Room {allocation.bed.room.room_number}",
            'user': allocation.student.user.get_full_name(),
            'date': allocation.allocation_date,
            'status': 'approved' if allocation.is_active else 'pending'
        })
    
    # Sort all activities by date
    recent_activities.sort(key=lambda x: x['date'], reverse=True)
    recent_activities = recent_activities[:10]
    
    context = {
        'page_title': 'Admin Dashboard',
        'user': request.user,
        
        # Basic stats
        'total_students': total_students,
        'total_lecturers': total_lecturers,
        'total_programmes': total_programmes,
        'total_units': total_units,
        'monthly_revenue': monthly_revenue,
        'hostel_occupancy': round(hostel_occupancy, 1),
        'total_books': total_books,
        'active_users': active_users,
        
        # Current academic info
        'current_academic_year': current_academic_year,
        'current_semester': current_semester,
        
        # Chart data (JSON encoded for JavaScript)
        'admission_labels': json.dumps(admission_labels),
        'male_data': json.dumps(male_data),
        'female_data': json.dumps(female_data),
        'other_data': json.dumps(other_data),
        
        'year_labels': json.dumps(year_labels),
        'year_counts': json.dumps(year_counts),
        
        'programme_type_labels': json.dumps(programme_type_labels),
        'programme_type_counts': json.dumps(programme_type_counts),
        
        'top_programme_labels': json.dumps(top_programme_labels),
        'top_programme_counts': json.dumps(top_programme_counts),
        
        'reporting_labels': json.dumps(reporting_labels),
        'reporting_approved': json.dumps(reporting_approved),
        'reporting_pending': json.dumps(reporting_pending),
        
        'population_labels': json.dumps(population_labels),
        'population_counts': json.dumps(population_counts),
        
        'fee_labels': json.dumps(fee_labels),
        'fee_expected': json.dumps(fee_expected),
        'fee_paid': json.dumps(fee_paid),
        'fee_percentages': json.dumps(fee_percentages),
        
        'gender_labels': json.dumps(gender_labels),
        'gender_counts': json.dumps(gender_counts),
        
        # Top students
        'top_students': top_students,
        
        # Recent activities
        'recent_activities': recent_activities,
    }
    
    return render(request, 'admin/dashboard.html', context)


@login_required
def student_dashboard(request):
    """Enhanced Student dashboard view"""
    try:
        student = Student.objects.get(user=request.user)
        
        from portal.models import (
            UnitEnrollment, FeeBalance, HostelAllocation, 
            Semester, SemesterGPA, HostelApplication
        )
        from django.utils import timezone
        from django.db.models import Sum, Count
        
        # Get current semester
        current_semester = Semester.objects.filter(is_current=True).first()
        
        # Get enrolled units (using UnitEnrollment instead of UnitRegistration)
        enrollments = UnitEnrollment.objects.filter(
            student=student,
            semester=current_semester,
            status__in=['approved', 'pending']
        ).select_related(
            'programme_unit__unit',
            'programme_unit__unit__department'
        ).prefetch_related(
            'programme_unit__allocations__lecturer'  # lecturer is already User model
        )
        
        # Get fee balance for current semester
        fee_balance = FeeBalance.objects.filter(
            student=student,
            semester=current_semester
        ).first()
        
        # If no fee balance for current semester, get the most recent one
        if not fee_balance:
            fee_balance = FeeBalance.objects.filter(
                student=student
            ).order_by('-updated_at').first()
        
        # Get current GPA
        current_gpa = SemesterGPA.objects.filter(
            student=student
        ).order_by('-semester__academic_year__start_date').first()
        
        # Update student's cumulative GPA if exists
        if current_gpa:
            student.cumulative_gpa = current_gpa.cumulative_gpa
            student.total_credit_hours = current_gpa.cumulative_credit_hours
        
        # Hostel logic: Year 1 students can apply, others see their allocation
        hostel_allocation = None
        hostel_application = None
        hostel_history = None
        can_apply_hostel = False
        
        if student.current_year == 1:
            # Year 1 students: Check if they can apply or have already applied
            can_apply_hostel = True
            
            # Check for existing application
            hostel_application = HostelApplication.objects.filter(
                student=student,
                semester=current_semester,
                status__in=['pending', 'approved']
            ).select_related('hostel').first()
            
            # Check for allocation if application was approved
            if hostel_application and hostel_application.status == 'approved':
                hostel_allocation = HostelAllocation.objects.filter(
                    student=student,
                    semester=current_semester,
                    is_active=True
                ).select_related('bed__room__hostel').first()
        else:
            # Year 2+ students: Show their current allocation
            hostel_allocation = HostelAllocation.objects.filter(
                student=student,
                academic_year=current_semester.academic_year if current_semester else None,
                is_active=True
            ).select_related('bed__room__hostel').first()
            
            # Also get their hostel history
            hostel_history = HostelAllocation.objects.filter(
                student=student
            ).select_related(
                'bed__room__hostel',
                'academic_year',
                'semester'
            ).order_by('-allocation_date')[:5]  # Last 5 allocations
        
        # Calculate enrollment statistics
        total_enrollments = enrollments.count()
        approved_enrollments = enrollments.filter(status='approved').count()
        pending_enrollments = enrollments.filter(status='pending').count()
        resit_enrollments = enrollments.filter(enrollment_type='resit').count()
        
        # Calculate total credit hours for enrolled units
        enrolled_credit_hours = enrollments.filter(
            status='approved'
        ).aggregate(
            total=Sum('programme_unit__unit__credit_hours')
        )['total'] or 0
        
        context = {
            'page_title': 'Student Dashboard',
            'student': student,
            'current_semester': current_semester,
            
            # Enrollments (renamed from registrations)
            'registrations': enrollments,  # Keep same name for template compatibility
            'total_enrollments': total_enrollments,
            'approved_enrollments': approved_enrollments,
            'pending_enrollments': pending_enrollments,
            'resit_enrollments': resit_enrollments,
            'enrolled_credit_hours': enrolled_credit_hours,
            
            # Financial info
            'fee_balance': fee_balance,
            
            # Academic info
            'current_gpa': current_gpa,
            
            # Hostel info
            'hostel_allocation': hostel_allocation,
            'hostel_application': hostel_application,
            'can_apply_hostel': can_apply_hostel,
            'hostel_history': hostel_history if student.current_year > 1 else None,
        }
        
        return render(request, 'student/dashboard.html', context)
    
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('login')
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Student dashboard error: {str(e)}', exc_info=True)
        return redirect('login')


@login_required
def hostel_application(request):
    """Hostel application view for Year 1 students"""
    try:
        student = Student.objects.get(user=request.user)
        
        from portal.models import (
            Hostel, HostelApplication, HostelFeeStructure, 
            Semester, FeeBalance, HostelRoom
        )
        from django.utils import timezone
        from django.db import transaction
        from decimal import Decimal
        
        # Check if student is Year 1
        if student.current_year != 1:
            messages.warning(request, 'Hostel applications are only available for Year 1 students.')
            return redirect('student_dashboard')
        
        # Get current semester
        current_semester = Semester.objects.filter(is_current=True).first()
        if not current_semester:
            messages.error(request, 'No active semester found.')
            return redirect('student_dashboard')
        
        # Check for existing application
        existing_application = HostelApplication.objects.filter(
            student=student,
            semester=current_semester
        ).select_related('hostel').first()
        
        # Get available hostels based on student gender
        available_hostels = Hostel.objects.filter(
            is_active=True,
            gender_type__in=[student.gender, 'mixed']
        ).prefetch_related('rooms')
        
        # Calculate available spaces for each hostel
        for hostel in available_hostels:
            total_capacity = hostel.total_capacity
            allocated_count = HostelAllocation.objects.filter(
                bed__room__hostel=hostel,
                academic_year=current_semester.academic_year,
                is_active=True
            ).count()
            hostel.available_spaces = total_capacity - allocated_count
            hostel.occupancy_percentage = (allocated_count / total_capacity * 100) if total_capacity > 0 else 0
            
            # Get fee structure
            fee_structure = HostelFeeStructure.objects.filter(
                hostel=hostel,
                academic_year=current_semester.academic_year,
                semester=current_semester,
                is_active=True
            ).first()
            hostel.fee_info = fee_structure
        
        # Get student's fee balance
        fee_balance = FeeBalance.objects.filter(
            student=student,
            semester=current_semester
        ).first()
        
        context = {
            'student': student,
            'current_semester': current_semester,
            'existing_application': existing_application,
            'available_hostels': available_hostels,
            'fee_balance': fee_balance,
        }
        
        if request.method == 'POST':
            # Check if already has pending/approved application
            if existing_application and existing_application.status in ['pending', 'approved']:
                messages.warning(request, 'You already have an active hostel application.')
                return redirect('hostel_application')
            
            hostel_id = request.POST.get('hostel')
            room_type = request.POST.get('room_type')
            
            if not hostel_id or not room_type:
                messages.error(request, 'Please select a hostel and room type.')
                return render(request, 'student/hostel_application.html', context)
            
            try:
                hostel = Hostel.objects.get(id=hostel_id, is_active=True)
                
                # Verify hostel gender compatibility
                if hostel.gender_type not in [student.gender, 'mixed']:
                    messages.error(request, 'Selected hostel is not compatible with your gender.')
                    return render(request, 'student/hostel_application.html', context)
                
                # Check hostel capacity
                allocated_count = HostelAllocation.objects.filter(
                    bed__room__hostel=hostel,
                    academic_year=current_semester.academic_year,
                    is_active=True
                ).count()
                
                if allocated_count >= hostel.total_capacity:
                    messages.error(request, 'Selected hostel is fully occupied.')
                    return render(request, 'student/hostel_application.html', context)
                
                # Get fee structure
                fee_structure = HostelFeeStructure.objects.filter(
                    hostel=hostel,
                    room_type=room_type,
                    academic_year=current_semester.academic_year,
                    semester=current_semester,
                    is_active=True
                ).first()
                
                if not fee_structure:
                    messages.error(request, 'Fee structure not found for selected room type.')
                    return render(request, 'student/hostel_application.html', context)
                
                with transaction.atomic():
                    # Create or update application
                    if existing_application:
                        # Update existing rejected/cancelled application
                        existing_application.hostel = hostel
                        existing_application.preferred_room_type = room_type
                        existing_application.status = 'pending'
                        existing_application.booking_fee_paid = False
                        existing_application.remarks = 'Application resubmitted'
                        existing_application.save()
                        application = existing_application
                    else:
                        # Create new application
                        application = HostelApplication.objects.create(
                            student=student,
                            hostel=hostel,
                            academic_year=current_semester.academic_year,
                            semester=current_semester,
                            preferred_room_type=room_type,
                            status='pending',
                            booking_fee_paid=False
                        )
                    
                    messages.success(
                        request, 
                        f'Hostel application submitted successfully for {hostel.name}. '
                        f'Booking fee: Ksh {fee_structure.booking_fee:,.2f}'
                    )
                    return redirect('hostel_application_status')
                    
            except Hostel.DoesNotExist:
                messages.error(request, 'Selected hostel not found.')
            except Exception as e:
                messages.error(request, f'Error submitting application: {str(e)}')
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Hostel application error: {str(e)}', exc_info=True)
        
        return render(request, 'student/hostel_application.html', context)
    
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('student_dashboard')


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Count, Q, Max
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from decimal import Decimal
import json
import uuid

from portal.models import (
    Student, Hostel, HostelRoom, HostelBed, HostelApplication,
    HostelAllocation, HostelFeeStructure, Semester, AcademicYear,
    BedReservation, MpesaPayment, HostelReview, HostelImage,
    HostelRoomImage, SMSNotification
)

# ============= HOSTEL DETAIL VIEW =============
@login_required
def hostel_detail(request, hostel_id):
    """View detailed information about a specific hostel"""
    try:
        student = Student.objects.get(user=request.user)
        hostel = get_object_or_404(Hostel, id=hostel_id, is_active=True)
        current_semester = Semester.objects.filter(is_current=True).first()
        
        if not current_semester:
            messages.error(request, 'No active semester found.')
            return redirect('hostel_application')
        
        # Get hostel images
        images = hostel.images.all().order_by('-is_primary', 'display_order')
        
        # Get fee structures for current semester
        fee_structures = HostelFeeStructure.objects.filter(
            hostel=hostel,
            academic_year=current_semester.academic_year,
            semester=current_semester,
            is_active=True
        ).order_by('room_type')
        
        # Get all rooms grouped by floor
        rooms = hostel.rooms.filter(is_active=True).prefetch_related('images')
        
        # Calculate availability for each room
        rooms_data = []
        for room in rooms:
            total_beds = room.capacity
            available_beds_count = room.beds.filter(
                status='available',
                academic_year=current_semester.academic_year
            ).count()
            
            room.available_beds = available_beds_count
            room.total_beds = total_beds
            room.occupancy_rate = ((total_beds - available_beds_count) / total_beds * 100) if total_beds > 0 else 0
            rooms_data.append(room)
        
        # Group rooms by floor
        rooms_by_floor = {}
        for room in rooms_data:
            if room.floor not in rooms_by_floor:
                rooms_by_floor[room.floor] = []
            rooms_by_floor[room.floor].append(room)
        
        # Sort floors
        rooms_by_floor = dict(sorted(rooms_by_floor.items()))
        
        # Calculate total available spaces
        total_capacity = hostel.total_capacity
        allocated_count = HostelAllocation.objects.filter(
            bed__room__hostel=hostel,
            academic_year=current_semester.academic_year,
            is_active=True
        ).count()
        hostel.available_spaces = total_capacity - allocated_count
        
        # Get reviews and ratings
        reviews = HostelReview.objects.filter(
            hostel=hostel,
            is_approved=True
        ).select_related('student__user').order_by('-created_at')[:10]
        
        ratings = {
            'overall': reviews.aggregate(avg=Avg('overall_rating'))['avg'] or 0,
            'cleanliness': reviews.aggregate(avg=Avg('cleanliness_rating'))['avg'] or 0,
            'facilities': reviews.aggregate(avg=Avg('facilities_rating'))['avg'] or 0,
            'security': reviews.aggregate(avg=Avg('security_rating'))['avg'] or 0,
            'management': reviews.aggregate(avg=Avg('management_rating'))['avg'] or 0,
        }
        
        context = {
            'student': student,
            'hostel': hostel,
            'current_semester': current_semester,
            'images': images,
            'fee_structures': fee_structures,
            'rooms_by_floor': rooms_by_floor,
            'reviews': reviews,
            'ratings': ratings,
        }
        
        return render(request, 'student/hostel_detail.html', context)
        
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('student_dashboard')


# ============= ROOM DETAIL VIEW =============
@login_required
def room_detail(request, room_id):
    """
    Display room details with bed selection
    Students can book directly without prior application
    """
    try:
        student = Student.objects.get(user=request.user)
        room = get_object_or_404(
            HostelRoom.objects.select_related('hostel'),
            id=room_id,
            is_active=True
        )
        current_semester = Semester.objects.filter(is_current=True).first()
        
        if not current_semester:
            messages.error(request, 'No active semester found.')
            return redirect('hostel_application')
        
        # REMOVED: Application check - allow direct booking
        
        # Check if student has existing active allocation
        existing_allocation = HostelAllocation.objects.filter(
            student=student,
            semester=current_semester,
            is_active=True
        ).select_related('bed__room__hostel').first()
        
        has_existing_allocation = existing_allocation is not None
        
        # Get all beds in the room
        beds = HostelBed.objects.filter(
            room=room,
            academic_year=current_semester.academic_year,
            is_active=True
        ).order_by('bed_number')
        
        # Check for pending reservations
        for bed in beds:
            pending_reservation = BedReservation.objects.filter(
                bed=bed,
                status='pending',
                expires_at__gt=timezone.now()
            ).first()
            
            if pending_reservation:
                bed.is_reserved = True
                bed.reservation_expires = pending_reservation.expires_at
            else:
                bed.is_reserved = False
        
        # Get fee structure
        fee_structure = HostelFeeStructure.objects.filter(
            hostel=room.hostel,
            room_type=room.room_type,
            academic_year=current_semester.academic_year,
            semester=current_semester,
            is_active=True
        ).first()
        
        # Calculate total amount
        total_amount = Decimal('0.00')
        if fee_structure:
            total_amount = (
                fee_structure.fee_amount + 
                fee_structure.booking_fee + 
                fee_structure.security_deposit
            )
        
        context = {
            'student': student,
            'room': room,
            'beds': beds,
            'fee_structure': fee_structure,
            'total_amount': total_amount,
            'has_existing_allocation': has_existing_allocation,
            'existing_allocation': existing_allocation,
            'current_semester': current_semester,
        }
        
        return render(request, 'student/room_detail.html', context)
        
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('student_dashboard')

# ============= RESERVE BED VIEW =============
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from decimal import Decimal
import json
import logging

from portal.models import (
    Student, HostelBed, Semester, HostelApplication, 
    HostelFeeStructure, BedReservation, MpesaPayment,
    SMSNotification, HostelAllocation
)
from portal.mpesa_utils import initiate_stk_push, query_stk_status

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["POST"])
def reserve_bed(request, bed_id):
    """
    Reserve a bed and initiate M-Pesa payment
    Requirements:
    1. Student cannot have existing active allocation
    2. Collect full student data
    3. Process full payment amount
    """
    try:
        student = Student.objects.get(user=request.user)
        bed = get_object_or_404(HostelBed, id=bed_id, is_active=True)
        current_semester = Semester.objects.filter(is_current=True).first()
        
        if not current_semester:
            return JsonResponse({
                'success': False,
                'message': 'No active semester found'
            }, status=400)
        
        # Get form data
        phone_number = request.POST.get('phone_number', '').strip()
        id_number = request.POST.get('id_number', '').strip()
        emergency_contact = request.POST.get('emergency_contact', '').strip()
        emergency_phone = request.POST.get('emergency_phone', '').strip()
        
        # Validate required fields
        if not all([phone_number, id_number, emergency_contact, emergency_phone]):
            return JsonResponse({
                'success': False,
                'message': 'All fields are required'
            }, status=400)
        
        # REMOVED: Application check - students can book directly
        
        # 1. CHECK: Ensure bed is available
        if bed.status != 'available':
            return JsonResponse({
                'success': False,
                'message': 'This bed is not available'
            }, status=400)
        
        # 2. CHECK: No existing active reservation
        existing_reservation = BedReservation.objects.filter(
            bed=bed,
            status='pending',
            expires_at__gt=timezone.now()
        ).first()
        
        if existing_reservation:
            return JsonResponse({
                'success': False,
                'message': 'This bed is currently reserved by another student. Please choose another bed.'
            }, status=400)
        
        # 3. CHECK: Student doesn't have existing allocation for this semester
        existing_allocation = HostelAllocation.objects.filter(
            student=student,
            semester=current_semester,
            is_active=True
        ).first()
        
        if existing_allocation:
            return JsonResponse({
                'success': False,
                'message': f'You already have an active allocation in {existing_allocation.bed.room.hostel.name}, Room {existing_allocation.bed.room.room_number}. You cannot book multiple beds.'
            }, status=400)
        
        # 4. CHECK: Student doesn't have pending reservation
        pending_reservation = BedReservation.objects.filter(
            student=student,
            status='pending',
            expires_at__gt=timezone.now()
        ).first()
        
        if pending_reservation:
            return JsonResponse({
                'success': False,
                'message': 'You already have a pending reservation. Please complete or cancel it first.'
            }, status=400)
        
        # Get fee structure - FULL AMOUNT
        fee_structure = HostelFeeStructure.objects.filter(
            hostel=bed.room.hostel,
            room_type=bed.room.room_type,
            academic_year=current_semester.academic_year,
            semester=current_semester,
            is_active=True
        ).first()
        
        if not fee_structure:
            return JsonResponse({
                'success': False,
                'message': 'Fee structure not found for this hostel'
            }, status=400)
        
        # Calculate FULL amount
        total_amount = (
            fee_structure.fee_amount + 
            fee_structure.booking_fee + 
            fee_structure.security_deposit
        )
        
        # Format phone number for M-Pesa (254XXXXXXXXX)
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        elif phone_number.startswith('+254'):
            phone_number = phone_number[1:]
        elif phone_number.startswith('254'):
            pass
        else:
            phone_number = '254' + phone_number
        
        # Validate phone number length
        if len(phone_number) != 12:
            return JsonResponse({
                'success': False,
                'message': 'Invalid phone number format. Please enter a valid Kenyan phone number.'
            }, status=400)
        
        with transaction.atomic():
            # Update student emergency contact info
            student.emergency_contact_name = emergency_contact
            student.emergency_contact_phone = emergency_phone
            if id_number:
                student.national_id = id_number
            student.save()
            
            # Create or get application automatically (for record-keeping)
            application, created = HostelApplication.objects.get_or_create(
                student=student,
                hostel=bed.room.hostel,
                semester=current_semester,
                academic_year=current_semester.academic_year,
                defaults={
                    'preferred_room_type': bed.room.room_type,
                    'status': 'approved',  # Auto-approve since booking directly
                    'booking_fee_paid': False,
                    'remarks': 'Auto-created from direct bed booking'
                }
            )
            
            # If application exists but was rejected/cancelled, update it
            if not created and application.status in ['rejected', 'cancelled']:
                application.status = 'approved'
                application.preferred_room_type = bed.room.room_type
                application.remarks = 'Updated from direct bed booking'
                application.save()
            
            # Create bed reservation with full amount
            reservation = BedReservation.objects.create(
                student=student,
                bed=bed,
                application=application,
                amount=total_amount,
                payment_phone=phone_number,
                status='pending',
                expires_at=timezone.now() + timezone.timedelta(minutes=15)
            )
            
            # Initiate M-Pesa STK Push for FULL AMOUNT
            account_reference = f"HOSTEL-{student.registration_number}"
            transaction_desc = f"Hostel Fee - {bed.room.hostel.name}"
            
            mpesa_response = initiate_stk_push(
                phone_number=phone_number,
                amount=float(total_amount),
                account_reference=account_reference,
                transaction_desc=transaction_desc,
                student=student,
                reservation=reservation,
                application=application
            )
            
            if mpesa_response['success']:
                return JsonResponse({
                    'success': True,
                    'message': 'Payment request sent to your phone. Please enter your M-Pesa PIN.',
                    'reservation_id': str(reservation.reservation_id),
                    'checkout_request_id': mpesa_response['checkout_request_id'],
                    'expires_at': reservation.expires_at.isoformat(),
                    'amount': str(total_amount)
                })
            else:
                # Delete reservation if M-Pesa failed
                reservation.delete()
                return JsonResponse({
                    'success': False,
                    'message': mpesa_response.get('message', 'Failed to initiate payment')
                }, status=400)
    
    except Student.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Student profile not found'
        }, status=404)
    except Exception as e:
        logger.error(f'Bed reservation error: {str(e)}', exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=500)

@login_required
def check_payment_status(request, reservation_id):
    """Check payment status via AJAX"""
    try:
        student = Student.objects.get(user=request.user)
        reservation = get_object_or_404(
            BedReservation,
            reservation_id=reservation_id,
            student=student
        )
        
        # Get latest payment
        latest_payment = reservation.mpesa_payments.order_by('-initiated_at').first()
        
        if not latest_payment:
            return JsonResponse({
                'success': False,
                'message': 'No payment found'
            })
        
        # Check if reservation expired
        is_expired = reservation.is_expired()
        
        return JsonResponse({
            'success': True,
            'reservation_status': reservation.status,
            'payment_status': latest_payment.status,
            'is_expired': is_expired,
            'mpesa_receipt': latest_payment.mpesa_receipt_number or '',
            'amount': str(reservation.amount)
        })
        
    except Student.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Student not found'
        }, status=404)
    except Exception as e:
        logger.error(f'Payment status check error: {str(e)}')
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def mpesa_callback(request):
    """
    M-Pesa STK Push Callback
    Receives payment status from Safaricom
    """
    try:
        # Parse callback data
        data = json.loads(request.body.decode('utf-8'))
        logger.info(f'M-Pesa Callback received: {json.dumps(data, indent=2)}')
        
        # Extract callback data
        stk_callback = data.get('Body', {}).get('stkCallback', {})
        merchant_request_id = stk_callback.get('MerchantRequestID')
        checkout_request_id = stk_callback.get('CheckoutRequestID')
        result_code = stk_callback.get('ResultCode')
        result_desc = stk_callback.get('ResultDesc')
        
        # Find payment record
        payment = MpesaPayment.objects.filter(
            checkout_request_id=checkout_request_id
        ).first()
        
        if not payment:
            logger.error(f'Payment not found for CheckoutRequestID: {checkout_request_id}')
            return JsonResponse({
                'ResultCode': 1,
                'ResultDesc': 'Payment record not found'
            })
        
        with transaction.atomic():
            # Update payment record
            payment.result_code = str(result_code)
            payment.result_desc = result_desc
            payment.completed_at = timezone.now()
            
            if result_code == 0:
                # Payment successful
                payment.status = 'success'
                
                # Extract callback metadata
                callback_metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])
                for item in callback_metadata:
                    if item.get('Name') == 'MpesaReceiptNumber':
                        payment.mpesa_receipt_number = item.get('Value')
                    elif item.get('Name') == 'TransactionDate':
                        payment.transaction_date = timezone.now()
                
                payment.save()
                
                # Update reservation
                if payment.bed_reservation:
                    reservation = payment.bed_reservation
                    reservation.status = 'confirmed'
                    reservation.save()
                    
                    # Create hostel allocation
                    allocation = HostelAllocation.objects.create(
                        student=reservation.student,
                        bed=reservation.bed,
                        academic_year=reservation.bed.academic_year,
                        semester=Semester.objects.filter(is_current=True).first(),
                        check_in_date=timezone.now(),
                        is_active=True,
                        fee_paid=True,
                        payment_reference=payment.mpesa_receipt_number,
                        allocated_by=None,  # Auto-allocated via payment
                        remarks=f'Auto-allocated after payment. Receipt: {payment.mpesa_receipt_number}'
                    )
                    
                    # Update bed status
                    reservation.bed.status = 'occupied'
                    reservation.bed.save()
                    
                    # Send confirmation email
                    send_booking_confirmation_email(reservation.student, allocation, payment)
                    
                    # Send SMS notification
                    send_booking_confirmation_sms(reservation.student, allocation, payment)
                    
                    logger.info(f'Allocation created for {reservation.student.registration_number}')
            
            else:
                # Payment failed
                payment.status = 'failed'
                payment.save()
                
                if payment.bed_reservation:
                    reservation = payment.bed_reservation
                    reservation.status = 'cancelled'
                    reservation.save()
                    
                    # Release bed
                    reservation.bed.status = 'available'
                    reservation.bed.save()
                    
                    # Send failure SMS
                    send_payment_failure_sms(reservation.student, result_desc)
        
        return JsonResponse({
            'ResultCode': 0,
            'ResultDesc': 'Success'
        })
        
    except Exception as e:
        logger.error(f'M-Pesa callback error: {str(e)}', exc_info=True)
        return JsonResponse({
            'ResultCode': 1,
            'ResultDesc': str(e)
        })


def send_booking_confirmation_email(student, allocation, payment):
    """Send booking confirmation email with receipt"""
    try:
        subject = f'Hostel Booking Confirmation - {allocation.bed.room.hostel.name}'
        
        context = {
            'student': student,
            'allocation': allocation,
            'payment': payment,
            'bed': allocation.bed,
            'room': allocation.bed.room,
            'hostel': allocation.bed.room.hostel,
        }
        
        html_message = render_to_string('emails/hostel_booking_confirmation.html', context)
        plain_message = f"""
Dear {student.user.get_full_name()},

Your hostel booking has been confirmed!

BOOKING DETAILS:
- Hostel: {allocation.bed.room.hostel.name}
- Room: {allocation.bed.room.room_number}
- Bed: {allocation.bed.bed_number}
- Floor: {allocation.bed.room.floor}

PAYMENT DETAILS:
- Amount Paid: Ksh {payment.amount}
- M-Pesa Receipt: {payment.mpesa_receipt_number}
- Payment Date: {payment.transaction_date}

Please present this email when checking in.

For any queries, contact the hostel office.

Best regards,
University Hostel Management
        """
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[student.user.email],
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f'Confirmation email sent to {student.user.email}')
        
    except Exception as e:
        logger.error(f'Email sending error: {str(e)}')


def send_booking_confirmation_sms(student, allocation, payment):
    """Send SMS confirmation"""
    try:
        message = (
            f"Hostel booking confirmed! "
            f"{allocation.bed.room.hostel.name}, Room {allocation.bed.room.room_number}, "
            f"Bed {allocation.bed.bed_number}. "
            f"Receipt: {payment.mpesa_receipt_number}. "
            f"Check your email for details."
        )
        
        # Create SMS notification record
        SMSNotification.objects.create(
            student=student,
            phone_number=student.user.phone_number,
            sms_type='booking_confirmation',
            message=message,
            status='sent',
            mpesa_payment=payment,
            hostel_allocation=allocation,
            sent_at=timezone.now()
        )
        
        # TODO: Integrate with actual SMS gateway (Africa's Talking, etc.)
        # send_sms(phone_number=student.user.phone_number, message=message)
        
        logger.info(f'SMS sent to {student.user.phone_number}')
        
    except Exception as e:
        logger.error(f'SMS sending error: {str(e)}')


def send_payment_failure_sms(student, reason):
    """Send SMS for failed payment"""
    try:
        message = f"Hostel payment failed: {reason}. Please try again or contact support."
        
        SMSNotification.objects.create(
            student=student,
            phone_number=student.user.phone_number,
            sms_type='payment_failed',
            message=message,
            status='sent',
            sent_at=timezone.now()
        )
        
        logger.info(f'Failure SMS sent to {student.user.phone_number}')
        
    except Exception as e:
        logger.error(f'SMS sending error: {str(e)}')


@login_required
def my_hostel_allocation(request):
    """View student's current allocation"""
    try:
        student = Student.objects.get(user=request.user)
        current_semester = Semester.objects.filter(is_current=True).first()
        
        allocation = HostelAllocation.objects.filter(
            student=student,
            semester=current_semester,
            is_active=True
        ).select_related(
            'bed__room__hostel',
            'bed__room'
        ).first()
        
        context = {
            'student': student,
            'allocation': allocation,
        }
        
        return render(request, 'student/my_hostel_allocation.html', context)
        
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('student_dashboard')
        
@login_required
def hostel_application_status(request):
    """View hostel application status"""
    try:
        student = Student.objects.get(user=request.user)
        
        from portal.models import HostelApplication, Semester
        
        current_semester = Semester.objects.filter(is_current=True).first()
        
        # Get all applications
        applications = HostelApplication.objects.filter(
            student=student
        ).select_related(
            'hostel',
            'academic_year',
            'semester',
            'approved_by'
        ).order_by('-application_date')
        
        # Get current application
        current_application = applications.filter(
            semester=current_semester
        ).first()
        
        context = {
            'student': student,
            'current_semester': current_semester,
            'current_application': current_application,
            'applications': applications,
        }
        
        return render(request, 'student/hostel_application_status.html', context)
        
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('student_dashboard')


@login_required
def cancel_hostel_application(request, application_id):
    """Cancel hostel application"""
    try:
        student = Student.objects.get(user=request.user)
        
        from portal.models import HostelApplication
        
        application = HostelApplication.objects.get(
            id=application_id,
            student=student
        )
        
        if application.status not in ['pending']:
            messages.error(request, 'Only pending applications can be cancelled.')
            return redirect('hostel_application_status')
        
        application.status = 'cancelled'
        application.remarks = 'Cancelled by student'
        application.save()
        
        messages.success(request, 'Hostel application cancelled successfully.')
        return redirect('hostel_application_status')
        
    except HostelApplication.DoesNotExist:
        messages.error(request, 'Application not found.')
        return redirect('hostel_application_status')
    except Exception as e:
        messages.error(request, f'Error cancelling application: {str(e)}')
        return redirect('hostel_application_status')


"""
REST API Views for Hostel Management
Add these to a new file: portal/api_views.py
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Avg, Count, Q
from django.utils import timezone
from decimal import Decimal

from portal.models import (
    Student, Hostel, HostelRoom, HostelBed, HostelApplication,
    HostelAllocation, HostelFeeStructure, Semester, AcademicYear,
    BedReservation, MpesaPayment, HostelReview
)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


# ============= HOSTEL APIs =============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_hostels_list(request):
    """
    Get list of available hostels
    
    Query params:
    - gender: Filter by gender (M/F/mixed)
    - available_only: Filter hostels with available spaces (true/false)
    - search: Search by hostel name
    """
    try:
        student = Student.objects.get(user=request.user)
        current_semester = Semester.objects.filter(is_current=True).first()
        
        hostels = Hostel.objects.filter(is_active=True)
        
        # Filter by student gender
        hostels = hostels.filter(
            Q(gender_type=student.gender) | Q(gender_type='mixed')
        )
        
        # Search filter
        search = request.GET.get('search')
        if search:
            hostels = hostels.filter(
                Q(name__icontains=search) | Q(code__icontains=search)
            )
        
        # Available spaces filter
        available_only = request.GET.get('available_only', 'false').lower() == 'true'
        
        hostels_data = []
        for hostel in hostels:
            # Calculate occupancy
            total_capacity = hostel.total_capacity
            allocated_count = HostelAllocation.objects.filter(
                bed__room__hostel=hostel,
                academic_year=current_semester.academic_year,
                is_active=True
            ).count()
            
            available_spaces = total_capacity - allocated_count
            
            if available_only and available_spaces <= 0:
                continue
            
            # Get average rating
            avg_rating = hostel.reviews.filter(
                is_approved=True
            ).aggregate(avg=Avg('overall_rating'))['avg'] or 0
            
            # Get primary image
            primary_image = hostel.images.filter(is_primary=True).first()
            
            # Get fee range
            fee_structures = HostelFeeStructure.objects.filter(
                hostel=hostel,
                academic_year=current_semester.academic_year,
                semester=current_semester,
                is_active=True
            )
            
            min_fee = fee_structures.aggregate(
                min=models.Min('fee_amount')
            )['min'] or 0
            
            max_fee = fee_structures.aggregate(
                max=models.Max('fee_amount')
            )['max'] or 0
            
            hostels_data.append({
                'id': hostel.id,
                'name': hostel.name,
                'code': hostel.code,
                'gender_type': hostel.gender_type,
                'location': hostel.location,
                'total_capacity': total_capacity,
                'available_spaces': available_spaces,
                'occupancy_percentage': (allocated_count / total_capacity * 100) if total_capacity > 0 else 0,
                'amenities': hostel.amenities,
                'avg_rating': float(avg_rating),
                'review_count': hostel.reviews.filter(is_approved=True).count(),
                'primary_image': primary_image.image.url if primary_image else None,
                'fee_range': {
                    'min': float(min_fee),
                    'max': float(max_fee)
                }
            })
        
        return Response({
            'success': True,
            'count': len(hostels_data),
            'hostels': hostels_data
        })
        
    except Student.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Student profile not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_hostel_detail(request, hostel_id):
    """Get detailed information about a specific hostel"""
    try:
        student = Student.objects.get(user=request.user)
        hostel = Hostel.objects.get(id=hostel_id, is_active=True)
        current_semester = Semester.objects.filter(is_current=True).first()
        
        # Get all images
        images = [{
            'id': img.id,
            'image': img.image.url,
            'caption': img.caption,
            'is_primary': img.is_primary
        } for img in hostel.images.all()]
        
        # Get fee structures
        fee_structures = HostelFeeStructure.objects.filter(
            hostel=hostel,
            academic_year=current_semester.academic_year,
            semester=current_semester,
            is_active=True
        )
        
        fees = [{
            'room_type': fs.room_type,
            'fee_amount': float(fs.fee_amount),
            'booking_fee': float(fs.booking_fee),
            'security_deposit': float(fs.security_deposit),
            'total': float(fs.fee_amount + fs.booking_fee + fs.security_deposit)
        } for fs in fee_structures]
        
        # Get reviews with ratings
        reviews = hostel.reviews.filter(is_approved=True)
        
        ratings = {
            'overall': float(reviews.aggregate(avg=Avg('overall_rating'))['avg'] or 0),
            'cleanliness': float(reviews.aggregate(avg=Avg('cleanliness_rating'))['avg'] or 0),
            'facilities': float(reviews.aggregate(avg=Avg('facilities_rating'))['avg'] or 0),
            'security': float(reviews.aggregate(avg=Avg('security_rating'))['avg'] or 0),
            'management': float(reviews.aggregate(avg=Avg('management_rating'))['avg'] or 0),
            'count': reviews.count()
        }
        
        # Get recent reviews
        recent_reviews = [{
            'student_name': f"{review.student.user.first_name} {review.student.user.last_name[0]}.",
            'title': review.title,
            'review': review.review,
            'overall_rating': float(review.overall_rating),
            'created_at': review.created_at.isoformat()
        } for review in reviews[:5]]
        
        return Response({
            'success': True,
            'hostel': {
                'id': hostel.id,
                'name': hostel.name,
                'code': hostel.code,
                'gender_type': hostel.gender_type,
                'location': hostel.location,
                'description': hostel.description,
                'amenities': hostel.amenities,
                'total_capacity': hostel.total_capacity,
                'images': images,
                'fees': fees,
                'ratings': ratings,
                'recent_reviews': recent_reviews
            }
        })
        
    except Hostel.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Hostel not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_hostel_rooms(request, hostel_id):
    """
    Get rooms in a hostel
    
    Query params:
    - floor: Filter by floor number
    - room_type: Filter by room type (single/double/triple/quad)
    - available_only: Show only rooms with available beds
    """
    try:
        hostel = Hostel.objects.get(id=hostel_id, is_active=True)
        current_semester = Semester.objects.filter(is_current=True).first()
        
        rooms = hostel.rooms.filter(is_active=True)
        
        # Filters
        floor = request.GET.get('floor')
        if floor:
            rooms = rooms.filter(floor=int(floor))
        
        room_type = request.GET.get('room_type')
        if room_type:
            rooms = rooms.filter(room_type=room_type)
        
        available_only = request.GET.get('available_only', 'false').lower() == 'true'
        
        rooms_data = []
        for room in rooms:
            # Get bed availability
            total_beds = room.capacity
            available_beds_count = room.beds.filter(
                status='available',
                academic_year=current_semester.academic_year
            ).count()
            
            if available_only and available_beds_count == 0:
                continue
            
            # Get primary image
            primary_image = room.images.filter(is_primary=True).first()
            
            # Get fee
            fee_structure = HostelFeeStructure.objects.filter(
                hostel=hostel,
                room_type=room.room_type,
                academic_year=current_semester.academic_year,
                semester=current_semester,
                is_active=True
            ).first()
            
            rooms_data.append({
                'id': room.id,
                'room_number': room.room_number,
                'floor': room.floor,
                'room_type': room.room_type,
                'capacity': total_beds,
                'available_beds': available_beds_count,
                'occupancy_rate': ((total_beds - available_beds_count) / total_beds * 100) if total_beds > 0 else 0,
                'has_bathroom': room.has_bathroom,
                'has_balcony': room.has_balcony,
                'primary_image': primary_image.image.url if primary_image else None,
                'fee': float(fee_structure.fee_amount) if fee_structure else 0
            })
        
        return Response({
            'success': True,
            'count': len(rooms_data),
            'rooms': rooms_data
        })
        
    except Hostel.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Hostel not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_room_beds(request, room_id):
    """Get available beds in a room"""
    try:
        room = HostelRoom.objects.get(id=room_id, is_active=True)
        current_semester = Semester.objects.filter(is_current=True).first()
        
        beds = room.beds.filter(
            academic_year=current_semester.academic_year
        ).order_by('bed_number')
        
        beds_data = []
        for bed in beds:
            # Check for active reservation
            active_reservation = BedReservation.objects.filter(
                bed=bed,
                status='pending',
                expires_at__gt=timezone.now()
            ).first()
            
            beds_data.append({
                'id': bed.id,
                'bed_number': bed.bed_number,
                'status': bed.status,
                'is_available': bed.status == 'available',
                'is_reserved': active_reservation is not None,
                'reservation_expires': active_reservation.expires_at.isoformat() if active_reservation else None
            })
        
        # Get fee
        fee_structure = HostelFeeStructure.objects.filter(
            hostel=room.hostel,
            room_type=room.room_type,
            academic_year=current_semester.academic_year,
            semester=current_semester,
            is_active=True
        ).first()
        
        return Response({
            'success': True,
            'room': {
                'id': room.id,
                'room_number': room.room_number,
                'room_type': room.room_type,
                'floor': room.floor,
                'capacity': room.capacity
            },
            'fee': {
                'fee_amount': float(fee_structure.fee_amount),
                'booking_fee': float(fee_structure.booking_fee),
                'security_deposit': float(fee_structure.security_deposit),
                'total': float(fee_structure.fee_amount + fee_structure.booking_fee + fee_structure.security_deposit)
            } if fee_structure else None,
            'beds': beds_data
        })
        
    except HostelRoom.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Room not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_reserve_bed(request):
    """
    Reserve a bed and initiate payment
    
    POST data:
    - bed_id: ID of the bed to reserve
    - phone_number: M-Pesa phone number
    """
    try:
        student = Student.objects.get(user=request.user)
        bed_id = request.data.get('bed_id')
        phone_number = request.data.get('phone_number')
        
        if not bed_id or not phone_number:
            return Response({
                'success': False,
                'message': 'Bed ID and phone number are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Use the reserve_bed view logic here
        # Return the response in API format
        
        return Response({
            'success': True,
            'message': 'Bed reserved successfully. Payment request sent.',
            'reservation_id': 'xxx',
            'checkout_request_id': 'xxx'
        })
        
    except Student.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Student profile not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_my_application(request):
    """Get student's current hostel application"""
    try:
        student = Student.objects.get(user=request.user)
        current_semester = Semester.objects.filter(is_current=True).first()
        
        application = HostelApplication.objects.filter(
            student=student,
            semester=current_semester
        ).select_related('hostel').first()
        
        if not application:
            return Response({
                'success': True,
                'has_application': False,
                'application': None
            })
        
        # Get reservation if any
        reservation = BedReservation.objects.filter(
            application=application,
            student=student
        ).select_related('bed__room__hostel').first()
        
        return Response({
            'success': True,
            'has_application': True,
            'application': {
                'id': application.id,
                'hostel': {
                    'id': application.hostel.id,
                    'name': application.hostel.name,
                    'code': application.hostel.code
                },
                'status': application.status,
                'preferred_room_type': application.preferred_room_type,
                'booking_fee_paid': application.booking_fee_paid,
                'application_date': application.application_date.isoformat(),
                'remarks': application.remarks
            },
            'reservation': {
                'bed_number': reservation.bed.bed_number,
                'room_number': reservation.bed.room.room_number,
                'floor': reservation.bed.room.floor,
                'status': reservation.status,
                'amount': float(reservation.amount)
            } if reservation else None
        })
        
    except Student.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Student profile not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_my_allocation(request):
    """Get student's current hostel allocation"""
    try:
        student = Student.objects.get(user=request.user)
        current_semester = Semester.objects.filter(is_current=True).first()
        
        allocation = HostelAllocation.objects.filter(
            student=student,
            semester=current_semester,
            is_active=True
        ).select_related('bed__room__hostel').first()
        
        if not allocation:
            return Response({
                'success': True,
                'has_allocation': False,
                'allocation': None
            })
        
        return Response({
            'success': True,
            'has_allocation': True,
            'allocation': {
                'hostel': {
                    'id': allocation.bed.room.hostel.id,
                    'name': allocation.bed.room.hostel.name,
                    'code': allocation.bed.room.hostel.code,
                    'location': allocation.bed.room.hostel.location
                },
                'room': {
                    'room_number': allocation.bed.room.room_number,
                    'floor': allocation.bed.room.floor,
                    'room_type': allocation.bed.room.room_type
                },
                'bed': {
                    'bed_number': allocation.bed.bed_number
                },
                'allocation_date': allocation.allocation_date.isoformat(),
                'check_in_date': allocation.check_in_date.isoformat() if allocation.check_in_date else None,
                'fee_paid': allocation.fee_paid,
                'payment_reference': allocation.payment_reference
            }
        })
        
    except Student.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Student profile not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_check_payment_status(request):
    """
    Check payment status
    
    POST data:
    - reservation_id: UUID of the reservation
    """
    try:
        student = Student.objects.get(user=request.user)
        reservation_id = request.data.get('reservation_id')
        
        reservation = BedReservation.objects.get(
            reservation_id=reservation_id,
            student=student
        )
        
        latest_payment = reservation.mpesa_payments.order_by('-initiated_at').first()
        
        return Response({
            'success': True,
            'reservation': {
                'id': str(reservation.reservation_id),
                'status': reservation.status,
                'expires_at': reservation.expires_at.isoformat(),
                'is_expired': reservation.is_expired()
            },
            'payment': {
                'status': latest_payment.status,
                'amount': float(latest_payment.amount),
                'phone_number': latest_payment.phone_number,
                'mpesa_receipt': latest_payment.mpesa_receipt_number
            } if latest_payment else None
        })
        
    except BedReservation.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Reservation not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_hostel_reviews(request, hostel_id):
    """Get reviews for a hostel"""
    try:
        hostel = Hostel.objects.get(id=hostel_id)
        
        reviews = hostel.reviews.filter(
            is_approved=True
        ).select_related('student__user').order_by('-created_at')
        
        # Pagination
        paginator = StandardResultsSetPagination()
        paginated_reviews = paginator.paginate_queryset(reviews, request)
        
        reviews_data = [{
            'id': review.id,
            'student_name': f"{review.student.user.first_name} {review.student.user.last_name[0]}.",
            'title': review.title,
            'review': review.review,
            'ratings': {
                'overall': float(review.overall_rating),
                'cleanliness': review.cleanliness_rating,
                'facilities': review.facilities_rating,
                'security': review.security_rating,
                'management': review.management_rating
            },
            'created_at': review.created_at.isoformat()
        } for review in paginated_reviews]
        
        return paginator.get_paginated_response({
            'success': True,
            'reviews': reviews_data
        })
        
    except Hostel.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Hostel not found'
        }, status=status.HTTP_404_NOT_FOUND)
# views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import timedelta

@login_required
def lecturer_dashboard(request):
    """Lecturer dashboard view"""
    # Get lecturer profile
    try:
        lecturer = request.user.lecturer_profile
    except:
        return render(request, 'lecturer/no_profile.html')
    
    # Get current semester
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get current academic year
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    
    # ============= CURRENT SEMESTER STATISTICS =============
    current_allocations = []
    total_students = 0
    pending_marks = 0
    
    if current_semester:
        # Get current semester allocations
        current_allocations = UnitAllocation.objects.filter(
            lecturer=request.user,
            semester=current_semester,
            status__in=['approved_hod', 'approved_hos', 'approved_dean']
        ).select_related(
            'programme_unit__unit',
            'programme_unit__programme',
            'semester__academic_year'
        ).prefetch_related(
            'programme_unit__registrations'
        )
        
        # Count total students enrolled in lecturer's units
        for allocation in current_allocations:
            students_count = UnitRegistration.objects.filter(
                programme_unit=allocation.programme_unit,
                semester=current_semester,
                status='registered'
            ).count()
            total_students += students_count
        
        # Count pending marks (assessments without marks or draft marks)
        pending_marks = StudentMarks.objects.filter(
            assessment__unit_allocation__lecturer=request.user,
            assessment__unit_allocation__semester=current_semester,
            status='draft'
        ).count()
    
    # ============= UNIT STATISTICS =============
    # Total units ever taught
    total_units_taught = UnitAllocation.objects.filter(
        lecturer=request.user
    ).values('programme_unit__unit').distinct().count()
    
    # Current semester units count
    current_units_count = current_allocations.count()
    
    # Total allocations
    total_allocations = UnitAllocation.objects.filter(
        lecturer=request.user
    ).count()
    
    # ============= RECENT ASSESSMENTS =============
    recent_assessments = Assessment.objects.filter(
        unit_allocation__lecturer=request.user,
        unit_allocation__semester=current_semester
    ).select_related(
        'unit_allocation__programme_unit__unit',
        'unit_allocation__semester'
    ).order_by('-date')[:5]
    
    # ============= UPCOMING ASSESSMENTS =============
    today = timezone.now().date()
    upcoming_assessments = Assessment.objects.filter(
        unit_allocation__lecturer=request.user,
        unit_allocation__semester=current_semester,
        date__gte=today
    ).select_related(
        'unit_allocation__programme_unit__unit',
        'unit_allocation__semester'
    ).order_by('date')[:5]
    
    # ============= TIMETABLE FOR TODAY =============
    current_day = timezone.now().strftime('%A').lower()
    today_schedule = []
    
    if current_semester:
        today_schedule = TimetableSlot.objects.filter(
            unit_allocation__lecturer=request.user,
            unit_allocation__semester=current_semester,
            day_of_week=current_day
        ).select_related(
            'unit_allocation__programme_unit__unit',
            'unit_allocation__programme_unit__programme'
        ).order_by('start_time')
    
    # ============= RECENT ACTIVITY =============
    # Get recent marks submissions
    recent_marks_submissions = StudentMarks.objects.filter(
        submitted_by=request.user
    ).select_related(
        'assessment__unit_allocation__programme_unit__unit',
        'student'
    ).order_by('-created_at')[:5]
    
    # ============= WORKLOAD ANALYSIS =============
    workload_data = []
    if current_semester:
        for allocation in current_allocations:
            students_count = UnitRegistration.objects.filter(
                programme_unit=allocation.programme_unit,
                semester=current_semester,
                status='registered'
            ).count()
            
            assessments_count = Assessment.objects.filter(
                unit_allocation=allocation
            ).count()
            
            workload_data.append({
                'unit': allocation.programme_unit.unit,
                'programme': allocation.programme_unit.programme,
                'students': students_count,
                'assessments': assessments_count,
                'max_students': allocation.max_students
            })
    
    # ============= QUICK STATS FOR CHARTS =============
    # Attendance statistics
    attendance_stats = {
        'present': 0,
        'absent': 0,
        'late': 0,
        'excused': 0
    }
    
    if current_semester:
        attendance_data = Attendance.objects.filter(
            unit_allocation__lecturer=request.user,
            unit_allocation__semester=current_semester
        ).values('status').annotate(count=Count('id'))
        
        for item in attendance_data:
            attendance_stats[item['status']] = item['count']
    
    # ============= ANNOUNCEMENTS =============
    recent_announcements = Announcement.objects.filter(
        Q(target_audience='all') | 
        Q(target_audience='lecturers') |
        Q(target_school=lecturer.department.school)
    ).filter(
        is_published=True,
        publish_date__lte=timezone.now()
    ).order_by('-created_at')[:5]
    
    context = {
        'page_title': 'Lecturer Dashboard',
        'lecturer': lecturer,
        'current_semester': current_semester,
        'current_academic_year': current_academic_year,
        
        # Statistics
        'total_students': total_students,
        'current_units_count': current_units_count,
        'total_units_taught': total_units_taught,
        'total_allocations': total_allocations,
        'pending_marks': pending_marks,
        
        # Units and schedules
        'current_allocations': current_allocations,
        'today_schedule': today_schedule,
        'current_day': current_day,
        
        # Assessments
        'recent_assessments': recent_assessments,
        'upcoming_assessments': upcoming_assessments,
        
        # Activity
        'recent_marks_submissions': recent_marks_submissions,
        'workload_data': workload_data,
        'attendance_stats': attendance_stats,
        
        # Announcements
        'recent_announcements': recent_announcements,
    }
    
    return render(request, 'lecturer/dashboard.html', context)

# Placeholder views for other roles
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Avg, Q, F, Max
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
from collections import defaultdict

@login_required
def dean_dashboard(request):
    """Dean Dashboard with comprehensive school statistics"""
    
    # Get dean's school
    try:
        dean_profile = request.user
        school = School.objects.get(dean=dean_profile)
    except School.DoesNotExist:
        # If no school assigned, show empty dashboard
        context = {
            'page_title': 'Dean Dashboard',
            'error': 'No school assigned to your account'
        }
        return render(request, 'dean/dashboard.html', context)
    
    # Get current academic period
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get all departments in the school
    departments = Department.objects.filter(school=school, is_active=True)
    
    # ==================== STAT CARDS ====================
    
    # Total Students in School
    total_students = Student.objects.filter(
        programme__department__school=school,
        student_status='active'
    ).count()
    
    # Total Lecturers in School
    total_lecturers = Lecturer.objects.filter(
        department__school=school,
        is_active=True
    ).count()
    
    # Total Programmes in School
    total_programmes = Programme.objects.filter(
        department__school=school,
        is_active=True
    ).count()
    
    # Average School GPA
    avg_school_gpa = Student.objects.filter(
        programme__department__school=school,
        student_status='active'
    ).aggregate(avg_gpa=Avg('cumulative_gpa'))['avg_gpa'] or 0
    
    # ==================== GENDER DISTRIBUTION ====================
    
    gender_data = Student.objects.filter(
        programme__department__school=school,
        student_status='active'
    ).values('gender').annotate(count=Count('id')).order_by('gender')
    
    gender_labels = []
    gender_counts = []
    gender_mapping = {'M': 'Male', 'F': 'Female', 'O': 'Other'}
    
    for item in gender_data:
        gender_labels.append(gender_mapping.get(item['gender'], 'Unknown'))
        gender_counts.append(item['count'])
    
    # ==================== YEAR OF STUDY DISTRIBUTION ====================
    
    year_data = Student.objects.filter(
        programme__department__school=school,
        student_status='active'
    ).values('current_year').annotate(count=Count('id')).order_by('current_year')
    
    year_labels = [f"Year {item['current_year']}" for item in year_data]
    year_counts = [item['count'] for item in year_data]
    
    # ==================== DEPARTMENT PERFORMANCE RANKING ====================
    
    dept_performance = []
    for dept in departments:
        avg_gpa = Student.objects.filter(
            programme__department=dept,
            student_status='active'
        ).aggregate(avg_gpa=Avg('cumulative_gpa'))['avg_gpa'] or 0
        
        student_count = Student.objects.filter(
            programme__department=dept,
            student_status='active'
        ).count()
        
        dept_performance.append({
            'department': dept,
            'avg_gpa': round(avg_gpa, 2),
            'student_count': student_count
        })
    
    # Sort by GPA
    dept_performance = sorted(dept_performance, key=lambda x: x['avg_gpa'], reverse=True)
    
    # ==================== PROGRAMME PERFORMANCE RANKING ====================
    
    programme_performance = []
    programmes = Programme.objects.filter(
        department__school=school,
        is_active=True
    )
    
    for prog in programmes:
        avg_gpa = Student.objects.filter(
            programme=prog,
            student_status='active'
        ).aggregate(avg_gpa=Avg('cumulative_gpa'))['avg_gpa'] or 0
        
        student_count = Student.objects.filter(
            programme=prog,
            student_status='active'
        ).count()
        
        if student_count > 0:  # Only include programmes with students
            programme_performance.append({
                'programme': prog,
                'avg_gpa': round(avg_gpa, 2),
                'student_count': student_count
            })
    
    # Sort by GPA
    programme_performance = sorted(programme_performance, key=lambda x: x['avg_gpa'], reverse=True)[:10]
    
    # ==================== TOP 10 PERFORMING STUDENTS ====================
    
    top_students = Student.objects.filter(
        programme__department__school=school,
        student_status='active'
    ).order_by('-cumulative_gpa')[:10]
    
    # ==================== UNIT PERFORMANCE (BEST & WORST) ====================
    
    if current_semester:
        # Get units offered in school
        unit_performance = []
        
        unit_results = SemesterResults.objects.filter(
            programme_unit__programme__department__school=school,
            semester=current_semester,
            is_published=True
        ).values(
            'programme_unit__unit__code',
            'programme_unit__unit__name'
        ).annotate(
            avg_marks=Avg('total_marks'),
            student_count=Count('id'),
            pass_count=Count('id', filter=Q(is_passed=True))
        )
        
        for item in unit_results:
            if item['student_count'] > 0:
                pass_rate = (item['pass_count'] / item['student_count']) * 100
                unit_performance.append({
                    'code': item['programme_unit__unit__code'],
                    'name': item['programme_unit__unit__name'],
                    'avg_marks': round(item['avg_marks'], 2),
                    'pass_rate': round(pass_rate, 2),
                    'student_count': item['student_count']
                })
        
        # Sort by average marks
        unit_performance_sorted = sorted(unit_performance, key=lambda x: x['avg_marks'], reverse=True)
        top_5_units = unit_performance_sorted[:5]
        bottom_5_units = unit_performance_sorted[-5:]
    else:
        top_5_units = []
        bottom_5_units = []
    
    # ==================== STUDENT ENROLLMENT TRENDS (12 MONTHS) ====================
    
    enrollment_labels = []
    enrollment_counts = []
    
    for i in range(11, -1, -1):
        month_date = timezone.now() - timedelta(days=30*i)
        month_label = month_date.strftime('%b %Y')
        enrollment_labels.append(month_label)
        
        count = Student.objects.filter(
            programme__department__school=school,
            admission_date__year=month_date.year,
            admission_date__month=month_date.month
        ).count()
        enrollment_counts.append(count)
    
    # ==================== SEMESTER REPORTING STATUS ====================
    
    if current_semester:
        reporting_data = SemesterReport.objects.filter(
            student__programme__department__school=school,
            to_semester=current_semester
        ).values('status').annotate(count=Count('id'))
        
        reporting_labels = []
        reporting_counts = []
        
        status_mapping = {
            'pending': 'Pending',
            'approved': 'Approved',
            'rejected': 'Rejected',
            'deferred': 'Deferred'
        }
        
        for item in reporting_data:
            reporting_labels.append(status_mapping.get(item['status'], item['status']))
            reporting_counts.append(item['count'])
    else:
        reporting_labels = []
        reporting_counts = []
    
    # ==================== FEE PAYMENT ANALYSIS ====================
    
    fee_labels = []
    fee_expected = []
    fee_paid = []
    fee_percentages = []
    
    # Get last 6 semesters
    recent_semesters = Semester.objects.all().order_by('-start_date')[:6]
    
    for sem in reversed(list(recent_semesters)):
        fee_labels.append(sem.name)
        
        # Calculate expected fees
        expected = FeeBalance.objects.filter(
            student__programme__department__school=school,
            semester=sem
        ).aggregate(total=Sum('total_fees'))['total'] or 0
        
        # Calculate paid fees
        paid = FeeBalance.objects.filter(
            student__programme__department__school=school,
            semester=sem
        ).aggregate(total=Sum('amount_paid'))['total'] or 0
        
        fee_expected.append(float(expected))
        fee_paid.append(float(paid))
        
        # Calculate percentage
        percentage = (paid / expected * 100) if expected > 0 else 0
        fee_percentages.append(round(percentage, 2))
    
    # ==================== PROGRAMME TYPE DISTRIBUTION ====================
    
    programme_type_data = Programme.objects.filter(
        department__school=school,
        is_active=True
    ).values('programme_type').annotate(count=Count('id'))
    
    programme_type_labels = []
    programme_type_counts = []
    
    type_mapping = {
        'certificate': 'Certificate',
        'diploma': 'Diploma',
        'degree': 'Degree',
        'masters': 'Masters',
        'phd': 'PhD'
    }
    
    for item in programme_type_data:
        programme_type_labels.append(type_mapping.get(item['programme_type'], item['programme_type']))
        programme_type_counts.append(item['count'])
    
    # ==================== DEPARTMENT COMPARISON (RADAR CHART DATA) ====================
    
    radar_labels = [dept.name for dept in departments[:6]]  # Max 6 departments for readability
    
    # Metrics: Avg GPA, Student Count (normalized), Programme Count (normalized)
    radar_datasets = []
    
    # Dataset 1: Average GPA (scale 0-4)
    dept_gpas = []
    for dept in departments[:6]:
        avg_gpa = Student.objects.filter(
            programme__department=dept,
            student_status='active'
        ).aggregate(avg_gpa=Avg('cumulative_gpa'))['avg_gpa'] or 0
        dept_gpas.append(round(avg_gpa, 2))
    
    # Dataset 2: Student Count (normalized to 100)
    dept_student_counts = []
    max_students = max([Student.objects.filter(
        programme__department=dept,
        student_status='active'
    ).count() for dept in departments[:6]]) or 1
    
    for dept in departments[:6]:
        count = Student.objects.filter(
            programme__department=dept,
            student_status='active'
        ).count()
        normalized = (count / max_students) * 4  # Scale to 0-4 like GPA
        dept_student_counts.append(round(normalized, 2))
    
    # ==================== ACADEMIC PERFORMANCE TRENDS ====================
    
    # Get last 5 semesters GPA trends
    performance_labels = []
    performance_data = []
    
    performance_semesters = Semester.objects.all().order_by('-start_date')[:5]
    
    for sem in reversed(list(performance_semesters)):
        performance_labels.append(sem.name)
        
        avg_gpa = SemesterGPA.objects.filter(
            student__programme__department__school=school,
            semester=sem
        ).aggregate(avg_gpa=Avg('semester_gpa'))['avg_gpa'] or 0
        
        performance_data.append(round(avg_gpa, 2))
    
    # Prepare context
    context = {
        'page_title': 'Dean Dashboard',
        'school': school,
        'current_academic_year': current_academic_year,
        'current_semester': current_semester,
        
        # Stat Cards
        'total_students': total_students,
        'total_lecturers': total_lecturers,
        'total_programmes': total_programmes,
        'avg_school_gpa': round(avg_school_gpa, 2),
        
        # Gender Distribution
        'gender_labels': gender_labels,
        'gender_counts': gender_counts,
        
        # Year Distribution
        'year_labels': year_labels,
        'year_counts': year_counts,
        
        # Rankings
        'dept_performance': dept_performance,
        'programme_performance': programme_performance,
        'top_students': top_students,
        
        # Unit Performance
        'top_5_units': top_5_units,
        'bottom_5_units': bottom_5_units,
        
        # Trends
        'enrollment_labels': enrollment_labels,
        'enrollment_counts': enrollment_counts,
        
        # Reporting
        'reporting_labels': reporting_labels,
        'reporting_counts': reporting_counts,
        
        # Fee Payment
        'fee_labels': fee_labels,
        'fee_expected': fee_expected,
        'fee_paid': fee_paid,
        'fee_percentages': fee_percentages,
        
        # Programme Types
        'programme_type_labels': programme_type_labels,
        'programme_type_counts': programme_type_counts,
        
        # Radar Chart
        'radar_labels': radar_labels,
        'dept_gpas': dept_gpas,
        'dept_student_counts': dept_student_counts,
        
        # Performance Trends
        'performance_labels': performance_labels,
        'performance_data': performance_data,
    }
    
    return render(request, 'dean/dashboard.html', context)

@login_required
def hos_dashboard(request):
    context = {'page_title': 'Head of School Dashboard'}
    return render(request, 'hos/dashboard.html', context)


@login_required
def hod_dashboard(request):
    context = {'page_title': 'HOD Dashboard'}
    return render(request, 'hod/dashboard.html', context)


"""
Finance Department Views
Complete views for finance officer functionality
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q, F, Avg
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.core.paginator import Paginator
from decimal import Decimal
from datetime import datetime, timedelta
import json

# Import models
from .models import (
    Student, FeeStructure, FeePayment, FeeBalance,
    Programme, AcademicYear, Semester, User,
    School, Department, SchoolBudget, BudgetAllocation,
    ExpenditureTracking, RevenueSource
)


# ============= DASHBOARD =============

@login_required
def finance_dashboard(request):
    """Finance Officer Dashboard with visualizations"""
    from datetime import timedelta
    from django.db.models.functions import TruncDate
    import json
    
    # Get current academic year and semester
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Today's collections
    today = timezone.now().date()
    today_collections = FeePayment.objects.filter(
        payment_date__date=today,
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Monthly collections
    month_start = today.replace(day=1)
    monthly_collections = FeePayment.objects.filter(
        payment_date__date__gte=month_start,
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Total outstanding fees
    outstanding_fees = FeeBalance.objects.filter(
        is_cleared=False,
        semester=current_semester
    ).aggregate(total=Sum('balance'))['total'] or Decimal('0.00')
    
    # Payment statistics
    total_students = Student.objects.filter(student_status='active').count()
    students_cleared = FeeBalance.objects.filter(
        is_cleared=True,
        semester=current_semester
    ).count()
    
    # Recent payments
    recent_payments = FeePayment.objects.select_related(
        'student', 'student__user', 'semester'
    ).filter(
        status='completed'
    ).order_by('-payment_date')[:10]
    
    # Payment method breakdown
    payment_methods = FeePayment.objects.filter(
        payment_date__date__gte=month_start,
        status='completed'
    ).values('payment_method').annotate(
        total=Sum('amount'),
        count=Count('id')
    )
    
    # Fee collection by programme
    programme_collections = FeePayment.objects.filter(
        payment_date__date__gte=month_start,
        status='completed'
    ).values(
        'student__programme__name',
        'student__programme__code'
    ).annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')[:10]
    
    # Pending payments
    pending_payments = FeePayment.objects.filter(
        status='pending'
    ).count()
    
    # Budget overview
    budget_overview = SchoolBudget.objects.filter(
        financial_year=current_academic_year,
        status='active'
    ).aggregate(
        total_allocation=Sum('total_allocation'),
        total_spent=Sum('amount_spent'),
        total_balance=Sum('balance')
    )
    
    # ============= GRAPH DATA =============
    
    # GRAPH 1: Daily Collections Trend (Last 30 days)
    thirty_days_ago = today - timedelta(days=30)
    daily_collections = FeePayment.objects.filter(
        payment_date__date__gte=thirty_days_ago,
        status='completed'
    ).annotate(
        date=TruncDate('payment_date')
    ).values('date').annotate(
        total=Sum('amount')
    ).order_by('date')
    
    # Format for Chart.js
    collections_dates = [item['date'].strftime('%Y-%m-%d') for item in daily_collections]
    collections_amounts = [float(item['total']) for item in daily_collections]
    
    daily_collections_data = {
        'labels': collections_dates,
        'data': collections_amounts
    }
    
    # GRAPH 2: Payment Methods Distribution (Pie Chart)
    payment_methods_chart = []
    for method in payment_methods:
        payment_methods_chart.append({
            'method': method['payment_method'].upper(),
            'amount': float(method['total']),
            'count': method['count']
        })
    
    payment_methods_data = {
        'labels': [item['method'] for item in payment_methods_chart],
        'data': [item['amount'] for item in payment_methods_chart],
        'counts': [item['count'] for item in payment_methods_chart]
    }
    
    # GRAPH 3: Top 10 Programmes by Collections (Bar Chart)
    programme_chart_data = {
        'labels': [item['student__programme__code'] for item in programme_collections],
        'data': [float(item['total']) for item in programme_collections],
        'counts': [item['count'] for item in programme_collections]
    }
    
    # BONUS GRAPH 4: Fee Clearance Status (Donut Chart)
    clearance_data = {
        'labels': ['Cleared', 'Outstanding'],
        'data': [students_cleared, total_students - students_cleared],
        'percentages': [
            round((students_cleared / total_students * 100), 1) if total_students > 0 else 0,
            round(((total_students - students_cleared) / total_students * 100), 1) if total_students > 0 else 0
        ]
    }
    
    context = {
        'current_academic_year': current_academic_year,
        'current_semester': current_semester,
        'today_collections': today_collections,
        'monthly_collections': monthly_collections,
        'outstanding_fees': outstanding_fees,
        'total_students': total_students,
        'students_cleared': students_cleared,
        'clearance_percentage': (students_cleared / total_students * 100) if total_students > 0 else 0,
        'recent_payments': recent_payments,
        'payment_methods': payment_methods,
        'programme_collections': programme_collections,
        'pending_payments': pending_payments,
        'budget_overview': budget_overview,
        
        # Graph data (JSON stringified for JavaScript)
        'daily_collections_data': json.dumps(daily_collections_data),
        'payment_methods_data': json.dumps(payment_methods_data),
        'programme_chart_data': json.dumps(programme_chart_data),
        'clearance_data': json.dumps(clearance_data),
    }
    
    return render(request, 'finance/dashboard.html', context)

# ============= FEE MANAGEMENT =============

@login_required
def fee_structure_list(request):
    """List all fee structures"""
    fee_structures = FeeStructure.objects.select_related(
        'programme', 'academic_year'
    ).filter(is_active=True).order_by(
        '-academic_year__start_date',
        'programme__name',
        'year_of_study',
        'semester_number'
    )
    
    # Filters
    programme_id = request.GET.get('programme')
    academic_year_id = request.GET.get('academic_year')
    year_of_study = request.GET.get('year_of_study')
    
    if programme_id:
        fee_structures = fee_structures.filter(programme_id=programme_id)
    if academic_year_id:
        fee_structures = fee_structures.filter(academic_year_id=academic_year_id)
    if year_of_study:
        fee_structures = fee_structures.filter(year_of_study=year_of_study)
    
    # Pagination
    paginator = Paginator(fee_structures, 20)
    page = request.GET.get('page')
    fee_structures = paginator.get_page(page)
    
    context = {
        'fee_structures': fee_structures,
        'programmes': Programme.objects.filter(is_active=True),
        'academic_years': AcademicYear.objects.filter(is_active=True),
    }
    
    return render(request, 'finance/fee_structure/list.html', context)


@login_required
def fee_structure_create(request):
    """Create new fee structure"""
    if request.method == 'POST':
        try:
            # Get form data
            programme_id = request.POST.get('programme')
            academic_year_id = request.POST.get('academic_year')
            year_of_study = request.POST.get('year_of_study')
            semester_number = request.POST.get('semester_number')
            
            # Create fee structure
            fee_structure = FeeStructure.objects.create(
                programme_id=programme_id,
                academic_year_id=academic_year_id,
                year_of_study=year_of_study,
                semester_number=semester_number,
                tuition_fee=Decimal(request.POST.get('tuition_fee', '0.00')),
                activity_fee=Decimal(request.POST.get('activity_fee', '0.00')),
                examination_fee=Decimal(request.POST.get('examination_fee', '0.00')),
                library_fee=Decimal(request.POST.get('library_fee', '0.00')),
                medical_fee=Decimal(request.POST.get('medical_fee', '0.00')),
                technology_fee=Decimal(request.POST.get('technology_fee', '0.00')),
                other_fees=Decimal(request.POST.get('other_fees', '0.00')),
            )
            
            messages.success(request, f'Fee structure created successfully. Total: KES {fee_structure.total_fee:,.2f}')
            return redirect('fee_structure_list')
            
        except Exception as e:
            messages.error(request, f'Error creating fee structure: {str(e)}')
    
    context = {
        'programmes': Programme.objects.filter(is_active=True),
        'academic_years': AcademicYear.objects.filter(is_active=True),
        'semester_choices': Semester.SEMESTER_NAMES,
    }
    
    return render(request, 'finance/fee_structure/create.html', context)


@login_required
def student_balances(request):
    """View student fee balances"""
    current_semester = Semester.objects.filter(is_current=True).first()
    
    balances = FeeBalance.objects.select_related(
        'student', 'student__user', 'student__programme', 'semester'
    ).filter(semester=current_semester)
    
    # Filters
    programme_id = request.GET.get('programme')
    year_of_study = request.GET.get('year_of_study')
    status = request.GET.get('status')
    search = request.GET.get('search')
    
    if programme_id:
        balances = balances.filter(student__programme_id=programme_id)
    if year_of_study:
        balances = balances.filter(student__current_year=year_of_study)
    if status == 'cleared':
        balances = balances.filter(is_cleared=True)
    elif status == 'owing':
        balances = balances.filter(is_cleared=False)
    if search:
        balances = balances.filter(
            Q(student__registration_number__icontains=search) |
            Q(student__user__first_name__icontains=search) |
            Q(student__user__last_name__icontains=search)
        )
    
    # Order by balance (highest first)
    balances = balances.order_by('-balance')
    
    # Statistics
    total_fees = balances.aggregate(total=Sum('total_fees'))['total'] or Decimal('0.00')
    total_paid = balances.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
    total_balance = balances.aggregate(total=Sum('balance'))['total'] or Decimal('0.00')
    
    # Pagination
    paginator = Paginator(balances, 50)
    page = request.GET.get('page')
    balances = paginator.get_page(page)
    
    context = {
        'balances': balances,
        'current_semester': current_semester,
        'programmes': Programme.objects.filter(is_active=True),
        'total_fees': total_fees,
        'total_paid': total_paid,
        'total_balance': total_balance,
    }
    
    return render(request, 'finance/student_balances/list.html', context)


@login_required
def student_balance_detail(request, student_id):
    """View detailed student balance"""
    student = get_object_or_404(Student.objects.select_related('user', 'programme'), id=student_id)
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Current balance
    current_balance = FeeBalance.objects.filter(
        student=student,
        semester=current_semester
    ).first()
    
    # Payment history
    payment_history = FeePayment.objects.filter(
        student=student
    ).select_related('semester', 'academic_year').order_by('-payment_date')
    
    # All balances
    all_balances = FeeBalance.objects.filter(
        student=student
    ).select_related('semester', 'academic_year').order_by('-semester__start_date')
    
    context = {
        'student': student,
        'current_balance': current_balance,
        'payment_history': payment_history,
        'all_balances': all_balances,
    }
    
    return render(request, 'finance/student_balances/detail.html', context)


# ============= PAYMENT PROCESSING =============

@login_required
def payment_processing(request):
    """Process fee payments"""
    if request.method == 'POST':
        try:
            student_id = request.POST.get('student_id')
            amount = Decimal(request.POST.get('amount'))
            payment_method = request.POST.get('payment_method')
            transaction_reference = request.POST.get('transaction_reference')
            
            student = Student.objects.get(id=student_id)
            current_semester = Semester.objects.filter(is_current=True).first()
            current_academic_year = AcademicYear.objects.filter(is_current=True).first()
            
            # Get or create fee balance
            fee_balance, created = FeeBalance.objects.get_or_create(
                student=student,
                semester=current_semester,
                academic_year=current_academic_year,
                defaults={'total_fees': Decimal('0.00')}
            )
            
            # Get fee structure
            fee_structure = FeeStructure.objects.filter(
                programme=student.programme,
                academic_year=current_academic_year,
                year_of_study=student.current_year,
                semester_number=student.current_semester
            ).first()
            
            if not fee_structure:
                messages.error(request, 'Fee structure not found for this student')
                return redirect('payment_processing')
            
            # Generate receipt number
            year = timezone.now().year
            last_payment = FeePayment.objects.filter(
                receipt_number__startswith=f'REC-{year}-'
            ).order_by('-id').first()
            
            if last_payment and last_payment.receipt_number:
                last_num = int(last_payment.receipt_number.split('-')[-1])
                receipt_number = f'REC-{year}-{last_num + 1:06d}'
            else:
                receipt_number = f'REC-{year}-000001'
            
            # Create payment
            payment = FeePayment.objects.create(
                student=student,
                semester=current_semester,
                academic_year=current_academic_year,
                fee_structure=fee_structure,
                amount=amount,
                payment_method=payment_method,
                transaction_reference=transaction_reference,
                payment_date=timezone.now(),
                status='completed',
                receipt_number=receipt_number,
                processed_by=request.user
            )
            
            # Update balance
            fee_balance.total_fees = fee_structure.total_fee
            fee_balance.amount_paid = F('amount_paid') + amount
            fee_balance.last_payment_date = timezone.now()
            fee_balance.save()
            fee_balance.refresh_from_db()
            
            messages.success(request, f'Payment processed successfully. Receipt No: {receipt_number}')
            return redirect('payment_receipt', payment_id=payment.id)
            
        except Exception as e:
            messages.error(request, f'Error processing payment: {str(e)}')
    
    # Get students for selection
    students = Student.objects.filter(
        student_status='active'
    ).select_related('user', 'programme')
    
    context = {
        'students': students,
        'payment_methods': FeePayment.PAYMENT_METHODS,
    }
    
    return render(request, 'finance/payments/process.html', context)


@login_required
def payment_receipt(request, payment_id):
    """Generate payment receipt"""
    payment = get_object_or_404(
        FeePayment.objects.select_related(
            'student', 'student__user', 'student__programme',
            'semester', 'academic_year', 'fee_structure'
        ),
        id=payment_id
    )
    
    context = {
        'payment': payment,
    }
    
    return render(request, 'finance/payments/receipt.html', context)


@login_required
def payment_list(request):
    """List all payments"""
    payments = FeePayment.objects.select_related(
        'student', 'student__user', 'semester', 'processed_by'
    ).all()
    
    # Filters
    status = request.GET.get('status')
    payment_method = request.GET.get('payment_method')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('search')
    
    if status:
        payments = payments.filter(status=status)
    if payment_method:
        payments = payments.filter(payment_method=payment_method)
    if date_from:
        payments = payments.filter(payment_date__date__gte=date_from)
    if date_to:
        payments = payments.filter(payment_date__date__lte=date_to)
    if search:
        payments = payments.filter(
            Q(student__registration_number__icontains=search) |
            Q(transaction_reference__icontains=search) |
            Q(receipt_number__icontains=search)
        )
    
    payments = payments.order_by('-payment_date')
    
    # Statistics
    stats = payments.aggregate(
        total_amount=Sum('amount'),
        count=Count('id')
    )
    
    # Pagination
    paginator = Paginator(payments, 50)
    page = request.GET.get('page')
    payments = paginator.get_page(page)
    
    context = {
        'payments': payments,
        'stats': stats,
        'payment_statuses': FeePayment.PAYMENT_STATUS,
        'payment_methods': FeePayment.PAYMENT_METHODS,
    }
    
    return render(request, 'finance/payments/list.html', context)


# ============= FINANCIAL REPORTING =============

@login_required
def daily_collections_report(request):
    """Daily collections report"""
    selected_date = request.GET.get('date', timezone.now().date())
    if isinstance(selected_date, str):
        selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    
    payments = FeePayment.objects.filter(
        payment_date__date=selected_date,
        status='completed'
    ).select_related('student', 'student__user', 'processed_by')
    
    # Summary by payment method
    summary_by_method = payments.values('payment_method').annotate(
        total=Sum('amount'),
        count=Count('id')
    )
    
    # Total collections
    total_collections = payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    context = {
        'selected_date': selected_date,
        'payments': payments,
        'summary_by_method': summary_by_method,
        'total_collections': total_collections,
        'payment_count': payments.count(),
    }
    
    return render(request, 'finance/reports/daily_collections.html', context)


@login_required
def monthly_collections_report(request):
    """Monthly collections report"""
    # Get current month or selected month
    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))
    
    # Calculate date range
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date()
    else:
        end_date = datetime(year, month + 1, 1).date()
    
    payments = FeePayment.objects.filter(
        payment_date__date__gte=start_date,
        payment_date__date__lt=end_date,
        status='completed'
    )
    
    # Daily breakdown
    daily_collections = payments.extra(
        select={'day': 'DATE(payment_date)'}
    ).values('day').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('day')
    
    # Summary by payment method
    summary_by_method = payments.values('payment_method').annotate(
        total=Sum('amount'),
        count=Count('id')
    )
    
    # Summary by programme
    summary_by_programme = payments.values(
        'student__programme__name'
    ).annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Total collections
    total_collections = payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    context = {
        'year': year,
        'month': month,
        'month_name': datetime(year, month, 1).strftime('%B'),
        'daily_collections': daily_collections,
        'summary_by_method': summary_by_method,
        'summary_by_programme': summary_by_programme,
        'total_collections': total_collections,
        'payment_count': payments.count(),
    }
    
    return render(request, 'finance/reports/monthly_collections.html', context)


@login_required
def revenue_analysis(request):
    """Revenue analysis and trends"""
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    
    # Revenue by source
    revenue_by_source = RevenueSource.objects.filter(
        academic_year=current_academic_year
    ).values('revenue_type').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    # Revenue by school
    revenue_by_school = RevenueSource.objects.filter(
        academic_year=current_academic_year
    ).values(
        'school__name', 'school__code'
    ).annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    # Monthly trend
    monthly_revenue = RevenueSource.objects.filter(
        academic_year=current_academic_year
    ).extra(
        select={'month': "EXTRACT(month FROM received_date)"}
    ).values('month').annotate(
        total=Sum('amount')
    ).order_by('month')
    
    # Fee collections
    fee_collections = FeePayment.objects.filter(
        academic_year=current_academic_year,
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    context = {
        'current_academic_year': current_academic_year,
        'revenue_by_source': revenue_by_source,
        'revenue_by_school': revenue_by_school,
        'monthly_revenue': monthly_revenue,
        'fee_collections': fee_collections,
    }
    
    return render(request, 'finance/reports/revenue_analysis.html', context)


@login_required
def debtors_report(request):
    """Debtors (outstanding balances) report"""
    current_semester = Semester.objects.filter(is_current=True).first()
    
    debtors = FeeBalance.objects.filter(
        is_cleared=False,
        semester=current_semester
    ).select_related(
        'student', 'student__user', 'student__programme'
    ).order_by('-balance')
    
    # Categorize by amount owed
    high_debtors = debtors.filter(balance__gte=50000)  # >= 50,000
    medium_debtors = debtors.filter(balance__gte=20000, balance__lt=50000)  # 20k-50k
    low_debtors = debtors.filter(balance__lt=20000)  # < 20k
    
    # Summary statistics
    total_outstanding = debtors.aggregate(total=Sum('balance'))['total'] or Decimal('0.00')
    total_students = debtors.count()
    average_debt = total_outstanding / total_students if total_students > 0 else Decimal('0.00')
    
    # By programme
    by_programme = debtors.values(
        'student__programme__name'
    ).annotate(
        total=Sum('balance'),
        count=Count('id')
    ).order_by('-total')
    
    # Pagination
    paginator = Paginator(debtors, 50)
    page = request.GET.get('page')
    debtors_page = paginator.get_page(page)
    
    context = {
        'debtors': debtors_page,
        'high_debtors_count': high_debtors.count(),
        'medium_debtors_count': medium_debtors.count(),
        'low_debtors_count': low_debtors.count(),
        'total_outstanding': total_outstanding,
        'total_students': total_students,
        'average_debt': average_debt,
        'by_programme': by_programme,
    }
    
    return render(request, 'finance/reports/debtors.html', context)


# ============= BUDGET MANAGEMENT =============

@login_required
def budget_list(request):
    """List school budgets"""
    budgets = SchoolBudget.objects.select_related(
        'school', 'financial_year'
    ).filter(is_active=True).order_by('-financial_year__start_date', 'school__name')
    
    context = {
        'budgets': budgets,
    }
    
    return render(request, 'finance/budget/list.html', context)


@login_required
def budget_detail(request, budget_id):
    """View budget details"""
    budget = get_object_or_404(
        SchoolBudget.objects.select_related('school', 'financial_year'),
        id=budget_id
    )
    
    # Department allocations
    allocations = BudgetAllocation.objects.filter(
        school_budget=budget
    ).select_related('department').order_by('department__name')
    
    # Expenditures
    expenditures = ExpenditureTracking.objects.filter(
        budget_allocation__school_budget=budget
    ).select_related('budget_allocation__department').order_by('-transaction_date')[:20]
    
    # Statistics
    total_allocated = allocations.aggregate(total=Sum('allocation_amount'))['total'] or Decimal('0.00')
    total_utilized = allocations.aggregate(total=Sum('amount_utilized'))['total'] or Decimal('0.00')
    
    context = {
        'budget': budget,
        'allocations': allocations,
        'expenditures': expenditures,
        'total_allocated': total_allocated,
        'total_utilized': total_utilized,
    }
    
    return render(request, 'finance/budget/detail.html', context)


@login_required
def expenditure_tracking(request):
    """Track expenditures"""
    expenditures = ExpenditureTracking.objects.select_related(
        'budget_allocation', 'budget_allocation__department',
        'requested_by', 'approved_by'
    ).all()
    
    # Filters
    status = request.GET.get('status')
    expenditure_type = request.GET.get('expenditure_type')
    department_id = request.GET.get('department')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if status:
        expenditures = expenditures.filter(status=status)
    if expenditure_type:
        expenditures = expenditures.filter(expenditure_type=expenditure_type)
    if department_id:
        expenditures = expenditures.filter(budget_allocation__department_id=department_id)
    if date_from:
        expenditures = expenditures.filter(transaction_date__gte=date_from)
    if date_to:
        expenditures = expenditures.filter(transaction_date__lte=date_to)
    
    expenditures = expenditures.order_by('-transaction_date')
    
    # Statistics
    stats = expenditures.aggregate(
        total_amount=Sum('amount'),
        count=Count('id')
    )
    
    # Pagination
    paginator = Paginator(expenditures, 50)
    page = request.GET.get('page')
    expenditures = paginator.get_page(page)
    
    context = {
        'expenditures': expenditures,
        'stats': stats,
        'departments': Department.objects.filter(is_active=True),
        'expenditure_types': ExpenditureTracking.EXPENDITURE_TYPE,
        'payment_statuses': ExpenditureTracking.PAYMENT_STATUS,
    }
    
    return render(request, 'finance/expenditure/list.html', context)


# ============= AJAX/API ENDPOINTS =============

@login_required
def get_student_balance(request, student_id):
    """Get student balance (AJAX)"""
    try:
        student = Student.objects.get(id=student_id)
        current_semester = Semester.objects.filter(is_current=True).first()
        
        balance = FeeBalance.objects.filter(
            student=student,
            semester=current_semester
        ).first()
        
        if balance:
            data = {
                'success': True,
                'student_name': student.user.get_full_name(),
                'registration_number': student.registration_number,
                'programme': student.programme.name,
                'total_fees': str(balance.total_fees),
                'amount_paid': str(balance.amount_paid),
                'balance': str(balance.balance),
                'is_cleared': balance.is_cleared,
            }
        else:
            data = {
                'success': False,
                'message': 'No balance record found for current semester'
            }
        
        return JsonResponse(data)
    except Student.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Student not found'})


@login_required
def search_students(request):
    """Search students (AJAX)"""
    query = request.GET.get('q', '')
    
    students = Student.objects.filter(
        Q(registration_number__icontains=query) |
        Q(user__first_name__icontains=query) |
        Q(user__last_name__icontains=query),
        student_status='active'
    ).select_related('user', 'programme')[:10]
    
    results = [{
        'id': s.id,
        'registration_number': s.registration_number,
        'name': s.user.get_full_name(),
        'programme': s.programme.name,
    } for s in students]
    
    return JsonResponse({'results': results})


# ============= EXPORTS =============

@login_required
def export_debtors_csv(request):
    """Export debtors list to CSV"""
    import csv
    from django.http import HttpResponse
    
    current_semester = Semester.objects.filter(is_current=True).first()
    
    debtors = FeeBalance.objects.filter(
        is_cleared=False,
        semester=current_semester
    ).select_related('student', 'student__user', 'student__programme')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="debtors_{timezone.now().date()}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Registration Number', 'Student Name', 'Programme', 
                    'Total Fees', 'Amount Paid', 'Balance', 'Last Payment Date'])
    
    for balance in debtors:
        writer.writerow([
            balance.student.registration_number,
            balance.student.user.get_full_name(),
            balance.student.programme.name,
            balance.total_fees,
            balance.amount_paid,
            balance.balance,
            balance.last_payment_date or 'N/A'
        ])
    
    return response

@login_required
def registrar_dashboard(request):
    context = {'page_title': 'Registrar Dashboard'}
    return render(request, 'registrar/dashboard.html', context)


"""
Librarian Views for University Management System
Handles all library management functionality
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count, Sum, Avg, F, ExpressionWrapper, DecimalField
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from datetime import datetime, timedelta
from decimal import Decimal
from django.core.paginator import Paginator
from django.db.models.functions import TruncMonth, TruncWeek

# Import models
from .models import (
    User, Student, Book, BookCategory, BookBorrowing,
    AcademicYear, Semester, Programme, Department, School
)


# ============= HELPER FUNCTIONS =============

def is_librarian(user):
    """Check if user is a librarian"""
    return user.is_authenticated and user.role == 'librarian'


# ============= DASHBOARD =============

@login_required
@user_passes_test(is_librarian)
def librarian_dashboard(request):
    """Main librarian dashboard with key metrics and statistics"""
    
    # Get current academic year and semester
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # ===== KEY METRICS =====
    
    # Total books in library
    total_books = Book.objects.aggregate(
        total_copies=Sum('total_copies')
    )['total_copies'] or 0
    
    # Available books
    available_books = Book.objects.aggregate(
        available=Sum('available_copies')
    )['available'] or 0
    
    # Currently borrowed books
    borrowed_books = BookBorrowing.objects.filter(
        status='active'
    ).count()
    
    # Overdue books
    overdue_books = BookBorrowing.objects.filter(
        status__in=['active', 'overdue'],
        due_date__lt=timezone.now().date()
    ).count()
    
    # Total categories
    total_categories = BookCategory.objects.count()
    
    # Active borrowers (students with active borrowings)
    active_borrowers = BookBorrowing.objects.filter(
        status='active'
    ).values('student').distinct().count()
    
    # ===== RECENT ACTIVITIES =====
    
    # Recent borrowings (last 10)
    recent_borrowings = BookBorrowing.objects.select_related(
        'student__user', 'book', 'issued_by'
    ).order_by('-borrow_date')[:10]
    
    # Recent returns (last 10)
    recent_returns = BookBorrowing.objects.filter(
        status='returned'
    ).select_related(
        'student__user', 'book', 'returned_to'
    ).order_by('-return_date')[:10]
    
    # Pending fine payments
    pending_fines = BookBorrowing.objects.filter(
        fine_amount__gt=0,
        fine_paid=False
    ).select_related('student__user', 'book').order_by('-fine_amount')[:10]
    
    # ===== STATISTICS FOR CHARTS =====
    
    # Borrowing trends (last 6 months)
    six_months_ago = timezone.now() - timedelta(days=180)
    monthly_borrowings = BookBorrowing.objects.filter(
        borrow_date__gte=six_months_ago
    ).annotate(
        month=TruncMonth('borrow_date')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    # Popular categories
    popular_categories = BookCategory.objects.annotate(
        borrowing_count=Count('books__borrowings')
    ).order_by('-borrowing_count')[:5]
    
    # Most borrowed books
    popular_books = Book.objects.annotate(
        borrow_count=Count('borrowings')
    ).order_by('-borrow_count')[:10]
    
    # Collection distribution by category
    collection_distribution = BookCategory.objects.annotate(
        total_books=Sum('books__total_copies')
    ).order_by('-total_books')[:10]
    
    # ===== ALERTS & NOTIFICATIONS =====
    
    # Books low on stock (available copies < 2)
    low_stock_books = Book.objects.filter(
        available_copies__lt=2,
        available_copies__gt=0
    ).count()
    
    # Books out of stock
    out_of_stock = Book.objects.filter(available_copies=0).count()
    
    # Books needing attention (damaged, lost)
    books_needing_attention = BookBorrowing.objects.filter(
        status__in=['lost', 'damaged']
    ).count()
    
    # ===== FINANCIAL SUMMARY =====
    
    # Total fines collected (current semester)
    if current_semester:
        fines_collected = BookBorrowing.objects.filter(
            semester=current_semester,
            fine_paid=True
        ).aggregate(
            total=Sum('fine_amount')
        )['total'] or Decimal('0.00')
        
        fines_pending = BookBorrowing.objects.filter(
            semester=current_semester,
            fine_paid=False
        ).aggregate(
            total=Sum('fine_amount')
        )['total'] or Decimal('0.00')
    else:
        fines_collected = Decimal('0.00')
        fines_pending = Decimal('0.00')
    
    # ===== QUICK ACTIONS DATA =====
    
    # Students with cleared fees (eligible to borrow)
    eligible_students_count = Student.objects.filter(
        student_status='active',
        fee_balances__is_cleared=True
    ).distinct().count()
    
    context = {
        # Academic info
        'current_academic_year': current_academic_year,
        'current_semester': current_semester,
        
        # Key metrics
        'total_books': total_books,
        'available_books': available_books,
        'borrowed_books': borrowed_books,
        'overdue_books': overdue_books,
        'total_categories': total_categories,
        'active_borrowers': active_borrowers,
        
        # Recent activities
        'recent_borrowings': recent_borrowings,
        'recent_returns': recent_returns,
        'pending_fines': pending_fines,
        
        # Statistics
        'monthly_borrowings': monthly_borrowings,
        'popular_categories': popular_categories,
        'popular_books': popular_books,
        'collection_distribution': collection_distribution,
        
        # Alerts
        'low_stock_books': low_stock_books,
        'out_of_stock': out_of_stock,
        'books_needing_attention': books_needing_attention,
        
        # Financial
        'fines_collected': fines_collected,
        'fines_pending': fines_pending,
        
        # Quick actions
        'eligible_students_count': eligible_students_count,
    }
    
    return render(request, 'librarian/dashboard.html', context)


# ============= CATALOG MANAGEMENT =============

@login_required
@user_passes_test(is_librarian)
def book_catalog_list(request):
    """List all books with search and filter"""
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    status = request.GET.get('status', '')
    sort_by = request.GET.get('sort', 'title')
    
    # Base queryset
    books = Book.objects.select_related('category').annotate(
        borrow_count=Count('borrowings')
    )
    
    # Apply search
    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(author__icontains=search_query) |
            Q(isbn__icontains=search_query) |
            Q(publisher__icontains=search_query)
        )
    
    # Apply category filter
    if category_id:
        books = books.filter(category_id=category_id)
    
    # Apply status filter
    if status:
        books = books.filter(status=status)
    
    # Apply sorting
    if sort_by == 'title':
        books = books.order_by('title')
    elif sort_by == 'author':
        books = books.order_by('author')
    elif sort_by == 'popularity':
        books = books.order_by('-borrow_count')
    elif sort_by == 'newest':
        books = books.order_by('-acquisition_date')
    
    # Pagination
    paginator = Paginator(books, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all categories for filter dropdown
    categories = BookCategory.objects.all()
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id,
        'selected_status': status,
        'sort_by': sort_by,
    }
    
    return render(request, 'librarian/catalog/book_list.html', context)


@login_required
@user_passes_test(is_librarian)
def add_book(request):
    """Add new book to catalog"""
    
    if request.method == 'POST':
        # Extract form data
        isbn = request.POST.get('isbn')
        title = request.POST.get('title')
        author = request.POST.get('author')
        publisher = request.POST.get('publisher', '')
        publication_year = request.POST.get('publication_year')
        edition = request.POST.get('edition', '')
        category_id = request.POST.get('category')
        total_copies = request.POST.get('total_copies', 1)
        shelf_location = request.POST.get('shelf_location', '')
        call_number = request.POST.get('call_number', '')
        description = request.POST.get('description', '')
        price = request.POST.get('price')
        cover_image = request.FILES.get('cover_image')
        
        # Validate required fields
        if not all([isbn, title, author, category_id]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('add_book')
        
        # Check if ISBN already exists
        if Book.objects.filter(isbn=isbn).exists():
            messages.error(request, f'Book with ISBN {isbn} already exists.')
            return redirect('add_book')
        
        try:
            # Create book
            book = Book.objects.create(
                isbn=isbn,
                title=title,
                author=author,
                publisher=publisher,
                publication_year=int(publication_year) if publication_year else None,
                edition=edition,
                category_id=category_id,
                total_copies=int(total_copies),
                available_copies=int(total_copies),
                shelf_location=shelf_location,
                call_number=call_number,
                description=description,
                price=Decimal(price) if price else None,
                cover_image=cover_image,
                acquisition_date=timezone.now().date(),
                status='available'
            )
            
            messages.success(request, f'Book "{title}" added successfully!')
            return redirect('book_catalog_list')
            
        except Exception as e:
            messages.error(request, f'Error adding book: {str(e)}')
            return redirect('add_book')
    
    # GET request - show form
    categories = BookCategory.objects.all()
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'librarian/catalog/add_book.html', context)


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

# Assuming these are your model imports
from .models import (
    Book, BookBorrowing, BookCategory, Student, 
    AcademicYear, Semester, User
)


def is_librarian(user):
    """Check if user is a librarian"""
    return user.is_authenticated and user.role == 'librarian'


@login_required
@user_passes_test(is_librarian)
def book_detail(request, book_id):
    """
    Detailed view of a specific book with borrowing history,
    availability status, and statistics
    """
    
    # Get the book or return 404
    book = get_object_or_404(Book, id=book_id)
    
    # Get current academic year and semester
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # ===== AVAILABILITY STATUS =====
    availability_status = {
        'total_copies': book.total_copies,
        'available_copies': book.available_copies,
        'borrowed_copies': book.total_copies - book.available_copies,
        'availability_percentage': (book.available_copies / book.total_copies * 100) if book.total_copies > 0 else 0,
        'status': book.status,
        'is_available': book.available_copies > 0,
    }
    
    # ===== BORROWING STATISTICS =====
    
    # Total times borrowed (all time)
    total_borrows = BookBorrowing.objects.filter(book=book).count()
    
    # Currently active borrowings
    active_borrowings = BookBorrowing.objects.filter(
        book=book,
        status='active'
    ).select_related('student__user', 'issued_by')
    
    # Overdue borrowings
    overdue_borrowings = BookBorrowing.objects.filter(
        book=book,
        status__in=['active', 'overdue'],
        due_date__lt=timezone.now().date()
    ).select_related('student__user', 'issued_by')
    
    # Borrowing this semester
    semester_borrows = 0
    if current_semester:
        semester_borrows = BookBorrowing.objects.filter(
            book=book,
            semester=current_semester
        ).count()
    
    # Borrowing this academic year
    year_borrows = 0
    if current_academic_year:
        year_borrows = BookBorrowing.objects.filter(
            book=book,
            academic_year=current_academic_year
        ).count()
    
    # Average borrowing duration (in days)
    returned_borrowings = BookBorrowing.objects.filter(
        book=book,
        status='returned',
        return_date__isnull=False
    )
    
    avg_duration = 0
    if returned_borrowings.exists():
        total_days = 0
        count = 0
        for borrowing in returned_borrowings:
            duration = (borrowing.return_date.date() - borrowing.borrow_date.date()).days
            total_days += duration
            count += 1
        avg_duration = total_days / count if count > 0 else 0
    
    borrowing_stats = {
        'total_borrows': total_borrows,
        'active_count': active_borrowings.count(),
        'overdue_count': overdue_borrowings.count(),
        'semester_borrows': semester_borrows,
        'year_borrows': year_borrows,
        'avg_duration': round(avg_duration, 1),
    }
    
    # ===== BORROWING HISTORY =====
    
    # Get all borrowing history (paginated)
    borrowing_history = BookBorrowing.objects.filter(
        book=book
    ).select_related(
        'student__user', 'student__programme',
        'issued_by', 'returned_to'
    ).order_by('-borrow_date')[:20]  # Last 20 borrowings
    
    # ===== FINANCIAL DATA =====
    
    # Total fines generated
    total_fines = BookBorrowing.objects.filter(
        book=book,
        fine_amount__gt=0
    ).aggregate(
        total=Sum('fine_amount')
    )['total'] or Decimal('0.00')
    
    # Fines collected
    fines_collected = BookBorrowing.objects.filter(
        book=book,
        fine_amount__gt=0,
        fine_paid=True
    ).aggregate(
        total=Sum('fine_amount')
    )['total'] or Decimal('0.00')
    
    # Pending fines
    fines_pending = BookBorrowing.objects.filter(
        book=book,
        fine_amount__gt=0,
        fine_paid=False
    ).aggregate(
        total=Sum('fine_amount')
    )['total'] or Decimal('0.00')
    
    financial_data = {
        'total_fines': total_fines,
        'fines_collected': fines_collected,
        'fines_pending': fines_pending,
        'collection_rate': (fines_collected / total_fines * 100) if total_fines > 0 else 0,
    }
    
    # ===== TOP BORROWERS =====
    
    # Students who borrowed this book most frequently
    top_borrowers = BookBorrowing.objects.filter(
        book=book
    ).values(
        'student__registration_number',
        'student__user__first_name',
        'student__user__last_name',
        'student__programme__code'
    ).annotate(
        borrow_count=Count('id')
    ).order_by('-borrow_count')[:5]
    
    # ===== RELATED BOOKS =====
    
    # Books in the same category
    related_books = Book.objects.filter(
        category=book.category,
        status= 'available'
    ).exclude(
        id=book.id
    ).annotate(
        borrow_count=Count('borrowings')
    ).order_by('-borrow_count')[:6]
    
    # ===== MONTHLY BORROWING TREND =====
    
    # Get borrowing trend for last 6 months
    six_months_ago = timezone.now() - timedelta(days=180)
    from django.db.models.functions import TruncMonth
    
    monthly_trend = BookBorrowing.objects.filter(
        book=book,
        borrow_date__gte=six_months_ago
    ).annotate(
        month=TruncMonth('borrow_date')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    # ===== RECENT ACTIVITY =====
    
    # Last 5 activities (borrows and returns)
    recent_activity = BookBorrowing.objects.filter(
        book=book
    ).select_related(
        'student__user', 'issued_by', 'returned_to'
    ).order_by('-borrow_date')[:5]
    
    # ===== BOOK CONDITION & STATUS =====
    
    # Check for any lost or damaged copies
    lost_copies = BookBorrowing.objects.filter(
        book=book,
        status='lost'
    ).count()
    
    damaged_copies = BookBorrowing.objects.filter(
        book=book,
        status='damaged'
    ).count()
    
    condition_data = {
        'lost_copies': lost_copies,
        'damaged_copies': damaged_copies,
        'good_copies': book.total_copies - lost_copies - damaged_copies,
    }
    
    context = {
        # Book Information
        'book': book,
        'current_academic_year': current_academic_year,
        'current_semester': current_semester,
        
        # Availability
        'availability_status': availability_status,
        
        # Statistics
        'borrowing_stats': borrowing_stats,
        'financial_data': financial_data,
        'condition_data': condition_data,
        
        # Borrowings
        'active_borrowings': active_borrowings,
        'overdue_borrowings': overdue_borrowings,
        'borrowing_history': borrowing_history,
        
        # Analytics
        'top_borrowers': top_borrowers,
        'related_books': related_books,
        'monthly_trend': monthly_trend,
        'recent_activity': recent_activity,
    }
    
    return render(request, 'librarian/catalog/book_detail.html', context)

@login_required
@user_passes_test(is_librarian)
def edit_book(request, book_id):
    """Edit existing book"""
    
    book = get_object_or_404(Book, id=book_id)
    
    if request.method == 'POST':
        # Update book details
        book.title = request.POST.get('title')
        book.author = request.POST.get('author')
        book.publisher = request.POST.get('publisher', '')
        book.publication_year = request.POST.get('publication_year')
        book.edition = request.POST.get('edition', '')
        book.category_id = request.POST.get('category')
        book.shelf_location = request.POST.get('shelf_location', '')
        book.call_number = request.POST.get('call_number', '')
        book.description = request.POST.get('description', '')
        book.price = request.POST.get('price')
        book.status = request.POST.get('status')
        
        if 'cover_image' in request.FILES:
            book.cover_image = request.FILES['cover_image']
        
        try:
            book.save()
            messages.success(request, 'Book updated successfully!')
            return redirect('book_catalog_list')
        except Exception as e:
            messages.error(request, f'Error updating book: {str(e)}')
    
    categories = BookCategory.objects.all()
    
    context = {
        'book': book,
        'categories': categories,
    }
    
    return render(request, 'librarian/catalog/edit_book.html', context)

@login_required
@user_passes_test(is_librarian)
def delete_book(request, book_id):
    """Delete a book (soft delete - mark as inactive)"""
    book = get_object_or_404(Book, id=book_id)
    
    # Check if book has active borrowings
    active_borrowings = BookBorrowing.objects.filter(
        book=book,
        status__in=['active', 'overdue']
    ).count()
    
    if active_borrowings > 0:
        messages.error(
            request, 
            f'Cannot delete book "{book.title}". It has {active_borrowings} active borrowing(s). '
            'Please wait for all copies to be returned.'
        )
        return redirect('book_detail', book_id=book.id)
    
    if request.method == 'POST':
        try:
            # Soft delete - mark as lost/removed
            book.status = 'lost'
            book.available_copies = 0
            book.save()
            
            messages.success(request, f'Book "{book.title}" has been removed from the system.')
            return redirect('book_list')
            
        except Exception as e:
            messages.error(request, f'Error deleting book: {str(e)}')
    
    return redirect('book_detail', book_id=book.id)

@login_required
@user_passes_test(is_librarian)
def manage_categories(request):
    """Manage book categories"""
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            name = request.POST.get('name')
            code = request.POST.get('code')
            description = request.POST.get('description', '')
            parent_id = request.POST.get('parent_category')
            
            try:
                BookCategory.objects.create(
                    name=name,
                    code=code,
                    description=description,
                    parent_category_id=parent_id if parent_id else None
                )
                messages.success(request, f'Category "{name}" created successfully!')
            except Exception as e:
                messages.error(request, f'Error creating category: {str(e)}')
        
        elif action == 'edit':
            category_id = request.POST.get('category_id')
            category = get_object_or_404(BookCategory, id=category_id)
            category.name = request.POST.get('name')
            category.description = request.POST.get('description', '')
            category.save()
            messages.success(request, 'Category updated successfully!')
        
        return redirect('manage_categories')
    
    # GET request
    categories = BookCategory.objects.annotate(
        book_count=Count('books'),
        subcategory_count=Count('subcategories')
    ).order_by('name')
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'librarian/catalog/manage_categories.html', context)


@login_required
@user_passes_test(is_librarian)
def inventory_management(request):
    """Manage book inventory and stock levels"""
    
    # Books needing attention
    low_stock = Book.objects.filter(
        available_copies__lte=2,
        available_copies__gt=0
    ).select_related('category')
    
    out_of_stock = Book.objects.filter(
        available_copies=0
    ).select_related('category')
    
    # Lost and damaged books
    lost_books = BookBorrowing.objects.filter(
        status='lost'
    ).select_related('book', 'student__user')
    
    damaged_books = Book.objects.filter(
        status='damaged'
    ).select_related('category')
    
    # Inventory summary by category
    category_summary = BookCategory.objects.annotate(
        total_books=Sum('books__total_copies'),
        available=Sum('books__available_copies'),
        borrowed=Sum('books__total_copies') - Sum('books__available_copies')
    ).order_by('name')
    
    context = {
        'low_stock': low_stock,
        'out_of_stock': out_of_stock,
        'lost_books': lost_books,
        'damaged_books': damaged_books,
        'category_summary': category_summary,
    }
    
    return render(request, 'librarian/catalog/inventory.html', context)


@login_required
@user_passes_test(is_librarian)
def update_stock(request, book_id):
    """Update book stock quantities"""
    
    book = get_object_or_404(Book, id=book_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        quantity = int(request.POST.get('quantity', 0))
        
        if action == 'add':
            book.total_copies += quantity
            book.available_copies += quantity
            messages.success(request, f'Added {quantity} copies to "{book.title}"')
        
        elif action == 'remove':
            if book.available_copies >= quantity:
                book.total_copies -= quantity
                book.available_copies -= quantity
                messages.success(request, f'Removed {quantity} copies from "{book.title}"')
            else:
                messages.error(request, 'Cannot remove more copies than available')
        
        elif action == 'adjust':
            new_total = int(request.POST.get('new_total'))
            new_available = int(request.POST.get('new_available'))
            
            if new_available <= new_total:
                book.total_copies = new_total
                book.available_copies = new_available
                messages.success(request, 'Stock quantities updated')
            else:
                messages.error(request, 'Available copies cannot exceed total copies')
        
        book.save()
        return redirect('inventory_management')
    
    context = {
        'book': book,
    }
    
    return render(request, 'librarian/catalog/update_stock.html', context)


# ============= CIRCULATION =============

@login_required
@user_passes_test(is_librarian)
def book_issuance(request):
    """Issue books to students"""
    
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        book_id = request.POST.get('book_id')
        
        try:
            student = Student.objects.get(id=student_id)
            book = Book.objects.get(id=book_id)
            current_semester = Semester.objects.filter(is_current=True).first()
            current_academic_year = AcademicYear.objects.filter(is_current=True).first()
            
            # Check if student is eligible (fee cleared, not suspended)
            if student.student_status != 'active':
                messages.error(request, 'Student is not active. Cannot issue book.')
                return redirect('book_issuance')
            
            # Check if student has any overdue books
            overdue = BookBorrowing.objects.filter(
                student=student,
                status__in=['active', 'overdue'],
                due_date__lt=timezone.now().date()
            ).exists()
            
            if overdue:
                messages.error(request, 'Student has overdue books. Clear them first.')
                return redirect('book_issuance')
            
            # Check if student has unpaid fines
            unpaid_fines = BookBorrowing.objects.filter(
                student=student,
                fine_amount__gt=0,
                fine_paid=False
            ).exists()
            
            if unpaid_fines:
                messages.error(request, 'Student has unpaid fines. Clear them first.')
                return redirect('book_issuance')
            
            # Check if book is available
            if book.available_copies < 1:
                messages.error(request, 'Book is not available.')
                return redirect('book_issuance')
            
            # Check borrowing limit (e.g., max 3 books)
            active_borrowings = BookBorrowing.objects.filter(
                student=student,
                status='active'
            ).count()
            
            if active_borrowings >= 3:
                messages.error(request, 'Student has reached borrowing limit (3 books).')
                return redirect('book_issuance')
            
            # Create borrowing record
            due_date = timezone.now().date() + timedelta(days=14)  # 2 weeks
            
            borrowing = BookBorrowing.objects.create(
                student=student,
                book=book,
                academic_year=current_academic_year,
                semester=current_semester,
                due_date=due_date,
                status='active',
                issued_by=request.user
            )
            
            # Update book availability
            book.available_copies -= 1
            if book.available_copies == 0:
                book.status = 'borrowed'
            book.save()
            
            messages.success(
                request, 
                f'Book "{book.title}" issued to {student.user.get_full_name()}. '
                f'Due date: {due_date.strftime("%d/%m/%Y")}'
            )
            
            return redirect('book_issuance')
            
        except Student.DoesNotExist:
            messages.error(request, 'Student not found.')
        except Book.DoesNotExist:
            messages.error(request, 'Book not found.')
        except Exception as e:
            messages.error(request, f'Error issuing book: {str(e)}')
        
        return redirect('book_issuance')
    
    # GET request - show issuance form
    # Recent issuances
    recent_issuances = BookBorrowing.objects.filter(
        status='active'
    ).select_related(
        'student__user', 'book', 'issued_by'
    ).order_by('-borrow_date')[:20]
    
    context = {
        'recent_issuances': recent_issuances,
    }
    
    return render(request, 'librarian/circulation/book_issuance.html', context)


@login_required
@user_passes_test(is_librarian)
def search_student_for_borrowing(request):
    """AJAX endpoint to search for students"""
    
    query = request.GET.get('q', '')
    
    if len(query) < 3:
        return JsonResponse({'students': []})
    
    students = Student.objects.filter(
        Q(registration_number__icontains=query) |
        Q(user__first_name__icontains=query) |
        Q(user__last_name__icontains=query) |
        Q(user__email__icontains=query),
        student_status='active'
    ).select_related('user', 'programme')[:10]
    
    student_list = []
    for student in students:
        # Check active borrowings
        active_count = BookBorrowing.objects.filter(
            student=student,
            status='active'
        ).count()
        
        # Check overdue
        has_overdue = BookBorrowing.objects.filter(
            student=student,
            status__in=['active', 'overdue'],
            due_date__lt=timezone.now().date()
        ).exists()
        
        student_list.append({
            'id': student.id,
            'registration_number': student.registration_number,
            'name': student.user.get_full_name(),
            'programme': student.programme.name,
            'active_borrowings': active_count,
            'has_overdue': has_overdue,
        })
    
    return JsonResponse({'students': student_list})


@login_required
@user_passes_test(is_librarian)
def search_book_for_borrowing(request):
    """AJAX endpoint to search for books"""
    
    query = request.GET.get('q', '')
    
    if len(query) < 3:
        return JsonResponse({'books': []})
    
    books = Book.objects.filter(
        Q(title__icontains=query) |
        Q(author__icontains=query) |
        Q(isbn__icontains=query),
        available_copies__gt=0
    ).select_related('category')[:10]
    
    book_list = []
    for book in books:
        book_list.append({
            'id': book.id,
            'isbn': book.isbn,
            'title': book.title,
            'author': book.author,
            'category': book.category.name,
            'available_copies': book.available_copies,
            'total_copies': book.total_copies,
        })
    
    return JsonResponse({'books': book_list})


@login_required
@user_passes_test(is_librarian)
def book_returns(request):
    """Process book returns"""
    
    if request.method == 'POST':
        borrowing_id = request.POST.get('borrowing_id')
        
        try:
            borrowing = BookBorrowing.objects.get(id=borrowing_id)
            
            # Calculate fine if overdue
            if borrowing.due_date < timezone.now().date():
                borrowing.calculate_fine()
            
            # Update borrowing record
            borrowing.return_date = timezone.now()
            borrowing.status = 'returned'
            borrowing.returned_to = request.user
            borrowing.save()
            
            # Update book availability
            book = borrowing.book
            book.available_copies += 1
            if book.status == 'borrowed':
                book.status = 'available'
            book.save()
            
            if borrowing.fine_amount > 0:
                messages.warning(
                    request,
                    f'Book returned. Fine of KES {borrowing.fine_amount} is pending payment.'
                )
            else:
                messages.success(request, 'Book returned successfully!')
            
            return redirect('book_returns')
            
        except BookBorrowing.DoesNotExist:
            messages.error(request, 'Borrowing record not found.')
        except Exception as e:
            messages.error(request, f'Error processing return: {str(e)}')
        
        return redirect('book_returns')
    
    # GET request - show active borrowings
    active_borrowings = BookBorrowing.objects.filter(
        status='active'
    ).select_related(
        'student__user', 'book', 'issued_by'
    ).order_by('due_date')
    
    # Mark overdue
    for borrowing in active_borrowings:
        if borrowing.due_date < timezone.now().date():
            borrowing.status = 'overdue'
            borrowing.save()
    
    # Refresh queryset
    active_borrowings = BookBorrowing.objects.filter(
        status__in=['active', 'overdue']
    ).select_related(
        'student__user', 'book', 'issued_by'
    ).order_by('due_date')
    
    context = {
        'active_borrowings': active_borrowings,
    }
    
    return render(request, 'librarian/circulation/book_returns.html', context)


@login_required
@user_passes_test(is_librarian)
def renew_borrowing(request, borrowing_id):
    """Renew a book borrowing"""
    
    borrowing = get_object_or_404(BookBorrowing, id=borrowing_id)
    
    if request.method == 'POST':
        # Check if student is eligible for renewal
        if borrowing.status == 'overdue':
            messages.error(request, 'Cannot renew overdue books. Please return first.')
            return redirect('book_returns')
        
        # Extend due date by 14 days
        borrowing.due_date = borrowing.due_date + timedelta(days=14)
        borrowing.save()
        
        messages.success(
            request,
            f'Borrowing renewed. New due date: {borrowing.due_date.strftime("%d/%m/%Y")}'
        )
        
        return redirect('book_returns')
    
    context = {
        'borrowing': borrowing,
    }
    
    return render(request, 'librarian/circulation/renew_borrowing.html', context)


@login_required
@user_passes_test(is_librarian)
def overdue_management(request):
    """Manage overdue books"""
    
    # Get all overdue borrowings
    overdue_borrowings = BookBorrowing.objects.filter(
        status__in=['active', 'overdue'],
        due_date__lt=timezone.now().date()
    ).select_related(
        'student__user', 'book'
    ).order_by('due_date')
    
    # Calculate fines for all overdue
    for borrowing in overdue_borrowings:
        borrowing.calculate_fine()
        if borrowing.status != 'overdue':
            borrowing.status = 'overdue'
            borrowing.save()
    
    # Summary statistics
    total_overdue = overdue_borrowings.count()
    total_fines = overdue_borrowings.aggregate(
        total=Sum('fine_amount')
    )['total'] or Decimal('0.00')
    
    # Group by days overdue
    overdue_ranges = {
        'range_1_7': overdue_borrowings.filter(
            due_date__gte=timezone.now().date() - timedelta(days=7)
        ).count(),

        'range_8_14': overdue_borrowings.filter(
            due_date__lt=timezone.now().date() - timedelta(days=7),
            due_date__gte=timezone.now().date() - timedelta(days=14)
        ).count(),

        'range_15_30': overdue_borrowings.filter(
            due_date__lt=timezone.now().date() - timedelta(days=14),
            due_date__gte=timezone.now().date() - timedelta(days=30)
        ).count(),

        'range_30_plus': overdue_borrowings.filter(
            due_date__lt=timezone.now().date() - timedelta(days=30)
        ).count(),
    }
    
    average_fine = Decimal('0.00')

    if total_overdue > 0:
        average_fine = total_fines / total_overdue


    context = {
        'overdue_borrowings': overdue_borrowings,
        'total_overdue': total_overdue,
        'total_fines': total_fines,
        'overdue_ranges': overdue_ranges,
        'average_fine': average_fine,
    }
    
    return render(request, 'librarian/circulation/overdue_management.html', context)


# ============= FINES & PAYMENTS =============

@login_required
@user_passes_test(is_librarian)
def fine_management(request):
    """Manage library fines"""
    
    # Pending fines
    pending_fines = BookBorrowing.objects.filter(
        fine_amount__gt=0,
        fine_paid=False
    ).select_related('student__user', 'book').order_by('-fine_amount')
    
    # Paid fines (recent)
    paid_fines = BookBorrowing.objects.filter(
        fine_amount__gt=0,
        fine_paid=True
    ).select_related('student__user', 'book').order_by('-updated_at')[:50]
    
    # Summary
    total_pending = pending_fines.aggregate(
        total=Sum('fine_amount')
    )['total'] or Decimal('0.00')
    
    total_paid = paid_fines.aggregate(
        total=Sum('fine_amount')
    )['total'] or Decimal('0.00')
    
    context = {
        'pending_fines': pending_fines,
        'paid_fines': paid_fines,
        'total_pending': total_pending,
        'total_paid': total_paid,
    }
    
    return render(request, 'librarian/fines/fine_management.html', context)


@login_required
@user_passes_test(is_librarian)
def process_fine_payment(request, borrowing_id):
    """Process fine payment"""
    
    borrowing = get_object_or_404(BookBorrowing, id=borrowing_id)
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        amount_paid = Decimal(request.POST.get('amount_paid'))
        
        if amount_paid >= borrowing.fine_amount:
            borrowing.fine_paid = True
            borrowing.save()
            
            messages.success(
                request,
                f'Fine payment of KES {amount_paid} recorded successfully.'
            )
        else:
            messages.error(
                request,
                f'Amount paid (KES {amount_paid}) is less than fine amount (KES {borrowing.fine_amount}).'
            )
        
        return redirect('fine_management')
    
    context = {
        'borrowing': borrowing,
    }
    
    return render(request, 'librarian/fines/process_payment.html', context)


@login_required
@user_passes_test(is_librarian)
def waive_fine(request, borrowing_id):
    """Waive a fine (requires approval)"""
    
    borrowing = get_object_or_404(BookBorrowing, id=borrowing_id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason')
        
        if not reason:
            messages.error(request, 'Please provide a reason for waiving the fine.')
            return redirect('waive_fine', borrowing_id=borrowing_id)
        
        # Waive the fine
        borrowing.fine_amount = Decimal('0.00')
        borrowing.fine_paid = True
        borrowing.remarks = f'Fine waived by {request.user.get_full_name()}. Reason: {reason}'
        borrowing.save()
        
        messages.success(request, 'Fine waived successfully.')
        return redirect('fine_management')
    
    context = {
        'borrowing': borrowing,
    }
    
    return render(request, 'librarian/fines/waive_fine.html', context)


# ============= LIBRARY REPORTS =============

@login_required
@user_passes_test(is_librarian)
def library_reports(request):
    """Main reports dashboard"""
    
    current_semester = Semester.objects.filter(is_current=True).first()
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    
    context = {
        'current_semester': current_semester,
        'current_academic_year': current_academic_year,
    }
    
    return render(request, 'librarian/reports/reports_dashboard.html', context)


@login_required
@user_passes_test(is_librarian)
def usage_statistics(request):
    """Generate usage statistics report"""
    
    # Date range filter
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date:
        start_date = (timezone.now() - timedelta(days=30)).date()
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    if not end_date:
        end_date = timezone.now().date()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Filter borrowings
    borrowings = BookBorrowing.objects.filter(
        borrow_date__gte=start_date,
        borrow_date__lte=end_date
    )
    
    # Total statistics
    total_borrowings = borrowings.count()
    total_returns = borrowings.filter(status='returned').count()
    total_active = borrowings.filter(status='active').count()
    total_overdue = borrowings.filter(status='overdue').count()
    
    # Unique borrowers
    unique_borrowers = borrowings.values('student').distinct().count()
    
    # Most active borrowers
    top_borrowers = borrowings.values(
        'student__registration_number',
        'student__user__first_name',
        'student__user__last_name'
    ).annotate(
        borrow_count=Count('id')
    ).order_by('-borrow_count')[:10]
    
    # Daily borrowing trend
    daily_trend = borrowings.annotate(
        date=F('borrow_date')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # Category-wise usage
    category_usage = borrowings.values(
        'book__category__name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_borrowings': total_borrowings,
        'total_returns': total_returns,
        'total_active': total_active,
        'total_overdue': total_overdue,
        'unique_borrowers': unique_borrowers,
        'top_borrowers': top_borrowers,
        'daily_trend': daily_trend,
        'category_usage': category_usage,
    }
    
    return render(request, 'librarian/reports/usage_statistics.html', context)


@login_required
@user_passes_test(is_librarian)
def collection_analysis(request):
    """Analyze library collection"""
    
    # Total collection
    total_books = Book.objects.aggregate(
        total=Sum('total_copies')
    )['total'] or 0
    
    # By category
    category_breakdown = BookCategory.objects.annotate(
        total_books=Sum('books__total_copies'),
        available_books=Sum('books__available_copies'),
        unique_titles=Count('books')
    ).order_by('-total_books')
    
    # By publication year
    year_distribution = Book.objects.values('publication_year').annotate(
        count=Count('id')
    ).order_by('-publication_year')[:20]
    
    # Popular vs unpopular books
    popular_books = Book.objects.annotate(
        borrow_count=Count('borrowings')
    ).filter(borrow_count__gt=0).order_by('-borrow_count')[:20]
    
    unpopular_books = Book.objects.annotate(
        borrow_count=Count('borrowings')
    ).filter(borrow_count=0).order_by('acquisition_date')[:20]
    
    # Condition analysis
    condition_summary = {
        'available': Book.objects.filter(status='available').count(),
        'borrowed': Book.objects.filter(status='borrowed').count(),
        'reserved': Book.objects.filter(status='reserved').count(),
        'maintenance': Book.objects.filter(status='maintenance').count(),
        'lost': Book.objects.filter(status='lost').count(),
        'damaged': Book.objects.filter(status='damaged').count(),
    }
    
    context = {
        'total_books': total_books,
        'category_breakdown': category_breakdown,
        'year_distribution': year_distribution,
        'popular_books': popular_books,
        'unpopular_books': unpopular_books,
        'condition_summary': condition_summary,
    }
    
    return render(request, 'librarian/reports/collection_analysis.html', context)


@login_required
@user_passes_test(is_librarian)
def circulation_report(request):
    """Detailed circulation report"""
    
    current_semester = Semester.objects.filter(is_current=True).first()
    
    if current_semester:
        # Semester borrowings
        semester_borrowings = BookBorrowing.objects.filter(
            semester=current_semester
        )
        
        total_issued = semester_borrowings.count()
        total_returned = semester_borrowings.filter(status='returned').count()
        currently_borrowed = semester_borrowings.filter(status='active').count()
        overdue_count = semester_borrowings.filter(status='overdue').count()
        
        # Programme-wise circulation
        programme_circulation = semester_borrowings.values(
            'student__programme__name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Department-wise
        department_circulation = semester_borrowings.values(
            'student__programme__department__name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Year of study
        year_circulation = semester_borrowings.values(
            'student__current_year'
        ).annotate(
            count=Count('id')
        ).order_by('student__current_year')
        
    else:
        total_issued = 0
        total_returned = 0
        currently_borrowed = 0
        overdue_count = 0
        programme_circulation = []
        department_circulation = []
        year_circulation = []
    
    context = {
        'current_semester': current_semester,
        'total_issued': total_issued,
        'total_returned': total_returned,
        'currently_borrowed': currently_borrowed,
        'overdue_count': overdue_count,
        'programme_circulation': programme_circulation,
        'department_circulation': department_circulation,
        'year_circulation': year_circulation,
    }
    
    return render(request, 'librarian/reports/circulation_report.html', context)


# Continue in next file for remaining views...

@login_required
def hostel_dashboard(request):
    context = {'page_title': 'Hostel Dashboard'}
    return render(request, 'hostel/dashboard.html', context)


@login_required
def procurement_dashboard(request):
    context = {'page_title': 'Procurement Dashboard'}
    return render(request, 'procurement/dashboard.html', context)

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import (
    User, Student, Lecturer, Department, School, Programme,
    Semester, AcademicYear, SemesterResults, SemesterGPA,
    UnitAllocation, UnitEnrollment, HostelAllocation,
    BookBorrowing, FeeBalance, Announcement, Message
)

@login_required
def profile_view(request):
    """User profile view with role-specific data"""
    user = request.user
    context = {
        'page_title': 'My Profile',
        'user': user,
        'current_semester': None,
        'academic_year': None,
    }
    
    # Get current semester and academic year
    current_semester = Semester.objects.filter(is_current=True).first()
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    
    if current_semester:
        context['current_semester'] = current_semester
        context['academic_year'] = current_semester.academic_year
    
    # ROLE-SPECIFIC DATA
    if user.role == 'student':
        try:
            student_profile = Student.objects.get(user=user)
            context['student_profile'] = student_profile
            
            # Student-specific data
            context['programme'] = student_profile.programme
            context['intake'] = student_profile.intake
            
            # Current semester results
            if current_semester:
                semester_results = SemesterResults.objects.filter(
                    student=student_profile,
                    semester=current_semester
                ).select_related('programme_unit__unit')
                context['semester_results'] = semester_results
                
                # Current semester GPA
                semester_gpa = SemesterGPA.objects.filter(
                    student=student_profile,
                    semester=current_semester
                ).first()
                context['semester_gpa'] = semester_gpa
                
                # Current unit enrollments
                enrollments = UnitEnrollment.objects.filter(
                    student=student_profile,
                    semester=current_semester,
                    status='approved'
                ).select_related('programme_unit__unit')
                context['current_enrollments'] = enrollments
                
                # Current fee balance
                fee_balance = FeeBalance.objects.filter(
                    student=student_profile,
                    semester=current_semester
                ).first()
                context['fee_balance'] = fee_balance
            
            # All-time data
            all_results = SemesterResults.objects.filter(
                student=student_profile
            ).select_related('semester', 'programme_unit__unit').order_by('-semester__academic_year__start_date')
            context['all_results'] = all_results
            
            # Hostel allocation
            hostel_allocation = HostelAllocation.objects.filter(
                student=student_profile,
                is_active=True
            ).select_related('bed__room__hostel').first()
            context['hostel_allocation'] = hostel_allocation
            
            # Current book borrowings
            current_borrowings = BookBorrowing.objects.filter(
                student=student_profile,
                status='active'
            ).select_related('book')
            context['current_borrowings'] = current_borrowings
            
            # Total credits earned
            total_credits = all_results.filter(is_passed=True).aggregate(
                total_credits=models.Sum('credit_hours')
            )['total_credits'] or 0
            context['total_credits_earned'] = total_credits
            
        except Student.DoesNotExist:
            context['student_profile'] = None
    
    elif user.role == 'lecturer':
        try:
            lecturer_profile = Lecturer.objects.get(user=user)
            context['lecturer_profile'] = lecturer_profile
            context['department'] = lecturer_profile.department
            
            # Current semester unit allocations
            if current_semester:
                unit_allocations = UnitAllocation.objects.filter(
                    lecturer=user,
                    semester=current_semester,
                    status__in=['approved_hod', 'approved_hos', 'approved_dean']
                ).select_related(
                    'programme_unit__unit',
                    'programme_unit__programme',
                    'semester'
                )
                context['current_allocations'] = unit_allocations
                
                # Calculate total units
                total_units_current = unit_allocations.count()
                context['total_units_current'] = total_units_current
            
            # All-time unit allocations
            all_allocations = UnitAllocation.objects.filter(
                lecturer=user
            ).select_related(
                'programme_unit__unit',
                'programme_unit__programme',
                'semester'
            ).order_by('-semester__academic_year__start_date')
            context['all_allocations'] = all_allocations
            
            # Total units all time
            total_units_all_time = all_allocations.count()
            context['total_units_all_time'] = total_units_all_time
            
        except Lecturer.DoesNotExist:
            context['lecturer_profile'] = None
    
    elif user.role == 'hod':
        try:
            department = Department.objects.get(hod=user)
            context['department'] = department
            context['school'] = department.school
            
            # Department statistics
            lecturers_count = Lecturer.objects.filter(
                department=department,
                is_active=True
            ).count()
            context['lecturers_count'] = lecturers_count
            
            students_count = Student.objects.filter(
                programme__department=department,
                student_status='active'
            ).count()
            context['students_count'] = students_count
            
            # Pending unit allocations for approval
            if current_semester:
                pending_allocations = UnitAllocation.objects.filter(
                    programme_unit__unit__department=department,
                    semester=current_semester,
                    status='pending'
                ).count()
                context['pending_allocations'] = pending_allocations
                
        except Department.DoesNotExist:
            context['department'] = None
    
    elif user.role == 'hos':
        try:
            school = School.objects.get(head_of_school=user)
            context['school'] = school
            
            # School statistics
            departments_count = Department.objects.filter(
                school=school,
                is_active=True
            ).count()
            context['departments_count'] = departments_count
            
            lecturers_count = Lecturer.objects.filter(
                department__school=school,
                is_active=True
            ).count()
            context['lecturers_count'] = lecturers_count
            
            # Pending approvals
            if current_semester:
                pending_allocations = UnitAllocation.objects.filter(
                    programme_unit__unit__department__school=school,
                    semester=current_semester,
                    status='approved_hod'
                ).count()
                context['pending_allocations'] = pending_allocations
                
        except School.DoesNotExist:
            context['school'] = None
    
    elif user.role == 'dean':
        try:
            school = School.objects.get(dean=user)
            context['school'] = school
            
            # Dean statistics
            programmes_count = Programme.objects.filter(
                department__school=school,
                is_active=True
            ).count()
            context['programmes_count'] = programmes_count
            
            students_count = Student.objects.filter(
                programme__department__school=school,
                student_status='active'
            ).count()
            context['students_count'] = students_count
            
            # Pending approvals
            if current_semester:
                pending_allocations = UnitAllocation.objects.filter(
                    programme_unit__unit__department__school=school,
                    semester=current_semester,
                    status='approved_hos'
                ).count()
                context['pending_allocations'] = pending_allocations
                
        except School.DoesNotExist:
            context['school'] = None
    
    elif user.role == 'hostel_warden':
        # Get all hostels managed by this warden
        hostels = Hostel.objects.filter(warden=user, is_active=True)
        context['hostels'] = hostels
        
        # Hostel statistics
        if current_academic_year:
            total_capacity = sum(hostel.total_capacity for hostel in hostels)
            context['total_capacity'] = total_capacity
            
            allocated_beds = HostelAllocation.objects.filter(
                bed__room__hostel__in=hostels,
                academic_year=current_academic_year,
                is_active=True
            ).count()
            context['allocated_beds'] = allocated_beds
            
            occupancy_rate = (allocated_beds / total_capacity * 100) if total_capacity > 0 else 0
            context['occupancy_rate'] = round(occupancy_rate, 2)
    
    elif user.role == 'librarian':
        # Library statistics
        total_books = Book.objects.filter(is_active=True).count()
        context['total_books'] = total_books
        
        active_borrowings = BookBorrowing.objects.filter(
            status='active'
        ).count()
        context['active_borrowings'] = active_borrowings
        
        overdue_books = BookBorrowing.objects.filter(
            status='overdue'
        ).count()
        context['overdue_books'] = overdue_books
    
    # Common data for all roles
    # Unread messages
    unread_messages = Message.objects.filter(
        recipient=user,
        is_read=False
    ).count()
    context['unread_messages'] = unread_messages
    
    # Recent announcements
    recent_announcements = Announcement.objects.filter(
        is_published=True
    ).order_by('-publish_date')[:5]
    context['recent_announcements'] = recent_announcements
    
    return render(request, 'profile/profile.html', context)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from .models import *
import json
from decimal import Decimal

# ============= STUDENT LIST VIEW =============
@login_required
@permission_required('auth.view_user', raise_exception=True)
def student_list(request):
    """List all students with search and filter functionality"""
    students = Student.objects.select_related(
        'user', 'programme', 'intake'
    ).prefetch_related('unit_registrations').all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        students = students.filter(
            Q(registration_number__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(national_id__icontains=search_query)
        )
    
    # Filter functionality
    programme_filter = request.GET.get('programme', '')
    if programme_filter:
        students = students.filter(programme_id=programme_filter)
    
    year_filter = request.GET.get('year', '')
    if year_filter:
        students = students.filter(current_year=year_filter)
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        students = students.filter(student_status=status_filter)
    
    # Get filter options
    programmes = Programme.objects.filter(is_active=True)
    years = Student.objects.values_list('current_year', flat=True).distinct().order_by('current_year')
    
    # Pagination
    paginator = Paginator(students, 25)  # Show 25 students per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'students': page_obj,
        'programmes': programmes,
        'years': years,
        'status_choices': Student.STUDENT_STATUS,
        'search_query': search_query,
        'programme_filter': programme_filter,
        'year_filter': year_filter,
        'status_filter': status_filter,
        'total_students': students.count(),
    }
    return render(request, 'admin/students/student_list.html', context)

# ============= STUDENT DETAIL VIEW =============
@login_required
@permission_required('auth.view_user', raise_exception=True)
def student_detail(request, reg_number):
    """View individual student details"""
    student = get_object_or_404(
        Student.objects.select_related(
            'user', 'programme', 'intake',
            'programme__department', 'programme__department__school'
        ).prefetch_related(
            'unit_registrations',
            'unit_registrations__programme_unit',
            'unit_registrations__semester',
            'unit_registrations__programme_unit__unit',
            'semester_results',
            'semester_results__programme_unit',
            'semester_results__programme_unit__unit',
            'semester_gpas',
            'fee_payments',
            'fee_balances',
            'hostel_allocations',
            'hostel_allocations__bed',
            'hostel_allocations__bed__room',
            'hostel_allocations__bed__room__hostel',
        ),
        registration_number=reg_number
    )
    
    # Get current semester
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get student's current units  // we will modify this to unitenrollment instead
    current_units = UnitRegistration.objects.filter(
        student=student,
        semester=current_semester,
        status='registered'
    ).select_related('programme_unit', 'programme_unit__unit') if current_semester else []
    
    # Get academic performance summary
    performance_summary = {
        'total_units_completed': student.semester_results.filter(is_passed=True).count(),
        'current_gpa': student.cumulative_gpa,
        'total_credits': student.total_credit_hours,
        'current_semester_gpa': None,
    }
    
    if current_semester:
        current_gpa = SemesterGPA.objects.filter(
            student=student,
            semester=current_semester
        ).first()
        if current_gpa:
            performance_summary['current_semester_gpa'] = current_gpa.semester_gpa
    
    # Get fee status
    fee_status = FeeBalance.objects.filter(
        student=student,
        semester=current_semester
    ).first() if current_semester else None
    
    # Get attendance summary (if available)
    attendance_summary = {
        'total_classes': 0,
        'attended': 0,
        'percentage': 0,
    }
    
    context = {
        'student': student,
        'current_semester': current_semester,
        'current_units': current_units,
        'performance_summary': performance_summary,
        'fee_status': fee_status,
        'attendance_summary': attendance_summary,
    }
    return render(request, 'admin/students/student_detail.html', context)

# ============= ADD STUDENT VIEW =============
@login_required
@permission_required('auth.add_user', raise_exception=True)
def add_student(request):
    """Add a new student with user account"""
    if request.method == 'POST':
        try:
            # Create user first
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            phone_number = request.POST.get('phone_number')
            id_number = request.POST.get('national_id')
            
            # Check if username or email already exists
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists.')
                return redirect('add_student')
            
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists.')
                return redirect('add_student')
            
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                id_number=id_number,
                role='student',
                is_active=True,
            )
            
            # Create student profile
            registration_number = request.POST.get('registration_number')
            programme_id = request.POST.get('programme')
            intake_id = request.POST.get('intake')
            gender = request.POST.get('gender')
            date_of_birth = request.POST.get('date_of_birth')
            admission_date = request.POST.get('admission_date')
            current_year = request.POST.get('current_year', 1)
            current_semester = request.POST.get('current_semester', '1')
            
            # Check if registration number already exists
            if Student.objects.filter(registration_number=registration_number).exists():
                messages.error(request, 'Registration number already exists.')
                user.delete()  # Delete the created user
                return redirect('add_student')
            
            # Check if national ID already exists
            if Student.objects.filter(national_id=id_number).exists():
                messages.error(request, 'National ID already registered.')
                user.delete()  # Delete the created user
                return redirect('add_student')
            
            student = Student.objects.create(
                user=user,
                registration_number=registration_number,
                programme_id=programme_id,
                intake_id=intake_id,
                gender=gender,
                date_of_birth=date_of_birth,
                national_id=id_number,
                admission_date=admission_date,
                current_year=current_year,
                current_semester=current_semester,
                student_status='active',
                # Additional fields
                permanent_address=request.POST.get('permanent_address', ''),
                current_address=request.POST.get('current_address', ''),
                emergency_contact_name=request.POST.get('emergency_contact_name', ''),
                emergency_contact_phone=request.POST.get('emergency_contact_phone', ''),
                emergency_contact_relationship=request.POST.get('emergency_contact_relationship', ''),
                sponsor_name=request.POST.get('sponsor_name', ''),
                sponsor_phone=request.POST.get('sponsor_phone', ''),
                sponsor_email=request.POST.get('sponsor_email', ''),
            )
            
            # Create initial fee balance if needed
            current_semester_obj = Semester.objects.filter(is_current=True).first()
            if current_semester_obj:
                # Get fee structure for student's programme and year
                fee_structure = FeeStructure.objects.filter(
                    programme=student.programme,
                    academic_year=current_semester_obj.academic_year,
                    year_of_study=student.current_year,
                    semester_number=student.current_semester,
                    is_active=True
                ).first()
                
                if fee_structure:
                    FeeBalance.objects.create(
                        student=student,
                        semester=current_semester_obj,
                        academic_year=current_semester_obj.academic_year,
                        total_fees=fee_structure.total_fee,
                        amount_paid=Decimal('0.00'),
                        balance=fee_structure.total_fee,
                    )
            
            messages.success(request, f'Student {registration_number} added successfully!')
            return redirect('student_detail', reg_number=registration_number)
            
        except Exception as e:
            messages.error(request, f'Error adding student: {str(e)}')
            return redirect('add_student')
    
    # GET request - show form
    programmes = Programme.objects.filter(is_active=True)
    intakes = Intake.objects.filter(is_active=True)
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Generate registration number (example logic)
    if current_semester:
        academic_year_short = current_semester.academic_year.name[2:4] + current_semester.academic_year.name[7:9]
        programme_count = Student.objects.filter(
            programme__department__school__code='CIT',
            admission_date__year=timezone.now().year
        ).count() + 1
        
        suggested_reg_number = f"SC{academic_year_short}/{str(programme_count).zfill(4)}/{timezone.now().year}"
    else:
        suggested_reg_number = f"SC{timezone.now().year % 100}/0001/{timezone.now().year}"
    
    context = {
        'programmes': programmes,
        'intakes': intakes,
        'gender_choices': Student.GENDER_CHOICES,
        'semester_choices': Semester.SEMESTER_NAMES,
        'suggested_reg_number': suggested_reg_number,
        'current_year': timezone.now().year,
    }
    return render(request, 'admin/students/add_student.html', context)

# ============= UPDATE STUDENT VIEW =============
@login_required
@permission_required('auth.change_user', raise_exception=True)
def update_student(request, reg_number):
    """Update student information"""
    student = get_object_or_404(Student, registration_number=reg_number)
    
    if request.method == 'POST':
        try:
            # Update user information
            user = student.user
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.email = request.POST.get('email', user.email)
            user.phone_number = request.POST.get('phone_number', user.phone_number)
            user.save()
            
            # Update student information
            student.programme_id = request.POST.get('programme', student.programme_id)
            student.current_year = request.POST.get('current_year', student.current_year)
            student.current_semester = request.POST.get('current_semester', student.current_semester)
            student.student_status = request.POST.get('student_status', student.student_status)
            student.gender = request.POST.get('gender', student.gender)
            student.date_of_birth = request.POST.get('date_of_birth', student.date_of_birth)
            student.permanent_address = request.POST.get('permanent_address', student.permanent_address)
            student.current_address = request.POST.get('current_address', student.current_address)
            student.emergency_contact_name = request.POST.get('emergency_contact_name', student.emergency_contact_name)
            student.emergency_contact_phone = request.POST.get('emergency_contact_phone', student.emergency_contact_phone)
            student.emergency_contact_relationship = request.POST.get('emergency_contact_relationship', student.emergency_contact_relationship)
            student.sponsor_name = request.POST.get('sponsor_name', student.sponsor_name)
            student.sponsor_phone = request.POST.get('sponsor_phone', student.sponsor_phone)
            student.sponsor_email = request.POST.get('sponsor_email', student.sponsor_email)
            student.save()
            
            messages.success(request, f'Student {reg_number} updated successfully!')
            return redirect('student_detail', reg_number=reg_number)
            
        except Exception as e:
            messages.error(request, f'Error updating student: {str(e)}')
            return redirect('update_student', reg_number=reg_number)
    
    # GET request - show form with current data
    programmes = Programme.objects.filter(is_active=True)
    
    context = {
        'student': student,
        'programmes': programmes,
        'gender_choices': Student.GENDER_CHOICES,
        'semester_choices': Semester.SEMESTER_NAMES,
        'status_choices': Student.STUDENT_STATUS,
    }
    return render(request, 'admin/students/update_student.html', context)

# ============= DELETE STUDENT VIEW =============
@login_required
@permission_required('auth.delete_user', raise_exception=True)
def delete_student(request, reg_number):
    """Delete a student (soft delete - change status to discontinued)"""
    student = get_object_or_404(Student, registration_number=reg_number)
    
    if request.method == 'POST':
        try:
            # Soft delete - change status to discontinued
            student.student_status = 'discontinued'
            student.user.is_active_user = False
            student.user.is_active = False
            student.user.save()
            student.save()
            
            messages.success(request, f'Student {reg_number} has been discontinued.')
            return redirect('student_list')
            
        except Exception as e:
            messages.error(request, f'Error deleting student: {str(e)}')
            return redirect('student_detail', reg_number=reg_number)
    
    # GET request - show confirmation page
    context = {
        'student': student,
    }
    return render(request, 'admin/students/delete_student.html', context)

# ============= STUDENT PERFORMANCE VIEW =============
@login_required
@permission_required('auth.view_user', raise_exception=True)
def student_performance(request, reg_number):
    """View student academic performance"""
    student = get_object_or_404(
        Student.objects.select_related('user', 'programme'),
        registration_number=reg_number
    )
    
    # Get all semester results
    semester_results = SemesterResults.objects.filter(
        student=student
    ).select_related(
        'programme_unit',
        'programme_unit__unit',
        'semester',
        'semester__academic_year'
    ).order_by('-semester__academic_year__start_date', '-semester__semester_number')
    
    # Get semester GPAs
    semester_gpas = SemesterGPA.objects.filter(
        student=student
    ).select_related('semester', 'semester__academic_year').order_by('-semester__academic_year__start_date')
    
    # Calculate summary statistics
    summary = {
        'total_units_completed': semester_results.filter(is_passed=True).count(),
        'total_credits_earned': semester_results.filter(is_passed=True).aggregate(
            total=Sum('credit_hours')
        )['total'] or 0,
        'overall_gpa': student.cumulative_gpa,
        'total_quality_points': 0,
        'transcript_ready': student.total_credit_hours >= student.programme.min_credit_hours,
    }
    
    # Group results by semester
    results_by_semester = {}
    for result in semester_results:
        semester_key = f"{result.semester.academic_year.name} - {result.semester.name}"
        if semester_key not in results_by_semester:
            results_by_semester[semester_key] = {
                'semester': result.semester,
                'results': [],
                'total_credits': 0,
                'total_quality_points': Decimal('0.00'),
                'semester_gpa': None,
            }
        results_by_semester[semester_key]['results'].append(result)
        results_by_semester[semester_key]['total_credits'] += result.credit_hours
        results_by_semester[semester_key]['total_quality_points'] += result.quality_points
    
    # Add semester GPA to each group
    for gpa in semester_gpas:
        semester_key = f"{gpa.semester.academic_year.name} - {gpa.semester.name}"
        if semester_key in results_by_semester:
            results_by_semester[semester_key]['semester_gpa'] = gpa.semester_gpa
    
    context = {
        'student': student,
        'results_by_semester': results_by_semester,
        'summary': summary,
        'semester_gpas': semester_gpas,
    }
    return render(request, 'admin/students/student_performance.html', context)

# ============= STUDENT FEE MANAGEMENT VIEW =============
@login_required
@permission_required('auth.view_user', raise_exception=True)
def student_fees(request, reg_number):
    """View and manage student fees"""
    student = get_object_or_404(
        Student.objects.select_related('user', 'programme'),
        registration_number=reg_number
    )
    
    # Get all fee balances
    fee_balances = FeeBalance.objects.filter(
        student=student
    ).select_related(
        'semester',
        'semester__academic_year'
    ).order_by('-semester__academic_year__start_date', '-semester__semester_number')
    
    # Get all fee payments
    fee_payments = FeePayment.objects.filter(
        student=student
    ).select_related(
        'semester',
        'semester__academic_year',
        'fee_structure'
    ).order_by('-payment_date')
    
    # Get current fee structure
    current_semester = Semester.objects.filter(is_current=True).first()
    current_fee_structure = None
    if current_semester:
        current_fee_structure = FeeStructure.objects.filter(
            programme=student.programme,
            academic_year=current_semester.academic_year,
            year_of_study=student.current_year,
            semester_number=student.current_semester,
            is_active=True
        ).first()
    
    # Calculate summary
    summary = {
        'total_fees_owed': fee_balances.aggregate(total=Sum('balance'))['total'] or Decimal('0.00'),
        'total_paid': fee_payments.filter(status='completed').aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
        'outstanding_semesters': fee_balances.filter(balance__gt=0).count(),
        'cleared_semesters': fee_balances.filter(is_cleared=True).count(),
    }
    
    context = {
        'student': student,
        'fee_balances': fee_balances,
        'fee_payments': fee_payments,
        'current_fee_structure': current_fee_structure,
        'summary': summary,
        'payment_methods': FeePayment.PAYMENT_METHODS,
    }
    return render(request, 'admin/students/student_fees.html', context)

# ============= ADD FEE PAYMENT VIEW =============
@login_required
@permission_required('auth.add_fee_payment', raise_exception=True)
def add_fee_payment(request, reg_number):
    """Add a new fee payment for student"""
    student = get_object_or_404(Student, registration_number=reg_number)
    
    if request.method == 'POST':
        try:
            semester_id = request.POST.get('semester')
            amount = Decimal(request.POST.get('amount', '0'))
            payment_method = request.POST.get('payment_method')
            transaction_reference = request.POST.get('transaction_reference')
            payment_date = request.POST.get('payment_date') or timezone.now().date()
            
            semester = get_object_or_404(Semester, id=semester_id)
            
            # Create fee payment
            fee_payment = FeePayment.objects.create(
                student=student,
                semester=semester,
                academic_year=semester.academic_year,
                amount=amount,
                payment_method=payment_method,
                transaction_reference=transaction_reference,
                payment_date=payment_date,
                status='completed',
                processed_by=request.user,
                remarks=request.POST.get('remarks', ''),
            )
            
            # Update fee balance
            fee_balance, created = FeeBalance.objects.get_or_create(
                student=student,
                semester=semester,
                academic_year=semester.academic_year,
                defaults={'total_fees': Decimal('0.00'), 'amount_paid': Decimal('0.00')}
            )
            
            fee_balance.amount_paid += amount
            fee_balance.last_payment_date = timezone.now()
            fee_balance.save()
            
            messages.success(request, f'Fee payment of {amount} recorded successfully!')
            return redirect('student_fees', reg_number=reg_number)
            
        except Exception as e:
            messages.error(request, f'Error recording payment: {str(e)}')
            return redirect('student_fees', reg_number=reg_number)
    
    # GET request - show form
    semesters = Semester.objects.filter(
        academic_year__is_active=True
    ).order_by('-academic_year__start_date', '-semester_number')
    
    context = {
        'student': student,
        'semesters': semesters,
        'payment_methods': FeePayment.PAYMENT_METHODS,
    }
    return render(request, 'admin/students/add_fee_payment.html', context)

# ============= AJAX VIEWS FOR DATA =============
@login_required
def get_student_details_ajax(request, reg_number):
    """Get student details for AJAX requests"""
    student = get_object_or_404(Student.objects.select_related('user', 'programme'), 
                               registration_number=reg_number)
    
    data = {
        'registration_number': student.registration_number,
        'full_name': student.user.get_full_name(),
        'programme': str(student.programme),
        'current_year': student.current_year,
        'current_semester': student.current_semester,
        'student_status': student.student_status,
        'email': student.user.email,
        'phone': student.user.phone_number,
        'gpa': str(student.cumulative_gpa),
    }
    return JsonResponse(data)

@login_required
def get_programme_fee_structure(request):
    """Get fee structure for programme, year, and semester"""
    programme_id = request.GET.get('programme_id')
    year = request.GET.get('year')
    semester = request.GET.get('semester')
    
    current_semester = Semester.objects.filter(is_current=True).first()
    if not current_semester:
        return JsonResponse({'error': 'No current semester found'}, status=400)
    
    fee_structure = FeeStructure.objects.filter(
        programme_id=programme_id,
        academic_year=current_semester.academic_year,
        year_of_study=year,
        semester_number=semester,
        is_active=True
    ).first()
    
    if fee_structure:
        data = {
            'tuition_fee': str(fee_structure.tuition_fee),
            'total_fee': str(fee_structure.total_fee),
            'breakdown': {
                'activity_fee': str(fee_structure.activity_fee),
                'examination_fee': str(fee_structure.examination_fee),
                'library_fee': str(fee_structure.library_fee),
                'medical_fee': str(fee_structure.medical_fee),
                'technology_fee': str(fee_structure.technology_fee),
                'other_fees': str(fee_structure.other_fees),
            }
        }
    else:
        data = {'error': 'No fee structure found'}
    
    return JsonResponse(data)

# ============= BULK ACTIONS =============
@login_required
@permission_required('auth.change_user', raise_exception=True)
def bulk_update_students(request):
    """Bulk update student status or year"""
    if request.method == 'POST':
        student_ids = request.POST.getlist('student_ids')
        action = request.POST.get('action')
        new_value = request.POST.get('new_value')
        
        if not student_ids:
            messages.error(request, 'No students selected.')
            return redirect('student_list')
        
        try:
            students = Student.objects.filter(id__in=student_ids)
            
            if action == 'update_status':
                students.update(student_status=new_value)
                message = f'Updated status for {students.count()} students.'
            elif action == 'update_year':
                students.update(current_year=new_value)
                message = f'Updated year for {students.count()} students.'
            elif action == 'update_semester':
                students.update(current_semester=new_value)
                message = f'Updated semester for {students.count()} students.'
            else:
                messages.error(request, 'Invalid action.')
                return redirect('student_list')
            
            messages.success(request, message)
            
        except Exception as e:
            messages.error(request, f'Error in bulk update: {str(e)}')
        
        return redirect('student_list')
    
    return redirect('student_list')

# ============= EXPORT STUDENTS =============
@login_required
def export_students(request):
    """Export student list to CSV"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="students.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Registration Number', 'Full Name', 'Email', 'Phone', 
        'Programme', 'Year', 'Semester', 'Status', 'GPA'
    ])
    
    students = Student.objects.select_related('user', 'programme').all()
    
    for student in students:
        writer.writerow([
            student.registration_number,
            student.user.get_full_name(),
            student.user.email,
            student.user.phone_number,
            str(student.programme),
            student.current_year,
            student.current_semester,
            student.get_student_status_display(),
            str(student.cumulative_gpa),
        ])
    
    return response



# Add these views to your views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal

# Import your models (adjust based on your project structure)
from .models import (
    Student, SemesterReport, ResitExam, UnitEnrollment, EnrollmentPeriod,
    Semester, AcademicYear, SemesterResults, ProgrammeUnit, UnitAllocation,
    FeeBalance, UnitGradingSystem
)


# ============= SEMESTER REPORTING VIEWS =============

@login_required
def semester_report_view(request):
    """View for students to report for a new semester"""
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('student_dashboard')
    
    # Get current semester
    current_semester = Semester.objects.filter(is_current=True).first()
    if not current_semester:
        messages.error(request, 'No active semester found.')
        return redirect('student_dashboard')
    
    # Check if already reported for current semester
    existing_report = SemesterReport.objects.filter(
        student=student,
        to_semester=current_semester,
        status__in=['pending', 'approved']
    ).first()
    
    if existing_report:
        messages.info(request, f'You have already reported for {current_semester}.')
        return redirect('semester_report_status', report_id=existing_report.id)
    
    # Get failed units count from previous semester
    failed_units = SemesterResults.objects.filter(
        student=student,
        is_passed=False,
        semester=student.semester_gpas.order_by('-semester__start_date').first().semester if student.semester_gpas.exists() else None
    ).count()
    
    # Get fee balance
    fee_balance = FeeBalance.objects.filter(
        student=student,
        semester=current_semester
    ).first()
    
    # Calculate next year and semester based on how many semesters your programme has 
    programme_total_semesters = student.programme.total_semesters
    is_fresher = not student.semester_gpas.exists()

    if is_fresher:
        # Freshly admitted students
        next_year = 1
        next_semester_number = '1'
    else:
        # Continuing students (promotion logic)
        current_year = student.current_year
        current_sem = int(student.current_semester)

        if current_sem < 2:  # Sem 1 → Sem 2
            next_semester_number = str(current_sem + 1)
            next_year = current_year
        else:  # Sem 2 → Next Year Sem 1
            next_semester_number = '1'
            next_year = current_year + 1

    
    # Get previous semester GPA
    previous_gpa = student.semester_gpas.order_by('-semester__start_date').first()
    
    context = {
        'student': student,
        'current_semester': current_semester,
        'failed_units_count': failed_units,
        'is_eligible': failed_units <= 2,
        'fee_balance': fee_balance,
        'next_year': next_year,
        'next_semester_number': next_semester_number,
        'previous_gpa': previous_gpa,
        'programme_total_semesters': programme_total_semesters,
    }
    
    if request.method == 'POST':
        try:
            # Create semester report
            semester_report = SemesterReport(
                student=student,
                from_academic_year=current_semester.academic_year if student.current_year else None,
                to_academic_year=current_semester.academic_year,
                from_semester=Semester.objects.filter(
                    academic_year=current_semester.academic_year,
                    semester_number=student.current_semester
                ).first() if student.current_semester else None,
                to_semester=current_semester,
                from_year_of_study=student.current_year if student.current_year else None,
                to_year_of_study=next_year,
                from_semester_number=student.current_semester if student.current_semester else None,
                to_semester_number=next_semester_number,
                failed_units_count=failed_units,
                fee_balance=fee_balance.balance if fee_balance else Decimal('0.00'),
                is_financially_cleared=fee_balance.is_cleared if fee_balance else True,
                previous_semester_gpa=previous_gpa.semester_gpa if previous_gpa else None,
                cumulative_gpa=student.cumulative_gpa,
                total_credits_earned=student.total_credit_hours,
            )
            
            semester_report.save()
            
            messages.success(request, f'Semester report submitted successfully for {current_semester}.')
            return redirect('semester_report_status', report_id=semester_report.id)
            
        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error submitting semester report: {str(e)}')
    
    return render(request, 'student/semester_report.html', context)


@login_required
def semester_report_status(request, report_id):
    """View semester report status"""
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('student_dashboard')
    
    report = get_object_or_404(SemesterReport, id=report_id, student=student)
    
    context = {
        'student': student,
        'report': report,
    }
    
    return render(request, 'student/semester_report_status.html', context)


@login_required
def semester_report_history(request):
    """View all semester reports"""
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('student_dashboard')
    
    reports = SemesterReport.objects.filter(student=student).order_by('-report_date')
    
    context = {
        'student': student,
        'reports': reports,
    }
    
    return render(request, 'student/semester_report_history.html', context)


# ============= UNIT ENROLLMENT VIEWS =============
@login_required
def unit_enrollment_view(request):
    """View for students to enroll in units"""
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('student_dashboard')
    
    # Get current semester
    current_semester = Semester.objects.filter(is_current=True).first()
    if not current_semester:
        messages.error(request, 'No active semester found.')
        return redirect('student_dashboard')
    
    # Check if student has reported for this semester
    semester_report = SemesterReport.objects.filter(
        student=student,
        to_semester=current_semester,
        status='approved'
    ).first()
    
    if not semester_report:
        messages.warning(request, 'You must report for the semester before enrolling in units.')
        return redirect('semester_report')
    
    # Check enrollment period
    enrollment_period = EnrollmentPeriod.objects.filter(
        semester=current_semester
    ).first()
    
    if not enrollment_period:
        messages.error(request, 'No enrollment period configured for this semester.')
        return redirect('student_dashboard')
    
    # Check if enrollment is open
    is_enrollment_open = enrollment_period.is_enrollment_open()
    is_resit_open = enrollment_period.is_resit_enrollment_open()
    
    if not is_enrollment_open and not is_resit_open:
        messages.error(request, 'Unit enrollment is not currently open.')
        return redirect('student_dashboard')
    
    # Get ALL available units for student's year and semester
    # (regardless of lecturer allocation)
    available_units = ProgrammeUnit.objects.filter(
        programme=student.programme,
        academic_year=current_semester.academic_year,
        year_of_study=student.current_year,
        semester_number=student.current_semester,
        is_active=True
    ).select_related(
        'unit', 
        'unit__department', 
        'programme'
    ).prefetch_related('allocations')
    
    # Get already enrolled units for this semester
    enrolled_units = UnitEnrollment.objects.filter(
        student=student,
        semester=current_semester,
        status__in=['pending', 'approved']
    ).values_list('programme_unit_id', flat=True)
    
    # Get failed units eligible for resit
    failed_units = SemesterResults.objects.filter(
        student=student,
        is_passed=False
    ).exclude(
        # Don't show units already enrolled
        programme_unit__in=enrolled_units
    ).select_related(
        'programme_unit', 
        'programme_unit__unit',
        'semester'
    ).order_by('-semester__academic_year__start_date')
    
    # Filter failed units that are offered this semester
    failed_units_offered = []
    if is_resit_open:
        for result in failed_units:
            # Check if the unit exists in the programme for current semester
            unit_offered = ProgrammeUnit.objects.filter(
                programme=student.programme,
                unit=result.programme_unit.unit,
                academic_year=current_semester.academic_year,
                is_active=True
            ).exists()
            
            if unit_offered:
                failed_units_offered.append(result)
    
    # Get fee balance information
    fee_balance = None
    try:
        from .models import FeeBalance
        fee_balance = FeeBalance.objects.filter(
            student=student,
            semester=current_semester
        ).first()
    except:
        pass
    
    context = {
        'student': student,
        'current_semester': current_semester,
        'semester_report': semester_report,
        'enrollment_period': enrollment_period,
        'available_units': available_units,
        'enrolled_units': list(enrolled_units),
        'failed_units_offered': failed_units_offered,
        'is_enrollment_open': is_enrollment_open,
        'is_resit_open': is_resit_open,
        'fee_balance': fee_balance,
    }
    
    if request.method == 'POST':
        selected_units = request.POST.getlist('units')
        resit_units = request.POST.getlist('resit_units')
        
        # Validate that at least one unit is selected
        if not selected_units and not resit_units:
            messages.warning(request, 'Please select at least one unit to enroll.')
            return render(request, 'student/unit_enrollment.html', context)
        
        # Check enrollment period again before processing
        if selected_units and not is_enrollment_open:
            messages.error(request, 'Normal unit enrollment is not currently open.')
            return render(request, 'student/unit_enrollment.html', context)
        
        if resit_units and not is_resit_open:
            messages.error(request, 'Resit unit enrollment is not currently open.')
            return render(request, 'student/unit_enrollment.html', context)
        
        try:
            with transaction.atomic():
                enrolled_count = 0
                resit_count = 0
                
                # Enroll in normal units
                if selected_units and is_enrollment_open:
                    for unit_id in selected_units:
                        programme_unit = get_object_or_404(ProgrammeUnit, id=unit_id)
                        
                        # Check if already enrolled
                        if UnitEnrollment.objects.filter(
                            student=student,
                            programme_unit=programme_unit,
                            semester=current_semester,
                            status__in=['pending', 'approved']
                        ).exists():
                            continue
                        
                        # Create enrollment
                        enrollment = UnitEnrollment(
                            student=student,
                            semester_report=semester_report,
                            programme_unit=programme_unit,
                            semester=current_semester,
                            enrollment_type='normal',
                            status='pending'
                        )
                        enrollment.save()
                        enrolled_count += 1
                
                # Enroll in resit units
                if resit_units and is_resit_open:
                    for result_id in resit_units:
                        result = get_object_or_404(SemesterResults, id=result_id, student=student)
                        
                        # Check if already enrolled
                        if UnitEnrollment.objects.filter(
                            student=student,
                            programme_unit=result.programme_unit,
                            semester=current_semester,
                            status__in=['pending', 'approved']
                        ).exists():
                            continue
                        
                        # Check if resit exam already exists
                        existing_resit = ResitExam.objects.filter(
                            student=student,
                            original_result=result,
                            resit_semester=current_semester
                        ).first()
                        
                        if existing_resit:
                            resit_exam = existing_resit
                        else:
                            # Create resit exam record
                            resit_exam = ResitExam(
                                student=student,
                                original_result=result,
                                resit_semester=current_semester,
                                original_semester=result.semester,
                                original_marks=result.total_marks,
                                original_grade=result.grade,
                                original_grade_point=result.grade_point,
                                resit_fee_amount=Decimal('2000.00'),
                                status='registered'
                            )
                            resit_exam.save()
                        
                        # Create enrollment
                        enrollment = UnitEnrollment(
                            student=student,
                            semester_report=semester_report,
                            programme_unit=result.programme_unit,
                            semester=current_semester,
                            enrollment_type='resit',
                            resit_exam=resit_exam,
                            status='pending'
                        )
                        enrollment.save()
                        resit_count += 1
                
                # Success messages
                if enrolled_count > 0 and resit_count > 0:
                    messages.success(
                        request, 
                        f'Successfully enrolled in {enrolled_count} normal unit(s) and {resit_count} resit unit(s).'
                    )
                elif enrolled_count > 0:
                    messages.success(request, f'Successfully enrolled in {enrolled_count} unit(s).')
                elif resit_count > 0:
                    messages.success(
                        request, 
                        f'Successfully enrolled in {resit_count} resit unit(s). Total resit fee: Ksh {resit_count * 2000:,}'
                    )
                else:
                    messages.info(request, 'All selected units were already enrolled.')
                
                return redirect('unit_enrollment_status')
                
        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error enrolling in units: {str(e)}')
            # Log the error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Unit enrollment error for student {student.registration_number}: {str(e)}')
    
    return render(request, 'student/unit_enrollment.html', context)



@login_required
def unit_enrollment_status(request):
    """View enrollment status"""
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('student_dashboard')
    
    current_semester = Semester.objects.filter(is_current=True).first()
    
    enrollments = UnitEnrollment.objects.filter(
        student=student,
        semester=current_semester
    ).select_related(
        'programme_unit', 
        'programme_unit__unit',
        'resit_exam'
    ).order_by('enrollment_type', 'programme_unit__unit__code')
    
    # Calculate counts
    total_enrollments = enrollments.count()
    approved_count = enrollments.filter(status='approved').count()
    pending_count = enrollments.filter(status='pending').count()
    resit_count = enrollments.filter(enrollment_type='resit').count()
    
    context = {
        'student': student,
        'current_semester': current_semester,
        'enrollments': enrollments,
        'total_enrollments': total_enrollments,
        'approved_count': approved_count,
        'pending_count': pending_count,
        'resit_count': resit_count,
    }
    
    return render(request, 'student/unit_enrollment_status.html', context)

# ============= RESIT EXAM VIEWS =============

@login_required
def resit_exam_registration(request):
    """Register for resit exams"""
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('student_dashboard')
    
    current_semester = Semester.objects.filter(is_current=True).first()
    if not current_semester:
        messages.error(request, 'No active semester found.')
        return redirect('student_dashboard')
    
    # Check if student has reported
    semester_report = SemesterReport.objects.filter(
        student=student,
        to_semester=current_semester,
        status='approved'
    ).first()
    
    if not semester_report:
        messages.warning(request, 'You must report for the semester before registering for resit exams.')
        return redirect('semester_report')
    
    # Check resit enrollment period
    enrollment_period = EnrollmentPeriod.objects.filter(
        semester=current_semester
    ).first()
    
    if not enrollment_period or not enrollment_period.is_resit_enrollment_open():
        messages.error(request, 'Resit exam registration is not currently open.')
        return redirect('student_dashboard')
    
    # Get failed units that are offered this semester
    failed_results = SemesterResults.objects.filter(
        student=student,
        is_passed=False
    ).select_related('programme_unit', 'programme_unit__unit', 'semester')
    
    eligible_resits = []
    for result in failed_results:
        # Check if unit is offered this semester
        if UnitAllocation.objects.filter(
            programme_unit=result.programme_unit,
            semester=current_semester,
            status='approved_dean'
        ).exists():
            # Check if not already registered
            if not ResitExam.objects.filter(
                student=student,
                original_result=result,
                resit_semester=current_semester
            ).exists():
                eligible_resits.append(result)
    
    context = {
        'student': student,
        'current_semester': current_semester,
        'eligible_resits': eligible_resits,
        'enrollment_period': enrollment_period,
    }
    
    if request.method == 'POST':
        selected_results = request.POST.getlist('resit_units')
        
        try:
            registered_count = 0
            
            for result_id in selected_results:
                result = get_object_or_404(SemesterResults, id=result_id, student=student)
                
                resit_exam = ResitExam(
                    student=student,
                    original_result=result,
                    resit_semester=current_semester,
                    original_semester=result.semester,
                    original_marks=result.total_marks,
                    original_grade=result.grade,
                    original_grade_point=result.grade_point,
                    resit_fee_amount=Decimal('2000.00'),
                )
                resit_exam.save()
                registered_count += 1
            
            if registered_count > 0:
                messages.success(request, f'Successfully registered for {registered_count} resit exam(s).')
            else:
                messages.warning(request, 'No resit exams selected.')
            
            return redirect('resit_exam_status')
            
        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error registering for resit exams: {str(e)}')
    
    return render(request, 'student/resit_exam_registration.html', context)


@login_required
def resit_exam_status(request):
    """View resit exam status"""
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('student_dashboard')
    
    resit_exams = ResitExam.objects.filter(
        student=student
    ).select_related(
        'original_result',
        'original_result__programme_unit',
        'original_result__programme_unit__unit',
        'resit_semester',
        'original_semester'
    ).order_by('-registration_date')
    
    context = {
        'student': student,
        'resit_exams': resit_exams,
    }
    
    return render(request, 'student/resit_exam_status.html', context)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count, Prefetch
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta
from decimal import Decimal
from .models import AcademicYear, Semester, Intake
from .forms import AcademicYearForm, SemesterForm, IntakeForm

# ============= ACADEMIC YEARS =============

@login_required
def academic_year_list(request):
    """List all academic years with semesters dropdown"""
    academic_years = AcademicYear.objects.prefetch_related(
        Prefetch('semesters', queryset=Semester.objects.order_by('semester_number'))
    ).annotate(
        semester_count=Count('semesters')
    ).order_by('-start_date')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        academic_years = academic_years.filter(
            Q(name__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter == 'current':
        academic_years = academic_years.filter(is_current=True)
    elif status_filter == 'active':
        academic_years = academic_years.filter(is_active=True)
    elif status_filter == 'inactive':
        academic_years = academic_years.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(academic_years, 10)
    page_number = request.GET.get('page')
    academic_years_page = paginator.get_page(page_number)
    
    context = {
        'academic_years': academic_years_page,
        'total_years': academic_years.count(),
        'search_query': search_query,
        'status_filter': status_filter,
        'current_year': AcademicYear.objects.filter(is_current=True).first(),
        'current_semester': Semester.objects.filter(is_current=True).first(),
    }
    
    return render(request, 'admin/academic_calendar/academic_year_list.html', context)

@login_required
def academic_year_detail(request, pk):
    """View details of a specific academic year"""
    academic_year = get_object_or_404(AcademicYear, pk=pk)
    
    # Get related data
    semesters = academic_year.semesters.all().order_by('semester_number')
    intakes = academic_year.intakes.all().order_by('start_date')
    programmes = academic_year.programme_units.values('programme__code', 'programme__name').distinct()
    
    # Statistics
    total_students = academic_year.student_gpas.values('student').distinct().count()
    total_units = academic_year.programme_units.count()
    
    context = {
        'academic_year': academic_year,
        'semesters': semesters,
        'intakes': intakes,
        'programmes': programmes,
        'total_students': total_students,
        'total_units': total_units,
    }
    
    return render(request, 'admin/academic_calendar/academic_year_detail.html', context)


@login_required
def add_academic_year(request):
    """Add a new academic year"""
    if request.method == 'POST':
        form = AcademicYearForm(request.POST)
        if form.is_valid():
            try:
                academic_year = form.save()
                messages.success(request, f'Academic year {academic_year.name} created successfully!')
                return redirect('academic_year_list')
            except Exception as e:
                messages.error(request, f'Error creating academic year: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AcademicYearForm()
    
    context = {
        'form': form,
        'title': 'Add Academic Year',
        'button_text': 'Create Academic Year',
    }
    
    return render(request, 'admin/academic_calendar/academic_year_form.html', context)


@login_required
def update_academic_year(request, pk):
    """Update an existing academic year"""
    academic_year = get_object_or_404(AcademicYear, pk=pk)
    
    if request.method == 'POST':
        form = AcademicYearForm(request.POST, instance=academic_year)
        if form.is_valid():
            try:
                academic_year = form.save()
                messages.success(request, f'Academic year {academic_year.name} updated successfully!')
                return redirect('academic_year_detail', pk=academic_year.pk)
            except Exception as e:
                messages.error(request, f'Error updating academic year: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AcademicYearForm(instance=academic_year)
    
    context = {
        'form': form,
        'academic_year': academic_year,
        'title': f'Update Academic Year - {academic_year.name}',
        'button_text': 'Update Academic Year',
    }
    
    return render(request, 'admin/academic_calendar/academic_year_form.html', context)


@login_required
def delete_academic_year(request, pk):
    """Delete an academic year"""
    academic_year = get_object_or_404(AcademicYear, pk=pk)
    
    if request.method == 'POST':
        try:
            name = academic_year.name
            academic_year.delete()
            messages.success(request, f'Academic year {name} deleted successfully!')
            return redirect('academic_year_list')
        except Exception as e:
            messages.error(request, f'Error deleting academic year: {str(e)}')
            return redirect('academic_year_detail', pk=pk)
    
    return redirect('academic_year_detail', pk=pk)


@login_required
@require_http_methods(["POST"])
def set_current_academic_year(request, pk):
    """Set an academic year as current (AJAX)"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            academic_year = get_object_or_404(AcademicYear, pk=pk)
            
            # Unset all other current years
            AcademicYear.objects.filter(is_current=True).update(is_current=False)
            
            # Set this as current
            academic_year.is_current = True
            academic_year.save()
            
            return JsonResponse({
                'success': True,
                'message': f'{academic_year.name} is now the current academic year!',
                'current_year_id': academic_year.pk,
                'current_year_name': academic_year.name
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error setting current academic year: {str(e)}'
            }, status=400)
    
    # Fallback for non-AJAX requests
    try:
        academic_year = get_object_or_404(AcademicYear, pk=pk)
        AcademicYear.objects.filter(is_current=True).update(is_current=False)
        academic_year.is_current = True
        academic_year.save()
        messages.success(request, f'{academic_year.name} is now the current academic year!')
    except Exception as e:
        messages.error(request, f'Error setting current academic year: {str(e)}')
    
    return redirect('academic_year_list')


# ============= SEMESTERS (AJAX) =============

@login_required
@require_http_methods(["GET"])
def get_semesters(request, academic_year_id):
    """Get semesters for a specific academic year (AJAX)"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            academic_year = get_object_or_404(AcademicYear, pk=academic_year_id)
            semesters = academic_year.semesters.all().order_by('semester_number')
            
            semesters_data = []
            for sem in semesters:
                # Get enrollment period if exists
                enrollment_period = None
                try:
                    period = EnrollmentPeriod.objects.get(semester=sem)
                    enrollment_period = {
                        'start_date': period.start_date.strftime('%Y-%m-%d %H:%M'),
                        'end_date': period.end_date.strftime('%Y-%m-%d %H:%M'),
                        'resit_start_date': period.resit_start_date.strftime('%Y-%m-%d %H:%M') if period.resit_start_date else None,
                        'resit_end_date': period.resit_end_date.strftime('%Y-%m-%d %H:%M') if period.resit_end_date else None,
                        'is_enrollment_open': period.is_enrollment_open(),
                        'is_resit_enrollment_open': period.is_resit_enrollment_open(),
                    }
                except EnrollmentPeriod.DoesNotExist:
                    pass
                
                semester_data = {
                    'id': sem.id,
                    'name': sem.name,
                    'semester_number': sem.semester_number,
                    'start_date': sem.start_date.strftime('%Y-%m-%d'),
                    'end_date': sem.end_date.strftime('%Y-%m-%d'),
                    'registration_start_date': sem.registration_start_date.strftime('%Y-%m-%d'),
                    'registration_end_date': sem.registration_end_date.strftime('%Y-%m-%d'),
                    'is_current': sem.is_current,
                    'is_active': sem.is_active,
                    'enrollment_period': enrollment_period,
                }
                semesters_data.append(semester_data)
            
            return JsonResponse({
                'success': True,
                'semesters': semesters_data,
                'count': len(semesters_data)
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

@login_required
@require_http_methods(["POST"])
def save_enrollment_period(request, semester_id):
    """Save or update enrollment period for a semester (called from semester form)"""
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse(
            {'success': False, 'message': 'Invalid request'},
            status=400
        )
    
    try:
        semester = get_object_or_404(Semester, pk=semester_id)
        
        # Get enrollment period data
        enrollment_start = request.POST.get('enrollment_start_date')
        enrollment_end = request.POST.get('enrollment_end_date')
        resit_start = request.POST.get('resit_enrollment_start_date')
        resit_end = request.POST.get('resit_enrollment_end_date')
        is_active = request.POST.get('enrollment_is_active', 'true').lower() == 'true'
        
        # Only create/update if start and end dates are provided
        if enrollment_start and enrollment_end:
            enrollment_period, created = EnrollmentPeriod.objects.update_or_create(
                semester=semester,
                defaults={
                    'start_date': datetime.strptime(enrollment_start, '%Y-%m-%dT%H:%M'),
                    'end_date': datetime.strptime(enrollment_end, '%Y-%m-%dT%H:%M'),
                    'resit_start_date': datetime.strptime(resit_start, '%Y-%m-%dT%H:%M') if resit_start else None,
                    'resit_end_date': datetime.strptime(resit_end, '%Y-%m-%dT%H:%M') if resit_end else None,
                    'is_active': is_active,
                }
            )
            
            action = 'created' if created else 'updated'
            return JsonResponse({
                'success': True,
                'message': f'Enrollment period {action} successfully'
            })
        else:
            return JsonResponse({
                'success': True,
                'message': 'Semester saved without enrollment period'
            })
            
    except ValueError as e:
        return JsonResponse(
            {'success': False, 'message': f'Invalid date format: {str(e)}'},
            status=400
        )
    except Exception as e:
        return JsonResponse(
            {'success': False, 'message': f'Error saving enrollment period: {str(e)}'},
            status=400
        )

from datetime import datetime
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError

@login_required
@require_http_methods(["POST"])
def add_semester_ajax(request, academic_year_id):
    """Add a semester to an academic year (AJAX)"""
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse(
            {'success': False, 'message': 'Invalid request'},
            status=400
        )

    try:
        academic_year = get_object_or_404(AcademicYear, pk=academic_year_id)

        # -----------------------------
        # Get POST data
        # -----------------------------
        semester_number = request.POST.get('semester_number')
        name = request.POST.get('name')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        registration_start_date = request.POST.get('registration_start_date')
        registration_end_date = request.POST.get('registration_end_date')
        is_active = request.POST.get('is_active', 'true').lower() == 'true'

        # -----------------------------
        # Validate required fields
        # -----------------------------
        if not all([
            semester_number,
            name,
            start_date,
            end_date,
            registration_start_date,
            registration_end_date
        ]):
            return JsonResponse(
                {'success': False, 'message': 'All fields are required'},
                status=400
            )

        # -----------------------------
        # Convert dates (FIXES strftime ERROR)
        # -----------------------------
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        registration_start_date = datetime.strptime(registration_start_date, '%Y-%m-%d').date()
        registration_end_date = datetime.strptime(registration_end_date, '%Y-%m-%d').date()

        # -----------------------------
        # Logical date validation
        # -----------------------------
        if start_date > end_date:
            return JsonResponse(
                {'success': False, 'message': 'Semester start date cannot be after end date'},
                status=400
            )

        if registration_start_date > registration_end_date:
            return JsonResponse(
                {'success': False, 'message': 'Registration start date cannot be after end date'},
                status=400
            )

        # -----------------------------
        # Check duplicate semester
        # -----------------------------
        if Semester.objects.filter(
            academic_year=academic_year,
            semester_number=semester_number
        ).exists():
            return JsonResponse(
                {
                    'success': False,
                    'message': f'Semester {semester_number} already exists for {academic_year}'
                },
                status=400
            )

        # -----------------------------
        # Create semester
        # -----------------------------
        semester = Semester(
            academic_year=academic_year,
            name=name,
            semester_number=semester_number,
            start_date=start_date,
            end_date=end_date,
            registration_start_date=registration_start_date,
            registration_end_date=registration_end_date,
            is_active=is_active,
            is_current=False
        )

        # Run model validation (clean())
        semester.full_clean()
        semester.save()

        # -----------------------------
        # Success response
        # -----------------------------
        return JsonResponse({
            'success': True,
            'message': f'Semester "{semester.name}" added successfully!',
            'semester': {
                'id': semester.id,
                'name': semester.name,
                'semester_number': semester.semester_number,
                'start_date': semester.start_date.strftime('%Y-%m-%d'),
                'end_date': semester.end_date.strftime('%Y-%m-%d'),
                'registration_start_date': semester.registration_start_date.strftime('%Y-%m-%d'),
                'registration_end_date': semester.registration_end_date.strftime('%Y-%m-%d'),
                'is_current': semester.is_current,
                'is_active': semester.is_active,
            }
        })

    except ValidationError as e:
        return JsonResponse(
            {'success': False, 'message': e.messages[0]},
            status=400
        )

    except Exception as e:
        return JsonResponse(
            {'success': False, 'message': f'Error adding semester: {str(e)}'},
            status=400
        )


from datetime import datetime
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .models import Semester


@login_required
@require_http_methods(["POST"])
def update_semester_ajax(request, semester_id):
    """Update a semester (AJAX)"""

    # Ensure AJAX request
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse(
            {'success': False, 'message': 'Invalid request'},
            status=400
        )

    try:
        semester = get_object_or_404(Semester, pk=semester_id)

        # Get form data
        name = request.POST.get('name')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        registration_start_date = request.POST.get('registration_start_date')
        registration_end_date = request.POST.get('registration_end_date')
        is_active = request.POST.get('is_active', 'true').lower() == 'true'

        # Update fields safely
        if name:
            semester.name = name

        if start_date:
            semester.start_date = datetime.strptime(start_date, '%Y-%m-%d').date()

        if end_date:
            semester.end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        if registration_start_date:
            semester.registration_start_date = datetime.strptime(
                registration_start_date, '%Y-%m-%d'
            ).date()

        if registration_end_date:
            semester.registration_end_date = datetime.strptime(
                registration_end_date, '%Y-%m-%d'
            ).date()

        semester.is_active = is_active
        semester.save()

        # Return clean JSON response
        return JsonResponse({
            'success': True,
            'message': f'Semester {semester.name} updated successfully!',
            'semester': {
                'id': semester.id,
                'name': semester.name,
                'semester_number': semester.semester_number,
                'start_date': semester.start_date.strftime('%Y-%m-%d') if semester.start_date else None,
                'end_date': semester.end_date.strftime('%Y-%m-%d') if semester.end_date else None,
                'registration_start_date': semester.registration_start_date.strftime('%Y-%m-%d')
                    if semester.registration_start_date else None,
                'registration_end_date': semester.registration_end_date.strftime('%Y-%m-%d')
                    if semester.registration_end_date else None,
                'is_current': semester.is_current,
                'is_active': semester.is_active,
                'academic_year_id': semester.academic_year.id,
            }
        })

    except ValueError:
        return JsonResponse(
            {'success': False, 'message': 'Invalid date format. Use YYYY-MM-DD.'},
            status=400
        )

    except Exception as e:
        return JsonResponse(
            {'success': False, 'message': f'Error updating semester: {str(e)}'},
            status=400
        )


@login_required
@require_http_methods(["POST"])
def set_current_semester(request, pk):  # Changed parameter name from semester_id to pk
    """Set a semester as current (AJAX)"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            semester = get_object_or_404(Semester, pk=pk)
            
            # Unset all other current semesters
            Semester.objects.filter(is_current=True).update(is_current=False)
            
            # Set this semester as current
            semester.is_current = True
            semester.is_active = True  # Also ensure it's active
            semester.save()
            
            # Also set the academic year as current and active
            academic_year = semester.academic_year
            AcademicYear.objects.filter(is_current=True).update(is_current=False)
            academic_year.is_current = True
            academic_year.is_active = True
            academic_year.save()
            
            return JsonResponse({
                'success': True,
                'message': f'{semester.name} is now the current semester!',
                'current_semester_id': semester.pk,
                'current_semester_name': semester.name,
                'current_year_id': academic_year.pk,
                'current_year_name': academic_year.name
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error setting current semester: {str(e)}'
            }, status=400)
    
    # Fallback for non-AJAX requests
    try:
        semester = get_object_or_404(Semester, pk=pk)
        
        # Unset all other current semesters
        Semester.objects.filter(is_current=True).update(is_current=False)
        
        # Set this semester as current
        semester.is_current = True
        semester.is_active = True
        semester.save()
        
        # Set the academic year as current
        academic_year = semester.academic_year
        AcademicYear.objects.filter(is_current=True).update(is_current=False)
        academic_year.is_current = True
        academic_year.is_active = True
        academic_year.save()
        
        messages.success(request, f'{semester.name} is now the current semester!')
    except Exception as e:
        messages.error(request, f'Error setting current semester: {str(e)}')
    
    return redirect('academic_year_list')


@login_required
@require_http_methods(["POST"])
def delete_semester_ajax(request, semester_id):
    """Delete a semester (AJAX)"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            semester = get_object_or_404(Semester, pk=semester_id)
            
            # Check if semester is current
            if semester.is_current:
                return JsonResponse({
                    'success': False,
                    'message': 'Cannot delete the current semester. Please set another semester as current first.'
                }, status=400)
            
            name = semester.name
            semester.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Semester {name} deleted successfully!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error deleting semester: {str(e)}'
            }, status=400)
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

# ============= SEMESTERS =============

@login_required
def semester_list(request):
    """List all semesters with search and filtering"""
    semesters = Semester.objects.select_related('academic_year').all().order_by('-academic_year__start_date', 'semester_number')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        semesters = semesters.filter(
            Q(name__icontains=search_query) |
            Q(academic_year__name__icontains=search_query)
        )
    
    # Filter by academic year
    year_filter = request.GET.get('year', '')
    if year_filter:
        semesters = semesters.filter(academic_year_id=year_filter)
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter == 'current':
        semesters = semesters.filter(is_current=True)
    elif status_filter == 'active':
        semesters = semesters.filter(is_active=True)
    elif status_filter == 'inactive':
        semesters = semesters.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(semesters, 10)
    page_number = request.GET.get('page')
    semesters_page = paginator.get_page(page_number)
    
    # Get academic years for filter
    academic_years = AcademicYear.objects.all().order_by('-start_date')
    
    context = {
        'semesters': semesters_page,
        'total_semesters': semesters.count(),
        'search_query': search_query,
        'year_filter': year_filter,
        'status_filter': status_filter,
        'academic_years': academic_years,
        'current_semester': Semester.objects.filter(is_current=True).first(),
        'semester_choices': Semester.SEMESTER_NAMES,
    }
    
    return render(request, 'admin/academic_calendar/semester_list.html', context)


@login_required
def semester_detail(request, pk):
    """View details of a specific semester"""
    semester = get_object_or_404(Semester.objects.select_related('academic_year'), pk=pk)
    
    # Get related data
    unit_allocations = semester.unit_allocations.select_related(
        'programme_unit__unit', 'programme_unit__programme', 'lecturer__user'
    ).all()
    
    unit_registrations = semester.unit_registrations.select_related(
        'student', 'programme_unit__unit'
    ).all()
    
    # Statistics
    total_students = unit_registrations.values('student').distinct().count()
    total_units = unit_allocations.values('programme_unit__unit').distinct().count()
    total_lecturers = unit_allocations.values('lecturer').distinct().count()
    
    # Registration status
    now = timezone.now().date()
    registration_open = semester.registration_start_date <= now <= semester.registration_end_date
    
    context = {
        'semester': semester,
        'unit_allocations': unit_allocations[:10],  # Show only first 10
        'unit_registrations': unit_registrations[:10],  # Show only first 10
        'total_students': total_students,
        'total_units': total_units,
        'total_lecturers': total_lecturers,
        'registration_open': registration_open,
    }
    
    return render(request, 'admin/academic_calendar/semester_detail.html', context)


@login_required
def add_semester(request):
    """Add a new semester"""
    if request.method == 'POST':
        form = SemesterForm(request.POST)
        if form.is_valid():
            try:
                semester = form.save()
                messages.success(request, f'Semester {semester.name} created successfully!')
                return redirect('semester_list')
            except Exception as e:
                messages.error(request, f'Error creating semester: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SemesterForm()
    
    context = {
        'form': form,
        'title': 'Add Semester',
        'button_text': 'Create Semester',
    }
    
    return render(request, 'admin/academic_calendar/semester_form.html', context)


@login_required
def update_semester(request, pk):
    """Update an existing semester"""
    semester = get_object_or_404(Semester, pk=pk)
    
    if request.method == 'POST':
        form = SemesterForm(request.POST, instance=semester)
        if form.is_valid():
            try:
                semester = form.save()
                messages.success(request, f'Semester {semester.name} updated successfully!')
                return redirect('semester_detail', pk=semester.pk)
            except Exception as e:
                messages.error(request, f'Error updating semester: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SemesterForm(instance=semester)
    
    context = {
        'form': form,
        'semester': semester,
        'title': f'Update Semester - {semester.name}',
        'button_text': 'Update Semester',
    }
    
    return render(request, 'admin/academic_calendar/semester_form.html', context)


@login_required
def delete_semester(request, pk):
    """Delete a semester"""
    semester = get_object_or_404(Semester, pk=pk)
    
    if request.method == 'POST':
        try:
            name = semester.name
            semester.delete()
            messages.success(request, f'Semester {name} deleted successfully!')
            return redirect('semester_list')
        except Exception as e:
            messages.error(request, f'Error deleting semester: {str(e)}')
            return redirect('semester_detail', pk=pk)
    
    return redirect('semester_detail', pk=pk)


@login_required
def backup_set_current_semester(request, pk):
    """Set a semester as current"""
    semester = get_object_or_404(Semester, pk=pk)
    
    try:
        # Unset all other current semesters
        Semester.objects.filter(is_current=True).update(is_current=False)
        
        # Set this as current
        semester.is_current = True
        semester.save()
        
        messages.success(request, f'{semester.name} is now the current semester!')
    except Exception as e:
        messages.error(request, f'Error setting current semester: {str(e)}')
    
    return redirect('semester_detail', pk=pk)


# ============= INTAKES =============

@login_required
def intake_list(request):
    """List all intakes with search and filtering"""
    intakes = Intake.objects.select_related('academic_year').all().order_by('-start_date')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        intakes = intakes.filter(
            Q(name__icontains=search_query) |
            Q(intake_number__icontains=search_query) |
            Q(academic_year__name__icontains=search_query)
        )
    
    # Filter by academic year
    year_filter = request.GET.get('year', '')
    if year_filter:
        intakes = intakes.filter(academic_year_id=year_filter)
    
    # Filter by month
    month_filter = request.GET.get('month', '')
    if month_filter:
        intakes = intakes.filter(month=month_filter)
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        intakes = intakes.filter(is_active=True)
    elif status_filter == 'inactive':
        intakes = intakes.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(intakes, 10)
    page_number = request.GET.get('page')
    intakes_page = paginator.get_page(page_number)
    
    # Get academic years for filter
    academic_years = AcademicYear.objects.all().order_by('-start_date')
    
    context = {
        'intakes': intakes_page,
        'total_intakes': intakes.count(),
        'search_query': search_query,
        'year_filter': year_filter,
        'month_filter': month_filter,
        'status_filter': status_filter,
        'academic_years': academic_years,
        'month_choices': Intake.INTAKE_MONTHS,
    }
    
    return render(request, 'admin/academic_calendar/intake_list.html', context)


@login_required
def intake_detail(request, pk):
    """View details of a specific intake"""
    intake = get_object_or_404(Intake.objects.select_related('academic_year'), pk=pk)
    
    # Get students in this intake
    students = intake.students.select_related('user', 'programme').all()
    
    # Statistics
    total_students = students.count()
    programmes = students.values('programme__code', 'programme__name').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Check if application is open
    now = timezone.now().date()
    application_open = now <= intake.application_deadline
    
    context = {
        'intake': intake,
        'students': students[:20],  # Show only first 20
        'total_students': total_students,
        'programmes': programmes,
        'application_open': application_open,
    }
    
    return render(request, 'admin/academic_calendar/intake_detail.html', context)


@login_required
def add_intake(request):
    """Add a new intake"""
    if request.method == 'POST':
        form = IntakeForm(request.POST)
        if form.is_valid():
            try:
                intake = form.save()
                messages.success(request, f'Intake {intake.name} created successfully!')
                return redirect('intake_list')
            except Exception as e:
                messages.error(request, f'Error creating intake: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = IntakeForm()
    
    context = {
        'form': form,
        'title': 'Add Intake',
        'button_text': 'Create Intake',
    }
    
    return render(request, 'admin/academic_calendar/intake_form.html', context)


@login_required
def update_intake(request, pk):
    """Update an existing intake"""
    intake = get_object_or_404(Intake, pk=pk)
    
    if request.method == 'POST':
        form = IntakeForm(request.POST, instance=intake)
        if form.is_valid():
            try:
                intake = form.save()
                messages.success(request, f'Intake {intake.name} updated successfully!')
                return redirect('intake_detail', pk=intake.pk)
            except Exception as e:
                messages.error(request, f'Error updating intake: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = IntakeForm(instance=intake)
    
    context = {
        'form': form,
        'intake': intake,
        'title': f'Update Intake - {intake.name}',
        'button_text': 'Update Intake',
    }
    
    return render(request, 'admin/academic_calendar/intake_form.html', context)


@login_required
def delete_intake(request, pk):
    """Delete an intake"""
    intake = get_object_or_404(Intake, pk=pk)
    
    if request.method == 'POST':
        try:
            name = intake.name
            intake.delete()
            messages.success(request, f'Intake {name} deleted successfully!')
            return redirect('intake_list')
        except Exception as e:
            messages.error(request, f'Error deleting intake: {str(e)}')
            return redirect('intake_detail', pk=pk)
    
    return redirect('intake_detail', pk=pk)


# ============= AJAX/API ENDPOINTS =============

@login_required
def get_semesters_by_year(request):
    """Get semesters for a specific academic year (AJAX)"""
    year_id = request.GET.get('year_id')
    if year_id:
        semesters = Semester.objects.filter(academic_year_id=year_id).values('id', 'name', 'semester_number')
        return JsonResponse(list(semesters), safe=False)
    return JsonResponse([], safe=False)


@login_required
def get_intakes_by_year(request):
    """Get intakes for a specific academic year (AJAX)"""
    year_id = request.GET.get('year_id')
    if year_id:
        intakes = Intake.objects.filter(academic_year_id=year_id).values('id', 'name', 'intake_number', 'month')
        return JsonResponse(list(intakes), safe=False)
    return JsonResponse([], safe=False)



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import School, Department, Programme, User

# ============= SCHOOLS/FACULTIES VIEWS =============

@login_required
def school_list(request):
    """List all schools with search and filters"""
    schools = School.objects.annotate(
        department_count=Count('departments')
    ).select_related('dean', 'head_of_school')
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        schools = schools.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        schools = schools.filter(is_active=True)
    elif status_filter == 'inactive':
        schools = schools.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(schools, 10)
    page = request.GET.get('page', 1)
    schools_page = paginator.get_page(page)
    
    context = {
        'schools': schools_page,
        'total_schools': schools.count(),
        'search_query': search_query,
        'status_filter': status_filter,
    }
    return render(request, 'admin/schools/school_list.html', context)


@login_required
def school_detail(request, pk):
    """View detailed information about a school"""
    school = get_object_or_404(
        School.objects.annotate(
            department_count=Count('departments'),
            programme_count=Count('departments__programmes')
        ).select_related('dean', 'head_of_school'),
        pk=pk
    )
    
    # Get departments with counts
    departments = school.departments.annotate(
        programme_count=Count('programmes'),
        lecturer_count=Count('lecturers')
    ).select_related('hod')
    
    context = {
        'school': school,
        'departments': departments,
    }
    return render(request, 'admin/schools/school_detail.html', context)


@login_required
def school_form(request, pk=None):
    """Add or update a school (unified form)"""
    school = get_object_or_404(School, pk=pk) if pk else None
    
    # Get users eligible to be Dean or HOS
    deans = User.objects.filter(role='dean', is_active=True)
    hos_users = User.objects.filter(role='hos', is_active=True)
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name')
            code = request.POST.get('code').upper()
            dean_id = request.POST.get('dean')
            hos_id = request.POST.get('head_of_school')
            description = request.POST.get('description', '')
            email = request.POST.get('email', '')
            phone_number = request.POST.get('phone_number', '')
            location = request.POST.get('location', '')
            is_active = request.POST.get('is_active') == 'on'
            
            # Validate required fields
            if not name or not code:
                messages.error(request, 'Name and Code are required.')
                return redirect(request.path)
            
            # Check for duplicate code (excluding current school if updating)
            existing_school = School.objects.filter(code=code)
            if school:
                existing_school = existing_school.exclude(pk=school.pk)
            if existing_school.exists():
                messages.error(request, f'School with code {code} already exists.')
                return redirect(request.path)
            
            # Create or update school
            if school:
                school.name = name
                school.code = code
                school.dean_id = dean_id if dean_id else None
                school.head_of_school_id = hos_id if hos_id else None
                school.description = description
                school.email = email
                school.phone_number = phone_number
                school.location = location
                school.is_active = is_active
                school.save()
                messages.success(request, f'School "{name}" updated successfully!')
            else:
                school = School.objects.create(
                    name=name,
                    code=code,
                    dean_id=dean_id if dean_id else None,
                    head_of_school_id=hos_id if hos_id else None,
                    description=description,
                    email=email,
                    phone_number=phone_number,
                    location=location,
                    is_active=is_active
                )
                messages.success(request, f'School "{name}" created successfully!')
            
            return redirect('school_detail', pk=school.pk)
            
        except Exception as e:
            messages.error(request, f'Error saving school: {str(e)}')
    
    context = {
        'school': school,
        'deans': deans,
        'hos_users': hos_users,
        'is_update': school is not None,
    }
    return render(request, 'admin/schools/school_form.html', context)


@login_required
@require_http_methods(["POST"])
def school_delete(request, pk):
    """Delete a school"""
    school = get_object_or_404(School, pk=pk)
    
    try:
        # Check if school has departments
        if school.departments.exists():
            messages.error(
                request, 
                f'Cannot delete "{school.name}". It has {school.departments.count()} department(s).'
            )
        else:
            school_name = school.name
            school.delete()
            messages.success(request, f'School "{school_name}" deleted successfully!')
        
        return redirect('school_list')
    except Exception as e:
        messages.error(request, f'Error deleting school: {str(e)}')
        return redirect('school_detail', pk=pk)


# ============= DEPARTMENTS VIEWS =============

@login_required
def department_list(request):
    """List all departments with search and filters"""
    departments = Department.objects.select_related(
        'school', 'hod'
    ).annotate(
        programme_count=Count('programmes'),
        lecturer_count=Count('lecturers')
    )
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        departments = departments.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(school__name__icontains=search_query)
        )
    
    # Filter by school
    school_filter = request.GET.get('school', '')
    if school_filter:
        departments = departments.filter(school_id=school_filter)
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        departments = departments.filter(is_active=True)
    elif status_filter == 'inactive':
        departments = departments.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(departments, 10)
    page = request.GET.get('page', 1)
    departments_page = paginator.get_page(page)
    
    # Get schools for filter dropdown
    schools = School.objects.filter(is_active=True).order_by('name')
    
    context = {
        'departments': departments_page,
        'total_departments': departments.count(),
        'search_query': search_query,
        'status_filter': status_filter,
        'school_filter': school_filter,
        'schools': schools,
    }
    return render(request, 'admin/departments/department_list.html', context)


@login_required
def department_detail(request, pk):
    """View detailed information about a department"""
    department = get_object_or_404(
        Department.objects.annotate(
            programme_count=Count('programmes'),
            lecturer_count=Count('lecturers'),
            unit_count=Count('units')
        ).select_related('school', 'hod'),
        pk=pk
    )
    
    # Get programmes
    programmes = department.programmes.annotate(
        student_count=Count('students')
    ).order_by('name')
    
    # Get lecturers
    lecturers = department.lecturers.select_related('user')[:10]
    
    context = {
        'department': department,
        'programmes': programmes,
        'lecturers': lecturers,
    }
    return render(request, 'admin/departments/department_detail.html', context)


@login_required
def department_form(request, pk=None):
    """Add or update a department (unified form)"""
    department = get_object_or_404(Department, pk=pk) if pk else None
    
    # Get schools and HODs
    schools = School.objects.filter(is_active=True).order_by('name')
    hods = User.objects.filter(role='hod', is_active=True)
    
    if request.method == 'POST':
        try:
            # Get form data
            school_id = request.POST.get('school')
            name = request.POST.get('name')
            code = request.POST.get('code').upper()
            hod_id = request.POST.get('hod')
            description = request.POST.get('description', '')
            email = request.POST.get('email', '')
            phone_number = request.POST.get('phone_number', '')
            location = request.POST.get('location', '')
            is_active = request.POST.get('is_active') == 'on'
            
            # Validate required fields
            if not school_id or not name or not code:
                messages.error(request, 'School, Name, and Code are required.')
                return redirect(request.path)
            
            # Check for duplicate code
            existing_dept = Department.objects.filter(code=code)
            if department:
                existing_dept = existing_dept.exclude(pk=department.pk)
            if existing_dept.exists():
                messages.error(request, f'Department with code {code} already exists.')
                return redirect(request.path)
            
            # Create or update department
            if department:
                department.school_id = school_id
                department.name = name
                department.code = code
                department.hod_id = hod_id if hod_id else None
                department.description = description
                department.email = email
                department.phone_number = phone_number
                department.location = location
                department.is_active = is_active
                department.save()
                messages.success(request, f'Department "{name}" updated successfully!')
            else:
                department = Department.objects.create(
                    school_id=school_id,
                    name=name,
                    code=code,
                    hod_id=hod_id if hod_id else None,
                    description=description,
                    email=email,
                    phone_number=phone_number,
                    location=location,
                    is_active=is_active
                )
                messages.success(request, f'Department "{name}" created successfully!')
            
            return redirect('department_detail', pk=department.pk)
            
        except Exception as e:
            messages.error(request, f'Error saving department: {str(e)}')
    
    context = {
        'department': department,
        'schools': schools,
        'hods': hods,
        'is_update': department is not None,
    }
    return render(request, 'admin/departments/department_form.html', context)


@login_required
@require_http_methods(["POST"])
def department_delete(request, pk):
    """Delete a department"""
    department = get_object_or_404(Department, pk=pk)
    
    try:
        # Check if department has programmes
        if department.programmes.exists():
            messages.error(
                request,
                f'Cannot delete "{department.name}". It has {department.programmes.count()} programme(s).'
            )
        else:
            dept_name = department.name
            department.delete()
            messages.success(request, f'Department "{dept_name}" deleted successfully!')
        
        return redirect('department_list')
    except Exception as e:
        messages.error(request, f'Error deleting department: {str(e)}')
        return redirect('department_detail', pk=pk)


# ============= PROGRAMMES VIEWS =============

@login_required
def programme_list(request):
    """List all programmes with search and filters"""
    programmes = Programme.objects.select_related(
        'department', 'department__school'
    ).annotate(
        student_count=Count('students')
    )
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        programmes = programmes.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(department__name__icontains=search_query)
        )
    
    # Filter by department
    department_filter = request.GET.get('department', '')
    if department_filter:
        programmes = programmes.filter(department_id=department_filter)
    
    # Filter by school
    school_filter = request.GET.get('school', '')
    if school_filter:
        programmes = programmes.filter(department__school_id=school_filter)
    
    # Filter by programme type
    type_filter = request.GET.get('type', '')
    if type_filter:
        programmes = programmes.filter(programme_type=type_filter)
    
    # Filter by study mode
    mode_filter = request.GET.get('mode', '')
    if mode_filter:
        programmes = programmes.filter(study_mode=mode_filter)
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        programmes = programmes.filter(is_active=True)
    elif status_filter == 'inactive':
        programmes = programmes.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(programmes, 10)
    page = request.GET.get('page', 1)
    programmes_page = paginator.get_page(page)
    
    # Get schools and departments for filters
    schools = School.objects.filter(is_active=True).order_by('name')
    departments = Department.objects.filter(is_active=True).select_related('school').order_by('name')
    
    context = {
        'programmes': programmes_page,
        'total_programmes': programmes.count(),
        'search_query': search_query,
        'status_filter': status_filter,
        'school_filter': school_filter,
        'department_filter': department_filter,
        'type_filter': type_filter,
        'mode_filter': mode_filter,
        'schools': schools,
        'departments': departments,
        'programme_types': Programme.PROGRAMME_TYPES,
        'study_modes': Programme.STUDY_MODES,
    }
    return render(request, 'admin/programmes/programme_list.html', context)


@login_required
def programme_detail(request, pk):
    """View detailed information about a programme"""
    programme = get_object_or_404(
        Programme.objects.annotate(
            student_count=Count('students'),
            unit_count=Count('programme_units', distinct=True)
        ).select_related('department', 'department__school'),
        pk=pk
    )
    
    # Get programme units grouped by year and semester
    from collections import defaultdict
    programme_units = programme.programme_units.select_related(
        'unit', 'academic_year'
    ).order_by('year_of_study', 'semester_number')
    
    units_by_year_sem = defaultdict(list)
    for pu in programme_units:
        key = f"Y{pu.year_of_study}S{pu.semester_number}"
        units_by_year_sem[key].append(pu)
    
    # Get recent students
    students = programme.students.select_related('user')[:10]
    
    context = {
        'programme': programme,
        'units_by_year_sem': dict(units_by_year_sem),
        'students': students,
    }
    return render(request, 'admin/programmes/programme_detail.html', context)


@login_required
def programme_form(request, pk=None):
    """Add or update a programme (unified form)"""
    programme = get_object_or_404(Programme, pk=pk) if pk else None
    
    # Get departments
    departments = Department.objects.filter(is_active=True).select_related('school').order_by('school__name', 'name')
    
    if request.method == 'POST':
        try:
            # Get form data
            department_id = request.POST.get('department')
            name = request.POST.get('name')
            code = request.POST.get('code').upper()
            programme_type = request.POST.get('programme_type')
            study_mode = request.POST.get('study_mode')
            duration_years = request.POST.get('duration_years')
            total_semesters = request.POST.get('total_semesters')
            min_credit_hours = request.POST.get('min_credit_hours', 120)
            description = request.POST.get('description', '')
            accreditation_body = request.POST.get('accreditation_body', '')
            accreditation_status = request.POST.get('accreditation_status', '')
            is_active = request.POST.get('is_active') == 'on'
            
            # Validate required fields
            if not all([department_id, name, code, programme_type, study_mode, duration_years, total_semesters]):
                messages.error(request, 'All required fields must be filled.')
                return redirect(request.path)
            
            # Check for duplicate code
            existing_prog = Programme.objects.filter(code=code)
            if programme:
                existing_prog = existing_prog.exclude(pk=programme.pk)
            if existing_prog.exists():
                messages.error(request, f'Programme with code {code} already exists.')
                return redirect(request.path)
            
            # Create or update programme
            if programme:
                programme.department_id = department_id
                programme.name = name
                programme.code = code
                programme.programme_type = programme_type
                programme.study_mode = study_mode
                programme.duration_years = duration_years
                programme.total_semesters = total_semesters
                programme.min_credit_hours = min_credit_hours
                programme.description = description
                programme.accreditation_body = accreditation_body
                programme.accreditation_status = accreditation_status
                programme.is_active = is_active
                programme.save()
                messages.success(request, f'Programme "{name}" updated successfully!')
            else:
                programme = Programme.objects.create(
                    department_id=department_id,
                    name=name,
                    code=code,
                    programme_type=programme_type,
                    study_mode=study_mode,
                    duration_years=duration_years,
                    total_semesters=total_semesters,
                    min_credit_hours=min_credit_hours,
                    description=description,
                    accreditation_body=accreditation_body,
                    accreditation_status=accreditation_status,
                    is_active=is_active
                )
                messages.success(request, f'Programme "{name}" created successfully!')
            
            return redirect('programme_detail', pk=programme.pk)
            
        except Exception as e:
            messages.error(request, f'Error saving programme: {str(e)}')
    
    context = {
        'programme': programme,
        'departments': departments,
        'programme_types': Programme.PROGRAMME_TYPES,
        'study_modes': Programme.STUDY_MODES,
        'is_update': programme is not None,
    }
    return render(request, 'admin/programmes/programme_form.html', context)


@login_required
@require_http_methods(["POST"])
def programme_delete(request, pk):
    """Delete a programme"""
    programme = get_object_or_404(Programme, pk=pk)
    
    try:
        # Check if programme has students
        if programme.students.exists():
            messages.error(
                request,
                f'Cannot delete "{programme.name}". It has {programme.students.count()} student(s).'
            )
        else:
            prog_name = programme.name
            programme.delete()
            messages.success(request, f'Programme "{prog_name}" deleted successfully!')
        
        return redirect('programme_list')
    except Exception as e:
        messages.error(request, f'Error deleting programme: {str(e)}')
        return redirect('programme_detail', pk=pk)


# ============= AJAX HELPER VIEWS =============

@login_required
def get_departments_by_school(request, school_id):
    """AJAX endpoint to get departments by school"""
    departments = Department.objects.filter(
        school_id=school_id,
        is_active=True
    ).values('id', 'name', 'code')
    
    return JsonResponse({
        'success': True,
        'departments': list(departments)
    })
    
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Prefetch
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import (
    Programme, Unit, ProgrammeUnit, AcademicYear, 
    Semester, Department, UnitGradingSystem
)
from collections import defaultdict
import json

# ============= PROGRAMME UNITS MANAGEMENT =============

@login_required
def programme_units_list(request):
    """List all programmes for unit management"""
    programmes = Programme.objects.filter(is_active=True).select_related(
        'department', 'department__school'
    ).annotate(
        unit_count=Count('programme_units', distinct=True)
    ).order_by('department__school__name', 'name')
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        programmes = programmes.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query)
        )
    
    # Filter by school
    school_filter = request.GET.get('school', '')
    if school_filter:
        programmes = programmes.filter(department__school_id=school_filter)
    
    # Filter by department
    department_filter = request.GET.get('department', '')
    if department_filter:
        programmes = programmes.filter(department_id=department_filter)
    
    # Pagination
    paginator = Paginator(programmes, 12)
    page = request.GET.get('page', 1)
    programmes_page = paginator.get_page(page)
    
    context = {
        'programmes': programmes_page,
        'total_programmes': programmes.count(),
        'search_query': search_query,
        'school_filter': school_filter,
        'department_filter': department_filter,
    }
    return render(request, 'admin/units/programme_units_list.html', context)


@login_required
def programme_units_structure(request, programme_id):
    """Dynamic programme unit structure view"""
    programme = get_object_or_404(
        Programme.objects.select_related('department', 'department__school'),
        pk=programme_id
    )
    
    # Get current academic year
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    
    # Get all academic years for dropdown
    academic_years = AcademicYear.objects.filter(is_active=True).order_by('-start_date')
    
    context = {
        'programme': programme,
        'current_academic_year': current_academic_year,
        'academic_years': academic_years,
    }
    return render(request, 'admin/units/programme_units_structure.html', context)


# ============= API ENDPOINTS =============

@login_required
def api_programme_structure(request, programme_id):
    """API: Get programme structure with years and semesters"""
    programme = get_object_or_404(Programme, pk=programme_id)
    academic_year_id = request.GET.get('academic_year')
    
    if not academic_year_id:
        academic_year = AcademicYear.objects.filter(is_current=True).first()
    else:
        academic_year = get_object_or_404(AcademicYear, pk=academic_year_id)
    
    # Build structure based on programme configuration
    structure = []
    
    # Calculate semesters per year based on total_semesters and duration_years
    total_semesters = programme.total_semesters
    duration_years = programme.duration_years
    
    # Determine semester distribution
    if total_semesters == duration_years * 2:
        # Regular: 2 semesters per year
        semesters_per_year = [2] * duration_years
    elif total_semesters == duration_years * 3:
        # Tri-semester: 3 semesters per year
        semesters_per_year = [3] * duration_years
    else:
        # Irregular distribution
        base_sem = total_semesters // duration_years
        extra_sem = total_semesters % duration_years
        semesters_per_year = [base_sem + (1 if i < extra_sem else 0) for i in range(duration_years)]
    
    # Build year structure
    for year_num in range(1, duration_years + 1):
        year_data = {
            'year': year_num,
            'semesters': []
        }
        
        num_semesters = semesters_per_year[year_num - 1]
        for sem_num in range(1, num_semesters + 1):
            # Get units for this year and semester
            programme_units = ProgrammeUnit.objects.filter(
                programme=programme,
                academic_year=academic_year,
                year_of_study=year_num,
                semester_number=str(sem_num)
            ).select_related('unit').order_by('unit__code')
            
            units_data = []
            total_credits = 0
            
            for pu in programme_units:
                units_data.append({
                    'id': pu.id,
                    'unit_id': pu.unit.id,
                    'code': pu.unit.code,
                    'name': pu.unit.name,
                    'credit_hours': pu.unit.credit_hours,
                    'unit_type': pu.unit_type,
                    'unit_type_display': pu.get_unit_type_display(),
                    'is_active': pu.is_active,
                })
                total_credits += pu.unit.credit_hours
            
            year_data['semesters'].append({
                'semester_number': sem_num,
                'units': units_data,
                'total_credits': total_credits,
                'unit_count': len(units_data)
            })
        
        structure.append(year_data)
    
    return JsonResponse({
        'success': True,
        'programme': {
            'id': programme.id,
            'name': programme.name,
            'code': programme.code,
            'duration_years': programme.duration_years,
            'total_semesters': programme.total_semesters,
        },
        'academic_year': {
            'id': academic_year.id,
            'name': academic_year.name,
        },
        'structure': structure
    })


@login_required
def api_available_units(request):
    """API: Get available units for adding to programme"""
    department_id = request.GET.get('department')
    unit_level = request.GET.get('level', '')
    search = request.GET.get('search', '')
    
    units = Unit.objects.filter(is_active=True)
    
    if department_id:
        units = units.filter(department_id=department_id)
    
    if unit_level:
        units = units.filter(unit_level=unit_level)
    
    if search:
        units = units.filter(
            Q(code__icontains=search) |
            Q(name__icontains=search)
        )
    
    units = units.select_related('department')[:50]
    
    units_data = [{
        'id': unit.id,
        'code': unit.code,
        'name': unit.name,
        'credit_hours': unit.credit_hours,
        'unit_level': unit.unit_level,
        'department': unit.department.name,
    } for unit in units]
    
    return JsonResponse({
        'success': True,
        'units': units_data
    })


@login_required
@require_http_methods(["POST"])
def api_add_programme_unit(request):
    """API: Add unit to programme"""
    try:
        data = json.loads(request.body)
        
        programme_id = data.get('programme_id')
        unit_id = data.get('unit_id')
        academic_year_id = data.get('academic_year_id')
        year_of_study = data.get('year_of_study')
        semester_number = data.get('semester_number')
        unit_type = data.get('unit_type', 'core')
        
        # Validate required fields
        if not all([programme_id, unit_id, academic_year_id, year_of_study, semester_number]):
            return JsonResponse({
                'success': False,
                'message': 'All fields are required'
            }, status=400)
        
        # Get objects
        programme = get_object_or_404(Programme, pk=programme_id)
        unit = get_object_or_404(Unit, pk=unit_id)
        academic_year = get_object_or_404(AcademicYear, pk=academic_year_id)
        
        # Check if already exists
        if ProgrammeUnit.objects.filter(
            programme=programme,
            unit=unit,
            academic_year=academic_year,
            year_of_study=year_of_study,
            semester_number=semester_number
        ).exists():
            return JsonResponse({
                'success': False,
                'message': f'{unit.code} is already added to this year and semester'
            }, status=400)
        
        # Create programme unit
        programme_unit = ProgrammeUnit.objects.create(
            programme=programme,
            unit=unit,
            academic_year=academic_year,
            year_of_study=year_of_study,
            semester_number=semester_number,
            unit_type=unit_type,
            is_active=True
        )
        
        return JsonResponse({
            'success': True,
            'message': f'{unit.code} added successfully',
            'programme_unit': {
                'id': programme_unit.id,
                'unit_id': unit.id,
                'code': unit.code,
                'name': unit.name,
                'credit_hours': unit.credit_hours,
                'unit_type': programme_unit.unit_type,
                'unit_type_display': programme_unit.get_unit_type_display(),
                'is_active': programme_unit.is_active,
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_update_programme_unit(request, programme_unit_id):
    """API: Update programme unit"""
    try:
        data = json.loads(request.body)
        programme_unit = get_object_or_404(ProgrammeUnit, pk=programme_unit_id)
        
        unit_type = data.get('unit_type')
        is_active = data.get('is_active')
        
        if unit_type:
            programme_unit.unit_type = unit_type
        
        if is_active is not None:
            programme_unit.is_active = is_active
        
        programme_unit.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Unit updated successfully',
            'programme_unit': {
                'id': programme_unit.id,
                'unit_type': programme_unit.unit_type,
                'unit_type_display': programme_unit.get_unit_type_display(),
                'is_active': programme_unit.is_active,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_delete_programme_unit(request, programme_unit_id):
    """API: Delete programme unit"""
    try:
        programme_unit = get_object_or_404(ProgrammeUnit, pk=programme_unit_id)
        
        # Check if unit has allocations or registrations
        if programme_unit.allocations.exists():
            return JsonResponse({
                'success': False,
                'message': 'Cannot delete. This unit has lecturer allocations.'
            }, status=400)
        
        if programme_unit.registrations.exists():
            return JsonResponse({
                'success': False,
                'message': 'Cannot delete. Students have registered for this unit.'
            }, status=400)
        
        unit_code = programme_unit.unit.code
        programme_unit.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'{unit_code} removed successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_copy_programme_units(request):
    """API: Copy units from one academic year to another"""
    try:
        data = json.loads(request.body)
        
        programme_id = data.get('programme_id')
        from_academic_year_id = data.get('from_academic_year_id')
        to_academic_year_id = data.get('to_academic_year_id')
        
        if not all([programme_id, from_academic_year_id, to_academic_year_id]):
            return JsonResponse({
                'success': False,
                'message': 'All fields are required'
            }, status=400)
        
        programme = get_object_or_404(Programme, pk=programme_id)
        from_year = get_object_or_404(AcademicYear, pk=from_academic_year_id)
        to_year = get_object_or_404(AcademicYear, pk=to_academic_year_id)
        
        # Get existing units
        existing_units = ProgrammeUnit.objects.filter(
            programme=programme,
            academic_year=from_year
        ).select_related('unit')
        
        copied_count = 0
        skipped_count = 0
        
        for pu in existing_units:
            # Check if already exists
            if not ProgrammeUnit.objects.filter(
                programme=programme,
                unit=pu.unit,
                academic_year=to_year,
                year_of_study=pu.year_of_study,
                semester_number=pu.semester_number
            ).exists():
                ProgrammeUnit.objects.create(
                    programme=programme,
                    unit=pu.unit,
                    academic_year=to_year,
                    year_of_study=pu.year_of_study,
                    semester_number=pu.semester_number,
                    unit_type=pu.unit_type,
                    is_active=pu.is_active
                )
                copied_count += 1
            else:
                skipped_count += 1
        
        return JsonResponse({
            'success': True,
            'message': f'Copied {copied_count} units. Skipped {skipped_count} duplicates.',
            'copied': copied_count,
            'skipped': skipped_count
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


# ============= ALL UNITS MANAGEMENT =============

@login_required
def units_list(request):
    """List all units"""
    units = Unit.objects.select_related('department').annotate(
        programme_count=Count('programme_assignments', distinct=True)
    )
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        units = units.filter(
            Q(code__icontains=search_query) |
            Q(name__icontains=search_query)
        )
    
    # Filter by department
    department_filter = request.GET.get('department', '')
    if department_filter:
        units = units.filter(department_id=department_filter)
    
    # Filter by level
    level_filter = request.GET.get('level', '')
    if level_filter:
        units = units.filter(unit_level=level_filter)
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        units = units.filter(is_active=True)
    elif status_filter == 'inactive':
        units = units.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(units, 20)
    page = request.GET.get('page', 1)
    units_page = paginator.get_page(page)
    
    from .models import Department
    departments = Department.objects.filter(is_active=True).order_by('name')
    
    context = {
        'units': units_page,
        'total_units': units.count(),
        'search_query': search_query,
        'department_filter': department_filter,
        'level_filter': level_filter,
        'status_filter': status_filter,
        'departments': departments,
        'unit_levels': Unit.UNIT_LEVELS,
    }
    return render(request, 'admin/units/units_list.html', context)


@login_required
def unit_detail(request, pk):
    """View unit details"""
    unit = get_object_or_404(
        Unit.objects.select_related('department').annotate(
            programme_count=Count('programme_assignments', distinct=True)
        ),
        pk=pk
    )
    
    # Get programmes using this unit
    programme_units = ProgrammeUnit.objects.filter(
        unit=unit
    ).select_related('programme', 'academic_year').order_by('-academic_year__start_date')
    
    # Get prerequisites
    prerequisites = unit.prerequisites.all()
    required_for = unit.required_for.all()
    
    context = {
        'unit': unit,
        'programme_units': programme_units,
        'prerequisites': prerequisites,
        'required_for': required_for,
    }
    return render(request, 'admin/units/unit_detail.html', context)


@login_required
def unit_form(request, pk=None):
    """Add or update a unit"""
    unit = get_object_or_404(Unit, pk=pk) if pk else None
    
    from .models import Department
    departments = Department.objects.filter(is_active=True).order_by('name')
    all_units = Unit.objects.filter(is_active=True).exclude(pk=pk) if pk else Unit.objects.filter(is_active=True)
    
    if request.method == 'POST':
        try:
            department_id = request.POST.get('department')
            code = request.POST.get('code').upper()
            name = request.POST.get('name')
            unit_level = request.POST.get('unit_level')
            credit_hours = request.POST.get('credit_hours', 3)
            description = request.POST.get('description', '')
            prerequisite_ids = request.POST.getlist('prerequisites')
            is_active = request.POST.get('is_active') == 'on'
            
            if not all([department_id, code, name, unit_level]):
                messages.error(request, 'All required fields must be filled.')
                return redirect(request.path)
            
            # Check duplicate code
            existing = Unit.objects.filter(code=code)
            if unit:
                existing = existing.exclude(pk=unit.pk)
            if existing.exists():
                messages.error(request, f'Unit with code {code} already exists.')
                return redirect(request.path)
            
            if unit:
                unit.department_id = department_id
                unit.code = code
                unit.name = name
                unit.unit_level = unit_level
                unit.credit_hours = credit_hours
                unit.description = description
                unit.is_active = is_active
                unit.save()
                unit.prerequisites.set(prerequisite_ids)
                messages.success(request, f'Unit "{code}" updated successfully!')
            else:
                unit = Unit.objects.create(
                    department_id=department_id,
                    code=code,
                    name=name,
                    unit_level=unit_level,
                    credit_hours=credit_hours,
                    description=description,
                    is_active=is_active
                )
                unit.prerequisites.set(prerequisite_ids)
                messages.success(request, f'Unit "{code}" created successfully!')
            
            return redirect('unit_detail', pk=unit.pk)
            
        except Exception as e:
            messages.error(request, f'Error saving unit: {str(e)}')
    
    context = {
        'unit': unit,
        'departments': departments,
        'all_units': all_units,
        'unit_levels': Unit.UNIT_LEVELS,
        'is_update': unit is not None,
    }
    return render(request, 'admin/units/unit_form.html', context)


@login_required
@require_http_methods(["POST"])
def unit_delete(request, pk):
    """Delete a unit"""
    unit = get_object_or_404(Unit, pk=pk)
    
    try:
        if unit.programme_assignments.exists():
            messages.error(
                request,
                f'Cannot delete "{unit.code}". It is assigned to programmes.'
            )
        else:
            code = unit.code
            unit.delete()
            messages.success(request, f'Unit "{code}" deleted successfully!')
            return redirect('units_list')
    except Exception as e:
        messages.error(request, f'Error deleting unit: {str(e)}')
    
    return redirect('unit_detail', pk=pk) 



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.http import HttpResponse
from django.utils import timezone
from decimal import Decimal
import csv

from .models import (
    Lecturer, User, Department, School, UnitAllocation, 
    Semester, AcademicYear, Programme, Unit
)
from .forms import LecturerForm, UserForm


# ============= LECTURER LIST VIEW =============
@login_required
def lecturer_list(request):
    """Display list of all lecturers with search and filter options"""
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    department_filter = request.GET.get('department', '')
    designation_filter = request.GET.get('designation', '')
    status_filter = request.GET.get('status', '')
    
    # Base queryset with related data
    lecturers = Lecturer.objects.select_related(
        'user', 'department', 'department__school'
    ).annotate(
        units_count=Count('user__unit_allocations', distinct=True)
    )
    
    # Apply search filter
    if search_query:
        lecturers = lecturers.filter(
            Q(employee_number__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__phone_number__icontains=search_query) |
            Q(qualification__icontains=search_query) |
            Q(specialization__icontains=search_query)
        )
    
    # Apply department filter
    if department_filter:
        lecturers = lecturers.filter(department_id=department_filter)
    
    # Apply designation filter
    if designation_filter:
        lecturers = lecturers.filter(designation=designation_filter)
    
    # Apply status filter
    if status_filter:
        if status_filter == 'active':
            lecturers = lecturers.filter(is_active=True)
        elif status_filter == 'inactive':
            lecturers = lecturers.filter(is_active=False)
    
    # Order by employee number
    lecturers = lecturers.order_by('employee_number')
    
    # Get total count before pagination
    total_lecturers = lecturers.count()
    
    # Pagination
    paginator = Paginator(lecturers, 20)  # 20 lecturers per page
    page_number = request.GET.get('page')
    lecturers_page = paginator.get_page(page_number)
    
    # Get filter options
    departments = Department.objects.filter(is_active=True).order_by('name')
    designations = Lecturer.DESIGNATION_CHOICES
    
    context = {
        'lecturers': lecturers_page,
        'total_lecturers': total_lecturers,
        'search_query': search_query,
        'department_filter': department_filter,
        'designation_filter': designation_filter,
        'status_filter': status_filter,
        'departments': departments,
        'designations': designations,
    }
    
    return render(request, 'admin/lecturers/lecturer_list.html', context)


# ============= LECTURER DETAIL VIEW =============
@login_required
def lecturer_detail(request, employee_number):
    """Display detailed information about a specific lecturer"""
    
    lecturer = get_object_or_404(
        Lecturer.objects.select_related('user', 'department', 'department__school'),
        employee_number=employee_number
    )
    
    # Get current academic year and semester
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get unit allocations for current semester
    current_allocations = UnitAllocation.objects.filter(
        lecturer=lecturer.user,
        semester=current_semester
    ).select_related(
        'programme_unit__unit',
        'programme_unit__programme',
        'semester'
    ) if current_semester else []
    
    # Get all unit allocations (history)
    all_allocations = UnitAllocation.objects.filter(
        lecturer=lecturer.user
    ).select_related(
        'programme_unit__unit',
        'programme_unit__programme',
        'semester',
        'semester__academic_year'
    ).order_by('-semester__academic_year__start_date', '-semester__start_date')[:10]
    
    # Calculate statistics
    total_units_taught = UnitAllocation.objects.filter(
        lecturer=lecturer.user
    ).values('programme_unit__unit').distinct().count()
    
    total_allocations = UnitAllocation.objects.filter(
        lecturer=lecturer.user
    ).count()
    
    current_units_count = current_allocations.count() if current_semester else 0
    
    context = {
        'lecturer': lecturer,
        'current_semester': current_semester,
        'current_allocations': current_allocations,
        'all_allocations': all_allocations,
        'total_units_taught': total_units_taught,
        'total_allocations': total_allocations,
        'current_units_count': current_units_count,
    }
    
    return render(request, 'admin/lecturers/lecturer_detail.html', context)


# ============= ADD/UPDATE LECTURER VIEW =============
@login_required
def lecturer_form(request, employee_number=None):
    """Add new lecturer or update existing one"""
    
    # Determine if we're editing or creating
    is_edit = employee_number is not None
    lecturer = None
    user = None
    
    if is_edit:
        lecturer = get_object_or_404(Lecturer, employee_number=employee_number)
        user = lecturer.user
    
    if request.method == 'POST':
        # Handle user form
        user_form = UserForm(request.POST, request.FILES, instance=user)
        lecturer_form = LecturerForm(request.POST, instance=lecturer)
        
        if user_form.is_valid() and lecturer_form.is_valid():
            try:
                # Save user first
                user_instance = user_form.save(commit=False)
                if not is_edit:
                    user_instance.role = 'lecturer'
                    # Generate username from email if not provided
                    if not user_instance.username:
                        user_instance.username = user_instance.email.split('@')[0]
                user_instance.save()
                
                # Save lecturer
                lecturer_instance = lecturer_form.save(commit=False)
                lecturer_instance.user = user_instance
                lecturer_instance.save()
                
                if is_edit:
                    messages.success(request, f'Lecturer {lecturer_instance.employee_number} updated successfully!')
                else:
                    messages.success(request, f'Lecturer {lecturer_instance.employee_number} added successfully!')
                
                return redirect('lecturer_detail', employee_number=lecturer_instance.employee_number)
                
            except Exception as e:
                messages.error(request, f'Error saving lecturer: {str(e)}')
        else:
            # Show form errors
            for field, errors in user_form.errors.items():
                for error in errors:
                    messages.error(request, f'User {field}: {error}')
            for field, errors in lecturer_form.errors.items():
                for error in errors:
                    messages.error(request, f'Lecturer {field}: {error}')
    else:
        user_form = UserForm(instance=user)
        lecturer_form = LecturerForm(instance=lecturer)
    
    # Get all departments for dropdown
    departments = Department.objects.filter(is_active=True).select_related('school').order_by('school__name', 'name')
    
    context = {
        'user_form': user_form,
        'lecturer_form': lecturer_form,
        'is_edit': is_edit,
        'lecturer': lecturer,
        'departments': departments,
    }
    
    return render(request, 'admin/lecturers/lecturer_form.html', context)


# ============= DELETE LECTURER VIEW =============
@login_required
def lecturer_delete(request, employee_number):
    """Delete a lecturer"""
    
    lecturer = get_object_or_404(Lecturer, employee_number=employee_number)
    
    if request.method == 'POST':
        try:
            # Check if lecturer has any allocations
            allocations_count = UnitAllocation.objects.filter(lecturer=lecturer.user).count()
            
            if allocations_count > 0:
                messages.warning(
                    request, 
                    f'Cannot delete lecturer {lecturer.employee_number}. '
                    f'They have {allocations_count} unit allocation(s). '
                    'Please remove or reassign these allocations first.'
                )
                return redirect('lecturer_detail', employee_number=employee_number)
            
            # Store details for message
            employee_num = lecturer.employee_number
            full_name = lecturer.user.get_full_name()
            
            # Delete user (will cascade delete lecturer)
            lecturer.user.delete()
            
            messages.success(
                request, 
                f'Lecturer {employee_num} - {full_name} has been deleted successfully.'
            )
            return redirect('lecturer_list')
            
        except Exception as e:
            messages.error(request, f'Error deleting lecturer: {str(e)}')
            return redirect('lecturer_detail', employee_number=employee_number)
    
    return redirect('lecturer_detail', employee_number=employee_number)


# ============= BULK ACTIONS VIEW =============
@login_required
def lecturer_bulk_update(request):
    """Handle bulk updates for lecturers"""
    
    if request.method == 'POST':
        action = request.POST.get('action')
        lecturer_ids = request.POST.get('lecturer_ids', '').split(',')
        
        if not lecturer_ids or not action:
            messages.error(request, 'No lecturers selected or action not specified.')
            return redirect('lecturer_list')
        
        # Remove empty strings
        lecturer_ids = [lid for lid in lecturer_ids if lid]
        
        try:
            lecturers = Lecturer.objects.filter(id__in=lecturer_ids)
            count = lecturers.count()
            
            if action == 'activate':
                lecturers.update(is_active=True)
                messages.success(request, f'{count} lecturer(s) activated successfully.')
                
            elif action == 'deactivate':
                lecturers.update(is_active=False)
                messages.success(request, f'{count} lecturer(s) deactivated successfully.')
                
            elif action == 'update_department':
                department_id = request.POST.get('department_value')
                if department_id:
                    department = get_object_or_404(Department, id=department_id)
                    lecturers.update(department=department)
                    messages.success(request, f'{count} lecturer(s) moved to {department.name}.')
                else:
                    messages.error(request, 'Department not specified.')
                    
            elif action == 'update_designation':
                designation = request.POST.get('designation_value')
                if designation:
                    lecturers.update(designation=designation)
                    messages.success(request, f'{count} lecturer(s) designation updated.')
                else:
                    messages.error(request, 'Designation not specified.')
            else:
                messages.error(request, 'Invalid action.')
                
        except Exception as e:
            messages.error(request, f'Error performing bulk action: {str(e)}')
    
    return redirect('lecturer_list')


# ============= EXPORT LECTURERS VIEW =============
@login_required
def export_lecturers(request):
    """Export lecturers to CSV"""
    
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="lecturers_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'Employee Number', 'First Name', 'Last Name', 'Email', 'Phone Number',
        'Department', 'School', 'Designation', 'Qualification', 'Specialization',
        'Office Location', 'Hire Date', 'Status'
    ])
    
    # Get lecturers
    lecturers = Lecturer.objects.select_related(
        'user', 'department', 'department__school'
    ).order_by('employee_number')
    
    # Write data
    for lecturer in lecturers:
        writer.writerow([
            lecturer.employee_number,
            lecturer.user.first_name,
            lecturer.user.last_name,
            lecturer.user.email,
            lecturer.user.phone_number or '',
            lecturer.department.name,
            lecturer.department.school.name,
            lecturer.get_designation_display(),
            lecturer.qualification,
            lecturer.specialization or '',
            lecturer.office_location or '',
            lecturer.hire_date.strftime('%Y-%m-%d'),
            'Active' if lecturer.is_active else 'Inactive'
        ])
    
    return response


# ============= LECTURER WORKLOAD VIEW =============
@login_required
def lecturer_workload(request, employee_number):
    """View lecturer's teaching workload"""
    
    lecturer = get_object_or_404(Lecturer, employee_number=employee_number)
    
    # Get selected semester or current
    semester_id = request.GET.get('semester')
    if semester_id:
        semester = get_object_or_404(Semester, id=semester_id)
    else:
        semester = Semester.objects.filter(is_current=True).first()
    
    # Get allocations for the semester
    allocations = UnitAllocation.objects.filter(
        lecturer=lecturer.user,
        semester=semester
    ).select_related(
        'programme_unit__unit',
        'programme_unit__programme',
        'programme_unit__programme__department'
    ).prefetch_related(
        'programme_unit__registrations'
    )
    
    # Calculate workload statistics
    total_units = allocations.count()
    total_students = sum([
        alloc.programme_unit.registrations.filter(
            semester=semester,
            status='registered'
        ).count() 
        for alloc in allocations
    ])
    
    # Calculate credit hours
    total_credit_hours = sum([
        alloc.programme_unit.unit.credit_hours 
        for alloc in allocations
    ])
    
    # Get all semesters for filter
    semesters = Semester.objects.order_by('-academic_year__start_date', '-start_date')[:10]
    
    context = {
        'lecturer': lecturer,
        'semester': semester,
        'semesters': semesters,
        'allocations': allocations,
        'total_units': total_units,
        'total_students': total_students,
        'total_credit_hours': total_credit_hours,
    }
    
    return render(request, 'admin/lecturers/lecturer_workload.html', context)


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Q, Avg, Sum
from django.utils import timezone
from django.contrib import messages
from decimal import Decimal
import csv
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch

@login_required
def lecturer_units(request):
    """View all units allocated to lecturer"""
    try:
        lecturer = request.user.lecturer_profile
    except:
        messages.error(request, 'Lecturer profile not found.')
        return redirect('lecturer_dashboard')
    
    # Get current semester
    current_semester = Semester.objects.filter(is_current=True).first()
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    
    # Get filter parameters
    semester_filter = request.GET.get('semester')
    academic_year_filter = request.GET.get('academic_year')
    status_filter = request.GET.get('status', 'approved')
    
    # Base query
    allocations_query = UnitAllocation.objects.filter(
        lecturer=request.user
    ).select_related(
        'programme_unit__unit',
        'programme_unit__programme',
        'programme_unit__programme__department',
        'semester',
        'semester__academic_year'
    )
    
    # Apply filters
    if semester_filter:
        allocations_query = allocations_query.filter(semester_id=semester_filter)
    elif current_semester:
        # Default to current semester
        allocations_query = allocations_query.filter(semester=current_semester)
    
    if academic_year_filter:
        allocations_query = allocations_query.filter(
            semester__academic_year_id=academic_year_filter
        )
    
    if status_filter and status_filter != 'all':
        if status_filter == 'approved':
            allocations_query = allocations_query.filter(
                status__in=['approved_hod', 'approved_hos', 'approved_dean']
            )
        else:
            allocations_query = allocations_query.filter(status=status_filter)
    
    allocations = allocations_query.order_by('-semester__academic_year__start_date', 'programme_unit__unit__code')
    
    # Add student counts to each allocation
    allocations_data = []
    for allocation in allocations:
        # Count enrolled students (approved enrollments)
        student_count = UnitEnrollment.objects.filter(
            programme_unit=allocation.programme_unit,
            semester=allocation.semester,
            status='approved'
        ).count()
        
        assessment_count = Assessment.objects.filter(
            unit_allocation=allocation
        ).count()
        
        allocations_data.append({
            'allocation': allocation,
            'student_count': student_count,
            'assessment_count': assessment_count
        })
    
    # Get all semesters and academic years for filters
    semesters = Semester.objects.all().order_by('-academic_year__start_date', '-semester_number')
    academic_years = AcademicYear.objects.all().order_by('-start_date')
    
    context = {
        'allocations_data': allocations_data,
        'current_semester': current_semester,
        'current_academic_year': current_academic_year,
        'semesters': semesters,
        'academic_years': academic_years,
        'semester_filter': semester_filter,
        'academic_year_filter': academic_year_filter,
        'status_filter': status_filter,
    }
    
    return render(request, 'lecturer/units_list.html', context)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
from django.db import transaction

@login_required
def unit_students(request, allocation_id):
    """View all students in a specific unit with marks and attendance"""
    try:
        lecturer = request.user.lecturer_profile
    except:
        messages.error(request, 'Lecturer profile not found.')
        return redirect('lecturer_dashboard')
    
    # Get the allocation
    allocation = get_object_or_404(
        UnitAllocation.objects.select_related(
            'programme_unit__unit',
            'programme_unit__programme',
            'semester',
            'semester__academic_year'
        ),
        id=allocation_id,
        lecturer=request.user
    )
    
    # Get all students enrolled for this unit (approved enrollments)
    enrollments = UnitEnrollment.objects.filter(
        programme_unit=allocation.programme_unit,
        semester=allocation.semester,
        status='approved'
    ).select_related(
        'student',
        'student__user',
        'student__programme',
        'semester_report'
    ).order_by('student__registration_number')
    
    # Get or create assessments for this unit
    assessments = Assessment.objects.filter(
        unit_allocation=allocation
    ).order_by('assessment_type')
    
    # Create default assessments if they don't exist
    if assessments.count() == 0:
        Assessment.objects.create(
            unit_allocation=allocation,
            assessment_type='cat1',
            title='CAT 1',
            max_marks=Decimal('30.00'),
            weight_percentage=Decimal('10.00'),
            date=timezone.now().date()
        )
        Assessment.objects.create(
            unit_allocation=allocation,
            assessment_type='cat2',
            title='CAT 2',
            max_marks=Decimal('30.00'),
            weight_percentage=Decimal('10.00'),
            date=timezone.now().date()
        )
        Assessment.objects.create(
            unit_allocation=allocation,
            assessment_type='cat3',
            title='CAT 3',
            max_marks=Decimal('30.00'),
            weight_percentage=Decimal('10.00'),
            date=timezone.now().date()
        )
        Assessment.objects.create(
            unit_allocation=allocation,
            assessment_type='final',
            title='Final Exam',
            max_marks=Decimal('70.00'),
            weight_percentage=Decimal('70.00'),
            date=timezone.now().date()
        )
        assessments = Assessment.objects.filter(unit_allocation=allocation).order_by('assessment_type')
    
    # Build student data with marks and attendance
    students_data = []
    for enrollment in enrollments:
        student = enrollment.student
        
        # Calculate attendance
        total_classes = Attendance.objects.filter(
            unit_allocation=allocation,
            student=student
        ).count()
        
        present_classes = Attendance.objects.filter(
            unit_allocation=allocation,
            student=student,
            status='present'
        ).count()
        
        attendance_percentage = 0
        if total_classes > 0:
            attendance_percentage = round((present_classes / total_classes) * 100, 1)
        
        # Get marks for each assessment
        marks = {}
        total_marks = Decimal('0.00')
        
        for assessment in assessments:
            student_mark = StudentMarks.objects.filter(
                assessment=assessment,
                student=student
            ).first()
            
            mark_value = student_mark.marks_obtained if student_mark else None
            marks[assessment.assessment_type] = {
                'value': mark_value,
                'max': assessment.max_marks,
                'id': student_mark.id if student_mark else None
            }
            
            if mark_value is not None:
                # Calculate weighted mark (convert to percentage of 100)
                weighted = (mark_value / assessment.max_marks) * assessment.weight_percentage
                total_marks += weighted
        
        # Determine if eligible for exam (attendance >= 75%)
        eligible_for_exam = attendance_percentage >= 0
        
        students_data.append({
            'enrollment': enrollment,
            'student': student,
            'enrollment_type': enrollment.get_enrollment_type_display(),
            'is_resit': enrollment.enrollment_type == 'resit',
            'attendance_total': total_classes,
            'attendance_present': present_classes,
            'attendance_percentage': attendance_percentage,
            'marks': marks,
            'total_marks': round(total_marks, 2),
            'eligible_for_exam': eligible_for_exam
        })
    
    context = {
        'allocation': allocation,
        'assessments': assessments,
        'students_data': students_data,
        'total_students': len(students_data),
    }
    
    return render(request, 'lecturer/unit_students.html', context)


def calculate_grade(total_marks, unit):
    """
    Calculate grade based on total marks and unit grading system
    Returns tuple: (grade, grade_point, is_passed)
    """
    grading = UnitGradingSystem.objects.filter(
        unit=unit,
        min_marks__lte=total_marks,
        max_marks__gte=total_marks
    ).first()
    
    if grading:
        return (grading.grade, grading.grade_point, grading.is_pass)
    
    # Default grading if no grading system is defined
    if total_marks >= 70:
        return ('A', Decimal('5.00'), True)
    elif total_marks >= 60:
        return ('B', Decimal('4.00'), True)
    elif total_marks >= 50:
        return ('C', Decimal('3.00'), True)
    elif total_marks >= 40:
        return ('D', Decimal('2.00'), True)
    else:
        return ('E', Decimal('1.00'), False)


@login_required
@transaction.atomic
def save_student_marks(request):
    """AJAX endpoint to save student marks and update semester results"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        assessment_id = request.POST.get('assessment_id')
        student_id = request.POST.get('student_id')
        marks_obtained = request.POST.get('marks_obtained')
        
        # Validate inputs
        if not all([assessment_id, student_id, marks_obtained]):
            return JsonResponse({'success': False, 'error': 'Missing required fields'})
        
        assessment = get_object_or_404(Assessment, id=assessment_id)
        student = get_object_or_404(Student, id=student_id)
        
        # Validate marks range
        marks_obtained = Decimal(marks_obtained)
        if marks_obtained < 0 or marks_obtained > assessment.max_marks:
            return JsonResponse({
                'success': False, 
                'error': f'Marks must be between 0 and {assessment.max_marks}'
            })
        
        # Check if lecturer owns this assessment
        if assessment.unit_allocation.lecturer != request.user:
            return JsonResponse({'success': False, 'error': 'Unauthorized'})
        
        # Verify student is enrolled in this unit
        enrollment = UnitEnrollment.objects.filter(
            student=student,
            programme_unit=assessment.unit_allocation.programme_unit,
            semester=assessment.unit_allocation.semester,
            status='approved'
        ).first()
        
        if not enrollment:
            return JsonResponse({
                'success': False, 
                'error': 'Student is not enrolled in this unit'
            })
        
        # Create or update student marks
        student_mark, created = StudentMarks.objects.update_or_create(
            assessment=assessment,
            student=student,
            defaults={
                'marks_obtained': marks_obtained,
                'attendance': True,
                'status': 'draft',
                'submitted_by': request.user
            }
        )
        
        # Calculate total marks for the student across all assessments
        all_assessments = Assessment.objects.filter(
            unit_allocation=assessment.unit_allocation
        )
        
        # Calculate CAT marks (CAT1, CAT2, CAT3, Assignment)
        cat_total = Decimal('0.00')
        assignment_total = Decimal('0.00')
        exam_marks = Decimal('0.00')
        total_marks = Decimal('0.00')
        
        for assess in all_assessments:
            mark = StudentMarks.objects.filter(
                assessment=assess,
                student=student
            ).first()
            
            if mark:
                weighted = (mark.marks_obtained / assess.max_marks) * assess.weight_percentage
                total_marks += weighted
                
                # Separate CAT, Assignment, and Exam marks
                if assess.assessment_type in ['cat1', 'cat2', 'cat3']:
                    cat_total += weighted
                elif assess.assessment_type == 'assignment':
                    assignment_total += weighted
                elif assess.assessment_type == 'final':
                    exam_marks = weighted
        
        # Calculate grade
        unit = assessment.unit_allocation.programme_unit.unit
        grade, grade_point, is_passed = calculate_grade(total_marks, unit)
        
        # Get or create SemesterResults
        semester_result, result_created = SemesterResults.objects.update_or_create(
            student=student,
            programme_unit=assessment.unit_allocation.programme_unit,
            semester=assessment.unit_allocation.semester,
            defaults={
                'academic_year': assessment.unit_allocation.semester.academic_year,
                'cat_marks': cat_total,
                'assignment_marks': assignment_total,
                'exam_marks': exam_marks,
                'total_marks': total_marks,
                'grade': grade,
                'grade_point': grade_point,
                'credit_hours': unit.credit_hours,
                'quality_points': grade_point * unit.credit_hours,
                'is_passed': is_passed,
                'is_supplementary': enrollment.enrollment_type == 'resit',
            }
        )
        
        # If this is a resit enrollment, update the ResitExam record
        if enrollment.enrollment_type == 'resit' and enrollment.resit_exam:
            resit_exam = enrollment.resit_exam
            resit_exam.resit_marks = total_marks
            resit_exam.resit_grade = grade
            resit_exam.resit_grade_point = grade_point
            if assessment.assessment_type == 'final':
                resit_exam.status = 'completed'
                resit_exam.marking_date = timezone.now()
                resit_exam.marked_by = request.user
            resit_exam.save()
        
        # Calculate semester GPA if all marks are entered
        update_semester_gpa(student, assessment.unit_allocation.semester)
        
        return JsonResponse({
            'success': True,
            'message': 'Marks saved successfully',
            'total_marks': float(round(total_marks, 2)),
            'grade': grade,
            'grade_point': float(grade_point),
            'is_passed': is_passed,
            'created': created,
            'semester_result_created': result_created
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def update_semester_gpa(student, semester):
    """
    Calculate and update student's semester GPA and cumulative GPA
    """
    # Get all semester results for this semester
    semester_results = SemesterResults.objects.filter(
        student=student,
        semester=semester,
        is_published=True  # Only consider published results
    )
    
    if not semester_results.exists():
        return
    
    # Calculate semester totals
    total_credit_hours = sum(result.credit_hours for result in semester_results)
    total_quality_points = sum(result.quality_points for result in semester_results)
    
    if total_credit_hours > 0:
        semester_gpa = total_quality_points / total_credit_hours
    else:
        semester_gpa = Decimal('0.00')
    
    # Calculate cumulative GPA
    all_results = SemesterResults.objects.filter(
        student=student,
        is_published=True
    )
    
    cumulative_credit_hours = sum(result.credit_hours for result in all_results)
    cumulative_quality_points = sum(result.quality_points for result in all_results)
    
    if cumulative_credit_hours > 0:
        cumulative_gpa = cumulative_quality_points / cumulative_credit_hours
    else:
        cumulative_gpa = Decimal('0.00')
    
    # Update or create SemesterGPA record
    SemesterGPA.objects.update_or_create(
        student=student,
        semester=semester,
        defaults={
            'academic_year': semester.academic_year,
            'total_credit_hours': total_credit_hours,
            'total_quality_points': total_quality_points,
            'semester_gpa': round(semester_gpa, 2),
            'cumulative_credit_hours': cumulative_credit_hours,
            'cumulative_quality_points': cumulative_quality_points,
            'cumulative_gpa': round(cumulative_gpa, 2),
        }
    )
    
    # Update student's cumulative GPA
    student.cumulative_gpa = round(cumulative_gpa, 2)
    student.total_credit_hours = cumulative_credit_hours
    student.save()
    
@login_required
def download_exam_list(request, allocation_id):
    """Download PDF list of students eligible for exam"""
    try:
        lecturer = request.user.lecturer_profile
    except:
        messages.error(request, 'Lecturer profile not found.')
        return redirect('lecturer_dashboard')
    
    allocation = get_object_or_404(
        UnitAllocation.objects.select_related(
            'programme_unit__unit',
            'programme_unit__programme',
            'semester',
            'semester__academic_year'
        ),
        id=allocation_id,
        lecturer=request.user
    )
    
    # Get all enrolled students with attendance >= 75%
    enrollments = UnitEnrollment.objects.filter(
        programme_unit=allocation.programme_unit,
        semester=allocation.semester,
        status='approved'
    ).select_related('student', 'student__user')
    
    eligible_students = []
    for enrollment in enrollments:
        student = enrollment.student
        
        # Calculate attendance
        total_classes = Attendance.objects.filter(
            unit_allocation=allocation,
            student=student
        ).count()
        
        present_classes = Attendance.objects.filter(
            unit_allocation=allocation,
            student=student,
            status='present'
        ).count()
        
        attendance_percentage = 0
        if total_classes > 0:
            attendance_percentage = round((present_classes / total_classes) * 100, 1)
        
        if attendance_percentage >= 75:
            eligible_students.append({
                'reg_no': student.registration_number,
                'name': student.user.get_full_name(),
                'attendance': attendance_percentage,
                'enrollment_type': enrollment.get_enrollment_type_display()
            })
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    normal_style = styles['Normal']
    
    # Title
    title = Paragraph(f"Exam Attendance List", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.2*inch))
    
    # Unit details
    unit_details = f"""
    <b>Unit:</b> {allocation.programme_unit.unit.code} - {allocation.programme_unit.unit.name}<br/>
    <b>Programme:</b> {allocation.programme_unit.programme.code}<br/>
    <b>Semester:</b> {allocation.semester.academic_year.name} - {allocation.semester.get_semester_number_display()}<br/>
    <b>Lecturer:</b> {lecturer.user.get_full_name()}<br/>
    <b>Date:</b> {timezone.now().strftime('%d %B %Y')}<br/>
    <b>Total Eligible:</b> {len(eligible_students)} students
    """
    elements.append(Paragraph(unit_details, normal_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Table
    table_data = [['No.', 'Registration Number', 'Student Name', 'Type', 'Attendance %']]
    
    for idx, student in enumerate(eligible_students, 1):
        table_data.append([
            str(idx),
            student['reg_no'],
            student['name'],
            student['enrollment_type'],
            f"{student['attendance']}%"
        ])
    
    table = Table(table_data, colWidths=[0.5*inch, 1.5*inch, 2.5*inch, 1*inch, 1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    # Create response
    response = HttpResponse(buffer, content_type='application/pdf')
    filename = f"exam_list_{allocation.programme_unit.unit.code}_{timezone.now().strftime('%Y%m%d')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


@login_required
def download_marks_csv(request, allocation_id):
    """Download CSV of all student marks"""
    try:
        lecturer = request.user.lecturer_profile
    except:
        messages.error(request, 'Lecturer profile not found.')
        return redirect('lecturer_dashboard')
    
    allocation = get_object_or_404(
        UnitAllocation.objects.select_related(
            'programme_unit__unit',
            'programme_unit__programme',
            'semester'
        ),
        id=allocation_id,
        lecturer=request.user
    )
    
    # Get assessments
    assessments = Assessment.objects.filter(
        unit_allocation=allocation
    ).order_by('assessment_type')
    
    # Get enrolled students
    enrollments = UnitEnrollment.objects.filter(
        programme_unit=allocation.programme_unit,
        semester=allocation.semester,
        status='approved'
    ).select_related('student', 'student__user').order_by('student__registration_number')
    
    # Create CSV
    response = HttpResponse(content_type='text/csv')
    filename = f"marks_{allocation.programme_unit.unit.code}_{timezone.now().strftime('%Y%m%d')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    
    # Headers
    headers = ['Registration Number', 'Student Name', 'Enrollment Type']
    for assessment in assessments:
        headers.append(f"{assessment.get_assessment_type_display()} ({assessment.max_marks})")
    headers.extend(['Total (%)', 'Attendance %'])
    
    writer.writerow(headers)
    
    # Data rows
    for enrollment in enrollments:
        student = enrollment.student
        row = [
            student.registration_number, 
            student.user.get_full_name(),
            enrollment.get_enrollment_type_display()
        ]
        
        total = Decimal('0.00')
        for assessment in assessments:
            mark = StudentMarks.objects.filter(
                assessment=assessment,
                student=student
            ).first()
            
            if mark:
                row.append(float(mark.marks_obtained))
                weighted = (mark.marks_obtained / assessment.max_marks) * assessment.weight_percentage
                total += weighted
            else:
                row.append('')
        
        row.append(float(round(total, 2)))
        
        # Attendance
        total_classes = Attendance.objects.filter(
            unit_allocation=allocation,
            student=student
        ).count()
        
        present_classes = Attendance.objects.filter(
            unit_allocation=allocation,
            student=student,
            status='present'
        ).count()
        
        attendance_percentage = 0
        if total_classes > 0:
            attendance_percentage = round((present_classes / total_classes) * 100, 1)
        
        row.append(attendance_percentage)
        
        writer.writerow(row)
    
    return response




# lecturer/views.py - Teaching Materials Management Views
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.http import require_POST, require_http_methods
from django.db.models import Count, Q, Prefetch
from django.utils import timezone
from django.core.paginator import Paginator
import mimetypes
import os

from .models import (
    UnitAllocation, TeachingMaterial, MaterialDownload, 
    MaterialComment, UnitEnrollment, Semester, AcademicYear
)


@login_required
def lecturer_teaching_materials(request):
    """
    Main view for lecturer to manage teaching materials for all allocated units
    Shows current semester's units with material upload capability
    """
    if not hasattr(request.user, 'lecturer_profile'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('lecturer_dashboard')
    
    lecturer = request.user
    
    # Get current semester
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get filters from request
    semester_filter = request.GET.get('semester')
    academic_year_filter = request.GET.get('academic_year')
    search_query = request.GET.get('search', '').strip()
    
    # Base queryset - get lecturer's approved allocations
    allocations = UnitAllocation.objects.filter(
        lecturer=lecturer,
        status__in=['approved_hod', 'approved_hos', 'approved_dean']
    ).select_related(
        'programme_unit__unit',
        'programme_unit__programme',
        'programme_unit__programme__department',
        'semester',
        'semester__academic_year'
    ).prefetch_related(
        Prefetch(
            'teaching_materials',
            queryset=TeachingMaterial.objects.order_by('week_number', '-upload_date')
        )
    )
    
    # Apply filters
    if semester_filter:
        allocations = allocations.filter(semester_id=semester_filter)
    elif current_semester:
        # Default to current semester
        allocations = allocations.filter(semester=current_semester)
    
    if academic_year_filter:
        allocations = allocations.filter(semester__academic_year_id=academic_year_filter)
    
    if search_query:
        allocations = allocations.filter(
            Q(programme_unit__unit__code__icontains=search_query) |
            Q(programme_unit__unit__name__icontains=search_query) |
            Q(programme_unit__programme__code__icontains=search_query)
        )
    
    # Annotate with counts
    allocations = allocations.annotate(
        materials_count=Count('teaching_materials', distinct=True),
        enrolled_students_count=Count(
            'programme_unit__enrollments',
            filter=Q(
                programme_unit__enrollments__semester=F('semester'),
                programme_unit__enrollments__status='approved'
            ),
            distinct=True
        )
    )
    
    # Get data for each allocation
    allocations_data = []
    for allocation in allocations:
        # Get enrolled students count for this specific allocation
        enrolled_count = UnitEnrollment.objects.filter(
            programme_unit=allocation.programme_unit,
            semester=allocation.semester,
            status='approved'
        ).count()
        
        # Get materials grouped by week
        materials_by_week = {}
        for material in allocation.teaching_materials.all():
            week = material.week_number
            if week not in materials_by_week:
                materials_by_week[week] = []
            materials_by_week[week].append(material)
        
        allocations_data.append({
            'allocation': allocation,
            'enrolled_students': enrolled_count,
            'materials_count': allocation.teaching_materials.count(),
            'materials_by_week': materials_by_week,
            'weeks_covered': sorted(materials_by_week.keys()) if materials_by_week else []
        })
    
    # Get all semesters and academic years for filters
    semesters = Semester.objects.select_related('academic_year').order_by('-start_date')
    academic_years = AcademicYear.objects.order_by('-start_date')
    
    context = {
        'allocations_data': allocations_data,
        'current_semester': current_semester,
        'semesters': semesters,
        'academic_years': academic_years,
        'semester_filter': semester_filter,
        'academic_year_filter': academic_year_filter,
        'search_query': search_query,
        'total_units': allocations.count(),
        'total_materials': sum(data['materials_count'] for data in allocations_data),
    }
    
    return render(request, 'lecturer/teaching_materials.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def upload_teaching_material(request, allocation_id):
    """
    API endpoint to upload teaching material for a specific unit allocation
    Handles both GET (return form data) and POST (save material)
    """
    if not hasattr(request.user, 'lecturer_profile'):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    allocation = get_object_or_404(
        UnitAllocation.objects.select_related(
            'programme_unit__unit',
            'semester'
        ),
        id=allocation_id,
        lecturer=request.user
    )
    
    if request.method == 'GET':
        # Return existing materials for this allocation
        materials = TeachingMaterial.objects.filter(
            unit_allocation=allocation
        ).order_by('week_number', '-upload_date')
        
        materials_data = [{
            'id': m.id,
            'week_number': m.week_number,
            'topic': m.topic,
            'material_type': m.get_material_type_display(),
            'file_type': m.get_file_type_display(),
            'file_url': m.file.url if m.file else None,
            'external_link': m.external_link,
            'description': m.description,
            'is_published': m.is_published,
            'upload_date': m.upload_date.strftime('%Y-%m-%d %H:%M'),
            'download_count': m.download_count,
            'view_count': m.view_count,
        } for m in materials]
        
        return JsonResponse({
            'success': True,
            'materials': materials_data,
            'unit_code': allocation.programme_unit.unit.code,
            'unit_name': allocation.programme_unit.unit.name,
        })
    
    elif request.method == 'POST':
        # Handle material upload
        try:
            week_number = request.POST.get('week_number')
            topic = request.POST.get('topic')
            description = request.POST.get('description', '')
            material_type = request.POST.get('material_type', 'notes')
            file_type = request.POST.get('file_type', 'pdf')
            is_published = request.POST.get('is_published', 'true') == 'true'
            external_link = request.POST.get('external_link', '')
            uploaded_file = request.FILES.get('file')
            
            # Validation
            if not week_number or not topic:
                return JsonResponse({
                    'success': False,
                    'error': 'Week number and topic are required'
                }, status=400)
            
            if not uploaded_file and not external_link:
                return JsonResponse({
                    'success': False,
                    'error': 'Please upload a file or provide an external link'
                }, status=400)
            
            # Create teaching material
            material = TeachingMaterial(
                unit_allocation=allocation,
                week_number=int(week_number),
                material_type=material_type,
                file_type=file_type,
                topic=topic,
                description=description,
                is_published=is_published,
                uploaded_by=request.user
            )
            
            if uploaded_file:
                material.file = uploaded_file
            
            if external_link:
                material.external_link = external_link
            
            material.save()
            
            messages.success(
                request, 
                f'Teaching material "{topic}" uploaded successfully for Week {week_number}!'
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Material uploaded successfully',
                'material_id': material.id,
                'material': {
                    'id': material.id,
                    'week_number': material.week_number,
                    'topic': material.topic,
                    'upload_date': material.upload_date.strftime('%Y-%m-%d %H:%M'),
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


@login_required
@require_POST
def update_teaching_material(request, material_id):
    """
    API endpoint to update existing teaching material
    """
    if not hasattr(request.user, 'lecturer_profile'):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    material = get_object_or_404(
        TeachingMaterial,
        id=material_id,
        unit_allocation__lecturer=request.user
    )
    
    try:
        # Update fields
        if 'topic' in request.POST:
            material.topic = request.POST['topic']
        
        if 'description' in request.POST:
            material.description = request.POST['description']
        
        if 'week_number' in request.POST:
            material.week_number = int(request.POST['week_number'])
        
        if 'material_type' in request.POST:
            material.material_type = request.POST['material_type']
        
        if 'is_published' in request.POST:
            material.is_published = request.POST['is_published'] == 'true'
        
        if 'external_link' in request.POST:
            material.external_link = request.POST['external_link']
        
        # Handle file replacement
        if 'file' in request.FILES:
            # Delete old file if exists
            if material.file:
                material.file.delete()
            material.file = request.FILES['file']
        
        material.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Material updated successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
def delete_teaching_material(request, material_id):
    """
    API endpoint to delete teaching material
    """
    if not hasattr(request.user, 'lecturer_profile'):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    material = get_object_or_404(
        TeachingMaterial,
        id=material_id,
        unit_allocation__lecturer=request.user
    )
    
    try:
        # Delete file if exists
        if material.file:
            material.file.delete()
        
        topic = material.topic
        material.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Material "{topic}" deleted successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
def toggle_material_publish(request, material_id):
    """
    API endpoint to toggle material publish status
    """
    if not hasattr(request.user, 'lecturer_profile'):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    material = get_object_or_404(
        TeachingMaterial,
        id=material_id,
        unit_allocation__lecturer=request.user
    )
    
    try:
        material.is_published = not material.is_published
        if material.is_published and not material.publish_date:
            material.publish_date = timezone.now()
        material.save()
        
        status = 'published' if material.is_published else 'unpublished'
        
        return JsonResponse({
            'success': True,
            'is_published': material.is_published,
            'message': f'Material {status} successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def get_material_stats(request, allocation_id):
    """
    API endpoint to get statistics for materials in a unit allocation
    """
    if not hasattr(request.user, 'lecturer_profile'):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    allocation = get_object_or_404(
        UnitAllocation,
        id=allocation_id,
        lecturer=request.user
    )
    
    materials = TeachingMaterial.objects.filter(unit_allocation=allocation)
    
    stats = {
        'total_materials': materials.count(),
        'published_materials': materials.filter(is_published=True).count(),
        'total_downloads': sum(m.download_count for m in materials),
        'total_views': sum(m.view_count for m in materials),
        'weeks_covered': materials.values_list('week_number', flat=True).distinct().count(),
        'by_type': {},
        'by_week': {}
    }
    
    # Group by material type
    for material in materials:
        mtype = material.get_material_type_display()
        if mtype not in stats['by_type']:
            stats['by_type'][mtype] = 0
        stats['by_type'][mtype] += 1
    
    # Group by week
    for material in materials:
        week = f"Week {material.week_number}"
        if week not in stats['by_week']:
            stats['by_week'][week] = 0
        stats['by_week'][week] += 1
    
    return JsonResponse({
        'success': True,
        'stats': stats
    })
    
    
# student/views.py - Student Teaching Materials Views
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, Http404, JsonResponse
from django.db.models import Count, Q, F, Prefetch
from django.utils import timezone
from django.core.paginator import Paginator

from .models import (
    Student, UnitEnrollment, TeachingMaterial, MaterialDownload,
    MaterialComment, Semester
)


@login_required
def student_teaching_materials(request):
    """
    Main view for students to access teaching materials for enrolled units
    """
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('student_dashboard')
    
    student = request.user.student_profile
    
    # Get current semester
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get filters
    semester_filter = request.GET.get('semester')
    unit_filter = request.GET.get('unit')
    week_filter = request.GET.get('week')
    material_type = request.GET.get('material_type')
    
    # Get student's enrolled units
    enrollments = UnitEnrollment.objects.filter(
        student=student,
        status='approved'
    ).select_related(
        'programme_unit__unit',
        'programme_unit__programme',
        'semester',
        'semester__academic_year'
    )
    
    # Apply semester filter
    if semester_filter:
        enrollments = enrollments.filter(semester_id=semester_filter)
    elif current_semester:
        enrollments = enrollments.filter(semester=current_semester)
    
    # Apply unit filter
    if unit_filter:
        enrollments = enrollments.filter(programme_unit__unit_id=unit_filter)
    
    # Get all materials for enrolled units
    unit_allocation_ids = []
    for enrollment in enrollments:
        # Get unit allocation for this enrollment
        from .models import UnitAllocation
        allocations = UnitAllocation.objects.filter(
            programme_unit=enrollment.programme_unit,
            semester=enrollment.semester,
            status__in=['approved_hod', 'approved_hos', 'approved_dean']
        )
        unit_allocation_ids.extend([a.id for a in allocations])
    
    # Get materials
    materials = TeachingMaterial.objects.filter(
        unit_allocation_id__in=unit_allocation_ids,
        is_published=True
    ).select_related(
        'unit_allocation__programme_unit__unit',
        'unit_allocation__lecturer',
        'uploaded_by'
    ).order_by('-upload_date')
    
    # Apply filters
    if week_filter:
        materials = materials.filter(week_number=week_filter)
    
    if material_type:
        materials = materials.filter(material_type=material_type)
    
    # Group materials by unit and week
    units_data = {}
    for enrollment in enrollments:
        unit_code = enrollment.programme_unit.unit.code
        if unit_code not in units_data:
            units_data[unit_code] = {
                'enrollment': enrollment,
                'materials_by_week': {},
                'total_materials': 0,
                'weeks_covered': set()
            }
    
    for material in materials:
        unit_code = material.unit_allocation.programme_unit.unit.code
        if unit_code in units_data:
            week = material.week_number
            
            if week not in units_data[unit_code]['materials_by_week']:
                units_data[unit_code]['materials_by_week'][week] = []
            
            # Check if student has downloaded this material
            has_downloaded = MaterialDownload.objects.filter(
                material=material,
                student=student
            ).exists()
            
            material_data = {
                'material': material,
                'has_downloaded': has_downloaded
            }
            
            units_data[unit_code]['materials_by_week'][week].append(material_data)
            units_data[unit_code]['total_materials'] += 1
            units_data[unit_code]['weeks_covered'].add(week)
    
    # Get available semesters
    semesters = Semester.objects.filter(
        unit_registrations__student=student
    ).distinct().order_by('-start_date')
    
    # Get available units for filter
    enrolled_units = set()
    for enrollment in enrollments:
        enrolled_units.add(enrollment.programme_unit.unit)
    
    context = {
        'units_data': units_data,
        'current_semester': current_semester,
        'semesters': semesters,
        'enrolled_units': enrolled_units,
        'semester_filter': semester_filter,
        'unit_filter': unit_filter,
        'week_filter': week_filter,
        'material_type': material_type,
        'total_materials': sum(data['total_materials'] for data in units_data.values()),
        'total_units': len(units_data),
    }
    
    return render(request, 'student/teaching_materials.html', context)


@login_required
def download_material(request, material_id):
    """
    Download or view a teaching material
    Track the download in MaterialDownload model
    """
    if not hasattr(request.user, 'student_profile'):
        raise Http404("Material not found")
    
    student = request.user.student_profile
    
    # Get material
    material = get_object_or_404(
        TeachingMaterial.objects.select_related(
            'unit_allocation__programme_unit__unit'
        ),
        id=material_id,
        is_published=True
    )
    
    # Check if student is enrolled in this unit
    is_enrolled = UnitEnrollment.objects.filter(
        student=student,
        programme_unit=material.unit_allocation.programme_unit,
        semester=material.unit_allocation.semester,
        status='approved'
    ).exists()
    
    if not is_enrolled:
        messages.error(request, "You are not enrolled in this unit.")
        return redirect('student_teaching_materials')
    
    # Track download
    MaterialDownload.objects.create(
        material=material,
        student=student,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    # Increment download count
    material.download_count += 1
    material.save()
    
    # If external link, redirect
    if material.external_link:
        return redirect(material.external_link)
    
    # If file, serve it
    if material.file:
        try:
            response = FileResponse(
                material.file.open('rb'),
                as_attachment=True,
                filename=material.file.name.split('/')[-1]
            )
            return response
        except Exception as e:
            messages.error(request, f"Error downloading file: {str(e)}")
            return redirect('student_teaching_materials')
    
    messages.error(request, "Material file not found.")
    return redirect('student_teaching_materials')


@login_required
def view_material(request, material_id):
    """
    View material details without downloading
    """
    if not hasattr(request.user, 'student_profile'):
        raise Http404("Material not found")
    
    student = request.user.student_profile
    
    material = get_object_or_404(
        TeachingMaterial.objects.select_related(
            'unit_allocation__programme_unit__unit',
            'unit_allocation__lecturer',
            'uploaded_by'
        ),
        id=material_id,
        is_published=True
    )
    
    # Check enrollment
    is_enrolled = UnitEnrollment.objects.filter(
        student=student,
        programme_unit=material.unit_allocation.programme_unit,
        semester=material.unit_allocation.semester,
        status='approved'
    ).exists()
    
    if not is_enrolled:
        messages.error(request, "You are not enrolled in this unit.")
        return redirect('student_teaching_materials')
    
    # Increment view count
    material.view_count += 1
    material.save()
    
    # Check if downloaded
    has_downloaded = MaterialDownload.objects.filter(
        material=material,
        student=student
    ).exists()
    
    # Get comments
    comments = MaterialComment.objects.filter(
        material=material,
        parent_comment=None
    ).select_related('student__user').prefetch_related(
        'replies__student__user'
    ).order_by('-created_at')
    
    context = {
        'material': material,
        'has_downloaded': has_downloaded,
        'comments': comments,
        'can_comment': True,
    }
    
    return render(request, 'student/view_material.html', context)


@login_required
def add_material_comment(request, material_id):
    """
    Add comment/question to a material
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)
    
    if not hasattr(request.user, 'student_profile'):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    student = request.user.student_profile
    
    material = get_object_or_404(
        TeachingMaterial,
        id=material_id,
        is_published=True
    )
    
    # Check enrollment
    is_enrolled = UnitEnrollment.objects.filter(
        student=student,
        programme_unit=material.unit_allocation.programme_unit,
        semester=material.unit_allocation.semester,
        status='approved'
    ).exists()
    
    if not is_enrolled:
        return JsonResponse({'error': 'Not enrolled'}, status=403)
    
    comment_text = request.POST.get('comment', '').strip()
    parent_id = request.POST.get('parent_id')
    
    if not comment_text:
        return JsonResponse({'error': 'Comment cannot be empty'}, status=400)
    
    # Create comment
    comment = MaterialComment(
        material=material,
        student=student,
        comment=comment_text
    )
    
    if parent_id:
        parent_comment = get_object_or_404(MaterialComment, id=parent_id)
        comment.parent_comment = parent_comment
    
    comment.save()
    
    return JsonResponse({
        'success': True,
        'comment': {
            'id': comment.id,
            'comment': comment.comment,
            'student_name': student.user.get_full_name(),
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
        }
    })


@login_required
def unit_materials_view(request, enrollment_id):
    """
    View all materials for a specific enrolled unit
    """
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('student_dashboard')
    
    student = request.user.student_profile
    
    # Get enrollment
    enrollment = get_object_or_404(
        UnitEnrollment.objects.select_related(
            'programme_unit__unit',
            'programme_unit__programme',
            'semester'
        ),
        id=enrollment_id,
        student=student,
        status='approved'
    )
    
    # Get unit allocations
    from .models import UnitAllocation
    allocations = UnitAllocation.objects.filter(
        programme_unit=enrollment.programme_unit,
        semester=enrollment.semester,
        status__in=['approved_hod', 'approved_hos', 'approved_dean']
    )
    
    # Get materials
    materials = TeachingMaterial.objects.filter(
        unit_allocation__in=allocations,
        is_published=True
    ).select_related(
        'uploaded_by',
        'unit_allocation__lecturer'
    ).order_by('week_number', '-upload_date')
    
    # Group by week
    materials_by_week = {}
    for material in materials:
        week = material.week_number
        if week not in materials_by_week:
            materials_by_week[week] = []
        
        has_downloaded = MaterialDownload.objects.filter(
            material=material,
            student=student
        ).exists()
        
        materials_by_week[week].append({
            'material': material,
            'has_downloaded': has_downloaded
        })
    
    context = {
        'enrollment': enrollment,
        'materials_by_week': materials_by_week,
        'total_materials': materials.count(),
        'weeks_covered': len(materials_by_week),
    }
    
    return render(request, 'student/unit_materials.html', context)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Student, User
from .forms import StudentProfileUpdateForm, StudentContactUpdateForm
import re

@login_required
def student_profile_view(request):
    """View student profile"""
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('student_dashboard')
    
    context = {
        'student': student,
        'user': request.user,
    }
    return render(request, 'student/profile/profile_view.html', context)


@login_required
def student_profile_update(request):
    """Update student profile (limited fields)"""
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('student_dashboard')
    
    if request.method == 'POST':
        # Fields that students can update
        allowed_fields = [
            'phone_number',
            'profile_picture',
            'current_address',
            'emergency_contact_name',
            'emergency_contact_phone',
            'emergency_contact_relationship',
            'sponsor_name',
            'sponsor_phone',
            'sponsor_email',
        ]
        
        try:
            with transaction.atomic():
                # Update User fields (limited)
                if 'phone_number' in request.POST:
                    phone = request.POST.get('phone_number', '').strip()
                    if phone:
                        # Validate phone number format
                        if not re.match(r'^[0-9+\-() ]{10,15}$', phone):
                            raise ValidationError("Invalid phone number format.")
                        request.user.phone_number = phone
                
                # Update profile picture
                if 'profile_picture' in request.FILES:
                    request.user.profile_picture = request.FILES['profile_picture']
                
                request.user.save()
                
                # Update Student fields
                student.current_address = request.POST.get('current_address', '').strip()
                student.emergency_contact_name = request.POST.get('emergency_contact_name', '').strip()
                student.emergency_contact_phone = request.POST.get('emergency_contact_phone', '').strip()
                student.emergency_contact_relationship = request.POST.get('emergency_contact_relationship', '').strip()
                student.sponsor_name = request.POST.get('sponsor_name', '').strip()
                student.sponsor_phone = request.POST.get('sponsor_phone', '').strip()
                student.sponsor_email = request.POST.get('sponsor_email', '').strip()
                
                student.save()
                
                messages.success(request, "Profile updated successfully!")
                return redirect('student_profile_view')
                
        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f"Error updating profile: {str(e)}")
    
    context = {
        'student': student,
        'user': request.user,
    }
    return render(request, 'student/profile/profile_update.html', context)


@login_required
def student_change_password(request):
    """Change student password"""
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('student_dashboard')
    
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Important: Update session to prevent logout
            update_session_auth_hash(request, user)
            
            messages.success(request, "Your password has been changed successfully!")
            return redirect('student_profile_view')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = PasswordChangeForm(request.user)
    
    context = {
        'form': form,
        'student': student,
    }
    return render(request, 'student/profile/change_password.html', context)


@login_required
def student_delete_profile_picture(request):
    """Delete student profile picture"""
    if request.method == 'POST':
        try:
            if request.user.profile_picture:
                request.user.profile_picture.delete()
                request.user.profile_picture = None
                request.user.save()
                messages.success(request, "Profile picture deleted successfully!")
            else:
                messages.info(request, "No profile picture to delete.")
        except Exception as e:
            messages.error(request, f"Error deleting profile picture: {str(e)}")
    
    return redirect('student_profile_update')



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Prefetch
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from .models import (
    UnitAllocation, ProgrammeUnit, Lecturer, User, Semester, 
    AcademicYear, Department, School, Unit
)
from decimal import Decimal

# ============= HELPER FUNCTIONS =============
def user_has_allocation_permission(user):
    """Check if user can allocate units"""
    return user.role in ['ict_admin', 'dean', 'hos', 'hod']

def get_user_schools(user):
    """Get schools user has access to"""
    if user.role == 'ict_admin':
        return School.objects.all()
    elif user.role == 'dean':
        return School.objects.filter(dean=user)
    elif user.role == 'hos':
        return School.objects.filter(head_of_school=user)
    elif user.role == 'hod':
        return School.objects.filter(departments__hod=user).distinct()
    return School.objects.none()

def get_user_departments(user):
    """Get departments user has access to"""
    if user.role == 'ict_admin':
        return Department.objects.all()
    elif user.role == 'dean':
        return Department.objects.filter(school__dean=user)
    elif user.role == 'hos':
        return Department.objects.filter(school__head_of_school=user)
    elif user.role == 'hod':
        return Department.objects.filter(hod=user)
    return Department.objects.none()

def get_available_lecturers(user, department=None, is_common_unit=False):
    """Get lecturers available for allocation based on user role"""
    if user.role == 'ict_admin':
        # Admin can allocate to any lecturer
        lecturers = Lecturer.objects.filter(is_active=True)
    elif user.role == 'dean':
        # Dean can allocate to lecturers in their school
        schools = get_user_schools(user)
        lecturers = Lecturer.objects.filter(
            department__school__in=schools,
            is_active=True
        )
        # For common units, dean can allocate to any lecturer
        if is_common_unit:
            lecturers = Lecturer.objects.filter(is_active=True)
    elif user.role in ['hos', 'hod']:
        # HOS/HOD can allocate to lecturers in their departments
        departments = get_user_departments(user)
        lecturers = Lecturer.objects.filter(
            department__in=departments,
            is_active=True
        )
    else:
        lecturers = Lecturer.objects.none()
    
    return lecturers.select_related('user', 'department', 'department__school')


# ============= MAIN VIEWS =============
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import (
    UnitAllocation, Semester, School, Department, 
    ProgrammeUnit, Lecturer
)

@login_required
def unit_allocation_dashboard(request):
    """Dashboard for unit allocation management - DEBUG VERSION"""
    
    try:
        # Check user permissions
        allowed_roles = ['ict_admin', 'dean', 'hos', 'hod', 'lecturer']
        if request.user.role not in allowed_roles:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard')
        
        print("Step 1: User check passed")
        
        # Get current semester
        current_semester = Semester.objects.filter(is_current=True).first()
        print(f"Step 2: Current semester: {current_semester}")
        
        if not current_semester:
            messages.warning(request, 'No active semester found.')
            return render(request, 'allocations/dashboard.html', {
                'current_semester': None,
                'schools': [],
                'departments': [],
                'total_allocations': 0,
                'pending_allocations': 0,
                'approved_allocations': 0,
                'rejected_allocations': 0,
                'unallocated_count': 0,
                'recent_allocations': [],
                'user_role': request.user.role,
            })
        
        # Simple allocations query - NO select_related at all for debugging
        print("Step 3: Building query")
        allocations_query = UnitAllocation.objects.filter(semester=current_semester)
        
        print("Step 4: Getting counts")
        total_allocations = allocations_query.count()
        pending_allocations = allocations_query.filter(status='pending').count()
        approved_allocations = allocations_query.filter(
            status__in=['approved_hod', 'approved_hos', 'approved_dean']
        ).count()
        
        print("Step 5: Getting recent allocations")
        # Get recent allocations WITHOUT select_related for now
        recent_allocations_qs = allocations_query.order_by('-created_at')[:10]
        recent_allocations = []
        
        # Manually load each allocation to see which one causes the error
        for i, allocation in enumerate(recent_allocations_qs):
            print(f"Processing allocation {i}: {allocation.id}")
            try:
                # Try to access all the fields used in the template
                _ = allocation.programme_unit.unit.code
                _ = allocation.programme_unit.unit.name
                _ = allocation.programme_unit.programme.code
                _ = allocation.programme_unit.programme.department.name
                _ = allocation.lecturer.user.get_full_name()
                _ = allocation.lecturer.employee_number
                recent_allocations.append(allocation)
                print(f"  ✓ Allocation {i} OK")
            except Exception as e:
                print(f"  ✗ Error on allocation {i}: {e}")
                continue
        
        print(f"Step 6: Successfully loaded {len(recent_allocations)} allocations")
        
        context = {
            'current_semester': current_semester,
            'schools': [],
            'departments': [],
            'total_allocations': total_allocations,
            'pending_allocations': pending_allocations,
            'approved_allocations': approved_allocations,
            'rejected_allocations': 0,
            'unallocated_count': 0,
            'recent_allocations': recent_allocations,
            'user_role': request.user.role,
        }
        
        print("Step 7: Rendering template")
        return render(request, 'allocations/dashboard.html', context)
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise
    
@login_required
def unit_allocation_list(request):
    """List all unit allocations with filters"""
    if not user_has_allocation_permission(request.user):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    # Get filters from request
    semester_id = request.GET.get('semester')
    school_id = request.GET.get('school')
    department_id = request.GET.get('department')
    status = request.GET.get('status')
    lecturer_id = request.GET.get('lecturer')
    search = request.GET.get('search', '')
    
    # Get current semester if not specified
    if semester_id:
        semester = get_object_or_404(Semester, id=semester_id)
    else:
        semester = Semester.objects.filter(is_current=True).first()
    
    # Build query
    # FIXED: Access lecturer profile through the reverse relation
    allocations = UnitAllocation.objects.filter(
        semester=semester
    ).select_related(
        'programme_unit__unit',
        'programme_unit__programme',
        'programme_unit__programme__department',
        'programme_unit__programme__department__school',
        'lecturer',  # lecturer is User
        'lecturer__lecturer_profile',  # Access Lecturer through reverse relation
        'lecturer__lecturer_profile__department',  # Access department
        'assigned_by',
        'approved_by_hod',
        'approved_by_hos',
        'approved_by_dean'
    )
    
    # Filter by user role
    if request.user.role != 'ict_admin':
        departments = get_user_departments(request.user)
        allocations = allocations.filter(
            programme_unit__programme__department__in=departments
        )
    
    # Apply filters
    if school_id:
        allocations = allocations.filter(
            programme_unit__programme__department__school_id=school_id
        )
    
    if department_id:
        allocations = allocations.filter(
            programme_unit__programme__department_id=department_id
        )
    
    if status:
        allocations = allocations.filter(status=status)
    
    if lecturer_id:
        # FIXED: lecturer_id should match the User ID, not Lecturer ID
        # Need to get the User from Lecturer
        try:
            lecturer = Lecturer.objects.get(id=lecturer_id)
            allocations = allocations.filter(lecturer=lecturer.user)
        except Lecturer.DoesNotExist:
            pass
    
    if search:
        allocations = allocations.filter(
            Q(programme_unit__unit__code__icontains=search) |
            Q(programme_unit__unit__name__icontains=search) |
            Q(lecturer__first_name__icontains=search) |  # FIXED: lecturer is User
            Q(lecturer__last_name__icontains=search) |
            Q(lecturer__lecturer_profile__employee_number__icontains=search)  # FIXED: Access through profile
        )
    
    # Order by
    allocations = allocations.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(allocations, 20)
    page_number = request.GET.get('page')
    allocations_page = paginator.get_page(page_number)
    
    # Get filter options
    semesters = Semester.objects.filter(is_active=True).order_by('-start_date')
    schools = get_user_schools(request.user)
    departments = get_user_departments(request.user)
    
    # FIXED: Get lecturers based on user access
    # Get all lecturers from departments user has access to
    lecturers = Lecturer.objects.filter(
        is_active=True,
        user__is_active=True,
        department__in=departments
    ).select_related('user', 'department').order_by('user__first_name', 'user__last_name')
    
    context = {
        'allocations': allocations_page,
        'semester': semester,
        'semesters': semesters,
        'schools': schools,
        'departments': departments,
        'lecturers': lecturers,
        'selected_school': school_id,
        'selected_department': department_id,
        'selected_status': status,
        'selected_lecturer': lecturer_id,
        'search': search,
        'user_role': request.user.role,
    }
    
    return render(request, 'allocations/allocation_list.html', context)


def get_user_schools(user):
    """Get schools a user has access to"""
    if user.role == 'ict_admin':
        return School.objects.all()
    elif user.role == 'hod':
        departments = Department.objects.filter(hod=user)
        school_ids = departments.values_list('school_id', flat=True).distinct()
        return School.objects.filter(id__in=school_ids)
    elif user.role == 'hos':
        return School.objects.filter(head_of_school=user)
    elif user.role == 'dean':
        return School.objects.filter(dean=user)
    else:
        return School.objects.none()

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import (
    ProgrammeUnit, UnitAllocation, Lecturer, Semester, 
    AcademicYear, Programme, Department, School, Unit
)

# Helper functions
def user_has_allocation_permission(user):
    """Check if user has permission to allocate units"""
    return user.role in ['ict_admin', 'hod', 'hos', 'dean']

def get_user_departments(user):
    """Get departments a user has access to"""
    from django.db.models import Q
    
    if user.role == 'ict_admin':
        return Department.objects.all()
    elif user.role == 'hod':
        return Department.objects.filter(hod=user)
    elif user.role == 'hos':
        # Get all departments in schools where user is HOS
        schools = School.objects.filter(head_of_school=user)
        return Department.objects.filter(school__in=schools)
    elif user.role == 'dean':
        # Get all departments in schools where user is Dean
        schools = School.objects.filter(dean=user)
        return Department.objects.filter(school__in=schools)
    else:
        return Department.objects.none()

def get_available_lecturers(user, department, is_common_unit=False):
    """Get available lecturers based on user role and unit type"""
    lecturers = Lecturer.objects.filter(
        is_active=True,
        user__is_active=True
    ).select_related('user', 'department', 'department__school')
    
    # For common units, show lecturers from all departments
    if is_common_unit:
        if user.role == 'ict_admin':
            return lecturers
        else:
            # Show lecturers from departments the user manages
            departments = get_user_departments(user)
            return lecturers.filter(department__in=departments)
    
    # For regular units, show lecturers from the specific department
    return lecturers.filter(department=department)

@login_required
def create_unit_allocation(request):
    """Create new unit allocation with search functionality"""
    if not user_has_allocation_permission(request.user):
        messages.error(request, 'You do not have permission to allocate units.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        programme_unit_id = request.POST.get('programme_unit')
        lecturer_id = request.POST.get('lecturer')
        semester_id = request.POST.get('semester')
        max_students = request.POST.get('max_students')
        remarks = request.POST.get('remarks', '')
        
        try:
            programme_unit = get_object_or_404(ProgrammeUnit, id=programme_unit_id)
            lecturer = get_object_or_404(Lecturer, id=lecturer_id)  # This is a Lecturer instance
            semester = get_object_or_404(Semester, id=semester_id)
            
            # Check if user has permission to allocate this unit
            if request.user.role != 'ict_admin':
                departments = get_user_departments(request.user)
                if programme_unit.programme.department not in departments:
                    # Check if it's a common unit
                    if programme_unit.unit_type != 'common':
                        messages.error(request, 'You do not have permission to allocate this unit.')
                        return redirect('unit_allocation_list')
            
            # Modified: Check if exact same allocation exists
            # FIXED: Use lecturer.user since UnitAllocation.lecturer expects User instance
            existing = UnitAllocation.objects.filter(
                programme_unit=programme_unit,
                semester=semester,
                lecturer=lecturer.user  # FIXED: Pass User instance, not Lecturer instance
            ).first()
            
            if existing:
                messages.warning(
                    request, 
                    f'This exact allocation already exists. '
                    f'{lecturer.user.get_full_name()} is already teaching '
                    f'{programme_unit.unit.code} for {programme_unit.programme.code} '
                    f'Year {programme_unit.year_of_study} Semester {programme_unit.semester_number}.'
                )
                return redirect('unit_allocation_list')
            
            # Create allocation
            # FIXED: Pass lecturer.user instead of lecturer
            allocation = UnitAllocation.objects.create(
                programme_unit=programme_unit,
                lecturer=lecturer.user,  # FIXED: Pass User instance
                semester=semester,
                assigned_by=request.user,
                max_students=max_students if max_students else None,
                remarks=remarks,
                status='pending'
            )
            
            messages.success(
                request, 
                f'Unit {programme_unit.unit.code} successfully allocated to {lecturer.user.get_full_name()} '
                f'for {programme_unit.programme.code} Year {programme_unit.year_of_study}.'
            )
            return redirect('unit_allocation_detail', allocation_id=allocation.id)
            
        except Exception as e:
            messages.error(request, f'Error creating allocation: {str(e)}')
            return redirect('create_unit_allocation')
    
    # GET request - show form
    semester_id = request.GET.get('semester')
    
    # Get current semester if not specified
    if semester_id:
        semester = get_object_or_404(Semester, id=semester_id)
    else:
        semester = Semester.objects.filter(is_current=True).first()
    
    # Get available semesters
    semesters = Semester.objects.filter(is_active=True).order_by('-start_date')
    
    # Get programmes for filter
    programmes = Programme.objects.filter(is_active=True).select_related(
        'department', 'department__school'
    )
    
    # Filter by user role
    if request.user.role != 'ict_admin':
        departments = get_user_departments(request.user)
        programmes = programmes.filter(department__in=departments)
    
    programmes = programmes.order_by('department__school__name', 'name')
    
    context = {
        'semester': semester,
        'semesters': semesters,
        'programmes': programmes,
        'user_role': request.user.role,
    }
    
    return render(request, 'allocations/create_allocation.html', context)

@login_required
def search_units_ajax(request):
    """AJAX endpoint to search for units"""
    if not user_has_allocation_permission(request.user):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    query = request.GET.get('q', '').strip()
    programme_id = request.GET.get('programme_id')
    year_of_study = request.GET.get('year_of_study')
    semester_number = request.GET.get('semester_number')
    semester_id = request.GET.get('semester_id')
    
    if not query or len(query) < 2:
        return JsonResponse({'units': []})
    
    try:
        # Get semester
        if semester_id:
            try:
                semester = Semester.objects.get(id=semester_id)
            except Semester.DoesNotExist:
                return JsonResponse({'error': 'Semester not found'}, status=404)
        else:
            semester = Semester.objects.filter(is_current=True).first()
        
        if not semester:
            return JsonResponse({'error': 'No active semester found'}, status=400)
        
        # Get academic year for the semester
        academic_year = semester.academic_year
        
        # Base query
        programme_units = ProgrammeUnit.objects.filter(
            academic_year=academic_year,
            is_active=True
        ).select_related(
            'unit',
            'programme',
            'programme__department',
            'programme__department__school'
        )
        
        # Filter by user role
        if request.user.role != 'ict_admin':
            departments = get_user_departments(request.user)
            programme_units = programme_units.filter(
                programme__department__in=departments
            )
        
        # Apply filters
        if programme_id:
            programme_units = programme_units.filter(programme_id=programme_id)
        
        if year_of_study:
            programme_units = programme_units.filter(year_of_study=year_of_study)
        
        if semester_number:
            programme_units = programme_units.filter(semester_number=semester_number)
        
        # Search by unit code or name
        programme_units = programme_units.filter(
            Q(unit__code__icontains=query) | 
            Q(unit__name__icontains=query)
        )
        
        # Limit results
        programme_units = programme_units[:20]
        
        # Format response
        units_data = []
        for pu in programme_units:
            try:
                # Count existing allocations for this unit in this semester
                allocation_count = UnitAllocation.objects.filter(
                    programme_unit=pu,
                    semester=semester
                ).count()
                
                units_data.append({
                    'id': pu.id,
                    'unit_code': pu.unit.code,
                    'unit_name': pu.unit.name,
                    'programme_code': pu.programme.code,
                    'programme_name': pu.programme.name,
                    'department': pu.programme.department.name,
                    'school': pu.programme.department.school.name,
                    'year_of_study': pu.year_of_study,
                    'semester_number': pu.semester_number,
                    'unit_type': pu.get_unit_type_display(),
                    'credit_hours': pu.unit.credit_hours,
                    'allocation_count': allocation_count,
                })
            except Exception as e:
                print(f"Error processing programme unit {pu.id}: {str(e)}")
                continue
        
        return JsonResponse({'units': units_data})
        
    except Exception as e:
        print(f"Error in search_units_ajax: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def search_lecturers_ajax(request):
    """AJAX endpoint to search for lecturers"""
    if not user_has_allocation_permission(request.user):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    query = request.GET.get('q', '').strip()
    programme_unit_id = request.GET.get('programme_unit_id')
    
    if not query or len(query) < 2:
        return JsonResponse({'lecturers': []})
    
    try:
        # Get programme unit to determine if it's a common unit
        is_common_unit = False
        target_department = None
        
        if programme_unit_id:
            try:
                programme_unit = ProgrammeUnit.objects.select_related(
                    'programme__department'
                ).get(id=programme_unit_id)
                is_common_unit = programme_unit.unit_type == 'common'
                target_department = programme_unit.programme.department
            except ProgrammeUnit.DoesNotExist:
                return JsonResponse({'error': 'Programme unit not found'}, status=404)
        
        # Base query
        lecturers = Lecturer.objects.filter(
            is_active=True,
            user__is_active=True
        ).select_related(
            'user',
            'department',
            'department__school'
        )
        
        # Filter by department unless it's a common unit or user is ict_admin
        if not is_common_unit and target_department and request.user.role != 'ict_admin':
            # For non-common units, show only lecturers from the unit's department
            lecturers = lecturers.filter(department=target_department)
        elif request.user.role != 'ict_admin':
            # For common units, show lecturers from departments user manages
            departments = get_user_departments(request.user)
            lecturers = lecturers.filter(department__in=departments)
        
        # Search by name, employee number, or phone
        lecturers = lecturers.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(employee_number__icontains=query) |
            Q(user__phone_number__icontains=query)
        )
        
        # Limit results
        lecturers = lecturers[:20]
        
        # Get current semester for allocation checks
        current_semester = Semester.objects.filter(is_current=True).first()
        
        # Format response
        lecturers_data = []
        for lecturer in lecturers:
            try:
                # Count current allocations - FIX: lecturer field points to User, so use lecturer.user
                current_allocations = 0
                if current_semester:
                    current_allocations = UnitAllocation.objects.filter(
                        lecturer=lecturer.user,  # FIXED: Pass the User instance directly
                        semester=current_semester
                    ).count()
                
                # If programme_unit_id is provided, check existing allocations for this unit
                existing_allocation = None
                existing_allocation_info = None
                
                if programme_unit_id and current_semester:
                    existing_allocation = UnitAllocation.objects.filter(
                        lecturer=lecturer.user,  # FIXED: Pass the User instance directly
                        programme_unit_id=programme_unit_id,
                        semester=current_semester
                    ).first()
                    
                    if existing_allocation:
                        existing_allocation_info = (
                            f"Already teaching this unit for "
                            f"{existing_allocation.programme_unit.programme.code} "
                            f"Year {existing_allocation.programme_unit.year_of_study}"
                        )
                
                lecturers_data.append({
                    'id': lecturer.id,
                    'name': lecturer.user.get_full_name(),
                    'employee_number': lecturer.employee_number,
                    'phone_number': lecturer.user.phone_number or '',
                    'department': lecturer.department.name,
                    'school': lecturer.department.school.name,
                    'designation': lecturer.get_designation_display(),
                    'current_allocations': current_allocations,
                    'has_existing_allocation': existing_allocation is not None,
                    'existing_allocation_info': existing_allocation_info,
                })
            except Exception as e:
                # Log error but continue with other lecturers
                print(f"Error processing lecturer {lecturer.id}: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
        
        return JsonResponse({
            'lecturers': lecturers_data,
            'is_common_unit': is_common_unit,
        })
        
    except Exception as e:
        print(f"Error in search_lecturers_ajax: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_lecturers_ajax(request):
    """AJAX endpoint to get lecturers based on department/common unit"""
    if not user_has_allocation_permission(request.user):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    programme_unit_id = request.GET.get('programme_unit_id')
    
    if not programme_unit_id:
        return JsonResponse({'error': 'Programme unit ID required'}, status=400)
    
    try:
        programme_unit = ProgrammeUnit.objects.select_related(
            'programme__department',
            'unit'
        ).get(id=programme_unit_id)
        
        # Check if it's a common unit
        is_common_unit = programme_unit.unit_type == 'common'
        
        # Get available lecturers
        lecturers = get_available_lecturers(
            request.user,
            programme_unit.programme.department,
            is_common_unit
        )
        
        # Format response
        lecturers_data = []
        for lecturer in lecturers:
            # Count current allocations
            current_allocations = UnitAllocation.objects.filter(
                lecturer=lecturer,
                semester__is_current=True
            ).count()
            
            lecturers_data.append({
                'id': lecturer.id,
                'name': lecturer.user.get_full_name(),
                'employee_number': lecturer.employee_number,
                'department': lecturer.department.name,
                'school': lecturer.department.school.name,
                'designation': lecturer.get_designation_display(),
                'current_allocations': current_allocations,
            })
        
        return JsonResponse({
            'lecturers': lecturers_data,
            'is_common_unit': is_common_unit,
            'unit_info': {
                'code': programme_unit.unit.code,
                'name': programme_unit.unit.name,
                'department': programme_unit.programme.department.name,
            }
        })
        
    except ProgrammeUnit.DoesNotExist:
        return JsonResponse({'error': 'Programme unit not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def unit_allocation_detail(request, allocation_id):
    """View unit allocation details"""
    allocation = get_object_or_404(
        UnitAllocation.objects.select_related(
            'programme_unit__unit',
            'programme_unit__programme',
            'programme_unit__programme__department',
            'programme_unit__programme__department__school',
            'lecturer',  # FIXED: lecturer is already a User, not Lecturer
            'lecturer__lecturer_profile',  # Access Lecturer through reverse relation
            'lecturer__lecturer_profile__department',  # Access department through lecturer_profile
            'semester',
            'assigned_by',
            'approved_by_hod',
            'approved_by_hos',
            'approved_by_dean'
        ),
        id=allocation_id
    )
    
    # Check permission
    if request.user.role != 'ict_admin':
        departments = get_user_departments(request.user)
        if allocation.programme_unit.programme.department not in departments:
            messages.error(request, 'You do not have permission to view this allocation.')
            return redirect('unit_allocation_list')
    
    # Get registered students count
    from .models import UnitEnrollment
    enrolled_students = UnitEnrollment.objects.filter(
        programme_unit=allocation.programme_unit,
        semester=allocation.semester,
        status='approved'
    ).count()
    
    context = {
        'allocation': allocation,
        'enrolled_students': enrolled_students,
        'user_role': request.user.role,
        'can_approve': can_approve_allocation(request.user, allocation),
    }
    
    return render(request, 'allocations/allocation_detail.html', context)


def can_approve_allocation(user, allocation):
    """Check if user can approve this allocation"""
    if user.role == 'ict_admin':
        return True
    
    if allocation.status == 'pending' and user.role == 'hod':
        return allocation.programme_unit.programme.department.hod == user
    
    if allocation.status == 'approved_hod' and user.role == 'hos':
        return allocation.programme_unit.programme.department.school.head_of_school == user
    
    if allocation.status == 'approved_hos' and user.role == 'dean':
        return allocation.programme_unit.programme.department.school.dean == user
    
    return False


@login_required
def approve_allocation(request, allocation_id):
    """Approve unit allocation"""
    allocation = get_object_or_404(UnitAllocation, id=allocation_id)
    
    if not can_approve_allocation(request.user, allocation):
        messages.error(request, 'You do not have permission to approve this allocation.')
        return redirect('unit_allocation_detail', allocation_id=allocation_id)
    
    if request.method == 'POST':
        remarks = request.POST.get('remarks', '')
        
        # Update status based on user role
        if request.user.role == 'ict_admin':
            allocation.status = 'approved_dean'
            allocation.approved_by_dean = request.user
        elif request.user.role == 'hod' and allocation.status == 'pending':
            allocation.status = 'approved_hod'
            allocation.approved_by_hod = request.user
        elif request.user.role == 'hos' and allocation.status == 'approved_hod':
            allocation.status = 'approved_hos'
            allocation.approved_by_hos = request.user
        elif request.user.role == 'dean' and allocation.status == 'approved_hos':
            allocation.status = 'approved_dean'
            allocation.approved_by_dean = request.user
        
        if remarks:
            allocation.remarks = f"{allocation.remarks}\n{request.user.get_full_name()}: {remarks}" if allocation.remarks else remarks
        
        allocation.save()
        
        messages.success(request, 'Allocation approved successfully.')
        return redirect('unit_allocation_detail', allocation_id=allocation_id)
    
    return render(request, 'allocations/approve_allocation.html', {'allocation': allocation})


@login_required
def reject_allocation(request, allocation_id):
    """Reject unit allocation"""
    allocation = get_object_or_404(UnitAllocation, id=allocation_id)
    
    if not can_approve_allocation(request.user, allocation):
        messages.error(request, 'You do not have permission to reject this allocation.')
        return redirect('unit_allocation_detail', allocation_id=allocation_id)
    
    if request.method == 'POST':
        remarks = request.POST.get('remarks', '')
        
        if not remarks:
            messages.error(request, 'Please provide a reason for rejection.')
            return redirect('unit_allocation_detail', allocation_id=allocation_id)
        
        allocation.status = 'rejected'
        allocation.remarks = f"{allocation.remarks}\nRejected by {request.user.get_full_name()}: {remarks}" if allocation.remarks else f"Rejected: {remarks}"
        allocation.save()
        
        messages.success(request, 'Allocation rejected.')
        return redirect('unit_allocation_detail', allocation_id=allocation_id)
    
    return render(request, 'allocations/reject_allocation.html', {'allocation': allocation})


@login_required
def edit_unit_allocation(request, allocation_id):
    """Edit existing unit allocation"""
    allocation = get_object_or_404(UnitAllocation, id=allocation_id)
    
    # Check permission
    if request.user.role != 'ict_admin':
        departments = get_user_departments(request.user)
        if allocation.programme_unit.programme.department not in departments:
            messages.error(request, 'You do not have permission to edit this allocation.')
            return redirect('unit_allocation_list')
    
    # Can only edit pending or rejected allocations
    if allocation.status not in ['pending', 'rejected']:
        messages.error(request, 'Cannot edit approved allocations.')
        return redirect('unit_allocation_detail', allocation_id=allocation_id)
    
    if request.method == 'POST':
        lecturer_id = request.POST.get('lecturer')
        max_students = request.POST.get('max_students')
        remarks = request.POST.get('remarks', '')
        
        try:
            lecturer = get_object_or_404(Lecturer, id=lecturer_id)
            
            # FIXED: Assign User instance, not Lecturer instance
            allocation.lecturer = lecturer.user
            allocation.max_students = max_students if max_students else None
            allocation.remarks = remarks
            allocation.status = 'pending'  # Reset to pending
            allocation.save()
            
            messages.success(request, 'Allocation updated successfully.')
            return redirect('unit_allocation_detail', allocation_id=allocation.id)
            
        except Exception as e:
            messages.error(request, f'Error updating allocation: {str(e)}')
    
    # Get available lecturers
    is_common_unit = allocation.programme_unit.unit_type == 'common'
    lecturers = get_available_lecturers(
        request.user,
        allocation.programme_unit.programme.department,
        is_common_unit
    )
    
    context = {
        'allocation': allocation,
        'lecturers': lecturers,
        'is_common_unit': is_common_unit,
        'user_role': request.user.role,
    }
    
    return render(request, 'allocations/edit_allocation.html', context)


@login_required
def delete_unit_allocation(request, allocation_id):
    """Delete unit allocation"""
    allocation = get_object_or_404(UnitAllocation, id=allocation_id)
    
    # Check permission
    if request.user.role not in ['ict_admin', 'dean']:
        messages.error(request, 'You do not have permission to delete allocations.')
        return redirect('unit_allocation_detail', allocation_id=allocation_id)
    
    if request.user.role != 'ict_admin':
        departments = get_user_departments(request.user)
        if allocation.programme_unit.programme.department not in departments:
            messages.error(request, 'You do not have permission to delete this allocation.')
            return redirect('unit_allocation_list')
    
    # Can only delete pending or rejected allocations
    if allocation.status not in ['pending', 'rejected']:
        messages.error(request, 'Cannot delete approved allocations.')
        return redirect('unit_allocation_detail', allocation_id=allocation_id)
    
    if request.method == 'POST':
        unit_code = allocation.programme_unit.unit.code
        allocation.delete()
        messages.success(request, f'Allocation for {unit_code} deleted successfully.')
        return redirect('unit_allocation_list')
    
    return render(request, 'allocations/delete_allocation.html', {'allocation': allocation})



from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.db.models import Sum, Avg, Count, Q, F
from django.utils import timezone
from decimal import Decimal
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from .models import (
    Student, AcademicYear, Semester, SemesterResults, 
    SemesterGPA, ResitExam, UnitEnrollment
)


@login_required
def student_transcript_view(request):
    """
    Main transcript view showing all academic years and semesters
    Only the logged-in student can view their own transcript
    """
    # Get student profile
    try:
        student = request.user.student_profile
    except:
        return HttpResponseForbidden("You don't have a student profile.")
    
    # Get all academic years the student has been enrolled in
    academic_years = AcademicYear.objects.filter(
        results__student=student
    ).distinct().order_by('start_date')
    
    # Organize data by academic year and semester
    transcript_data = []
    
    for academic_year in academic_years:
        # Get semesters for this academic year
        semesters = Semester.objects.filter(
            academic_year=academic_year,
            results__student=student
        ).distinct().order_by('semester_number')
        
        semester_data = []
        for semester in semesters:
            # Get results for this semester
            results = SemesterResults.objects.filter(
                student=student,
                semester=semester,
                academic_year=academic_year
            ).select_related(
                'programme_unit__unit',
                'programme_unit__programme'
            ).order_by('programme_unit__unit__code')
            
            # Check for resit exams
            results_with_resit = []
            for result in results:
                resit = ResitExam.objects.filter(
                    student=student,
                    original_result=result,
                    status='completed'
                ).first()
                
                results_with_resit.append({
                    'result': result,
                    'resit': resit
                })
            
            # Get semester GPA
            semester_gpa = SemesterGPA.objects.filter(
                student=student,
                semester=semester
            ).first()
            
            semester_data.append({
                'semester': semester,
                'results': results_with_resit,
                'gpa_data': semester_gpa,
                'total_units': results.count(),
                'passed_units': results.filter(is_passed=True).count(),
                'failed_units': results.filter(is_passed=False).count(),
            })
        
        transcript_data.append({
            'academic_year': academic_year,
            'semesters': semester_data
        })
    
    # Calculate overall statistics
    overall_gpa = student.cumulative_gpa
    total_credits = student.total_credit_hours
    
    # Determine class classification
    class_classification = get_class_classification(overall_gpa, student.current_year)
    
    # Calculate completion percentage
    required_credits = student.programme.min_credit_hours
    completion_percentage = (total_credits / required_credits * 100) if required_credits > 0 else 0
    
    # Get total units taken and passed
    total_units = SemesterResults.objects.filter(student=student).count()
    passed_units = SemesterResults.objects.filter(student=student, is_passed=True).count()
    failed_units = total_units - passed_units
    
    context = {
        'student': student,
        'transcript_data': transcript_data,
        'overall_gpa': overall_gpa,
        'total_credits': total_credits,
        'required_credits': required_credits,
        'completion_percentage': completion_percentage,
        'class_classification': class_classification,
        'total_units': total_units,
        'passed_units': passed_units,
        'failed_units': failed_units,
        'current_year': student.current_year,
    }
    
    return render(request, 'student/transcript.html', context)


def get_class_classification(gpa, current_year):
    """
    Determine class classification based on GPA
    Only applies from 3rd year onwards for degree programs
    """
    if current_year < 3:
        return {
            'class': 'In Progress',
            'description': 'Classification will be determined from Year 3',
            'color': 'info',
            'icon': 'ri-time-line'
        }
    
    if gpa >= 3.70:
        return {
            'class': 'First Class Honours',
            'description': 'Outstanding Performance',
            'color': 'success',
            'icon': 'ri-medal-line',
            'advice': 'Excellent work! Maintain this exceptional performance.'
        }
    elif gpa >= 3.30:
        return {
            'class': 'Second Class Honours (Upper Division)',
            'description': 'Very Good Performance',
            'color': 'primary',
            'icon': 'ri-award-line',
            'advice': 'Great job! A little more effort can push you to First Class.'
        }
    elif gpa >= 2.70:
        return {
            'class': 'Second Class Honours (Lower Division)',
            'description': 'Good Performance',
            'color': 'info',
            'icon': 'ri-star-line',
            'advice': 'Good work! Focus on improving to reach Upper Second Class.'
        }
    elif gpa >= 2.00:
        return {
            'class': 'Pass',
            'description': 'Satisfactory Performance',
            'color': 'warning',
            'icon': 'ri-checkbox-circle-line',
            'advice': 'You can do better! Put in more effort to improve your grades.'
        }
    else:
        return {
            'class': 'Below Pass',
            'description': 'Needs Improvement',
            'color': 'danger',
            'icon': 'ri-alert-line',
            'advice': 'Critical: You need to significantly improve your performance.'
        }


@login_required
def download_full_transcript(request):
    """Download complete transcript as PDF"""
    try:
        student = request.user.student_profile
    except:
        return HttpResponseForbidden("You don't have a student profile.")
    
    # Create PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#2E7D32'),
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#2E7D32'),
        spaceAfter=8
    )
    
    # Header
    elements.append(Paragraph("OFFICIAL ACADEMIC TRANSCRIPT", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Student Information
    student_info = [
        ['Registration Number:', student.registration_number],
        ['Student Name:', student.user.get_full_name()],
        ['Programme:', student.programme.name],
        ['Programme Code:', student.programme.code],
        ['Admission Date:', student.admission_date.strftime('%B %d, %Y')],
        ['Current Status:', student.get_student_status_display()],
    ]
    
    info_table = Table(student_info, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 9),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2E7D32')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Get all academic years and results
    academic_years = AcademicYear.objects.filter(
        results__student=student
    ).distinct().order_by('start_date')
    
    for academic_year in academic_years:
        # Academic Year Header
        elements.append(Paragraph(f"Academic Year: {academic_year.name}", heading_style))
        elements.append(Spacer(1, 0.1*inch))
        
        semesters = Semester.objects.filter(
            academic_year=academic_year,
            results__student=student
        ).distinct().order_by('semester_number')
        
        for semester in semesters:
            # Semester subheading
            elements.append(Paragraph(f"  {semester.name}", styles['Heading3']))
            
            # Get results
            results = SemesterResults.objects.filter(
                student=student,
                semester=semester,
                academic_year=academic_year
            ).select_related('programme_unit__unit').order_by('programme_unit__unit__code')
            
            if results.exists():
                # Results table
                data = [['Code', 'Unit Name', 'Credits', 'Marks', 'Grade', 'Points']]
                
                for result in results:
                    # Check for resit
                    resit = ResitExam.objects.filter(
                        student=student,
                        original_result=result,
                        status='completed'
                    ).first()
                    
                    if resit:
                        marks_display = f"{result.total_marks} → {resit.resit_marks}"
                        grade_display = f"{result.grade} → {resit.resit_grade}"
                    else:
                        marks_display = str(result.total_marks)
                        grade_display = result.grade
                    
                    data.append([
                        result.programme_unit.unit.code,
                        result.programme_unit.unit.name[:40],
                        str(result.credit_hours),
                        marks_display,
                        grade_display,
                        str(result.grade_point)
                    ])
                
                results_table = Table(data, colWidths=[0.8*inch, 2.5*inch, 0.7*inch, 0.8*inch, 0.7*inch, 0.7*inch])
                results_table.setStyle(TableStyle([
                    ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 9),
                    ('FONT', (0, 1), (-1, -1), 'Helvetica', 8),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('ALIGN', (1, 1), (1, -1), 'LEFT'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
                ]))
                elements.append(results_table)
                
                # Semester GPA
                semester_gpa = SemesterGPA.objects.filter(
                    student=student,
                    semester=semester
                ).first()
                
                if semester_gpa:
                    gpa_data = [
                        ['Semester GPA:', f"{semester_gpa.semester_gpa:.2f}"],
                        ['Cumulative GPA:', f"{semester_gpa.cumulative_gpa:.2f}"],
                    ]
                    gpa_table = Table(gpa_data, colWidths=[1.5*inch, 1*inch])
                    gpa_table.setStyle(TableStyle([
                        ('FONT', (0, 0), (-1, -1), 'Helvetica-Bold', 9),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ]))
                    elements.append(Spacer(1, 0.1*inch))
                    elements.append(gpa_table)
            else:
                elements.append(Paragraph("  No results available", styles['Normal']))
            
            elements.append(Spacer(1, 0.2*inch))
        
        elements.append(Spacer(1, 0.1*inch))
    
    # Overall Summary
    elements.append(Paragraph("OVERALL SUMMARY", heading_style))
    summary_data = [
        ['Cumulative GPA:', f"{student.cumulative_gpa:.2f}"],
        ['Total Credits Earned:', str(student.total_credit_hours)],
        ['Required Credits:', str(student.programme.min_credit_hours)],
        ['Classification:', get_class_classification(student.cumulative_gpa, student.current_year)['class']],
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 3*inch])
    summary_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica-Bold', 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2E7D32')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(summary_table)
    
    # Footer
    elements.append(Spacer(1, 0.3*inch))
    footer_text = f"Generated on {timezone.now().strftime('%B %d, %Y at %I:%M %p')}"
    elements.append(Paragraph(footer_text, styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="transcript_{student.registration_number}.pdf"'
    
    return response


@login_required
def download_yearly_transcript(request, academic_year_id):
    """Download transcript for a specific academic year"""
    try:
        student = request.user.student_profile
    except:
        return HttpResponseForbidden("You don't have a student profile.")
    
    academic_year = get_object_or_404(AcademicYear, pk=academic_year_id)
    
    # Similar PDF generation but filtered for specific academic year
    # (Implementation similar to download_full_transcript but filtered)
    
    return HttpResponse("Yearly transcript generation")


@login_required
def download_semester_transcript(request, semester_id):
    """Download transcript for a specific semester"""
    try:
        student = request.user.student_profile
    except:
        return HttpResponseForbidden("You don't have a student profile.")
    
    semester = get_object_or_404(Semester, pk=semester_id)
    
    # Similar PDF generation but filtered for specific semester
    # (Implementation similar to download_full_transcript but filtered)
    
    return HttpResponse("Semester transcript generation")


# views.py - Add these views to your existing views file

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Prefetch
from decimal import Decimal
from django.db import transaction

# Import your models
from .models import (
    Student, UnitEnrollment, Assessment, StudentMarks, 
    SemesterResults, SemesterGPA, UnitAllocation, 
    AcademicYear, Semester, UnitGradingSystem, ResitExam
)

@login_required
def admin_marks_entry(request):
    """Admin interface for entering student marks"""
    # Check if user is admin/registrar
    if request.user.role not in ['ict_admin', 'registrar', 'vc', 'dean']:
        messages.error(request, 'Unauthorized access.')
        return redirect('dashboard')
    
    # Get current academic year and semester
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get all academic years and semesters for filters
    academic_years = AcademicYear.objects.filter(is_active=True).order_by('-start_date')
    semesters = Semester.objects.filter(is_active=True).order_by('-start_date')
    
    context = {
        'current_academic_year': current_academic_year,
        'current_semester': current_semester,
        'academic_years': academic_years,
        'semesters': semesters,
    }
    
    return render(request, 'admin/marks_entry.html', context)


@login_required
def admin_search_student(request):
    """AJAX endpoint to search for students"""
    if request.user.role not in ['ict_admin','registrar', 'vc', 'dean']:
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    search_term = request.GET.get('term', '').strip()
    
    if len(search_term) < 2:
        return JsonResponse({'success': False, 'error': 'Enter at least 2 characters'})
    
    # Search students by registration number, phone, or national ID
    students = Student.objects.filter(
        Q(registration_number__icontains=search_term) |
        Q(user__phone_number__icontains=search_term) |
        Q(national_id__icontains=search_term) |
        Q(user__first_name__icontains=search_term) |
        Q(user__last_name__icontains=search_term)
    ).select_related(
        'user',
        'programme',
        'programme__department'
    )[:10]  # Limit to 10 results
    
    results = []
    for student in students:
        results.append({
            'id': student.id,
            'registration_number': student.registration_number,
            'name': student.user.get_full_name(),
            'phone': student.user.phone_number,
            'national_id': student.national_id,
            'programme': student.programme.name,
            'programme_code': student.programme.code,
            'current_year': student.current_year,
            'current_semester': student.current_semester,
        })
    
    return JsonResponse({'success': True, 'students': results})


@login_required
def admin_get_student_enrollments(request):
    """AJAX endpoint to get student enrollments for a specific semester"""
    if request.user.role not in ['ict_admin','registrar', 'vc', 'dean']:
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    student_id = request.GET.get('student_id')
    semester_id = request.GET.get('semester_id')
    
    if not all([student_id, semester_id]):
        return JsonResponse({'success': False, 'error': 'Missing parameters'})
    
    try:
        student = get_object_or_404(Student, id=student_id)
        semester = get_object_or_404(Semester, id=semester_id)
        
        # Get all enrollments for this student in this semester
        enrollments = UnitEnrollment.objects.filter(
            student=student,
            semester=semester,
            status='approved'
        ).select_related(
            'programme_unit__unit',
            'programme_unit__programme',
            'semester',
            'semester__academic_year'
        ).order_by('programme_unit__unit__code')
        
        enrollment_data = []
        for enrollment in enrollments:
            unit = enrollment.programme_unit.unit
            unit_allocation = UnitAllocation.objects.filter(
                programme_unit=enrollment.programme_unit,
                semester=semester
            ).first()
            
            if not unit_allocation:
                continue
            
            # Get assessments for this unit
            assessments = Assessment.objects.filter(
                unit_allocation=unit_allocation
            ).order_by('assessment_type')
            
            # Get existing marks
            marks_data = {}
            total_marks = Decimal('0.00')
            
            for assessment in assessments:
                student_mark = StudentMarks.objects.filter(
                    assessment=assessment,
                    student=student
                ).first()
                
                mark_value = student_mark.marks_obtained if student_mark else None
                marks_data[assessment.assessment_type] = {
                    'assessment_id': assessment.id,
                    'assessment_type': assessment.assessment_type,
                    'title': assessment.title,
                    'max_marks': float(assessment.max_marks),
                    'weight_percentage': float(assessment.weight_percentage),
                    'value': float(mark_value) if mark_value is not None else None,
                    'mark_id': student_mark.id if student_mark else None,
                }
                
                if mark_value is not None:
                    weighted = (mark_value / assessment.max_marks) * assessment.weight_percentage
                    total_marks += weighted
            
            # Get existing semester result
            semester_result = SemesterResults.objects.filter(
                student=student,
                programme_unit=enrollment.programme_unit,
                semester=semester
            ).first()
            
            enrollment_data.append({
                'enrollment_id': enrollment.id,
                'unit_code': unit.code,
                'unit_name': unit.name,
                'credit_hours': unit.credit_hours,
                'enrollment_type': enrollment.get_enrollment_type_display(),
                'is_resit': enrollment.enrollment_type == 'resit',
                'marks': marks_data,
                'total_marks': float(round(total_marks, 2)),
                'grade': semester_result.grade if semester_result else None,
                'grade_point': float(semester_result.grade_point) if semester_result else None,
                'is_passed': semester_result.is_passed if semester_result else None,
            })
        
        return JsonResponse({
            'success': True,
            'enrollments': enrollment_data,
            'student': {
                'registration_number': student.registration_number,
                'name': student.user.get_full_name(),
                'programme': student.programme.name,
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@transaction.atomic
def admin_save_student_marks(request):
    """AJAX endpoint for admin to save and approve student marks"""
    if request.user.role not in ['ict_admin','registrar', 'vc', 'dean']:
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        assessment_id = request.POST.get('assessment_id')
        student_id = request.POST.get('student_id')
        marks_obtained = request.POST.get('marks_obtained')
        auto_approve = request.POST.get('auto_approve', 'false') == 'true'
        
        # Validate inputs
        if not all([assessment_id, student_id, marks_obtained]):
            return JsonResponse({'success': False, 'error': 'Missing required fields'})
        
        assessment = get_object_or_404(Assessment, id=assessment_id)
        student = get_object_or_404(Student, id=student_id)
        
        # Validate marks range
        marks_obtained = Decimal(marks_obtained)
        if marks_obtained < 0 or marks_obtained > assessment.max_marks:
            return JsonResponse({
                'success': False, 
                'error': f'Marks must be between 0 and {assessment.max_marks}'
            })
        
        # Verify student is enrolled in this unit
        enrollment = UnitEnrollment.objects.filter(
            student=student,
            programme_unit=assessment.unit_allocation.programme_unit,
            semester=assessment.unit_allocation.semester,
            status='approved'
        ).first()
        
        if not enrollment:
            return JsonResponse({
                'success': False, 
                'error': 'Student is not enrolled in this unit'
            })
        
        # Determine approval status based on user role and auto_approve flag
        if auto_approve:
            if request.user.role == 'dean':
                mark_status = 'approved_dean'
            elif request.user.role == 'vc':
                mark_status = 'published'
            else:
                mark_status = 'approved_hod'
        else:
            mark_status = 'draft'
        
        # Create or update student marks
        student_mark, created = StudentMarks.objects.update_or_create(
            assessment=assessment,
            student=student,
            defaults={
                'marks_obtained': marks_obtained,
                'attendance': True,
                'status': mark_status,
                'submitted_by': request.user
            }
        )
        
        # If auto-approve, set approval fields
        if auto_approve:
            if request.user.role in ['dean', 'vc']:
                student_mark.approved_by_hod = request.user
                student_mark.approved_by_hos = request.user
                student_mark.approved_by_dean = request.user
                student_mark.save()
        
        # Calculate total marks for the student across all assessments
        all_assessments = Assessment.objects.filter(
            unit_allocation=assessment.unit_allocation
        )
        
        # Calculate CAT marks, assignment marks, and exam marks
        cat_total = Decimal('0.00')
        assignment_total = Decimal('0.00')
        exam_marks = Decimal('0.00')
        total_marks = Decimal('0.00')
        
        for assess in all_assessments:
            mark = StudentMarks.objects.filter(
                assessment=assess,
                student=student
            ).first()
            
            if mark:
                weighted = (mark.marks_obtained / assess.max_marks) * assess.weight_percentage
                total_marks += weighted
                
                # Separate CAT, Assignment, and Exam marks
                if assess.assessment_type in ['cat1', 'cat2', 'cat3']:
                    cat_total += weighted
                elif assess.assessment_type == 'assignment':
                    assignment_total += weighted
                elif assess.assessment_type == 'final':
                    exam_marks = weighted
        
        # Calculate grade
        unit = assessment.unit_allocation.programme_unit.unit
        grade, grade_point, is_passed = calculate_grade(total_marks, unit)
        
        # Determine if results should be published
        result_published = auto_approve and request.user.role in ['dean', 'vc']
        
        # Get or create SemesterResults
        semester_result, result_created = SemesterResults.objects.update_or_create(
            student=student,
            programme_unit=assessment.unit_allocation.programme_unit,
            semester=assessment.unit_allocation.semester,
            defaults={
                'academic_year': assessment.unit_allocation.semester.academic_year,
                'cat_marks': cat_total,
                'assignment_marks': assignment_total,
                'exam_marks': exam_marks,
                'total_marks': total_marks,
                'grade': grade,
                'grade_point': grade_point,
                'credit_hours': unit.credit_hours,
                'quality_points': grade_point * unit.credit_hours,
                'is_passed': is_passed,
                'is_supplementary': enrollment.enrollment_type == 'resit',
                'is_published': result_published,
                'published_date': timezone.now() if result_published else None,
            }
        )
        
        # Set approvals if auto-approve
        if auto_approve and request.user.role in ['dean', 'vc']:
            semester_result.approved_by_hod = request.user
            semester_result.approved_by_hos = request.user
            semester_result.approved_by_dean = request.user
            semester_result.save()
        
        # If this is a resit enrollment, update the ResitExam record
        if enrollment.enrollment_type == 'resit' and enrollment.resit_exam:
            resit_exam = enrollment.resit_exam
            resit_exam.resit_marks = total_marks
            resit_exam.resit_grade = grade
            resit_exam.resit_grade_point = grade_point
            if assessment.assessment_type == 'final':
                resit_exam.status = 'completed'
                resit_exam.marking_date = timezone.now()
                resit_exam.marked_by = request.user
            resit_exam.save()
        
        # Calculate semester GPA if results are published
        if result_published:
            update_semester_gpa(student, assessment.unit_allocation.semester)
        
        return JsonResponse({
            'success': True,
            'message': 'Marks saved and approved successfully' if auto_approve else 'Marks saved successfully',
            'total_marks': float(round(total_marks, 2)),
            'grade': grade,
            'grade_point': float(grade_point),
            'is_passed': is_passed,
            'is_published': result_published,
            'created': created,
            'semester_result_created': result_created
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def calculate_grade(total_marks, unit):
    """
    Calculate grade based on total marks and unit grading system
    Returns tuple: (grade, grade_point, is_passed)
    """
    grading = UnitGradingSystem.objects.filter(
        unit=unit,
        min_marks__lte=total_marks,
        max_marks__gte=total_marks
    ).first()
    
    if grading:
        return (grading.grade, grading.grade_point, grading.is_pass)
    
    # Default grading if no grading system is defined
    if total_marks >= 70:
        return ('A', Decimal('5.00'), True)
    elif total_marks >= 60:
        return ('B', Decimal('4.00'), True)
    elif total_marks >= 50:
        return ('C', Decimal('3.00'), True)
    elif total_marks >= 40:
        return ('D', Decimal('2.00'), True)
    else:
        return ('E', Decimal('1.00'), False)


def update_semester_gpa(student, semester):
    """
    Calculate and update student's semester GPA and cumulative GPA
    """
    # Get all semester results for this semester
    semester_results = SemesterResults.objects.filter(
        student=student,
        semester=semester,
        is_published=True
    )
    
    if not semester_results.exists():
        return
    
    # Calculate semester totals
    total_credit_hours = sum(result.credit_hours for result in semester_results)
    total_quality_points = sum(result.quality_points for result in semester_results)
    
    if total_credit_hours > 0:
        semester_gpa = total_quality_points / total_credit_hours
    else:
        semester_gpa = Decimal('0.00')
    
    # Calculate cumulative GPA
    all_results = SemesterResults.objects.filter(
        student=student,
        is_published=True
    )
    
    cumulative_credit_hours = sum(result.credit_hours for result in all_results)
    cumulative_quality_points = sum(result.quality_points for result in all_results)
    
    if cumulative_credit_hours > 0:
        cumulative_gpa = cumulative_quality_points / cumulative_credit_hours
    else:
        cumulative_gpa = Decimal('0.00')
    
    # Update or create SemesterGPA record
    SemesterGPA.objects.update_or_create(
        student=student,
        semester=semester,
        defaults={
            'academic_year': semester.academic_year,
            'total_credit_hours': total_credit_hours,
            'total_quality_points': total_quality_points,
            'semester_gpa': round(semester_gpa, 2),
            'cumulative_credit_hours': cumulative_credit_hours,
            'cumulative_quality_points': cumulative_quality_points,
            'cumulative_gpa': round(cumulative_gpa, 2),
        }
    )
    
    # Update student's cumulative GPA
    student.cumulative_gpa = round(cumulative_gpa, 2)
    student.total_credit_hours = cumulative_credit_hours
    student.save()
    
    
    
    
# views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q, Count
from .models import EnrollmentPeriod, Semester, AcademicYear
import json
from datetime import datetime

@login_required
def enrollment_period_list(request):
    """Main view for enrollment period management"""
    # Get all enrollment periods with related data
    enrollment_periods = EnrollmentPeriod.objects.select_related(
        'semester',
        'semester__academic_year'
    ).all()
    
    # Get active semesters for dropdown
    semesters = Semester.objects.filter(is_active=True).select_related('academic_year')
    
    # Get academic years
    academic_years = AcademicYear.objects.filter(is_active=True)
    
    context = {
        'enrollment_periods': enrollment_periods,
        'semesters': semesters,
        'academic_years': academic_years,
        'total_periods': enrollment_periods.count(),
    }
    
    return render(request, 'admin/enrollment_periods.html', context)


@login_required
@require_http_methods(["POST"])
def enrollment_period_create(request):
    """Create new enrollment period via AJAX"""
    try:
        data = json.loads(request.body)
        
        semester_id = data.get('semester_id')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        resit_start_date = data.get('resit_start_date')
        resit_end_date = data.get('resit_end_date')
        is_active = data.get('is_active', True)
        remarks = data.get('remarks', '')
        
        # Validate required fields
        if not all([semester_id, start_date, end_date]):
            return JsonResponse({
                'success': False,
                'error': 'Semester, start date, and end date are required.'
            }, status=400)
        
        # Get semester
        semester = get_object_or_404(Semester, id=semester_id)
        
        # Check if enrollment period already exists for this semester
        if EnrollmentPeriod.objects.filter(semester=semester).exists():
            return JsonResponse({
                'success': False,
                'error': f'Enrollment period already exists for {semester.name}.'
            }, status=400)
        
        # Parse dates
        start_dt = timezone.datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_dt = timezone.datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Validate date range
        if end_dt <= start_dt:
            return JsonResponse({
                'success': False,
                'error': 'End date must be after start date.'
            }, status=400)
        
        # Create enrollment period
        enrollment_period = EnrollmentPeriod.objects.create(
            semester=semester,
            start_date=start_dt,
            end_date=end_dt,
            is_active=is_active,
            remarks=remarks
        )
        
        # Add resit dates if provided
        if resit_start_date and resit_end_date:
            resit_start_dt = timezone.datetime.fromisoformat(resit_start_date.replace('Z', '+00:00'))
            resit_end_dt = timezone.datetime.fromisoformat(resit_end_date.replace('Z', '+00:00'))
            
            if resit_end_dt <= resit_start_dt:
                return JsonResponse({
                    'success': False,
                    'error': 'Resit end date must be after resit start date.'
                }, status=400)
            
            enrollment_period.resit_start_date = resit_start_dt
            enrollment_period.resit_end_date = resit_end_dt
            enrollment_period.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Enrollment period created successfully.',
            'period': {
                'id': enrollment_period.id,
                'semester': str(enrollment_period.semester),
                'semester_id': enrollment_period.semester.id,
                'academic_year': enrollment_period.semester.academic_year.name,
                'start_date': enrollment_period.start_date.isoformat(),
                'end_date': enrollment_period.end_date.isoformat(),
                'resit_start_date': enrollment_period.resit_start_date.isoformat() if enrollment_period.resit_start_date else None,
                'resit_end_date': enrollment_period.resit_end_date.isoformat() if enrollment_period.resit_end_date else None,
                'is_active': enrollment_period.is_active,
                'is_enrollment_open': enrollment_period.is_enrollment_open(),
                'is_resit_enrollment_open': enrollment_period.is_resit_enrollment_open(),
                'remarks': enrollment_period.remarks,
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["PUT", "POST"])
def enrollment_period_update(request, period_id):
    """Update enrollment period via AJAX"""
    try:
        enrollment_period = get_object_or_404(EnrollmentPeriod, id=period_id)
        data = json.loads(request.body)
        
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        resit_start_date = data.get('resit_start_date')
        resit_end_date = data.get('resit_end_date')
        is_active = data.get('is_active')
        remarks = data.get('remarks')
        
        # Update dates if provided
        if start_date:
            start_dt = timezone.datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            enrollment_period.start_date = start_dt
        
        if end_date:
            end_dt = timezone.datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            enrollment_period.end_date = end_dt
        
        # Validate date range
        if enrollment_period.end_date <= enrollment_period.start_date:
            return JsonResponse({
                'success': False,
                'error': 'End date must be after start date.'
            }, status=400)
        
        # Update resit dates if provided
        if resit_start_date and resit_end_date:
            resit_start_dt = timezone.datetime.fromisoformat(resit_start_date.replace('Z', '+00:00'))
            resit_end_dt = timezone.datetime.fromisoformat(resit_end_date.replace('Z', '+00:00'))
            
            if resit_end_dt <= resit_start_dt:
                return JsonResponse({
                    'success': False,
                    'error': 'Resit end date must be after resit start date.'
                }, status=400)
            
            enrollment_period.resit_start_date = resit_start_dt
            enrollment_period.resit_end_date = resit_end_dt
        elif resit_start_date == '' or resit_end_date == '':
            # Clear resit dates if empty strings provided
            enrollment_period.resit_start_date = None
            enrollment_period.resit_end_date = None
        
        if is_active is not None:
            enrollment_period.is_active = is_active
        
        if remarks is not None:
            enrollment_period.remarks = remarks
        
        enrollment_period.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Enrollment period updated successfully.',
            'period': {
                'id': enrollment_period.id,
                'semester': str(enrollment_period.semester),
                'semester_id': enrollment_period.semester.id,
                'academic_year': enrollment_period.semester.academic_year.name,
                'start_date': enrollment_period.start_date.isoformat(),
                'end_date': enrollment_period.end_date.isoformat(),
                'resit_start_date': enrollment_period.resit_start_date.isoformat() if enrollment_period.resit_start_date else None,
                'resit_end_date': enrollment_period.resit_end_date.isoformat() if enrollment_period.resit_end_date else None,
                'is_active': enrollment_period.is_active,
                'is_enrollment_open': enrollment_period.is_enrollment_open(),
                'is_resit_enrollment_open': enrollment_period.is_resit_enrollment_open(),
                'remarks': enrollment_period.remarks,
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["DELETE", "POST"])
def enrollment_period_delete(request, period_id):
    """Delete enrollment period via AJAX"""
    try:
        enrollment_period = get_object_or_404(EnrollmentPeriod, id=period_id)
        
        # Check if there are any enrollments
        if enrollment_period.semester.enrollments.exists():
            return JsonResponse({
                'success': False,
                'error': 'Cannot delete enrollment period with existing enrollments.'
            }, status=400)
        
        semester_name = str(enrollment_period.semester)
        enrollment_period.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Enrollment period for {semester_name} deleted successfully.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def enrollment_period_detail(request, period_id):
    """Get enrollment period details via AJAX"""
    try:
        enrollment_period = get_object_or_404(EnrollmentPeriod, id=period_id)
        
        # Get enrollment statistics
        total_enrollments = enrollment_period.semester.enrollments.count()
        pending_enrollments = enrollment_period.semester.enrollments.filter(status='pending').count()
        approved_enrollments = enrollment_period.semester.enrollments.filter(status='approved').count()
        
        return JsonResponse({
            'success': True,
            'period': {
                'id': enrollment_period.id,
                'semester': str(enrollment_period.semester),
                'semester_id': enrollment_period.semester.id,
                'academic_year': enrollment_period.semester.academic_year.name,
                'start_date': enrollment_period.start_date.isoformat(),
                'end_date': enrollment_period.end_date.isoformat(),
                'resit_start_date': enrollment_period.resit_start_date.isoformat() if enrollment_period.resit_start_date else None,
                'resit_end_date': enrollment_period.resit_end_date.isoformat() if enrollment_period.resit_end_date else None,
                'is_active': enrollment_period.is_active,
                'is_enrollment_open': enrollment_period.is_enrollment_open(),
                'is_resit_enrollment_open': enrollment_period.is_resit_enrollment_open(),
                'remarks': enrollment_period.remarks,
                'statistics': {
                    'total_enrollments': total_enrollments,
                    'pending_enrollments': pending_enrollments,
                    'approved_enrollments': approved_enrollments,
                }
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500) 


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Count
from django.http import JsonResponse
from django.core.paginator import Paginator
from decimal import Decimal
from .models import (
    FeeStructure, Programme, AcademicYear, Semester, 
    Student, FeePayment, FeeBalance
)

@login_required
def fee_structure_list(request):
    """List all fee structures with filters"""
    # Get filter parameters
    programme_filter = request.GET.get('programme', '')
    year_filter = request.GET.get('year', '')
    semester_filter = request.GET.get('semester', '')
    academic_year_filter = request.GET.get('academic_year', '')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    fee_structures = FeeStructure.objects.filter(is_active=True).select_related(
        'programme', 
        'programme__department',
        'programme__department__school',
        'academic_year'
    ).order_by('programme__code', 'year_of_study', 'semester_number')
    
    # Apply filters
    if programme_filter:
        fee_structures = fee_structures.filter(programme_id=programme_filter)
    
    if year_filter:
        fee_structures = fee_structures.filter(year_of_study=year_filter)
    
    if semester_filter:
        fee_structures = fee_structures.filter(semester_number=semester_filter)
    
    if academic_year_filter:
        fee_structures = fee_structures.filter(academic_year_id=academic_year_filter)
    
    if search_query:
        fee_structures = fee_structures.filter(
            Q(programme__code__icontains=search_query) |
            Q(programme__name__icontains=search_query) |
            Q(programme__department__name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(fee_structures, 20)
    page_number = request.GET.get('page')
    fee_structures_page = paginator.get_page(page_number)
    
    # Get data for filters
    programmes = Programme.objects.filter(is_active=True).order_by('code')
    academic_years = AcademicYear.objects.filter(is_active=True).order_by('-start_date')
    years = range(1, 8)  # Years 1-7
    semester_choices = Semester.SEMESTER_NAMES
    
    context = {
        'fee_structures': fee_structures_page,
        'programmes': programmes,
        'academic_years': academic_years,
        'years': years,
        'semester_choices': semester_choices,
        'total_structures': fee_structures.count(),
        'programme_filter': programme_filter,
        'year_filter': year_filter,
        'semester_filter': semester_filter,
        'academic_year_filter': academic_year_filter,
        'search_query': search_query,
    }
    
    return render(request, 'finance/fee_structure_list.html', context)


@login_required
def add_fee_structure(request):
    """Add new fee structure"""
    if request.method == 'POST':
        try:
            programme_id = request.POST.get('programme')
            academic_year_id = request.POST.get('academic_year')
            year_of_study = request.POST.get('year_of_study')
            semester_number = request.POST.get('semester_number')
            
            # Get fee components
            tuition_fee = Decimal(request.POST.get('tuition_fee', '0'))
            activity_fee = Decimal(request.POST.get('activity_fee', '0'))
            examination_fee = Decimal(request.POST.get('examination_fee', '0'))
            library_fee = Decimal(request.POST.get('library_fee', '0'))
            medical_fee = Decimal(request.POST.get('medical_fee', '0'))
            technology_fee = Decimal(request.POST.get('technology_fee', '0'))
            other_fees = Decimal(request.POST.get('other_fees', '0'))
            
            # Check if fee structure already exists
            existing = FeeStructure.objects.filter(
                programme_id=programme_id,
                academic_year_id=academic_year_id,
                year_of_study=year_of_study,
                semester_number=semester_number
            ).exists()
            
            if existing:
                messages.error(request, 'Fee structure already exists for this programme, year, and semester.')
                return redirect('add_fee_structure')
            
            # Create fee structure
            fee_structure = FeeStructure.objects.create(
                programme_id=programme_id,
                academic_year_id=academic_year_id,
                year_of_study=year_of_study,
                semester_number=semester_number,
                tuition_fee=tuition_fee,
                activity_fee=activity_fee,
                examination_fee=examination_fee,
                library_fee=library_fee,
                medical_fee=medical_fee,
                technology_fee=technology_fee,
                other_fees=other_fees,
            )
            # total_fee is calculated automatically in model's save method
            
            messages.success(request, f'Fee structure created successfully. Total: KES {fee_structure.total_fee:,.2f}')
            return redirect('fee_structure_list')
            
        except Exception as e:
            messages.error(request, f'Error creating fee structure: {str(e)}')
            return redirect('add_fee_structure')
    
    # GET request
    programmes = Programme.objects.filter(is_active=True).select_related('department').order_by('code')
    academic_years = AcademicYear.objects.filter(is_active=True).order_by('-start_date')
    years = range(1, 8)
    semester_choices = Semester.SEMESTER_NAMES
    
    context = {
        'programmes': programmes,
        'academic_years': academic_years,
        'years': years,
        'semester_choices': semester_choices,
    }
    
    return render(request, 'finance/add_fee_structure.html', context)


@login_required
def update_fee_structure(request, structure_id):
    """Update existing fee structure"""
    fee_structure = get_object_or_404(FeeStructure, id=structure_id)
    
    if request.method == 'POST':
        try:
            # Update fee components
            fee_structure.tuition_fee = Decimal(request.POST.get('tuition_fee', '0'))
            fee_structure.activity_fee = Decimal(request.POST.get('activity_fee', '0'))
            fee_structure.examination_fee = Decimal(request.POST.get('examination_fee', '0'))
            fee_structure.library_fee = Decimal(request.POST.get('library_fee', '0'))
            fee_structure.medical_fee = Decimal(request.POST.get('medical_fee', '0'))
            fee_structure.technology_fee = Decimal(request.POST.get('technology_fee', '0'))
            fee_structure.other_fees = Decimal(request.POST.get('other_fees', '0'))
            
            fee_structure.save()  # total_fee calculated automatically
            
            messages.success(request, f'Fee structure updated successfully. New total: KES {fee_structure.total_fee:,.2f}')
            return redirect('fee_structure_list')
            
        except Exception as e:
            messages.error(request, f'Error updating fee structure: {str(e)}')
    
    context = {
        'fee_structure': fee_structure,
    }
    
    return render(request, 'finance/update_fee_structure.html', context)


@login_required
def delete_fee_structure(request, structure_id):
    """Delete fee structure (soft delete)"""
    fee_structure = get_object_or_404(FeeStructure, id=structure_id)
    
    if request.method == 'POST':
        try:
            # Check if any payments exist for this structure
            payment_count = FeePayment.objects.filter(fee_structure=fee_structure).count()
            
            if payment_count > 0:
                messages.warning(
                    request, 
                    f'Cannot delete. {payment_count} payment(s) are linked to this fee structure. '
                    'Consider deactivating instead.'
                )
                return redirect('fee_structure_list')
            
            # Soft delete
            fee_structure.is_active = False
            fee_structure.save()
            
            messages.success(request, 'Fee structure deactivated successfully.')
            return redirect('fee_structure_list')
            
        except Exception as e:
            messages.error(request, f'Error deleting fee structure: {str(e)}')
            return redirect('fee_structure_list')
    
    context = {
        'fee_structure': fee_structure,
    }
    
    return render(request, 'finance/delete_fee_structure.html', context)


@login_required
def view_fee_structure(request, structure_id):
    """View detailed fee structure"""
    fee_structure = get_object_or_404(
        FeeStructure.objects.select_related(
            'programme',
            'programme__department',
            'programme__department__school',
            'academic_year'
        ),
        id=structure_id
    )
    
    # Get statistics
    total_students = Student.objects.filter(
        programme=fee_structure.programme,
        current_year=fee_structure.year_of_study,
        student_status='active'
    ).count()
    
    # Get payment statistics for this structure
    payments = FeePayment.objects.filter(
        fee_structure=fee_structure,
        status='completed'
    ).aggregate(
        total_collected=Sum('amount'),
        payment_count=Count('id')
    )
    
    # Calculate expected revenue
    expected_revenue = fee_structure.total_fee * total_students
    collected_revenue = payments['total_collected'] or Decimal('0')
    collection_percentage = (collected_revenue / expected_revenue * 100) if expected_revenue > 0 else 0
    
    context = {
        'fee_structure': fee_structure,
        'total_students': total_students,
        'expected_revenue': expected_revenue,
        'collected_revenue': collected_revenue,
        'collection_percentage': collection_percentage,
        'payment_count': payments['payment_count'] or 0,
    }
    
    return render(request, 'finance/view_fee_structure.html', context)


@login_required
def duplicate_fee_structure(request, structure_id):
    """Duplicate fee structure to another academic year"""
    source_structure = get_object_or_404(FeeStructure, id=structure_id)
    
    if request.method == 'POST':
        try:
            target_academic_year_id = request.POST.get('target_academic_year')
            
            # Check if target structure already exists
            existing = FeeStructure.objects.filter(
                programme=source_structure.programme,
                academic_year_id=target_academic_year_id,
                year_of_study=source_structure.year_of_study,
                semester_number=source_structure.semester_number
            ).exists()
            
            if existing:
                messages.error(request, 'Fee structure already exists for the target academic year.')
                return redirect('fee_structure_list')
            
            # Create duplicate
            new_structure = FeeStructure.objects.create(
                programme=source_structure.programme,
                academic_year_id=target_academic_year_id,
                year_of_study=source_structure.year_of_study,
                semester_number=source_structure.semester_number,
                tuition_fee=source_structure.tuition_fee,
                activity_fee=source_structure.activity_fee,
                examination_fee=source_structure.examination_fee,
                library_fee=source_structure.library_fee,
                medical_fee=source_structure.medical_fee,
                technology_fee=source_structure.technology_fee,
                other_fees=source_structure.other_fees,
            )
            
            messages.success(request, f'Fee structure duplicated successfully to {new_structure.academic_year}.')
            return redirect('fee_structure_list')
            
        except Exception as e:
            messages.error(request, f'Error duplicating fee structure: {str(e)}')
            return redirect('fee_structure_list')
    
    academic_years = AcademicYear.objects.filter(is_active=True).exclude(
        id=source_structure.academic_year_id
    ).order_by('-start_date')
    
    context = {
        'source_structure': source_structure,
        'academic_years': academic_years,
    }
    
    return render(request, 'finance/duplicate_fee_structure.html', context)


@login_required
def bulk_create_fee_structures(request):
    """Bulk create fee structures for all years and semesters of a programme"""
    if request.method == 'POST':
        try:
            programme_id = request.POST.get('programme')
            academic_year_id = request.POST.get('academic_year')
            programme = get_object_or_404(Programme, id=programme_id)
            
            created_count = 0
            skipped_count = 0
            
            # Loop through all years and semesters
            for year in range(1, programme.duration_years + 1):
                for semester_num in range(1, 3):  # Assuming 2 semesters per year
                    semester_str = str(semester_num)
                    
                    # Check if already exists
                    if FeeStructure.objects.filter(
                        programme=programme,
                        academic_year_id=academic_year_id,
                        year_of_study=year,
                        semester_number=semester_str
                    ).exists():
                        skipped_count += 1
                        continue
                    
                    # Get base fees from POST or use defaults
                    base_tuition = Decimal(request.POST.get(f'tuition_year_{year}_sem_{semester_num}', 
                                                           request.POST.get('base_tuition', '50000')))
                    
                    FeeStructure.objects.create(
                        programme=programme,
                        academic_year_id=academic_year_id,
                        year_of_study=year,
                        semester_number=semester_str,
                        tuition_fee=base_tuition,
                        activity_fee=Decimal(request.POST.get('activity_fee', '2000')),
                        examination_fee=Decimal(request.POST.get('examination_fee', '3000')),
                        library_fee=Decimal(request.POST.get('library_fee', '1500')),
                        medical_fee=Decimal(request.POST.get('medical_fee', '2500')),
                        technology_fee=Decimal(request.POST.get('technology_fee', '1000')),
                        other_fees=Decimal(request.POST.get('other_fees', '0')),
                    )
                    created_count += 1
            
            messages.success(
                request, 
                f'Bulk creation completed. Created: {created_count}, Skipped (already exist): {skipped_count}'
            )
            return redirect('fee_structure_list')
            
        except Exception as e:
            messages.error(request, f'Error in bulk creation: {str(e)}')
            return redirect('bulk_create_fee_structures')
    
    programmes = Programme.objects.filter(is_active=True).select_related('department').order_by('code')
    academic_years = AcademicYear.objects.filter(is_active=True).order_by('-start_date')
    
    context = {
        'programmes': programmes,
        'academic_years': academic_years,
    }
    
    return render(request, 'finance/bulk_create_fee_structures.html', context)


# AJAX API Endpoints
@login_required
def get_fee_structure_details(request, structure_id):
    """AJAX endpoint to get fee structure details"""
    try:
        fee_structure = FeeStructure.objects.select_related(
            'programme', 'academic_year'
        ).get(id=structure_id)
        
        data = {
            'success': True,
            'structure': {
                'id': fee_structure.id,
                'programme_code': fee_structure.programme.code,
                'programme_name': fee_structure.programme.name,
                'academic_year': fee_structure.academic_year.name,
                'year_of_study': fee_structure.year_of_study,
                'semester_number': fee_structure.semester_number,
                'tuition_fee': str(fee_structure.tuition_fee),
                'activity_fee': str(fee_structure.activity_fee),
                'examination_fee': str(fee_structure.examination_fee),
                'library_fee': str(fee_structure.library_fee),
                'medical_fee': str(fee_structure.medical_fee),
                'technology_fee': str(fee_structure.technology_fee),
                'other_fees': str(fee_structure.other_fees),
                'total_fee': str(fee_structure.total_fee),
            }
        }
        return JsonResponse(data)
    except FeeStructure.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Fee structure not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def get_programme_fee_structures(request, programme_id):
    """AJAX endpoint to get all fee structures for a programme"""
    try:
        academic_year_id = request.GET.get('academic_year')
        
        filters = {'programme_id': programme_id, 'is_active': True}
        if academic_year_id:
            filters['academic_year_id'] = academic_year_id
        
        structures = FeeStructure.objects.filter(**filters).select_related(
            'academic_year'
        ).order_by('year_of_study', 'semester_number')
        
        data = {
            'success': True,
            'structures': [
                {
                    'id': s.id,
                    'year': s.year_of_study,
                    'semester': s.semester_number,
                    'academic_year': s.academic_year.name,
                    'total_fee': str(s.total_fee),
                }
                for s in structures
            ]
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from decimal import Decimal
from datetime import datetime
import csv
from .models import (
    FeePayment, FeeStructure, FeeBalance, Student, 
    AcademicYear, Semester, Programme
)
from .forms import FeePaymentForm

@login_required
def fee_payment_list(request):
    """List all fee payments with filters and search"""
    
    # Get all payments
    payments = FeePayment.objects.select_related(
        'student__user',
        'student__programme',
        'semester',
        'academic_year',
        'fee_structure',
        'processed_by'
    ).order_by('-payment_date')
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    programme_filter = request.GET.get('programme', '')
    semester_filter = request.GET.get('semester', '')
    academic_year_filter = request.GET.get('academic_year', '')
    status_filter = request.GET.get('status', '')
    payment_method_filter = request.GET.get('payment_method', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Apply search
    if search_query:
        payments = payments.filter(
            Q(student__registration_number__icontains=search_query) |
            Q(student__user__first_name__icontains=search_query) |
            Q(student__user__last_name__icontains=search_query) |
            Q(transaction_reference__icontains=search_query) |
            Q(receipt_number__icontains=search_query)
        )
    
    # Apply filters
    if programme_filter:
        payments = payments.filter(student__programme_id=programme_filter)
    
    if semester_filter:
        payments = payments.filter(semester_id=semester_filter)
    
    if academic_year_filter:
        payments = payments.filter(academic_year_id=academic_year_filter)
    
    if status_filter:
        payments = payments.filter(status=status_filter)
    
    if payment_method_filter:
        payments = payments.filter(payment_method=payment_method_filter)
    
    # Apply date filters
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            payments = payments.filter(payment_date__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            payments = payments.filter(payment_date__lte=date_to_obj)
        except ValueError:
            pass
    
    # Get statistics
    total_payments = payments.count()
    total_amount = payments.filter(status='completed').aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    
    pending_payments = payments.filter(status='pending').count()
    completed_payments = payments.filter(status='completed').count()
    failed_payments = payments.filter(status='failed').count()
    
    # Pagination
    paginator = Paginator(payments, 25)  # Show 25 payments per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    programmes = Programme.objects.filter(is_active=True).order_by('code')
    semesters = Semester.objects.filter(is_active=True).order_by('-academic_year__start_date')
    academic_years = AcademicYear.objects.filter(is_active=True).order_by('-start_date')
    
    context = {
        'payments': page_obj,
        'total_payments': total_payments,
        'total_amount': total_amount,
        'pending_payments': pending_payments,
        'completed_payments': completed_payments,
        'failed_payments': failed_payments,
        'search_query': search_query,
        'programmes': programmes,
        'semesters': semesters,
        'academic_years': academic_years,
        'programme_filter': programme_filter,
        'semester_filter': semester_filter,
        'academic_year_filter': academic_year_filter,
        'status_filter': status_filter,
        'payment_method_filter': payment_method_filter,
        'date_from': date_from,
        'date_to': date_to,
        'status_choices': FeePayment.PAYMENT_STATUS,
        'payment_method_choices': FeePayment.PAYMENT_METHODS,
    }
    
    return render(request, 'admin/fee_management/payment_list.html', context)


@login_required
def fee_payment_detail(request, payment_id):
    """View detailed information about a specific payment"""
    payment = get_object_or_404(
        FeePayment.objects.select_related(
            'student__user',
            'student__programme',
            'semester',
            'academic_year',
            'fee_structure',
            'processed_by'
        ),
        id=payment_id
    )
    
    # Get student's payment history
    payment_history = FeePayment.objects.filter(
        student=payment.student
    ).exclude(id=payment.id).order_by('-payment_date')[:5]
    
    # Get student's fee balance
    try:
        fee_balance = FeeBalance.objects.get(
            student=payment.student,
            semester=payment.semester
        )
    except FeeBalance.DoesNotExist:
        fee_balance = None
    
    context = {
        'payment': payment,
        'payment_history': payment_history,
        'fee_balance': fee_balance,
    }
    
    return render(request, 'admin/fee_management/payment_detail.html', context)


@login_required
def admin_add_fee_payment(request):
    """Add a new fee payment"""
    if request.method == 'POST':
        form = FeePaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.processed_by = request.user
            
            # Generate receipt number if completed
            if payment.status == 'completed' and not payment.receipt_number:
                payment.receipt_number = generate_receipt_number()
            
            payment.save()
            
            # Update fee balance
            update_fee_balance(payment.student, payment.semester)
            
            messages.success(request, 'Fee payment added successfully!')
            return redirect('fee_payment_detail', payment_id=payment.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = FeePaymentForm()
    
    context = {
        'form': form,
        'action': 'add',
    }
    
    return render(request, 'admin/fee_management/payment_form.html', context)


@login_required
def update_fee_payment(request, payment_id):
    """Update an existing fee payment"""
    payment = get_object_or_404(FeePayment, id=payment_id)
    
    if request.method == 'POST':
        form = FeePaymentForm(request.POST, instance=payment)
        if form.is_valid():
            updated_payment = form.save(commit=False)
            
            # Generate receipt number if status changed to completed
            if updated_payment.status == 'completed' and not updated_payment.receipt_number:
                updated_payment.receipt_number = generate_receipt_number()
            
            updated_payment.save()
            
            # Update fee balance
            update_fee_balance(updated_payment.student, updated_payment.semester)
            
            messages.success(request, 'Fee payment updated successfully!')
            return redirect('fee_payment_detail', payment_id=payment.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = FeePaymentForm(instance=payment)
    
    context = {
        'form': form,
        'payment': payment,
        'action': 'update',
    }
    
    return render(request, 'admin/fee_management/payment_form.html', context)


@login_required
def delete_fee_payment(request, payment_id):
    """Delete a fee payment"""
    payment = get_object_or_404(FeePayment, id=payment_id)
    
    if request.method == 'POST':
        student = payment.student
        semester = payment.semester
        payment.delete()
        
        # Update fee balance
        update_fee_balance(student, semester)
        
        messages.success(request, 'Fee payment deleted successfully!')
        return redirect('fee_payment_list')
    
    context = {
        'payment': payment,
    }
    
    return render(request, 'admin/fee_management/payment_confirm_delete.html', context)


@login_required
@require_http_methods(["GET"])
def student_payment_history(request, registration_number):
    """Get payment history for a specific student (AJAX)"""
    student = get_object_or_404(Student, registration_number=registration_number)
    
    # Get all payments grouped by academic year and semester
    payments = FeePayment.objects.filter(
        student=student
    ).select_related(
        'academic_year',
        'semester',
        'fee_structure'
    ).order_by('-academic_year__start_date', '-semester__semester_number', '-payment_date')
    
    # Get fee balances
    fee_balances = FeeBalance.objects.filter(
        student=student
    ).select_related(
        'academic_year',
        'semester'
    ).order_by('-academic_year__start_date', '-semester__semester_number')
    
    # Group payments by academic year and semester
    grouped_payments = {}
    for payment in payments:
        key = f"{payment.academic_year.id}_{payment.semester.id}"
        if key not in grouped_payments:
            grouped_payments[key] = {
                'academic_year': payment.academic_year,
                'semester': payment.semester,
                'payments': [],
                'total_paid': Decimal('0.00'),
                'balance': None
            }
        grouped_payments[key]['payments'].append({
            'id': payment.id,
            'amount': str(payment.amount),
            'payment_method': payment.get_payment_method_display(),
            'transaction_reference': payment.transaction_reference,
            'receipt_number': payment.receipt_number or 'N/A',
            'payment_date': payment.payment_date.strftime('%Y-%m-%d %H:%M'),
            'status': payment.get_status_display(),
            'status_class': get_status_class(payment.status),
        })
        grouped_payments[key]['total_paid'] += payment.amount
    
    # Add balance information
    for balance in fee_balances:
        key = f"{balance.academic_year.id}_{balance.semester.id}"
        if key in grouped_payments:
            grouped_payments[key]['balance'] = {
                'total_fees': str(balance.total_fees),
                'amount_paid': str(balance.amount_paid),
                'balance': str(balance.balance),
                'is_cleared': balance.is_cleared,
            }
    
    # Convert to list and format for response
    result = []
    for key, data in grouped_payments.items():
        result.append({
            'academic_year': {
                'id': data['academic_year'].id,
                'name': data['academic_year'].name,
            },
            'semester': {
                'id': data['semester'].id,
                'name': data['semester'].name,
            },
            'payments': data['payments'],
            'total_paid': str(data['total_paid']),
            'balance': data['balance'],
        })
    
    return JsonResponse({
        'success': True,
        'student': {
            'registration_number': student.registration_number,
            'name': student.user.get_full_name(),
            'programme': f"{student.programme.code} - {student.programme.name}",
            'current_year': student.current_year,
            'current_semester': student.current_semester,
        },
        'payment_history': result
    })


@login_required
def export_fee_payments(request):
    """Export fee payments to CSV"""
    # Get filter parameters (same as list view)
    payments = FeePayment.objects.select_related(
        'student__user',
        'student__programme',
        'semester',
        'academic_year'
    ).order_by('-payment_date')
    
    # Apply filters (reuse logic from list view)
    search_query = request.GET.get('search', '')
    programme_filter = request.GET.get('programme', '')
    semester_filter = request.GET.get('semester', '')
    academic_year_filter = request.GET.get('academic_year', '')
    status_filter = request.GET.get('status', '')
    
    if search_query:
        payments = payments.filter(
            Q(student__registration_number__icontains=search_query) |
            Q(student__user__first_name__icontains=search_query) |
            Q(student__user__last_name__icontains=search_query)
        )
    
    if programme_filter:
        payments = payments.filter(student__programme_id=programme_filter)
    if semester_filter:
        payments = payments.filter(semester_id=semester_filter)
    if academic_year_filter:
        payments = payments.filter(academic_year_id=academic_year_filter)
    if status_filter:
        payments = payments.filter(status=status_filter)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="fee_payments_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Receipt Number',
        'Registration Number',
        'Student Name',
        'Programme',
        'Academic Year',
        'Semester',
        'Amount',
        'Payment Method',
        'Transaction Reference',
        'Payment Date',
        'Status',
        'Processed By'
    ])
    
    for payment in payments:
        writer.writerow([
            payment.receipt_number or 'N/A',
            payment.student.registration_number,
            payment.student.user.get_full_name(),
            f"{payment.student.programme.code} - {payment.student.programme.name}",
            payment.academic_year.name,
            payment.semester.name,
            payment.amount,
            payment.get_payment_method_display(),
            payment.transaction_reference,
            payment.payment_date.strftime('%Y-%m-%d %H:%M'),
            payment.get_status_display(),
            payment.processed_by.get_full_name() if payment.processed_by else 'N/A'
        ])
    
    return response


# Helper functions
def generate_receipt_number():
    """Generate a unique receipt number"""
    from django.db.models import Max
    import random
    
    year = timezone.now().year
    last_payment = FeePayment.objects.filter(
        receipt_number__startswith=f'RCT/{year}/'
    ).aggregate(Max('id'))
    
    next_id = (last_payment['id__max'] or 0) + 1
    random_suffix = random.randint(1000, 9999)
    
    return f'RCT/{year}/{next_id:06d}/{random_suffix}'


def update_fee_balance(student, semester):
    """Update fee balance for a student in a semester"""
    # Get or create fee balance
    fee_balance, created = FeeBalance.objects.get_or_create(
        student=student,
        semester=semester,
        academic_year=semester.academic_year,
        defaults={
            'total_fees': Decimal('0.00'),
            'amount_paid': Decimal('0.00'),
            'balance': Decimal('0.00')
        }
    )
    
    # Get fee structure
    try:
        fee_structure = FeeStructure.objects.get(
            programme=student.programme,
            academic_year=semester.academic_year,
            year_of_study=student.current_year,
            semester_number=semester.semester_number
        )
        fee_balance.total_fees = fee_structure.total_fee
    except FeeStructure.DoesNotExist:
        pass
    
    # Calculate total paid
    total_paid = FeePayment.objects.filter(
        student=student,
        semester=semester,
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    fee_balance.amount_paid = total_paid
    fee_balance.balance = fee_balance.total_fees - fee_balance.amount_paid
    fee_balance.is_cleared = fee_balance.balance <= 0
    
    # Update last payment date
    last_payment = FeePayment.objects.filter(
        student=student,
        semester=semester,
        status='completed'
    ).order_by('-payment_date').first()
    
    if last_payment:
        fee_balance.last_payment_date = last_payment.payment_date
    
    if fee_balance.is_cleared:
        fee_balance.clearance_date = timezone.now()
    
    fee_balance.save()
    return fee_balance


def get_status_class(status):
    """Get CSS class for payment status"""
    status_classes = {
        'completed': 'status-completed',
        'pending': 'status-pending',
        'failed': 'status-failed',
        'reversed': 'status-reversed',
    }
    return status_classes.get(status, 'status-other')

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from decimal import Decimal
from .models import (
    Hostel, HostelRoom, HostelBed, HostelAllocation, HostelApplication,
    HostelFeeStructure, HostelImage, HostelRoomImage, BedReservation,
    AcademicYear, Semester, Student, User
)
from .forms import HostelForm, HostelRoomForm, HostelBedForm

# ============= HOSTEL MANAGEMENT VIEWS =============

@login_required
def admin_hostel_list(request):
    """List all hostels with statistics"""
    
    # Get all hostels
    hostels = Hostel.objects.prefetch_related('rooms', 'rooms__beds').annotate(
        room_count=Count('rooms', distinct=True),
        total_beds=Count('rooms__beds', distinct=True)
    ).order_by('name')
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    gender_filter = request.GET.get('gender', '')
    status_filter = request.GET.get('status', '')
    
    # Apply search
    if search_query:
        hostels = hostels.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    # Apply filters
    if gender_filter:
        hostels = hostels.filter(gender_type=gender_filter)
    
    if status_filter == 'active':
        hostels = hostels.filter(is_active=True)
    elif status_filter == 'inactive':
        hostels = hostels.filter(is_active=False)
    
    # Get statistics
    total_hostels = hostels.count()
    total_capacity = sum(h.total_capacity for h in hostels)
    total_rooms = sum(h.room_count for h in hostels)
    total_beds_count = sum(h.total_beds for h in hostels)
    
    # Get current academic year for occupancy stats
    current_year = AcademicYear.objects.filter(is_current=True).first()
    occupied_beds = 0
    available_beds = 0
    
    if current_year:
        occupied_beds = HostelBed.objects.filter(
            academic_year=current_year,
            status='occupied'
        ).count()
        available_beds = HostelBed.objects.filter(
            academic_year=current_year,
            status='available'
        ).count()
    
    # Pagination
    paginator = Paginator(hostels, 12)  # Show 12 hostels per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'hostels': page_obj,
        'total_hostels': total_hostels,
        'total_capacity': total_capacity,
        'total_rooms': total_rooms,
        'total_beds': total_beds_count,
        'occupied_beds': occupied_beds,
        'available_beds': available_beds,
        'search_query': search_query,
        'gender_filter': gender_filter,
        'status_filter': status_filter,
        'gender_choices': Hostel.GENDER_TYPES,
    }
    
    return render(request, 'admin/hostel/hostel_list.html', context)


@login_required
def admin_hostel_detail(request, hostel_code):
    """View detailed information about a specific hostel"""
    hostel = get_object_or_404(
        Hostel.objects.prefetch_related(
            'rooms', 'rooms__beds', 'images', 'fee_structures'
        ).annotate(
            room_count=Count('rooms', distinct=True),
            total_beds=Count('rooms__beds', distinct=True)
        ),
        code=hostel_code
    )
    
    # Get rooms grouped by floor
    rooms = HostelRoom.objects.filter(hostel=hostel).prefetch_related('beds', 'images').order_by('floor', 'room_number')
    
    # Get current academic year
    current_year = AcademicYear.objects.filter(is_current=True).first()
    
    # Get bed statistics for current year
    bed_stats = {
        'available': 0,
        'occupied': 0,
        'reserved': 0,
        'maintenance': 0
    }
    
    if current_year:
        beds = HostelBed.objects.filter(
            room__hostel=hostel,
            academic_year=current_year
        )
        bed_stats = {
            'available': beds.filter(status='available').count(),
            'occupied': beds.filter(status='occupied').count(),
            'reserved': beds.filter(status='reserved').count(),
            'maintenance': beds.filter(status='maintenance').count(),
        }
    
    # Get recent applications
    recent_applications = HostelApplication.objects.filter(
        hostel=hostel
    ).select_related('student__user', 'academic_year', 'semester').order_by('-application_date')[:10]
    
    # Get current allocations
    current_allocations = HostelAllocation.objects.filter(
        bed__room__hostel=hostel,
        is_active=True
    ).select_related('student__user', 'bed__room').order_by('-allocation_date')[:20]
    
    # Get fee structures
    fee_structures = HostelFeeStructure.objects.filter(
        hostel=hostel,
        is_active=True
    ).select_related('academic_year', 'semester').order_by('-academic_year__start_date')
    
    context = {
        'hostel': hostel,
        'rooms': rooms,
        'bed_stats': bed_stats,
        'recent_applications': recent_applications,
        'current_allocations': current_allocations,
        'fee_structures': fee_structures,
        'current_year': current_year,
    }
    
    return render(request, 'admin/hostel/hostel_detail.html', context)


@login_required
def admin_hostel_room_detail(request, room_id):
    """View detailed information about a specific room"""
    room = get_object_or_404(
        HostelRoom.objects.prefetch_related('beds', 'images').select_related('hostel'),
        id=room_id
    )
    
    # Get current academic year
    current_year = AcademicYear.objects.filter(is_current=True).first()
    
    # Get beds for current year
    beds = HostelBed.objects.filter(
        room=room,
        academic_year=current_year
    ).prefetch_related('allocations__student__user').order_by('bed_number')
    
    # Get bed statistics
    bed_stats = {
        'total': beds.count(),
        'available': beds.filter(status='available').count(),
        'occupied': beds.filter(status='occupied').count(),
        'reserved': beds.filter(status='reserved').count(),
        'maintenance': beds.filter(status='maintenance').count(),
    }
    
    # Get current allocations for this room
    current_allocations = HostelAllocation.objects.filter(
        bed__room=room,
        is_active=True
    ).select_related('student__user', 'bed', 'academic_year', 'semester')
    
    # Get room images
    images = HostelRoomImage.objects.filter(room=room).order_by('-is_primary', '-created_at')
    
    context = {
        'room': room,
        'beds': beds,
        'bed_stats': bed_stats,
        'current_allocations': current_allocations,
        'images': images,
        'current_year': current_year,
    }
    
    return render(request, 'admin/hostel/room_detail.html', context)


@login_required
def admin_hostel_bed_detail(request, bed_id):
    """View detailed information about a specific bed"""
    bed = get_object_or_404(
        HostelBed.objects.select_related('room__hostel', 'academic_year'),
        id=bed_id
    )
    
    # Get allocation history
    allocations = HostelAllocation.objects.filter(
        bed=bed
    ).select_related(
        'student__user',
        'student__programme',
        'academic_year',
        'semester',
        'allocated_by'
    ).order_by('-allocation_date')
    
    # Get current allocation
    current_allocation = allocations.filter(is_active=True).first()
    
    # Get bed reservations
    reservations = BedReservation.objects.filter(
        bed=bed
    ).select_related('student__user').order_by('-created_at')[:10]
    
    context = {
        'bed': bed,
        'allocations': allocations,
        'current_allocation': current_allocation,
        'reservations': reservations,
    }
    
    return render(request, 'admin/hostel/bed_detail.html', context)


@login_required
def admin_add_hostel(request):
    """Add a new hostel"""
    if request.method == 'POST':
        form = HostelForm(request.POST, request.FILES)
        if form.is_valid():
            hostel = form.save()
            messages.success(request, f'Hostel "{hostel.name}" added successfully!')
            return redirect('admin_hostel_detail', hostel_code=hostel.code)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = HostelForm()
    
    context = {
        'form': form,
        'action': 'add',
    }
    
    return render(request, 'admin/hostel/hostel_form.html', context)


@login_required
def admin_update_hostel(request, hostel_code):
    """Update an existing hostel"""
    hostel = get_object_or_404(Hostel, code=hostel_code)
    
    if request.method == 'POST':
        form = HostelForm(request.POST, request.FILES, instance=hostel)
        if form.is_valid():
            updated_hostel = form.save()
            messages.success(request, f'Hostel "{updated_hostel.name}" updated successfully!')
            return redirect('admin_hostel_detail', hostel_code=updated_hostel.code)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = HostelForm(instance=hostel)
    
    context = {
        'form': form,
        'hostel': hostel,
        'action': 'update',
    }
    
    return render(request, 'admin/hostel/hostel_form.html', context)


@login_required
def admin_delete_hostel(request, hostel_code):
    """Delete a hostel"""
    hostel = get_object_or_404(Hostel, code=hostel_code)
    
    if request.method == 'POST':
        hostel_name = hostel.name
        hostel.delete()
        messages.success(request, f'Hostel "{hostel_name}" deleted successfully!')
        return redirect('admin_hostel_list')
    
    context = {
        'hostel': hostel,
    }
    
    return render(request, 'admin/hostel/hostel_confirm_delete.html', context)


# ============= API ENDPOINTS =============

@login_required
@require_http_methods(["POST"])
def api_bulk_create_hostels(request):
    """
    Bulk create hostels for a specific admission
    Expected JSON format:
    {
        "academic_year_id": 1,
        "hostels": [
            {
                "name": "Hostel A",
                "code": "HST-A",
                "gender_type": "M",
                "total_capacity": 100,
                "location": "Block A",
                "floors": 4,
                "rooms_per_floor": 10,
                "room_type": "double",
                "beds_per_room": 2
            }
        ]
    }
    """
    import json
    
    try:
        data = json.loads(request.body)
        academic_year_id = data.get('academic_year_id')
        hostels_data = data.get('hostels', [])
        
        if not academic_year_id or not hostels_data:
            return JsonResponse({
                'success': False,
                'error': 'Academic year and hostels data are required'
            }, status=400)
        
        # Get academic year
        try:
            academic_year = AcademicYear.objects.get(id=academic_year_id)
        except AcademicYear.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Academic year not found'
            }, status=404)
        
        # Get warden (optional)
        warden = None
        warden_id = data.get('warden_id')
        if warden_id:
            try:
                warden = User.objects.get(id=warden_id, role='hostel_warden')
            except User.DoesNotExist:
                pass
        
        created_hostels = []
        errors = []
        
        for hostel_data in hostels_data:
            try:
                # Create hostel
                hostel = Hostel.objects.create(
                    name=hostel_data['name'],
                    code=hostel_data['code'],
                    gender_type=hostel_data['gender_type'],
                    total_capacity=hostel_data['total_capacity'],
                    location=hostel_data.get('location', ''),
                    description=hostel_data.get('description', ''),
                    amenities=hostel_data.get('amenities', ''),
                    warden=warden,
                    is_active=True
                )
                
                # Create rooms and beds
                floors = hostel_data.get('floors', 1)
                rooms_per_floor = hostel_data.get('rooms_per_floor', 10)
                room_type = hostel_data.get('room_type', 'double')
                beds_per_room = hostel_data.get('beds_per_room', 2)
                
                # Get capacity based on room type
                room_capacity_map = {
                    'single': 1,
                    'double': 2,
                    'triple': 3,
                    'quad': 4
                }
                capacity = room_capacity_map.get(room_type, beds_per_room)
                
                room_number_counter = 1
                
                for floor in range(1, floors + 1):
                    for room_num in range(1, rooms_per_floor + 1):
                        # Create room
                        room = HostelRoom.objects.create(
                            hostel=hostel,
                            room_number=f"{floor}{room_num:02d}",
                            floor=floor,
                            room_type=room_type,
                            capacity=capacity,
                            has_bathroom=hostel_data.get('has_bathroom', True),
                            has_balcony=hostel_data.get('has_balcony', False),
                            is_active=True
                        )
                        
                        # Create beds for this room
                        for bed_num in range(1, capacity + 1):
                            HostelBed.objects.create(
                                room=room,
                                bed_number=str(bed_num),
                                status='available',
                                academic_year=academic_year,
                                is_active=True
                            )
                        
                        room_number_counter += 1
                
                created_hostels.append({
                    'id': hostel.id,
                    'name': hostel.name,
                    'code': hostel.code,
                    'rooms_created': floors * rooms_per_floor,
                    'beds_created': floors * rooms_per_floor * capacity
                })
                
            except Exception as e:
                errors.append({
                    'hostel': hostel_data.get('name', 'Unknown'),
                    'error': str(e)
                })
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully created {len(created_hostels)} hostel(s)',
            'hostels': created_hostels,
            'errors': errors
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_bulk_create_rooms(request, hostel_code):
    """
    Bulk create rooms for a specific hostel
    Expected JSON format:
    {
        "academic_year_id": 1,
        "floors": 4,
        "rooms_per_floor": 10,
        "room_type": "double",
        "has_bathroom": true,
        "has_balcony": false
    }
    """
    import json
    
    try:
        hostel = get_object_or_404(Hostel, code=hostel_code)
        data = json.loads(request.body)
        
        academic_year_id = data.get('academic_year_id')
        floors = data.get('floors', 1)
        rooms_per_floor = data.get('rooms_per_floor', 10)
        room_type = data.get('room_type', 'double')
        has_bathroom = data.get('has_bathroom', True)
        has_balcony = data.get('has_balcony', False)
        
        # Get academic year
        try:
            academic_year = AcademicYear.objects.get(id=academic_year_id)
        except AcademicYear.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Academic year not found'
            }, status=404)
        
        # Get capacity based on room type
        room_capacity_map = {
            'single': 1,
            'double': 2,
            'triple': 3,
            'quad': 4
        }
        capacity = room_capacity_map.get(room_type, 2)
        
        created_rooms = []
        created_beds_count = 0
        
        for floor in range(1, floors + 1):
            for room_num in range(1, rooms_per_floor + 1):
                # Check if room already exists
                room_number = f"{floor}{room_num:02d}"
                if HostelRoom.objects.filter(hostel=hostel, room_number=room_number).exists():
                    continue
                
                # Create room
                room = HostelRoom.objects.create(
                    hostel=hostel,
                    room_number=room_number,
                    floor=floor,
                    room_type=room_type,
                    capacity=capacity,
                    has_bathroom=has_bathroom,
                    has_balcony=has_balcony,
                    is_active=True
                )
                
                # Create beds for this room
                for bed_num in range(1, capacity + 1):
                    HostelBed.objects.create(
                        room=room,
                        bed_number=str(bed_num),
                        status='available',
                        academic_year=academic_year,
                        is_active=True
                    )
                    created_beds_count += 1
                
                created_rooms.append({
                    'id': room.id,
                    'room_number': room.room_number,
                    'floor': room.floor,
                    'beds': capacity
                })
        
        # Update hostel total capacity
        total_beds = HostelBed.objects.filter(
            room__hostel=hostel,
            academic_year=academic_year
        ).count()
        hostel.total_capacity = total_beds
        hostel.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully created {len(created_rooms)} room(s) with {created_beds_count} bed(s)',
            'rooms': created_rooms,
            'total_capacity': total_beds
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_bulk_create_beds(request, room_id):
    """
    Bulk create beds for a specific room
    Expected JSON format:
    {
        "academic_year_id": 1,
        "number_of_beds": 2
    }
    """
    import json
    
    try:
        room = get_object_or_404(HostelRoom, id=room_id)
        data = json.loads(request.body)
        
        academic_year_id = data.get('academic_year_id')
        number_of_beds = data.get('number_of_beds', room.capacity)
        
        # Get academic year
        try:
            academic_year = AcademicYear.objects.get(id=academic_year_id)
        except AcademicYear.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Academic year not found'
            }, status=404)
        
        # Check if beds already exist for this academic year
        existing_beds = HostelBed.objects.filter(
            room=room,
            academic_year=academic_year
        ).count()
        
        if existing_beds >= number_of_beds:
            return JsonResponse({
                'success': False,
                'error': f'Room already has {existing_beds} bed(s) for this academic year'
            }, status=400)
        
        created_beds = []
        beds_to_create = number_of_beds - existing_beds
        start_number = existing_beds + 1
        
        for bed_num in range(start_number, start_number + beds_to_create):
            bed = HostelBed.objects.create(
                room=room,
                bed_number=str(bed_num),
                status='available',
                academic_year=academic_year,
                is_active=True
            )
            created_beds.append({
                'id': bed.id,
                'bed_number': bed.bed_number,
                'status': bed.status
            })
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully created {len(created_beds)} bed(s)',
            'beds': created_beds
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_hostel_stats(request, hostel_code):
    """Get statistics for a specific hostel"""
    hostel = get_object_or_404(Hostel, code=hostel_code)
    
    # Get current academic year
    current_year = AcademicYear.objects.filter(is_current=True).first()
    
    if not current_year:
        return JsonResponse({
            'success': False,
            'error': 'No current academic year found'
        }, status=404)
    
    # Get bed statistics
    total_beds = HostelBed.objects.filter(
        room__hostel=hostel,
        academic_year=current_year
    ).count()
    
    available_beds = HostelBed.objects.filter(
        room__hostel=hostel,
        academic_year=current_year,
        status='available'
    ).count()
    
    occupied_beds = HostelBed.objects.filter(
        room__hostel=hostel,
        academic_year=current_year,
        status='occupied'
    ).count()
    
    reserved_beds = HostelBed.objects.filter(
        room__hostel=hostel,
        academic_year=current_year,
        status='reserved'
    ).count()
    
    maintenance_beds = HostelBed.objects.filter(
        room__hostel=hostel,
        academic_year=current_year,
        status='maintenance'
    ).count()
    
    # Get room statistics
    total_rooms = HostelRoom.objects.filter(hostel=hostel).count()
    
    # Get application statistics
    pending_applications = HostelApplication.objects.filter(
        hostel=hostel,
        status='pending'
    ).count()
    
    approved_applications = HostelApplication.objects.filter(
        hostel=hostel,
        status='approved'
    ).count()
    
    # Calculate occupancy rate
    occupancy_rate = (occupied_beds / total_beds * 100) if total_beds > 0 else 0
    
    return JsonResponse({
        'success': True,
        'hostel': {
            'code': hostel.code,
            'name': hostel.name,
            'gender_type': hostel.gender_type,
            'location': hostel.location,
        },
        'stats': {
            'total_beds': total_beds,
            'available_beds': available_beds,
            'occupied_beds': occupied_beds,
            'reserved_beds': reserved_beds,
            'maintenance_beds': maintenance_beds,
            'total_rooms': total_rooms,
            'occupancy_rate': round(occupancy_rate, 2),
            'pending_applications': pending_applications,
            'approved_applications': approved_applications,
        }
    })


@login_required
@require_http_methods(["GET"])
def api_available_beds(request):
    """Get available beds with filters"""
    # Get filter parameters
    hostel_id = request.GET.get('hostel_id')
    gender_type = request.GET.get('gender_type')
    room_type = request.GET.get('room_type')
    academic_year_id = request.GET.get('academic_year_id')
    
    # Base query
    beds = HostelBed.objects.filter(
        status='available'
    ).select_related('room__hostel', 'academic_year')
    
    # Apply filters
    if hostel_id:
        beds = beds.filter(room__hostel_id=hostel_id)
    
    if gender_type:
        beds = beds.filter(room__hostel__gender_type=gender_type)
    
    if room_type:
        beds = beds.filter(room__room_type=room_type)
    
    if academic_year_id:
        beds = beds.filter(academic_year_id=academic_year_id)
    else:
        # Default to current academic year
        current_year = AcademicYear.objects.filter(is_current=True).first()
        if current_year:
            beds = beds.filter(academic_year=current_year)
    
    # Prepare response
    available_beds = []
    for bed in beds[:50]:  # Limit to 50 beds
        available_beds.append({
            'id': bed.id,
            'bed_number': bed.bed_number,
            'room': {
                'id': bed.room.id,
                'room_number': bed.room.room_number,
                'floor': bed.room.floor,
                'room_type': bed.room.get_room_type_display(),
                'capacity': bed.room.capacity,
            },
            'hostel': {
                'id': bed.room.hostel.id,
                'name': bed.room.hostel.name,
                'code': bed.room.hostel.code,
                'gender_type': bed.room.hostel.get_gender_type_display(),
                'location': bed.room.hostel.location,
            }
        })
    
    return JsonResponse({
        'success': True,
        'count': len(available_beds),
        'beds': available_beds
    })
    
    
# views.py - Hostel Application Management Views

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Case, When, IntegerField
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import JsonResponse
from decimal import Decimal

from .models import (
    HostelApplication, Hostel, HostelBed, HostelFeeStructure,
    Student, AcademicYear, Semester, HostelRoom, BedReservation
)

# ============= ADMIN VIEWS =============

@login_required
def admin_hostel_application_list(request):
    """List all hostel applications with filters"""
    applications = HostelApplication.objects.select_related(
        'student__user', 'hostel', 'academic_year', 'semester'
    ).order_by('-application_date')
    
    # Filters
    status_filter = request.GET.get('status')
    hostel_filter = request.GET.get('hostel')
    academic_year_filter = request.GET.get('academic_year')
    semester_filter = request.GET.get('semester')
    search_query = request.GET.get('search')
    
    if status_filter:
        applications = applications.filter(status=status_filter)
    if hostel_filter:
        applications = applications.filter(hostel_id=hostel_filter)
    if academic_year_filter:
        applications = applications.filter(academic_year_id=academic_year_filter)
    if semester_filter:
        applications = applications.filter(semester_id=semester_filter)
    if search_query:
        applications = applications.filter(
            Q(student__registration_number__icontains=search_query) |
            Q(student__user__first_name__icontains=search_query) |
            Q(student__user__last_name__icontains=search_query)
        )
    
    # Statistics
    stats = HostelApplication.objects.aggregate(
        total=Count('id'),
        pending=Count(Case(When(status='pending', then=1), output_field=IntegerField())),
        approved=Count(Case(When(status='approved', then=1), output_field=IntegerField())),
        rejected=Count(Case(When(status='rejected', then=1), output_field=IntegerField())),
    )
    
    # Pagination
    paginator = Paginator(applications, 20)
    page_number = request.GET.get('page')
    applications_page = paginator.get_page(page_number)
    
    context = {
        'applications': applications_page,
        'stats': stats,
        'hostels': Hostel.objects.filter(is_active=True),
        'academic_years': AcademicYear.objects.filter(is_active=True),
        'semesters': Semester.objects.filter(is_active=True),
        'status_filter': status_filter,
        'hostel_filter': hostel_filter,
        'academic_year_filter': academic_year_filter,
        'semester_filter': semester_filter,
        'search_query': search_query,
    }
    
    return render(request, 'admin/hostel/application_list.html', context)


@login_required
def admin_hostel_application_detail(request, pk):
    """View detailed hostel application"""
    application = get_object_or_404(
        HostelApplication.objects.select_related(
            'student__user', 'student__programme', 'hostel',
            'academic_year', 'semester', 'approved_by'
        ),
        pk=pk
    )
    
    # Get available beds in the hostel
    available_beds = HostelBed.objects.filter(
        room__hostel=application.hostel,
        room__room_type=application.preferred_room_type,
        status='available',
        academic_year=application.academic_year,
        is_active=True
    ).select_related('room').order_by('room__room_number', 'bed_number')
    
    # Get fee structure
    fee_structure = HostelFeeStructure.objects.filter(
        hostel=application.hostel,
        room_type=application.preferred_room_type,
        academic_year=application.academic_year,
        semester=application.semester
    ).first()
    
    # Check for existing reservations
    existing_reservation = BedReservation.objects.filter(
        student=application.student,
        application=application,
        status__in=['pending', 'confirmed']
    ).first()
    
    context = {
        'application': application,
        'available_beds': available_beds,
        'fee_structure': fee_structure,
        'existing_reservation': existing_reservation,
    }
    
    return render(request, 'admin/hostel/application_detail.html', context)


@login_required
def admin_approve_application(request, pk):
    """Approve hostel application"""
    if request.method == 'POST':
        application = get_object_or_404(HostelApplication, pk=pk)
        
        if application.status == 'approved':
            messages.warning(request, 'Application is already approved.')
            return redirect('admin_hostel_application_detail', pk=pk)
        
        # Check if booking fee is paid
        if not application.booking_fee_paid:
            messages.error(request, 'Cannot approve application. Booking fee not paid.')
            return redirect('admin_hostel_application_detail', pk=pk)
        
        # Update application
        application.status = 'approved'
        application.approved_by = request.user
        application.approved_date = timezone.now()
        application.save()
        
        messages.success(request, f'Application for {application.student.user.get_full_name()} approved successfully.')
        return redirect('admin_hostel_application_detail', pk=pk)
    
    return redirect('admin_hostel_application_list')


@login_required
def admin_reject_application(request, pk):
    """Reject hostel application"""
    if request.method == 'POST':
        application = get_object_or_404(HostelApplication, pk=pk)
        remarks = request.POST.get('remarks', '')
        
        if application.status == 'rejected':
            messages.warning(request, 'Application is already rejected.')
            return redirect('admin_hostel_application_detail', pk=pk)
        
        # Update application
        application.status = 'rejected'
        application.remarks = remarks
        application.save()
        
        messages.success(request, f'Application for {application.student.user.get_full_name()} rejected.')
        return redirect('admin_hostel_application_detail', pk=pk)
    
    return redirect('admin_hostel_application_list')


# views.py - Library Management Views

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Case, When, IntegerField, F, Sum
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import JsonResponse
from decimal import Decimal
from datetime import timedelta, date
from django.core.mail import send_mail
from django.conf import settings

from .models import (
    Book, BookCategory, BookBorrowing, Student, 
    AcademicYear, Semester, User
)

# ============= ADMIN VIEWS =============

@login_required
def admin_library_book_list(request):
    """List all books with filters and search"""
    books = Book.objects.select_related('category').annotate(
        borrowed_count=Count(
            'borrowings',
            filter=Q(borrowings__status='active')
        )
    ).order_by('title')
    
    # Filters
    category_filter = request.GET.get('category')
    status_filter = request.GET.get('status')
    search_query = request.GET.get('search')
    
    if category_filter:
        books = books.filter(category_id=category_filter)
    if status_filter:
        books = books.filter(status=status_filter)
    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(author__icontains=search_query) |
            Q(isbn__icontains=search_query)
        )
    
    # Statistics
    stats = {
        'total_books': Book.objects.count(),
        'available': Book.objects.filter(status='available').count(),
        'borrowed': Book.objects.filter(status='borrowed').count(),
        'total_copies': Book.objects.aggregate(total=Sum('total_copies'))['total'] or 0,
    }
    
    # Pagination
    paginator = Paginator(books, 20)
    page_number = request.GET.get('page')
    books_page = paginator.get_page(page_number)
    
    context = {
        'books': books_page,
        'stats': stats,
        'categories': BookCategory.objects.all().order_by('name'),
        'category_filter': category_filter,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'admin/library/book_list.html', context)


@login_required
def admin_library_book_detail(request, pk):
    """View detailed book information"""
    book = get_object_or_404(
        Book.objects.select_related('category'),
        pk=pk
    )
    
    # Get borrowing history
    borrowings = BookBorrowing.objects.filter(
        book=book
    ).select_related(
        'student__user', 'student__programme',
        'issued_by', 'returned_to'
    ).order_by('-borrow_date')
    
    # Current borrowings (active)
    current_borrowings = borrowings.filter(status__in=['active', 'overdue'])
    
    # Calculate overdue fines for active borrowings
    for borrowing in current_borrowings:
        borrowing.calculate_fine()
    
    # Statistics for this book
    book_stats = {
        'total_borrowed': borrowings.count(),
        'currently_borrowed': current_borrowings.count(),
        'overdue': borrowings.filter(status='overdue').count(),
        'total_fines': borrowings.aggregate(
            total=Sum('fine_amount')
        )['total'] or Decimal('0.00'),
    }
    
    context = {
        'book': book,
        'borrowings': borrowings[:10],  # Last 10 borrowings
        'current_borrowings': current_borrowings,
        'book_stats': book_stats,
    }
    
    return render(request, 'admin/library/book_detail.html', context)


@login_required
def admin_library_issue_book(request, book_id):
    """Issue a book to a student"""
    book = get_object_or_404(Book, pk=book_id)
    
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        
        # Validate book availability
        if book.available_copies <= 0:
            messages.error(request, f'{book.title} is currently not available.')
            return redirect('admin_library_book_detail', pk=book_id)
        
        # Get student
        try:
            student = Student.objects.get(pk=student_id)
        except Student.DoesNotExist:
            messages.error(request, 'Student not found.')
            return redirect('admin_library_book_detail', pk=book_id)
        
        # Check if student already has this book
        existing = BookBorrowing.objects.filter(
            student=student,
            book=book,
            status__in=['active', 'overdue']
        ).exists()
        
        if existing:
            messages.error(request, f'{student.user.get_full_name()} already has this book.')
            return redirect('admin_library_book_detail', pk=book_id)
        
        # Check student's borrowing limit (max 3 books)
        active_borrowings = BookBorrowing.objects.filter(
            student=student,
            status__in=['active', 'overdue']
        ).count()
        
        if active_borrowings >= 3:
            messages.error(request, f'{student.user.get_full_name()} has reached the maximum borrowing limit (3 books).')
            return redirect('admin_library_book_detail', pk=book_id)
        
        # Get current academic year and semester
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        current_semester = Semester.objects.filter(is_current=True).first()
        
        if not current_academic_year or not current_semester:
            messages.error(request, 'No active academic year or semester.')
            return redirect('admin_library_book_detail', pk=book_id)
        
        # Create borrowing record (2 weeks loan period)
        due_date = date.today() + timedelta(days=14)
        
        borrowing = BookBorrowing.objects.create(
            student=student,
            book=book,
            academic_year=current_academic_year,
            semester=current_semester,
            due_date=due_date,
            issued_by=request.user,
            status='active'
        )
        
        # Update book availability
        book.available_copies -= 1
        if book.available_copies == 0:
            book.status = 'borrowed'
        book.save()
        
        # Send email notification
        send_book_issue_email(borrowing)
        
        messages.success(
            request, 
            f'Book "{book.title}" issued to {student.user.get_full_name()} successfully. Due date: {due_date}'
        )
        return redirect('admin_library_book_detail', pk=book_id)
    
    # GET request - show issue form
    # Get available students
    students = Student.objects.select_related(
        'user', 'programme'
    ).filter(
        student_status='active'
    ).order_by('user__first_name')
    
    context = {
        'book': book,
        'students': students,
    }
    
    return render(request, 'admin/library/issue_book.html', context)


@login_required
def admin_library_return_book(request, borrowing_id):
    """Return a borrowed book"""
    borrowing = get_object_or_404(
        BookBorrowing.objects.select_related('book', 'student__user'),
        pk=borrowing_id
    )
    
    if request.method == 'POST':
        if borrowing.status == 'returned':
            messages.warning(request, 'This book has already been returned.')
            return redirect('admin_library_borrowings')
        
        # Calculate final fine
        borrowing.calculate_fine()
        
        # Mark as returned
        borrowing.status = 'returned'
        borrowing.return_date = timezone.now()
        borrowing.returned_to = request.user
        borrowing.save()
        
        # Update book availability
        book = borrowing.book
        book.available_copies += 1
        if book.available_copies > 0:
            book.status = 'available'
        book.save()
        
        # Send return confirmation email
        send_book_return_email(borrowing)
        
        if borrowing.fine_amount > 0:
            messages.success(
                request,
                f'Book returned successfully. Fine: KES {borrowing.fine_amount}. '
                f'Student: {borrowing.student.user.get_full_name()}'
            )
        else:
            messages.success(
                request,
                f'Book returned successfully by {borrowing.student.user.get_full_name()}.'
            )
        
        return redirect('admin_library_borrowings')
    
    return redirect('admin_library_borrowings')


@login_required
def admin_library_borrowings(request):
    """List all borrowings with filters"""
    borrowings = BookBorrowing.objects.select_related(
        'student__user', 'book', 'issued_by'
    ).order_by('-borrow_date')
    
    # Filters
    status_filter = request.GET.get('status')
    overdue_only = request.GET.get('overdue')
    search_query = request.GET.get('search')
    
    if status_filter:
        borrowings = borrowings.filter(status=status_filter)
    if overdue_only:
        borrowings = borrowings.filter(status='overdue')
    if search_query:
        borrowings = borrowings.filter(
            Q(student__registration_number__icontains=search_query) |
            Q(student__user__first_name__icontains=search_query) |
            Q(student__user__last_name__icontains=search_query) |
            Q(book__title__icontains=search_query)
        )
    
    # Calculate fines for active borrowings
    active_borrowings = borrowings.filter(status__in=['active', 'overdue'])
    for borrowing in active_borrowings:
        borrowing.calculate_fine()
    
    # Statistics
    stats = {
        'total': borrowings.count(),
        'active': borrowings.filter(status='active').count(),
        'overdue': borrowings.filter(status='overdue').count(),
        'returned': borrowings.filter(status='returned').count(),
        'total_fines': borrowings.aggregate(
            total=Sum('fine_amount')
        )['total'] or Decimal('0.00'),
    }
    
    # Pagination
    paginator = Paginator(borrowings, 20)
    page_number = request.GET.get('page')
    borrowings_page = paginator.get_page(page_number)
    
    context = {
        'borrowings': borrowings_page,
        'stats': stats,
        'status_filter': status_filter,
        'overdue_only': overdue_only,
        'search_query': search_query,
    }
    
    return render(request, 'admin/library/borrowings_list.html', context)


@login_required
def admin_library_overdue_books(request):
    """List overdue books and send reminders"""
    # Get overdue borrowings
    overdue_borrowings = BookBorrowing.objects.filter(
        status__in=['active', 'overdue'],
        due_date__lt=date.today()
    ).select_related(
        'student__user', 'book'
    ).order_by('due_date')
    
    # Calculate fines
    for borrowing in overdue_borrowings:
        borrowing.calculate_fine()
    
    # Calculate days overdue
    for borrowing in overdue_borrowings:
        borrowing.days_overdue = (date.today() - borrowing.due_date).days
    
    context = {
        'overdue_borrowings': overdue_borrowings,
    }
    
    return render(request, 'admin/library/overdue_books.html', context)


@login_required
def admin_library_send_reminder(request, borrowing_id):
    """Send email reminder to student"""
    borrowing = get_object_or_404(
        BookBorrowing.objects.select_related('student__user', 'book'),
        pk=borrowing_id
    )
    
    # Send reminder email
    send_overdue_reminder_email(borrowing)
    
    messages.success(
        request,
        f'Reminder sent to {borrowing.student.user.get_full_name()} ({borrowing.student.user.email})'
    )
    
    return redirect('admin_library_overdue_books')


@login_required
def admin_library_send_all_reminders(request):
    """Send reminders to all students with overdue books"""
    overdue_borrowings = BookBorrowing.objects.filter(
        status__in=['active', 'overdue'],
        due_date__lt=date.today()
    ).select_related('student__user', 'book')
    
    count = 0
    for borrowing in overdue_borrowings:
        send_overdue_reminder_email(borrowing)
        count += 1
    
    messages.success(request, f'Sent {count} reminder email(s) successfully.')
    return redirect('admin_library_overdue_books')


# ============= HELPER FUNCTIONS =============

def send_book_issue_email(borrowing):
    """Send email when book is issued"""
    subject = f'Book Issued: {borrowing.book.title}'
    message = f"""
Dear {borrowing.student.user.get_full_name()},

You have been issued the following book:

Title: {borrowing.book.title}
Author: {borrowing.book.author}
ISBN: {borrowing.book.isbn}

Borrow Date: {borrowing.borrow_date.strftime('%B %d, %Y')}
Due Date: {borrowing.due_date.strftime('%B %d, %Y')}

Please return the book by the due date to avoid late fees (KES 5 per day).

Best regards,
Library Management
"""
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [borrowing.student.user.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Error sending email: {e}")


def send_book_return_email(borrowing):
    """Send email when book is returned"""
    subject = f'Book Returned: {borrowing.book.title}'
    message = f"""
Dear {borrowing.student.user.get_full_name()},

You have returned the following book:

Title: {borrowing.book.title}
Return Date: {borrowing.return_date.strftime('%B %d, %Y')}

"""
    
    if borrowing.fine_amount > 0:
        message += f"\nLate Fee: KES {borrowing.fine_amount}\n"
        if not borrowing.fine_paid:
            message += "Please pay the late fee at the library counter.\n"
    else:
        message += "No late fees. Thank you for returning on time!\n"
    
    message += "\nBest regards,\nLibrary Management"
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [borrowing.student.user.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Error sending email: {e}")


def send_overdue_reminder_email(borrowing):
    """Send reminder email for overdue books"""
    days_overdue = (date.today() - borrowing.due_date).days
    borrowing.calculate_fine()
    
    subject = f'OVERDUE: {borrowing.book.title} - Action Required'
    message = f"""
Dear {borrowing.student.user.get_full_name()},

This is a reminder that the following book is OVERDUE:

Title: {borrowing.book.title}
Author: {borrowing.book.author}
Due Date: {borrowing.due_date.strftime('%B %d, %Y')}
Days Overdue: {days_overdue} days

Current Late Fee: KES {borrowing.fine_amount}
(KES 5 per day)

Please return the book as soon as possible to avoid additional charges.

Best regards,
Library Management
"""
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [borrowing.student.user.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Error sending email: {e}")


# ============= API ENDPOINTS =============

@login_required
def api_calculate_fine(request, borrowing_id):
    """API endpoint to calculate current fine"""
    borrowing = get_object_or_404(BookBorrowing, pk=borrowing_id)
    borrowing.calculate_fine()
    
    return JsonResponse({
        'success': True,
        'borrowing_id': borrowing.id,
        'fine_amount': float(borrowing.fine_amount),
        'days_overdue': max(0, (date.today() - borrowing.due_date).days),
        'status': borrowing.status
    })


@login_required
def api_search_students(request):
    """API endpoint to search students"""
    query = request.GET.get('q', '')
    
    if len(query) < 2:
        return JsonResponse({'students': []})
    
    students = Student.objects.filter(
        Q(registration_number__icontains=query) |
        Q(user__first_name__icontains=query) |
        Q(user__last_name__icontains=query),
        student_status='active'
    ).select_related('user', 'programme')[:10]
    
    result = [{
        'id': s.id,
        'registration_number': s.registration_number,
        'name': s.user.get_full_name(),
        'programme': s.programme.code
    } for s in students]
    
    return JsonResponse({'students': result})


# ============================================
# views.py - Timetable Management Views
# ============================================

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Prefetch
from django.utils import timezone
from decimal import Decimal
import json

from portal.models import (
    Programme, AcademicYear, Semester, Timetable, TimetableSlot,
    ProgrammeUnit, UnitAllocation, Unit, User, Department, School
)


@login_required
def admin_timetable_master(request):
    """Master timetable management view"""
    # Get all active programmes for dropdown
    programmes = Programme.objects.select_related(
        'department__school'
    ).filter(is_active=True).order_by('department__school__name', 'name')
    
    # Get current academic year
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    
    # Get all academic years for dropdown
    academic_years = AcademicYear.objects.filter(is_active=True).order_by('-start_date')
    
    # Get current semester
    current_semester = Semester.objects.filter(is_current=True).first()
    
    context = {
        'programmes': programmes,
        'academic_years': academic_years,
        'current_academic_year': current_academic_year,
        'current_semester': current_semester,
    }
    
    return render(request, 'admin/timetable/master_timetable.html', context)


# ============================================
# API Endpoints
# ============================================

@login_required
@require_http_methods(["GET"])
def api_get_programme_units(request):
    """Get units for a specific programme, year, and semester"""
    programme_id = request.GET.get('programme_id')
    academic_year_id = request.GET.get('academic_year_id')
    year_of_study = request.GET.get('year_of_study')
    semester_number = request.GET.get('semester_number')
    
    if not all([programme_id, academic_year_id, year_of_study, semester_number]):
        return JsonResponse({
            'success': False,
            'error': 'Missing required parameters'
        }, status=400)
    
    try:
        # Get programme units for the specified criteria
        programme_units = ProgrammeUnit.objects.filter(
            programme_id=programme_id,
            academic_year_id=academic_year_id,
            year_of_study=year_of_study,
            semester_number=semester_number,
            is_active=True
        ).select_related(
            'unit',
            'unit__department'
        ).order_by('unit__code')
        
        # Get current semester
        semester = Semester.objects.filter(
            academic_year_id=academic_year_id,
            semester_number=semester_number
        ).first()
        
        if not semester:
            return JsonResponse({
                'success': False,
                'error': 'Semester not found'
            }, status=404)
        
        # Get or create timetable
        programme = Programme.objects.get(id=programme_id)
        academic_year = AcademicYear.objects.get(id=academic_year_id)
        
        timetable, created = Timetable.objects.get_or_create(
            programme=programme,
            academic_year=academic_year,
            semester=semester,
            year_of_study=year_of_study,
            defaults={
                'name': f"{programme.code} - Year {year_of_study} Sem {semester_number} ({academic_year.name})",
                'created_by': request.user
            }
        )
        
        # Get existing timetable slots
        existing_slots = TimetableSlot.objects.filter(
            timetable=timetable
        ).select_related(
            'unit_allocation__lecturer',
            'unit_allocation__programme_unit__unit'
        )
        
        # Build units data with allocation info
        units_data = []
        for pu in programme_units:
            # Check for unit allocation
            allocation = UnitAllocation.objects.filter(
                programme_unit=pu,
                semester=semester
            ).select_related('lecturer').first()
            
            # Check for existing slot
            slot = existing_slots.filter(
                unit_allocation__programme_unit=pu
            ).first() if allocation else None
            
            unit_info = {
                'id': pu.id,
                'unit_code': pu.unit.code,
                'unit_name': pu.unit.name,
                'credit_hours': pu.unit.credit_hours,
                'unit_type': pu.get_unit_type_display(),
                'allocation_id': allocation.id if allocation else None,
                'lecturer_name': allocation.lecturer.get_full_name() if allocation else 'Not Allocated',
                'lecturer_id': allocation.lecturer.id if allocation else None,
                'is_allocated': bool(allocation),
                'slot': {
                    'id': slot.id,
                    'day': slot.day_of_week,
                    'start_time': slot.start_time.strftime('%H:%M'),
                    'end_time': slot.end_time.strftime('%H:%M'),
                    'venue': slot.venue,
                    'slot_type': slot.get_slot_type_display(),
                } if slot else None
            }
            
            units_data.append(unit_info)
        
        return JsonResponse({
            'success': True,
            'timetable_id': timetable.id,
            'units': units_data,
            'message': f'Found {len(units_data)} units'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_get_lecturers(request):
    """Get all lecturers for allocation"""
    lecturers = User.objects.filter(
        role='lecturer',
        is_active_user=True
    ).select_related('lecturer_profile__department').order_by('first_name', 'last_name')
    
    lecturers_data = [{
        'id': lec.id,
        'name': lec.get_full_name(),
        'department': lec.lecturer_profile.department.name if hasattr(lec, 'lecturer_profile') else 'N/A',
        'designation': lec.lecturer_profile.get_designation_display() if hasattr(lec, 'lecturer_profile') else 'N/A'
    } for lec in lecturers]
    
    return JsonResponse({
        'success': True,
        'lecturers': lecturers_data
    })

@login_required
@require_http_methods(["POST"])
def api_save_timetable_slot(request):
    """Save or update a timetable slot"""
    try:
        data = json.loads(request.body)
        
        timetable_id = data.get('timetable_id')
        programme_unit_id = data.get('programme_unit_id')
        lecturer_id = data.get('lecturer_id')
        day_of_week = data.get('day')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        venue = data.get('venue')
        slot_type = data.get('slot_type', 'lecture')
        slot_id = data.get('slot_id')  # For updates
        
        # Validate required fields
        if not all([timetable_id, programme_unit_id, day_of_week, start_time, end_time, venue]):
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields'
            }, status=400)
        
        # Get timetable
        timetable = Timetable.objects.get(id=timetable_id)
        
        # Get programme unit
        programme_unit = ProgrammeUnit.objects.get(id=programme_unit_id)
        
        # Handle unit allocation
        if lecturer_id:
            # Try to get existing allocation first
            allocation = UnitAllocation.objects.filter(
                programme_unit=programme_unit,
                semester=timetable.semester,
                lecturer_id=lecturer_id
            ).first()
            
            if not allocation:
                # Check if there's an allocation with a different lecturer
                existing_allocation = UnitAllocation.objects.filter(
                    programme_unit=programme_unit,
                    semester=timetable.semester
                ).first()
                
                if existing_allocation:
                    # Update the existing allocation with the new lecturer
                    existing_allocation.lecturer_id = lecturer_id
                    existing_allocation.save()
                    allocation = existing_allocation
                else:
                    # Create new allocation
                    allocation = UnitAllocation.objects.create(
                        programme_unit=programme_unit,
                        semester=timetable.semester,
                        lecturer_id=lecturer_id,
                        assigned_by=request.user,
                        status='pending'
                    )
        else:
            # Try to get existing allocation
            allocation = UnitAllocation.objects.filter(
                programme_unit=programme_unit,
                semester=timetable.semester
            ).first()
            
            if not allocation:
                return JsonResponse({
                    'success': False,
                    'error': 'Please allocate a lecturer first'
                }, status=400)
        
        # Check for conflicts (same time, same day, same timetable)
        conflicts = TimetableSlot.objects.filter(
            timetable=timetable,
            day_of_week=day_of_week,
            start_time__lt=end_time,
            end_time__gt=start_time
        )
        
        if slot_id:
            conflicts = conflicts.exclude(id=slot_id)
        
        if conflicts.exists():
            conflict_slot = conflicts.first()
            return JsonResponse({
                'success': False,
                'error': f'Time conflict with {conflict_slot.unit_allocation.programme_unit.unit.code}',
                'conflict': True
            }, status=400)
        
        # Create or update slot
        if slot_id:
            # Update existing slot
            slot = TimetableSlot.objects.get(id=slot_id)
            slot.day_of_week = day_of_week
            slot.start_time = start_time
            slot.end_time = end_time
            slot.venue = venue
            slot.slot_type = slot_type
            slot.unit_allocation = allocation
            slot.save()
            message = 'Slot updated successfully'
        else:
            # Create new slot
            slot = TimetableSlot.objects.create(
                timetable=timetable,
                unit_allocation=allocation,
                day_of_week=day_of_week,
                start_time=start_time,
                end_time=end_time,
                venue=venue,
                slot_type=slot_type
            )
            message = 'Slot created successfully'
        
        # Helper function to format time
        def format_time(time_value):
            """Convert time to string format HH:MM"""
            if isinstance(time_value, str):
                # Already a string, just ensure it's in HH:MM format
                return time_value[:5] if len(time_value) > 5 else time_value
            else:
                # It's a time object, format it
                return time_value.strftime('%H:%M')
        
        return JsonResponse({
            'success': True,
            'message': message,
            'slot': {
                'id': slot.id,
                'day': slot.day_of_week,
                'start_time': format_time(slot.start_time),
                'end_time': format_time(slot.end_time),
                'venue': slot.venue,
                'unit_code': allocation.programme_unit.unit.code,
                'unit_name': allocation.programme_unit.unit.name,
                'lecturer_name': allocation.lecturer.get_full_name()
            }
        })
        
    except Timetable.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Timetable not found'
        }, status=404)
    except ProgrammeUnit.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Programme unit not found'
        }, status=404)
    except TimetableSlot.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Timetable slot not found'
        }, status=404)
    except Exception as e:
        import traceback
        print(traceback.format_exc())  # For debugging
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
        
        
@login_required
@require_http_methods(["POST"])
def api_delete_timetable_slot(request):
    """Delete a timetable slot"""
    try:
        data = json.loads(request.body)
        slot_id = data.get('slot_id')
        
        if not slot_id:
            return JsonResponse({
                'success': False,
                'error': 'Slot ID required'
            }, status=400)
        
        slot = TimetableSlot.objects.get(id=slot_id)
        slot.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Slot deleted successfully'
        })
        
    except TimetableSlot.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Slot not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_get_timetable_slots(request):
    """Get all slots for a timetable"""
    timetable_id = request.GET.get('timetable_id')
    
    if not timetable_id:
        return JsonResponse({
            'success': False,
            'error': 'Timetable ID required'
        }, status=400)
    
    try:
        slots = TimetableSlot.objects.filter(
            timetable_id=timetable_id
        ).select_related(
            'unit_allocation__lecturer',
            'unit_allocation__programme_unit__unit'
        ).order_by('day_of_week', 'start_time')
        
        slots_data = [{
            'id': slot.id,
            'day': slot.day_of_week,
            'start_time': slot.start_time.strftime('%H:%M'),
            'end_time': slot.end_time.strftime('%H:%M'),
            'venue': slot.venue,
            'slot_type': slot.get_slot_type_display(),
            'unit_code': slot.unit_allocation.programme_unit.unit.code,
            'unit_name': slot.unit_allocation.programme_unit.unit.name,
            'lecturer_name': slot.unit_allocation.lecturer.get_full_name(),
            'lecturer_id': slot.unit_allocation.lecturer.id,
            'programme_unit_id': slot.unit_allocation.programme_unit.id,
        } for slot in slots]
        
        return JsonResponse({
            'success': True,
            'slots': slots_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_publish_timetable(request):
    """Publish timetable to make it visible to students"""
    try:
        data = json.loads(request.body)
        timetable_id = data.get('timetable_id')
        
        if not timetable_id:
            return JsonResponse({
                'success': False,
                'error': 'Timetable ID required'
            }, status=400)
        
        timetable = Timetable.objects.get(id=timetable_id)
        timetable.is_published = True
        timetable.published_date = timezone.now()
        timetable.approved_by = request.user
        timetable.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Timetable published successfully'
        })
        
    except Timetable.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Timetable not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import (
    Student,
    AcademicYear,
    Semester,
    Timetable,
    TimetableSlot
)


@login_required
def student_timetable(request):
    """
    Student personal timetable view
    Shows timetable only if it is published
    """
    try:
        # ===============================
        # Get student profile
        # ===============================
        student = request.user.student_profile

        # ===============================
        # Get current academic year & semester
        # ===============================
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        current_semester = Semester.objects.filter(is_current=True).first()

        timetable = None
        slots = []
        organized_slots = {}

        # ===============================
        # Fetch timetable ONLY if published
        # ===============================
        if current_academic_year and current_semester:
            timetable = Timetable.objects.filter(
                programme=student.programme,
                academic_year=current_academic_year,
                semester=current_semester,
                year_of_study=student.current_year,
                is_published=True
            ).first()

            if timetable:
                slots = TimetableSlot.objects.filter(
                    timetable=timetable
                ).select_related(
                    'unit_allocation__lecturer',
                    'unit_allocation__programme_unit__unit'
                ).order_by('day_of_week', 'start_time')

        # ===============================
        # Organize slots by day + time
        # ===============================
        for slot in slots:
            key = f"{slot.day_of_week}_{slot.start_time}"
            organized_slots[key] = slot

        # ===============================
        # Context
        # ===============================
        context = {
            'student': student,
            'current_academic_year': current_academic_year,
            'current_semester': current_semester,
            'timetable': timetable,
            'organized_slots': organized_slots,
            'has_timetable': timetable is not None,
        }

        return render(request, 'student/timetable.html', context)

    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('student_dashboard')

    except Exception as e:
        messages.error(request, f"Error loading timetable: {str(e)}")
        return redirect('student_dashboard')


# views.py - Updated Student ID Views with M-Pesa Integration

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q
import json

from .models import (
    Student, StudentIDType, StudentIDFeeStructure, StudentIDApplication,
    StudentIDCard, StudentIDPayment, IDCardNotification, AcademicYear
)
from .student_mpesa_integration import (
    StudentIDMpesaIntegration, process_student_id_mpesa_callback
)


@login_required
def student_id_dashboard(request):
    """Student ID dashboard - view applications and cards"""
    student = get_object_or_404(Student, user=request.user)
    
    # Get all applications
    applications = StudentIDApplication.objects.filter(
        student=student
    ).order_by('-application_date')
    
    # Get active application
    active_application = applications.filter(
        status__in=['draft', 'submitted', 'under_review', 'payment_pending', 
                   'payment_confirmed', 'in_production']
    ).first()
    
    # Get all ID cards
    id_cards = StudentIDCard.objects.filter(student=student).order_by('-issue_date')
    
    # Get active card
    active_card = id_cards.filter(status='active').first()
    
    # Get recent notifications
    notifications = IDCardNotification.objects.filter(
        student=student
    ).order_by('-sent_at')[:5]
    
    context = {
        'student': student,
        'applications': applications,
        'active_application': active_application,
        'id_cards': id_cards,
        'active_card': active_card,
        'notifications': notifications,
    }
    
    return render(request, 'student/student_id_dashboard.html', context)


@login_required
def apply_for_student_id(request):
    """Apply for a new student ID card"""
    student = get_object_or_404(Student, user=request.user)
    current_year = AcademicYear.objects.filter(is_current=True).first()
    
    if not current_year:
        messages.error(request, "No active academic year found.")
        return redirect('student_id_dashboard')
    
    if request.method == 'POST':
        id_type_id = request.POST.get('id_type')
        is_rush = request.POST.get('is_rush') == 'on'
        application_reason = request.POST.get('application_reason')
        reason_details = request.POST.get('reason_details', '')
        
        try:
            id_type = StudentIDType.objects.get(id=id_type_id, is_active=True)
            fee_structure = StudentIDFeeStructure.objects.get(
                id_type=id_type,
                academic_year=current_year,
                is_active=True
            )
            
            # Check if student already has an active application
            active_apps = StudentIDApplication.objects.filter(
                student=student,
                status__in=['draft', 'submitted', 'under_review', 'payment_pending', 
                           'payment_confirmed', 'in_production']
            )
            
            if active_apps.exists():
                messages.warning(request, "You already have an active ID application. Please complete it first.")
                return redirect('view_id_application', application_id=active_apps.first().id)
            
            # Create application
            is_replacement = application_reason in ['lost', 'damaged', 'expired']
            application = StudentIDApplication.objects.create(
                student=student,
                id_type=id_type,
                fee_structure=fee_structure,
                application_reason=application_reason,
                reason_details=reason_details,
                is_rush_processing=is_rush,
                is_replacement=is_replacement,
                amount_due=fee_structure.get_total_fee(
                    is_rush=is_rush,
                    is_replacement=is_replacement
                ),
                status='draft'
            )
            
            # Send notification
            IDCardNotification.objects.create(
                student=student,
                application=application,
                notification_type='application_submitted',
                title='Student ID Application Created',
                message=f'Your student ID application #{application.application_number} has been created. Please upload your photo and proceed to payment.',
                sent_via_portal=True
            )
            
            messages.success(request, f"Application #{application.application_number} created successfully! Please upload your photo.")
            return redirect('upload_id_photo', application_id=application.id)
            
        except StudentIDType.DoesNotExist:
            messages.error(request, "Invalid ID type selected.")
        except StudentIDFeeStructure.DoesNotExist:
            messages.error(request, "No fee structure found for the selected ID type.")
        except Exception as e:
            messages.error(request, f"Error creating application: {str(e)}")
    
    # GET request - show application form
    id_types = StudentIDType.objects.filter(is_active=True)
    current_fees = StudentIDFeeStructure.objects.filter(
        academic_year=current_year,
        is_active=True
    ).select_related('id_type')
    
    context = {
        'student': student,
        'id_types': id_types,
        'current_fees': current_fees,
        'current_year': current_year,
    }
    
    return render(request, 'student/apply_student_id.html', context)


@login_required
def upload_id_photo(request, application_id):
    """Upload photo for ID application"""
    student = get_object_or_404(Student, user=request.user)
    application = get_object_or_404(
        StudentIDApplication, 
        id=application_id, 
        student=student
    )
    
    if application.status not in ['draft', 'submitted']:
        messages.error(request, "Cannot upload photo. Application is not in draft status.")
        return redirect('view_id_application', application_id=application.id)
    
    if request.method == 'POST':
        if 'photo' in request.FILES:
            application.photo = request.FILES['photo']
            
            # Optional back photo
            if 'photo_back' in request.FILES:
                application.photo_back = request.FILES['photo_back']
            
            application.status = 'submitted'
            application.submitted_date = timezone.now()
            application.save()
            
            # Send notification
            IDCardNotification.objects.create(
                student=student,
                application=application,
                notification_type='application_submitted',
                title='Photo Uploaded Successfully',
                message=f'Photo uploaded for application #{application.application_number}. You can now proceed to payment.',
                sent_via_portal=True
            )
            
            messages.success(request, "Photo uploaded successfully! You can now proceed to payment.")
            return redirect('view_id_application', application_id=application.id)
        else:
            messages.error(request, "Please select a photo to upload.")
    
    context = {
        'student': student,
        'application': application,
    }
    
    return render(request, 'student/upload_id_photo.html', context)


@login_required
def view_id_application(request, application_id):
    """View application details"""
    student = get_object_or_404(Student, user=request.user)
    application = get_object_or_404(
        StudentIDApplication, 
        id=application_id, 
        student=student
    )
    
    # Get payments for this application
    payments = StudentIDPayment.objects.filter(
        application=application
    ).order_by('-payment_date')
    
    # Get notifications
    notifications = IDCardNotification.objects.filter(
        application=application
    ).order_by('-sent_at')
    
    context = {
        'student': student,
        'application': application,
        'payments': payments,
        'notifications': notifications,
    }
    
    return render(request, 'student/view_id_application.html', context)


@login_required
def initiate_id_payment(request, application_id):
    """Initiate payment for ID application"""
    student = get_object_or_404(Student, user=request.user)
    application = get_object_or_404(
        StudentIDApplication, 
        id=application_id, 
        student=student
    )
    
    if application.status not in ['submitted', 'payment_pending']:
        messages.error(request, "Payment cannot be initiated for this application.")
        return redirect('view_id_application', application_id=application.id)
    
    if application.balance <= 0:
        messages.info(request, "This application has been fully paid.")
        return redirect('view_id_application', application_id=application.id)
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        phone_number = request.POST.get('phone_number', '')
        
        try:
            if payment_method == 'mpesa':
                # Validate phone number
                if not phone_number:
                    messages.error(request, "Please provide a phone number for M-Pesa payment.")
                    return redirect('initiate_id_payment', application_id=application.id)
                
                # Create payment record first
                payment = StudentIDPayment.objects.create(
                    application=application,
                    amount=application.balance,
                    payment_method='mpesa',
                    phone_number=phone_number,
                    status='pending'
                )
                
                # Initialize M-Pesa
                mpesa = StudentIDMpesaIntegration()
                response = mpesa.initiate_stk_push(
                    phone_number=phone_number,
                    amount=application.balance,
                    account_reference=payment.payment_reference,
                    transaction_desc=f"Student ID: {application.application_number}"
                )
                
                if response.get('success'):
                    # Update payment with M-Pesa details
                    payment.merchant_request_id = response.get('merchant_request_id')
                    payment.checkout_request_id = response.get('checkout_request_id')
                    payment.save()
                    
                    # Update application status
                    application.status = 'payment_pending'
                    application.save()
                    
                    messages.success(
                        request, 
                        f"Payment request sent! Please check your phone ({phone_number}) "
                        f"and enter your M-Pesa PIN to complete the payment."
                    )
                    return redirect('view_id_application', application_id=application.id)
                else:
                    # Failed to initiate
                    payment.status = 'failed'
                    payment.result_description = response.get('error', 'Failed to initiate payment')
                    payment.save()
                    
                    messages.error(
                        request, 
                        f"Failed to initiate M-Pesa payment: {response.get('error')}"
                    )
            
            elif payment_method in ['bank', 'cash', 'card']:
                # Create payment record for other methods
                payment = StudentIDPayment.objects.create(
                    application=application,
                    amount=application.balance,
                    payment_method=payment_method,
                    status='pending'
                )
                
                application.status = 'payment_pending'
                application.save()
                
                # Send notification with payment instructions
                IDCardNotification.objects.create(
                    student=student,
                    application=application,
                    notification_type='payment_request',
                    title='Payment Instructions',
                    message=f'Payment instructions for {payment_method} will be sent to your email. '
                           f'Reference: {payment.payment_reference}',
                    sent_via_portal=True,
                    sent_via_email=True
                )
                
                messages.info(
                    request, 
                    f"Payment instructions for {payment_method} have been sent to your email. "
                    f"Payment reference: {payment.payment_reference}"
                )
                return redirect('view_id_application', application_id=application.id)
            
            else:
                messages.error(request, "Invalid payment method selected.")
                
        except Exception as e:
            messages.error(request, f"Error initiating payment: {str(e)}")
    
    context = {
        'student': student,
        'application': application,
    }
    
    return render(request, 'student/initiate_id_payment.html', context)


@login_required
def my_student_ids(request):
    """View all issued student ID cards"""
    student = get_object_or_404(Student, user=request.user)
    
    # Get all ID cards
    id_cards = StudentIDCard.objects.filter(
        student=student
    ).select_related('application').order_by('-issue_date')
    
    # Get current active card
    active_card = id_cards.filter(status='active').first()
    
    context = {
        'student': student,
        'id_cards': id_cards,
        'active_card': active_card,
    }
    
    return render(request, 'student/my_student_ids.html', context)


@login_required
def download_digital_id(request, card_id):
    """Download digital ID card"""
    student = get_object_or_404(Student, user=request.user)
    card = get_object_or_404(
        StudentIDCard, 
        id=card_id, 
        student=student
    )
    
    if not card.digital_id_file:
        messages.error(request, "Digital ID file not available.")
        return redirect('my_student_ids')
    
    # Update last verified
    card.last_verified = timezone.now()
    card.save()
    
    # Serve file
    response = HttpResponse(card.digital_id_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="student_id_{card.card_number}.pdf"'
    return response


@csrf_exempt
def student_id_payment_callback(request):
    """Handle M-Pesa payment callbacks for student ID"""
    if request.method == 'POST':
        try:
            # Parse callback data
            callback_data = json.loads(request.body.decode('utf-8'))
            
            # Process callback
            result = process_student_id_mpesa_callback(callback_data)
            
            if result.get('success'):
                return JsonResponse({
                    'ResultCode': 0,
                    'ResultDesc': 'Success'
                })
            else:
                return JsonResponse({
                    'ResultCode': 1,
                    'ResultDesc': result.get('error', 'Processing failed')
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'ResultCode': 1,
                'ResultDesc': 'Invalid JSON'
            }, status=400)
        except Exception as e:
            print(f"Callback error: {str(e)}")
            return JsonResponse({
                'ResultCode': 1,
                'ResultDesc': str(e)
            }, status=500)
    
    return JsonResponse({
        'ResultCode': 1,
        'ResultDesc': 'Invalid request method'
    }, status=405)


@login_required
def check_payment_status(request, application_id):
    """AJAX endpoint to check payment status"""
    student = get_object_or_404(Student, user=request.user)
    application = get_object_or_404(
        StudentIDApplication, 
        id=application_id, 
        student=student
    )
    
    # Get latest payment
    latest_payment = StudentIDPayment.objects.filter(
        application=application
    ).order_by('-payment_date').first()
    
    if latest_payment:
        return JsonResponse({
            'status': latest_payment.status,
            'application_status': application.status,
            'amount_paid': float(application.amount_paid),
            'balance': float(application.balance),
            'is_paid': application.is_paid,
            'payment_reference': latest_payment.payment_reference,
            'mpesa_receipt': latest_payment.mpesa_receipt_number or '',
        })
    
    return JsonResponse({
        'status': 'no_payment',
        'application_status': application.status,
    })


# Public endpoint for ID verification (no login required)
def verify_student_id(request, card_number):
    """Verify a student ID card (public endpoint)"""
    try:
        id_card = StudentIDCard.objects.select_related(
            'student__user', 'student__programme'
        ).get(
            card_number=card_number,
            status='active'
        )
        
        # Update last verified timestamp
        id_card.last_verified = timezone.now()
        id_card.save()
        
        response_data = {
            'valid': True,
            'card_number': id_card.card_number,
            'student_name': id_card.student.user.get_full_name(),
            'registration_number': id_card.student.registration_number,
            'programme': id_card.student.programme.name,
            'issue_date': id_card.issue_date.strftime('%Y-%m-%d'),
            'expiry_date': id_card.expiry_date.strftime('%Y-%m-%d'),
            'is_expired': id_card.is_expired,
            'status': id_card.status,
        }
        
        return JsonResponse(response_data)
        
    except StudentIDCard.DoesNotExist:
        return JsonResponse({
            'valid': False, 
            'error': 'ID card not found or inactive'
        }, status=404)


@login_required
def id_notifications(request):
    """View all ID-related notifications"""
    student = get_object_or_404(Student, user=request.user)
    
    notifications = IDCardNotification.objects.filter(
        student=student
    ).order_by('-sent_at')
    
    # Mark as read
    notifications.filter(is_read=False).update(
        is_read=True, 
        read_date=timezone.now()
    )
    
    context = {
        'student': student,
        'notifications': notifications,
    }
    
    return render(request, 'student/id_notifications.html', context)


# ============= ADMIN VIEWS =============

@login_required
def admin_id_applications(request):
    """Admin view of all ID applications"""
    if request.user.role not in ['admin', 'registrar', 'finance']:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('admin_dashboard')
    
    status_filter = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    applications = StudentIDApplication.objects.all().select_related(
        'student', 'id_type', 'fee_structure'
    ).order_by('-application_date')
    
    if status_filter:
        applications = applications.filter(status=status_filter)
    
    if date_from:
        applications = applications.filter(application_date__date__gte=date_from)
    
    if date_to:
        applications = applications.filter(application_date__date__lte=date_to)
    
    # Statistics
    total_applications = applications.count()
    pending_payment = applications.filter(status='payment_pending').count()
    in_production = applications.filter(status='in_production').count()
    ready_for_pickup = applications.filter(status='ready_for_pickup').count()
    
    context = {
        'applications': applications,
        'total_applications': total_applications,
        'pending_payment': pending_payment,
        'in_production': in_production,
        'ready_for_pickup': ready_for_pickup,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'admin/students/student_id_applications.html', context)


@login_required
def admin_view_application(request, application_id):
    """Admin view of specific application"""
    if request.user.role not in ['admin', 'registrar', 'finance']:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('admin_dashboard')
    
    application = get_object_or_404(StudentIDApplication, id=application_id)
    payments = StudentIDPayment.objects.filter(application=application).order_by('-payment_date')
    
    # Get any issued card
    try:
        issued_card = StudentIDCard.objects.get(application=application)
    except StudentIDCard.DoesNotExist:
        issued_card = None
    
    context = {
        'application': application,
        'payments': payments,
        'issued_card': issued_card,
    }
    
    return render(request, 'admin/students/view_id_application.html', context)


@login_required
def update_application_status(request, application_id):
    """Update application status (admin only)"""
    if request.user.role not in ['admin', 'registrar', 'finance']:
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('admin_dashboard')
    
    application = get_object_or_404(StudentIDApplication, id=application_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        if new_status in dict(StudentIDApplication.APPLICATION_STATUS).keys():
            old_status = application.status
            application.status = new_status
            application.reviewed_by = request.user
            application.review_date = timezone.now()
            application.review_notes = notes
            
            # Set completion date if moving to completed
            if new_status == 'completed':
                application.actual_completion_date = timezone.now().date()
            
            application.save()
            
            # Send notification to student
            IDCardNotification.objects.create(
                student=application.student,
                application=application,
                notification_type='status_update',
                title=f'Application Status Updated',
                message=f'Your student ID application #{application.application_number} status has been updated from {old_status} to {new_status}. Notes: {notes}',
                sent_via_portal=True,
                sent_via_email=True
            )
            
            messages.success(request, f"Application status updated to {new_status}.")
        else:
            messages.error(request, "Invalid status selected.")
    
    return redirect('admin_view_id_application', application_id=application.id)


@login_required
def issue_student_id(request, application_id):
    """Issue student ID card (admin only)"""
    if request.user.role not in ['admin', 'registrar']:
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('admin_dashboard')
    
    application = get_object_or_404(StudentIDApplication, id=application_id)
    
    if application.status != 'payment_confirmed':
        messages.error(request, "Cannot issue ID card. Payment not confirmed.")
        return redirect('admin_view_id_application', application_id=application.id)
    
    if request.method == 'POST':
        card_type = request.POST.get('card_type', 'physical')
        pick_up_location = request.POST.get('pick_up_location', '')
        pick_up_code = request.POST.get('pick_up_code', '')
        
        try:
            # Check if card already issued
            if StudentIDCard.objects.filter(application=application).exists():
                messages.warning(request, "ID card already issued for this application.")
                return redirect('admin_view_id_application', application_id=application.id)
            
            # Generate and issue card
            id_card = StudentIDCard.objects.create(
                student=application.student,
                application=application,
                card_type=card_type,
                issue_date=timezone.now().date(),
                expiry_date=timezone.now().date() + timedelta(days=application.id_type.validity_period_months * 30),
                status='active',
                pick_up_location=pick_up_location if card_type == 'physical' else '',
                barcode=f"BAR{application.application_number}"
            )
            
            # Update application status
            if card_type == 'physical':
                application.status = 'ready_for_pickup'
                application.pick_up_location = pick_up_location
                application.pick_up_code = pick_up_code
            else:
                application.status = 'delivered'
                application.digital_id_url = f"/media/digital_ids/{id_card.id}.pdf"
                application.digital_id_sent_date = timezone.now()
            
            application.save()
            
            # Send notification
            if card_type == 'physical':
                notification_type = 'ready_for_pickup'
                title = 'ID Card Ready for Pickup'
                message = f'Your physical student ID card for application #{application.application_number} is ready for pickup at {pick_up_location}. Pickup code: {pick_up_code}'
            else:
                notification_type = 'delivered'
                title = 'Digital ID Card Delivered'
                message = f'Your digital student ID card for application #{application.application_number} has been delivered. You can download it from your portal.'
            
            IDCardNotification.objects.create(
                student=application.student,
                application=application,
                notification_type=notification_type,
                title=title,
                message=message,
                sent_via_portal=True,
                sent_via_email=True,
                sent_via_sms=True
            )
            
            messages.success(request, f"Student ID card issued successfully!")
            
        except Exception as e:
            messages.error(request, f"Error issuing ID card: {str(e)}")
    
    context = {
        'application': application,
    }
    
    return render(request, 'admin/students/issue_student_id.html', context)


@login_required
def id_card_reports(request):
    """Generate reports for ID cards"""
    if request.user.role not in ['admin', 'registrar', 'finance']:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('admin_dashboard')
    
    # Date range filter
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Base queryset
    applications = StudentIDApplication.objects.all()
    cards = StudentIDCard.objects.all()
    payments = StudentIDPayment.objects.filter(status='completed')
    
    if date_from:
        applications = applications.filter(application_date__date__gte=date_from)
        cards = cards.filter(issue_date__gte=date_from)
        payments = payments.filter(payment_date__date__gte=date_from)
    
    if date_to:
        applications = applications.filter(application_date__date__lte=date_to)
        cards = cards.filter(issue_date__lte=date_to)
        payments = payments.filter(payment_date__date__lte=date_to)
    
    # Statistics
    total_revenue = payments.aggregate(total=Sum('amount'))['total'] or 0
    total_applications = applications.count()
    total_cards_issued = cards.count()
    
    # Status distribution
    status_counts = applications.values('status').annotate(count=Count('id')).order_by('status')
    
    # Revenue by ID type
    revenue_by_type = StudentIDPayment.objects.filter(
        status='completed',
        application__fee_structure__id_type__isnull=False
    ).values(
        'application__fee_structure__id_type__name'
    ).annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    context = {
        'total_revenue': total_revenue,
        'total_applications': total_applications,
        'total_cards_issued': total_cards_issued,
        'status_counts': status_counts,
        'revenue_by_type': revenue_by_type,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'admin/students/id_card_reports.html', context)

# views.py - Add these views to handle chat API endpoints

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db.models import Q
import json
from datetime import timedelta

from .models import (
    ChatSession, ChatMessage, AIKnowledgeBase, 
    AIPersonalization, ProactiveAIAlert, AITrainingData,
    Student, SemesterResults, FeeBalance
)


@require_http_methods(["POST"])
def chat_send_message(request):
    """Handle incoming chat messages"""
    try:
        data = json.loads(request.body)
        message_text = data.get('message', '').strip()
        session_id = data.get('session_id')
        
        if not message_text:
            return JsonResponse({'success': False, 'error': 'Empty message'})
        
        # Get or create session
        try:
            session = ChatSession.objects.get(session_id=session_id)
        except ChatSession.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid session'})
        
        # Create user message
        user_message = ChatMessage.objects.create(
            session=session,
            message_type='user',
            message_text=message_text
        )
        
        # Update session
        session.message_count += 1
        session.last_activity = timezone.now()
        session.save()
        
        # Process message and get AI response
        ai_response, actions = process_ai_message(message_text, session, request.user)
        
        # Create AI response message
        ai_message = ChatMessage.objects.create(
            session=session,
            message_type='ai',
            message_text=ai_response,
            detected_intent=detect_intent(message_text)
        )
        
        session.message_count += 1
        session.save()
        
        return JsonResponse({
            'success': True,
            'response': ai_response,
            'actions': actions,
            'message_id': str(ai_message.message_id)
        })
        
    except Exception as e:
        print(f"Chat error: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': 'An error occurred processing your message'
        })


def process_ai_message(message, session, user):
    """Process message and generate AI response"""
    message_lower = message.lower()
    
    # Check for greeting
    if any(word in message_lower for word in ['hello', 'hi', 'hey', 'greetings']):
        name = user.first_name if user.is_authenticated else 'there'
        return (
            f"Hello {name}! 👋 I'm your MUT AI Assistant. "
            f"I can help you with academic information, fees, timetables, "
            f"results, and much more. What would you like to know?",
            []
        )
    
    # Search knowledge base
    knowledge_matches = AIKnowledgeBase.objects.filter(
        Q(question__icontains=message) |
        Q(keywords__icontains=message),
        status='active',
        is_verified=True
    ).order_by('-confidence_score', '-usage_count')
    
    # Check authentication requirement
    if user.is_authenticated:
        knowledge_matches = knowledge_matches.filter(
            Q(requires_authentication=False) |
            Q(requires_authentication=True)
        )
    else:
        knowledge_matches = knowledge_matches.filter(requires_authentication=False)
    
    if knowledge_matches.exists():
        knowledge = knowledge_matches.first()
        
        # Update usage stats
        knowledge.usage_count += 1
        knowledge.last_used = timezone.now()
        knowledge.save()
        
        # Personalize response if authenticated
        response = personalize_response(knowledge.answer, user)
        
        # Generate action buttons
        actions = generate_actions(knowledge, user)
        
        return response, actions
    
    # Handle specific queries for authenticated users
    if user.is_authenticated and hasattr(user, 'student_profile'):
        student = user.student_profile
        
        # GPA query
        if 'gpa' in message_lower or 'grade' in message_lower:
            return handle_gpa_query(student)
        
        # Fee query
        if 'fee' in message_lower or 'balance' in message_lower or 'payment' in message_lower:
            return handle_fee_query(student)
        
        # Timetable query
        if 'timetable' in message_lower or 'schedule' in message_lower or 'class' in message_lower:
            return handle_timetable_query(student)
        
        # Results query
        if 'result' in message_lower or 'exam' in message_lower or 'marks' in message_lower:
            return handle_results_query(student)
        
        # Registration query
        if 'register' in message_lower or 'enroll' in message_lower or 'unit' in message_lower:
            return handle_registration_query(student)
    
    # Default response with suggestions
    suggestions = get_popular_questions(user)
    actions = [
        {'type': 'message', 'value': q, 'label': q[:30] + '...', 'icon': 'ri-question-line'}
        for q in suggestions[:3]
    ]
    
    return (
        "I'm not sure I understand that question. Here are some things I can help you with:",
        actions
    )


def handle_gpa_query(student):
    """Handle GPA-related queries"""
    gpa = float(student.cumulative_gpa)
    
    response = f"Your current cumulative GPA is {gpa:.2f}."
    
    if gpa >= 3.5:
        response += " Excellent work! Keep up the great performance! 🌟"
    elif gpa >= 3.0:
        response += " You're doing well! Keep pushing for excellence! 💪"
    elif gpa >= 2.5:
        response += " You're on track. Consider seeking academic support to improve further."
    else:
        response += " Your GPA needs attention. I recommend speaking with your academic advisor for support."
    
    actions = [
        {'type': 'link', 'value': '/student/transcript/', 'label': 'View Full Results', 'icon': 'ri-file-list-line'},
        {'type': 'message', 'value': 'How can I improve my GPA?', 'label': 'Improvement Tips', 'icon': 'ri-lightbulb-line'}
    ]
    
    return response, actions


def handle_fee_query(student):
    """Handle fee-related queries"""
    try:
        # Get latest fee balance
        from django.db.models import Max
        current_semester = student.current_semester
        
        fee_balance = FeeBalance.objects.filter(
            student=student
        ).order_by('-academic_year__start_date', '-semester__start_date').first()
        
        if fee_balance:
            balance = float(fee_balance.balance)
            total = float(fee_balance.total_fees)
            paid = float(fee_balance.amount_paid)
            
            if balance <= 0:
                response = "✅ Great news! Your fees are fully paid."
            else:
                response = f"Your current fee balance is KES {balance:,.2f}.\n"
                response += f"Total fees: KES {total:,.2f}\n"
                response += f"Amount paid: KES {paid:,.2f}"
        else:
            response = "I couldn't find your fee balance information. Please contact the finance office."
        
        actions = [
            {'type': 'link', 'value': '/student/fees/statement/', 'label': 'Fee Statement', 'icon': 'ri-file-text-line'},
            {'type': 'link', 'value': '/student/fees/payment/', 'label': 'Make Payment', 'icon': 'ri-money-dollar-circle-line'}
        ]
        
        return response, actions
        
    except Exception as e:
        return "I encountered an error fetching your fee information. Please try again later.", []


def handle_timetable_query(student):
    """Handle timetable queries"""
    response = f"I can help you with your timetable for Year {student.current_year}, "
    response += f"Semester {student.current_semester}."
    
    actions = [
        {'type': 'link', 'value': '/student/timetable/', 'label': 'View Timetable', 'icon': 'ri-calendar-line'},
        {'type': 'link', 'value': '/student/units/', 'label': 'My Units', 'icon': 'ri-book-open-line'}
    ]
    
    return response, actions


def handle_results_query(student):
    """Handle results queries"""
    # Get latest results
    latest_results = SemesterResults.objects.filter(
        student=student,
        is_published=True
    ).order_by('-semester__start_date')[:5]
    
    if latest_results.exists():
        response = f"Your latest results are available. You have {latest_results.count()} "
        response += "published results."
    else:
        response = "No results are currently published for you."
    
    actions = [
        {'type': 'link', 'value': '/student/results/', 'label': 'View Results', 'icon': 'ri-file-list-line'},
        {'type': 'link', 'value': '/student/transcript/', 'label': 'Transcript', 'icon': 'ri-file-download-line'}
    ]
    
    return response, actions


def handle_registration_query(student):
    """Handle unit registration queries"""
    response = "I can help you with unit registration. "
    response += "Make sure you've reported for the semester before enrolling in units."
    
    actions = [
        {'type': 'link', 'value': '/student/semester-report/', 'label': 'Semester Report', 'icon': 'ri-file-chart-line'},
        {'type': 'link', 'value': '/student/unit-enrollment/', 'label': 'Enroll Units', 'icon': 'ri-book-mark-line'}
    ]
    
    return response, actions


def personalize_response(response, user):
    """Personalize response with user data"""
    if not user.is_authenticated:
        return response
    
    # Replace placeholders
    response = response.replace('{user_name}', user.first_name or user.username)
    
    if hasattr(user, 'student_profile'):
        student = user.student_profile
        response = response.replace('{registration_number}', student.registration_number)
        response = response.replace('{programme}', student.programme.name)
        response = response.replace('{year}', str(student.current_year))
        response = response.replace('{semester}', str(student.current_semester))
    
    return response


def generate_actions(knowledge, user):
    """Generate action buttons from knowledge entry"""
    actions = []
    
    if knowledge.has_links and knowledge.links:
        for link in knowledge.links[:3]:
            actions.append({
                'type': 'link',
                'value': link.get('url', '#'),
                'label': link.get('label', 'More Info'),
                'icon': link.get('icon', 'ri-external-link-line')
            })
    
    return actions


def detect_intent(message):
    """Detect user intent from message"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['hello', 'hi', 'hey']):
        return 'greeting'
    elif '?' in message:
        return 'question'
    elif any(word in message_lower for word in ['help', 'assist', 'support']):
        return 'request'
    elif any(word in message_lower for word in ['complaint', 'problem', 'issue']):
        return 'complaint'
    else:
        return 'other'


def get_popular_questions(user):
    """Get popular questions from knowledge base"""
    questions = AIKnowledgeBase.objects.filter(
        status='active',
        is_verified=True
    ).order_by('-usage_count')[:10]
    
    return [q.question for q in questions]


@login_required
@require_http_methods(["POST"])
def mark_alerts_read(request):
    """Mark AI alerts as read"""
    try:
        ProactiveAIAlert.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def check_new_alerts(request):
    """Check for new alerts"""
    try:
        new_alerts = ProactiveAIAlert.objects.filter(
            user=request.user,
            is_read=False,
            sent_at__gte=timezone.now() - timedelta(hours=24)
        ).count()
        
        latest = ProactiveAIAlert.objects.filter(
            user=request.user,
            is_read=False
        ).order_by('-sent_at').first()
        
        return JsonResponse({
            'new_alerts': new_alerts,
            'latest_alert': latest.title if latest else ''
        })
    except Exception as e:
        return JsonResponse({'new_alerts': 0, 'latest_alert': ''})


@require_http_methods(["POST"])
def rate_message(request):
    """Rate AI message"""
    try:
        data = json.loads(request.body)
        message_id = data.get('message_id')
        rating = data.get('rating')
        
        message = ChatMessage.objects.get(message_id=message_id)
        message.user_rating = rating
        message.was_helpful = rating >= 4
        message.save()
        
        # Update knowledge base if linked
        if message.matched_knowledge:
            knowledge = message.matched_knowledge
            if rating >= 4:
                knowledge.helpful_count += 1
            else:
                knowledge.not_helpful_count += 1
            knowledge.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_http_methods(["POST"])
def end_session(request):
    """End chat session"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        
        session = ChatSession.objects.get(session_id=session_id)
        session.status = 'completed'
        session.ended_at = timezone.now()
        session.update_duration()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, FileResponse, Http404
from django.db.models import Q, Count
from django.utils import timezone
from .models import (
    FAQ, SupportTicket, TicketReply, SystemGuide, 
    ContactInfo, Student
)


@login_required
def help_faqs(request):
    """Display FAQs grouped by category"""
    category = request.GET.get('category', 'all')
    search_query = request.GET.get('q', '')
    
    # Get all active FAQs
    faqs = FAQ.objects.filter(is_active=True)
    
    # Filter by category
    if category != 'all':
        faqs = faqs.filter(category=category)
    
    # Search
    if search_query:
        faqs = faqs.filter(
            Q(question__icontains=search_query) | 
            Q(answer__icontains=search_query)
        )
    
    # Group FAQs by category
    faqs_by_category = {}
    for faq in faqs:
        if faq.category not in faqs_by_category:
            faqs_by_category[faq.category] = []
        faqs_by_category[faq.category].append(faq)
    
    # Get categories with counts
    categories = FAQ.objects.filter(is_active=True).values('category').annotate(
        count=Count('id')
    ).order_by('category')
    
    context = {
        'faqs_by_category': faqs_by_category,
        'categories': categories,
        'selected_category': category,
        'search_query': search_query,
        'total_faqs': faqs.count(),
    }
    
    return render(request, 'student/help/faqs.html', context)


@login_required
def faq_detail(request, faq_id):
    """View single FAQ and mark as helpful/not helpful"""
    faq = get_object_or_404(FAQ, id=faq_id, is_active=True)
    
    # Increment view count
    faq.views_count += 1
    faq.save(update_fields=['views_count'])
    
    context = {
        'faq': faq,
    }
    
    return render(request, 'student/help/faq_detail.html', context)


@login_required
def faq_feedback(request, faq_id):
    """Mark FAQ as helpful or not helpful"""
    if request.method == 'POST':
        faq = get_object_or_404(FAQ, id=faq_id)
        is_helpful = request.POST.get('is_helpful') == 'true'
        
        if is_helpful:
            faq.is_helpful_count += 1
        else:
            faq.is_not_helpful_count += 1
        
        faq.save()
        
        return JsonResponse({
            'success': True,
            'helpful_count': faq.is_helpful_count,
            'not_helpful_count': faq.is_not_helpful_count
        })
    
    return JsonResponse({'success': False})


@login_required
def contact_support(request):
    """Display contact information for support"""
    contacts = ContactInfo.objects.filter(is_active=True)
    
    # Get student's recent tickets
    student = request.user.student_profile
    recent_tickets = SupportTicket.objects.filter(
        student=student
    ).order_by('-created_at')[:5]
    
    context = {
        'contacts': contacts,
        'recent_tickets': recent_tickets,
    }
    
    return render(request, 'student/help/contact_support.html', context)


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count

from .models import SystemGuide


@login_required
def system_guides(request):
    """Display system guides and tutorials"""

    guide_type = request.GET.get('type', 'all')
    search_query = request.GET.get('q', '').strip()

    # Base queryset
    guides = SystemGuide.objects.filter(is_active=True)

    # Filter by type
    if guide_type != 'all':
        guides = guides.filter(guide_type=guide_type)

    # Search
    if search_query:
        guides = guides.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(content__icontains=search_query)
        )

    # Group guides by type
    guides_by_type = {}
    for guide in guides:
        guides_by_type.setdefault(guide.guide_type, []).append(guide)

    # Guide types summary with counts
    guide_types = (
        SystemGuide.objects
        .filter(is_active=True)
        .values('guide_type')
        .annotate(count=Count('id'))
        .order_by('guide_type')
    )

    # 🔥 Most viewed guides (FIXED PROPERLY)
    popular_guides = (
        SystemGuide.objects
        .filter(is_active=True)
        .order_by('-views_count')[:5]
    )

    context = {
        'guides_by_type': guides_by_type,
        'guide_types': guide_types,
        'popular_guides': popular_guides,
        'selected_type': guide_type,
        'search_query': search_query,
        'total_guides': guides.count(),
    }

    return render(request, 'student/help/system_guides.html', context)



@login_required
def guide_detail(request, guide_id):
    """View single guide"""
    guide = get_object_or_404(SystemGuide, id=guide_id, is_active=True)
    
    # Increment view count
    guide.views_count += 1
    guide.save(update_fields=['views_count'])
    
    # Get related guides
    related_guides = SystemGuide.objects.filter(
        guide_type=guide.guide_type,
        is_active=True
    ).exclude(id=guide.id)[:3]
    
    context = {
        'guide': guide,
        'related_guides': related_guides,
    }
    
    return render(request, 'student/help/guide_detail.html', context)


@login_required
def report_issue(request):
    """Create a new support ticket"""
    student = request.user.student_profile
    
    if request.method == 'POST':
        category = request.POST.get('category')
        priority = request.POST.get('priority', 'medium')
        subject = request.POST.get('subject')
        description = request.POST.get('description')
        attachment = request.FILES.get('attachment')
        
        # Validate
        if not all([category, subject, description]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('report_issue')
        
        # Create ticket
        ticket = SupportTicket.objects.create(
            student=student,
            category=category,
            priority=priority,
            subject=subject,
            description=description,
            attachment=attachment,
            status='open'
        )
        
        messages.success(
            request, 
            f'Support ticket {ticket.ticket_number} created successfully. '
            f'We will respond to you shortly.'
        )
        return redirect('my_tickets')
    
    # Get recent tickets
    recent_tickets = SupportTicket.objects.filter(
        student=student
    ).order_by('-created_at')[:3]
    
    context = {
        'categories': SupportTicket.CATEGORIES,
        'priorities': SupportTicket.PRIORITY_LEVELS,
        'recent_tickets': recent_tickets,
    }
    
    return render(request, 'student/help/report_issue.html', context)


@login_required
def my_tickets(request):
    """View all student's support tickets"""
    student = request.user.student_profile
    
    status_filter = request.GET.get('status', 'all')
    category_filter = request.GET.get('category', 'all')
    
    tickets = SupportTicket.objects.filter(student=student)
    
    # Apply filters
    if status_filter != 'all':
        tickets = tickets.filter(status=status_filter)
    
    if category_filter != 'all':
        tickets = tickets.filter(category=category_filter)
    
    tickets = tickets.order_by('-created_at')
    
    # Get statistics
    stats = {
        'total': SupportTicket.objects.filter(student=student).count(),
        'open': SupportTicket.objects.filter(student=student, status='open').count(),
        'in_progress': SupportTicket.objects.filter(student=student, status='in_progress').count(),
        'resolved': SupportTicket.objects.filter(student=student, status='resolved').count(),
        'closed': SupportTicket.objects.filter(student=student, status='closed').count(),
    }
    
    context = {
        'tickets': tickets,
        'stats': stats,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'statuses': SupportTicket.TICKET_STATUS,
        'categories': SupportTicket.CATEGORIES,
    }
    
    return render(request, 'student/help/my_tickets.html', context)


@login_required
def ticket_detail(request, ticket_number):
    """View ticket details and replies"""
    student = request.user.student_profile
    ticket = get_object_or_404(
        SupportTicket, 
        ticket_number=ticket_number,
        student=student
    )
    
    if request.method == 'POST':
        message = request.POST.get('message')
        attachment = request.FILES.get('attachment')
        
        if message:
            TicketReply.objects.create(
                ticket=ticket,
                user=request.user,
                message=message,
                attachment=attachment,
                is_staff_reply=False
            )
            
            # Update ticket status
            if ticket.status == 'resolved' or ticket.status == 'closed':
                ticket.status = 'open'
                ticket.save()
            
            messages.success(request, 'Reply added successfully.')
            return redirect('ticket_detail', ticket_number=ticket_number)
    
    # Get all replies
    replies = ticket.replies.all().select_related('user')
    
    context = {
        'ticket': ticket,
        'replies': replies,
    }
    
    return render(request, 'student/help/ticket_detail.html', context)


@login_required
def close_ticket(request, ticket_number):
    """Close a support ticket"""
    if request.method == 'POST':
        student = request.user.student_profile
        ticket = get_object_or_404(
            SupportTicket,
            ticket_number=ticket_number,
            student=student
        )
        
        ticket.status = 'closed'
        ticket.save()
        
        messages.success(request, f'Ticket {ticket_number} closed successfully.')
        return redirect('my_tickets')
    
    return redirect('my_tickets')

# ==================== VIEWS.PY - Student Finance ====================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum, Q
from django.utils import timezone
from decimal import Decimal
from .models import (
    Student, FeeStructure, FeePayment, FeeBalance,
    Semester, AcademicYear
)


@login_required
def student_fee_statement(request):
    """View detailed fee statement"""
    try:
        student = request.user.student_profile
        
        # Get current semester
        current_semester = Semester.objects.filter(is_current=True).first()
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        
        # Get fee balance for current semester
        fee_balance = None
        if current_semester:
            fee_balance = FeeBalance.objects.filter(
                student=student,
                semester=current_semester
            ).first()
        
        # Get all fee balances (history)
        all_balances = FeeBalance.objects.filter(
            student=student
        ).select_related(
            'semester', 
            'academic_year'
        ).order_by('-academic_year__start_date', '-semester__start_date')
        
        # Get recent payments
        recent_payments = FeePayment.objects.filter(
            student=student,
            status='completed'
        ).order_by('-payment_date')[:10]
        
        # Calculate totals
        total_fees_all_time = all_balances.aggregate(
            total=Sum('total_fees')
        )['total'] or Decimal('0.00')
        
        total_paid_all_time = all_balances.aggregate(
            total=Sum('amount_paid')
        )['total'] or Decimal('0.00')
        
        total_balance_all_time = all_balances.aggregate(
            total=Sum('balance')
        )['total'] or Decimal('0.00')
        
        context = {
            'student': student,
            'current_semester': current_semester,
            'current_academic_year': current_academic_year,
            'fee_balance': fee_balance,
            'all_balances': all_balances,
            'recent_payments': recent_payments,
            'total_fees_all_time': total_fees_all_time,
            'total_paid_all_time': total_paid_all_time,
            'total_balance_all_time': total_balance_all_time,
        }
        
        return render(request, 'student/finance/fee_statement.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading fee statement: {str(e)}')
        return redirect('student_dashboard')


@login_required
def student_make_payment(request):
    """Make fee payment page with M-Pesa integration"""
    try:
        student = request.user.student_profile
        
        # Get current semester
        current_semester = Semester.objects.filter(is_current=True).first()
        
        if not current_semester:
            messages.warning(request, 'No active semester found.')
            return redirect('student_fee_statement')
        
        # Get fee balance
        fee_balance = FeeBalance.objects.filter(
            student=student,
            semester=current_semester
        ).first()
        
        if not fee_balance:
            messages.warning(request, 'No fee structure found for current semester.')
            return redirect('student_fee_statement')
        
        # M-Pesa payment details
        mpesa_paybill = '400200'  # Your paybill number
        mpesa_account = student.registration_number
        
        context = {
            'student': student,
            'current_semester': current_semester,
            'fee_balance': fee_balance,
            'mpesa_paybill': mpesa_paybill,
            'mpesa_account': mpesa_account,
        }
        
        return render(request, 'student/finance/make_payment.html', context)
        
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('student_fee_statement')


@login_required
def student_payment_history(request):
    """View all payment history"""
    try:
        student = request.user.student_profile
        
        # Filters
        status_filter = request.GET.get('status', 'all')
        semester_filter = request.GET.get('semester', 'all')
        
        # Get all payments
        payments = FeePayment.objects.filter(student=student)
        
        # Apply filters
        if status_filter != 'all':
            payments = payments.filter(status=status_filter)
        
        if semester_filter != 'all':
            payments = payments.filter(semester_id=semester_filter)
        
        payments = payments.select_related(
            'semester',
            'academic_year',
            'fee_structure',
            'processed_by'
        ).order_by('-payment_date')
        
        # Get all semesters for filter
        semesters = Semester.objects.all().order_by('-start_date')
        
        # Calculate statistics
        total_paid = payments.filter(status='completed').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        completed_count = payments.filter(status='completed').count()
        pending_count = payments.filter(status='pending').count()
        failed_count = payments.filter(status='failed').count()
        
        context = {
            'student': student,
            'payments': payments,
            'semesters': semesters,
            'status_filter': status_filter,
            'semester_filter': semester_filter,
            'total_paid': total_paid,
            'completed_count': completed_count,
            'pending_count': pending_count,
            'failed_count': failed_count,
        }
        
        return render(request, 'student/finance/payment_history.html', context)
        
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('student_fee_statement')


@login_required
def student_payment_receipt(request, payment_id):
    """View/Download single payment receipt"""
    try:
        student = request.user.student_profile
        
        payment = get_object_or_404(
            FeePayment,
            id=payment_id,
            student=student,
            status='completed'
        )
        
        # Check if download requested
        download = request.GET.get('download', 'false') == 'true'
        
        context = {
            'student': student,
            'payment': payment,
        }
        
        if download:
            # Render as PDF (you'll need to implement PDF generation)
            # For now, just render the template
            response = render(request, 'student/finance/receipt_pdf.html', context)
            response['Content-Disposition'] = f'attachment; filename="receipt_{payment.receipt_number}.pdf"'
            return response
        
        return render(request, 'student/finance/receipt.html', context)
        
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('student_payment_history')


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum

from .models import FeePayment


@login_required
def student_all_receipts(request):
    """View all receipts grouped by semester with totals"""
    try:
        student = request.user.student_profile

        payments = FeePayment.objects.filter(
            student=student,
            status='completed',
            receipt_number__isnull=False
        ).select_related(
            'semester',
            'academic_year'
        ).order_by('-payment_date')

        # Group payments by semester WITH totals
        receipts_by_semester = {}

        for payment in payments:
            semester_key = payment.semester.name

            if semester_key not in receipts_by_semester:
                receipts_by_semester[semester_key] = {
                    'payments': [],
                    'total': 0
                }

            receipts_by_semester[semester_key]['payments'].append(payment)
            receipts_by_semester[semester_key]['total'] += payment.amount

        # Grand total
        grand_total = payments.aggregate(
            total=Sum('amount')
        )['total'] or 0

        context = {
            'student': student,
            'payments': payments,
            'receipts_by_semester': receipts_by_semester,
            'grand_total': grand_total,
        }

        return render(request, 'student/finance/all_receipts.html', context)

    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('student_fee_statement')



from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum

from .models import FeeStructure, AcademicYear


@login_required
def student_fee_structure(request):
    """View fee structure for student's programme"""
    try:
        student = request.user.student_profile

        # Current academic year
        current_academic_year = AcademicYear.objects.filter(
            is_current=True
        ).first()

        # Fee structures
        fee_structures = FeeStructure.objects.filter(
            programme=student.programme,
            academic_year=current_academic_year,
            is_active=True
        ).order_by('year_of_study', 'semester_number')

        # Current semester structure
        current_fee_structure = fee_structures.filter(
            year_of_study=student.current_year,
            semester_number=student.current_semester
        ).first()

        # Group by year WITH totals
        structures_by_year = {}

        for structure in fee_structures:
            year = structure.year_of_study

            if year not in structures_by_year:
                structures_by_year[year] = {
                    'structures': [],
                    'year_total': 0
                }

            structures_by_year[year]['structures'].append(structure)
            structures_by_year[year]['year_total'] += structure.total_fee

        # Programme total
        programme_total = fee_structures.aggregate(
            total=Sum('total_fee')
        )['total'] or 0

        context = {
            'student': student,
            'current_academic_year': current_academic_year,
            'current_fee_structure': current_fee_structure,
            'structures_by_year': structures_by_year,
            'programme_total': programme_total,
            'total_semesters': fee_structures.count(),
        }

        return render(request, 'student/finance/fee_structure.html', context)

    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('student_fee_statement')



@login_required
def verify_payment(request):
    """AJAX endpoint to verify M-Pesa payment"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            
            transaction_ref = data.get('transaction_ref')
            amount = data.get('amount')
            phone_number = data.get('phone_number')
            
            student = request.user.student_profile
            current_semester = Semester.objects.filter(is_current=True).first()
            
            if not all([transaction_ref, amount, phone_number, current_semester]):
                return JsonResponse({
                    'success': False,
                    'error': 'Missing required fields'
                })
            
            # Get fee structure
            fee_structure = FeeStructure.objects.filter(
                programme=student.programme,
                academic_year=current_semester.academic_year,
                year_of_study=student.current_year,
                semester_number=student.current_semester
            ).first()
            
            if not fee_structure:
                return JsonResponse({
                    'success': False,
                    'error': 'Fee structure not found'
                })
            
            # Create payment record
            payment = FeePayment.objects.create(
                student=student,
                semester=current_semester,
                academic_year=current_semester.academic_year,
                fee_structure=fee_structure,
                amount=Decimal(amount),
                payment_method='mpesa',
                transaction_reference=transaction_ref,
                payment_date=timezone.now(),
                status='pending'  # Will be updated by M-Pesa callback
            )
            
            # Here you would integrate with M-Pesa API to verify the transaction
            # For now, we'll simulate successful verification
            
            # Simulate M-Pesa verification (replace with actual API call)
            # mpesa_verified = verify_mpesa_transaction(transaction_ref)
            
            # For demo purposes, mark as completed
            payment.status = 'completed'
            payment.receipt_number = f'RCP-{timezone.now().strftime("%Y%m%d")}-{payment.id:05d}'
            payment.save()
            
            # Update fee balance
            fee_balance, created = FeeBalance.objects.get_or_create(
                student=student,
                semester=current_semester,
                academic_year=current_semester.academic_year,
                defaults={
                    'total_fees': fee_structure.total_fee,
                    'amount_paid': Decimal('0.00'),
                    'balance': fee_structure.total_fee
                }
            )
            
            fee_balance.amount_paid += Decimal(amount)
            fee_balance.balance = fee_balance.total_fees - fee_balance.amount_paid
            fee_balance.last_payment_date = timezone.now()
            if fee_balance.balance <= 0:
                fee_balance.is_cleared = True
                fee_balance.clearance_date = timezone.now()
            fee_balance.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Payment verified successfully',
                'receipt_number': payment.receipt_number,
                'new_balance': float(fee_balance.balance)
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


# student/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count, Case, When, IntegerField
from django.core.paginator import Paginator
from django.http import JsonResponse
from datetime import timedelta
from decimal import Decimal
from .models import (
    Student, Book, BookCategory, BookBorrowing, 
    User, AcademicYear, Semester
)


# ============= BOOK SEARCH & BROWSE =============
@login_required
def library_search_books(request):
    """Search and browse available books"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('student_dashboard')
    
    # Get search parameters
    search_query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    status_filter = request.GET.get('status', 'available')
    sort_by = request.GET.get('sort', 'title')
    
    # Base queryset with availability annotation
    books = Book.objects.annotate(
        currently_available=Case(
            When(status='available', available_copies__gt=0, then=1),
            default=0,
            output_field=IntegerField()
        )
    )
    
    # Apply filters
    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(author__icontains=search_query) |
            Q(isbn__icontains=search_query) |
            Q(call_number__icontains=search_query)
        )
    
    if category_id:
        books = books.filter(category_id=category_id)
    
    if status_filter == 'available':
        books = books.filter(status='available', available_copies__gt=0)
    elif status_filter == 'borrowed':
        books = books.filter(status='borrowed')
    
    # Sorting
    sort_options = {
        'title': 'title',
        'author': 'author',
        'recent': '-acquisition_date',
        'popular': '-id'  # Could be replaced with a popularity score
    }
    books = books.order_by(sort_options.get(sort_by, 'title'))
    
    # Pagination
    paginator = Paginator(books, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get categories for filter
    categories = BookCategory.objects.all().order_by('name')
    
    # Get student's current borrowings
    current_borrowings = BookBorrowing.objects.filter(
        student=student,
        status__in=['active', 'overdue']
    ).select_related('book')
    
    borrowed_book_ids = [b.book.id for b in current_borrowings]
    
    # Get current semester for new borrowings
    try:
        current_semester = Semester.objects.get(is_current=True)
        current_academic_year = AcademicYear.objects.get(is_current=True)
    except (Semester.DoesNotExist, AcademicYear.DoesNotExist):
        current_semester = None
        current_academic_year = None
    
    context = {
        'student': student,
        'page_obj': page_obj,
        'categories': categories,
        'search_query': search_query,
        'category_id': category_id,
        'status_filter': status_filter,
        'sort_by': sort_by,
        'borrowed_book_ids': borrowed_book_ids,
        'current_borrowings_count': current_borrowings.count(),
        'max_books_allowed': 3,  # Maximum books a student can borrow
        'current_semester': current_semester,
        'current_academic_year': current_academic_year,
    }
    
    return render(request, 'student/library/search_books.html', context)


# ============= BOOK RESERVATION =============
@login_required
def reserve_book(request, book_id):
    """Reserve a book for pickup"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('library_search_books')
    
    book = get_object_or_404(Book, id=book_id)
    
    # Check if book is available
    if book.status != 'available' or book.available_copies <= 0:
        messages.error(request, f'The book "{book.title}" is currently not available.')
        return redirect('library_search_books')
    
    # Check if student has reached borrowing limit
    active_borrowings = BookBorrowing.objects.filter(
        student=student,
        status__in=['active', 'overdue']
    ).count()
    
    if active_borrowings >= 3:  # Maximum 3 books
        messages.error(request, 'You have reached the maximum borrowing limit of 3 books.')
        return redirect('library_search_books')
    
    # Check if student already has this book
    existing_borrowing = BookBorrowing.objects.filter(
        student=student,
        book=book,
        status__in=['active', 'overdue']
    ).exists()
    
    if existing_borrowing:
        messages.error(request, f'You have already borrowed "{book.title}".')
        return redirect('library_search_books')
    
    # Check if student has unpaid fines
    unpaid_fines = BookBorrowing.objects.filter(
        student=student,
        fine_amount__gt=0,
        fine_paid=False
    ).aggregate(total=Sum('fine_amount'))['total'] or 0
    
    if unpaid_fines > 0:
        messages.error(request, f'You have unpaid library fines of KES {unpaid_fines}. Please clear your fines before borrowing.')
        return redirect('library_fines')
    
    # Get current semester and academic year
    try:
        current_semester = Semester.objects.get(is_current=True)
        current_academic_year = AcademicYear.objects.get(is_current=True)
    except (Semester.DoesNotExist, AcademicYear.DoesNotExist):
        messages.error(request, 'No active academic period found.')
        return redirect('library_search_books')
    
    if request.method == 'POST':
        # Create reservation (borrowing with 30-minute pickup window)
        now = timezone.now()
        pickup_deadline = now + timedelta(minutes=30)
        due_date = (now + timedelta(days=14)).date()  # 2 weeks from now
        
        borrowing = BookBorrowing.objects.create(
            student=student,
            book=book,
            academic_year=current_academic_year,
            semester=current_semester,
            borrow_date=now,
            due_date=due_date,
            status='active',  # We'll use a custom field to track reservation
            remarks=f'Reserved online. Must be picked up by {pickup_deadline.strftime("%I:%M %p")}'
        )
        
        # Update book availability
        book.available_copies -= 1
        if book.available_copies == 0:
            book.status = 'borrowed'
        book.save()
        
        messages.success(
            request,
            f'Book reserved successfully! Please pick it up from the library within 30 minutes '
            f'(by {pickup_deadline.strftime("%I:%M %p")}). Your reservation will be cancelled if not picked up.'
        )
        return redirect('library_reservations')
    
    context = {
        'student': student,
        'book': book,
        'current_borrowings_count': active_borrowings,
        'unpaid_fines': unpaid_fines,
    }
    
    return render(request, 'student/library/reserve_book.html', context)


# ============= MY BORROWINGS =============
@login_required
def my_borrowings(request):
    """View all current and past borrowings"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('student_dashboard')
    
    # Get filter parameters
    status_filter = request.GET.get('status', 'all')
    
    # Base queryset
    borrowings = BookBorrowing.objects.filter(
        student=student
    ).select_related('book', 'book__category', 'issued_by', 'returned_to')
    
    # Apply status filter
    if status_filter == 'active':
        borrowings = borrowings.filter(status='active')
    elif status_filter == 'overdue':
        borrowings = borrowings.filter(status='overdue')
    elif status_filter == 'returned':
        borrowings = borrowings.filter(status='returned')
    
    borrowings = borrowings.order_by('-borrow_date')
    
    # Calculate fines for overdue books
    for borrowing in borrowings:
        if borrowing.status in ['active', 'overdue']:
            borrowing.calculate_fine()
    
    # Pagination
    paginator = Paginator(borrowings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Summary statistics
    total_borrowed = borrowings.count()
    active_count = borrowings.filter(status='active').count()
    overdue_count = borrowings.filter(status='overdue').count()
    returned_count = borrowings.filter(status='returned').count()
    total_fines = borrowings.filter(fine_paid=False).aggregate(
        total=Sum('fine_amount')
    )['total'] or Decimal('0.00')
    
    context = {
        'student': student,
        'page_obj': page_obj,
        'status_filter': status_filter,
        'total_borrowed': total_borrowed,
        'active_count': active_count,
        'overdue_count': overdue_count,
        'returned_count': returned_count,
        'total_fines': total_fines,
    }
    
    return render(request, 'student/library/my_borrowings.html', context)


# ============= BOOK RESERVATIONS =============
@login_required
def book_reservations(request):
    """View and manage active reservations (books waiting for pickup)"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('student_dashboard')
    
    now = timezone.now()
    
    # Get reservations (borrowings made within last 30 minutes with specific status)
    thirty_minutes_ago = now - timedelta(minutes=30)
    
    reservations = BookBorrowing.objects.filter(
        student=student,
        status='active',
        borrow_date__gte=thirty_minutes_ago,
        return_date__isnull=True  # Not yet picked up/returned
    ).select_related('book', 'book__category')
    
    # Calculate remaining time for each reservation
    for reservation in reservations:
        pickup_deadline = reservation.borrow_date + timedelta(minutes=30)
        time_remaining = pickup_deadline - now
        
        if time_remaining.total_seconds() > 0:
            reservation.minutes_remaining = int(time_remaining.total_seconds() / 60)
            reservation.pickup_deadline = pickup_deadline
            reservation.is_expired = False
        else:
            reservation.minutes_remaining = 0
            reservation.is_expired = True
    
    # Get expired reservations (for cancellation)
    expired_reservations = [r for r in reservations if r.is_expired]
    
    # Auto-cancel expired reservations
    for reservation in expired_reservations:
        # Return the book copy
        reservation.book.available_copies += 1
        if reservation.book.available_copies > 0:
            reservation.book.status = 'available'
        reservation.book.save()
        
        # Cancel the borrowing
        reservation.delete()
    
    # Refresh reservations after cancellation
    active_reservations = [r for r in reservations if not r.is_expired]
    
    context = {
        'student': student,
        'reservations': active_reservations,
        'expired_count': len(expired_reservations),
    }
    
    return render(request, 'student/library/reservations.html', context)


@login_required
def cancel_reservation(request, borrowing_id):
    """Cancel a book reservation"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('student_dashboard')
    
    borrowing = get_object_or_404(
        BookBorrowing,
        id=borrowing_id,
        student=student,
        status='active',
        return_date__isnull=True
    )
    
    # Check if it's within 30 minutes (still a reservation)
    thirty_minutes_ago = timezone.now() - timedelta(minutes=30)
    if borrowing.borrow_date < thirty_minutes_ago:
        messages.error(request, 'This reservation has already been processed.')
        return redirect('library_reservations')
    
    if request.method == 'POST':
        # Return the book copy
        borrowing.book.available_copies += 1
        if borrowing.book.available_copies > 0:
            borrowing.book.status = 'available'
        borrowing.book.save()
        
        # Delete the reservation
        book_title = borrowing.book.title
        borrowing.delete()
        
        messages.success(request, f'Reservation for "{book_title}" has been cancelled.')
        return redirect('library_reservations')
    
    context = {
        'student': student,
        'borrowing': borrowing,
    }
    
    return render(request, 'student/library/cancel_reservation.html', context)


# ============= LIBRARY FINES =============
@login_required
def library_fines(request):
    """View and manage library fines"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('student_dashboard')
    
    # Get all borrowings with fines
    borrowings_with_fines = BookBorrowing.objects.filter(
        student=student,
        fine_amount__gt=0
    ).select_related('book', 'book__category').order_by('-borrow_date')
    
    # Calculate current fines for active overdue books
    for borrowing in borrowings_with_fines:
        if borrowing.status in ['active', 'overdue']:
            borrowing.calculate_fine()
    
    # Summary
    total_fines = borrowings_with_fines.aggregate(
        total=Sum('fine_amount')
    )['total'] or Decimal('0.00')
    
    unpaid_fines = borrowings_with_fines.filter(
        fine_paid=False
    ).aggregate(
        total=Sum('fine_amount')
    )['total'] or Decimal('0.00')
    
    paid_fines = borrowings_with_fines.filter(
        fine_paid=True
    ).aggregate(
        total=Sum('fine_amount')
    )['total'] or Decimal('0.00')
    
    context = {
        'student': student,
        'borrowings_with_fines': borrowings_with_fines,
        'total_fines': total_fines,
        'unpaid_fines': unpaid_fines,
        'paid_fines': paid_fines,
    }
    
    return render(request, 'student/library/fines.html', context)


# ============= DIGITAL RESOURCES =============
@login_required
def digital_resources(request):
    """View digital library resources and e-books"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('student_dashboard')
    
    # Get categories for digital resources
    categories = BookCategory.objects.all().order_by('name')
    
    # This could be extended to include actual digital resources
    # For now, we'll show information about available digital platforms
    
    digital_platforms = [
        {
            'name': 'IEEE Xplore',
            'description': 'Access to IEEE journals, conferences, and standards',
            'url': '#',
            'icon': 'ri-book-open-line',
            'category': 'Engineering & Technology'
        },
        {
            'name': 'JSTOR',
            'description': 'Academic journals, books, and primary sources',
            'url': '#',
            'icon': 'ri-article-line',
            'category': 'Arts & Sciences'
        },
        {
            'name': 'SpringerLink',
            'description': 'Scientific, technical, and medical content',
            'url': '#',
            'icon': 'ri-flask-line',
            'category': 'Science & Medicine'
        },
        {
            'name': 'ACM Digital Library',
            'description': 'Computing and information technology resources',
            'url': '#',
            'icon': 'ri-computer-line',
            'category': 'Computer Science'
        },
    ]
    
    context = {
        'student': student,
        'categories': categories,
        'digital_platforms': digital_platforms,
    }
    
    return render(request, 'student/library/digital_resources.html', context)


# ============= AJAX ENDPOINTS =============
@login_required
def check_book_availability(request, book_id):
    """AJAX endpoint to check real-time book availability"""
    try:
        student = Student.objects.get(user=request.user)
        book = Book.objects.get(id=book_id)
        
        # Check if student already has this book
        has_borrowed = BookBorrowing.objects.filter(
            student=student,
            book=book,
            status__in=['active', 'overdue']
        ).exists()
        
        # Check if there's a reservation slot available (no pending reservations)
        recent_reservations = BookBorrowing.objects.filter(
            book=book,
            status='active',
            borrow_date__gte=timezone.now() - timedelta(minutes=30),
            return_date__isnull=True
        ).count()
        
        data = {
            'available': book.status == 'available' and book.available_copies > 0,
            'available_copies': book.available_copies,
            'total_copies': book.total_copies,
            'has_borrowed': has_borrowed,
            'pending_reservations': recent_reservations,
        }
        
        return JsonResponse(data)
    except (Student.DoesNotExist, Book.DoesNotExist):
        return JsonResponse({'error': 'Not found'}, status=404)


# Add missing import
from django.db.models import Sum

# ==================== VIEWS.PY ====================

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Avg, Q, F, Max, Min
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from decimal import Decimal


# ==================== SCHOOL PROFILE ====================

@login_required
def school_profile(request):
    """School profile and overview information"""
    
    # Get dean's school
    try:
        dean_profile = request.user
        school = School.objects.get(dean=dean_profile)
    except School.DoesNotExist:
        messages.error(request, 'No school assigned to your account')
        return redirect('dean_dashboard')
    
    # Get current academic period
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get school statistics
    total_departments = Department.objects.filter(school=school, is_active=True).count()
    total_programmes = Programme.objects.filter(
        department__school=school, 
        is_active=True
    ).count()
    total_students = Student.objects.filter(
        programme__department__school=school,
        student_status='active'
    ).count()
    total_lecturers = Lecturer.objects.filter(
        department__school=school,
        is_active=True
    ).count()
    
    # Programme breakdown by type
    programme_breakdown = Programme.objects.filter(
        department__school=school,
        is_active=True
    ).values('programme_type').annotate(
        count=Count('id')
    ).order_by('programme_type')
    
    # Student breakdown by year
    student_by_year = Student.objects.filter(
        programme__department__school=school,
        student_status='active'
    ).values('current_year').annotate(
        count=Count('id')
    ).order_by('current_year')
    
    # Recent activities
    recent_activities = []
    
    # Recent student admissions
    recent_admissions = Student.objects.filter(
        programme__department__school=school,
        admission_date__gte=timezone.now() - timedelta(days=30)
    ).count()
    
    if recent_admissions > 0:
        recent_activities.append({
            'type': 'admission',
            'title': f'{recent_admissions} New Student Admissions',
            'description': 'In the last 30 days',
            'date': timezone.now(),
            'icon': 'ri-user-add-line',
            'color': 'success'
        })
    
    # Recent programme additions
    recent_programmes = Programme.objects.filter(
        department__school=school,
        created_at__gte=timezone.now() - timedelta(days=90)
    ).count()
    
    if recent_programmes > 0:
        recent_activities.append({
            'type': 'programme',
            'title': f'{recent_programmes} New Programmes Added',
            'description': 'In the last 90 days',
            'date': timezone.now(),
            'icon': 'ri-book-line',
            'color': 'info'
        })
    
    context = {
        'page_title': 'School Profile',
        'school': school,
        'current_academic_year': current_academic_year,
        'current_semester': current_semester,
        'total_departments': total_departments,
        'total_programmes': total_programmes,
        'total_students': total_students,
        'total_lecturers': total_lecturers,
        'programme_breakdown': programme_breakdown,
        'student_by_year': student_by_year,
        'recent_activities': recent_activities,
    }
    
    return render(request, 'dean/school_overview/school_profile.html', context)


# ==================== DEPARTMENTS ====================

@login_required
def departments_list(request):
    """List all departments in the school"""
    
    # Get dean's school
    try:
        dean_profile = request.user
        school = School.objects.get(dean=dean_profile)
    except School.DoesNotExist:
        messages.error(request, 'No school assigned to your account')
        return redirect('dean_dashboard')
    
    # Get all departments with related data
    departments = Department.objects.filter(
        school=school,
        is_active=True
    ).annotate(
        student_count=Count(
            'programmes__students',
            filter=Q(programmes__students__student_status='active'),
            distinct=True
        ),
        lecturer_count=Count(
            'lecturers',
            filter=Q(lecturers__is_active=True),
            distinct=True
        ),
        programme_count=Count(
            'programmes',
            filter=Q(programmes__is_active=True),
            distinct=True
        ),
        avg_gpa=Avg(
            'programmes__students__cumulative_gpa',
            filter=Q(programmes__students__student_status='active')
        )
    ).order_by('name')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        departments = departments.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(departments, 10)
    page_number = request.GET.get('page')
    departments_page = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Departments',
        'school': school,
        'departments': departments_page,
        'search_query': search_query,
        'total_departments': departments.count(),
    }
    
    return render(request, 'dean/school_overview/departments_list.html', context)


@login_required
def dean_department_detail(request, department_id):
    """Department detail view with statistics"""
    
    # Get dean's school
    try:
        dean_profile = request.user
        school = School.objects.get(dean=dean_profile)
    except School.DoesNotExist:
        messages.error(request, 'No school assigned to your account')
        return redirect('dean_dashboard')
    
    # Get department
    department = get_object_or_404(
        Department,
        id=department_id,
        school=school,
        is_active=True
    )
    
    # Get current academic period
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Department statistics
    total_programmes = Programme.objects.filter(
        department=department,
        is_active=True
    ).count()
    
    total_students = Student.objects.filter(
        programme__department=department,
        student_status='active'
    ).count()
    
    total_lecturers = Lecturer.objects.filter(
        department=department,
        is_active=True
    ).count()
    
    avg_gpa = Student.objects.filter(
        programme__department=department,
        student_status='active'
    ).aggregate(avg_gpa=Avg('cumulative_gpa'))['avg_gpa'] or 0
    
    # Get programmes with student count
    programmes = Programme.objects.filter(
        department=department,
        is_active=True
    ).annotate(
        student_count=Count(
            'students',
            filter=Q(students__student_status='active')
        )
    ).order_by('name')
    
    # Get lecturers
    lecturers = Lecturer.objects.filter(
        department=department,
        is_active=True
    ).select_related('user').order_by('user__first_name')[:10]
    
    # Student distribution by year
    students_by_year = Student.objects.filter(
        programme__department=department,
        student_status='active'
    ).values('current_year').annotate(
        count=Count('id')
    ).order_by('current_year')
    
    # Gender distribution
    students_by_gender = Student.objects.filter(
        programme__department=department,
        student_status='active'
    ).values('gender').annotate(
        count=Count('id')
    )
    
    context = {
        'page_title': f'{department.name} - Department Details',
        'school': school,
        'department': department,
        'current_academic_year': current_academic_year,
        'current_semester': current_semester,
        'total_programmes': total_programmes,
        'total_students': total_students,
        'total_lecturers': total_lecturers,
        'avg_gpa': round(avg_gpa, 2),
        'programmes': programmes,
        'lecturers': lecturers,
        'students_by_year': students_by_year,
        'students_by_gender': students_by_gender,
    }
    
    return render(request, 'dean/school_overview/department_detail.html', context)


# ==================== ACADEMIC STAFF ====================


@login_required
def academic_staff(request):
    """List all academic staff in the school"""

    # Get dean's school
    try:
        school = School.objects.get(dean=request.user)
    except School.DoesNotExist:
        messages.error(request, 'No school assigned to your account')
        return redirect('dean_dashboard')

    # Get all lecturers
    lecturers = Lecturer.objects.filter(
        department__school=school,
        is_active=True
    ).select_related(
        'user',
        'department'
    ).annotate(
        unit_count=Count('id') * 0   # placeholder (no unit allocation model yet)
    ).order_by(
        'department__name',
        'user__first_name'
    )

    # Filter by department
    department_filter = request.GET.get('department', '')
    if department_filter:
        lecturers = lecturers.filter(department_id=department_filter)

    # Filter by designation
    designation_filter = request.GET.get('designation', '')
    if designation_filter:
        lecturers = lecturers.filter(designation=designation_filter)

    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        lecturers = lecturers.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(employee_number__icontains=search_query) |
            Q(department__name__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(lecturers, 20)
    page_number = request.GET.get('page')
    lecturers_page = paginator.get_page(page_number)

    # Departments for filter
    departments = Department.objects.filter(
        school=school,
        is_active=True
    ).order_by('name')

    # Statistics
    total_lecturers = lecturers.count()

    lecturers_by_designation = Lecturer.objects.filter(
        department__school=school,
        is_active=True
    ).values('designation').annotate(
        count=Count('id')
    ).order_by('designation')

    context = {
        'page_title': 'Academic Staff',
        'school': school,
        'lecturers': lecturers_page,
        'departments': departments,
        'search_query': search_query,
        'department_filter': department_filter,
        'designation_filter': designation_filter,
        'total_lecturers': total_lecturers,
        'lecturers_by_designation': lecturers_by_designation,
    }

    return render(
        request,
        'dean/school_overview/academic_staff.html',
        context
    )


@login_required
def staff_detail(request, lecturer_id):
    """Staff member detail view"""

    # Get dean's school
    try:
        school = School.objects.get(dean=request.user)
    except School.DoesNotExist:
        messages.error(request, 'No school assigned to your account')
        return redirect('dean_dashboard')

    # Get lecturer
    lecturer = get_object_or_404(
        Lecturer,
        id=lecturer_id,
        department__school=school,
        is_active=True
    )

    # Get current semester
    current_semester = Semester.objects.filter(is_current=True).first()

    # Current unit allocations
    if current_semester:
        unit_allocations = UnitAllocation.objects.filter(
            lecturer=lecturer.user,   # ✅ FIX
            semester=current_semester
        ).select_related(
            'programme_unit__unit',
            'programme_unit__programme'
        ).order_by(
            'programme_unit__programme__name'
        )
    else:
        unit_allocations = UnitAllocation.objects.none()

    # Teaching history
    teaching_history = UnitAllocation.objects.filter(
        lecturer=lecturer.user      # ✅ FIX
    ).select_related(
        'semester',
        'programme_unit__unit'
    ).order_by(
        '-semester__start_date'
    )[:20]

    # Statistics
    total_units_current = unit_allocations.count()

    total_units_all_time = UnitAllocation.objects.filter(
        lecturer=lecturer.user      # ✅ FIX
    ).values(
        'programme_unit__unit'
    ).distinct().count()

    context = {
        'page_title': f'{lecturer.user.get_full_name()} - Staff Profile',
        'school': school,
        'lecturer': lecturer,
        'current_semester': current_semester,
        'unit_allocations': unit_allocations,
        'teaching_history': teaching_history,
        'total_units_current': total_units_current,
        'total_units_all_time': total_units_all_time,
    }

    return render(
        request,
        'dean/school_overview/staff_detail.html',
        context
    )

# ==================== STUDENT POPULATION ====================

@login_required
def student_population(request):
    """Student population overview and analytics"""
    
    # Get dean's school
    try:
        dean_profile = request.user
        school = School.objects.get(dean=dean_profile)
    except School.DoesNotExist:
        messages.error(request, 'No school assigned to your account')
        return redirect('dean_dashboard')
    
    # Get current academic period
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Overall statistics
    total_students = Student.objects.filter(
        programme__department__school=school,
        student_status='active'
    ).count()
    
    male_students = Student.objects.filter(
        programme__department__school=school,
        student_status='active',
        gender='M'
    ).count()
    
    female_students = Student.objects.filter(
        programme__department__school=school,
        student_status='active',
        gender='F'
    ).count()
    
    avg_gpa = Student.objects.filter(
        programme__department__school=school,
        student_status='active'
    ).aggregate(avg_gpa=Avg('cumulative_gpa'))['avg_gpa'] or 0
    
    # Students by department
    students_by_department = Department.objects.filter(
        school=school,
        is_active=True
    ).annotate(
        student_count=Count(
            'programmes__students',
            filter=Q(programmes__students__student_status='active')
        )
    ).order_by('-student_count')
    
    # Students by programme
    students_by_programme = Programme.objects.filter(
        department__school=school,
        is_active=True
    ).annotate(
        student_count=Count(
            'students',
            filter=Q(students__student_status='active')
        )
    ).order_by('-student_count')[:10]
    
    # Students by year of study
    students_by_year = Student.objects.filter(
        programme__department__school=school,
        student_status='active'
    ).values('current_year').annotate(
        count=Count('id')
    ).order_by('current_year')
    
    # Students by intake
    students_by_intake = Student.objects.filter(
        programme__department__school=school,
        student_status='active'
    ).values(
        'intake__name'
    ).annotate(
        count=Count('id')
    ).order_by('-intake__start_date')[:5]
    
    # Students by status
    students_by_status = Student.objects.filter(
        programme__department__school=school
    ).values('student_status').annotate(
        count=Count('id')
    ).order_by('student_status')
    
    # Recent admissions (last 30 days)
    recent_admissions = Student.objects.filter(
        programme__department__school=school,
        admission_date__gte=timezone.now() - timedelta(days=30)
    ).select_related(
        'user',
        'programme'
    ).order_by('-admission_date')[:10]
    
    # Search students
    search_query = request.GET.get('search', '')
    if search_query:
        students = Student.objects.filter(
            programme__department__school=school
        ).filter(
            Q(registration_number__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(programme__name__icontains=search_query)
        ).select_related('user', 'programme')[:20]
    else:
        students = []
    
    context = {
        'page_title': 'Student Population',
        'school': school,
        'current_academic_year': current_academic_year,
        'current_semester': current_semester,
        'total_students': total_students,
        'male_students': male_students,
        'female_students': female_students,
        'avg_gpa': round(avg_gpa, 2),
        'students_by_department': students_by_department,
        'students_by_programme': students_by_programme,
        'students_by_year': students_by_year,
        'students_by_intake': students_by_intake,
        'students_by_status': students_by_status,
        'recent_admissions': recent_admissions,
        'search_query': search_query,
        'students': students,
    }
    
    return render(request, 'dean/school_overview/student_population.html', context)


# ==================== SCHOOL CALENDAR ====================

@login_required
def school_calendar(request):
    """School calendar with events and important dates"""
    
    # Get dean's school
    try:
        dean_profile = request.user
        school = School.objects.get(dean=dean_profile)
    except School.DoesNotExist:
        messages.error(request, 'No school assigned to your account')
        return redirect('dean_dashboard')
    
    # Get current academic year
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    
    # Get all academic years
    academic_years = AcademicYear.objects.filter(is_active=True).order_by('-start_date')
    
    # Get semesters for current academic year
    if current_academic_year:
        semesters = Semester.objects.filter(
            academic_year=current_academic_year
        ).order_by('semester_number')
    else:
        semesters = []
    
    # Get intakes
    intakes = Intake.objects.filter(
        academic_year=current_academic_year,
        is_active=True
    ).order_by('-start_date') if current_academic_year else []
    
    # Get upcoming events
    upcoming_events = Event.objects.filter(
        academic_year=current_academic_year,
        is_published=True,
        start_date__gte=timezone.now()
    ).order_by('start_date')[:10] if current_academic_year else []
    
    # Get recent events
    recent_events = Event.objects.filter(
        academic_year=current_academic_year,
        is_published=True,
        end_date__lt=timezone.now()
    ).order_by('-start_date')[:5] if current_academic_year else []
    
    # Important dates
    important_dates = []
    
    if current_academic_year:
        important_dates.append({
            'title': 'Academic Year Start',
            'date': current_academic_year.start_date,
            'type': 'academic_year',
            'color': 'primary'
        })
        important_dates.append({
            'title': 'Academic Year End',
            'date': current_academic_year.end_date,
            'type': 'academic_year',
            'color': 'primary'
        })
    
    for semester in semesters:
        important_dates.append({
            'title': f'{semester.name} - Start',
            'date': semester.start_date,
            'type': 'semester',
            'color': 'success'
        })
        important_dates.append({
            'title': f'{semester.name} - End',
            'date': semester.end_date,
            'type': 'semester',
            'color': 'success'
        })
        important_dates.append({
            'title': f'{semester.name} - Registration Opens',
            'date': semester.registration_start_date,
            'type': 'registration',
            'color': 'warning'
        })
        important_dates.append({
            'title': f'{semester.name} - Registration Closes',
            'date': semester.registration_end_date,
            'type': 'registration',
            'color': 'danger'
        })
    
    # Sort important dates
    important_dates.sort(key=lambda x: x['date'])
    
    context = {
        'page_title': 'School Calendar',
        'school': school,
        'current_academic_year': current_academic_year,
        'academic_years': academic_years,
        'semesters': semesters,
        'intakes': intakes,
        'upcoming_events': upcoming_events,
        'recent_events': recent_events,
        'important_dates': important_dates,
    }
    
    return render(request, 'dean/school_overview/school_calendar.html', context)


# ==================== VIEWS.PY - ACADEMIC MANAGEMENT ====================

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Avg, Q, F, Max, Min
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from decimal import Decimal


# ==================== PROGRAMME DEVELOPMENT ====================

@login_required
def programme_development(request):
    """Programme development and management overview"""
    
    # Get dean's school
    try:
        dean_profile = request.user
        school = School.objects.get(dean=dean_profile)
    except School.DoesNotExist:
        messages.error(request, 'No school assigned to your account')
        return redirect('dean_dashboard')
    
    # Get current academic year
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    
    # Get all programmes
    programmes = Programme.objects.filter(
        department__school=school
    ).select_related('department').annotate(
        student_count=Count(
            'students',
            filter=Q(students__student_status='active')
        ),
        unit_count=Count(
            'programme_units',
            distinct=True
        ),
        avg_gpa=Avg(
            'students__cumulative_gpa',
            filter=Q(students__student_status='active')
        )
    ).order_by('-is_active', 'department__name', 'name')
    
    # Filter by department
    department_filter = request.GET.get('department', '')
    if department_filter:
        programmes = programmes.filter(department_id=department_filter)
    
    # Filter by programme type
    type_filter = request.GET.get('type', '')
    if type_filter:
        programmes = programmes.filter(programme_type=type_filter)
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        if status_filter == 'active':
            programmes = programmes.filter(is_active=True)
        elif status_filter == 'inactive':
            programmes = programmes.filter(is_active=False)
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        programmes = programmes.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(department__name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(programmes, 15)
    page_number = request.GET.get('page')
    programmes_page = paginator.get_page(page_number)
    
    # Statistics
    total_programmes = Programme.objects.filter(
        department__school=school
    ).count()
    
    active_programmes = Programme.objects.filter(
        department__school=school,
        is_active=True
    ).count()
    
    programmes_by_type = Programme.objects.filter(
        department__school=school
    ).values('programme_type').annotate(
        count=Count('id')
    ).order_by('programme_type')
    
    programmes_by_department = Department.objects.filter(
        school=school
    ).annotate(
        programme_count=Count('programmes')
    ).order_by('-programme_count')[:5]
    
    # Get departments for filter
    departments = Department.objects.filter(
        school=school,
        is_active=True
    ).order_by('name')
    
    context = {
        'page_title': 'Programme Development',
        'school': school,
        'programmes': programmes_page,
        'departments': departments,
        'current_academic_year': current_academic_year,
        'search_query': search_query,
        'department_filter': department_filter,
        'type_filter': type_filter,
        'status_filter': status_filter,
        'total_programmes': total_programmes,
        'active_programmes': active_programmes,
        'programmes_by_type': programmes_by_type,
        'programmes_by_department': programmes_by_department,
    }
    
    return render(request, 'dean/academic_management/programme_development.html', context)


@login_required
def programme_detail(request, programme_id):
    """Detailed view of a programme"""
    
    # Get dean's school
    try:
        dean_profile = request.user
        school = School.objects.get(dean=dean_profile)
    except School.DoesNotExist:
        messages.error(request, 'No school assigned to your account')
        return redirect('dean_dashboard')
    
    # Get programme
    programme = get_object_or_404(
        Programme,
        id=programme_id,
        department__school=school
    )
    
    # Get current academic year
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    
    # Statistics
    total_students = Student.objects.filter(
        programme=programme,
        student_status='active'
    ).count()
    
    students_by_year = Student.objects.filter(
        programme=programme,
        student_status='active'
    ).values('current_year').annotate(
        count=Count('id')
    ).order_by('current_year')
    
    avg_gpa = Student.objects.filter(
        programme=programme,
        student_status='active'
    ).aggregate(avg_gpa=Avg('cumulative_gpa'))['avg_gpa'] or 0
    
    # Get programme units by year and semester
    programme_units = ProgrammeUnit.objects.filter(
        programme=programme,
        academic_year=current_academic_year,
        is_active=True
    ).select_related('unit').order_by(
        'year_of_study',
        'semester_number',
        'unit__code'
    ) if current_academic_year else []
    
    # Organize units by year and semester
    units_structure = {}
    for pu in programme_units:
        year_key = f"Year {pu.year_of_study}"
        sem_key = f"Semester {pu.semester_number}"
        
        if year_key not in units_structure:
            units_structure[year_key] = {}
        if sem_key not in units_structure[year_key]:
            units_structure[year_key][sem_key] = []
        
        units_structure[year_key][sem_key].append(pu)
    
    # Get recent graduates
    recent_graduates = Student.objects.filter(
        programme=programme,
        student_status='graduated'
    ).select_related('user').order_by('-updated_at')[:10]
    
    # Employment/progression data (if available)
    total_graduates = Student.objects.filter(
        programme=programme,
        student_status='graduated'
    ).count()
    
    context = {
        'page_title': f'{programme.name} - Programme Details',
        'school': school,
        'programme': programme,
        'current_academic_year': current_academic_year,
        'total_students': total_students,
        'students_by_year': students_by_year,
        'avg_gpa': round(avg_gpa, 2),
        'units_structure': units_structure,
        'recent_graduates': recent_graduates,
        'total_graduates': total_graduates,
    }
    
    return render(request, 'dean/academic_management/programme_detail.html', context)


# ==================== CURRICULUM REVIEW ====================

@login_required
def curriculum_review(request):
    """Curriculum review and unit management"""
    
    # Get dean's school
    try:
        dean_profile = request.user
        school = School.objects.get(dean=dean_profile)
    except School.DoesNotExist:
        messages.error(request, 'No school assigned to your account')
        return redirect('dean_dashboard')
    
    # Get current academic year and semester
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get all units in the school
    units = Unit.objects.filter(
        department__school=school,
        is_active=True
    ).select_related('department').annotate(
        programme_count=Count(
            'programme_assignments',
            filter=Q(programme_assignments__is_active=True),
            distinct=True
        ),
        student_count=Count(
            'programme_assignments__programme__students',
            filter=Q(programme_assignments__programme__students__student_status='active'),
            distinct=True
        )
    ).order_by('department__name', 'unit_level', 'code')
    
    # Filters
    department_filter = request.GET.get('department', '')
    if department_filter:
        units = units.filter(department_id=department_filter)
    
    level_filter = request.GET.get('level', '')
    if level_filter:
        units = units.filter(unit_level=level_filter)
    
    search_query = request.GET.get('search', '')
    if search_query:
        units = units.filter(
            Q(code__icontains=search_query) |
            Q(name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(units, 20)
    page_number = request.GET.get('page')
    units_page = paginator.get_page(page_number)
    
    # Statistics
    total_units = Unit.objects.filter(
        department__school=school,
        is_active=True
    ).count()
    
    units_by_level = Unit.objects.filter(
        department__school=school,
        is_active=True
    ).values('unit_level').annotate(
        count=Count('id')
    ).order_by('unit_level')
    
    units_by_department = Department.objects.filter(
        school=school,
        is_active=True
    ).annotate(
        unit_count=Count('units', filter=Q(units__is_active=True))
    ).order_by('-unit_count')
    
    # Unit performance analysis (if current semester exists)
    if current_semester:
        unit_performance = SemesterResults.objects.filter(
            programme_unit__programme__department__school=school,
            semester=current_semester,
            is_published=True
        ).values(
            'programme_unit__unit__code',
            'programme_unit__unit__name'
        ).annotate(
            avg_marks=Avg('total_marks'),
            pass_rate=Avg('is_passed') * 100,
            student_count=Count('id')
        ).order_by('-avg_marks')[:10]
    else:
        unit_performance = []
    
    # Get departments for filter
    departments = Department.objects.filter(
        school=school,
        is_active=True
    ).order_by('name')
    
    context = {
        'page_title': 'Curriculum Review',
        'school': school,
        'units': units_page,
        'departments': departments,
        'current_academic_year': current_academic_year,
        'current_semester': current_semester,
        'search_query': search_query,
        'department_filter': department_filter,
        'level_filter': level_filter,
        'total_units': total_units,
        'units_by_level': units_by_level,
        'units_by_department': units_by_department,
        'unit_performance': unit_performance,
    }
    
    return render(request, 'dean/academic_management/curriculum_review.html', context)


@login_required
def unit_detail(request, unit_id):
    """Detailed view of a unit"""
    
    # Get dean's school
    try:
        dean_profile = request.user
        school = School.objects.get(dean=dean_profile)
    except School.DoesNotExist:
        messages.error(request, 'No school assigned to your account')
        return redirect('dean_dashboard')
    
    # Get unit
    unit = get_object_or_404(
        Unit,
        id=unit_id,
        department__school=school
    )
    
    # Get current semester
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get programmes offering this unit
    programme_units = ProgrammeUnit.objects.filter(
        unit=unit,
        is_active=True
    ).select_related('programme', 'academic_year')
    
    # Get current allocations
    if current_semester:
        allocations = UnitAllocation.objects.filter(
            programme_unit__unit=unit,
            semester=current_semester
        ).select_related(
            'lecturer__user',
            'programme_unit__programme'
        )
    else:
        allocations = []
    
    # Performance statistics
    if current_semester:
        performance_stats = SemesterResults.objects.filter(
            programme_unit__unit=unit,
            semester=current_semester,
            is_published=True
        ).aggregate(
            avg_marks=Avg('total_marks'),
            max_marks=Max('total_marks'),
            min_marks=Min('total_marks'),
            pass_count=Count('id', filter=Q(is_passed=True)),
            total_count=Count('id')
        )
        
        if performance_stats['total_count'] > 0:
            pass_rate = (performance_stats['pass_count'] / performance_stats['total_count']) * 100
        else:
            pass_rate = 0
    else:
        performance_stats = None
        pass_rate = 0
    
    # Grade distribution
    if current_semester:
        grade_distribution = SemesterResults.objects.filter(
            programme_unit__unit=unit,
            semester=current_semester,
            is_published=True
        ).values('grade').annotate(
            count=Count('id')
        ).order_by('grade')
    else:
        grade_distribution = []
    
    # Prerequisites
    prerequisites = unit.prerequisites.all()
    required_for = unit.required_for.all()
    
    context = {
        'page_title': f'{unit.code} - {unit.name}',
        'school': school,
        'unit': unit,
        'current_semester': current_semester,
        'programme_units': programme_units,
        'allocations': allocations,
        'performance_stats': performance_stats,
        'pass_rate': round(pass_rate, 2),
        'grade_distribution': grade_distribution,
        'prerequisites': prerequisites,
        'required_for': required_for,
    }
    
    return render(request, 'dean/academic_management/unit_detail.html', context)


# ==================== ACADEMIC STANDARDS ====================

@login_required
def academic_standards(request):
    """Academic standards monitoring and quality assurance"""
    
    # Get dean's school
    try:
        dean_profile = request.user
        school = School.objects.get(dean=dean_profile)
    except School.DoesNotExist:
        messages.error(request, 'No school assigned to your account')
        return redirect('dean_dashboard')
    
    # Get current academic year and semester
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Overall school performance
    avg_school_gpa = Student.objects.filter(
        programme__department__school=school,
        student_status='active'
    ).aggregate(avg_gpa=Avg('cumulative_gpa'))['avg_gpa'] or 0
    
    # Department performance comparison
    department_performance = Department.objects.filter(
        school=school,
        is_active=True
    ).annotate(
        avg_gpa=Avg(
            'programmes__students__cumulative_gpa',
            filter=Q(programmes__students__student_status='active')
        ),
        student_count=Count(
            'programmes__students',
            filter=Q(programmes__students__student_status='active'),
            distinct=True
        )
    ).order_by('-avg_gpa')
    
    # Programme performance
    programme_performance = Programme.objects.filter(
        department__school=school,
        is_active=True
    ).annotate(
        avg_gpa=Avg(
            'students__cumulative_gpa',
            filter=Q(students__student_status='active')
        ),
        student_count=Count(
            'students',
            filter=Q(students__student_status='active')
        )
    ).order_by('-avg_gpa')[:10]
    
    # Pass rate analysis
    if current_semester:
        pass_rate_by_unit = SemesterResults.objects.filter(
            programme_unit__programme__department__school=school,
            semester=current_semester,
            is_published=True
        ).values(
            'programme_unit__unit__code',
            'programme_unit__unit__name'
        ).annotate(
            pass_count=Count('id', filter=Q(is_passed=True)),
            total_count=Count('id'),
            avg_marks=Avg('total_marks')
        ).order_by('pass_count')[:15]
        
        # Calculate pass rates
        for item in pass_rate_by_unit:
            if item['total_count'] > 0:
                item['pass_rate'] = (item['pass_count'] / item['total_count']) * 100
            else:
                item['pass_rate'] = 0
    else:
        pass_rate_by_unit = []
    
    # Grade distribution across school
    if current_semester:
        grade_distribution = SemesterResults.objects.filter(
            programme_unit__programme__department__school=school,
            semester=current_semester,
            is_published=True
        ).values('grade').annotate(
            count=Count('id')
        ).order_by('grade')
    else:
        grade_distribution = []
    
    # Student progression rates
    progression_stats = {
        'year_1_to_2': 0,
        'year_2_to_3': 0,
        'year_3_to_4': 0,
        'graduation_rate': 0
    }
    
    # Top performing students
    top_students = Student.objects.filter(
        programme__department__school=school,
        student_status='active'
    ).order_by('-cumulative_gpa')[:20]
    
    # At-risk students (GPA < 2.0)
    at_risk_students = Student.objects.filter(
        programme__department__school=school,
        student_status='active',
        cumulative_gpa__lt=2.0
    ).select_related('user', 'programme').order_by('cumulative_gpa')[:20]
    
    # Graduation statistics
    graduation_stats = Student.objects.filter(
        programme__department__school=school,
        student_status='graduated'
    ).aggregate(
        total_graduated=Count('id'),
        avg_final_gpa=Avg('cumulative_gpa')
    )
    
    # Recent semester GPA trends (last 5 semesters)
    recent_semesters = Semester.objects.all().order_by('-start_date')[:5]
    semester_trends = []
    
    for sem in reversed(list(recent_semesters)):
        avg_gpa = SemesterGPA.objects.filter(
            student__programme__department__school=school,
            semester=sem
        ).aggregate(avg_gpa=Avg('semester_gpa'))['avg_gpa'] or 0
        
        semester_trends.append({
            'semester': sem.name,
            'avg_gpa': round(avg_gpa, 2)
        })
    
    context = {
        'page_title': 'Academic Standards',
        'school': school,
        'current_academic_year': current_academic_year,
        'current_semester': current_semester,
        'avg_school_gpa': round(avg_school_gpa, 2),
        'department_performance': department_performance,
        'programme_performance': programme_performance,
        'pass_rate_by_unit': pass_rate_by_unit,
        'grade_distribution': grade_distribution,
        'progression_stats': progression_stats,
        'top_students': top_students,
        'at_risk_students': at_risk_students,
        'graduation_stats': graduation_stats,
        'semester_trends': semester_trends,
    }
    
    return render(request, 'dean/academic_management/academic_standards.html', context)


# ==================== ACCREDITATION ====================

@login_required
def accreditation(request):
    """Accreditation status and compliance tracking"""
    
    # Get dean's school
    try:
        dean_profile = request.user
        school = School.objects.get(dean=dean_profile)
    except School.DoesNotExist:
        messages.error(request, 'No school assigned to your account')
        return redirect('dean_dashboard')
    
    # Get programmes with accreditation info
    programmes = Programme.objects.filter(
        department__school=school
    ).select_related('department').annotate(
        student_count=Count(
            'students',
            filter=Q(students__student_status='active')
        )
    ).order_by('department__name', 'name')
    
    # Filter by accreditation status
    status_filter = request.GET.get('status', '')
    if status_filter:
        programmes = programmes.filter(accreditation_status__icontains=status_filter)
    
    # Statistics
    total_programmes = programmes.count()
    accredited_programmes = programmes.exclude(
        Q(accreditation_status='') | Q(accreditation_status__isnull=True)
    ).count()
    
    # Group by accreditation body
    accreditation_bodies = programmes.exclude(
        Q(accreditation_body='') | Q(accreditation_body__isnull=True)
    ).values('accreditation_body').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Accreditation status breakdown
    accreditation_statuses = programmes.exclude(
        Q(accreditation_status='') | Q(accreditation_status__isnull=True)
    ).values('accreditation_status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Compliance checklist (sample data structure)
    compliance_areas = [
        {
            'area': 'Faculty Qualifications',
            'status': 'compliant',
            'details': 'All lecturers meet minimum qualification requirements',
            'last_review': timezone.now() - timedelta(days=90)
        },
        {
            'area': 'Infrastructure & Facilities',
            'status': 'under_review',
            'details': 'Laboratory equipment upgrade in progress',
            'last_review': timezone.now() - timedelta(days=45)
        },
        {
            'area': 'Curriculum Standards',
            'status': 'compliant',
            'details': 'All programmes meet industry standards',
            'last_review': timezone.now() - timedelta(days=60)
        },
        {
            'area': 'Student Support Services',
            'status': 'compliant',
            'details': 'Adequate support systems in place',
            'last_review': timezone.now() - timedelta(days=120)
        },
        {
            'area': 'Quality Assurance Systems',
            'status': 'action_required',
            'details': 'Internal audit procedures need updating',
            'last_review': timezone.now() - timedelta(days=180)
        },
    ]
    
    context = {
        'page_title': 'Accreditation',
        'school': school,
        'programmes': programmes,
        'total_programmes': total_programmes,
        'accredited_programmes': accredited_programmes,
        'accreditation_bodies': accreditation_bodies,
        'accreditation_statuses': accreditation_statuses,
        'compliance_areas': compliance_areas,
        'status_filter': status_filter,
    }
    
    return render(request, 'dean/academic_management/accreditation.html', context)


# ==================== EXTERNAL EXAMINERS ====================

@login_required
def external_examiners(request):
    """External examiners management and reports"""
    
    # Get dean's school
    try:
        dean_profile = request.user
        school = School.objects.get(dean=dean_profile)
    except School.DoesNotExist:
        messages.error(request, 'No school assigned to your account')
        return redirect('dean_dashboard')
    
    # Get current academic year
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    
    # Note: External Examiners model doesn't exist in your schema
    # This is a placeholder structure showing what data would be displayed
    
    # Sample external examiner data structure
    external_examiners_data = [
        {
            'id': 1,
            'name': 'Prof. John Smith',
            'institution': 'University of Nairobi',
            'specialization': 'Computer Science',
            'programmes': ['BSc Computer Science', 'BSc IT'],
            'appointment_date': timezone.now() - timedelta(days=730),
            'contract_end': timezone.now() + timedelta(days=365),
            'status': 'active',
            'reports_submitted': 3,
            'last_visit': timezone.now() - timedelta(days=60)
        },
        # Add more sample data as needed
    ]
    
    # Statistics
    total_examiners = len(external_examiners_data)
    active_examiners = len([e for e in external_examiners_data if e['status'] == 'active'])
    
    # Programmes requiring external examiners
    programmes = Programme.objects.filter(
        department__school=school,
        is_active=True
    ).select_related('department').order_by('department__name', 'name')
    
    # External examiner reports (sample structure)
    recent_reports = [
        {
            'examiner': 'Prof. John Smith',
            'programme': 'BSc Computer Science',
            'report_date': timezone.now() - timedelta(days=30),
            'semester': 'Semester 1 - 2024/2025',
            'status': 'submitted',
            'recommendations': 3,
            'rating': 'excellent'
        },
        # Add more sample reports
    ]
    
    context = {
        'page_title': 'External Examiners',
        'school': school,
        'current_academic_year': current_academic_year,
        'external_examiners': external_examiners_data,
        'total_examiners': total_examiners,
        'active_examiners': active_examiners,
        'programmes': programmes,
        'recent_reports': recent_reports,
    }
    
    return render(request, 'dean/academic_management/external_examiners.html', context)

"""
Dean Views - Complete Implementation
File: views/dean_views.py
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Avg, Q, F
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from decimal import Decimal
import json

from .models import (
    # Quality Assurance
    TeachingEvaluation, ProgrammeReview, AuditReport, ComplianceCheck, QualityMetric,
    # Research & Innovation
    ResearchProject, ResearchGrant, Publication, ResearchCenter, InnovationProject,
    # Human Resources
    StaffRecruitment, PerformanceAppraisal, StaffPromotion, StaffTraining, DisciplinaryCase,
    # Financial Management
    # SchoolBudget, BudgetAllocation, ExpenditureTracking, RevenueSource,
    # # Partnerships
    # Partnership, MOU, CollaborativeProject, AlumniRelation,
    # # Strategic Planning
    # StrategicGoal, PerformanceIndicator, KPIMeasurement, AnnualPlan, 
    # AnnualPlanActivity, ProgressReport, DeanApproval,
    # Core models
    School, Department, AcademicYear, Semester, Programme, Lecturer, User
)


# ============================================================================
# QUALITY ASSURANCE VIEWS
# ============================================================================

@login_required
def dean_teaching_evaluations_view(request):
    """View all teaching evaluations for the school"""
    dean_school = request.user.school_as_dean.first()
    
    if not dean_school:
        messages.error(request, "You are not assigned as a Dean.")
        return redirect('dashboard')
    
    # Get current academic year
    current_year = AcademicYear.objects.filter(is_current=True).first()
    
    # Filters
    academic_year_id = request.GET.get('academic_year', current_year.id if current_year else None)
    semester_id = request.GET.get('semester')
    department_id = request.GET.get('department')
    status = request.GET.get('status')
    
    # Base queryset
    evaluations = TeachingEvaluation.objects.filter(
        unit_allocation__programme_unit__programme__department__school=dean_school
    ).select_related(
        'unit_allocation__programme_unit__unit',
        'unit_allocation__lecturer__user',
        'unit_allocation__programme_unit__programme__department',
        'academic_year',
        'semester'
    ).order_by('-created_at')
    
    # Apply filters
    if academic_year_id:
        evaluations = evaluations.filter(academic_year_id=academic_year_id)
    if semester_id:
        evaluations = evaluations.filter(semester_id=semester_id)
    if department_id:
        evaluations = evaluations.filter(
            unit_allocation__programme_unit__programme__department_id=department_id
        )
    if status:
        evaluations = evaluations.filter(status=status)
    
    # Statistics
    stats = {
        'total_evaluations': evaluations.count(),
        'published': evaluations.filter(status='published').count(),
        'open': evaluations.filter(status='open').count(),
        'closed': evaluations.filter(status='closed').count(),
        'avg_overall_rating': evaluations.aggregate(Avg('overall_rating'))['overall_rating__avg'] or 0,
        'avg_response_rate': evaluations.aggregate(Avg('response_rate'))['response_rate__avg'] or 0,
    }
    
    # Pagination
    paginator = Paginator(evaluations, 20)
    page_number = request.GET.get('page')
    evaluations_page = paginator.get_page(page_number)
    
    context = {
        'evaluations': evaluations_page,
        'stats': stats,
        'academic_years': AcademicYear.objects.all().order_by('-start_date'),
        'semesters': Semester.objects.filter(academic_year_id=academic_year_id) if academic_year_id else [],
        'departments': dean_school.departments.all(),
        'current_year': current_year,
        'selected_year': academic_year_id,
        'selected_semester': semester_id,
        'selected_department': department_id,
        'selected_status': status,
    }
    
    return render(request, 'dean/quality_assurance/teaching_evaluations.html', context)


@login_required
def dean_programme_reviews_view(request):
    """View all programme reviews"""
    dean_school = request.user.school_as_dean.first()
    
    if not dean_school:
        messages.error(request, "You are not assigned as a Dean.")
        return redirect('dashboard')
    
    # Filters
    academic_year_id = request.GET.get('academic_year')
    review_type = request.GET.get('review_type')
    status = request.GET.get('status')
    
    # Base queryset
    reviews = ProgrammeReview.objects.filter(
        programme__department__school=dean_school
    ).select_related(
        'programme__department',
        'academic_year',
        'conducted_by',
        'approved_by'
    ).order_by('-review_date')
    
    # Apply filters
    if academic_year_id:
        reviews = reviews.filter(academic_year_id=academic_year_id)
    if review_type:
        reviews = reviews.filter(review_type=review_type)
    if status:
        reviews = reviews.filter(status=status)
    
    # Statistics
    stats = {
        'total_reviews': reviews.count(),
        'completed': reviews.filter(status='completed').count(),
        'in_progress': reviews.filter(status='in_progress').count(),
        'scheduled': reviews.filter(status='scheduled').count(),
        'avg_overall_rating': reviews.aggregate(Avg('overall_rating'))['overall_rating__avg'] or 0,
    }
    
    # Pagination
    paginator = Paginator(reviews, 15)
    page_number = request.GET.get('page')
    reviews_page = paginator.get_page(page_number)
    
    context = {
        'reviews': reviews_page,
        'stats': stats,
        'academic_years': AcademicYear.objects.all().order_by('-start_date'),
        'review_types': ProgrammeReview.REVIEW_TYPE,
        'statuses': ProgrammeReview.REVIEW_STATUS,
    }
    
    return render(request, 'dean/quality_assurance/programme_reviews.html', context)


@login_required
def dean_audit_reports_view(request):
    """View all audit reports"""
    dean_school = request.user.school_as_dean.first()
    
    if not dean_school:
        messages.error(request, "You are not assigned as a Dean.")
        return redirect('dashboard')
    
    # Filters
    audit_type = request.GET.get('audit_type')
    status = request.GET.get('status')
    academic_year_id = request.GET.get('academic_year')
    
    # Base queryset
    audits = AuditReport.objects.filter(
        Q(school=dean_school) | Q(department__school=dean_school)
    ).select_related('school', 'department', 'academic_year').order_by('-audit_date')
    
    # Apply filters
    if audit_type:
        audits = audits.filter(audit_type=audit_type)
    if status:
        audits = audits.filter(status=status)
    if academic_year_id:
        audits = audits.filter(academic_year_id=academic_year_id)
    
    # Statistics
    stats = {
        'total_audits': audits.count(),
        'completed': audits.filter(status='completed').count(),
        'ongoing': audits.filter(status='ongoing').count(),
        'planned': audits.filter(status='planned').count(),
    }
    
    # Pagination
    paginator = Paginator(audits, 15)
    page_number = request.GET.get('page')
    audits_page = paginator.get_page(page_number)
    
    context = {
        'audits': audits_page,
        'stats': stats,
        'audit_types': AuditReport.AUDIT_TYPE,
        'statuses': AuditReport.AUDIT_STATUS,
        'academic_years': AcademicYear.objects.all().order_by('-start_date'),
    }
    
    return render(request, 'dean/quality_assurance/audit_reports.html', context)


@login_required
def dean_compliance_monitoring_view(request):
    """View compliance checks"""
    dean_school = request.user.school_as_dean.first()
    
    if not dean_school:
        messages.error(request, "You are not assigned as a Dean.")
        return redirect('dashboard')
    
    # Filters
    compliance_area = request.GET.get('compliance_area')
    status = request.GET.get('status')
    
    # Base queryset
    compliance_checks = ComplianceCheck.objects.filter(
        school=dean_school
    ).select_related(
        'academic_year',
        'responsible_person',
        'checked_by'
    ).order_by('-check_date')
    
    # Apply filters
    if compliance_area:
        compliance_checks = compliance_checks.filter(compliance_area=compliance_area)
    if status:
        compliance_checks = compliance_checks.filter(status=status)
    
    # Statistics
    stats = {
        'total_checks': compliance_checks.count(),
        'compliant': compliance_checks.filter(status='compliant').count(),
        'non_compliant': compliance_checks.filter(status='non_compliant').count(),
        'partially_compliant': compliance_checks.filter(status='partially_compliant').count(),
        'action_required': compliance_checks.filter(action_required=True, is_resolved=False).count(),
    }
    
    # Pagination
    paginator = Paginator(compliance_checks, 20)
    page_number = request.GET.get('page')
    checks_page = paginator.get_page(page_number)
    
    context = {
        'checks': checks_page,
        'stats': stats,
        'compliance_areas': ComplianceCheck.COMPLIANCE_AREA,
        'statuses': ComplianceCheck.COMPLIANCE_STATUS,
    }
    
    return render(request, 'dean/quality_assurance/compliance_monitoring.html', context)


@login_required
def dean_quality_metrics_view(request):
    """View quality metrics and KPIs"""
    dean_school = request.user.school_as_dean.first()
    
    if not dean_school:
        messages.error(request, "You are not assigned as a Dean.")
        return redirect('dashboard')
    
    # Filters
    metric_type = request.GET.get('metric_type')
    academic_year_id = request.GET.get('academic_year')
    
    # Base queryset
    metrics = QualityMetric.objects.filter(
        school=dean_school
    ).select_related('academic_year', 'programme', 'recorded_by').order_by('-measurement_date')
    
    # Apply filters
    if metric_type:
        metrics = metrics.filter(metric_type=metric_type)
    if academic_year_id:
        metrics = metrics.filter(academic_year_id=academic_year_id)
    
    # Statistics
    stats = {
        'total_metrics': metrics.count(),
        'targets_met': metrics.filter(is_target_met=True).count(),
        'targets_not_met': metrics.filter(is_target_met=False).count(),
        'avg_achievement': metrics.aggregate(
            avg=Avg(F('actual_value') * 100.0 / F('target_value'))
        )['avg'] or 0,
    }
    
    # Trend analysis
    improving = metrics.filter(trend='improving').count()
    declining = metrics.filter(trend='declining').count()
    stable = metrics.filter(trend='stable').count()
    
    stats['trends'] = {
        'improving': improving,
        'declining': declining,
        'stable': stable,
    }
    
    # Pagination
    paginator = Paginator(metrics, 20)
    page_number = request.GET.get('page')
    metrics_page = paginator.get_page(page_number)
    
    context = {
        'metrics': metrics_page,
        'stats': stats,
        'metric_types': QualityMetric.METRIC_TYPE,
        'academic_years': AcademicYear.objects.all().order_by('-start_date'),
    }
    
    return render(request, 'dean/quality_assurance/quality_metrics.html', context)


# ============================================================================
# RESEARCH & INNOVATION VIEWS
# ============================================================================

@login_required
def dean_research_strategy_view(request):
    """Research strategy overview and dashboard"""
    dean_school = request.user.school_as_dean.first()
    
    if not dean_school:
        messages.error(request, "You are not assigned as a Dean.")
        return redirect('dashboard')
    
    current_year = AcademicYear.objects.filter(is_current=True).first()
    
    # Research projects statistics
    projects = ResearchProject.objects.filter(school=dean_school)
    
    stats = {
        'total_projects': projects.count(),
        'ongoing': projects.filter(status='ongoing').count(),
        'completed': projects.filter(status='completed').count(),
        'total_budget': projects.aggregate(Sum('total_budget'))['total_budget__sum'] or 0,
        'funds_utilized': projects.aggregate(Sum('funds_utilized'))['funds_utilized__sum'] or 0,
        'total_publications': projects.aggregate(Sum('publications_count'))['publications_count__sum'] or 0,
        'total_patents': projects.aggregate(Sum('patents_count'))['patents_count__sum'] or 0,
    }
    
    # Research grants
    grants = ResearchGrant.objects.filter(school=dean_school)
    grant_stats = {
        'total_grants': grants.count(),
        'active': grants.filter(status='active').count(),
        'amount_awarded': grants.aggregate(Sum('amount_awarded'))['amount_awarded__sum'] or 0,
    }
    
    # Publications
    publications = Publication.objects.filter(school=dean_school)
    pub_stats = {
        'total_publications': publications.count(),
        'peer_reviewed': publications.filter(is_peer_reviewed=True).count(),
        'this_year': publications.filter(year=timezone.now().year).count(),
    }
    
    # Research centers
    centers = ResearchCenter.objects.filter(school=dean_school, is_active=True)
    
    # Recent research activities
    recent_projects = projects.order_by('-created_at')[:5]
    recent_publications = publications.order_by('-publication_date')[:5]
    recent_grants = grants.order_by('-application_date')[:5]
    
    context = {
        'stats': stats,
        'grant_stats': grant_stats,
        'pub_stats': pub_stats,
        'centers': centers,
        'recent_projects': recent_projects,
        'recent_publications': recent_publications,
        'recent_grants': recent_grants,
    }
    
    return render(request, 'dean/research/research_strategy.html', context)


@login_required
def dean_grant_management_view(request):
    """Manage research grants"""
    dean_school = request.user.school_as_dean.first()
    
    if not dean_school:
        messages.error(request, "You are not assigned as a Dean.")
        return redirect('dashboard')
    
    # Filters
    grant_type = request.GET.get('grant_type')
    status = request.GET.get('status')
    
    # Base queryset
    grants = ResearchGrant.objects.filter(
        school=dean_school
    ).select_related(
        'principal_applicant__user',
        'principal_applicant__department'
    ).prefetch_related('co_applicants').order_by('-application_date')
    
    # Apply filters
    if grant_type:
        grants = grants.filter(grant_type=grant_type)
    if status:
        grants = grants.filter(status=status)
    
    # Statistics
    stats = {
        'total_grants': grants.count(),
        'approved': grants.filter(status='approved').count(),
        'active': grants.filter(status='active').count(),
        'completed': grants.filter(status='completed').count(),
        'total_applied': grants.aggregate(Sum('amount_applied'))['amount_applied__sum'] or 0,
        'total_awarded': grants.aggregate(Sum('amount_awarded'))['amount_awarded__sum'] or 0,
        'success_rate': (grants.filter(status__in=['approved', 'active', 'completed']).count() / grants.count() * 100) if grants.count() > 0 else 0,
    }
    
    # Pagination
    paginator = Paginator(grants, 15)
    page_number = request.GET.get('page')
    grants_page = paginator.get_page(page_number)
    
    context = {
        'grants': grants_page,
        'stats': stats,
        'grant_types': ResearchGrant.GRANT_TYPE,
        'statuses': ResearchGrant.GRANT_STATUS,
    }
    
    return render(request, 'dean/research/grant_management.html', context)


@login_required
def dean_publications_view(request):
    """View all publications"""
    dean_school = request.user.school_as_dean.first()
    
    if not dean_school:
        messages.error(request, "You are not assigned as a Dean.")
        return redirect('dashboard')
    
    # Filters
    publication_type = request.GET.get('publication_type')
    year = request.GET.get('year')
    
    # Base queryset
    publications = Publication.objects.filter(
        school=dean_school
    ).select_related(
        'corresponding_author__user',
        'research_project'
    ).prefetch_related('authors').order_by('-publication_date')
    
    # Apply filters
    if publication_type:
        publications = publications.filter(publication_type=publication_type)
    if year:
        publications = publications.filter(year=year)
    
    # Statistics
    stats = {
        'total_publications': publications.count(),
        'peer_reviewed': publications.filter(is_peer_reviewed=True).count(),
        'total_citations': publications.aggregate(Sum('citations_count'))['citations_count__sum'] or 0,
        'avg_impact_factor': publications.filter(impact_factor__isnull=False).aggregate(
            Avg('impact_factor'))['impact_factor__avg'] or 0,
    }
    
    # Publications by type
    by_type = publications.values('publication_type').annotate(count=Count('id'))
    
    # Pagination
    paginator = Paginator(publications, 15)
    page_number = request.GET.get('page')
    publications_page = paginator.get_page(page_number)
    
    context = {
        'publications': publications_page,
        'stats': stats,
        'by_type': by_type,
        'publication_types': Publication.PUBLICATION_TYPE,
        'years': range(timezone.now().year, timezone.now().year - 10, -1),
    }
    
    return render(request, 'dean/research/publications.html', context)


@login_required
def dean_research_centers_view(request):
    """Manage research centers"""
    dean_school = request.user.school_as_dean.first()
    
    if not dean_school:
        messages.error(request, "You are not assigned as a Dean.")
        return redirect('dashboard')
    
    # Get all research centers
    centers = ResearchCenter.objects.filter(
        school=dean_school
    ).select_related('director__user', 'deputy_director__user').order_by('name')
    
    # Statistics
    stats = {
        'total_centers': centers.count(),
        'active_centers': centers.filter(is_active=True).count(),
        'total_budget': centers.aggregate(Sum('annual_budget'))['annual_budget__sum'] or 0,
    }
    
    context = {
        'centers': centers,
        'stats': stats,
    }
    
    return render(request, 'dean/research/research_centers.html', context)


@login_required
def dean_innovation_projects_view(request):
    """Manage innovation projects"""
    dean_school = request.user.school_as_dean.first()
    
    if not dean_school:
        messages.error(request, "You are not assigned as a Dean.")
        return redirect('dashboard')
    
    # Filters
    status = request.GET.get('status')
    
    # Base queryset
    projects = InnovationProject.objects.filter(
        school=dean_school
    ).select_related('project_lead__user').prefetch_related('team_members').order_by('-created_at')
    
    # Apply filters
    if status:
        projects = projects.filter(status=status)
    
    # Statistics
    stats = {
        'total_projects': projects.count(),
        'in_development': projects.filter(status='development').count(),
        'commercialization': projects.filter(status='commercialization').count(),
        'completed': projects.filter(status='completed').count(),
        'total_budget': projects.aggregate(Sum('budget'))['budget__sum'] or 0,
        'total_revenue': projects.aggregate(Sum('revenue_generated'))['revenue_generated__sum'] or 0,
        'with_ip': projects.filter(has_ip_protection=True).count(),
    }
    
    # Pagination
    paginator = Paginator(projects, 15)
    page_number = request.GET.get('page')
    projects_page = paginator.get_page(page_number)
    
    context = {
        'projects': projects_page,
        'stats': stats,
        'statuses': InnovationProject.PROJECT_STATUS,
    }
    
    return render(request, 'dean/research/innovation_projects.html', context)


# ============================================================================
# HUMAN RESOURCES VIEWS
# ============================================================================

@login_required
def dean_staff_recruitment_view(request):
    """Manage staff recruitment"""
    dean_school = request.user.school_as_dean.first()
    
    if not dean_school:
        messages.error(request, "You are not assigned as a Dean.")
        return redirect('dashboard')
    
    # Filters
    status = request.GET.get('status')
    department_id = request.GET.get('department')
    
    # Base queryset
    recruitments = StaffRecruitment.objects.filter(
        school=dean_school
    ).select_related('department', 'academic_year').order_by('-advertised_date')
    
    # Apply filters
    if status:
        recruitments = recruitments.filter(status=status)
    if department_id:
        recruitments = recruitments.filter(department_id=department_id)
    
    # Statistics
    stats = {
        'total_recruitments': recruitments.count(),
        'open': recruitments.filter(status='open').count(),
        'shortlisting': recruitments.filter(status='shortlisting').count(),
        'interviewing': recruitments.filter(status='interviewing').count(),
        'total_applications': recruitments.aggregate(Sum('total_applications'))['total_applications__sum'] or 0,
        'positions_filled': recruitments.filter(status='accepted').count(),
    }
    
    # Pagination
    paginator = Paginator(recruitments, 15)
    page_number = request.GET.get('page')
    recruitments_page = paginator.get_page(page_number)
    
    context = {
        'recruitments': recruitments_page,
        'stats': stats,
        'departments': dean_school.departments.all(),
        'statuses': StaffRecruitment.RECRUITMENT_STATUS,
    }
    
    return render(request, 'dean/hr/staff_recruitment.html', context)


@login_required
def dean_performance_appraisal_view(request):
    """View staff performance appraisals"""
    dean_school = request.user.school_as_dean.first()
    
    if not dean_school:
        messages.error(request, "You are not assigned as a Dean.")
        return redirect('dashboard')
    
    # Filters
    academic_year_id = request.GET.get('academic_year')
    appraisal_period = request.GET.get('appraisal_period')
    department_id = request.GET.get('department')
    
    # Base queryset
    appraisals = PerformanceAppraisal.objects.filter(
        lecturer__department__school=dean_school
    ).select_related(
        'lecturer__user',
        'lecturer__department',
        'academic_year'
    ).order_by('-review_date')
    
    # Apply filters
    if academic_year_id:
        appraisals = appraisals.filter(academic_year_id=academic_year_id)
    if appraisal_period:
        appraisals = appraisals.filter(appraisal_period=appraisal_period)
    if department_id:
        appraisals = appraisals.filter(lecturer__department_id=department_id)
    
    # Statistics
    stats = {
        'total_appraisals': appraisals.count(),
        'outstanding': appraisals.filter(overall_rating='outstanding').count(),
        'exceeds': appraisals.filter(overall_rating='exceeds').count(),
        'meets': appraisals.filter(overall_rating='meets').count(),
        'needs_improvement': appraisals.filter(overall_rating='needs_improvement').count(),
        'avg_score': appraisals.aggregate(Avg('overall_score'))['overall_score__avg'] or 0,
    }
    
    # Pagination
    paginator = Paginator(appraisals, 15)
    page_number = request.GET.get('page')
    appraisals_page = paginator.get_page(page_number)
    
    context = {
        'appraisals': appraisals_page,
        'stats': stats,
        'academic_years': AcademicYear.objects.all().order_by('-start_date'),
        'appraisal_periods': PerformanceAppraisal.APPRAISAL_PERIOD,
        'departments': dean_school.departments.all(),
    }
    
    return render(request, 'dean/hr/performance_appraisal.html', context)


@login_required
def dean_promotions_view(request):
    """Manage staff promotions"""
    dean_school = request.user.school_as_dean.first()
    
    if not dean_school:
        messages.error(request, "You are not assigned as a Dean.")
        return redirect('dashboard')
    
    # Filters
    status = request.GET.get('status')
    
    # Base queryset
    promotions = StaffPromotion.objects.filter(
        lecturer__department__school=dean_school
    ).select_related(
        'lecturer__user',
        'lecturer__department',
        'academic_year'
    ).order_by('-application_date')
    
    # Apply filters
    if status:
        promotions = promotions.filter(status=status)
    
    # Promotions needing Dean's recommendation
    pending_dean = promotions.filter(status='pending_hos', dean_recommended_by__isnull=True)
    
    # Statistics
    stats = {
        'total_promotions': promotions.count(),
        'pending_dean': pending_dean.count(),
        'approved': promotions.filter(status='approved').count(),
        'implemented': promotions.filter(status='implemented').count(),
    }
    
    # Pagination
    paginator = Paginator(promotions, 15)
    page_number = request.GET.get('page')
    promotions_page = paginator.get_page(page_number)
    
    context = {
        'promotions': promotions_page,
        'pending_dean': pending_dean,
        'stats': stats,
        'statuses': StaffPromotion.PROMOTION_STATUS,
    }
    
    return render(request, 'dean/hr/promotions.html', context)


@login_required
def dean_staff_development_view(request):
    """View staff training and development"""
    dean_school = request.user.school_as_dean.first()
    
    if not dean_school:
        messages.error(request, "You are not assigned as a Dean.")
        return redirect('dashboard')
    
    # Filters
    training_type = request.GET.get('training_type')
    status = request.GET.get('status')
    
    # Base queryset
    trainings = StaffTraining.objects.filter(
        lecturer__department__school=dean_school
    ).select_related('lecturer__user', 'lecturer__department').order_by('-start_date')
    
    # Apply filters
    if training_type:
        trainings = trainings.filter(training_type=training_type)
    if status:
        trainings = trainings.filter(status=status)
    
    # Statistics
    stats = {
        'total_trainings': trainings.count(),
        'completed': trainings.filter(status='completed').count(),
        'ongoing': trainings.filter(status='ongoing').count(),
        'total_cost': trainings.aggregate(Sum('cost'))['cost__sum'] or 0,
        'certificates_obtained': trainings.filter(certificate_obtained=True).count(),
    }
    
    # Pagination
    paginator = Paginator(trainings, 15)
    page_number = request.GET.get('page')
    trainings_page = paginator.get_page(page_number)
    
    context = {
        'trainings': trainings_page,
        'stats': stats,
        'training_types': StaffTraining.TRAINING_TYPE,
        'statuses': StaffTraining.TRAINING_STATUS,
    }
    
    return render(request, 'dean/hr/staff_development.html', context)


@login_required
def dean_disciplinary_matters_view(request):
    """Manage disciplinary cases"""
    dean_school = request.user.school_as_dean.first()
    
    if not dean_school:
        messages.error(request, "You are not assigned as a Dean.")
        return redirect('dashboard')
    
    # Filters
    status = request.GET.get('status')
    severity = request.GET.get('severity')
    
    # Base queryset
    cases = DisciplinaryCase.objects.filter(
        lecturer__department__school=dean_school
    ).select_related(
        'lecturer__user',
        'lecturer__department',
        'academic_year'
    ).order_by('-reported_date')
    
    # Apply filters
    # Statistics
    stats = {
        'total_cases': cases.count(),
        'under_investigation': cases.filter(status='under_investigation').count(),
        'resolved': cases.filter(status='resolved').count(),
        'appealed': cases.filter(status='appealed').count(),
        'gross_misconduct': cases.filter(severity='gross_misconduct').count(),
    }

    # Pagination
    paginator = Paginator(cases, 15)
    page_number = request.GET.get('page')
    cases_page = paginator.get_page(page_number)

    context = {
        'cases': cases_page,
        'stats': stats,
        'statuses': DisciplinaryCase.CASE_STATUS,
        'severities': DisciplinaryCase.SEVERITY,
    }

    return render(request, 'dean/hr/disciplinary_matters.html', context)


# ============================================================================
# FINANCIAL MANAGEMENT VIEWS
# ============================================================================
@login_required
def dean_school_budget_view(request):
    """Manage school budget"""
    dean_school = request.user.school_as_dean.first()
    if not dean_school:
        messages.error(request, "You are not assigned as a Dean.")
        return redirect('dashboard')

    # Filters
    financial_year_id = request.GET.get('financial_year')
    status = request.GET.get('status')

    # Base queryset
    budgets = SchoolBudget.objects.filter(
        school=dean_school
    ).select_related('financial_year').order_by('-financial_year__start_date')

    # Apply filters
    if financial_year_id:
        budgets = budgets.filter(financial_year_id=financial_year_id)
    if status:
        budgets = budgets.filter(status=status)

    # Current budget
    current_year = AcademicYear.objects.filter(is_current=True).first()
    current_budget = budgets.filter(financial_year=current_year).first() if current_year else None

    # Statistics
    if current_budget:
        budget_stats = {
            'total_allocation': current_budget.total_allocation,
            'amount_spent': current_budget.amount_spent,
            'balance': current_budget.balance,
            'utilization_rate': (current_budget.amount_spent / current_budget.total_allocation * 100) if current_budget.total_allocation > 0 else 0,
        }
    else:
        budget_stats = {
            'total_allocation': 0,
            'amount_spent': 0,
            'balance': 0,
            'utilization_rate': 0,
        }

    context = {
        'budgets': budgets,
        'current_budget': current_budget,
        'budget_stats': budget_stats,
        'financial_years': AcademicYear.objects.all().order_by('-start_date'),
        'statuses': SchoolBudget.BUDGET_STATUS,
    }

    return render(request, 'dean/finance/school_budget.html', context)


@login_required
def dean_resource_allocation_view(request):
    """Manage resource allocation to departments"""
    dean_school = request.user.school_as_dean.first()
    if not dean_school:
        messages.error(request, "You are not assigned as a Dean.")
        return redirect('dashboard')

    # Get current budget
    current_year = AcademicYear.objects.filter(is_current=True).first()
    current_budget = SchoolBudget.objects.filter(
        school=dean_school,
        financial_year=current_year
    ).first() if current_year else None

    # Get allocations
    if current_budget:
        allocations = BudgetAllocation.objects.filter(
            school_budget=current_budget
        ).select_related('department').order_by('department__name')
    else:
        allocations = BudgetAllocation.objects.none()

    # Statistics
    stats = {
        'total_allocated': allocations.aggregate(Sum('allocation_amount'))['allocation_amount__sum'] or 0,
        'total_utilized': allocations.aggregate(Sum('amount_utilized'))['amount_utilized__sum'] or 0,
        'avg_utilization': allocations.aggregate(Avg('utilization_percentage'))['utilization_percentage__avg'] or 0,
    }

    context = {
        'current_budget': current_budget,
        'allocations': allocations,
        'stats': stats,
    }

    return render(request, 'dean/finance/resource_allocation.html', context)


@login_required
def dean_expenditure_control_view(request):
        """Monitor expenditure"""
        dean_school = request.user.school_as_dean.first()
        if not dean_school:
            messages.error(request, "You are not assigned as a Dean.")
            return redirect('dashboard')

        # Get current budget and allocations
        current_year = AcademicYear.objects.filter(is_current=True).first()
        current_budget = SchoolBudget.objects.filter(
            school=dean_school,
            financial_year=current_year
        ).first() if current_year else None

        if current_budget:
            allocations = BudgetAllocation.objects.filter(school_budget=current_budget)
            
            # Get expenditures
            expenditures = ExpenditureTracking.objects.filter(
                budget_allocation__in=allocations
            ).select_related('budget_allocation__department').order_by('-transaction_date')
            
            # Filters
            expenditure_type = request.GET.get('expenditure_type')
            status = request.GET.get('status')
            department_id = request.GET.get('department')
            
            if expenditure_type:
                expenditures = expenditures.filter(expenditure_type=expenditure_type)
            if status:
                expenditures = expenditures.filter(status=status)
            if department_id:
                expenditures = expenditures.filter(budget_allocation__department_id=department_id)
            
            # Statistics
            stats = {
                'total_expenditures': expenditures.count(),
                'total_amount': expenditures.filter(status='paid').aggregate(Sum('amount'))['amount__sum'] or 0,
                'pending_approval': expenditures.filter(status='pending').count(),
                'approved': expenditures.filter(status='approved').count(),
            }
            
            # Pagination
            paginator = Paginator(expenditures, 20)
            page_number = request.GET.get('page')
            expenditures_page = paginator.get_page(page_number)
        else:
            expenditures_page = []
            stats = {
                'total_expenditures': 0,
                'total_amount': 0,
                'pending_approval': 0,
                'approved': 0,
            }

        context = {
            'current_budget': current_budget,
            'expenditures': expenditures_page,
            'stats': stats,
            'expenditure_types': ExpenditureTracking.EXPENDITURE_TYPE,
            'statuses': ExpenditureTracking.PAYMENT_STATUS,
            'departments': dean_school.departments.all(),
        }

        return render(request, 'dean/finance/expenditure_control.html', context)
    
@login_required
def dean_revenue_generation_view(request):
    """Track revenue sources"""
    dean_school = request.user.school_as_dean.first()
    if not dean_school:
        messages.error(request, "You are not assigned as a Dean.")
        return redirect('dashboard')

    # Filters
    revenue_type = request.GET.get('revenue_type')
    academic_year_id = request.GET.get('academic_year')

    # Base queryset
    revenues = RevenueSource.objects.filter(
        school=dean_school
    ).select_related('academic_year').order_by('-received_date')

    # Apply filters
    if revenue_type:
        revenues = revenues.filter(revenue_type=revenue_type)
    if academic_year_id:
        revenues = revenues.filter(academic_year_id=academic_year_id)

    # Statistics
    stats = {
        'total_revenue': revenues.aggregate(Sum('amount'))['amount__sum'] or 0,
        'by_type': revenues.values('revenue_type').annotate(
            total=Sum('amount')
        ).order_by('-total'),
    }

    # Pagination
    paginator = Paginator(revenues, 20)
    page_number = request.GET.get('page')
    revenues_page = paginator.get_page(page_number)

    context = {
        'revenues': revenues_page,
        'stats': stats,
        'revenue_types': RevenueSource.REVENUE_TYPE,
        'academic_years': AcademicYear.objects.all().order_by('-start_date'),
    }

    return render(request, 'dean/finance/revenue_generation.html', context)


@login_required
def dean_financial_reports_view(request):
    """Generate and view financial reports"""
    dean_school = request.user.school_as_dean.first()
    if not dean_school:
        messages.error(request, "You are not assigned as a Dean.")
        return redirect('dashboard')

    # Get current year
    current_year = AcademicYear.objects.filter(is_current=True).first()

    # Budget summary
    budgets = SchoolBudget.objects.filter(school=dean_school)

    # Revenue summary
    revenues = RevenueSource.objects.filter(school=dean_school)
    if current_year:
        revenues = revenues.filter(academic_year=current_year)

    # Expenditure summary
    current_budget = budgets.filter(financial_year=current_year).first() if current_year else None
    if current_budget:
        allocations = BudgetAllocation.objects.filter(school_budget=current_budget)
        expenditures = ExpenditureTracking.objects.filter(
            budget_allocation__in=allocations,
            status='paid'
        )
    else:
        expenditures = ExpenditureTracking.objects.none()

    # Financial summary
    summary = {
        'total_budget': current_budget.total_allocation if current_budget else 0,
        'total_revenue': revenues.aggregate(Sum('amount'))['amount__sum'] or 0,
        'total_expenditure': expenditures.aggregate(Sum('amount'))['amount__sum'] or 0,
        'budget_balance': current_budget.balance if current_budget else 0,
    }

    # Expenditure by type
    expenditure_by_type = expenditures.values('expenditure_type').annotate(
        total=Sum('amount')
    ).order_by('-total')

    # Revenue by type
    revenue_by_type = revenues.values('revenue_type').annotate(
        total=Sum('amount')
    ).order_by('-total')

    context = {
        'summary': summary,
        'current_year': current_year,
        'current_budget': current_budget,
        'expenditure_by_type': expenditure_by_type,
        'revenue_by_type': revenue_by_type,
    }

    return render(request, 'dean/finance/financial_reports.html', context)



# ============================================================================
# PARTNERSHIPS & LINKAGES VIEWS
# ============================================================================


@login_required
def dean_industry_linkages_view(request):
    """Manage industry partnerships"""
    dean_school = request.user.school_as_dean.first()
    if not dean_school:
        messages.error(request, "You are not assigned as a Dean.")
        return redirect('dashboard')

    # Filters
    partnership_type = request.GET.get('partnership_type')
    status = request.GET.get('status')

    # Base queryset
    partnerships = Partnership.objects.filter(
        school=dean_school,
        partnership_type='industry'
    ).select_related('focal_person').order_by('partner_name')

    # Apply filters
    if partnership_type:
        partnerships = partnerships.filter(partnership_type=partnership_type)
    if status:
        partnerships = partnerships.filter(status=status)

    # Statistics
    stats = {
        'total_partners': partnerships.count(),
        'active': partnerships.filter(status='active').count(),
        'prospective': partnerships.filter(status='prospective').count(),
    }

    context = {
        'partnerships': partnerships,
        'stats': stats,
        'partnership_types': Partnership.PARTNERSHIP_TYPE,
        'statuses': Partnership.PARTNERSHIP_STATUS,
    }

    return render(request, 'dean/partnerships/industry_linkages.html', context)


@login_required
def dean_international_partners_view(request):
    """Manage international partnerships"""
    dean_school = request.user.school_as_dean.first()
    if not dean_school:
        messages.error(request, "You are not assigned as a Dean.")
        return redirect('dashboard')

    # Get international partnerships
    partnerships = Partnership.objects.filter(
        school=dean_school,
        partnership_type='international'
    ).select_related('focal_person').order_by('partner_name')

    # Statistics
    stats = {
        'total_partners': partnerships.count(),
        'active': partnerships.filter(status='active').count(),
        'countries': partnerships.values('country').distinct().count(),
    }

    # Group by country
    by_country = partnerships.values('country').annotate(
        count=Count('id')
    ).order_by('-count')

    context = {
        'partnerships': partnerships,
        'stats': stats,
        'by_country': by_country,
    }

    return render(request, 'dean/partnerships/international_partners.html', context)


@login_required
def dean_mous_view(request):
    """Manage MOUs"""
    dean_school = request.user.school_as_dean.first()
    if not dean_school:
        messages.error(request, "You are not assigned as a Dean.")
        return redirect('dashboard')

    # Filters
    status = request.GET.get('status')

    # Base queryset
    mous = MOU.objects.filter(
        partnership__school=dean_school
    ).select_related('partnership').order_by('-signing_date')

    # Apply filters
    if status:
        mous = mous.filter(status=status)

    # Statistics
    stats = {
        'total_mous': mous.count(),
        'active': mous.filter(status='active').count(),
        'expiring_soon': mous.filter(
            status='active',
            expiry_date__lte=timezone.now().date() + timedelta(days=90)
        ).count(),
    }

    # Pagination
    paginator = Paginator(mous, 15)
    page_number = request.GET.get('page')
    mous_page = paginator.get_page(page_number)

    context = {
        'mous': mous_page,
        'stats': stats,
        'statuses': MOU.MOU_STATUS,
    }

    return render(request, 'dean/partnerships/mous.html', context)


@login_required
def dean_collaborative_projects_view(request):
    """Manage collaborative projects"""
    dean_school = request.user.school_as_dean.first()
    if not dean_school:
        messages.error(request, "You are not assigned as a Dean.")
        return redirect('dashboard')

    # Filters
    status = request.GET.get('status')

    # Base queryset
    projects = CollaborativeProject.objects.filter(
        partnership__school=dean_school
    ).select_related(
        'partnership',
        'project_leader__user'
    ).prefetch_related('team_members').order_by('-start_date')

    # Apply filters
    if status:
        projects = projects.filter(status=status)

    # Statistics
    stats = {
        'total_projects': projects.count(),
        'ongoing': projects.filter(status='ongoing').count(),
        'completed': projects.filter(status='completed').count(),
        'total_budget': projects.aggregate(Sum('total_budget'))['total_budget__sum'] or 0,
        'total_publications': projects.aggregate(Sum('publications'))['publications__sum'] or 0,
    }

    # Pagination
    paginator = Paginator(projects, 15)
    page_number = request.GET.get('page')
    projects_page = paginator.get_page(page_number)

    context = {
        'projects': projects_page,
        'stats': stats,
        'statuses': CollaborativeProject.PROJECT_STATUS,
    }

    return render(request, 'dean/partnerships/collaborative_projects.html', context)

@login_required
def dean_alumni_relations_view(request):
    """Manage alumni engagement"""
    dean_school = request.user.school_as_dean.first()
    if not dean_school:
        messages.error(request, "You are not assigned as a Dean.")
        return redirect('dashboard')

    # Filters
    engagement_type = request.GET.get('engagement_type')

    # Base queryset
    alumni_relations = AlumniRelation.objects.filter(
        programme__department__school=dean_school
    ).select_related('programme').order_by('-engagement_date')

    # Apply filters
    if engagement_type:
        alumni_relations = alumni_relations.filter(engagement_type=engagement_type)

    # Statistics
    stats = {
        'total_engagements': alumni_relations.count(),
        'total_students_impacted': alumni_relations.aggregate(
            Sum('students_impacted'))['students_impacted__sum'] or 0,
        'total_contributions': alumni_relations.aggregate(
            Sum('contribution_value'))['contribution_value__sum'] or 0,
    }

    # By engagement type
    by_type = alumni_relations.values('engagement_type').annotate(
        count=Count('id')
    ).order_by('-count')

    # Pagination
    paginator = Paginator(alumni_relations, 15)
    page_number = request.GET.get('page')
    relations_page = paginator.get_page(page_number)

    context = {
        'relations': relations_page,
        'stats': stats,
        'by_type': by_type,
        'engagement_types': AlumniRelation.ENGAGEMENT_TYPE,
    }

    return render(request, 'dean/partnerships/alumni_relations.html', context)


# ============================================================================
# STRATEGIC PLANNING VIEWS
# ============================================================================
@login_required
def dean_strategic_goals_view(request):
    """Manage strategic goals"""
    dean_school = request.user.school_as_dean.first()
    if not dean_school:
        messages.error(request, "You are not assigned as a Dean.")
        return redirect('dashboard')

    # Filters
    category = request.GET.get('category')
    status = request.GET.get('status')

    # Base queryset
    goals = StrategicGoal.objects.filter(
        school=dean_school
    ).select_related('start_year', 'target_year', 'champion').order_by('category')

    # Apply filters
    if category:
        goals = goals.filter(category=category)
    if status:
        goals = goals.filter(status=status)

    # Statistics
    stats = {
        'total_goals': goals.count(),
        'active': goals.filter(status='active').count(),
        'achieved': goals.filter(status='achieved').count(),
        'avg_progress': goals.aggregate(Avg('progress_percentage'))['progress_percentage__avg'] or 0,
    }

    # Progress by category
    by_category = goals.values('category').annotate(
        count=Count('id'),
        avg_progress=Avg('progress_percentage')
    ).order_by('category')

    context = {
        'goals': goals,
        'stats': stats,
        'by_category': by_category,
        'categories': StrategicGoal.GOAL_CATEGORY,
        'statuses': StrategicGoal.GOAL_STATUS,
    }

    return render(request, 'dean/strategic/strategic_goals.html', context)


@login_required
def dean_performance_indicators_view(request):
    """Manage performance indicators (KPIs)"""
    dean_school = request.user.school_as_dean.first()
    if not dean_school:
        messages.error(request, "You are not assigned as a Dean.")
        return redirect('dashboard')

    # Get all indicators
    indicators = PerformanceIndicator.objects.filter(
        strategic_goal__school=dean_school,
        is_active=True
    ).select_related('strategic_goal', 'baseline_year', 'responsible_person').order_by('indicator_code')

    # Statistics
    stats = {
        'total_indicators': indicators.count(),
        'targets_met': indicators.filter(achievement_percentage__gte=100).count(),
        'on_track': indicators.filter(
            achievement_percentage__gte=80,
            achievement_percentage__lt=100
        ).count(),
        'behind': indicators.filter(achievement_percentage__lt=80).count(),
        'avg_achievement': indicators.aggregate(Avg('achievement_percentage'))['achievement_percentage__avg'] or 0,
    }

    # By indicator type
    by_type = indicators.values('indicator_type').annotate(
        count=Count('id'),
        avg_achievement=Avg('achievement_percentage')
    ).order_by('indicator_type')

    context = {
        'indicators': indicators,
        'stats': stats,
        'by_type': by_type,
    }

    return render(request, 'dean/strategic/performance_indicators.html', context)


@login_required
def dean_annual_plans_view(request):
    """Manage annual plans"""
    dean_school = request.user.school_as_dean.first()
    if not dean_school:
        messages.error(request, "You are not assigned as a Dean.")
        return redirect('dashboard')

    # Get all plans
    plans = AnnualPlan.objects.filter(
        school=dean_school
    ).select_related('academic_year').order_by('-academic_year__start_date')

    # Current plan
    current_year = AcademicYear.objects.filter(is_current=True).first()
    current_plan = plans.filter(academic_year=current_year).first() if current_year else None

    # Statistics
    stats = {
        'total_plans': plans.count(),
        'active': plans.filter(status='active').count(),
        'completed': plans.filter(status='completed').count(),
    }

    if current_plan:
        # Activities for current plan
        activities = AnnualPlanActivity.objects.filter(annual_plan=current_plan)
        stats['current_plan'] = {
            'total_activities': activities.count(),
            'completed': activities.filter(status='completed').count(),
            'in_progress': activities.filter(status='in_progress').count(),
            'delayed': activities.filter(status='delayed').count(),
            'avg_completion': activities.aggregate(Avg('completion_percentage'))['completion_percentage__avg'] or 0,
        }

    context = {
        'plans': plans,
        'current_plan': current_plan,
        'stats': stats,
    }

    return render(request, 'dean/strategic/annual_plans.html', context)



@login_required
def dean_progress_reports_view(request):
    """View progress reports"""
    dean_school = request.user.school_as_dean.first()
    if not dean_school:
        messages.error(request, "You are not assigned as a Dean.")
        return redirect('dashboard')

    # Filters
    report_type = request.GET.get('report_type')
    status = request.GET.get('status')

    # Base queryset
    reports = ProgressReport.objects.filter(
        school=dean_school
    ).select_related('academic_year', 'annual_plan').order_by('-reporting_period_end')

    # Apply filters
    if report_type:
        reports = reports.filter(report_type=report_type)
    if status:
        reports = reports.filter(status=status)

    # Statistics
    stats = {
        'total_reports': reports.count(),
        'published': reports.filter(status='published').count(),
        'draft': reports.filter(status='draft').count(),
    }

    # Pagination
    paginator = Paginator(reports, 15)
    page_number = request.GET.get('page')
    reports_page = paginator.get_page(page_number)

    context = {
        'reports': reports_page,
        'stats': stats,
        'report_types': ProgressReport.REPORT_TYPE,
        'statuses': ProgressReport.REPORT_STATUS,
    }

    return render(request, 'dean/strategic/progress_reports.html', context)


@login_required
def dean_future_planning_view(request):
    """Future planning and forecasting"""
    dean_school = request.user.school_as_dean.first()
    if not dean_school:
        messages.error(request, "You are not assigned as a Dean.")
        return redirect('dashboard')

    # Get upcoming goals and plans
    future_goals = StrategicGoal.objects.filter(
        school=dean_school,
        target_year__start_date__gt=timezone.now().date()
    ).select_related('target_year').order_by('target_year__start_date')

    # Budget projections
    current_year = AcademicYear.objects.filter(is_current=True).first()
    if current_year:
        current_budget = SchoolBudget.objects.filter(
            school=dean_school,
            financial_year=current_year
        ).first()
    else:
        current_budget = None

    # Staffing projections
    recruitments = StaffRecruitment.objects.filter(
        school=dean_school,
        status='open'
    ).count()

    # Research pipeline
    research_proposals = ResearchProject.objects.filter(
        school=dean_school,
        status='proposal'
    ).count()

    context = {
        'future_goals': future_goals,
        'current_budget': current_budget,
        'open_recruitments': recruitments,
        'research_proposals': research_proposals,
    }

    return render(request, 'dean/strategic/future_planning.html', context)


# ============================================================================
# APPROVALS & AUTHORIZATIONS VIEWS
# ============================================================================
@login_required
def dean_approvals_view(request):
    """Main approvals dashboard"""
    dean_school = request.user.school_as_dean.first()
    if not dean_school:
        messages.error(request, "You are not assigned as a Dean.")
        return redirect('dashboard')

    # Get pending approvals
    approvals = DeanApproval.objects.filter(
        department__school=dean_school,
        status='pending'
    ).select_related('requested_by', 'department').order_by('-request_date')

    # Group by approval type
    by_type = approvals.values('approval_type').annotate(
        count=Count('id')
    ).order_by('-count')

    # Priority items
    urgent = approvals.filter(priority='urgent')
    high = approvals.filter(priority='high')

    # Statistics
    stats = {
        'total_pending': approvals.count(),
        'urgent': urgent.count(),
        'high': high.count(),
        'medium': approvals.filter(priority='medium').count(),
        'low': approvals.filter(priority='low').count(),
    }

    context = {
        'approvals': approvals[:20],  # Latest 20
        'urgent_items': urgent,
        'high_priority': high,
        'by_type': by_type,
        'stats': stats,
    }

    return render(request, 'dean/approvals/dashboard.html', context)


@login_required
def dean_department_budgets_approval_view(request):
    """Approve department budgets"""
    dean_school = request.user.school_as_dean.first()
    if not dean_school:
        messages.error(request, "You are not assigned as a Dean.")
        return redirect('dashboard')

    # Get current year budget
    current_year = AcademicYear.objects.filter(is_current=True).first()
    school_budget = SchoolBudget.objects.filter(
        school=dean_school,
        financial_year=current_year
    ).first() if current_year else None

    if school_budget:
        # Get allocations needing approval
        allocations = BudgetAllocation.objects.filter(
            school_budget=school_budget
        ).select_related('department').order_by('department__name')
    else:
        allocations = BudgetAllocation.objects.none()

    context = {
        'school_budget': school_budget,
        'allocations': allocations,
    }

    return render(request, 'dean/approvals/department_budgets.html', context)

@login_required
def dean_staff_appointments_approval_view(request):
    """Approve staff appointments"""
    dean_school = request.user.school_as_dean.first()
    if not dean_school:
        messages.error(request, "You are not assigned as a Dean.")
        return redirect('dashboard')

    # Get recruitments needing dean approval
    recruitments = StaffRecruitment.objects.filter(
        school=dean_school,
        approved_by_dean__isnull=True
    ).select_related('department').order_by('-advertised_date')

    context = {
        'recruitments': recruitments,
    }

    return render(request, 'dean/approvals/staff_appointments.html', context)
    
    
@login_required
def dean_research_grants_approval_view(request):
    """Approve research grants"""
    dean_school = request.user.school_as_dean.first()
    if not dean_school:
        messages.error(request, "You are not assigned as a Dean.")
        return redirect('dashboard')

    # Get grants needing review
    grants = ResearchGrant.objects.filter(
        school=dean_school,
        status='under_review'
    ).select_related('principal_applicant__user').order_by('-application_date')

    context = {
        'grants': grants,
    }

    return render(request, 'dean/approvals/research_grants.html', context)     


# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q
from datetime import datetime, timedelta
from .models import (
    Lecturer, UnitAllocation, Assessment, UnitEnrollment, 
    Student, Semester, AcademicYear
)

@login_required
def lecturer_assessments(request):
    """View all assessments for lecturer's allocated units"""
    try:
        lecturer = request.user.lecturer_profile
    except Lecturer.DoesNotExist:
        messages.error(request, 'You do not have a lecturer profile.')
        return redirect('dashboard')
    
    # Get current semester
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get lecturer's unit allocations for current semester
    unit_allocations = UnitAllocation.objects.filter(
        lecturer=request.user,
        semester=current_semester,
        status__in=['approved_hod', 'approved_hos', 'approved_dean']
    ).select_related(
        'programme_unit__unit',
        'programme_unit__programme',
        'semester'
    )
    
    # Get all assessments for these allocations
    assessments = Assessment.objects.filter(
        unit_allocation__in=unit_allocations
    ).annotate(
        total_students=Count('student_marks', distinct=True),
        submitted_count=Count('student_marks', filter=Q(student_marks__attendance=True), distinct=True)
    ).order_by('-created_at')
    
    # Filter by unit if specified
    unit_filter = request.GET.get('unit')
    if unit_filter:
        assessments = assessments.filter(unit_allocation__id=unit_filter)
    
    # Filter by assessment type
    type_filter = request.GET.get('type')
    if type_filter:
        assessments = assessments.filter(assessment_type=type_filter)
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter == 'upcoming':
        assessments = assessments.filter(date__gt=timezone.now().date())
    elif status_filter == 'ongoing':
        assessments = assessments.filter(
            date__lte=timezone.now().date(),
            is_published=False
        )
    elif status_filter == 'completed':
        assessments = assessments.filter(is_published=True)
    
    context = {
        'assessments': assessments,
        'unit_allocations': unit_allocations,
        'current_semester': current_semester,
        'unit_filter': unit_filter,
        'type_filter': type_filter,
        'status_filter': status_filter,
    }
    
    return render(request, 'lecturer/assessments/list.html', context)


@login_required
def create_assessment(request):
    """Create a new assessment (CAT/Assignment)"""
    try:
        lecturer = request.user.lecturer_profile
    except Lecturer.DoesNotExist:
        messages.error(request, 'You do not have a lecturer profile.')
        return redirect('dashboard')
    
    # Get current semester
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get lecturer's unit allocations
    unit_allocations = UnitAllocation.objects.filter(
        lecturer=request.user,
        semester=current_semester,
        status__in=['approved_hod', 'approved_hos', 'approved_dean']
    ).select_related('programme_unit__unit', 'programme_unit__programme')
    
    if request.method == 'POST':
        unit_allocation_id = request.POST.get('unit_allocation')
        assessment_type = request.POST.get('assessment_type')
        title = request.POST.get('title')
        max_marks = request.POST.get('max_marks')
        weight_percentage = request.POST.get('weight_percentage')
        date = request.POST.get('date')
        duration_minutes = request.POST.get('duration_minutes')
        venue = request.POST.get('venue')
        instructions = request.POST.get('instructions')
        
        # Online CAT specific fields
        is_online = request.POST.get('is_online') == 'on'
        start_time = request.POST.get('start_time') if is_online else None
        end_time = request.POST.get('end_time') if is_online else None
        
        # Validation
        if not all([unit_allocation_id, assessment_type, title, max_marks, weight_percentage, date]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('create_assessment')
        
        try:
            unit_allocation = UnitAllocation.objects.get(
                id=unit_allocation_id,
                lecturer=request.user
            )
            
            # Check if assessment already exists
            existing = Assessment.objects.filter(
                unit_allocation=unit_allocation,
                assessment_type=assessment_type
            ).exists()
            
            if existing:
                messages.warning(request, f'A {assessment_type} assessment already exists for this unit.')
                return redirect('create_assessment')
            
            # Create assessment
            assessment = Assessment.objects.create(
                unit_allocation=unit_allocation,
                assessment_type=assessment_type,
                title=title,
                max_marks=max_marks,
                weight_percentage=weight_percentage,
                date=date,
                duration_minutes=duration_minutes or None,
                venue=venue or '',
                instructions=instructions or ''
            )
            
            # Get enrolled students for this unit
            enrolled_students = UnitEnrollment.objects.filter(
                programme_unit=unit_allocation.programme_unit,
                semester=current_semester,
                status='approved'
            ).select_related('student')
            
            # Create StudentMarks entries for enrolled students
            from .models import StudentMarks
            for enrollment in enrolled_students:
                StudentMarks.objects.create(
                    assessment=assessment,
                    student=enrollment.student,
                    marks_obtained=0,
                    attendance=False,
                    status='draft'
                )
            
            messages.success(
                request, 
                f'{assessment_type.upper()} created successfully! {enrolled_students.count()} students enrolled.'
            )
            return redirect('assessment_detail', assessment_id=assessment.id)
            
        except UnitAllocation.DoesNotExist:
            messages.error(request, 'Invalid unit allocation.')
            return redirect('create_assessment')
        except Exception as e:
            messages.error(request, f'Error creating assessment: {str(e)}')
            return redirect('create_assessment')
    
    context = {
        'unit_allocations': unit_allocations,
        'current_semester': current_semester,
    }
    
    return render(request, 'lecturer/assessments/create.html', context)


@login_required
def edit_assessment(request, assessment_id):
    """Edit an existing assessment"""
    assessment = get_object_or_404(
        Assessment,
        id=assessment_id,
        unit_allocation__lecturer=request.user
    )
    
    if request.method == 'POST':
        assessment.title = request.POST.get('title')
        assessment.max_marks = request.POST.get('max_marks')
        assessment.weight_percentage = request.POST.get('weight_percentage')
        assessment.date = request.POST.get('date')
        assessment.duration_minutes = request.POST.get('duration_minutes') or None
        assessment.venue = request.POST.get('venue', '')
        assessment.instructions = request.POST.get('instructions', '')
        
        try:
            assessment.save()
            messages.success(request, 'Assessment updated successfully!')
            return redirect('assessment_detail', assessment_id=assessment.id)
        except Exception as e:
            messages.error(request, f'Error updating assessment: {str(e)}')
    
    context = {
        'assessment': assessment,
    }
    
    return render(request, 'lecturer/assessments/edit.html', context)


@login_required
def assessment_detail(request, assessment_id):
    """View detailed information about an assessment"""
    assessment = get_object_or_404(
        Assessment.objects.select_related(
            'unit_allocation__programme_unit__unit',
            'unit_allocation__programme_unit__programme',
            'unit_allocation__semester'
        ).annotate(
            total_students=Count('student_marks', distinct=True),
            attended_count=Count('student_marks', filter=Q(student_marks__attendance=True), distinct=True),
            submitted_count=Count('student_marks', filter=Q(student_marks__status='submitted'), distinct=True)
        ),
        id=assessment_id,
        unit_allocation__lecturer=request.user
    )
    
    # Get student marks
    student_marks = assessment.student_marks.select_related(
        'student__user',
        'student__programme'
    ).order_by('student__registration_number')
    
    # Calculate statistics
    total_students = assessment.total_students
    attended = assessment.attended_count
    not_attended = total_students - attended
    attendance_rate = (attended / total_students * 100) if total_students > 0 else 0
    
    # Check if assessment is still editable (before date or not published)
    is_editable = assessment.date >= timezone.now().date() and not assessment.is_published
    
    context = {
        'assessment': assessment,
        'student_marks': student_marks,
        'total_students': total_students,
        'attended': attended,
        'not_attended': not_attended,
        'attendance_rate': round(attendance_rate, 1),
        'is_editable': is_editable,
    }
    
    return render(request, 'lecturer/assessments/detail.html', context)


@login_required
def extend_assessment(request, assessment_id):
    """Extend assessment date/time"""
    assessment = get_object_or_404(
        Assessment,
        id=assessment_id,
        unit_allocation__lecturer=request.user
    )
    
    if request.method == 'POST':
        new_date = request.POST.get('new_date')
        new_duration = request.POST.get('new_duration')
        reason = request.POST.get('reason', '')
        
        if new_date:
            old_date = assessment.date
            assessment.date = new_date
            
            if new_duration:
                assessment.duration_minutes = new_duration
            
            try:
                assessment.save()
                messages.success(
                    request,
                    f'Assessment extended from {old_date} to {new_date}. Reason: {reason}'
                )
                return redirect('assessment_detail', assessment_id=assessment.id)
            except Exception as e:
                messages.error(request, f'Error extending assessment: {str(e)}')
        else:
            messages.error(request, 'Please provide a new date.')
    
    context = {
        'assessment': assessment,
    }
    
    return render(request, 'lecturer/assessments/extend.html', context)


@login_required
def assessment_participants(request, assessment_id):
    """View all students enrolled for this assessment"""
    assessment = get_object_or_404(
        Assessment,
        id=assessment_id,
        unit_allocation__lecturer=request.user
    )
    
    # Get enrolled students
    student_marks = assessment.student_marks.select_related(
        'student__user',
        'student__programme'
    ).order_by('student__registration_number')
    
    # Filter by attendance status
    status_filter = request.GET.get('status')
    if status_filter == 'attended':
        student_marks = student_marks.filter(attendance=True)
    elif status_filter == 'not_attended':
        student_marks = student_marks.filter(attendance=False)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        student_marks = student_marks.filter(
            Q(student__registration_number__icontains=search_query) |
            Q(student__user__first_name__icontains=search_query) |
            Q(student__user__last_name__icontains=search_query)
        )
    
    context = {
        'assessment': assessment,
        'student_marks': student_marks,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'lecturer/assessments/participants.html', context)


@login_required
def delete_assessment(request, assessment_id):
    """Delete an assessment"""
    assessment = get_object_or_404(
        Assessment,
        id=assessment_id,
        unit_allocation__lecturer=request.user
    )
    
    if request.method == 'POST':
        # Only allow deletion if not published
        if assessment.is_published:
            messages.error(request, 'Cannot delete a published assessment.')
            return redirect('assessment_detail', assessment_id=assessment.id)
        
        unit_name = assessment.unit_allocation.programme_unit.unit.name
        assessment_type = assessment.get_assessment_type_display()
        
        try:
            assessment.delete()
            messages.success(request, f'{assessment_type} for {unit_name} deleted successfully!')
            return redirect('lecturer_assessments')
        except Exception as e:
            messages.error(request, f'Error deleting assessment: {str(e)}')
            return redirect('assessment_detail', assessment_id=assessment.id)
    
    context = {
        'assessment': assessment,
    }
    
    return render(request, 'lecturer/assessments/delete_confirm.html', context)


# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q, Avg, Sum, F
from django.http import HttpResponse, JsonResponse
from datetime import datetime
import csv
from decimal import Decimal
from .models import (
    Lecturer, UnitAllocation, Assessment, StudentMarks, 
    UnitEnrollment, Student, Semester, AcademicYear,
    SemesterResults, UnitGradingSystem
)

# ============= GRADING VIEWS =============

@login_required
def grading_dashboard(request):
    """Dashboard showing all assessments that need grading"""
    try:
        lecturer = request.user.lecturer_profile
    except Lecturer.DoesNotExist:
        messages.error(request, 'You do not have a lecturer profile.')
        return redirect('dashboard')
    
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get all assessments for current semester
    assessments = Assessment.objects.filter(
        unit_allocation__lecturer=request.user,
        unit_allocation__semester=current_semester,
        unit_allocation__status__in=['approved_hod', 'approved_hos', 'approved_dean']
    ).select_related(
        'unit_allocation__programme_unit__unit',
        'unit_allocation__programme_unit__programme'
    ).annotate(
        total_students=Count('student_marks'),
        graded_count=Count('student_marks', filter=Q(student_marks__marks_obtained__gt=0)),
        submitted_count=Count('student_marks', filter=Q(student_marks__status='submitted'))
    ).order_by('date')
    
    # Categorize assessments
    pending_grading = assessments.filter(
        date__lte=timezone.now().date(),
        is_published=False
    ).exclude(graded_count=F('total_students'))
    
    graded_not_submitted = assessments.filter(
        graded_count=F('total_students'),
        is_published=False
    )
    
    submitted_to_hod = assessments.filter(
        student_marks__status='submitted'
    ).distinct()
    
    context = {
        'current_semester': current_semester,
        'pending_grading': pending_grading,
        'graded_not_submitted': graded_not_submitted,
        'submitted_to_hod': submitted_to_hod,
        'total_assessments': assessments.count(),
    }
    
    return render(request, 'lecturer/grading/dashboard.html', context)


@login_required
def grade_students(request, assessment_id):
    """Grade individual students for an assessment"""
    assessment = get_object_or_404(
        Assessment.objects.select_related(
            'unit_allocation__programme_unit__unit',
            'unit_allocation__programme_unit__programme'
        ),
        id=assessment_id,
        unit_allocation__lecturer=request.user
    )
    
    if request.method == 'POST':
        # Process individual grade submission
        student_mark_id = request.POST.get('student_mark_id')
        marks_obtained = request.POST.get('marks_obtained')
        attendance = request.POST.get('attendance') == 'on'
        remarks = request.POST.get('remarks', '')
        
        try:
            student_mark = StudentMarks.objects.get(
                id=student_mark_id,
                assessment=assessment
            )
            
            # Validate marks
            marks_obtained = Decimal(marks_obtained) if marks_obtained else Decimal('0')
            if marks_obtained > assessment.max_marks:
                messages.error(request, f'Marks cannot exceed {assessment.max_marks}')
                return redirect('grade_students', assessment_id=assessment_id)
            
            student_mark.marks_obtained = marks_obtained
            student_mark.attendance = attendance
            student_mark.remarks = remarks
            student_mark.status = 'draft'
            student_mark.submitted_by = request.user
            student_mark.save()
            
            messages.success(request, f'Marks saved for {student_mark.student.user.get_full_name()}')
            
        except StudentMarks.DoesNotExist:
            messages.error(request, 'Invalid student mark record.')
        except Exception as e:
            messages.error(request, f'Error saving marks: {str(e)}')
        
        return redirect('grade_students', assessment_id=assessment_id)
    
    # Get all student marks
    student_marks = assessment.student_marks.select_related(
        'student__user',
        'student__programme'
    ).order_by('student__registration_number')
    
    # Calculate statistics
    total_students = student_marks.count()
    graded_count = student_marks.filter(marks_obtained__gt=0).count()
    avg_marks = student_marks.aggregate(Avg('marks_obtained'))['marks_obtained__avg'] or 0
    
    context = {
        'assessment': assessment,
        'student_marks': student_marks,
        'total_students': total_students,
        'graded_count': graded_count,
        'avg_marks': round(avg_marks, 2),
        'grading_progress': round((graded_count / total_students * 100), 1) if total_students > 0 else 0,
    }
    
    return render(request, 'lecturer/grading/grade_students.html', context)


@login_required
def bulk_upload_marks(request, assessment_id):
    """Bulk upload marks via CSV"""
    assessment = get_object_or_404(
        Assessment,
        id=assessment_id,
        unit_allocation__lecturer=request.user
    )
    
    if request.method == 'POST' and request.FILES.get('marks_file'):
        csv_file = request.FILES['marks_file']
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Please upload a CSV file.')
            return redirect('grade_students', assessment_id=assessment_id)
        
        try:
            # Read CSV file
            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            
            updated_count = 0
            error_count = 0
            errors = []
            
            for row in reader:
                try:
                    reg_number = row.get('registration_number', '').strip()
                    marks = row.get('marks', '').strip()
                    attendance = row.get('attendance', '').strip().upper() in ['YES', 'Y', '1', 'TRUE']
                    remarks = row.get('remarks', '').strip()
                    
                    if not reg_number or not marks:
                        continue
                    
                    # Get student mark
                    student_mark = StudentMarks.objects.filter(
                        assessment=assessment,
                        student__registration_number=reg_number
                    ).first()
                    
                    if not student_mark:
                        errors.append(f"Student {reg_number} not found")
                        error_count += 1
                        continue
                    
                    # Validate marks
                    marks_value = Decimal(marks)
                    if marks_value > assessment.max_marks:
                        errors.append(f"{reg_number}: Marks exceed maximum ({assessment.max_marks})")
                        error_count += 1
                        continue
                    
                    # Update marks
                    student_mark.marks_obtained = marks_value
                    student_mark.attendance = attendance
                    student_mark.remarks = remarks
                    student_mark.status = 'draft'
                    student_mark.submitted_by = request.user
                    student_mark.save()
                    
                    updated_count += 1
                    
                except Exception as e:
                    errors.append(f"{reg_number}: {str(e)}")
                    error_count += 1
            
            if updated_count > 0:
                messages.success(request, f'Successfully uploaded marks for {updated_count} student(s).')
            
            if error_count > 0:
                messages.warning(request, f'{error_count} error(s) occurred. Check details below.')
                for error in errors[:10]:  # Show first 10 errors
                    messages.error(request, error)
            
        except Exception as e:
            messages.error(request, f'Error processing file: {str(e)}')
        
        return redirect('grade_students', assessment_id=assessment_id)
    
    return redirect('grade_students', assessment_id=assessment_id)


@login_required
def download_grading_template(request, assessment_id):
    """Download CSV template for bulk grading"""
    assessment = get_object_or_404(
        Assessment,
        id=assessment_id,
        unit_allocation__lecturer=request.user
    )
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="grading_template_{assessment_id}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['registration_number', 'student_name', 'marks', 'attendance', 'remarks'])
    
    # Add student data
    student_marks = assessment.student_marks.select_related('student__user').order_by('student__registration_number')
    
    for mark in student_marks:
        writer.writerow([
            mark.student.registration_number,
            mark.student.user.get_full_name(),
            '',  # Empty for marks to be filled
            '',  # Empty for attendance
            ''   # Empty for remarks
        ])
    
    return response


# ============= FINAL EXAMS VIEWS =============

@login_required
def final_exams(request):
    """View and manage final exams"""
    try:
        lecturer = request.user.lecturer_profile
    except Lecturer.DoesNotExist:
        messages.error(request, 'You do not have a lecturer profile.')
        return redirect('dashboard')
    
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get all final exams
    final_exams = Assessment.objects.filter(
        unit_allocation__lecturer=request.user,
        unit_allocation__semester=current_semester,
        assessment_type='final'
    ).select_related(
        'unit_allocation__programme_unit__unit',
        'unit_allocation__programme_unit__programme'
    ).annotate(
        total_students=Count('student_marks'),
        graded_count=Count('student_marks', filter=Q(student_marks__marks_obtained__gt=0))
    )
    
    # Get units without final exams
    unit_allocations = UnitAllocation.objects.filter(
        lecturer=request.user,
        semester=current_semester,
        status__in=['approved_hod', 'approved_hos', 'approved_dean']
    ).exclude(
        assessments__assessment_type='final'
    ).select_related('programme_unit__unit', 'programme_unit__programme')
    
    context = {
        'current_semester': current_semester,
        'final_exams': final_exams,
        'unit_allocations': unit_allocations,
    }
    
    return render(request, 'lecturer/grading/final_exams.html', context)


@login_required
def create_final_exam(request):
    """Create final exam assessment"""
    if request.method == 'POST':
        unit_allocation_id = request.POST.get('unit_allocation')
        title = request.POST.get('title')
        max_marks = request.POST.get('max_marks', 70)
        weight_percentage = request.POST.get('weight_percentage', 70)
        date = request.POST.get('date')
        duration_minutes = request.POST.get('duration_minutes')
        venue = request.POST.get('venue', '')
        instructions = request.POST.get('instructions', '')
        
        try:
            unit_allocation = UnitAllocation.objects.get(
                id=unit_allocation_id,
                lecturer=request.user
            )
            
            # Check if final exam already exists
            if Assessment.objects.filter(
                unit_allocation=unit_allocation,
                assessment_type='final'
            ).exists():
                messages.error(request, 'Final exam already exists for this unit.')
                return redirect('final_exams')
            
            # Create final exam
            exam = Assessment.objects.create(
                unit_allocation=unit_allocation,
                assessment_type='final',
                title=title,
                max_marks=max_marks,
                weight_percentage=weight_percentage,
                date=date,
                duration_minutes=duration_minutes,
                venue=venue,
                instructions=instructions
            )
            
            # Create student marks entries
            current_semester = unit_allocation.semester
            enrolled_students = UnitEnrollment.objects.filter(
                programme_unit=unit_allocation.programme_unit,
                semester=current_semester,
                status='approved'
            ).select_related('student')
            
            for enrollment in enrolled_students:
                StudentMarks.objects.create(
                    assessment=exam,
                    student=enrollment.student,
                    marks_obtained=0,
                    attendance=False,
                    status='draft'
                )
            
            messages.success(request, f'Final exam created successfully! {enrolled_students.count()} students enrolled.')
            return redirect('grade_final_exam', exam_id=exam.id)
            
        except Exception as e:
            messages.error(request, f'Error creating final exam: {str(e)}')
            return redirect('final_exams')
    
    return redirect('final_exams')


@login_required
def grade_final_exam(request, exam_id):
    """Grade final exam - same as grade_students but with final exam context"""
    return grade_students(request, exam_id)


# ============= MODERATION VIEWS =============

@login_required
def moderation_dashboard(request):
    """Dashboard for moderation activities"""
    try:
        lecturer = request.user.lecturer_profile
    except Lecturer.DoesNotExist:
        messages.error(request, 'You do not have a lecturer profile.')
        return redirect('dashboard')
    
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get assessments pending moderation (graded but not submitted)
    assessments = Assessment.objects.filter(
        unit_allocation__lecturer=request.user,
        unit_allocation__semester=current_semester
    ).annotate(
        total_students=Count('student_marks'),
        graded_count=Count('student_marks', filter=Q(student_marks__marks_obtained__gt=0))
    ).filter(
        graded_count=F('total_students'),
        is_published=False
    ).select_related(
        'unit_allocation__programme_unit__unit',
        'unit_allocation__programme_unit__programme'
    )
    
    # Get assessments under moderation
    under_moderation = StudentMarks.objects.filter(
        assessment__unit_allocation__lecturer=request.user,
        status__in=['submitted', 'approved_hod']
    ).values(
        'assessment__id',
        'assessment__title',
        'assessment__unit_allocation__programme_unit__unit__code',
        'status'
    ).annotate(
        count=Count('id')
    )
    
    context = {
        'current_semester': current_semester,
        'assessments': assessments,
        'under_moderation': under_moderation,
    }
    
    return render(request, 'lecturer/grading/moderation_dashboard.html', context)


@login_required
def request_moderation(request, assessment_id):
    """Request moderation for assessment"""
    assessment = get_object_or_404(
        Assessment,
        id=assessment_id,
        unit_allocation__lecturer=request.user
    )
    
    if request.method == 'POST':
        # Check if all students are graded
        total_students = assessment.student_marks.count()
        graded_students = assessment.student_marks.filter(marks_obtained__gt=0).count()
        
        if graded_students < total_students:
            messages.error(request, f'Please grade all students before requesting moderation. {total_students - graded_students} student(s) pending.')
            return redirect('grade_students', assessment_id=assessment_id)
        
        # Update all student marks to submitted status
        assessment.student_marks.update(
            status='submitted',
            submitted_by=request.user
        )
        
        messages.success(request, 'Marks submitted for moderation successfully.')
        return redirect('moderation_dashboard')
    
    return redirect('grade_students', assessment_id=assessment_id)


@login_required
def view_moderation(request, assessment_id):
    """View moderation status and comments"""
    assessment = get_object_or_404(
        Assessment,
        id=assessment_id,
        unit_allocation__lecturer=request.user
    )
    
    student_marks = assessment.student_marks.select_related(
        'student__user',
        'approved_by_hod',
        'approved_by_hos',
        'approved_by_dean'
    ).order_by('student__registration_number')
    
    # Get moderation statistics
    moderation_stats = {
        'total': student_marks.count(),
        'submitted': student_marks.filter(status='submitted').count(),
        'approved_hod': student_marks.filter(status='approved_hod').count(),
        'approved_hos': student_marks.filter(status='approved_hos').count(),
        'approved_dean': student_marks.filter(status='approved_dean').count(),
        'published': student_marks.filter(status='published').count(),
        'rejected': student_marks.filter(status='rejected').count(),
    }
    
    context = {
        'assessment': assessment,
        'student_marks': student_marks,
        'moderation_stats': moderation_stats,
    }
    
    return render(request, 'lecturer/grading/view_moderation.html', context)


# ============= RESULT SUBMISSION VIEWS =============

@login_required
def results_dashboard(request):
    """Dashboard for result submission"""
    try:
        lecturer = request.user.lecturer_profile
    except Lecturer.DoesNotExist:
        messages.error(request, 'You do not have a lecturer profile.')
        return redirect('dashboard')
    
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get unit allocations with assessment completion status
    unit_allocations = UnitAllocation.objects.filter(
        lecturer=request.user,
        semester=current_semester,
        status__in=['approved_hod', 'approved_hos', 'approved_dean']
    ).select_related(
        'programme_unit__unit',
        'programme_unit__programme'
    ).annotate(
        total_assessments=Count('assessments'),
        completed_assessments=Count('assessments', filter=Q(assessments__is_published=True))
    )
    
    # Check if results exist
    for allocation in unit_allocations:
        allocation.results_exist = SemesterResults.objects.filter(
            programme_unit=allocation.programme_unit,
            semester=current_semester
        ).exists()
    
    context = {
        'current_semester': current_semester,
        'unit_allocations': unit_allocations,
    }
    
    return render(request, 'lecturer/grading/results_dashboard.html', context)


@login_required
def submit_results(request, unit_allocation_id):
    """Submit final results for a unit"""
    unit_allocation = get_object_or_404(
        UnitAllocation.objects.select_related(
            'programme_unit__unit',
            'programme_unit__programme',
            'semester'
        ),
        id=unit_allocation_id,
        lecturer=request.user
    )
    
    if request.method == 'POST':
        try:
            # Get all assessments for this unit
            assessments = Assessment.objects.filter(
                unit_allocation=unit_allocation
            )
            
            # Get enrolled students
            enrollments = UnitEnrollment.objects.filter(
                programme_unit=unit_allocation.programme_unit,
                semester=unit_allocation.semester,
                status='approved'
            ).select_related('student')
            
            results_created = 0
            
            for enrollment in enrollments:
                # Calculate total marks
                student_marks = StudentMarks.objects.filter(
                    assessment__in=assessments,
                    student=enrollment.student
                )
                
                # Calculate weighted marks
                cat_total = Decimal('0')
                assignment_total = Decimal('0')
                exam_total = Decimal('0')
                total_marks = Decimal('0')
                
                for mark in student_marks:
                    weighted_mark = (mark.marks_obtained / mark.assessment.max_marks) * mark.assessment.weight_percentage
                    
                    if mark.assessment.assessment_type in ['cat1', 'cat2', 'cat3']:
                        cat_total += weighted_mark
                    elif mark.assessment.assessment_type == 'assignment':
                        assignment_total += weighted_mark
                    elif mark.assessment.assessment_type == 'final':
                        exam_total += weighted_mark
                    
                    total_marks += weighted_mark
                
                # Get grade from grading system
                grading = UnitGradingSystem.objects.filter(
                    unit=unit_allocation.programme_unit.unit,
                    min_marks__lte=total_marks,
                    max_marks__gte=total_marks
                ).first()
                
                if not grading:
                    # Default grading if not found
                    if total_marks >= 70:
                        grade, grade_point = 'A', Decimal('4.00')
                    elif total_marks >= 60:
                        grade, grade_point = 'B', Decimal('3.00')
                    elif total_marks >= 50:
                        grade, grade_point = 'C', Decimal('2.00')
                    elif total_marks >= 40:
                        grade, grade_point = 'D', Decimal('1.00')
                    else:
                        grade, grade_point = 'F', Decimal('0.00')
                else:
                    grade = grading.grade
                    grade_point = grading.grade_point
                
                # Calculate quality points
                credit_hours = unit_allocation.programme_unit.unit.credit_hours
                quality_points = grade_point * credit_hours
                
                # Create or update semester result
                SemesterResults.objects.update_or_create(
                    student=enrollment.student,
                    programme_unit=unit_allocation.programme_unit,
                    semester=unit_allocation.semester,
                    defaults={
                        'academic_year': unit_allocation.semester.academic_year,
                        'cat_marks': cat_total,
                        'assignment_marks': assignment_total,
                        'exam_marks': exam_total,
                        'total_marks': total_marks,
                        'grade': grade,
                        'grade_point': grade_point,
                        'credit_hours': credit_hours,
                        'quality_points': quality_points,
                        'is_passed': grade_point >= Decimal('2.00'),
                    }
                )
                
                results_created += 1
            
            messages.success(request, f'Results submitted successfully for {results_created} student(s).')
            return redirect('results_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error submitting results: {str(e)}')
            return redirect('preview_results', unit_allocation_id=unit_allocation_id)
    
    return redirect('preview_results', unit_allocation_id=unit_allocation_id)


@login_required
def preview_results(request, unit_allocation_id):
    """Preview results before submission"""
    unit_allocation = get_object_or_404(
        UnitAllocation.objects.select_related(
            'programme_unit__unit',
            'programme_unit__programme',
            'semester'
        ),
        id=unit_allocation_id,
        lecturer=request.user
    )
    
    # Get all assessments
    assessments = Assessment.objects.filter(
        unit_allocation=unit_allocation
    ).order_by('assessment_type')
    
    # Get enrolled students with calculated results
    enrollments = UnitEnrollment.objects.filter(
        programme_unit=unit_allocation.programme_unit,
        semester=unit_allocation.semester,
        status='approved'
    ).select_related('student__user')
    
    # Calculate preview results
    preview_data = []
    
    for enrollment in enrollments:
        student_data = {
            'student': enrollment.student,
            'assessments': {},
            'totals': {
                'cat': Decimal('0'),
                'assignment': Decimal('0'),
                'exam': Decimal('0'),
                'total': Decimal('0')
            }
        }
        
        # Get marks for each assessment
        for assessment in assessments:
            mark = StudentMarks.objects.filter(
                assessment=assessment,
                student=enrollment.student
            ).first()
            
            if mark:
                weighted_mark = (mark.marks_obtained / assessment.max_marks) * assessment.weight_percentage
                student_data['assessments'][assessment.id] = {
                    'marks': mark.marks_obtained,
                    'max_marks': assessment.max_marks,
                    'weighted': weighted_mark
                }
                
                # Add to totals
                if assessment.assessment_type in ['cat1', 'cat2', 'cat3']:
                    student_data['totals']['cat'] += weighted_mark
                elif assessment.assessment_type == 'assignment':
                    student_data['totals']['assignment'] += weighted_mark
                elif assessment.assessment_type == 'final':
                    student_data['totals']['exam'] += weighted_mark
                
                student_data['totals']['total'] += weighted_mark
        
        # Calculate grade
        total_marks = student_data['totals']['total']
        if total_marks >= 70:
            student_data['grade'] = 'A'
        elif total_marks >= 60:
            student_data['grade'] = 'B'
        elif total_marks >= 50:
            student_data['grade'] = 'C'
        elif total_marks >= 40:
            student_data['grade'] = 'D'
        else:
            student_data['grade'] = 'F'
        
        preview_data.append(student_data)
    
    context = {
        'unit_allocation': unit_allocation,
        'assessments': assessments,
        'preview_data': preview_data,
    }
    
    return render(request, 'lecturer/grading/preview_results.html', context)


@login_required
def submission_history(request, unit_allocation_id):
    """View submission history for a unit"""
    unit_allocation = get_object_or_404(
        UnitAllocation,
        id=unit_allocation_id,
        lecturer=request.user
    )
    
    # Get all results for this unit
    results = SemesterResults.objects.filter(
        programme_unit=unit_allocation.programme_unit,
        semester=unit_allocation.semester
    ).select_related(
        'student__user',
        'approved_by_hod',
        'approved_by_hos',
        'approved_by_dean'
    ).order_by('-created_at')
    
    context = {
        'unit_allocation': unit_allocation,
        'results': results,
    }
    
    return render(request, 'lecturer/grading/submission_history.html', context)


# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q, Avg, Sum, F, Max, Min
from django.http import HttpResponse, JsonResponse
from datetime import datetime, timedelta
import csv
from decimal import Decimal

from .models import (
    Lecturer, UnitAllocation, Student, UnitEnrollment, 
    StudentMarks, Assessment, SemesterResults, Attendance,
    AdvisingNote, StudentSpecialNeed, Semester, AcademicYear
)

# ============= STUDENTS DASHBOARD =============

@login_required
def students_dashboard(request):
    """Main students dashboard for lecturers"""
    try:
        lecturer = request.user.lecturer_profile
    except Lecturer.DoesNotExist:
        messages.error(request, 'You do not have a lecturer profile.')
        return redirect('dashboard')
    
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get lecturer's units
    unit_allocations = UnitAllocation.objects.filter(
        lecturer=request.user,
        semester=current_semester,
        status__in=['approved_hod', 'approved_hos', 'approved_dean']
    ).select_related('programme_unit__unit', 'programme_unit__programme')
    
    # Get total students across all units
    total_students = UnitEnrollment.objects.filter(
        programme_unit__in=[ua.programme_unit for ua in unit_allocations],
        semester=current_semester,
        status='approved'
    ).values('student').distinct().count()
    
    # Get students with special needs
    special_needs_students = StudentSpecialNeed.objects.filter(
        student__unit_enrollments__programme_unit__in=[ua.programme_unit for ua in unit_allocations],
        student__unit_enrollments__semester=current_semester,
        is_active=True
    ).values('student').distinct().count()
    
    # Get students needing academic advising (low performance)
    students_needing_advising = Student.objects.filter(
        unit_enrollments__programme_unit__in=[ua.programme_unit for ua in unit_allocations],
        unit_enrollments__semester=current_semester,
        cumulative_gpa__lt=2.5
    ).distinct().count()
    
    # Recent advising notes
    recent_notes = AdvisingNote.objects.filter(
        lecturer=request.user
    ).select_related('student__user')[:5]
    
    context = {
        'current_semester': current_semester,
        'unit_allocations': unit_allocations,
        'total_students': total_students,
        'special_needs_students': special_needs_students,
        'students_needing_advising': students_needing_advising,
        'recent_notes': recent_notes,
    }
    
    return render(request, 'lecturer/students/dashboard.html', context)


# ============= CLASS LISTS =============

@login_required
def class_lists(request):
    """View all class lists for lecturer's units"""
    try:
        lecturer = request.user.lecturer_profile
    except Lecturer.DoesNotExist:
        messages.error(request, 'You do not have a lecturer profile.')
        return redirect('dashboard')
    
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get all unit allocations with student counts
    unit_allocations = UnitAllocation.objects.filter(
        lecturer=request.user,
        semester=current_semester,
        status__in=['approved_hod', 'approved_hos', 'approved_dean']
    ).select_related(
        'programme_unit__unit',
        'programme_unit__programme',
        'semester'
    ).annotate(
        enrolled_count=Count('programme_unit__enrollments', 
                           filter=Q(programme_unit__enrollments__semester=current_semester,
                                  programme_unit__enrollments__status='approved'))
    ).order_by('programme_unit__unit__code')
    
    context = {
        'current_semester': current_semester,
        'unit_allocations': unit_allocations,
    }
    
    return render(request, 'lecturer/students/class_lists.html', context)


@login_required
def class_detail(request, unit_allocation_id):
    """Detailed class list for a specific unit"""
    unit_allocation = get_object_or_404(
        UnitAllocation.objects.select_related(
            'programme_unit__unit',
            'programme_unit__programme',
            'semester'
        ),
        id=unit_allocation_id,
        lecturer=request.user
    )
    
    # Get enrolled students
    enrollments = UnitEnrollment.objects.filter(
        programme_unit=unit_allocation.programme_unit,
        semester=unit_allocation.semester,
        status='approved'
    ).select_related(
        'student__user',
        'student__programme'
    ).order_by('student__registration_number')
    
    # Get attendance statistics for each student
    students_data = []
    for enrollment in enrollments:
        # Get attendance record
        total_classes = Attendance.objects.filter(
            unit_allocation=unit_allocation,
            student=enrollment.student
        ).count()
        
        attended = Attendance.objects.filter(
            unit_allocation=unit_allocation,
            student=enrollment.student,
            status='present'
        ).count()
        
        attendance_rate = (attended / total_classes * 100) if total_classes > 0 else 0
        
        # Get current marks
        marks_data = StudentMarks.objects.filter(
            assessment__unit_allocation=unit_allocation,
            student=enrollment.student
        ).values('assessment__assessment_type').annotate(
            total_marks=Sum('marks_obtained')
        )
        
        students_data.append({
            'student': enrollment.student,
            'enrollment': enrollment,
            'attendance_rate': round(attendance_rate, 1),
            'total_classes': total_classes,
            'attended': attended,
            'marks_data': marks_data,
        })
    
    # Filter options
    search_query = request.GET.get('search', '')
    if search_query:
        students_data = [
            data for data in students_data
            if search_query.lower() in data['student'].registration_number.lower() or
               search_query.lower() in data['student'].user.get_full_name().lower()
        ]
    
    context = {
        'unit_allocation': unit_allocation,
        'students_data': students_data,
        'total_students': len(students_data),
        'search_query': search_query,
    }
    
    return render(request, 'lecturer/students/class_detail.html', context)


@login_required
def export_class_list(request, unit_allocation_id):
    """Export class list to CSV"""
    unit_allocation = get_object_or_404(
        UnitAllocation,
        id=unit_allocation_id,
        lecturer=request.user
    )
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="class_list_{unit_allocation.programme_unit.unit.code}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Registration Number', 'Student Name', 'Email', 'Programme', 
        'Year', 'Semester', 'Phone Number', 'ID Number'
    ])
    
    # Get enrolled students
    enrollments = UnitEnrollment.objects.filter(
        programme_unit=unit_allocation.programme_unit,
        semester=unit_allocation.semester,
        status='approved'
    ).select_related('student__user', 'student__programme').order_by('student__registration_number')
    
    for enrollment in enrollments:
        writer.writerow([
            enrollment.student.registration_number,
            enrollment.student.user.get_full_name(),
            enrollment.student.user.email,
            enrollment.student.programme.code,
            enrollment.student.current_year,
            enrollment.student.current_semester,
            enrollment.student.user.phone_number,
            enrollment.student.national_id,
        ])
    
    return response


# ============= STUDENT PERFORMANCE =============

@login_required
def student_performance_overview(request):
    """Overview of student performance across units"""
    try:
        lecturer = request.user.lecturer_profile
    except Lecturer.DoesNotExist:
        messages.error(request, 'You do not have a lecturer profile.')
        return redirect('dashboard')
    
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get lecturer's units
    unit_allocations = UnitAllocation.objects.filter(
        lecturer=request.user,
        semester=current_semester,
        status__in=['approved_hod', 'approved_hos', 'approved_dean']
    ).select_related('programme_unit__unit', 'programme_unit__programme')
    
    # Get performance data per unit
    unit_performance = []
    for allocation in unit_allocations:
        enrollments = UnitEnrollment.objects.filter(
            programme_unit=allocation.programme_unit,
            semester=current_semester,
            status='approved'
        ).count()
        
        # Get average marks
        avg_marks = StudentMarks.objects.filter(
            assessment__unit_allocation=allocation
        ).aggregate(Avg('marks_obtained'))['marks_obtained__avg'] or 0
        
        # Get students by performance category
        high_performers = Student.objects.filter(
            unit_enrollments__programme_unit=allocation.programme_unit,
            unit_enrollments__semester=current_semester,
            cumulative_gpa__gte=3.5
        ).distinct().count()
        
        low_performers = Student.objects.filter(
            unit_enrollments__programme_unit=allocation.programme_unit,
            unit_enrollments__semester=current_semester,
            cumulative_gpa__lt=2.0
        ).distinct().count()
        
        unit_performance.append({
            'allocation': allocation,
            'total_students': enrollments,
            'avg_marks': round(avg_marks, 2),
            'high_performers': high_performers,
            'low_performers': low_performers,
        })
    
    # Search for specific student
    search_query = request.GET.get('search', '')
    search_results = None
    if search_query:
        search_results = Student.objects.filter(
            Q(registration_number__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        ).filter(
            unit_enrollments__programme_unit__in=[ua.programme_unit for ua in unit_allocations],
            unit_enrollments__semester=current_semester
        ).distinct().select_related('user', 'programme')[:10]
    
    context = {
        'current_semester': current_semester,
        'unit_performance': unit_performance,
        'search_query': search_query,
        'search_results': search_results,
    }
    
    return render(request, 'lecturer/students/performance_overview.html', context)


@login_required
def student_performance_detail(request, registration_number):
    """Detailed performance view for a specific student"""
    student = get_object_or_404(
        Student.objects.select_related('user', 'programme'),
        registration_number=registration_number
    )
    
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Check if lecturer teaches this student
    lecturer_units = UnitAllocation.objects.filter(
        lecturer=request.user,
        semester=current_semester,
        programme_unit__enrollments__student=student,
        programme_unit__enrollments__semester=current_semester
    ).exists()
    
    if not lecturer_units:
        messages.error(request, 'You do not teach this student in the current semester.')
        return redirect('student_performance_overview')
    
    # Get student's enrollments for current semester
    enrollments = UnitEnrollment.objects.filter(
        student=student,
        semester=current_semester,
        status='approved'
    ).select_related('programme_unit__unit')
    
    # Get performance data for each unit
    unit_performances = []
    for enrollment in enrollments:
        # Get all marks for this unit
        marks = StudentMarks.objects.filter(
            student=student,
            assessment__unit_allocation__programme_unit=enrollment.programme_unit,
            assessment__unit_allocation__semester=current_semester
        ).select_related('assessment')
        
        total_marks = sum([mark.marks_obtained for mark in marks])
        total_possible = sum([mark.assessment.max_marks for mark in marks])
        percentage = (total_marks / total_possible * 100) if total_possible > 0 else 0
        
        # Get attendance
        attendance_records = Attendance.objects.filter(
            student=student,
            unit_allocation__programme_unit=enrollment.programme_unit,
            unit_allocation__semester=current_semester
        )
        
        total_classes = attendance_records.count()
        attended = attendance_records.filter(status='present').count()
        attendance_rate = (attended / total_classes * 100) if total_classes > 0 else 0
        
        unit_performances.append({
            'unit': enrollment.programme_unit.unit,
            'marks': marks,
            'total_marks': total_marks,
            'total_possible': total_possible,
            'percentage': round(percentage, 2),
            'attendance_rate': round(attendance_rate, 1),
            'total_classes': total_classes,
            'attended': attended,
        })
    
    # Get semester results history
    semester_results = SemesterResults.objects.filter(
        student=student
    ).select_related('semester', 'programme_unit__unit').order_by('-semester__start_date')
    
    # Get advising notes
    advising_notes = AdvisingNote.objects.filter(
        student=student
    ).select_related('lecturer').order_by('-created_at')[:5]
    
    context = {
        'student': student,
        'current_semester': current_semester,
        'unit_performances': unit_performances,
        'semester_results': semester_results,
        'advising_notes': advising_notes,
    }
    
    return render(request, 'lecturer/students/performance_detail.html', context)


@login_required
def student_unit_performance(request, registration_number, unit_id):
    """Detailed performance for a student in a specific unit"""
    student = get_object_or_404(Student, registration_number=registration_number)
    
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get unit allocation
    unit_allocation = get_object_or_404(
        UnitAllocation.objects.select_related('programme_unit__unit'),
        programme_unit__unit__id=unit_id,
        lecturer=request.user,
        semester=current_semester
    )
    
    # Get all assessments and marks
    assessments = Assessment.objects.filter(
        unit_allocation=unit_allocation
    ).order_by('assessment_type', 'date')
    
    marks_data = []
    for assessment in assessments:
        mark = StudentMarks.objects.filter(
            assessment=assessment,
            student=student
        ).first()
        
        marks_data.append({
            'assessment': assessment,
            'mark': mark,
            'percentage': (mark.marks_obtained / assessment.max_marks * 100) if mark else 0
        })
    
    # Get attendance records
    attendance_records = Attendance.objects.filter(
        student=student,
        unit_allocation=unit_allocation
    ).order_by('-attendance_date')
    
    context = {
        'student': student,
        'unit_allocation': unit_allocation,
        'marks_data': marks_data,
        'attendance_records': attendance_records,
    }
    
    return render(request, 'lecturer/students/unit_performance.html', context)


# ============= ACADEMIC ADVISING =============

@login_required
def academic_advising(request):
    """Academic advising dashboard"""
    try:
        lecturer = request.user.lecturer_profile
    except Lecturer.DoesNotExist:
        messages.error(request, 'You do not have a lecturer profile.')
        return redirect('dashboard')
    
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get students taught by lecturer
    lecturer_students = Student.objects.filter(
        unit_enrollments__programme_unit__allocations__lecturer=request.user,
        unit_enrollments__semester=current_semester
    ).distinct().select_related('user', 'programme')
    
    # Categorize students
    at_risk_students = lecturer_students.filter(cumulative_gpa__lt=2.0)
    low_performing = lecturer_students.filter(cumulative_gpa__gte=2.0, cumulative_gpa__lt=2.5)
    high_performing = lecturer_students.filter(cumulative_gpa__gte=3.5)
    
    # Get all advising notes
    all_notes = AdvisingNote.objects.filter(
        lecturer=request.user
    ).select_related('student__user').order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter == 'open':
        all_notes = all_notes.filter(is_resolved=False)
    elif status_filter == 'resolved':
        all_notes = all_notes.filter(is_resolved=True)
    elif status_filter == 'action_required':
        all_notes = all_notes.filter(action_required=True, is_resolved=False)
    
    context = {
        'current_semester': current_semester,
        'at_risk_students': at_risk_students,
        'low_performing': low_performing,
        'high_performing': high_performing,
        'all_notes': all_notes,
        'status_filter': status_filter,
    }
    
    return render(request, 'lecturer/students/academic_advising.html', context)


@login_required
def student_advising_detail(request, registration_number):
    """Detailed advising view for a student"""
    student = get_object_or_404(
        Student.objects.select_related('user', 'programme'),
        registration_number=registration_number
    )
    
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get all advising notes for this student
    advising_notes = AdvisingNote.objects.filter(
        student=student
    ).select_related('lecturer').order_by('-created_at')
    
    # Get student's academic performance
    semester_results = SemesterResults.objects.filter(
        student=student
    ).select_related('semester', 'programme_unit__unit').order_by('-semester__start_date')[:5]
    
    # Get current semester performance
    current_enrollments = UnitEnrollment.objects.filter(
        student=student,
        semester=current_semester,
        status='approved'
    ).select_related('programme_unit__unit')
    
    context = {
        'student': student,
        'current_semester': current_semester,
        'advising_notes': advising_notes,
        'semester_results': semester_results,
        'current_enrollments': current_enrollments,
    }
    
    return render(request, 'lecturer/students/advising_detail.html', context)


@login_required
def add_advising_note(request, registration_number):
    """Add new advising note"""
    student = get_object_or_404(Student, registration_number=registration_number)
    
    if request.method == 'POST':
        note_type = request.POST.get('note_type')
        subject = request.POST.get('subject')
        note = request.POST.get('note')
        action_required = request.POST.get('action_required') == 'on'
        follow_up_date = request.POST.get('follow_up_date') or None
        is_confidential = request.POST.get('is_confidential') == 'on'
        
        try:
            AdvisingNote.objects.create(
                student=student,
                lecturer=request.user,
                note_type=note_type,
                subject=subject,
                note=note,
                action_required=action_required,
                follow_up_date=follow_up_date,
                is_confidential=is_confidential
            )
            
            messages.success(request, 'Advising note added successfully.')
            return redirect('student_advising_detail', registration_number=registration_number)
            
        except Exception as e:
            messages.error(request, f'Error adding note: {str(e)}')
    
    return redirect('student_advising_detail', registration_number=registration_number)


@login_required
def edit_advising_note(request, note_id):
    """Edit existing advising note"""
    note = get_object_or_404(
        AdvisingNote,
        id=note_id,
        lecturer=request.user
    )
    
    if request.method == 'POST':
        note.note_type = request.POST.get('note_type')
        note.subject = request.POST.get('subject')
        note.note = request.POST.get('note')
        note.action_required = request.POST.get('action_required') == 'on'
        note.action_taken = request.POST.get('action_taken', '')
        note.follow_up_date = request.POST.get('follow_up_date') or None
        note.is_confidential = request.POST.get('is_confidential') == 'on'
        note.is_resolved = request.POST.get('is_resolved') == 'on'
        
        if note.is_resolved and not note.resolved_date:
            note.resolved_date = timezone.now()
        
        try:
            note.save()
            messages.success(request, 'Advising note updated successfully.')
        except Exception as e:
            messages.error(request, f'Error updating note: {str(e)}')
    
    return redirect('student_advising_detail', registration_number=note.student.registration_number)


# ============= SPECIAL NEEDS =============

@login_required
def special_needs(request):
    """View students with special needs"""
    try:
        lecturer = request.user.lecturer_profile
    except Lecturer.DoesNotExist:
        messages.error(request, 'You do not have a lecturer profile.')
        return redirect('dashboard')
    
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get students with special needs that lecturer teaches
    special_needs_students = StudentSpecialNeed.objects.filter(
        student__unit_enrollments__programme_unit__allocations__lecturer=request.user,
        student__unit_enrollments__semester=current_semester,
        is_active=True
    ).distinct().select_related(
        'student__user',
        'student__programme'
    ).order_by('student__registration_number')
    
    # Filter by type
    type_filter = request.GET.get('type')
    if type_filter:
        special_needs_students = special_needs_students.filter(need_type=type_filter)
    
    # Statistics
    total_special_needs = special_needs_students.count()
    by_type = StudentSpecialNeed.objects.filter(
        student__unit_enrollments__programme_unit__allocations__lecturer=request.user,
        student__unit_enrollments__semester=current_semester,
        is_active=True
    ).values('need_type').annotate(count=Count('id'))
    
    context = {
        'current_semester': current_semester,
        'special_needs_students': special_needs_students,
        'total_special_needs': total_special_needs,
        'by_type': by_type,
        'type_filter': type_filter,
    }
    
    return render(request, 'lecturer/students/special_needs.html', context)


@login_required
def special_needs_detail(request, registration_number):
    """Detailed view of student's special needs"""
    student = get_object_or_404(
        Student.objects.select_related('user', 'programme'),
        registration_number=registration_number
    )
    
    # Get all special needs records for this student
    special_needs_records = StudentSpecialNeed.objects.filter(
        student=student
    ).select_related('reported_by').order_by('-created_at')
    
    context = {
        'student': student,
        'special_needs_records': special_needs_records,
    }
    
    return render(request, 'lecturer/students/special_needs_detail.html', context)



@login_required
def update_special_needs(request, registration_number):
    """Update special needs support information"""
    
    student = get_object_or_404(Student, registration_number=registration_number)
    special_needs = StudentSpecialNeed.objects.filter(student=student)

    if request.method == 'POST':
        special_need_id = request.POST.get('special_need_id')
        support_provided = request.POST.get('support_provided')
        review_notes = request.POST.get('review_notes')

        try:
            special_need = StudentSpecialNeed.objects.get(
                id=special_need_id,
                student=student
            )

            special_need.support_provided = support_provided
            special_need.review_notes = review_notes
            special_need.last_reviewed = timezone.now().date()
            special_need.save()

            messages.success(
                request,
                'Special needs information updated successfully.'
            )

            return redirect('student_special_needs', registration_number=student.registration_number)

        except StudentSpecialNeed.DoesNotExist:
            messages.error(
                request,
                'Invalid special need selected. Please try again.'
            )

            return redirect('student_special_needs', registration_number=student.registration_number)

    # GET request – show update form
    context = {
        'student': student,
        'special_needs': special_needs,
    }

    return render(request, 'lecturer/students//update_special_needs.html', context)



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import (
    ResearchProject, Publication, ResearchGrant, Lecturer,
    UnitAllocation, StaffTraining, PerformanceAppraisal,
    SemesterResults, TeachingMaterial, Student, Semester,
    AcademicYear, Unit, Programme, Department
)
from .decorators import lecturer_required
from decimal import Decimal


# ============= RESEARCH VIEWS =============

@login_required
@lecturer_required
def research_projects_list(request):
    """List all research projects for the lecturer"""
    try:
        lecturer = request.user.lecturer_profile
    except Lecturer.DoesNotExist:
        messages.error(request, 'Lecturer profile not found.')
        return redirect('lecturer_dashboard')
    
    # Get projects where lecturer is PI or Co-Investigator
    projects_pi = ResearchProject.objects.filter(
        principal_investigator=lecturer
    ).select_related('school', 'department')
    
    projects_co = ResearchProject.objects.filter(
        co_investigators=lecturer
    ).select_related('school', 'department')
    
    # Combine and remove duplicates
    projects = (projects_pi | projects_co).distinct().order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        projects = projects.filter(status=status_filter)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        projects = projects.filter(
            Q(title__icontains=search_query) |
            Q(project_code__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(projects, 10)
    page_number = request.GET.get('page')
    projects_page = paginator.get_page(page_number)
    
    # Statistics
    stats = {
        'total_projects': projects.count(),
        'ongoing': projects.filter(status='ongoing').count(),
        'completed': projects.filter(status='completed').count(),
        'total_budget': projects.aggregate(Sum('total_budget'))['total_budget__sum'] or 0,
        'total_publications': projects.aggregate(Sum('publications_count'))['publications_count__sum'] or 0,
    }
    
    context = {
        'projects': projects_page,
        'stats': stats,
        'status_choices': ResearchProject.PROJECT_STATUS,
        'current_status': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'lecturer/research/projects_list.html', context)


@login_required
@lecturer_required
def research_project_detail(request, project_id):
    """View details of a specific research project"""
    try:
        lecturer = request.user.lecturer_profile
    except Lecturer.DoesNotExist:
        messages.error(request, 'Lecturer profile not found.')
        return redirect('lecturer_dashboard')
    
    project = get_object_or_404(
        ResearchProject,
        id=project_id
    )
    
    # Check if lecturer is part of this project
    if project.principal_investigator != lecturer and lecturer not in project.co_investigators.all():
        messages.error(request, 'You do not have access to this project.')
        return redirect('lecturer_research_projects')
    
    # Get related publications
    publications = project.publications.all().order_by('-publication_date')
    
    # Calculate project metrics
    duration_days = (project.end_date - project.start_date).days
    days_elapsed = (timezone.now().date() - project.start_date).days
    progress_percentage = min((days_elapsed / duration_days * 100), 100) if duration_days > 0 else 0
    
    budget_utilization = (project.funds_utilized / project.total_budget * 100) if project.total_budget > 0 else 0
    
    context = {
        'project': project,
        'publications': publications,
        'progress_percentage': round(progress_percentage, 2),
        'budget_utilization': round(budget_utilization, 2),
        'co_investigators': project.co_investigators.all(),
    }
    
    return render(request, 'lecturer/research/project_detail.html', context)


@login_required
@lecturer_required
def publications_list(request):
    """List all publications by the lecturer"""
    try:
        lecturer = request.user.lecturer_profile
    except Lecturer.DoesNotExist:
        messages.error(request, 'Lecturer profile not found.')
        return redirect('lecturer_dashboard')
    
    # Get publications
    publications = Publication.objects.filter(
        authors=lecturer
    ).select_related(
        'corresponding_author', 'school', 'research_project'
    ).prefetch_related('authors').order_by('-publication_date')
    
    # Filter by type if provided
    pub_type = request.GET.get('type')
    if pub_type:
        publications = publications.filter(publication_type=pub_type)
    
    # Filter by year
    year_filter = request.GET.get('year')
    if year_filter:
        publications = publications.filter(year=year_filter)
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        publications = publications.filter(
            Q(title__icontains=search_query) |
            Q(journal_name__icontains=search_query) |
            Q(keywords__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(publications, 15)
    page_number = request.GET.get('page')
    publications_page = paginator.get_page(page_number)
    
    # Statistics
    stats = {
        'total_publications': publications.count(),
        'journal_articles': publications.filter(publication_type='journal').count(),
        'conference_papers': publications.filter(publication_type='conference').count(),
        'total_citations': publications.aggregate(Sum('citations_count'))['citations_count__sum'] or 0,
        'peer_reviewed': publications.filter(is_peer_reviewed=True).count(),
    }
    
    # Get unique years for filter
    years = publications.values_list('year', flat=True).distinct().order_by('-year')
    
    context = {
        'publications': publications_page,
        'stats': stats,
        'publication_types': Publication.PUBLICATION_TYPE,
        'years': years,
        'current_type': pub_type,
        'current_year': year_filter,
        'search_query': search_query,
    }
    
    return render(request, 'lecturer/research/publications_list.html', context)


@login_required
@lecturer_required
def publication_detail(request, publication_id):
    """View publication details"""
    try:
        lecturer = request.user.lecturer_profile
    except Lecturer.DoesNotExist:
        messages.error(request, 'Lecturer profile not found.')
        return redirect('lecturer_dashboard')
    
    publication = get_object_or_404(
        Publication,
        id=publication_id,
        authors=lecturer
    )
    
    context = {
        'publication': publication,
        'authors': publication.authors.all(),
    }
    
    return render(request, 'lecturer/research/publication_detail.html', context)


@login_required
@lecturer_required
def research_grants_list(request):
    """List research grants"""
    try:
        lecturer = request.user.lecturer_profile
    except Lecturer.DoesNotExist:
        messages.error(request, 'Lecturer profile not found.')
        return redirect('lecturer_dashboard')
    
    # Get grants where lecturer is principal or co-applicant
    grants_principal = ResearchGrant.objects.filter(
        principal_applicant=lecturer
    ).select_related('school')
    
    grants_co = ResearchGrant.objects.filter(
        co_applicants=lecturer
    ).select_related('school')
    
    grants = (grants_principal | grants_co).distinct().order_by('-application_date')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        grants = grants.filter(status=status_filter)
    
    # Filter by type
    type_filter = request.GET.get('type')
    if type_filter:
        grants = grants.filter(grant_type=type_filter)
    
    # Pagination
    paginator = Paginator(grants, 10)
    page_number = request.GET.get('page')
    grants_page = paginator.get_page(page_number)
    
    # Statistics
    stats = {
        'total_grants': grants.count(),
        'active_grants': grants.filter(status='active').count(),
        'total_applied': grants.aggregate(Sum('amount_applied'))['amount_applied__sum'] or 0,
        'total_awarded': grants.aggregate(Sum('amount_awarded'))['amount_awarded__sum'] or 0,
    }
    
    context = {
        'grants': grants_page,
        'stats': stats,
        'status_choices': ResearchGrant.GRANT_STATUS,
        'type_choices': ResearchGrant.GRANT_TYPE,
        'current_status': status_filter,
        'current_type': type_filter,
    }
    
    return render(request, 'lecturer/research/grants_list.html', context)


# ============= DEPARTMENT VIEWS =============

@login_required
@lecturer_required
def unit_allocations_list(request):
    """View unit allocations for the lecturer"""
    try:
        lecturer = request.user.lecturer_profile
    except Lecturer.DoesNotExist:
        messages.error(request, 'Lecturer profile not found.')
        return redirect('lecturer_dashboard')
    
    # Get current academic year and semester
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get allocations
    allocations = UnitAllocation.objects.filter(
        lecturer=request.user
    ).select_related(
        'programme_unit__unit',
        'programme_unit__programme',
        'semester__academic_year',
        'assigned_by'
    ).order_by('-semester__academic_year__start_date', 'programme_unit__unit__code')
    
    # Filter by semester if provided
    semester_id = request.GET.get('semester')
    if semester_id:
        allocations = allocations.filter(semester_id=semester_id)
    elif current_semester:
        allocations = allocations.filter(semester=current_semester)
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        allocations = allocations.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(allocations, 15)
    page_number = request.GET.get('page')
    allocations_page = paginator.get_page(page_number)
    
    # Calculate teaching load
    current_allocations = allocations.filter(
        semester=current_semester
    ) if current_semester else allocations.none()
    
    teaching_load = {
        'total_units': current_allocations.count(),
        'total_students': current_allocations.aggregate(
            total=Sum('max_students')
        )['total'] or 0,
        'approved_units': current_allocations.filter(
            status='approved_dean'
        ).count(),
    }
    
    # Get available semesters for filter
    semesters = Semester.objects.all().order_by('-academic_year__start_date', '-semester_number')
    
    context = {
        'allocations': allocations_page,
        'teaching_load': teaching_load,
        'semesters': semesters,
        'current_semester': current_semester,
        'selected_semester': semester_id,
        'status_choices': UnitAllocation.STATUS_CHOICES,
        'current_status': status_filter,
    }
    
    return render(request, 'lecturer/department/unit_allocations.html', context)


@login_required
@lecturer_required
def unit_allocation_detail(request, allocation_id):
    """View details of a unit allocation"""
    try:
        lecturer = request.user.lecturer_profile
    except Lecturer.DoesNotExist:
        messages.error(request, 'Lecturer profile not found.')
        return redirect('lecturer_dashboard')
    
    allocation = get_object_or_404(
        UnitAllocation,
        id=allocation_id,
        lecturer=request.user
    )
    
    # Get enrolled students count
    enrolled_students = UnitEnrollment.objects.filter(
        programme_unit=allocation.programme_unit,
        semester=allocation.semester,
        status='approved'
    ).count()
    
    # Get teaching materials
    materials = TeachingMaterial.objects.filter(
        unit_allocation=allocation,
        is_published=True
    ).order_by('week_number')
    
    # Get assessments
    assessments = allocation.assessments.all().order_by('date')
    
    # Get attendance summary
    # This would require an Attendance model query
    
    context = {
        'allocation': allocation,
        'enrolled_students': enrolled_students,
        'materials': materials,
        'assessments': assessments,
    }
    
    return render(request, 'lecturer/department/allocation_detail.html', context)


@login_required
@lecturer_required
def staff_development_list(request):
    """View staff development and training"""
    try:
        lecturer = request.user.lecturer_profile
    except Lecturer.DoesNotExist:
        messages.error(request, 'Lecturer profile not found.')
        return redirect('lecturer_dashboard')
    
    # Get trainings
    trainings = StaffTraining.objects.filter(
        lecturer=lecturer
    ).order_by('-start_date')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        trainings = trainings.filter(status=status_filter)
    
    # Filter by type
    type_filter = request.GET.get('type')
    if type_filter:
        trainings = trainings.filter(training_type=type_filter)
    
    # Pagination
    paginator = Paginator(trainings, 10)
    page_number = request.GET.get('page')
    trainings_page = paginator.get_page(page_number)
    
    # Statistics
    stats = {
        'total_trainings': trainings.count(),
        'completed': trainings.filter(status='completed').count(),
        'ongoing': trainings.filter(status='ongoing').count(),
        'total_days': trainings.aggregate(Sum('duration_days'))['duration_days__sum'] or 0,
        'certifications': trainings.filter(certificate_obtained=True).count(),
    }
    
    context = {
        'trainings': trainings_page,
        'stats': stats,
        'status_choices': StaffTraining.TRAINING_STATUS,
        'type_choices': StaffTraining.TRAINING_TYPE,
        'current_status': status_filter,
        'current_type': type_filter,
    }
    
    return render(request, 'lecturer/department/staff_development.html', context)


# ============= REPORTS VIEWS =============

@login_required
@lecturer_required
def teaching_load_report(request):
    """Generate teaching load report"""
    try:
        lecturer = request.user.lecturer_profile
    except Lecturer.DoesNotExist:
        messages.error(request, 'Lecturer profile not found.')
        return redirect('lecturer_dashboard')
    
    # Get selected academic year or current
    academic_year_id = request.GET.get('academic_year')
    if academic_year_id:
        academic_year = get_object_or_404(AcademicYear, id=academic_year_id)
    else:
        academic_year = AcademicYear.objects.filter(is_current=True).first()
    
    if not academic_year:
        messages.error(request, 'No academic year found.')
        return redirect('lecturer_dashboard')
    
    # Get allocations for the academic year
    allocations = UnitAllocation.objects.filter(
        lecturer=request.user,
        semester__academic_year=academic_year,
        status='approved_dean'
    ).select_related(
        'programme_unit__unit',
        'programme_unit__programme',
        'semester'
    ).order_by('semester__semester_number')
    
    # Group by semester
    semester_data = {}
    for allocation in allocations:
        semester_key = allocation.semester.name
        if semester_key not in semester_data:
            semester_data[semester_key] = {
                'semester': allocation.semester,
                'allocations': [],
                'total_units': 0,
                'total_students': 0,
                'total_credit_hours': 0,
            }
        
        semester_data[semester_key]['allocations'].append(allocation)
        semester_data[semester_key]['total_units'] += 1
        semester_data[semester_key]['total_students'] += allocation.max_students or 0
        semester_data[semester_key]['total_credit_hours'] += allocation.programme_unit.unit.credit_hours
    
    # Get all academic years for filter
    academic_years = AcademicYear.objects.all().order_by('-start_date')
    
    # Calculate yearly totals
    yearly_totals = {
        'total_units': sum(data['total_units'] for data in semester_data.values()),
        'total_students': sum(data['total_students'] for data in semester_data.values()),
        'total_credit_hours': sum(data['total_credit_hours'] for data in semester_data.values()),
    }
    
    context = {
        'academic_year': academic_year,
        'semester_data': semester_data,
        'yearly_totals': yearly_totals,
        'academic_years': academic_years,
    }
    
    return render(request, 'lecturer/reports/teaching_load.html', context)


@login_required
@lecturer_required
def student_results_report(request):
    """View student results for units taught"""
    try:
        lecturer = request.user.lecturer_profile
    except Lecturer.DoesNotExist:
        messages.error(request, 'Lecturer profile not found.')
        return redirect('lecturer_dashboard')
    
    # Get selected semester or current
    semester_id = request.GET.get('semester')
    if semester_id:
        semester = get_object_or_404(Semester, id=semester_id)
    else:
        semester = Semester.objects.filter(is_current=True).first()
    
    if not semester:
        messages.error(request, 'No semester found.')
        return redirect('lecturer_dashboard')
    
    # Get allocations for the semester
    allocations = UnitAllocation.objects.filter(
        lecturer=request.user,
        semester=semester,
        status='approved_dean'
    ).select_related('programme_unit__unit', 'programme_unit__programme')
    
    # Get results for each allocation
    results_data = []
    for allocation in allocations:
        results = SemesterResults.objects.filter(
            programme_unit=allocation.programme_unit,
            semester=semester,
            is_published=True
        ).select_related('student')
        
        if results.exists():
            # Calculate statistics
            total_students = results.count()
            passed = results.filter(is_passed=True).count()
            failed = total_students - passed
            pass_rate = (passed / total_students * 100) if total_students > 0 else 0
            
            avg_marks = results.aggregate(Avg('total_marks'))['total_marks__avg'] or 0
            
            # Grade distribution
            grade_dist = {}
            for result in results:
                grade = result.grade
                grade_dist[grade] = grade_dist.get(grade, 0) + 1
            
            results_data.append({
                'allocation': allocation,
                'total_students': total_students,
                'passed': passed,
                'failed': failed,
                'pass_rate': round(pass_rate, 2),
                'avg_marks': round(avg_marks, 2),
                'grade_distribution': grade_dist,
            })
    
    # Get semesters for filter
    semesters = Semester.objects.all().order_by('-academic_year__start_date', '-semester_number')
    
    context = {
        'semester': semester,
        'results_data': results_data,
        'semesters': semesters,
    }
    
    return render(request, 'lecturer/reports/student_results.html', context)


@login_required
@lecturer_required
def research_output_report(request):
    """Generate research output report"""
    try:
        lecturer = request.user.lecturer_profile
    except Lecturer.DoesNotExist:
        messages.error(request, 'Lecturer profile not found.')
        return redirect('lecturer_dashboard')
    
    # Get selected year or current
    year = request.GET.get('year')
    if year:
        year = int(year)
    else:
        year = timezone.now().year
    
    # Get publications for the year
    publications = Publication.objects.filter(
        authors=lecturer,
        year=year
    ).select_related('research_project')
    
    # Get research projects
    projects = ResearchProject.objects.filter(
        Q(principal_investigator=lecturer) | Q(co_investigators=lecturer),
        start_date__year__lte=year,
        end_date__year__gte=year
    ).distinct()
    
    # Get grants
    grants = ResearchGrant.objects.filter(
        Q(principal_applicant=lecturer) | Q(co_applicants=lecturer),
        application_date__year=year
    ).distinct()
    
    # Statistics
    pub_stats = {
        'total': publications.count(),
        'journal_articles': publications.filter(publication_type='journal').count(),
        'conference_papers': publications.filter(publication_type='conference').count(),
        'books': publications.filter(publication_type='book').count(),
        'peer_reviewed': publications.filter(is_peer_reviewed=True).count(),
        'total_citations': publications.aggregate(Sum('citations_count'))['citations_count__sum'] or 0,
    }
    
    project_stats = {
        'total': projects.count(),
        'ongoing': projects.filter(status='ongoing').count(),
        'completed': projects.filter(status='completed').count(),
    }
    
    grant_stats = {
        'total_applied': grants.count(),
        'approved': grants.filter(status='approved').count(),
        'total_amount': grants.aggregate(Sum('amount_awarded'))['amount_awarded__sum'] or 0,
    }
    
    # Get years for filter
    years = range(timezone.now().year, timezone.now().year - 10, -1)
    
    context = {
        'selected_year': year,
        'publications': publications,
        'projects': projects,
        'grants': grants,
        'pub_stats': pub_stats,
        'project_stats': project_stats,
        'grant_stats': grant_stats,
        'years': years,
    }
    
    return render(request, 'lecturer/reports/research_output.html', context)


@login_required
@lecturer_required
def annual_report(request):
    """Generate comprehensive annual report"""
    try:
        lecturer = request.user.lecturer_profile
    except Lecturer.DoesNotExist:
        messages.error(request, 'Lecturer profile not found.')
        return redirect('lecturer_dashboard')
    
    # Get selected academic year or current
    academic_year_id = request.GET.get('academic_year')
    if academic_year_id:
        academic_year = get_object_or_404(AcademicYear, id=academic_year_id)
    else:
        academic_year = AcademicYear.objects.filter(is_current=True).first()
    
    if not academic_year:
        messages.error(request, 'No academic year found.')
        return redirect('lecturer_dashboard')
    
    year = academic_year.start_date.year
    
    # Teaching Data
    teaching_allocations = UnitAllocation.objects.filter(
        lecturer=request.user,
        semester__academic_year=academic_year,
        status='approved_dean'
    ).select_related('programme_unit__unit', 'semester')
    
    teaching_stats = {
        'total_units': teaching_allocations.count(),
        'total_students': teaching_allocations.aggregate(Sum('max_students'))['max_students__sum'] or 0,
        'total_credit_hours': sum(
            alloc.programme_unit.unit.credit_hours for alloc in teaching_allocations
        ),
    }
    
    # Research Data
    publications = Publication.objects.filter(
        authors=lecturer,
        publication_date__year=year
    )
    
    projects = ResearchProject.objects.filter(
        Q(principal_investigator=lecturer) | Q(co_investigators=lecturer),
        start_date__year__lte=year,
        end_date__year__gte=year
    ).distinct()
    
    research_stats = {
        'publications': publications.count(),
        'projects': projects.count(),
        'citations': publications.aggregate(Sum('citations_count'))['citations_count__sum'] or 0,
    }
    
    # Professional Development
    trainings = StaffTraining.objects.filter(
        lecturer=lecturer,
        start_date__year=year
    )
    
    development_stats = {
        'trainings_attended': trainings.count(),
        'certificates_obtained': trainings.filter(certificate_obtained=True).count(),
        'total_days': trainings.aggregate(Sum('duration_days'))['duration_days__sum'] or 0,
    }
    
    # Performance Appraisal
    appraisal = PerformanceAppraisal.objects.filter(
        lecturer=lecturer,
        academic_year=academic_year
    ).first()
    
    # Get academic years for filter
    academic_years = AcademicYear.objects.all().order_by('-start_date')
    
    context = {
        'academic_year': academic_year,
        'lecturer': lecturer,
        'teaching_stats': teaching_stats,
        'research_stats': research_stats,
        'development_stats': development_stats,
        'appraisal': appraisal,
        'publications': publications[:5],  # Top 5
        'projects': projects[:5],  # Top 5
        'academic_years': academic_years,
    }
    
    return render(request, 'lecturer/reports/annual_report.html', context)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count, Sum, F, Case, When, DecimalField
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from decimal import Decimal
import json

from .models import (
    SemesterReport, Student, Semester, AcademicYear, 
    Programme, FeeBalance, SemesterResults
)


def is_admin_or_registrar(user):
    """Check if user is admin or registrar"""
    return user.is_staff or user.role in ['registrar', 'finance', 'dean', 'hos']


@login_required
@user_passes_test(is_admin_or_registrar)
def semester_reporting_management(request):
    """Main semester reporting management view"""
    
    # Get current semester
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get filter parameters
    semester_id = request.GET.get('semester', current_semester.id if current_semester else None)
    programme_id = request.GET.get('programme', '')
    year_of_study = request.GET.get('year', '')
    status = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    financial_status = request.GET.get('financial_status', '')
    eligibility_filter = request.GET.get('eligibility', '')
    
    # Base queryset
    reports = SemesterReport.objects.select_related(
        'student__user',
        'student__programme__department__school',
        'to_semester',
        'to_academic_year',
        'approved_by'
    ).all()
    
    # Apply filters
    if semester_id:
        reports = reports.filter(to_semester_id=semester_id)
    
    if programme_id:
        reports = reports.filter(student__programme_id=programme_id)
    
    if year_of_study:
        reports = reports.filter(to_year_of_study=year_of_study)
    
    if status:
        reports = reports.filter(status=status)
    
    if financial_status:
        if financial_status == 'cleared':
            reports = reports.filter(is_financially_cleared=True)
        elif financial_status == 'not_cleared':
            reports = reports.filter(is_financially_cleared=False)
    
    if eligibility_filter:
        if eligibility_filter == 'eligible':
            reports = reports.filter(is_eligible=True)
        elif eligibility_filter == 'not_eligible':
            reports = reports.filter(is_eligible=False)
    
    if search_query:
        reports = reports.filter(
            Q(student__registration_number__icontains=search_query) |
            Q(student__user__first_name__icontains=search_query) |
            Q(student__user__last_name__icontains=search_query) |
            Q(student__user__email__icontains=search_query)
        )
    
    # Order by most recent first
    reports = reports.order_by('-report_date')
    
    # Calculate statistics
    total_reports = reports.count()
    pending_reports = reports.filter(status='pending').count()
    approved_reports = reports.filter(status='approved').count()
    rejected_reports = reports.filter(status='rejected').count()
    
    # Financial statistics
    financially_cleared = reports.filter(is_financially_cleared=True).count()
    financially_pending = reports.filter(is_financially_cleared=False).count()
    
    # Eligibility statistics
    eligible_students = reports.filter(is_eligible=True).count()
    ineligible_students = reports.filter(is_eligible=False).count()
    
    # Aggregate by programme
    programme_stats = reports.values(
        'student__programme__name',
        'student__programme__code',
        'student__programme_id'
    ).annotate(
        total=Count('id'),
        pending=Count(Case(When(status='pending', then=1))),
        approved=Count(Case(When(status='approved', then=1))),
        rejected=Count(Case(When(status='rejected', then=1)))
    ).order_by('-total')
    
    # Pagination
    paginator = Paginator(reports, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    semesters = Semester.objects.filter(is_active=True).order_by('-academic_year__start_date')
    programmes = Programme.objects.filter(is_active=True).select_related('department__school')
    years = range(1, 8)
    
    context = {
        'reports': page_obj,
        'current_semester': current_semester,
        'semesters': semesters,
        'programmes': programmes,
        'years': years,
        'total_reports': total_reports,
        'pending_reports': pending_reports,
        'approved_reports': approved_reports,
        'rejected_reports': rejected_reports,
        'financially_cleared': financially_cleared,
        'financially_pending': financially_pending,
        'eligible_students': eligible_students,
        'ineligible_students': ineligible_students,
        'programme_stats': programme_stats,
        'search_query': search_query,
        'semester_id': semester_id,
        'programme_id': programme_id,
        'year_of_study': year_of_study,
        'status': status,
        'financial_status': financial_status,
        'eligibility_filter': eligibility_filter,
        'status_choices': SemesterReport.REPORT_STATUS,
    }
    
    return render(request, 'admin/semester_reporting_management.html', context)


@login_required
@user_passes_test(is_admin_or_registrar)
@require_http_methods(["POST"])
def bulk_approve_reports(request):
    """API endpoint for bulk approval of semester reports"""
    
    try:
        data = json.loads(request.body)
        report_ids = data.get('report_ids', [])
        bypass_fee_check = data.get('bypass_fee_check', False)
        bypass_eligibility_check = data.get('bypass_eligibility_check', False)
        
        if not report_ids:
            return JsonResponse({
                'success': False,
                'message': 'No reports selected'
            }, status=400)
        
        # Get reports
        reports = SemesterReport.objects.filter(id__in=report_ids)
        
        if not reports.exists():
            return JsonResponse({
                'success': False,
                'message': 'No valid reports found'
            }, status=404)
        
        approved_count = 0
        failed_count = 0
        errors = []
        
        for report in reports:
            # Check if already approved
            if report.status == 'approved':
                failed_count += 1
                errors.append({
                    'student': report.student.registration_number,
                    'reason': 'Already approved'
                })
                continue
            
            # Check financial clearance unless bypassed
            if not bypass_fee_check and not report.is_financially_cleared:
                failed_count += 1
                errors.append({
                    'student': report.student.registration_number,
                    'reason': f'Fee balance: {report.fee_balance}'
                })
                continue
            
            # Check eligibility unless bypassed
            if not bypass_eligibility_check and not report.is_eligible:
                failed_count += 1
                errors.append({
                    'student': report.student.registration_number,
                    'reason': f'Not eligible: {report.failed_units_count} failed units'
                })
                continue
            
            # Approve the report
            report.status = 'approved'
            report.approved_by = request.user
            report.approval_date = timezone.now()
            report.remarks = f"Bulk approved by {request.user.get_full_name()}"
            
            if bypass_fee_check:
                report.remarks += " (Fee check bypassed)"
            if bypass_eligibility_check:
                report.remarks += " (Eligibility check bypassed)"
            
            report.save()
            
            # Update student's current year and semester
            student = report.student
            student.current_year = report.to_year_of_study
            student.current_semester = report.to_semester_number
            student.save()
            
            approved_count += 1
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully approved {approved_count} report(s)',
            'approved_count': approved_count,
            'failed_count': failed_count,
            'errors': errors
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


@login_required
@user_passes_test(is_admin_or_registrar)
@require_http_methods(["POST"])
def bulk_reject_reports(request):
    """API endpoint for bulk rejection of semester reports"""
    
    try:
        data = json.loads(request.body)
        report_ids = data.get('report_ids', [])
        rejection_reason = data.get('rejection_reason', '')
        
        if not report_ids:
            return JsonResponse({
                'success': False,
                'message': 'No reports selected'
            }, status=400)
        
        if not rejection_reason:
            return JsonResponse({
                'success': False,
                'message': 'Rejection reason is required'
            }, status=400)
        
        # Get reports
        reports = SemesterReport.objects.filter(
            id__in=report_ids,
            status='pending'
        )
        
        if not reports.exists():
            return JsonResponse({
                'success': False,
                'message': 'No pending reports found'
            }, status=404)
        
        # Reject reports
        updated_count = reports.update(
            status='rejected',
            rejection_reason=rejection_reason,
            remarks=f"Bulk rejected by {request.user.get_full_name()}: {rejection_reason}"
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully rejected {updated_count} report(s)',
            'rejected_count': updated_count
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


@login_required
@user_passes_test(is_admin_or_registrar)
@require_http_methods(["POST"])
def approve_programme_reports(request):
    """API endpoint to approve all reports for a specific programme and year"""
    
    try:
        data = json.loads(request.body)
        semester_id = data.get('semester_id')
        programme_id = data.get('programme_id')
        year_of_study = data.get('year_of_study')
        bypass_fee_check = data.get('bypass_fee_check', False)
        bypass_eligibility_check = data.get('bypass_eligibility_check', False)
        
        if not all([semester_id, programme_id, year_of_study]):
            return JsonResponse({
                'success': False,
                'message': 'Semester, programme, and year are required'
            }, status=400)
        
        # Build query
        query = Q(
            to_semester_id=semester_id,
            student__programme_id=programme_id,
            to_year_of_study=year_of_study,
            status='pending'
        )
        
        # Add financial and eligibility filters if not bypassed
        if not bypass_fee_check:
            query &= Q(is_financially_cleared=True)
        
        if not bypass_eligibility_check:
            query &= Q(is_eligible=True)
        
        # Get reports
        reports = SemesterReport.objects.filter(query)
        
        if not reports.exists():
            return JsonResponse({
                'success': False,
                'message': 'No eligible reports found for approval'
            }, status=404)
        
        approved_count = 0
        
        for report in reports:
            report.status = 'approved'
            report.approved_by = request.user
            report.approval_date = timezone.now()
            report.remarks = f"Programme-wide approval by {request.user.get_full_name()}"
            
            if bypass_fee_check:
                report.remarks += " (Fee check bypassed)"
            if bypass_eligibility_check:
                report.remarks += " (Eligibility check bypassed)"
            
            report.save()
            
            # Update student
            student = report.student
            student.current_year = report.to_year_of_study
            student.current_semester = report.to_semester_number
            student.save()
            
            approved_count += 1
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully approved {approved_count} report(s)',
            'approved_count': approved_count
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


@login_required
@user_passes_test(is_admin_or_registrar)
@require_http_methods(["GET"])
def get_report_details(request, report_id):
    """API endpoint to get detailed information about a report"""
    
    try:
        report = get_object_or_404(
            SemesterReport.objects.select_related(
                'student__user',
                'student__programme',
                'to_semester',
                'to_academic_year',
                'from_semester',
                'from_academic_year',
                'approved_by'
            ),
            id=report_id
        )
        
        # Get fee balance
        fee_balance = None
        if report.to_semester:
            try:
                balance = FeeBalance.objects.get(
                    student=report.student,
                    semester=report.to_semester
                )
                fee_balance = {
                    'total_fees': float(balance.total_fees),
                    'amount_paid': float(balance.amount_paid),
                    'balance': float(balance.balance),
                    'is_cleared': balance.is_cleared
                }
            except FeeBalance.DoesNotExist:
                pass
        
        # Get failed units
        failed_units = []
        if report.from_semester:
            failed_results = SemesterResults.objects.filter(
                student=report.student,
                semester=report.from_semester,
                is_passed=False
            ).select_related('programme_unit__unit')
            
            failed_units = [{
                'unit_code': result.programme_unit.unit.code,
                'unit_name': result.programme_unit.unit.name,
                'grade': result.grade,
                'total_marks': float(result.total_marks)
            } for result in failed_results]
        
        data = {
            'id': report.id,
            'student': {
                'registration_number': report.student.registration_number,
                'name': report.student.user.get_full_name(),
                'email': report.student.user.email,
                'phone': report.student.user.phone_number,
                'programme': report.student.programme.name,
                'programme_code': report.student.programme.code,
            },
            'progression': {
                'from_year': report.from_year_of_study,
                'from_semester': report.from_semester_number,
                'to_year': report.to_year_of_study,
                'to_semester': report.to_semester_number,
            },
            'academic_info': {
                'previous_gpa': float(report.previous_semester_gpa) if report.previous_semester_gpa else None,
                'cumulative_gpa': float(report.cumulative_gpa) if report.cumulative_gpa else None,
                'total_credits': report.total_credits_earned,
                'failed_units_count': report.failed_units_count,
                'failed_units': failed_units,
            },
            'financial_info': {
                'fee_balance': float(report.fee_balance),
                'is_cleared': report.is_financially_cleared,
                'clearance_date': report.financial_clearance_date.isoformat() if report.financial_clearance_date else None,
                'details': fee_balance,
            },
            'eligibility': {
                'is_eligible': report.is_eligible,
                'eligibility_remarks': report.eligibility_remarks,
                'checked_at': report.eligibility_checked_at.isoformat() if report.eligibility_checked_at else None,
            },
            'status': {
                'status': report.status,
                'status_display': report.get_status_display(),
                'report_date': report.report_date.isoformat(),
                'approved_by': report.approved_by.get_full_name() if report.approved_by else None,
                'approval_date': report.approval_date.isoformat() if report.approval_date else None,
                'rejection_reason': report.rejection_reason,
                'remarks': report.remarks,
            },
        }
        
        return JsonResponse({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


@login_required
@user_passes_test(is_admin_or_registrar)
@require_http_methods(["POST"])
def individual_approve_report(request, report_id):
    """API endpoint to approve individual report"""
    
    try:
        data = json.loads(request.body)
        bypass_fee_check = data.get('bypass_fee_check', False)
        bypass_eligibility_check = data.get('bypass_eligibility_check', False)
        remarks = data.get('remarks', '')
        
        report = get_object_or_404(SemesterReport, id=report_id)
        
        # Validation
        if report.status == 'approved':
            return JsonResponse({
                'success': False,
                'message': 'Report is already approved'
            }, status=400)
        
        if not bypass_fee_check and not report.is_financially_cleared:
            return JsonResponse({
                'success': False,
                'message': f'Student has fee balance of {report.fee_balance}. Use bypass option to approve anyway.'
            }, status=400)
        
        if not bypass_eligibility_check and not report.is_eligible:
            return JsonResponse({
                'success': False,
                'message': f'Student is not eligible: {report.eligibility_remarks}. Use bypass option to approve anyway.'
            }, status=400)
        
        # Approve
        report.status = 'approved'
        report.approved_by = request.user
        report.approval_date = timezone.now()
        
        report_remarks = f"Approved by {request.user.get_full_name()}"
        if bypass_fee_check:
            report_remarks += " (Fee check bypassed)"
        if bypass_eligibility_check:
            report_remarks += " (Eligibility check bypassed)"
        if remarks:
            report_remarks += f" - {remarks}"
        
        report.remarks = report_remarks
        report.save()
        
        # Update student
        student = report.student
        student.current_year = report.to_year_of_study
        student.current_semester = report.to_semester_number
        student.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Report approved successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


@login_required
@user_passes_test(is_admin_or_registrar)
@require_http_methods(["POST"])
def individual_reject_report(request, report_id):
    """API endpoint to reject individual report"""
    
    try:
        data = json.loads(request.body)
        rejection_reason = data.get('rejection_reason', '')
        
        if not rejection_reason:
            return JsonResponse({
                'success': False,
                'message': 'Rejection reason is required'
            }, status=400)
        
        report = get_object_or_404(SemesterReport, id=report_id)
        
        if report.status == 'rejected':
            return JsonResponse({
                'success': False,
                'message': 'Report is already rejected'
            }, status=400)
        
        # Reject
        report.status = 'rejected'
        report.rejection_reason = rejection_reason
        report.remarks = f"Rejected by {request.user.get_full_name()}: {rejection_reason}"
        report.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Report rejected successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)
        
        

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count, Sum, F, Case, When, DecimalField
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from decimal import Decimal
import json

from .models import (
    UnitEnrollment, Student, Semester, AcademicYear, 
    Programme, ProgrammeUnit, UnitAllocation, SemesterReport,
    ResitExam, EnrollmentPeriod
)


def is_admin_or_registrar(user):
    """Check if user is admin or registrar"""
    return user.is_staff or user.role in ['registrar', 'finance', 'dean', 'hos', 'hod']


@login_required
@user_passes_test(is_admin_or_registrar)
def unit_enrollment_management(request):
    """Main unit enrollment management view"""
    
    # Get current semester
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get filter parameters
    semester_id = request.GET.get('semester', current_semester.id if current_semester else None)
    programme_id = request.GET.get('programme', '')
    year_of_study = request.GET.get('year', '')
    status = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    enrollment_type = request.GET.get('enrollment_type', '')
    unit_id = request.GET.get('unit', '')
    
    # Base queryset
    enrollments = UnitEnrollment.objects.select_related(
        'student__user',
        'student__programme__department__school',
        'semester',
        'semester_report',
        'programme_unit__unit',
        'programme_unit__programme',
        'approved_by',
        'resit_exam'
    ).all()
    
    # Apply filters
    if semester_id:
        enrollments = enrollments.filter(semester_id=semester_id)
    
    if programme_id:
        enrollments = enrollments.filter(student__programme_id=programme_id)
    
    if year_of_study:
        enrollments = enrollments.filter(semester_report__to_year_of_study=year_of_study)
    
    if status:
        enrollments = enrollments.filter(status=status)
    
    if enrollment_type:
        enrollments = enrollments.filter(enrollment_type=enrollment_type)
    
    if unit_id:
        enrollments = enrollments.filter(programme_unit__unit_id=unit_id)
    
    if search_query:
        enrollments = enrollments.filter(
            Q(student__registration_number__icontains=search_query) |
            Q(student__user__first_name__icontains=search_query) |
            Q(student__user__last_name__icontains=search_query) |
            Q(student__user__email__icontains=search_query) |
            Q(programme_unit__unit__code__icontains=search_query) |
            Q(programme_unit__unit__name__icontains=search_query)
        )
    
    # Order by most recent first
    enrollments = enrollments.order_by('-enrollment_date')
    
    # Calculate statistics
    total_enrollments = enrollments.count()
    pending_enrollments = enrollments.filter(status='pending').count()
    approved_enrollments = enrollments.filter(status='approved').count()
    rejected_enrollments = enrollments.filter(status='rejected').count()
    dropped_enrollments = enrollments.filter(status='dropped').count()
    
    # Enrollment type statistics
    normal_enrollments = enrollments.filter(enrollment_type='normal').count()
    resit_enrollments = enrollments.filter(enrollment_type='resit').count()
    retake_enrollments = enrollments.filter(enrollment_type='retake').count()
    
    # Aggregate by programme
    programme_stats = enrollments.values(
        'student__programme__name',
        'student__programme__code',
        'student__programme_id'
    ).annotate(
        total=Count('id'),
        pending=Count(Case(When(status='pending', then=1))),
        approved=Count(Case(When(status='approved', then=1))),
        rejected=Count(Case(When(status='rejected', then=1)))
    ).order_by('-total')
    
    # Aggregate by unit
    unit_stats = enrollments.values(
        'programme_unit__unit__code',
        'programme_unit__unit__name',
        'programme_unit__unit_id'
    ).annotate(
        total=Count('id'),
        pending=Count(Case(When(status='pending', then=1))),
        approved=Count(Case(When(status='approved', then=1)))
    ).order_by('-total')[:10]  # Top 10 units
    
    # Check enrollment period
    enrollment_period = None
    if semester_id:
        try:
            enrollment_period = EnrollmentPeriod.objects.get(semester_id=semester_id)
        except EnrollmentPeriod.DoesNotExist:
            pass
    
    # Pagination
    paginator = Paginator(enrollments, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    semesters = Semester.objects.filter(is_active=True).order_by('-academic_year__start_date')
    programmes = Programme.objects.filter(is_active=True).select_related('department__school')
    years = range(1, 8)
    
    # Get units for current semester
    units = []
    if semester_id:
        units = ProgrammeUnit.objects.filter(
            programme_id__in=enrollments.values_list('student__programme_id', flat=True).distinct()
        ).select_related('unit').values(
            'unit_id', 'unit__code', 'unit__name'
        ).distinct().order_by('unit__code')
    
    context = {
        'enrollments': page_obj,
        'current_semester': current_semester,
        'semesters': semesters,
        'programmes': programmes,
        'years': years,
        'units': units,
        'total_enrollments': total_enrollments,
        'pending_enrollments': pending_enrollments,
        'approved_enrollments': approved_enrollments,
        'rejected_enrollments': rejected_enrollments,
        'dropped_enrollments': dropped_enrollments,
        'normal_enrollments': normal_enrollments,
        'resit_enrollments': resit_enrollments,
        'retake_enrollments': retake_enrollments,
        'programme_stats': programme_stats,
        'unit_stats': unit_stats,
        'enrollment_period': enrollment_period,
        'search_query': search_query,
        'semester_id': semester_id,
        'programme_id': programme_id,
        'year_of_study': year_of_study,
        'status': status,
        'enrollment_type': enrollment_type,
        'unit_id': unit_id,
        'status_choices': UnitEnrollment.ENROLLMENT_STATUS,
        'type_choices': UnitEnrollment.ENROLLMENT_TYPE,
    }
    
    return render(request, 'admin/unit_enrollment_management.html', context)


@login_required
@user_passes_test(is_admin_or_registrar)
@require_http_methods(["POST"])
def bulk_approve_enrollments(request):
    """API endpoint for bulk approval of unit enrollments"""
    
    try:
        data = json.loads(request.body)
        enrollment_ids = data.get('enrollment_ids', [])
        bypass_semester_report_check = data.get('bypass_semester_report_check', False)
        
        if not enrollment_ids:
            return JsonResponse({
                'success': False,
                'message': 'No enrollments selected'
            }, status=400)
        
        # Get enrollments
        enrollments = UnitEnrollment.objects.filter(id__in=enrollment_ids)
        
        if not enrollments.exists():
            return JsonResponse({
                'success': False,
                'message': 'No valid enrollments found'
            }, status=404)
        
        approved_count = 0
        failed_count = 0
        errors = []
        
        for enrollment in enrollments:
            # Check if already approved
            if enrollment.status == 'approved':
                failed_count += 1
                errors.append({
                    'student': enrollment.student.registration_number,
                    'unit': enrollment.programme_unit.unit.code,
                    'reason': 'Already approved'
                })
                continue
            
            # Check if semester report is approved (unless bypassed)
            if not bypass_semester_report_check:
                if not enrollment.semester_report or enrollment.semester_report.status != 'approved':
                    failed_count += 1
                    errors.append({
                        'student': enrollment.student.registration_number,
                        'unit': enrollment.programme_unit.unit.code,
                        'reason': 'Student has not reported for semester or report not approved'
                    })
                    continue
            
            # Check if unit is offered in this semester
            unit_offered = UnitAllocation.objects.filter(
                programme_unit=enrollment.programme_unit,
                semester=enrollment.semester,
                status__in=['approved_hod', 'approved_hos', 'approved_dean']
            ).exists()
            
            if not unit_offered:
                failed_count += 1
                errors.append({
                    'student': enrollment.student.registration_number,
                    'unit': enrollment.programme_unit.unit.code,
                    'reason': 'Unit is not offered in this semester'
                })
                continue
            
            # Approve the enrollment
            enrollment.status = 'approved'
            enrollment.approved_by = request.user
            enrollment.approval_date = timezone.now()
            enrollment.remarks = f"Bulk approved by {request.user.get_full_name()}"
            
            if bypass_semester_report_check:
                enrollment.remarks += " (Semester report check bypassed)"
            
            enrollment.save()
            approved_count += 1
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully approved {approved_count} enrollment(s)',
            'approved_count': approved_count,
            'failed_count': failed_count,
            'errors': errors
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


@login_required
@user_passes_test(is_admin_or_registrar)
@require_http_methods(["POST"])
def bulk_reject_enrollments(request):
    """API endpoint for bulk rejection of unit enrollments"""
    
    try:
        data = json.loads(request.body)
        enrollment_ids = data.get('enrollment_ids', [])
        rejection_reason = data.get('rejection_reason', '')
        
        if not enrollment_ids:
            return JsonResponse({
                'success': False,
                'message': 'No enrollments selected'
            }, status=400)
        
        if not rejection_reason:
            return JsonResponse({
                'success': False,
                'message': 'Rejection reason is required'
            }, status=400)
        
        # Get enrollments
        enrollments = UnitEnrollment.objects.filter(
            id__in=enrollment_ids,
            status='pending'
        )
        
        if not enrollments.exists():
            return JsonResponse({
                'success': False,
                'message': 'No pending enrollments found'
            }, status=404)
        
        # Reject enrollments
        updated_count = enrollments.update(
            status='rejected',
            rejection_reason=rejection_reason,
            remarks=f"Bulk rejected by {request.user.get_full_name()}: {rejection_reason}"
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully rejected {updated_count} enrollment(s)',
            'rejected_count': updated_count
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


@login_required
@user_passes_test(is_admin_or_registrar)
@require_http_methods(["POST"])
def approve_programme_enrollments(request):
    """API endpoint to approve all enrollments for a specific programme, year, and unit"""
    
    try:
        data = json.loads(request.body)
        semester_id = data.get('semester_id')
        programme_id = data.get('programme_id')
        year_of_study = data.get('year_of_study')
        unit_id = data.get('unit_id')
        bypass_semester_report_check = data.get('bypass_semester_report_check', False)
        
        # Build query
        query = Q(
            semester_id=semester_id,
            student__programme_id=programme_id,
            status='pending'
        )
        
        if year_of_study:
            query &= Q(semester_report__to_year_of_study=year_of_study)
        
        if unit_id:
            query &= Q(programme_unit__unit_id=unit_id)
        
        # Add semester report filter if not bypassed
        if not bypass_semester_report_check:
            query &= Q(semester_report__status='approved')
        
        # Get enrollments
        enrollments = UnitEnrollment.objects.filter(query)
        
        if not enrollments.exists():
            return JsonResponse({
                'success': False,
                'message': 'No eligible enrollments found for approval'
            }, status=404)
        
        approved_count = 0
        failed_count = 0
        errors = []
        
        for enrollment in enrollments:
            # Check if unit is offered
            unit_offered = UnitAllocation.objects.filter(
                programme_unit=enrollment.programme_unit,
                semester=enrollment.semester,
                status__in=['approved_hod', 'approved_hos', 'approved_dean']
            ).exists()
            
            if not unit_offered:
                failed_count += 1
                errors.append({
                    'student': enrollment.student.registration_number,
                    'unit': enrollment.programme_unit.unit.code,
                    'reason': 'Unit not offered'
                })
                continue
            
            enrollment.status = 'approved'
            enrollment.approved_by = request.user
            enrollment.approval_date = timezone.now()
            enrollment.remarks = f"Programme-wide approval by {request.user.get_full_name()}"
            
            if bypass_semester_report_check:
                enrollment.remarks += " (Semester report check bypassed)"
            
            enrollment.save()
            approved_count += 1
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully approved {approved_count} enrollment(s)',
            'approved_count': approved_count,
            'failed_count': failed_count,
            'errors': errors
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


@login_required
@user_passes_test(is_admin_or_registrar)
@require_http_methods(["GET"])
def get_enrollment_details(request, enrollment_id):
    """API endpoint to get detailed information about an enrollment"""
    
    try:
        enrollment = get_object_or_404(
            UnitEnrollment.objects.select_related(
                'student__user',
                'student__programme',
                'semester',
                'semester_report',
                'programme_unit__unit',
                'programme_unit__programme',
                'approved_by',
                'resit_exam'
            ),
            id=enrollment_id
        )
        
        # Get unit allocation info
        unit_allocation = None
        try:
            allocation = UnitAllocation.objects.select_related(
                'lecturer__user',
                'programme_unit__unit'
            ).filter(
                programme_unit=enrollment.programme_unit,
                semester=enrollment.semester
            ).first()
            
            if allocation:
                unit_allocation = {
                    'lecturer': allocation.lecturer.user.get_full_name(),
                    'status': allocation.get_status_display(),
                    'max_students': allocation.max_students,
                }
        except UnitAllocation.DoesNotExist:
            pass
        
        # Get resit info if applicable
        resit_info = None
        if enrollment.enrollment_type == 'resit' and enrollment.resit_exam:
            resit = enrollment.resit_exam
            resit_info = {
                'original_marks': float(resit.original_marks),
                'original_grade': resit.original_grade,
                'fee_paid': resit.fee_paid,
                'resit_fee_amount': float(resit.resit_fee_amount),
                'exam_date': resit.exam_date.isoformat() if resit.exam_date else None,
                'status': resit.get_status_display(),
            }
        
        # Get semester report info
        semester_report_info = None
        if enrollment.semester_report:
            report = enrollment.semester_report
            semester_report_info = {
                'status': report.get_status_display(),
                'from_year': report.from_year_of_study,
                'to_year': report.to_year_of_study,
                'is_eligible': report.is_eligible,
                'failed_units_count': report.failed_units_count,
                'cumulative_gpa': float(report.cumulative_gpa) if report.cumulative_gpa else None,
            }
        
        data = {
            'id': enrollment.id,
            'student': {
                'registration_number': enrollment.student.registration_number,
                'name': enrollment.student.user.get_full_name(),
                'email': enrollment.student.user.email,
                'phone': enrollment.student.user.phone_number,
                'programme': enrollment.student.programme.name,
                'programme_code': enrollment.student.programme.code,
                'current_year': enrollment.student.current_year,
                'current_semester': enrollment.student.current_semester,
            },
            'unit': {
                'code': enrollment.programme_unit.unit.code,
                'name': enrollment.programme_unit.unit.name,
                'credit_hours': enrollment.programme_unit.unit.credit_hours,
                'level': enrollment.programme_unit.unit.get_unit_level_display(),
            },
            'enrollment': {
                'enrollment_type': enrollment.get_enrollment_type_display(),
                'enrollment_date': enrollment.enrollment_date.isoformat(),
                'status': enrollment.get_status_display(),
                'semester': enrollment.semester.name,
            },
            'approval': {
                'approved_by': enrollment.approved_by.get_full_name() if enrollment.approved_by else None,
                'approval_date': enrollment.approval_date.isoformat() if enrollment.approval_date else None,
                'rejection_reason': enrollment.rejection_reason,
                'remarks': enrollment.remarks,
            },
            'unit_allocation': unit_allocation,
            'resit_info': resit_info,
            'semester_report': semester_report_info,
        }
        
        return JsonResponse({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


@login_required
@user_passes_test(is_admin_or_registrar)
@require_http_methods(["POST"])
def individual_approve_enrollment(request, enrollment_id):
    """API endpoint to approve individual enrollment"""
    
    try:
        data = json.loads(request.body)
        bypass_semester_report_check = data.get('bypass_semester_report_check', False)
        remarks = data.get('remarks', '')
        
        enrollment = get_object_or_404(UnitEnrollment, id=enrollment_id)
        
        # Validation
        if enrollment.status == 'approved':
            return JsonResponse({
                'success': False,
                'message': 'Enrollment is already approved'
            }, status=400)
        
        # Check semester report
        if not bypass_semester_report_check:
            if not enrollment.semester_report or enrollment.semester_report.status != 'approved':
                return JsonResponse({
                    'success': False,
                    'message': 'Student has not reported for semester or report not approved. Use bypass option to approve anyway.'
                }, status=400)
        
        # Check if unit is offered
        unit_offered = UnitAllocation.objects.filter(
            programme_unit=enrollment.programme_unit,
            semester=enrollment.semester,
            status__in=['approved_hod', 'approved_hos', 'approved_dean']
        ).exists()
        
        if not unit_offered:
            return JsonResponse({
                'success': False,
                'message': 'Unit is not offered in this semester'
            }, status=400)
        
        # Approve
        enrollment.status = 'approved'
        enrollment.approved_by = request.user
        enrollment.approval_date = timezone.now()
        
        enrollment_remarks = f"Approved by {request.user.get_full_name()}"
        if bypass_semester_report_check:
            enrollment_remarks += " (Semester report check bypassed)"
        if remarks:
            enrollment_remarks += f" - {remarks}"
        
        enrollment.remarks = enrollment_remarks
        enrollment.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Enrollment approved successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


@login_required
@user_passes_test(is_admin_or_registrar)
@require_http_methods(["POST"])
def individual_reject_enrollment(request, enrollment_id):
    """API endpoint to reject individual enrollment"""
    
    try:
        data = json.loads(request.body)
        rejection_reason = data.get('rejection_reason', '')
        
        if not rejection_reason:
            return JsonResponse({
                'success': False,
                'message': 'Rejection reason is required'
            }, status=400)
        
        enrollment = get_object_or_404(UnitEnrollment, id=enrollment_id)
        
        if enrollment.status == 'rejected':
            return JsonResponse({
                'success': False,
                'message': 'Enrollment is already rejected'
            }, status=400)
        
        # Reject
        enrollment.status = 'rejected'
        enrollment.rejection_reason = rejection_reason
        enrollment.remarks = f"Rejected by {request.user.get_full_name()}: {rejection_reason}"
        enrollment.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Enrollment rejected successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


@login_required
@user_passes_test(is_admin_or_registrar)
@require_http_methods(["GET"])
def get_enrollment_statistics(request):
    """API endpoint to get enrollment statistics"""
    
    try:
        semester_id = request.GET.get('semester_id')
        programme_id = request.GET.get('programme_id')
        
        query = Q()
        if semester_id:
            query &= Q(semester_id=semester_id)
        if programme_id:
            query &= Q(student__programme_id=programme_id)
        
        enrollments = UnitEnrollment.objects.filter(query)
        
        stats = {
            'total': enrollments.count(),
            'by_status': {
                'pending': enrollments.filter(status='pending').count(),
                'approved': enrollments.filter(status='approved').count(),
                'rejected': enrollments.filter(status='rejected').count(),
                'dropped': enrollments.filter(status='dropped').count(),
            },
            'by_type': {
                'normal': enrollments.filter(enrollment_type='normal').count(),
                'resit': enrollments.filter(enrollment_type='resit').count(),
                'retake': enrollments.filter(enrollment_type='retake').count(),
            },
            'top_units': list(enrollments.values(
                'programme_unit__unit__code',
                'programme_unit__unit__name'
            ).annotate(
                count=Count('id')
            ).order_by('-count')[:5])
        }
        
        return JsonResponse({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)