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


@login_required
def admin_dashboard(request):
    """Admin dashboard view"""
    context = {
        'page_title': 'Admin Dashboard',
        'user': request.user,
    }
    return render(request, 'admin/dashboard.html', context)


@login_required
def student_dashboard(request):
    """Student dashboard view"""
    try:
        student = Student.objects.get(user=request.user)
        
        # Get student's current registrations
        from portal.models import UnitRegistration, FeeBalance, HostelAllocation
        from django.utils import timezone
        
        current_semester = student.programme.get_current_semester() if hasattr(student.programme, 'get_current_semester') else None
        
        registrations = UnitRegistration.objects.filter(
            student=student,
            semester__is_current=True
        ).select_related('programme_unit__unit')
        
        # Get fee balance - Fixed: changed created_at to updated_at
        fee_balance = FeeBalance.objects.filter(
            student=student
        ).order_by('-updated_at').first()
        
        # Get hostel info
        hostel_allocation = HostelAllocation.objects.filter(
            student=student,
            is_active=True
        ).select_related('bed__room__hostel').first()
        
        context = {
            'page_title': 'Student Dashboard',
            'student': student,
            'registrations': registrations,
            'fee_balance': fee_balance,
            'hostel_allocation': hostel_allocation,
        }
        return render(request, 'student/dashboard.html', context)
    
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('login')


@login_required
def lecturer_dashboard(request):
    """Lecturer dashboard view"""
    context = {
        'page_title': 'Lecturer Dashboard',
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
    
    # Calculate next year and semester
    current_year = student.current_year
    current_sem = int(student.current_semester)
    programme_total_semesters = student.programme.total_semesters
    
    # Determine next semester
    if current_sem < 3:  # If not in final semester of year
        next_semester_number = str(current_sem + 1)
        next_year = current_year
    else:  # Move to next year
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
    
    if not enrollment_period or not enrollment_period.is_enrollment_open():
        messages.error(request, 'Unit enrollment is not currently open.')
        return redirect('student_dashboard')
    
    # Get available units for student's year and semester
    available_units = ProgrammeUnit.objects.filter(
        programme=student.programme,
        academic_year=current_semester.academic_year,
        year_of_study=student.current_year,
        semester_number=student.current_semester,
        is_active=True
    ).select_related('unit', 'programme')
    
    # Filter units that are allocated (have lecturers)
    available_units = available_units.filter(
        allocations__semester=current_semester,
        allocations__status='approved_dean'
    ).distinct()
    
    # Get already enrolled units
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
        programme_unit__in=enrolled_units
    ).select_related('programme_unit', 'programme_unit__unit')
    
    # Filter failed units that are offered this semester
    failed_units_offered = []
    for result in failed_units:
        if UnitAllocation.objects.filter(
            programme_unit=result.programme_unit,
            semester=current_semester,
            status='approved_dean'
        ).exists():
            failed_units_offered.append(result)
    
    context = {
        'student': student,
        'current_semester': current_semester,
        'semester_report': semester_report,
        'enrollment_period': enrollment_period,
        'available_units': available_units,
        'enrolled_units': enrolled_units,
        'failed_units_offered': failed_units_offered,
    }
    
    if request.method == 'POST':
        selected_units = request.POST.getlist('units')
        resit_units = request.POST.getlist('resit_units')
        
        try:
            enrolled_count = 0
            
            # Enroll in normal units
            for unit_id in selected_units:
                programme_unit = get_object_or_404(ProgrammeUnit, id=unit_id)
                
                enrollment = UnitEnrollment(
                    student=student,
                    semester_report=semester_report,
                    programme_unit=programme_unit,
                    semester=current_semester,
                    enrollment_type='normal'
                )
                enrollment.save()
                enrolled_count += 1
            
            # Enroll in resit units
            for result_id in resit_units:
                result = get_object_or_404(SemesterResults, id=result_id, student=student)
                
                # Create resit exam record
                resit_exam = ResitExam(
                    student=student,
                    original_result=result,
                    resit_semester=current_semester,
                    original_semester=result.semester,
                    original_marks=result.total_marks,
                    original_grade=result.grade,
                    original_grade_point=result.grade_point,
                    resit_fee_amount=Decimal('2000.00'),  # Set appropriate resit fee
                )
                resit_exam.save()
                
                # Create enrollment
                enrollment = UnitEnrollment(
                    student=student,
                    semester_report=semester_report,
                    programme_unit=result.programme_unit,
                    semester=current_semester,
                    enrollment_type='resit',
                    resit_exam=resit_exam
                )
                enrollment.save()
                enrolled_count += 1
            
            if enrolled_count > 0:
                messages.success(request, f'Successfully enrolled in {enrolled_count} unit(s).')
            else:
                messages.warning(request, 'No units selected for enrollment.')
            
            return redirect('unit_enrollment_status')
            
        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error enrolling in units: {str(e)}')
    
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
    
    context = {
        'student': student,
        'current_semester': current_semester,
        'enrollments': enrollments,
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
            
            semesters_data = [{
                'id': sem.id,
                'name': sem.name,
                'semester_number': sem.semester_number,
                'start_date': sem.start_date.strftime('%Y-%m-%d'),
                'end_date': sem.end_date.strftime('%Y-%m-%d'),
                'registration_start_date': sem.registration_start_date.strftime('%Y-%m-%d'),
                'registration_end_date': sem.registration_end_date.strftime('%Y-%m-%d'),
                'is_current': sem.is_current,
                'is_active': sem.is_active,
            } for sem in semesters]
            
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


@login_required
@require_http_methods(["POST"])
def update_semester_ajax(request, semester_id):
    """Update a semester (AJAX)"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            semester = get_object_or_404(Semester, pk=semester_id)
            
            # Get form data
            name = request.POST.get('name')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            registration_start_date = request.POST.get('registration_start_date')
            registration_end_date = request.POST.get('registration_end_date')
            is_active = request.POST.get('is_active', 'true').lower() == 'true'
            
            # Update semester
            if name:
                semester.name = name
            if start_date:
                semester.start_date = start_date
            if end_date:
                semester.end_date = end_date
            if registration_start_date:
                semester.registration_start_date = registration_start_date
            if registration_end_date:
                semester.registration_end_date = registration_end_date
            
            semester.is_active = is_active
            semester.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Semester {semester.name} updated successfully!',
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
                    'academic_year_id': semester.academic_year.id,
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error updating semester: {str(e)}'
            }, status=400)
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)


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