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
        return redirect('library_dashboard')
    
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
@login_required
def dean_dashboard(request):
    context = {'page_title': 'Dean Dashboard'}
    return render(request, 'dean/dashboard.html', context)


@login_required
def hos_dashboard(request):
    context = {'page_title': 'Head of School Dashboard'}
    return render(request, 'hos/dashboard.html', context)


@login_required
def hod_dashboard(request):
    context = {'page_title': 'HOD Dashboard'}
    return render(request, 'hod/dashboard.html', context)


@login_required
def finance_dashboard(request):
    context = {'page_title': 'Finance Dashboard'}
    return render(request, 'finance/dashboard.html', context)


@login_required
def registrar_dashboard(request):
    context = {'page_title': 'Registrar Dashboard'}
    return render(request, 'registrar/dashboard.html', context)


@login_required
def library_dashboard(request):
    context = {'page_title': 'Library Dashboard'}
    return render(request, 'library/dashboard.html', context)


@login_required
def hostel_dashboard(request):
    context = {'page_title': 'Hostel Dashboard'}
    return render(request, 'hostel/dashboard.html', context)


@login_required
def procurement_dashboard(request):
    context = {'page_title': 'Procurement Dashboard'}
    return render(request, 'procurement/dashboard.html', context)


@login_required
def profile_view(request):
    """User profile view"""
    context = {
        'page_title': 'My Profile',
    }
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
    
    # Get student's current units
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



# views.py
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
    ).prefetch_related(
        'programme_unit__registrations'
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
        student_count = UnitRegistration.objects.filter(
            programme_unit=allocation.programme_unit,
            semester=allocation.semester,
            status='registered'
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
    
    # Get all students registered for this unit
    registrations = UnitRegistration.objects.filter(
        programme_unit=allocation.programme_unit,
        semester=allocation.semester,
        status='registered'
    ).select_related(
        'student',
        'student__user',
        'student__programme'
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
    for registration in registrations:
        student = registration.student
        
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
        eligible_for_exam = attendance_percentage >= 75
        
        students_data.append({
            'registration': registration,
            'student': student,
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


@login_required
def save_student_marks(request):
    """AJAX endpoint to save student marks"""
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
        
        # Calculate total marks for the student
        all_assessments = Assessment.objects.filter(
            unit_allocation=assessment.unit_allocation
        )
        
        total = Decimal('0.00')
        for assess in all_assessments:
            mark = StudentMarks.objects.filter(
                assessment=assess,
                student=student
            ).first()
            
            if mark:
                weighted = (mark.marks_obtained / assess.max_marks) * assess.weight_percentage
                total += weighted
        
        return JsonResponse({
            'success': True,
            'message': 'Marks saved successfully',
            'total_marks': float(round(total, 2)),
            'created': created
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


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
    
    # Get all students with attendance >= 75%
    registrations = UnitRegistration.objects.filter(
        programme_unit=allocation.programme_unit,
        semester=allocation.semester,
        status='registered'
    ).select_related('student', 'student__user')
    
    eligible_students = []
    for registration in registrations:
        student = registration.student
        
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
                'attendance': attendance_percentage
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
    table_data = [['No.', 'Registration Number', 'Student Name', 'Attendance %']]
    
    for idx, student in enumerate(eligible_students, 1):
        table_data.append([
            str(idx),
            student['reg_no'],
            student['name'],
            f"{student['attendance']}%"
        ])
    
    table = Table(table_data, colWidths=[0.6*inch, 1.8*inch, 3*inch, 1.2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
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
    
    # Get students
    registrations = UnitRegistration.objects.filter(
        programme_unit=allocation.programme_unit,
        semester=allocation.semester,
        status='registered'
    ).select_related('student', 'student__user').order_by('student__registration_number')
    
    # Create CSV
    response = HttpResponse(content_type='text/csv')
    filename = f"marks_{allocation.programme_unit.unit.code}_{timezone.now().strftime('%Y%m%d')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    
    # Headers
    headers = ['Registration Number', 'Student Name']
    for assessment in assessments:
        headers.append(f"{assessment.get_assessment_type_display()} ({assessment.max_marks})")
    headers.extend(['Total (%)', 'Attendance %'])
    
    writer.writerow(headers)
    
    # Data rows
    for registration in registrations:
        student = registration.student
        row = [student.registration_number, student.user.get_full_name()]
        
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