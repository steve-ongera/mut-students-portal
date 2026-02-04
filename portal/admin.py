from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.db.models import Count, Sum
from .models import *

# ============= CUSTOM USER ADMIN =============
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'get_full_name', 'is_active_user', 'is_staff')
    list_filter = ('role', 'is_active_user', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'id_number')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone_number', 'id_number', 'profile_picture', 'is_active_user')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone_number', 'id_number', 'email', 'first_name', 'last_name')
        }),
    )

# ============= ACADEMIC STRUCTURE =============
@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'dean', 'head_of_school', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'code', 'email')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'school', 'hod', 'is_active', 'created_at')
    list_filter = ('school', 'is_active', 'created_at')
    search_fields = ('name', 'code', 'email')
    ordering = ('school', 'name')
    readonly_fields = ('created_at', 'updated_at')

# ============= ACADEMIC YEAR & SEMESTER =============
@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_current', 'is_active')
    list_filter = ('is_current', 'is_active')
    search_fields = ('name',)
    ordering = ('-start_date',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('name', 'academic_year', 'semester_number', 'start_date', 'end_date', 'is_current')
    list_filter = ('is_current', 'is_active', 'semester_number')
    search_fields = ('name',)
    ordering = ('-academic_year__start_date', 'semester_number')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Intake)
class IntakeAdmin(admin.ModelAdmin):
    list_display = ('name', 'intake_number', 'month', 'academic_year', 'start_date', 'is_active')
    list_filter = ('month', 'is_active', 'academic_year')
    search_fields = ('name', 'intake_number')
    ordering = ('-start_date',)
    readonly_fields = ('created_at', 'updated_at')

# ============= PROGRAMME & UNITS =============
@admin.register(Programme)
class ProgrammeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'department', 'programme_type', 'study_mode', 'duration_years', 'is_active')
    list_filter = ('programme_type', 'study_mode', 'is_active', 'department__school')
    search_fields = ('name', 'code')
    ordering = ('department', 'name')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'department', 'unit_level', 'credit_hours', 'is_active')
    list_filter = ('unit_level', 'is_active', 'department')
    search_fields = ('code', 'name')
    ordering = ('code',)
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('prerequisites',)

class ProgrammeUnitInline(admin.TabularInline):
    model = ProgrammeUnit
    extra = 1
    fields = ('unit', 'year_of_study', 'semester_number', 'unit_type', 'is_active')

@admin.register(ProgrammeUnit)
class ProgrammeUnitAdmin(admin.ModelAdmin):
    list_display = ('programme', 'unit', 'year_of_study', 'semester_number', 'unit_type', 'is_active')
    list_filter = ('programme', 'year_of_study', 'semester_number', 'unit_type')
    search_fields = ('programme__name', 'unit__name', 'unit__code')
    ordering = ('programme', 'year_of_study', 'semester_number')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(UnitGradingSystem)
class UnitGradingSystemAdmin(admin.ModelAdmin):
    list_display = ('unit', 'grade', 'min_marks', 'max_marks', 'grade_point', 'is_pass')
    list_filter = ('is_pass', 'unit__department')
    search_fields = ('unit__name', 'grade')
    ordering = ('unit', '-min_marks')

@admin.register(UnitAllocation)
class UnitAllocationAdmin(admin.ModelAdmin):
    list_display = ('programme_unit', 'lecturer', 'semester', 'status', 'created_at')
    list_filter = ('status', 'semester', 'programme_unit__programme')
    search_fields = ('lecturer__username', 'programme_unit__unit__name')
    ordering = ('-semester__academic_year__start_date',)
    readonly_fields = ('created_at', 'updated_at')

# ============= STUDENT MANAGEMENT =============
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('registration_number', 'get_student_name', 'programme', 'current_year', 
                   'student_status', 'cumulative_gpa')
    list_filter = ('student_status', 'programme', 'current_year', 'gender', 'intake')
    search_fields = ('registration_number', 'user__username', 'user__first_name', 
                    'user__last_name', 'national_id')
    ordering = ('registration_number',)
    readonly_fields = ('created_at', 'updated_at')
    
    def get_student_name(self, obj):
        return obj.user.get_full_name()
    get_student_name.short_description = 'Student Name'

@admin.register(StudentProgression)
class StudentProgressionAdmin(admin.ModelAdmin):
    list_display = ('student', 'previous_programme', 'new_programme', 'progression_date', 
                   'final_gpa', 'approved_by')
    list_filter = ('progression_date', 'new_programme')
    search_fields = ('student__registration_number', 'student__user__username')
    ordering = ('-progression_date',)
    readonly_fields = ('created_at',)

@admin.register(UnitRegistration)
class UnitRegistrationAdmin(admin.ModelAdmin):
    list_display = ('student', 'programme_unit', 'semester', 'status', 'is_retake', 'registration_date')
    list_filter = ('status', 'is_retake', 'semester')
    search_fields = ('student__registration_number', 'programme_unit__unit__name')
    ordering = ('-registration_date',)

# ============= ASSESSMENT & GRADING =============
@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'unit_allocation', 'assessment_type', 'max_marks', 
                   'weight_percentage', 'date', 'is_published')
    list_filter = ('assessment_type', 'is_published', 'date')
    search_fields = ('title', 'unit_allocation__programme_unit__unit__name')
    ordering = ('-date',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(StudentMarks)
class StudentMarksAdmin(admin.ModelAdmin):
    list_display = ('student', 'assessment', 'marks_obtained', 'status', 'attendance', 'submitted_by')
    list_filter = ('status', 'attendance', 'assessment__assessment_type')
    search_fields = ('student__registration_number', 'assessment__title')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(SemesterResults)
class SemesterResultsAdmin(admin.ModelAdmin):
    list_display = ('student', 'programme_unit', 'semester', 'total_marks', 'grade', 
                   'grade_point', 'is_passed', 'is_published')
    list_filter = ('is_passed', 'is_published', 'semester', 'grade')
    search_fields = ('student__registration_number', 'programme_unit__unit__name')
    ordering = ('-semester__academic_year__start_date', 'student')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(SemesterGPA)
class SemesterGPAAdmin(admin.ModelAdmin):
    list_display = ('student', 'semester', 'semester_gpa', 'cumulative_gpa', 
                   'total_credit_hours', 'class_rank', 'is_published')
    list_filter = ('is_published', 'semester')
    search_fields = ('student__registration_number',)
    ordering = ('-semester__academic_year__start_date', '-cumulative_gpa')
    readonly_fields = ('created_at', 'updated_at')

# ============= FEE MANAGEMENT =============
@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('programme', 'academic_year', 'year_of_study', 'semester_number', 
                   'total_fee', 'is_active')
    list_filter = ('academic_year', 'year_of_study', 'semester_number', 'is_active')
    search_fields = ('programme__name',)
    ordering = ('-academic_year__start_date', 'programme')
    readonly_fields = ('total_fee', 'created_at', 'updated_at')

@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'amount', 'payment_method', 'transaction_reference', 
                   'receipt_number', 'status', 'payment_date')
    list_filter = ('status', 'payment_method', 'semester')
    search_fields = ('student__registration_number', 'transaction_reference', 'receipt_number')
    ordering = ('-payment_date',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(FeeBalance)
class FeeBalanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'semester', 'total_fees', 'amount_paid', 'balance', 
                   'is_cleared', 'last_payment_date')
    list_filter = ('is_cleared', 'semester')
    search_fields = ('student__registration_number',)
    ordering = ('-semester__academic_year__start_date',)
    readonly_fields = ('balance', 'updated_at')

# ============= LECTURER =============
@admin.register(Lecturer)
class LecturerAdmin(admin.ModelAdmin):
    list_display = ('employee_number', 'get_lecturer_name', 'department', 'designation', 
                   'qualification', 'is_active')
    list_filter = ('designation', 'department', 'is_active')
    search_fields = ('employee_number', 'user__username', 'user__first_name', 'user__last_name')
    ordering = ('employee_number',)
    readonly_fields = ('created_at', 'updated_at')
    
    def get_lecturer_name(self, obj):
        return obj.user.get_full_name()
    get_lecturer_name.short_description = 'Lecturer Name'

# ============= HOSTEL MANAGEMENT =============
@admin.register(Hostel)
class HostelAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'gender_type', 'warden', 'total_capacity', 'is_active')
    list_filter = ('gender_type', 'is_active')
    search_fields = ('name', 'code')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(HostelRoom)
class HostelRoomAdmin(admin.ModelAdmin):
    list_display = ('hostel', 'room_number', 'floor', 'room_type', 'capacity', 
                   'has_bathroom', 'is_active')
    list_filter = ('hostel', 'room_type', 'floor', 'is_active')
    search_fields = ('room_number', 'hostel__name')
    ordering = ('hostel', 'floor', 'room_number')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(HostelBed)
class HostelBedAdmin(admin.ModelAdmin):
    list_display = ('room', 'bed_number', 'status', 'academic_year', 'is_active')
    list_filter = ('status', 'academic_year', 'is_active')
    search_fields = ('bed_number', 'room__room_number')
    ordering = ('room', 'bed_number')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(HostelFeeStructure)
class HostelFeeStructureAdmin(admin.ModelAdmin):
    list_display = ('hostel', 'room_type', 'academic_year', 'semester', 'fee_amount', 
                   'booking_fee', 'is_active')
    list_filter = ('academic_year', 'semester', 'room_type', 'is_active')
    search_fields = ('hostel__name',)
    ordering = ('-academic_year__start_date', 'hostel')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(HostelApplication)
class HostelApplicationAdmin(admin.ModelAdmin):
    list_display = ('student', 'hostel', 'academic_year', 'semester', 'status', 
                   'booking_fee_paid', 'application_date')
    list_filter = ('status', 'booking_fee_paid', 'academic_year', 'semester')
    search_fields = ('student__registration_number', 'hostel__name')
    ordering = ('-application_date',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(HostelAllocation)
class HostelAllocationAdmin(admin.ModelAdmin):
    list_display = ('student', 'bed', 'academic_year', 'semester', 'is_active', 
                   'fee_paid', 'allocation_date')
    list_filter = ('is_active', 'fee_paid', 'academic_year', 'semester')
    search_fields = ('student__registration_number',)
    ordering = ('-allocation_date',)

# ============= LIBRARY MANAGEMENT =============
@admin.register(BookCategory)
class BookCategoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'parent_category')
    search_fields = ('name', 'code')
    ordering = ('name',)

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('isbn', 'title', 'author', 'category', 'total_copies', 
                   'available_copies', 'status')
    list_filter = ('status', 'category', 'publication_year')
    search_fields = ('isbn', 'title', 'author')
    ordering = ('title',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(BookBorrowing)
class BookBorrowingAdmin(admin.ModelAdmin):
    list_display = ('student', 'book', 'borrow_date', 'due_date', 'return_date', 
                   'status', 'fine_amount', 'fine_paid')
    list_filter = ('status', 'fine_paid', 'semester')
    search_fields = ('student__registration_number', 'book__title')
    ordering = ('-borrow_date',)
    readonly_fields = ('created_at', 'updated_at')
    actions = ['calculate_fines']
    
    def calculate_fines(self, request, queryset):
        for borrowing in queryset:
            borrowing.calculate_fine()
        self.message_user(request, f"Fines calculated for {queryset.count()} records")
    calculate_fines.short_description = "Calculate fines for selected borrowings"

# ============= TIMETABLE & ATTENDANCE =============
@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ('name', 'programme', 'academic_year', 'semester', 'year_of_study', 
                   'is_published', 'created_by')
    list_filter = ('is_published', 'academic_year', 'semester', 'year_of_study')
    search_fields = ('name', 'programme__name')
    ordering = ('-academic_year__start_date',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(TimetableSlot)
class TimetableSlotAdmin(admin.ModelAdmin):
    list_display = ('timetable', 'day_of_week', 'start_time', 'end_time', 'unit_allocation', 
                   'slot_type', 'venue')
    list_filter = ('day_of_week', 'slot_type', 'timetable__programme')
    search_fields = ('venue', 'unit_allocation__programme_unit__unit__name')
    ordering = ('timetable', 'day_of_week', 'start_time')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'unit_allocation', 'attendance_date', 'status', 'marked_by')
    list_filter = ('status', 'attendance_date', 'unit_allocation__programme_unit__programme')
    search_fields = ('student__registration_number',)
    ordering = ('-attendance_date',)
    readonly_fields = ('created_at', 'updated_at')

# ============= COMMUNICATION =============
@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'announcement_type', 'target_audience', 'is_published', 
                   'is_pinned', 'created_by', 'created_at')
    list_filter = ('announcement_type', 'target_audience', 'is_published', 'is_pinned')
    search_fields = ('title', 'content')
    ordering = ('-is_pinned', '-created_at')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'start_date', 'end_date', 'venue', 
                   'registration_required', 'is_published')
    list_filter = ('event_type', 'is_published', 'registration_required')
    search_fields = ('title', 'description', 'venue')
    ordering = ('start_date',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'sender', 'recipient', 'category', 'status', 
                   'priority', 'is_read', 'created_at')
    list_filter = ('status', 'category', 'priority', 'is_read')
    search_fields = ('subject', 'message', 'sender__username', 'recipient__username')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

