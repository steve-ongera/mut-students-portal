"""
Librarian Utilities and Helper Functions
Reusable functions for library management
"""

from django.db.models import Q, Count, Sum, Avg, F
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from .models import *

# ============= ELIGIBILITY CHECKS =============

def check_student_eligibility(student):
    """
    Check if student is eligible to borrow books
    Returns: (is_eligible: bool, reasons: list)
    """
    reasons = []
    
    # Check if student is active
    if student.student_status != 'active':
        reasons.append(f'Student status is {student.get_student_status_display()}')
    
    # Check for overdue books
    has_overdue = BookBorrowing.objects.filter(
        student=student,
        status__in=['active', 'overdue'],
        due_date__lt=timezone.now().date()
    ).exists()
    
    if has_overdue:
        reasons.append('Student has overdue books')
    
    # Check for unpaid fines
    has_unpaid_fines = BookBorrowing.objects.filter(
        student=student,
        fine_amount__gt=0,
        fine_paid=False
    ).exists()
    
    if has_unpaid_fines:
        reasons.append('Student has unpaid fines')
    
    # Check borrowing limit
    active_count = BookBorrowing.objects.filter(
        student=student,
        status='active'
    ).count()
    
    max_books = 3  # Maximum books allowed
    if active_count >= max_books:
        reasons.append(f'Borrowing limit reached ({active_count}/{max_books})')
    
    # Check fee clearance (if fee balance model exists)
    try:
        from .models import FeeBalance
        current_semester = Semester.objects.filter(is_current=True).first()
        if current_semester:
            fee_balance = FeeBalance.objects.filter(
                student=student,
                semester=current_semester
            ).first()
            
            if fee_balance and not fee_balance.is_cleared:
                reasons.append('Fee balance not cleared')
    except:
        pass  # Fee balance check optional
    
    is_eligible = len(reasons) == 0
    
    return is_eligible, reasons


def get_student_borrowing_stats(student):
    """Get borrowing statistics for a student"""
    
    stats = {
        'total_borrowed': BookBorrowing.objects.filter(student=student).count(),
        'currently_borrowed': BookBorrowing.objects.filter(
            student=student, 
            status='active'
        ).count(),
        'total_returned': BookBorrowing.objects.filter(
            student=student, 
            status='returned'
        ).count(),
        'overdue_count': BookBorrowing.objects.filter(
            student=student,
            status='overdue'
        ).count(),
        'total_fines': BookBorrowing.objects.filter(
            student=student
        ).aggregate(total=Sum('fine_amount'))['total'] or Decimal('0.00'),
        'unpaid_fines': BookBorrowing.objects.filter(
            student=student,
            fine_paid=False
        ).aggregate(total=Sum('fine_amount'))['total'] or Decimal('0.00'),
    }
    
    return stats


# ============= BOOK AVAILABILITY =============

def check_book_availability(book):
    """
    Check book availability and reservation status
    Returns: dict with availability info
    """
    
    availability = {
        'is_available': book.available_copies > 0,
        'available_copies': book.available_copies,
        'total_copies': book.total_copies,
        'borrowed_copies': book.total_copies - book.available_copies,
        'status': book.status,
    }
    
    # Check for reservations (if implemented)
    # availability['reserved_by'] = []
    
    return availability


def get_popular_books(limit=10, days=30):
    """Get most borrowed books in recent period"""
    
    date_from = timezone.now() - timedelta(days=days)
    
    popular = Book.objects.annotate(
        recent_borrows=Count(
            'borrowings',
            filter=Q(borrowings__borrow_date__gte=date_from)
        )
    ).filter(
        recent_borrows__gt=0
    ).order_by('-recent_borrows')[:limit]
    
    return popular


# ============= FINE CALCULATIONS =============

def calculate_fine_amount(due_date, return_date=None, daily_rate=5):
    """
    Calculate fine for overdue book
    Args:
        due_date: Date when book was due
        return_date: Date when book was returned (None for current date)
        daily_rate: Fine per day (default 5 KES)
    Returns:
        Decimal: Fine amount
    """
    
    if return_date is None:
        return_date = timezone.now().date()
    
    if return_date <= due_date:
        return Decimal('0.00')
    
    days_overdue = (return_date - due_date).days
    fine = Decimal(str(days_overdue * daily_rate))
    
    return fine


def update_all_overdue_fines():
    """Update fines for all overdue books"""
    
    overdue_borrowings = BookBorrowing.objects.filter(
        status__in=['active', 'overdue'],
        due_date__lt=timezone.now().date()
    )
    
    updated_count = 0
    for borrowing in overdue_borrowings:
        borrowing.calculate_fine()
        if borrowing.status != 'overdue':
            borrowing.status = 'overdue'
        borrowing.save()
        updated_count += 1
    
    return updated_count


# ============= REPORTING HELPERS =============

