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
    
    
# Customize admin site
admin.site.site_header = "MUT University Management System"
admin.site.site_title = "MUT Admin"
admin.site.index_title = "Welcome to MUT University Management System"