# ============= PROCUREMENT =============
@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('supplier_code', 'name', 'contact_person', 'phone_number', 
                   'email', 'rating', 'is_active')
    list_filter = ('is_active', 'rating')
    search_fields = ('supplier_code', 'name', 'contact_person', 'email')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ProcurementCategory)
class ProcurementCategoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'parent_category')
    search_fields = ('name', 'code')
    ordering = ('name',)

class RequisitionItemInline(admin.TabularInline):
    model = RequisitionItem
    extra = 1
    fields = ('category', 'item_description', 'quantity', 'unit_of_measure', 
             'estimated_unit_price', 'total_estimated_price')
    readonly_fields = ('total_estimated_price',)

@admin.register(PurchaseRequisition)
class PurchaseRequisitionAdmin(admin.ModelAdmin):
    list_display = ('requisition_number', 'department', 'requested_by', 'status', 
                   'created_at', 'get_total_items')
    list_filter = ('status', 'department', 'academic_year')
    search_fields = ('requisition_number', 'purpose')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [RequisitionItemInline]
    
    def get_total_items(self, obj):
        return obj.items.count()
    get_total_items.short_description = 'Total Items'

@admin.register(RequisitionItem)
class RequisitionItemAdmin(admin.ModelAdmin):
    list_display = ('requisition', 'category', 'item_description', 'quantity', 
                   'unit_of_measure', 'total_estimated_price')
    list_filter = ('category', 'requisition__status')
    search_fields = ('item_description', 'requisition__requisition_number')
    readonly_fields = ('total_estimated_price',)



from django.contrib import admin
from .models import (
    SemesterReport, ResitExam, UnitEnrollment, EnrollmentPeriod
)