def get_circulation_summary(start_date, end_date):
    """Get circulation summary for date range"""
    
    borrowings = BookBorrowing.objects.filter(
        borrow_date__gte=start_date,
        borrow_date__lte=end_date
    )
    
    summary = {
        'total_issued': borrowings.count(),
        'total_returned': borrowings.filter(status='returned').count(),
        'currently_active': borrowings.filter(status='active').count(),
        'overdue': borrowings.filter(status='overdue').count(),
        'unique_borrowers': borrowings.values('student').distinct().count(),
        'unique_books': borrowings.values('book').distinct().count(),
        'total_fines': borrowings.aggregate(
            total=Sum('fine_amount')
        )['total'] or Decimal('0.00'),
    }
    
    return summary


def get_category_performance(category_id=None, days=90):
    """Get performance metrics for book categories"""
    
    date_from = timezone.now() - timedelta(days=days)
    
    if category_id:
        categories = BookCategory.objects.filter(id=category_id)
    else:
        categories = BookCategory.objects.all()
    
    performance = []
    
    for category in categories:
        books_count = Book.objects.filter(category=category).aggregate(
            total=Sum('total_copies')
        )['total'] or 0
        
        borrows_count = BookBorrowing.objects.filter(
            book__category=category,
            borrow_date__gte=date_from
        ).count()
        
        performance.append({
            'category': category.name,
            'total_books': books_count,
            'borrows': borrows_count,
            'utilization_rate': (borrows_count / books_count * 100) if books_count > 0 else 0
        })
    
    return performance


# ============= NOTIFICATIONS =============

def get_overdue_notifications():
    """Get list of students with overdue books for notifications"""
    
    overdue_borrowings = BookBorrowing.objects.filter(
        status='overdue'
    ).select_related('student__user', 'book')
    
    notifications = []
    
    for borrowing in overdue_borrowings:
        days_overdue = (timezone.now().date() - borrowing.due_date).days
        
        notifications.append({
            'student': borrowing.student,
            'book': borrowing.book,
            'due_date': borrowing.due_date,
            'days_overdue': days_overdue,
            'fine_amount': borrowing.fine_amount,
        })
    
    return notifications


def send_overdue_reminders():
    """
    Send reminders to students with overdue books
    This would integrate with your email/SMS system
    """
    
    notifications = get_overdue_notifications()
    
    for notif in notifications:
        # Example: Send email
        # send_email(
        #     to=notif['student'].user.email,
        #     subject='Library Book Overdue',
        #     message=f"Your book '{notif['book'].title}' is {notif['days_overdue']} days overdue..."
        # )
        pass
    
    return len(notifications)


# ============= SEARCH & FILTERS =============

def advanced_book_search(query_params):
    """
    Advanced book search with multiple filters
    Args:
        query_params: dict with search parameters
    Returns:
        QuerySet of books
    """
    
    books = Book.objects.all()
    
    # Text search
    if query_params.get('search'):
        search = query_params['search']
        books = books.filter(
            Q(title__icontains=search) |
            Q(author__icontains=search) |
            Q(isbn__icontains=search) |
            Q(publisher__icontains=search)
        )
    
    # Category filter
    if query_params.get('category'):
        books = books.filter(category_id=query_params['category'])
    
    # Status filter
    if query_params.get('status'):
        books = books.filter(status=query_params['status'])
    
    # Publication year range
    if query_params.get('year_from'):
        books = books.filter(publication_year__gte=query_params['year_from'])
    
    if query_params.get('year_to'):
        books = books.filter(publication_year__lte=query_params['year_to'])
    
    # Availability
    if query_params.get('available_only'):
        books = books.filter(available_copies__gt=0)
    
    return books


def search_students_for_library(query):
    """Search for students in library context"""
    
    students = Student.objects.filter(
        Q(registration_number__icontains=query) |
        Q(user__first_name__icontains=query) |
        Q(user__last_name__icontains=query) |
        Q(user__email__icontains=query)
    ).select_related(
        'user', 'programme'
    ).filter(
        student_status='active'
    )
    
    return students


# ============= INVENTORY HELPERS =============

def get_low_stock_books(threshold=2):
    """Get books with low stock levels"""
    
    low_stock = Book.objects.filter(
        available_copies__lte=threshold,
        available_copies__gt=0
    ).select_related('category').order_by('available_copies')
    
    return low_stock


def get_inventory_summary():
    """Get overall inventory summary"""
    
    summary = {
        'total_titles': Book.objects.count(),
        'total_copies': Book.objects.aggregate(
            total=Sum('total_copies')
        )['total'] or 0,
        'available_copies': Book.objects.aggregate(
            total=Sum('available_copies')
        )['total'] or 0,
        'borrowed_copies': Book.objects.aggregate(
            total=Sum(F('total_copies') - F('available_copies'))
        )['total'] or 0,
        'categories_count': BookCategory.objects.count(),
        'low_stock_count': get_low_stock_books().count(),
        'out_of_stock_count': Book.objects.filter(available_copies=0).count(),
    }
    
    return summary


# ============= ANALYTICS =============

