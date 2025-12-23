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