@admin.register(SemesterReport)
class SemesterReportAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'from_year_of_study', 'from_semester_number',
        'to_year_of_study', 'to_semester_number', 'status',
        'is_eligible', 'failed_units_count', 'report_date'
    ]
    list_filter = [
        'status', 'is_eligible', 'to_semester',
        'to_academic_year', 'to_year_of_study'
    ]
    search_fields = [
        'student__registration_number',
        'student__user__first_name',
        'student__user__last_name'
    ]
    readonly_fields = [
        'report_date', 'eligibility_checked_at',
        'created_at', 'updated_at'
    ]
    fieldsets = (
        ('Student Information', {
            'fields': ('student',)
        }),
        ('Progression Details', {
            'fields': (
                ('from_academic_year', 'to_academic_year'),
                ('from_semester', 'to_semester'),
                ('from_year_of_study', 'to_year_of_study'),
                ('from_semester_number', 'to_semester_number'),
            )
        }),
        ('Eligibility', {
            'fields': (
                'failed_units_count',
                'is_eligible',
                'eligibility_checked_at',
                'eligibility_remarks',
            )
        }),
        ('Financial Status', {
            'fields': (
                'fee_balance',
                'is_financially_cleared',
                'financial_clearance_date',
            )
        }),
        ('Academic Performance', {
            'fields': (
                'previous_semester_gpa',
                'cumulative_gpa',
                'total_credits_earned',
            )
        }),
        ('Status & Approval', {
            'fields': (
                'status',
                'approved_by',
                'approval_date',
                'rejection_reason',
                'remarks',
            )
        }),
        ('Timestamps', {
            'fields': (
                'report_date',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_reports', 'reject_reports']
    
    def approve_reports(self, request, queryset):
        from django.utils import timezone
        count = queryset.update(
            status='approved',
            approved_by=request.user,
            approval_date=timezone.now()
        )
        self.message_user(request, f'{count} report(s) approved successfully.')
    approve_reports.short_description = 'Approve selected reports'
    
    def reject_reports(self, request, queryset):
        count = queryset.update(status='rejected')
        self.message_user(request, f'{count} report(s) rejected.')
    reject_reports.short_description = 'Reject selected reports'


@admin.register(ResitExam)
class ResitExamAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'get_unit_code', 'original_grade',
        'resit_grade', 'resit_semester', 'status',
        'fee_paid', 'attendance', 'registration_date'
    ]
    list_filter = [
        'status', 'fee_paid', 'attendance',
        'resit_semester', 'original_semester'
    ]
    search_fields = [
        'student__registration_number',
        'student__user__first_name',
        'student__user__last_name',
        'original_result__programme_unit__unit__code',
        'original_result__programme_unit__unit__name'
    ]
    readonly_fields = [
        'registration_date', 'created_at', 'updated_at'
    ]
    fieldsets = (
        ('Student & Unit', {
            'fields': (
                'student',
                'original_result',
                'resit_semester',
            )
        }),
        ('Original Attempt', {
            'fields': (
                'original_semester',
                ('original_marks', 'original_grade', 'original_grade_point'),
            )
        }),
        ('Resit Details', {
            'fields': (
                ('resit_marks', 'resit_grade', 'resit_grade_point'),
                ('exam_date', 'exam_venue'),
                'attendance',
            )
        }),
        ('Fee Payment', {
            'fields': (
                'resit_fee_amount',
                'fee_paid',
                ('payment_reference', 'payment_date'),
            )
        }),
        ('Status & Approval', {
            'fields': (
                'status',
                'approved_by',
                'approval_date',
            )
        }),
        ('Marking', {
            'fields': (
                'marked_by',
                'marking_date',
                'remarks',
            )
        }),
        ('Timestamps', {
            'fields': (
                'registration_date',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_resits', 'mark_as_completed']
    
    def get_unit_code(self, obj):
        return obj.original_result.programme_unit.unit.code
    get_unit_code.short_description = 'Unit Code'
    
    def approve_resits(self, request, queryset):
        from django.utils import timezone
        count = queryset.update(
            status='approved',
            approved_by=request.user,
            approval_date=timezone.now()
        )
        self.message_user(request, f'{count} resit exam(s) approved.')
    approve_resits.short_description = 'Approve selected resit exams'
    
    def mark_as_completed(self, request, queryset):
        count = queryset.update(status='completed')
        self.message_user(request, f'{count} resit exam(s) marked as completed.')
    mark_as_completed.short_description = 'Mark as completed'


@admin.register(UnitEnrollment)
class UnitEnrollmentAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'get_unit_code', 'semester',
        'enrollment_type', 'status', 'enrollment_date'
    ]
    list_filter = [
        'status', 'enrollment_type', 'semester'
    ]
    search_fields = [
        'student__registration_number',
        'student__user__first_name',
        'student__user__last_name',
        'programme_unit__unit__code',
        'programme_unit__unit__name'
    ]
    readonly_fields = [
        'enrollment_date', 'created_at', 'updated_at'
    ]
    fieldsets = (
        ('Enrollment Details', {
            'fields': (
                'student',
                'semester_report',
                'programme_unit',
                'semester',
                'enrollment_type',
            )
        }),
        ('Resit Link', {
            'fields': ('resit_exam',),
            'classes': ('collapse',)
        }),
        ('Status & Approval', {
            'fields': (
                'status',
                'approved_by',
                'approval_date',
                'rejection_reason',
                'remarks',
            )
        }),
        ('Timestamps', {
            'fields': (
                'enrollment_date',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_enrollments', 'reject_enrollments']
    
    def get_unit_code(self, obj):
        return obj.programme_unit.unit.code
    get_unit_code.short_description = 'Unit Code'
    
    def approve_enrollments(self, request, queryset):
        from django.utils import timezone
        count = queryset.update(
            status='approved',
            approved_by=request.user,
            approval_date=timezone.now()
        )
        self.message_user(request, f'{count} enrollment(s) approved.')
    approve_enrollments.short_description = 'Approve selected enrollments'
    
    def reject_enrollments(self, request, queryset):
        count = queryset.update(status='rejected')
        self.message_user(request, f'{count} enrollment(s) rejected.')
    reject_enrollments.short_description = 'Reject selected enrollments'

@admin.register(EnrollmentPeriod)
class EnrollmentPeriodAdmin(admin.ModelAdmin):
    list_display = [
        'semester', 'start_date', 'end_date',
        'is_active', 'is_enrollment_open_display',
        'is_resit_enrollment_open_display'
    ]
    list_filter = ['is_active', 'semester']
    readonly_fields = [
        'is_enrollment_open_display',
        'is_resit_enrollment_open_display',
        'created_at', 'updated_at'
    ]
    fieldsets = (
        ('Semester', {
            'fields': ('semester',)
        }),
        ('Normal Enrollment Period', {
            'fields': (
                ('start_date', 'end_date'),
                'is_enrollment_open_display',
            )
        }),
        ('Resit Enrollment Period', {
            'fields': (
                ('resit_start_date', 'resit_end_date'),
                'is_resit_enrollment_open_display',
            )
        }),
        ('Status', {
            'fields': (
                'is_active',
                'remarks',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    def is_enrollment_open_display(self, obj):
        # Check if object exists and has the required dates
        if not obj or not obj.pk or not obj.start_date or not obj.end_date:
            return None
        return obj.is_enrollment_open()
    is_enrollment_open_display.short_description = 'Enrollment Open'
    is_enrollment_open_display.boolean = True
    
    def is_resit_enrollment_open_display(self, obj):
        # Check if object exists and has the required dates
        if not obj or not obj.pk or not obj.resit_start_date or not obj.resit_end_date:
            return None
        return obj.is_resit_enrollment_open()
    is_resit_enrollment_open_display.short_description = 'Resit Enrollment Open'
    is_resit_enrollment_open_display.boolean = True

# admin.py - Add these to your Django admin
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import TeachingMaterial, MaterialDownload, MaterialComment


@admin.register(TeachingMaterial)
class TeachingMaterialAdmin(admin.ModelAdmin):
    list_display = [
        'topic', 'unit_code', 'week_number', 'material_type', 
        'file_type', 'is_published', 'upload_date', 'download_count', 
        'view_count', 'uploaded_by'
    ]
    list_filter = [
        'material_type', 'file_type', 'is_published', 'week_number',
        'unit_allocation__semester', 'upload_date'
    ]
    search_fields = [
        'topic', 'description', 
        'unit_allocation__programme_unit__unit__code',
        'unit_allocation__programme_unit__unit__name',
        'uploaded_by__username', 'uploaded_by__first_name', 'uploaded_by__last_name'
    ]
    readonly_fields = [
        'upload_date', 'download_count', 'view_count', 
        'file_size', 'created_at', 'updated_at', 'display_file'
    ]
    
    fieldsets = (
        ('Material Information', {
            'fields': (
                'unit_allocation', 'week_number', 'material_type', 
                'file_type', 'topic', 'description'
            )
        }),
        ('Upload', {
            'fields': ('file', 'display_file', 'external_link', 'file_size')
        }),
        ('Publishing', {
            'fields': ('is_published', 'publish_date', 'uploaded_by')
        }),
        ('Statistics', {
            'fields': ('download_count', 'view_count', 'upload_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'upload_date'
    
    def unit_code(self, obj):
        return obj.unit_allocation.programme_unit.unit.code
    unit_code.short_description = 'Unit Code'
    unit_code.admin_order_field = 'unit_allocation__programme_unit__unit__code'
    
    def display_file(self, obj):
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">View File</a>',
                obj.file.url
            )
        elif obj.external_link:
            return format_html(
                '<a href="{}" target="_blank">External Link</a>',
                obj.external_link
            )
        return '-'
    display_file.short_description = 'File/Link'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'unit_allocation__programme_unit__unit',
            'unit_allocation__lecturer',
            'uploaded_by'
        )


@admin.register(MaterialDownload)
class MaterialDownloadAdmin(admin.ModelAdmin):
    list_display = [
        'material_topic', 'student_name', 'student_reg_no', 
        'download_date', 'ip_address'
    ]
    list_filter = ['download_date']
    search_fields = [
        'material__topic',
        'student__registration_number',
        'student__user__first_name',
        'student__user__last_name'
    ]
    readonly_fields = ['material', 'student', 'download_date', 'ip_address', 'user_agent']
    date_hierarchy = 'download_date'
    
    def material_topic(self, obj):
        return obj.material.topic
    material_topic.short_description = 'Material'
    
    def student_name(self, obj):
        return obj.student.user.get_full_name()
    student_name.short_description = 'Student Name'
    
    def student_reg_no(self, obj):
        return obj.student.registration_number
    student_reg_no.short_description = 'Reg. Number'
    
    def has_add_permission(self, request):
        return False
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('material', 'student__user')


@admin.register(MaterialComment)
class MaterialCommentAdmin(admin.ModelAdmin):
    list_display = [
        'material_topic', 'student_name', 'comment_preview', 
        'is_resolved', 'created_at', 'parent_comment'
    ]
    list_filter = ['is_resolved', 'created_at']
    search_fields = [
        'material__topic',
        'student__registration_number',
        'student__user__first_name',
        'student__user__last_name',
        'comment'
    ]
    readonly_fields = ['material', 'student', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Comment Information', {
            'fields': ('material', 'student', 'comment', 'parent_comment')
        }),
        ('Status', {
            'fields': ('is_resolved',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def material_topic(self, obj):
        return obj.material.topic
    material_topic.short_description = 'Material'
    
    def student_name(self, obj):
        return obj.student.user.get_full_name()
    student_name.short_description = 'Student'
    
    def comment_preview(self, obj):
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
    comment_preview.short_description = 'Comment'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('material', 'student__user', 'parent_comment')


# Custom admin actions
def publish_materials(modeladmin, request, queryset):
    """Bulk publish materials"""
    from django.utils import timezone
    count = queryset.filter(is_published=False).update(
        is_published=True,
        publish_date=timezone.now()
    )
    modeladmin.message_user(
        request,
        f'{count} material(s) published successfully.'
    )
publish_materials.short_description = 'Publish selected materials'

def unpublish_materials(modeladmin, request, queryset):
    """Bulk unpublish materials"""
    count = queryset.filter(is_published=True).update(is_published=False)
    modeladmin.message_user(
        request,
        f'{count} material(s) unpublished successfully.'
    )
unpublish_materials.short_description = 'Unpublish selected materials'

# Add actions to TeachingMaterialAdmin
TeachingMaterialAdmin.actions = [publish_materials, unpublish_materials]

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    StudentIDType, StudentIDFeeStructure, StudentIDApplication,
    StudentIDCard, StudentIDPayment, IDCardNotification
)


# ============= STUDENT ID TYPE ADMIN =============
@admin.register(StudentIDType)
class StudentIDTypeAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'name', 'id_type', 'base_price', 'validity_period_months',
        'processing_days', 'rush_processing_days', 'is_active_badge', 'created_at'
    ]
    list_filter = ['id_type', 'is_active', 'created_at']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'id_type', 'description')
        }),
        ('Pricing & Validity', {
            'fields': ('base_price', 'validity_period_months')
        }),
        ('Processing Times', {
            'fields': ('processing_days', 'rush_processing_days')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-size: 11px;">Active</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">Inactive</span>'
        )
    is_active_badge.short_description = 'Status'


# ============= STUDENT ID FEE STRUCTURE ADMIN =============
@admin.register(StudentIDFeeStructure)
class StudentIDFeeStructureAdmin(admin.ModelAdmin):
    list_display = [
        'id_type', 'academic_year', 'base_fee', 'rush_processing_fee',
        'replacement_fee', 'digital_only_fee', 'effective_from',
        'effective_to', 'is_active_badge'
    ]
    list_filter = ['is_active', 'academic_year', 'id_type', 'effective_from']
    search_fields = ['id_type__name', 'id_type__code', 'academic_year__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'effective_from'
    
    fieldsets = (
        ('ID Type & Academic Year', {
            'fields': ('id_type', 'academic_year')
        }),
        ('Fee Structure', {
            'fields': (
                'base_fee', 'rush_processing_fee', 
                'replacement_fee', 'digital_only_fee'
            )
        }),
        ('Effective Period', {
            'fields': ('effective_from', 'effective_to')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-size: 11px;">Active</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">Inactive</span>'
        )
    is_active_badge.short_description = 'Status'


# ============= STUDENT ID APPLICATION ADMIN =============
class StudentIDPaymentInline(admin.TabularInline):
    model = StudentIDPayment
    extra = 0
    readonly_fields = [
        'payment_reference', 'amount', 'payment_method', 'status',
        'transaction_id', 'mpesa_receipt_number', 'payment_date'
    ]
    can_delete = False
    fields = [
        'payment_reference', 'amount', 'payment_method', 'status',
        'mpesa_receipt_number', 'payment_date'
    ]


class IDCardNotificationInline(admin.TabularInline):
    model = IDCardNotification
    extra = 0
    readonly_fields = ['notification_type', 'title', 'is_read', 'sent_at']
    can_delete = False
    fields = ['notification_type', 'title', 'sent_via_email', 'sent_via_sms', 'is_read', 'sent_at']


@admin.register(StudentIDApplication)
class StudentIDApplicationAdmin(admin.ModelAdmin):
    list_display = [
        'application_number', 'student_link', 'id_type', 'application_reason',
        'status_badge', 'is_rush_badge', 'amount_due', 'amount_paid',
        'balance_display', 'payment_status_badge', 'application_date'
    ]
    list_filter = [
        'status', 'application_reason', 'is_rush_processing',
        'is_replacement', 'application_date', 'id_type'
    ]
    search_fields = [
        'application_number', 'student__registration_number',
        'student__user__first_name', 'student__user__last_name',
        'payment_reference'
    ]
    readonly_fields = [
        'application_number', 'application_date', 'submitted_date',
        'amount_due', 'amount_paid', 'balance', 'is_paid',
        'created_at', 'updated_at', 'photo_preview', 'photo_back_preview'
    ]
    date_hierarchy = 'application_date'
    inlines = [StudentIDPaymentInline, IDCardNotificationInline]
    
    fieldsets = (
        ('Application Information', {
            'fields': (
                'application_number', 'student', 'id_type', 'fee_structure'
            )
        }),
        ('Reason & Details', {
            'fields': (
                'application_reason', 'reason_details',
                'is_rush_processing', 'is_replacement'
            )
        }),
        ('Photos', {
            'fields': ('photo', 'photo_preview', 'photo_back', 'photo_back_preview')
        }),
        ('Status & Dates', {
            'fields': (
                'status', 'application_date', 'submitted_date',
                'estimated_completion_date', 'actual_completion_date'
            )
        }),
        ('Payment Information', {
            'fields': (
                'amount_due', 'amount_paid', 'balance', 'is_paid',
                'payment_reference', 'payment_date'
            )
        }),
        ('Pickup/Delivery', {
            'fields': (
                'pick_up_location', 'pick_up_code',
                'digital_id_url', 'digital_id_sent_date'
            )
        }),
        ('Review', {
            'fields': (
                'reviewed_by', 'review_date', 'review_notes'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_under_review', 'mark_as_payment_pending', 'mark_as_in_production']
    
    def student_link(self, obj):
        url = reverse('admin:portal_student_change', args=[obj.student.id])
        return format_html('<a href="{}">{}</a>', url, obj.student.registration_number)
    student_link.short_description = 'Student'
    
    def status_badge(self, obj):
        colors = {
            'draft': '#6c757d',
            'submitted': '#007bff',
            'under_review': '#17a2b8',
            'payment_pending': '#ffc107',
            'payment_confirmed': '#28a745',
            'in_production': '#fd7e14',
            'ready_for_pickup': '#20c997',
            'delivered': '#28a745',
            'completed': '#28a745',
            'rejected': '#dc3545',
            'cancelled': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def is_rush_badge(self, obj):
        if obj.is_rush_processing:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-size: 11px;">RUSH</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">Normal</span>'
        )
    is_rush_badge.short_description = 'Processing'
    
    def balance_display(self, obj):
        balance = obj.balance
        if balance > 0:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">{:,.2f}</span>',
                balance
            )
        return format_html(
            '<span style="color: #28a745; font-weight: bold;">0.00</span>'
        )
    balance_display.short_description = 'Balance'
    
    def payment_status_badge(self, obj):
        if obj.is_paid:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-size: 11px;">Paid</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">Unpaid</span>'
        )
    payment_status_badge.short_description = 'Payment'
    
    def photo_preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="max-width: 150px; max-height: 150px;" />',
                obj.photo.url
            )
        return "No photo"
    photo_preview.short_description = 'Photo Preview'
    
    def photo_back_preview(self, obj):
        if obj.photo_back:
            return format_html(
                '<img src="{}" style="max-width: 150px; max-height: 150px;" />',
                obj.photo_back.url
            )
        return "No back photo"
    photo_back_preview.short_description = 'Back Photo Preview'
    
    def mark_as_under_review(self, request, queryset):
        updated = queryset.update(status='under_review', review_date=timezone.now())
        self.message_user(request, f'{updated} application(s) marked as under review.')
    mark_as_under_review.short_description = 'Mark selected as Under Review'
    
    def mark_as_payment_pending(self, request, queryset):
        updated = queryset.update(status='payment_pending')
        self.message_user(request, f'{updated} application(s) marked as payment pending.')
    mark_as_payment_pending.short_description = 'Mark selected as Payment Pending'
    
    def mark_as_in_production(self, request, queryset):
        updated = queryset.filter(status='payment_confirmed').update(status='in_production')
        self.message_user(request, f'{updated} application(s) moved to production.')
    mark_as_in_production.short_description = 'Move to Production'


# ============= STUDENT ID CARD ADMIN =============
@admin.register(StudentIDCard)
class StudentIDCardAdmin(admin.ModelAdmin):
    list_display = [
        'card_number', 'student_link', 'application_link', 'card_type',
        'issue_date', 'expiry_date', 'status_badge', 'expired_badge',
        'pick_up_date'
    ]
    list_filter = ['status', 'card_type', 'issue_date', 'expiry_date']
    search_fields = [
        'card_number', 'student__registration_number',
        'student__user__first_name', 'student__user__last_name',
        'barcode'
    ]
    readonly_fields = [
        'card_number', 'is_expired', 'created_at', 'updated_at',
        'qr_code_preview', 'digital_id_preview'
    ]
    date_hierarchy = 'issue_date'
    
    fieldsets = (
        ('Card Information', {
            'fields': ('card_number', 'student', 'application', 'card_type')
        }),
        ('Validity', {
            'fields': ('issue_date', 'expiry_date', 'status', 'is_expired')
        }),
        ('Security Features', {
            'fields': ('qr_code', 'qr_code_preview', 'barcode', 'security_features')
        }),
        ('Digital ID', {
            'fields': ('digital_id_file', 'digital_id_preview', 'digital_id_hash')
        }),
        ('Pickup Information', {
            'fields': (
                'picked_up_by', 'pick_up_date',
                'received_signature', 'last_verified'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_active', 'mark_as_inactive', 'mark_as_expired']
    
    def student_link(self, obj):
        url = reverse('admin:portal_student_change', args=[obj.student.id])
        return format_html('<a href="{}">{}</a>', url, obj.student.registration_number)
    student_link.short_description = 'Student'
    
    def application_link(self, obj):
        url = reverse('admin:your_app_studentidapplication_change', args=[obj.application.id])
        return format_html('<a href="{}">{}</a>', url, obj.application.application_number)
    application_link.short_description = 'Application'
    
    def status_badge(self, obj):
        colors = {
            'active': '#28a745',
            'inactive': '#6c757d',
            'lost': '#dc3545',
            'damaged': '#ffc107',
            'expired': '#dc3545',
            'replaced': '#17a2b8',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def expired_badge(self, obj):
        if obj.is_expired:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-size: 11px;">Expired</span>'
            )
        return format_html(
            '<span style="background-color: #28a745; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">Valid</span>'
        )
    expired_badge.short_description = 'Validity'
    
    def qr_code_preview(self, obj):
        if obj.qr_code:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px;" />',
                obj.qr_code.url
            )
        return "No QR code"
    qr_code_preview.short_description = 'QR Code Preview'
    
    def digital_id_preview(self, obj):
        if obj.digital_id_file:
            return format_html(
                '<a href="{}" target="_blank">View Digital ID</a>',
                obj.digital_id_file.url
            )
        return "No digital ID file"
    digital_id_preview.short_description = 'Digital ID'
    
    def mark_as_active(self, request, queryset):
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} card(s) marked as active.')
    mark_as_active.short_description = 'Mark selected as Active'
    
    def mark_as_inactive(self, request, queryset):
        updated = queryset.update(status='inactive')
        self.message_user(request, f'{updated} card(s) marked as inactive.')
    mark_as_inactive.short_description = 'Mark selected as Inactive'
    
    def mark_as_expired(self, request, queryset):
        updated = queryset.update(status='expired')
        self.message_user(request, f'{updated} card(s) marked as expired.')
    mark_as_expired.short_description = 'Mark selected as Expired'


# ============= STUDENT ID PAYMENT ADMIN =============
@admin.register(StudentIDPayment)
class StudentIDPaymentAdmin(admin.ModelAdmin):
    list_display = [
        'payment_reference', 'application_link', 'amount',
        'payment_method', 'status_badge', 'payment_date',
        'mpesa_receipt_number', 'confirmed_date'
    ]
    list_filter = ['status', 'payment_method', 'payment_date']
    search_fields = [
        'payment_reference', 'transaction_id', 'mpesa_receipt_number',
        'phone_number', 'application__application_number',
        'application__student__registration_number'
    ]
    readonly_fields = [
        'payment_reference', 'payment_date', 'created_at', 'updated_at'
    ]
    date_hierarchy = 'payment_date'
    
    fieldsets = (
        ('Payment Information', {
            'fields': (
                'payment_reference', 'application', 'amount',
                'payment_method', 'status'
            )
        }),
        ('Transaction Details', {
            'fields': (
                'transaction_id', 'merchant_request_id',
                'checkout_request_id'
            )
        }),
        ('M-Pesa Details', {
            'fields': ('mpesa_receipt_number', 'phone_number')
        }),
        ('Dates', {
            'fields': ('payment_date', 'confirmed_date')
        }),
        ('Response', {
            'fields': ('result_code', 'result_description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_completed', 'mark_as_failed']
    
    def application_link(self, obj):
        url = reverse('admin:your_app_studentidapplication_change', args=[obj.application.id])
        return format_html('<a href="{}">{}</a>', url, obj.application.application_number)
    application_link.short_description = 'Application'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'completed': '#28a745',
            'failed': '#dc3545',
            'reversed': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed', confirmed_date=timezone.now())
        self.message_user(request, f'{updated} payment(s) marked as completed.')
    mark_as_completed.short_description = 'Mark selected as Completed'
    
    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} payment(s) marked as failed.')
    mark_as_failed.short_description = 'Mark selected as Failed'


# ============= ID CARD NOTIFICATION ADMIN =============
@admin.register(IDCardNotification)
class IDCardNotificationAdmin(admin.ModelAdmin):
    list_display = [
        'student_link', 'notification_type', 'title',
        'delivery_methods', 'is_read_badge', 'sent_at'
    ]
    list_filter = [
        'notification_type', 'is_read', 'sent_via_email',
        'sent_via_sms', 'sent_via_portal', 'sent_at'
    ]
    search_fields = [
        'student__registration_number', 'student__user__first_name',
        'student__user__last_name', 'title', 'message',
        'application__application_number'
    ]
    readonly_fields = ['sent_at', 'created_at', 'read_date']
    date_hierarchy = 'sent_at'
    
    fieldsets = (
        ('Notification Details', {
            'fields': (
                'student', 'application', 'notification_type',
                'title', 'message'
            )
        }),
        ('Delivery Methods', {
            'fields': ('sent_via_email', 'sent_via_sms', 'sent_via_portal')
        }),
        ('Status', {
            'fields': ('is_read', 'read_date')
        }),
        ('Tracking', {
            'fields': ('email_message_id', 'sms_message_id')
        }),
        ('Timestamps', {
            'fields': ('sent_at', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def student_link(self, obj):
        url = reverse('admin:portal_student_change', args=[obj.student.id])
        return format_html('<a href="{}">{}</a>', url, obj.student.registration_number)
    student_link.short_description = 'Student'
    
    def delivery_methods(self, obj):
        methods = []
        if obj.sent_via_email:
            methods.append('<span style="background-color: #007bff; color: white; '
                         'padding: 2px 6px; border-radius: 3px; font-size: 10px;">Email</span>')
        if obj.sent_via_sms:
            methods.append('<span style="background-color: #28a745; color: white; '
                         'padding: 2px 6px; border-radius: 3px; font-size: 10px;">SMS</span>')
        if obj.sent_via_portal:
            methods.append('<span style="background-color: #17a2b8; color: white; '
                         'padding: 2px 6px; border-radius: 3px; font-size: 10px;">Portal</span>')
        return format_html(' '.join(methods) if methods else 'None')
    delivery_methods.short_description = 'Sent Via'
    
    def is_read_badge(self, obj):
        if obj.is_read:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-size: 11px;">Read</span>'
            )
        return format_html(
            '<span style="background-color: #ffc107; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">Unread</span>'
        )
    is_read_badge.short_description = 'Read Status'
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True, read_date=timezone.now())
        self.message_user(request, f'{updated} notification(s) marked as read.')
    mark_as_read.short_description = 'Mark selected as Read'
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False, read_date=None)
        self.message_user(request, f'{updated} notification(s) marked as unread.')
    mark_as_unread.short_description = 'Mark selected as Unread'


from django.contrib import admin
from .models import (
    AIKnowledgeBase, ChatSession, ChatMessage,
    AIPersonalization, ProactiveAIAlert, AITrainingData,
    AIAnalytics, AIModelVersion, QuickAction
)

@admin.register(AIKnowledgeBase)
class AIKnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ['question', 'category', 'status', 'confidence_score', 'usage_count']
    list_filter = ['category', 'status', 'requires_authentication']
    search_fields = ['question', 'answer', 'keywords']
    ordering = ['-usage_count']

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'user', 'is_authenticated', 'message_count', 'started_at', 'status']
    list_filter = ['status', 'is_authenticated', 'started_at']
    search_fields = ['user__username', 'session_id']

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['message_id', 'session', 'message_type', 'detected_intent', 'timestamp']
    list_filter = ['message_type', 'detected_intent', 'was_helpful']
    search_fields = ['message_text']

@admin.register(ProactiveAIAlert)
class ProactiveAIAlertAdmin(admin.ModelAdmin):
    list_display = ['alert_type', 'user', 'priority', 'is_read', 'sent_at']
    list_filter = ['alert_type', 'priority', 'is_read']
    search_fields = ['title', 'message']

@admin.register(QuickAction)
class QuickActionAdmin(admin.ModelAdmin):
    list_display = ['name', 'action_type', 'is_active', 'display_order', 'usage_count']
    list_filter = ['action_type', 'is_active']
    ordering = ['display_order']

from django.contrib import admin
from .models import FAQ, SupportTicket, TicketReply, SystemGuide, ContactInfo


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'category', 'display_order', 'views_count', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['question', 'answer']
    ordering = ['category', 'display_order']


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ['ticket_number', 'student', 'category', 'priority', 'status', 'created_at']
    list_filter = ['status', 'category', 'priority', 'created_at']
    search_fields = ['ticket_number', 'subject', 'student__registration_number']
    readonly_fields = ['ticket_number', 'created_at']


@admin.register(TicketReply)
class TicketReplyAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'user', 'is_staff_reply', 'created_at']
    list_filter = ['is_staff_reply', 'created_at']
    search_fields = ['ticket__ticket_number', 'message']


@admin.register(SystemGuide)
class SystemGuideAdmin(admin.ModelAdmin):
    list_display = ['title', 'guide_type', 'display_order', 'views_count', 'is_active']
    list_filter = ['guide_type', 'is_active']
    search_fields = ['title', 'description']
    ordering = ['guide_type', 'display_order']


@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    list_display = ['department', 'email', 'phone_primary', 'display_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['department', 'email']
    ordering = ['display_order']
    

# ============= GOVERNANCE MODELS ADMIN =============

@admin.register(UniversityCouncil)
class UniversityCouncilAdmin(admin.ModelAdmin):
    list_display = ['name', 'member_type', 'organization', 'position', 'appointment_date', 'term_end_date', 'is_active_badge']
    list_filter = ['member_type', 'is_active', 'appointment_date']
    search_fields = ['name', 'organization', 'position', 'email']
    ordering = ['member_type', 'name']
    date_hierarchy = 'appointment_date'
    
    fieldsets = (
        ('Member Information', {
            'fields': ('name', 'member_type', 'organization', 'position')
        }),
        ('Term Details', {
            'fields': ('appointment_date', 'term_end_date', 'is_active')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone_number')
        }),
        ('Additional Details', {
            'fields': ('profile_photo', 'bio'),
            'classes': ('collapse',)
        }),
    )
    
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">●</span> Active')
        return format_html('<span style="color: red;">●</span> Inactive')
    is_active_badge.short_description = 'Status'


@admin.register(SenateSession)
class SenateSessionAdmin(admin.ModelAdmin):
    list_display = ['session_number', 'session_date', 'venue', 'status', 'chaired_by', 'attendee_count']
    list_filter = ['status', 'session_date', 'academic_year']
    search_fields = ['session_number', 'venue', 'agenda', 'decisions']
    ordering = ['-session_date']
    date_hierarchy = 'session_date'
    filter_horizontal = ['attendees']
    
    fieldsets = (
        ('Session Information', {
            'fields': ('session_number', 'academic_year', 'session_date', 'venue', 'status')
        }),
        ('Session Details', {
            'fields': ('agenda', 'minutes', 'decisions')
        }),
        ('Participants', {
            'fields': ('chaired_by', 'attendees')
        }),
        ('Documents', {
            'fields': ('minutes_document',),
            'classes': ('collapse',)
        }),
    )
    
    def attendee_count(self, obj):
        return obj.attendees.count()
    attendee_count.short_description = 'Attendees'
    
    def save_model(self, request, obj, form, change):
        if not obj.session_number:
            # Auto-generate session number
            year = obj.session_date.year
            last_session = SenateSession.objects.filter(
                session_number__startswith=f'SEN-{year}-'
            ).order_by('-session_number').first()
            
            if last_session:
                last_num = int(last_session.session_number.split('-')[-1])
                next_num = last_num + 1
            else:
                next_num = 1
            
            obj.session_number = f'SEN-{year}-{next_num:03d}'
        
        super().save_model(request, obj, form, change)


@admin.register(ManagementBoardMeeting)
class ManagementBoardMeetingAdmin(admin.ModelAdmin):
    list_display = ['meeting_number', 'meeting_date', 'academic_year', 'has_decisions']
    list_filter = ['meeting_date', 'academic_year']
    search_fields = ['meeting_number', 'agenda', 'decisions']
    ordering = ['-meeting_date']
    date_hierarchy = 'meeting_date'
    
    fieldsets = (
        ('Meeting Information', {
            'fields': ('meeting_number', 'academic_year', 'meeting_date')
        }),
        ('Meeting Content', {
            'fields': ('agenda', 'decisions', 'action_items')
        }),
        ('Documents', {
            'fields': ('minutes_document',),
            'classes': ('collapse',)
        }),
    )
    
    def has_decisions(self, obj):
        if obj.decisions:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: orange;">-</span>')
    has_decisions.short_description = 'Decisions'


# ============= RANKINGS & INFRASTRUCTURE ADMIN =============

@admin.register(InternationalRanking)
class InternationalRankingAdmin(admin.ModelAdmin):
    list_display = ['ranking_type', 'year', 'overall_rank', 'national_rank', 'regional_rank', 'score', 'trend_indicator']
    list_filter = ['ranking_type', 'year']
    search_fields = ['ranking_type', 'analysis']
    ordering = ['-year', 'ranking_type']
    
    fieldsets = (
        ('Ranking Details', {
            'fields': ('ranking_type', 'year')
        }),
        ('Rankings', {
            'fields': ('overall_rank', 'national_rank', 'regional_rank', 'score')
        }),
        ('Category Scores', {
            'fields': ('category_scores',),
            'description': 'JSON field for category-specific scores'
        }),
        ('Analysis', {
            'fields': ('analysis', 'report_document'),
            'classes': ('collapse',)
        }),
    )
    
    def trend_indicator(self, obj):
        # Get previous year ranking
        previous = InternationalRanking.objects.filter(
            ranking_type=obj.ranking_type,
            year=obj.year - 1
        ).first()
        
        if previous and previous.overall_rank and obj.overall_rank:
            if obj.overall_rank < previous.overall_rank:
                return format_html('<span style="color: green;">↑ Improved</span>')
            elif obj.overall_rank > previous.overall_rank:
                return format_html('<span style="color: red;">↓ Declined</span>')
            else:
                return format_html('<span style="color: blue;">→ Same</span>')
        return '-'
    trend_indicator.short_description = 'Trend'


@admin.register(CapitalProject)
class CapitalProjectAdmin(admin.ModelAdmin):
    list_display = ['project_number', 'project_name', 'location', 'total_budget', 'amount_spent', 'completion_percentage', 'status', 'progress_bar']
    list_filter = ['status', 'start_date', 'expected_completion']
    search_fields = ['project_number', 'project_name', 'location', 'contractor']
    ordering = ['-start_date']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Project Information', {
            'fields': ('project_number', 'project_name', 'description', 'location')
        }),
        ('Financial Details', {
            'fields': ('total_budget', 'amount_spent', 'funding_source')
        }),
        ('Implementation', {
            'fields': ('contractor', 'project_manager', 'status')
        }),
        ('Timeline', {
            'fields': ('start_date', 'expected_completion', 'actual_completion', 'completion_percentage')
        }),
    )
    
    readonly_fields = ['project_number']
    
    def progress_bar(self, obj):
        percentage = obj.completion_percentage
        color = 'green' if percentage >= 75 else 'orange' if percentage >= 50 else 'red'
        return format_html(
            '<div style="width:100px; background-color:#f0f0f0; border-radius:3px;">'
            '<div style="width:{}px; background-color:{}; height:20px; border-radius:3px; text-align:center; color:white; line-height:20px;">'
            '{}%</div></div>',
            int(percentage),
            color,
            int(percentage)
        )
    progress_bar.short_description = 'Progress'


@admin.register(RiskRegister)
class RiskRegisterAdmin(admin.ModelAdmin):
    list_display = ['risk_number', 'risk_title', 'risk_category', 'likelihood', 'impact', 'risk_score', 'risk_level', 'risk_owner', 'status']
    list_filter = ['risk_category', 'likelihood', 'impact', 'status']
    search_fields = ['risk_number', 'risk_title', 'risk_description']
    ordering = ['-risk_score', 'risk_category']
    
    fieldsets = (
        ('Risk Identification', {
            'fields': ('risk_number', 'risk_category', 'risk_title', 'risk_description')
        }),
        ('Risk Assessment', {
            'fields': ('likelihood', 'impact', 'risk_score')
        }),
        ('Risk Management', {
            'fields': ('mitigation_strategy', 'risk_owner', 'status', 'review_date')
        }),
    )
    
    readonly_fields = ['risk_number']
    
    def risk_level(self, obj):
        score = obj.risk_score
        if score >= 15:
            return format_html('<span style="background-color:red; color:white; padding:3px 8px; border-radius:3px;">HIGH</span>')
        elif score >= 10:
            return format_html('<span style="background-color:orange; color:white; padding:3px 8px; border-radius:3px;">MEDIUM</span>')
        else:
            return format_html('<span style="background-color:green; color:white; padding:3px 8px; border-radius:3px;">LOW</span>')
    risk_level.short_description = 'Risk Level'
    
    def save_model(self, request, obj, form, change):
        # Calculate risk score
        likelihood_scores = {'rare': 1, 'unlikely': 2, 'possible': 3, 'likely': 4, 'almost_certain': 5}
        impact_scores = {'insignificant': 1, 'minor': 2, 'moderate': 3, 'major': 4, 'catastrophic': 5}
        
        obj.risk_score = likelihood_scores.get(obj.likelihood, 3) * impact_scores.get(obj.impact, 3)
        super().save_model(request, obj, form, change)


# ============= QUALITY ASSURANCE ADMIN =============

@admin.register(TeachingEvaluation)
class TeachingEvaluationAdmin(admin.ModelAdmin):
    list_display = ['unit_code', 'lecturer_name', 'semester', 'total_responses', 'response_rate_display', 'overall_rating', 'status']
    list_filter = ['status', 'semester', 'academic_year']
    search_fields = ['unit_allocation__programme_unit__unit__code', 'unit_allocation__lecturer__user__first_name', 'unit_allocation__lecturer__user__last_name']
    ordering = ['-semester__academic_year__start_date', '-overall_rating']
    
    fieldsets = (
        ('Evaluation Details', {
            'fields': ('unit_allocation', 'academic_year', 'semester')
        }),
        ('Evaluation Period', {
            'fields': ('start_date', 'end_date', 'status')
        }),
        ('Response Data', {
            'fields': ('total_responses', 'total_enrolled', 'response_rate')
        }),
        ('Average Ratings', {
            'fields': ('avg_content_delivery', 'avg_engagement', 'avg_assessment_fairness', 'avg_availability', 'overall_rating')
        }),
        ('Feedback', {
            'fields': ('positive_comments', 'improvement_areas'),
            'classes': ('collapse',)
        }),
        ('Publication', {
            'fields': ('is_published', 'published_date')
        }),
    )
    
    readonly_fields = ['response_rate']
    
    def unit_code(self, obj):
        return obj.unit_allocation.programme_unit.unit.code
    unit_code.short_description = 'Unit'
    
    def lecturer_name(self, obj):
        return obj.unit_allocation.lecturer.user.get_full_name()
    lecturer_name.short_description = 'Lecturer'
    
    def response_rate_display(self, obj):
        rate = obj.response_rate
        color = 'green' if rate >= 70 else 'orange' if rate >= 50 else 'red'
        return format_html('<span style="color:{};">{:.1f}%</span>', color, rate)
    response_rate_display.short_description = 'Response Rate'


@admin.register(ProgrammeReview)
class ProgrammeReviewAdmin(admin.ModelAdmin):
    list_display = ['programme', 'review_type', 'review_date', 'overall_rating', 'status', 'rating_badge']
    list_filter = ['review_type', 'status', 'academic_year']
    search_fields = ['programme__name', 'programme__code', 'review_panel']
    ordering = ['-review_date']
    date_hierarchy = 'review_date'
    
    fieldsets = (
        ('Review Information', {
            'fields': ('programme', 'review_type', 'academic_year', 'review_date', 'review_panel')
        }),
        ('SWOT Analysis', {
            'fields': ('strengths', 'weaknesses', 'opportunities', 'threats')
        }),
        ('Recommendations', {
            'fields': ('recommendations', 'action_plan')
        }),
        ('Ratings', {
            'fields': ('curriculum_rating', 'teaching_quality_rating', 'resources_rating', 
                      'student_satisfaction_rating', 'employability_rating', 'overall_rating')
        }),
        ('Follow-up', {
            'fields': ('follow_up_date', 'follow_up_notes'),
            'classes': ('collapse',)
        }),
        ('Approval', {
            'fields': ('status', 'conducted_by', 'approved_by', 'report_document')
        }),
    )
    
    readonly_fields = ['overall_rating']
    
    def rating_badge(self, obj):
        rating = obj.overall_rating
        if rating >= 4.0:
            color = 'green'
        elif rating >= 3.0:
            color = 'orange'
        else:
            color = 'red'
        return format_html('<span style="color:{};">★ {:.2f}</span>', color, rating)
    rating_badge.short_description = 'Rating'


@admin.register(AuditReport)
class AuditReportAdmin(admin.ModelAdmin):
    list_display = ['audit_number', 'audit_type', 'audit_date', 'school', 'department', 'status', 'has_follow_up']
    list_filter = ['audit_type', 'status', 'audit_date']
    search_fields = ['audit_number', 'auditor_name', 'auditor_organization', 'key_findings']
    ordering = ['-audit_date']
    date_hierarchy = 'audit_date'
    
    fieldsets = (
        ('Audit Information', {
            'fields': ('audit_number', 'audit_type', 'academic_year', 'school', 'department')
        }),
        ('Auditor Details', {
            'fields': ('audit_date', 'auditor_name', 'auditor_organization')
        }),
        ('Findings', {
            'fields': ('executive_summary', 'key_findings', 'non_conformities', 'observations')
        }),
        ('Recommendations', {
            'fields': ('recommendations', 'management_response', 'corrective_actions')
        }),
        ('Timeline', {
            'fields': ('implementation_deadline', 'follow_up_date')
        }),
        ('Status & Documents', {
            'fields': ('status', 'audit_document')
        }),
    )
    
    readonly_fields = ['audit_number']
    
    def has_follow_up(self, obj):
        if obj.follow_up_date:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    has_follow_up.short_description = 'Follow-up'


@admin.register(ComplianceCheck)
class ComplianceCheckAdmin(admin.ModelAdmin):
    list_display = ['school', 'compliance_area', 'check_date', 'status', 'action_required', 'is_resolved', 'deadline']
    list_filter = ['compliance_area', 'status', 'action_required', 'is_resolved']
    search_fields = ['school__name', 'requirement', 'evidence']
    ordering = ['-check_date']
    date_hierarchy = 'check_date'
    
    fieldsets = (
        ('Compliance Details', {
            'fields': ('school', 'compliance_area', 'academic_year', 'check_date')
        }),
        ('Requirements', {
            'fields': ('requirement', 'criteria')
        }),
        ('Status', {
            'fields': ('status', 'evidence', 'gaps')
        }),
        ('Actions', {
            'fields': ('action_required', 'action_plan', 'responsible_person', 'deadline')
        }),
        ('Resolution', {
            'fields': ('is_resolved', 'resolution_date', 'resolution_notes'),
            'classes': ('collapse',)
        }),
        ('Documents', {
            'fields': ('checked_by', 'supporting_documents')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.checked_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(QualityMetric)
class QualityMetricAdmin(admin.ModelAdmin):
    list_display = ['metric_name', 'school', 'programme', 'metric_type', 'target_value', 'actual_value', 'variance_display', 'target_met', 'trend']
    list_filter = ['metric_type', 'measurement_period', 'is_target_met', 'trend', 'school']
    search_fields = ['metric_name', 'description']
    ordering = ['-measurement_date', 'school']
    date_hierarchy = 'measurement_date'
    
    fieldsets = (
        ('Metric Information', {
            'fields': ('school', 'programme', 'metric_type', 'academic_year', 'measurement_period')
        }),
        ('Metric Details', {
            'fields': ('metric_name', 'description', 'unit_of_measure')
        }),
        ('Performance', {
            'fields': ('target_value', 'actual_value', 'is_target_met', 'variance', 'variance_percentage')
        }),
        ('Analysis', {
            'fields': ('trend', 'comments', 'action_items')
        }),
        ('Recording', {
            'fields': ('measurement_date', 'recorded_by')
        }),
    )
    
    readonly_fields = ['variance', 'variance_percentage', 'is_target_met']
    
    def variance_display(self, obj):
        variance = obj.variance_percentage
        if variance >= 0:
            return format_html('<span style="color:green;">+{:.1f}%</span>', variance)
        return format_html('<span style="color:red;">{:.1f}%</span>', variance)
    variance_display.short_description = 'Variance'
    
    def target_met(self, obj):
        if obj.is_target_met:
            return format_html('<span style="color:green;">✓</span>')
        return format_html('<span style="color:red;">✗</span>')
    target_met.short_description = 'Met'


# ============= RESEARCH MODELS ADMIN =============

@admin.register(ResearchProject)
class ResearchProjectAdmin(admin.ModelAdmin):
    list_display = ['project_code', 'title_short', 'project_type', 'school', 'principal_investigator', 'total_budget', 'status', 'duration']
    list_filter = ['project_type', 'status', 'school']
    search_fields = ['project_code', 'title', 'principal_investigator__user__first_name', 'principal_investigator__user__last_name']
    ordering = ['-start_date']
    date_hierarchy = 'start_date'
    filter_horizontal = ['co_investigators']
    
    fieldsets = (
        ('Project Information', {
            'fields': ('project_code', 'title', 'project_type', 'school', 'department')
        }),
        ('Research Team', {
            'fields': ('principal_investigator', 'co_investigators')
        }),
        ('Project Details', {
            'fields': ('abstract', 'objectives', 'methodology', 'expected_outcomes')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date', 'duration_months')
        }),
        ('Funding', {
            'fields': ('total_budget', 'funding_source', 'funds_allocated', 'funds_utilized')
        }),
        ('Status & Outputs', {
            'fields': ('status', 'publications_count', 'patents_count')
        }),
        ('Approval', {
            'fields': ('approved_by', 'approval_date', 'proposal_document', 'final_report')
        }),
    )
    
    readonly_fields = ['project_code']
    
    def title_short(self, obj):
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_short.short_description = 'Title'
    
    def duration(self, obj):
        return f"{obj.duration_months} months"
    duration.short_description = 'Duration'


@admin.register(ResearchGrant)
class ResearchGrantAdmin(admin.ModelAdmin):
    list_display = ['grant_number', 'grant_title_short', 'grant_type', 'funding_agency', 'amount_applied', 'amount_awarded', 'status', 'application_date']
    list_filter = ['grant_type', 'status', 'application_date']
    search_fields = ['grant_number', 'grant_title', 'funding_agency']
    ordering = ['-application_date']
    date_hierarchy = 'application_date'
    filter_horizontal = ['co_applicants']
    
    fieldsets = (
        ('Grant Information', {
            'fields': ('grant_number', 'grant_title', 'grant_type', 'funding_agency')
        }),
        ('Applicants', {
            'fields': ('principal_applicant', 'co_applicants', 'school')
        }),
        ('Financial Details', {
            'fields': ('amount_applied', 'amount_awarded')
        }),
        ('Timeline', {
            'fields': ('application_date', 'decision_date', 'project_start_date', 'project_end_date')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Documents', {
            'fields': ('proposal_document', 'award_letter')
        }),
        ('Reporting', {
            'fields': ('progress_reports', 'final_report_submitted'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['grant_number']
    
    def grant_title_short(self, obj):
        return obj.grant_title[:50] + '...' if len(obj.grant_title) > 50 else obj.grant_title
    grant_title_short.short_description = 'Title'


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ['title_short', 'publication_type', 'corresponding_author', 'year', 'is_peer_reviewed', 'citations_count', 'impact_factor']
    list_filter = ['publication_type', 'year', 'is_peer_reviewed', 'school']
    search_fields = ['title', 'journal_name', 'conference_name', 'publisher', 'doi']
    ordering = ['-publication_date']
    date_hierarchy = 'publication_date'
    filter_horizontal = ['authors']
    
    fieldsets = (
        ('Publication Information', {
            'fields': ('title', 'publication_type', 'publication_date', 'year')
        }),
        ('Authors', {
            'fields': ('authors', 'corresponding_author', 'school')
        }),
        ('Publication Details', {
            'fields': ('journal_name', 'conference_name', 'publisher', 'isbn_issn', 'doi')
        }),
        ('Quality Metrics', {
            'fields': ('is_peer_reviewed', 'impact_factor', 'citations_count')
        }),
        ('Content', {
            'fields': ('abstract', 'keywords'),
            'classes': ('collapse',)
        }),
        ('Links & Files', {
            'fields': ('url', 'pdf_file')
        }),
        ('Research Link', {
            'fields': ('research_project',),
            'classes': ('collapse',)
        }),
    )
    
    def title_short(self, obj):
        return obj.title[:60] + '...' if len(obj.title) > 60 else obj.title
    title_short.short_description = 'Title'


@admin.register(ResearchCenter)
class ResearchCenterAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'school', 'director', 'annual_budget', 'establishment_date', 'is_active']
    list_filter = ['school', 'is_active', 'establishment_date']
    search_fields = ['code', 'name', 'description', 'focus_areas']
    ordering = ['name']
    
    fieldsets = (
        ('Center Information', {
            'fields': ('code', 'name', 'school', 'description')
        }),
        ('Leadership', {
            'fields': ('director', 'deputy_director')
        }),
        ('Research Focus', {
            'fields': ('focus_areas', 'objectives')
        }),
        ('Resources', {
            'fields': ('location', 'facilities', 'annual_budget')
        }),
        ('Contact', {
            'fields': ('email', 'phone_number', 'website')
        }),
        ('Status', {
            'fields': ('establishment_date', 'is_active')
        }),
    )


@admin.register(InnovationProject)
class InnovationProjectAdmin(admin.ModelAdmin):
    list_display = ['project_code', 'title_short', 'school', 'project_lead', 'status', 'technology_readiness_level', 'has_ip_protection']
    list_filter = ['status', 'technology_readiness_level', 'has_ip_protection', 'school']
    search_fields = ['project_code', 'title', 'description']
    ordering = ['-start_date']
    filter_horizontal = ['team_members']
    
    fieldsets = (
        ('Project Information', {
            'fields': ('project_code', 'title', 'school', 'description')
        }),
        ('Team', {
            'fields': ('project_lead', 'team_members')
        }),
        ('Innovation Details', {
            'fields': ('problem_statement', 'solution', 'innovation_type')
        }),
        ('Development', {
            'fields': ('status', 'technology_readiness_level')
        }),
        ('IP & Commercialization', {
            'fields': ('has_ip_protection', 'ip_type', 'ip_reference', 'market_potential', 'target_market')
        }),
        ('Funding', {
            'fields': ('budget', 'funding_received', 'revenue_generated')
        }),
        ('Timeline', {
            'fields': ('start_date', 'expected_completion', 'actual_completion')
        }),
        ('Documents', {
            'fields': ('business_plan', 'technical_document'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['project_code']
    
    def title_short(self, obj):
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_short.short_description = 'Title'


# ============= HR MODELS ADMIN =============

@admin.register(PerformanceAppraisal)
class PerformanceAppraisalAdmin(admin.ModelAdmin):
    list_display = ['lecturer', 'academic_year', 'appraisal_period', 'overall_score', 'overall_rating', 'review_date', 'rating_badge']
    list_filter = ['appraisal_period', 'overall_rating', 'academic_year']
    search_fields = ['lecturer__employee_number', 'lecturer__user__first_name', 'lecturer__user__last_name']
    ordering = ['-review_date']
    date_hierarchy = 'review_date'
    
    fieldsets = (
        ('Appraisal Information', {
            'fields': ('lecturer', 'academic_year', 'appraisal_period', 'review_date')
        }),
        ('Performance Scores (0-100)', {
            'fields': ('teaching_quality', 'research_output', 'service_delivery', 'student_feedback', 'professional_development')
        }),
        ('Overall Performance', {
            'fields': ('overall_score', 'overall_rating')
        }),
        ('Feedback', {
            'fields': ('strengths', 'areas_for_improvement', 'training_needs', 'career_development_plan')
        }),
        ('Goals', {
            'fields': ('goals_set', 'previous_goals_achievement'),
            'classes': ('collapse',)
        }),
        ('Approval', {
            'fields': ('self_assessment', 'hod_comments', 'hod_approved_by', 'dean_comments', 'dean_approved_by', 'appraisal_document')
        }),
    )
    
    readonly_fields = ['overall_score', 'overall_rating']
    
    def rating_badge(self, obj):
        rating_colors = {
            'outstanding': 'green',
            'exceeds': 'blue',
            'meets': 'orange',
            'needs_improvement': 'red',
            'unsatisfactory': 'darkred'
        }
        color = rating_colors.get(obj.overall_rating, 'gray')
        return format_html(
            '<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>',
            color,
            obj.get_overall_rating_display()
        )
    rating_badge.short_description = 'Rating'


@admin.register(StaffPromotion)
class StaffPromotionAdmin(admin.ModelAdmin):
    list_display = ['lecturer', 'current_designation', 'proposed_designation', 'application_date', 'status', 'decision_date']
    list_filter = ['status', 'application_date', 'current_designation', 'proposed_designation']
    search_fields = ['lecturer__employee_number', 'lecturer__user__first_name', 'lecturer__user__last_name']
    ordering = ['-application_date']
    date_hierarchy = 'application_date'
    
    fieldsets = (
        ('Promotion Information', {
            'fields': ('lecturer', 'current_designation', 'proposed_designation', 'academic_year', 'application_date')
        }),
        ('Qualifications', {
            'fields': ('years_in_current_position', 'highest_qualification', 'additional_qualifications')
        }),
        ('Performance Metrics', {
            'fields': ('teaching_years', 'publications_count', 'research_grants_count', 'phd_supervisions')
        }),
        ('Justification', {
            'fields': ('justification', 'supporting_documents')
        }),
        ('HOD Review', {
            'fields': ('hod_recommendation', 'hod_recommended_by', 'hod_recommendation_date'),
            'classes': ('collapse',)
        }),
        ('Dean/School Review', {
            'fields': ('school_recommendation', 'dean_recommended_by', 'dean_recommendation_date'),
            'classes': ('collapse',)
        }),
        ('Final Decision', {
            'fields': ('status', 'final_decision', 'decided_by', 'decision_date')
        }),
        ('Implementation', {
            'fields': ('effective_date', 'new_salary_scale'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StaffTraining)
class StaffTrainingAdmin(admin.ModelAdmin):
    list_display = ['lecturer', 'training_type', 'title', 'organizer', 'start_date', 'duration_days', 'cost', 'status', 'certificate_obtained']
    list_filter = ['training_type', 'status', 'is_sponsored', 'certificate_obtained', 'start_date']
    search_fields = ['title', 'organizer', 'lecturer__user__first_name', 'lecturer__user__last_name']
    ordering = ['-start_date']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Training Information', {
            'fields': ('lecturer', 'training_type', 'title', 'organizer', 'venue')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date', 'duration_days')
        }),
        ('Financial', {
            'fields': ('cost', 'funding_source', 'is_sponsored')
        }),
        ('Outcomes', {
            'fields': ('skills_acquired', 'certificate_obtained', 'certificate_file')
        }),
        ('Relevance', {
            'fields': ('relevance_to_role', 'expected_impact')
        }),
        ('Approval & Status', {
            'fields': ('status', 'approved_by', 'approval_date')
        }),
        ('Post-Training', {
            'fields': ('completion_report', 'report_submitted_date'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DisciplinaryCase)
class DisciplinaryCaseAdmin(admin.ModelAdmin):
    list_display = ['case_number', 'lecturer', 'severity', 'incident_date', 'status', 'decision_date', 'is_appealed']
    list_filter = ['severity', 'status', 'is_appealed', 'incident_date']
    search_fields = ['case_number', 'lecturer__employee_number', 'allegation']
    ordering = ['-reported_date']
    date_hierarchy = 'reported_date'
    
    fieldsets = (
        ('Case Information', {
            'fields': ('case_number', 'lecturer', 'academic_year', 'incident_date', 'reported_date', 'reported_by')
        }),
        ('Case Details', {
            'fields': ('allegation', 'severity', 'evidence', 'witness_statements')
        }),
        ('Investigation', {
            'fields': ('investigating_officer', 'investigation_findings', 'investigation_completed_date'),
            'classes': ('collapse',)
        }),
        ('Hearing', {
            'fields': ('hearing_date', 'hearing_venue', 'hearing_panel', 'hearing_minutes'),
            'classes': ('collapse',)
        }),
        ('Decision', {
            'fields': ('status', 'decision', 'disciplinary_action', 'decided_by', 'decision_date')
        }),
        ('Appeal', {
            'fields': ('is_appealed', 'appeal_details', 'appeal_decision'),
            'classes': ('collapse',)
        }),
        ('Documents', {
            'fields': ('supporting_documents',)
        }),
    )
    
    readonly_fields = ['case_number']


@admin.register(StaffRecruitment)
class StaffRecruitmentAdmin(admin.ModelAdmin):
    list_display = ['recruitment_number', 'position_title', 'position_type', 'school', 'department', 'application_deadline', 'total_applications', 'status']
    list_filter = ['position_type', 'contract_type', 'status', 'advertised_date']
    search_fields = ['recruitment_number', 'position_title', 'school__name', 'department__name']
    ordering = ['-advertised_date']
    date_hierarchy = 'advertised_date'
    
    fieldsets = (
        ('Recruitment Information', {
            'fields': ('recruitment_number', 'school', 'department', 'academic_year')
        }),
        ('Position Details', {
            'fields': ('position_title', 'position_type', 'contract_type', 'number_of_positions', 'salary_scale')
        }),
        ('Requirements', {
            'fields': ('qualifications_required', 'experience_required', 'responsibilities', 'key_competencies')
        }),
        ('Job Details', {
            'fields': ('job_description', 'reporting_to', 'location'),
            'classes': ('collapse',)
        }),
        ('Timeline', {
            'fields': ('advertised_date', 'application_deadline', 'shortlisting_date', 'interview_date', 'expected_start_date')
        }),
        ('Applications', {
            'fields': ('total_applications', 'shortlisted_candidates', 'interviewed_candidates')
        }),
        ('Interview', {
            'fields': ('interview_panel_members', 'interview_venue'),
            'classes': ('collapse',)
        }),
        ('Selection', {
            'fields': ('status', 'selected_candidate_name', 'selected_candidate_email', 'selected_candidate_phone')
        }),
        ('Offer', {
            'fields': ('offer_letter_sent', 'offer_sent_date', 'offer_expiry_date', 'offer_accepted_date'),
            'classes': ('collapse',)
        }),
        ('Contract', {
            'fields': ('contract_start_date', 'contract_end_date', 'probation_period_months'),
            'classes': ('collapse',)
        }),
        ('Approvals', {
            'fields': ('approved_by_hod', 'approved_by_dean', 'approved_by_hr'),
            'classes': ('collapse',)
        }),
        ('Documents', {
            'fields': ('job_advertisement', 'shortlisting_report', 'interview_report', 'offer_letter')
        }),
        ('Notes', {
            'fields': ('recruitment_justification', 'rejection_reason', 'closure_notes'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['recruitment_number']


# ============= FINANCIAL MODELS ADMIN =============

@admin.register(SchoolBudget)
class SchoolBudgetAdmin(admin.ModelAdmin):
    list_display = ['school', 'financial_year', 'total_allocation', 'amount_spent', 'balance', 'utilization_percentage', 'status']
    list_filter = ['status', 'financial_year', 'school']
    search_fields = ['school__name', 'school__code']
    ordering = ['-financial_year__start_date', 'school__name']
    
    fieldsets = (
        ('Budget Information', {
            'fields': ('school', 'financial_year', 'status')
        }),
        ('Budget Amounts', {
            'fields': ('total_allocation', 'amount_spent', 'balance')
        }),
        ('Budget Breakdown', {
            'fields': ('personnel_budget', 'operations_budget', 'development_budget', 'research_budget')
        }),
        ('Approval Workflow', {
            'fields': ('submitted_by', 'submitted_date', 'approved_by', 'approval_date')
        }),
        ('Notes', {
            'fields': ('remarks',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['balance']
    
    def utilization_percentage(self, obj):
        if obj.total_allocation > 0:
            percentage = (obj.amount_spent / obj.total_allocation) * 100
            color = 'red' if percentage > 90 else 'orange' if percentage > 75 else 'green'
            return format_html('<span style="color:{};">{:.1f}%</span>', color, percentage)
        return '0%'
    utilization_percentage.short_description = 'Utilization'


@admin.register(BudgetAllocation)
class BudgetAllocationAdmin(admin.ModelAdmin):
    list_display = ['department', 'school_budget', 'allocation_amount', 'amount_utilized', 'balance', 'utilization_percentage', 'allocation_date']
    list_filter = ['school_budget__financial_year', 'school_budget__school', 'allocation_date']
    search_fields = ['department__name', 'department__code']
    ordering = ['-allocation_date']
    
    fieldsets = (
        ('Allocation Information', {
            'fields': ('school_budget', 'department', 'allocation_date')
        }),
        ('Financial Details', {
            'fields': ('allocation_amount', 'amount_utilized', 'balance', 'utilization_percentage')
        }),
        ('Category Breakdown', {
            'fields': ('personnel', 'operations', 'equipment', 'supplies')
        }),
        ('Allocation Details', {
            'fields': ('allocated_by', 'remarks')
        }),
    )
    
    readonly_fields = ['balance', 'utilization_percentage']


@admin.register(ExpenditureTracking)
class ExpenditureTrackingAdmin(admin.ModelAdmin):
    list_display = ['transaction_number', 'budget_allocation', 'expenditure_type', 'payee_name', 'amount', 'transaction_date', 'status']
    list_filter = ['expenditure_type', 'status', 'transaction_date']
    search_fields = ['transaction_number', 'payee_name', 'description', 'invoice_number']
    ordering = ['-transaction_date']
    date_hierarchy = 'transaction_date'
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('transaction_number', 'budget_allocation', 'expenditure_type', 'description')
        }),
        ('Payee Details', {
            'fields': ('payee_name', 'invoice_number', 'invoice_date')
        }),
        ('Financial', {
            'fields': ('amount', 'transaction_date', 'payment_date')
        }),
        ('Approval', {
            'fields': ('status', 'requested_by', 'approved_by')
        }),
        ('Documents', {
            'fields': ('supporting_document', 'payment_voucher')
        }),
        ('Notes', {
            'fields': ('remarks',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['transaction_number']


@admin.register(RevenueSource)
class RevenueSourceAdmin(admin.ModelAdmin):
    list_display = ['school', 'revenue_type', 'source_name', 'amount', 'received_date', 'receipt_number']
    list_filter = ['revenue_type', 'received_date', 'school', 'academic_year']
    search_fields = ['source_name', 'receipt_number', 'description']
    ordering = ['-received_date']
    date_hierarchy = 'received_date'
    
    fieldsets = (
        ('Revenue Information', {
            'fields': ('school', 'academic_year', 'revenue_type', 'source_name')
        }),
        ('Financial Details', {
            'fields': ('amount', 'received_date', 'receipt_number')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Recording', {
            'fields': ('recorded_by', 'supporting_document')
        }),
        ('Notes', {
            'fields': ('remarks',),
            'classes': ('collapse',)
        }),
    )


# ============= PARTNERSHIP MODELS ADMIN =============

@admin.register(Partnership)
class PartnershipAdmin(admin.ModelAdmin):
    list_display = ['partner_name', 'partnership_type', 'school', 'country', 'start_date', 'end_date', 'status']
    list_filter = ['partnership_type', 'status', 'country', 'school']
    search_fields = ['partner_name', 'description', 'contact_person']
    ordering = ['-start_date']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Partnership Information', {
            'fields': ('school', 'partner_name', 'partnership_type', 'country')
        }),
        ('Contact Details', {
            'fields': ('contact_person', 'contact_email', 'contact_phone')
        }),
        ('Partnership Details', {
            'fields': ('description', 'areas_of_collaboration', 'benefits')
        }),
        ('Management', {
            'fields': ('focal_person', 'status')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date')
        }),
        ('Additional', {
            'fields': ('website', 'logo'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MOU)
class MOUAdmin(admin.ModelAdmin):
    list_display = ['mou_number', 'partnership', 'title_short', 'signing_date', 'expiry_date', 'days_to_expiry', 'status', 'renewal_notice_sent']
    list_filter = ['status', 'signing_date', 'renewal_notice_sent']
    search_fields = ['mou_number', 'title', 'partnership__partner_name']
    ordering = ['expiry_date']
    date_hierarchy = 'signing_date'
    
    fieldsets = (
        ('MOU Information', {
            'fields': ('mou_number', 'partnership', 'title')
        }),
        ('Dates', {
            'fields': ('signing_date', 'effective_date', 'expiry_date')
        }),
        ('Terms', {
            'fields': ('scope', 'deliverables', 'responsibilities')
        }),
        ('Signatories', {
            'fields': ('university_signatory', 'partner_signatory')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Documents', {
            'fields': ('mou_document',)
        }),
        ('Renewal', {
            'fields': ('renewal_notice_sent', 'renewal_date'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('remarks',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['mou_number']
    
    def title_short(self, obj):
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_short.short_description = 'Title'
    
    def days_to_expiry(self, obj):
        from datetime import date
        days = (obj.expiry_date - date.today()).days
        if days < 0:
            return format_html('<span style="color:red;">Expired</span>')
        elif days < 30:
            return format_html('<span style="color:red;">{} days</span>', days)
        elif days < 90:
            return format_html('<span style="color:orange;">{} days</span>', days)
        return format_html('<span style="color:green;">{} days</span>', days)
    days_to_expiry.short_description = 'Expires In'


@admin.register(CollaborativeProject)
class CollaborativeProjectAdmin(admin.ModelAdmin):
    list_display = ['title_short', 'partnership', 'project_leader', 'start_date', 'end_date', 'total_budget', 'status']
    list_filter = ['status', 'start_date']
    search_fields = ['title', 'description', 'partnership__partner_name']
    ordering = ['-start_date']
    date_hierarchy = 'start_date'
    filter_horizontal = ['team_members']
    
    fieldsets = (
        ('Project Information', {
            'fields': ('partnership', 'title', 'description', 'objectives')
        }),
        ('Team', {
            'fields': ('project_leader', 'team_members')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date')
        }),
        ('Budget', {
            'fields': ('total_budget', 'university_contribution', 'partner_contribution')
        }),
        ('Outputs', {
            'fields': ('publications', 'students_trained')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Reports', {
            'fields': ('progress_report', 'final_report'),
            'classes': ('collapse',)
        }),
    )
    
    def title_short(self, obj):
        return obj.title[:60] + '...' if len(obj.title) > 60 else obj.title
    title_short.short_description = 'Title'


@admin.register(AlumniRelation)
class AlumniRelationAdmin(admin.ModelAdmin):
    list_display = ['alumni_name', 'programme', 'graduation_year', 'current_organization', 'engagement_type', 'engagement_date', 'contribution_value']
    list_filter = ['engagement_type', 'graduation_year', 'engagement_date', 'programme']
    search_fields = ['alumni_name', 'current_organization', 'current_position']
    ordering = ['-engagement_date']
    date_hierarchy = 'engagement_date'
    
    fieldsets = (
        ('Alumni Information', {
            'fields': ('alumni_name', 'programme', 'graduation_year', 'current_organization', 'current_position')
        }),
        ('Engagement', {
            'fields': ('engagement_type', 'engagement_date', 'description')
        }),
        ('Impact', {
            'fields': ('students_impacted', 'contribution_value')
        }),
        ('Contact', {
            'fields': ('email', 'phone_number')
        }),
        ('Coordination', {
            'fields': ('coordinated_by', 'remarks')
        }),
    )


# ============= STRATEGIC PLANNING ADMIN =============

@admin.register(StrategicGoal)
class StrategicGoalAdmin(admin.ModelAdmin):
    list_display = ['title_short', 'school', 'category', 'target_year', 'progress_percentage', 'progress_bar', 'status', 'champion']
    list_filter = ['category', 'status', 'school', 'target_year']
    search_fields = ['title', 'description', 'target_metric']
    ordering = ['-progress_percentage', 'target_year']
    
    fieldsets = (
        ('Goal Information', {
            'fields': ('school', 'category', 'title', 'description')
        }),
        ('Timeline', {
            'fields': ('start_year', 'target_year')
        }),
        ('Targets', {
            'fields': ('target_metric', 'baseline_value', 'target_value', 'current_value')
        }),
        ('Progress', {
            'fields': ('progress_percentage',)
        }),
        ('Responsibility', {
            'fields': ('champion', 'status')
        }),
        ('Budget', {
            'fields': ('estimated_budget',)
        }),
        ('Notes', {
            'fields': ('remarks',),
            'classes': ('collapse',)
        }),
    )
    
    def title_short(self, obj):
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_short.short_description = 'Title'
    
    def progress_bar(self, obj):
        percentage = obj.progress_percentage
        color = 'green' if percentage >= 75 else 'orange' if percentage >= 50 else 'red'
        return format_html(
            '<div style="width:100px; background-color:#f0f0f0; border-radius:3px;">'
            '<div style="width:{}px; background-color:{}; height:20px; border-radius:3px; text-align:center; color:white; line-height:20px;">'
            '{}%</div></div>',
            int(percentage),
            color,
            int(percentage)
        )
    progress_bar.short_description = 'Progress'


@admin.register(PerformanceIndicator)
class PerformanceIndicatorAdmin(admin.ModelAdmin):
    list_display = ['indicator_code', 'indicator_name_short', 'strategic_goal', 'target_value', 'current_value', 'achievement_percentage', 'is_active']
    list_filter = ['indicator_type', 'is_active', 'baseline_year']
    search_fields = ['indicator_code', 'indicator_name', 'description']
    ordering = ['indicator_code']
    
    fieldsets = (
        ('Indicator Information', {
            'fields': ('strategic_goal', 'indicator_code', 'indicator_name', 'description', 'indicator_type')
        }),
        ('Measurement', {
            'fields': ('unit_of_measure', 'baseline_year', 'baseline_value', 'target_value', 'current_value', 'achievement_percentage')
        }),
        ('Data Collection', {
            'fields': ('data_source', 'collection_frequency', 'responsible_person')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    
    readonly_fields = ['achievement_percentage']
    
    def indicator_name_short(self, obj):
        return obj.indicator_name[:60] + '...' if len(obj.indicator_name) > 60 else obj.indicator_name
    indicator_name_short.short_description = 'Indicator'


@admin.register(AnnualPlan)
class AnnualPlanAdmin(admin.ModelAdmin):
    list_display = ['school', 'academic_year', 'title', 'total_budget', 'allocated_budget', 'status']
    list_filter = ['status', 'academic_year', 'school']
    search_fields = ['title', 'description', 'key_priorities']
    ordering = ['-academic_year__start_date', 'school']
    
    fieldsets = (
        ('Plan Information', {
            'fields': ('school', 'academic_year', 'title', 'description')
        }),
        ('Priorities', {
            'fields': ('key_priorities',)
        }),
        ('Budget', {
            'fields': ('total_budget', 'allocated_budget')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Approval', {
            'fields': ('prepared_by', 'approved_by', 'approval_date', 'plan_document')
        }),
    )


@admin.register(AnnualPlanActivity)
class AnnualPlanActivityAdmin(admin.ModelAdmin):
    list_display = ['activity_code', 'activity_name_short', 'annual_plan', 'responsible_person', 'start_date', 'end_date', 'completion_percentage', 'status']
    list_filter = ['status', 'annual_plan__academic_year', 'annual_plan__school']
    search_fields = ['activity_code', 'activity_name', 'description']
    ordering = ['annual_plan', 'activity_code']
    
    fieldsets = (
        ('Activity Information', {
            'fields': ('annual_plan', 'strategic_goal', 'activity_code', 'activity_name', 'description')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date')
        }),
        ('Resources', {
            'fields': ('budget_allocated', 'budget_utilized')
        }),
        ('Responsibility', {
            'fields': ('responsible_person', 'status', 'completion_percentage')
        }),
        ('Deliverables', {
            'fields': ('expected_output', 'actual_output')
        }),
        ('Notes', {
            'fields': ('remarks',),
            'classes': ('collapse',)
        }),
    )
    
    def activity_name_short(self, obj):
        return obj.activity_name[:50] + '...' if len(obj.activity_name) > 50 else obj.activity_name
    activity_name_short.short_description = 'Activity'


@admin.register(ProgressReport)
class ProgressReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'school', 'report_type', 'reporting_period_end', 'overall_progress_percentage', 'status']
    list_filter = ['report_type', 'status', 'academic_year', 'school']
    search_fields = ['title', 'executive_summary']
    ordering = ['-reporting_period_end']
    date_hierarchy = 'reporting_period_end'
    
    fieldsets = (
        ('Report Information', {
            'fields': ('school', 'academic_year', 'annual_plan', 'report_type', 'title')
        }),
        ('Reporting Period', {
            'fields': ('reporting_period_start', 'reporting_period_end')
        }),
        ('Content', {
            'fields': ('executive_summary', 'achievements', 'challenges', 'recommendations')
        }),
        ('Metrics', {
            'fields': ('overall_progress_percentage', 'budget_utilization_percentage')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Workflow', {
            'fields': ('prepared_by', 'reviewed_by', 'published_by', 'published_date', 'report_document')
        }),
    )


@admin.register(DeanApproval)
class DeanApprovalAdmin(admin.ModelAdmin):
    list_display = ['approval_type', 'title', 'department', 'requested_by', 'request_date', 'priority', 'status']
    list_filter = ['approval_type', 'priority', 'status', 'request_date']
    search_fields = ['title', 'description', 'department__name']
    ordering = ['-request_date']
    date_hierarchy = 'request_date'
    
    fieldsets = (
        ('Request Information', {
            'fields': ('department', 'approval_type', 'title', 'description', 'priority')
        }),
        ('Request Details', {
            'fields': ('requested_by', 'request_date', 'supporting_document')
        }),
        ('Approval', {
            'fields': ('status', 'approved_by', 'decision_date', 'decision_notes')
        }),
    )
 
# Customize admin site
admin.site.site_header = "MUT University Management System"
admin.site.site_title = "MUT Admin"
admin.site.index_title = "Welcome to MUT University Management System"