def get_borrowing_trends(days=90):
    """Get borrowing trends over time"""
    
    date_from = timezone.now() - timedelta(days=days)
    
    trends = BookBorrowing.objects.filter(
        borrow_date__gte=date_from
    ).extra(
        select={'day': 'DATE(borrow_date)'}
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')
    
    return trends


def get_top_borrowers(limit=10, semester=None):
    """Get students who borrow most frequently"""
    
    borrowings = BookBorrowing.objects.all()
    
    if semester:
        borrowings = borrowings.filter(semester=semester)
    
    top_borrowers = borrowings.values(
        'student__registration_number',
        'student__user__first_name',
        'student__user__last_name',
        'student__programme__name'
    ).annotate(
        borrow_count=Count('id')
    ).order_by('-borrow_count')[:limit]
    
    return top_borrowers


def calculate_collection_utilization():
    """Calculate how well the collection is being used"""
    
    total_books = Book.objects.aggregate(
        total=Sum('total_copies')
    )['total'] or 0
    
    if total_books == 0:
        return 0
    
    # Books that have been borrowed at least once
    borrowed_books = Book.objects.annotate(
        borrow_count=Count('borrowings')
    ).filter(borrow_count__gt=0).aggregate(
        total=Sum('total_copies')
    )['total'] or 0
    
    utilization_rate = (borrowed_books / total_books) * 100
    
    return round(utilization_rate, 2)


# ============= VALIDATION HELPERS =============

def validate_isbn(isbn):
    """Validate ISBN format (basic)"""
    
    # Remove hyphens and spaces
    isbn = isbn.replace('-', '').replace(' ', '')
    
    # Check length (ISBN-10 or ISBN-13)
    if len(isbn) not in [10, 13]:
        return False, "ISBN must be 10 or 13 digits"
    
    # Check if all characters are digits (except last char in ISBN-10 can be X)
    if len(isbn) == 10:
        if not (isbn[:-1].isdigit() and (isbn[-1].isdigit() or isbn[-1].upper() == 'X')):
            return False, "Invalid ISBN-10 format"
    else:
        if not isbn.isdigit():
            return False, "Invalid ISBN-13 format"
    
    return True, "Valid ISBN"


def validate_book_data(book_data):
    """Validate book data before creation/update"""
    
    errors = []
    
    # Required fields
    required = ['isbn', 'title', 'author', 'category']
    for field in required:
        if not book_data.get(field):
            errors.append(f"{field.title()} is required")
    
    # ISBN validation
    if book_data.get('isbn'):
        is_valid, message = validate_isbn(book_data['isbn'])
        if not is_valid:
            errors.append(message)
    
    # Numeric validations
    if book_data.get('total_copies'):
        try:
            copies = int(book_data['total_copies'])
            if copies < 1:
                errors.append("Total copies must be at least 1")
        except ValueError:
            errors.append("Total copies must be a number")
    
    if book_data.get('publication_year'):
        try:
            year = int(book_data['publication_year'])
            current_year = timezone.now().year
            if year < 1500 or year > current_year + 1:
                errors.append(f"Publication year must be between 1500 and {current_year + 1}")
        except ValueError:
            errors.append("Publication year must be a valid year")
    
    return len(errors) == 0, errors


# ============= EXPORT HELPERS =============

def export_circulation_data(start_date, end_date, format='csv'):
    """
    Export circulation data for given period
    Returns data in requested format
    """
    
    borrowings = BookBorrowing.objects.filter(
        borrow_date__gte=start_date,
        borrow_date__lte=end_date
    ).select_related('student__user', 'book', 'issued_by')
    
    data = []
    for borrowing in borrowings:
        data.append({
            'Registration Number': borrowing.student.registration_number,
            'Student Name': borrowing.student.user.get_full_name(),
            'Book Title': borrowing.book.title,
            'ISBN': borrowing.book.isbn,
            'Borrow Date': borrowing.borrow_date.strftime('%Y-%m-%d'),
            'Due Date': borrowing.due_date.strftime('%Y-%m-%d'),
            'Return Date': borrowing.return_date.strftime('%Y-%m-%d') if borrowing.return_date else 'Not returned',
            'Status': borrowing.get_status_display(),
            'Fine Amount': str(borrowing.fine_amount),
            'Fine Paid': 'Yes' if borrowing.fine_paid else 'No',
        })
    
    return data


# ============= DASHBOARD DATA =============

def get_dashboard_metrics():
    """Get all metrics for librarian dashboard"""
    
    metrics = {
        'inventory': get_inventory_summary(),
        'circulation': get_circulation_summary(
            timezone.now().date() - timedelta(days=30),
            timezone.now().date()
        ),
        'top_books': get_popular_books(limit=5),
        'top_borrowers': get_top_borrowers(limit=5),
        'overdue_count': BookBorrowing.objects.filter(status='overdue').count(),
        'pending_fines': BookBorrowing.objects.filter(
            fine_paid=False
        ).aggregate(total=Sum('fine_amount'))['total'] or Decimal('0.00'),
    }
    
    return metrics