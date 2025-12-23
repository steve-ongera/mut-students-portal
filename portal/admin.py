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

# Customize admin site
admin.site.site_header = "MUT University Management System"
admin.site.site_title = "MUT Admin"
admin.site.index_title = "Welcome to MUT University Management System"