from django.urls import path
from portal import views

urlpatterns = [
    # Authentication
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('dashboard/', views.student_dashboard, name='dashboard'),  # Alias
    path('lecturer/dashboard/', views.lecturer_dashboard, name='lecturer_dashboard'),
    path('dean/dashboard/', views.dean_dashboard, name='dean_dashboard'),
    path('hos/dashboard/', views.hos_dashboard, name='hos_dashboard'),
    path('hod/dashboard/', views.hod_dashboard, name='hod_dashboard'),
    path('finance/dashboard/', views.finance_dashboard, name='finance_dashboard'),
    path('registrar/dashboard/', views.registrar_dashboard, name='registrar_dashboard'),
    path('library/dashboard/', views.library_dashboard, name='library_dashboard'),
    path('hostel/dashboard/', views.hostel_dashboard, name='hostel_dashboard'),
    path('procurement/dashboard/', views.procurement_dashboard, name='procurement_dashboard'),
    
    # Student list and management
    path('students/', views.student_list, name='student_list'),
    path('students/add/', views.add_student, name='add_student'),
    path('students/bulk-update/', views.bulk_update_students, name='bulk_update_students'),
    path('students/export/', views.export_students, name='export_students'),
    
    # Individual student management
    path('students/<path:reg_number>/', views.student_detail, name='student_detail'),
    path('update/students/<path:reg_number>/', views.update_student, name='update_student'),
    path('delete/students/<path:reg_number>/', views.delete_student, name='delete_student'),
    path('performance/students/<path:reg_number>/', views.student_performance, name='student_performance'),
    path('fees/students/<path:reg_number>/', views.student_fees, name='student_fees'),
    path('add-payment/students/<path:reg_number>/', views.add_fee_payment, name='add_fee_payment'),

    # AJAX
    path('students/ajax/<path:reg_number>/', views.get_student_details_ajax, name='get_student_details_ajax'),
    path('students/ajax/fee-structure/', views.get_programme_fee_structure, name='get_programme_fee_structure'),
    
    # Semester Reporting
    path('semester-report/', views.semester_report_view, name='semester_report'),
    path('semester-report/<int:report_id>/status/', views.semester_report_status, name='semester_report_status'),
    path('semester-report/history/', views.semester_report_history, name='semester_report_history'),
    
    # Unit Enrollment
    path('unit-enrollment/', views.unit_enrollment_view, name='unit_enrollment'),
    path('unit-enrollment/status/', views.unit_enrollment_status, name='unit_enrollment_status'),
    
    # Resit Exams
    path('resit-exam/registration/', views.resit_exam_registration, name='resit_exam_registration'),
    path('resit-exam/status/', views.resit_exam_status, name='resit_exam_status'),
    
    # ============= ACADEMIC YEARS =============
    # Academic Year URLs
    path('academic-years/', views.academic_year_list, name='academic_year_list'),
    path('academic-years/add/', views.add_academic_year, name='add_academic_year'),
    path('academic-years/<int:pk>/', views.academic_year_detail, name='academic_year_detail'),
    path('academic-years/<int:pk>/update/', views.update_academic_year, name='update_academic_year'),
    path('academic-years/<int:pk>/delete/', views.delete_academic_year, name='delete_academic_year'),
    path('academic-years/<int:pk>/set-current/', views.set_current_academic_year, name='set_current_academic_year'),
    
    # Semester AJAX URLs
    path('academic-years/<int:academic_year_id>/semesters/', views.get_semesters, name='get_semesters'),
    path('academic-years/<int:academic_year_id>/add-semester/', views.add_semester_ajax, name='add_semester_ajax'),
    path('semesters/<int:semester_id>/update/', views.update_semester_ajax, name='update_semester_ajax'),
    path('semesters/<int:pk>/set-current/', views.set_current_semester, name='set_current_semester'),
    path('semesters/<int:semester_id>/delete/', views.delete_semester_ajax, name='delete_semester_ajax'),
    path('semesters/<int:semester_id>/enrollment-period/',views.save_enrollment_period, name='save_enrollment_period'),
    
    # ============= SEMESTERS =============
    path('semesters/', views.semester_list, name='semester_list'),
    path('semesters/add/', views.add_semester, name='add_semester'),
    path('semesters/<int:pk>/', views.semester_detail, name='semester_detail'),
    path('update/semesters/<int:pk>/', views.update_semester, name='update_semester'),
    path('delete/semesters/<int:pk>/', views.delete_semester, name='delete_semester'),
    path('set-current/semesters/<int:pk>/', views.backup_set_current_semester, name='backup_set_current_semester'),
    
    # ============= INTAKES =============
    path('intakes/', views.intake_list, name='intake_list'),
    path('intakes/add/', views.add_intake, name='add_intake'),
    path('intakes/<int:pk>/', views.intake_detail, name='intake_detail'),
    path('intakes/<int:pk>/update/', views.update_intake, name='update_intake'),
    path('intakes/<int:pk>/delete/', views.delete_intake, name='delete_intake'),
    
    # ============= AJAX/API ENDPOINTS =============
    path('api/semesters-by-year/', views.get_semesters_by_year, name='get_semesters_by_year'),
    path('api/intakes-by-year/', views.get_intakes_by_year, name='get_intakes_by_year'),
    
    # ============= SCHOOLS/FACULTIES =============
    path('schools/', views.school_list, name='school_list'),
    path('schools/add/', views.school_form, name='school_add'),
    path('schools/<int:pk>/', views.school_detail, name='school_detail'),
    path('schools/<int:pk>/update/', views.school_form, name='school_update'),
    path('schools/<int:pk>/delete/', views.school_delete, name='school_delete'),
    
    # ============= DEPARTMENTS =============
    path('departments/', views.department_list, name='department_list'),
    path('departments/add/', views.department_form, name='department_add'),
    path('departments/<int:pk>/', views.department_detail, name='department_detail'),
    path('departments/<int:pk>/update/', views.department_form, name='department_update'),
    path('departments/<int:pk>/delete/', views.department_delete, name='department_delete'),
    
    # ============= PROGRAMMES =============
    path('programmes/', views.programme_list, name='programme_list'),
    path('programmes/add/', views.programme_form, name='programme_add'),
    path('programmes/<int:pk>/', views.programme_detail, name='programme_detail'),
    path('programmes/<int:pk>/update/', views.programme_form, name='programme_update'),
    path('programmes/<int:pk>/delete/', views.programme_delete, name='programme_delete'),
    
    # ============= AJAX HELPERS =============
    path('api/schools/<int:school_id>/departments/', views.get_departments_by_school, name='get_departments_by_school'),
    
    # ============= ALL UNITS =============
    path('units/', views.units_list, name='units_list'),
    path('units/add/', views.unit_form, name='unit_form'),
    path('units/<int:pk>/', views.unit_detail, name='unit_detail'),
    path('units/<int:pk>/update/', views.unit_form, name='unit_update'),
    path('units/<int:pk>/delete/', views.unit_delete, name='unit_delete'),
    
    # ============= PROGRAMME UNITS =============
    path('programme-units/', views.programme_units_list, name='programme_units_list'),
    path('programme-units/<int:programme_id>/', views.programme_units_structure, name='programme_units_structure'),
    
    # ============= PROGRAMME UNITS API =============
    path('api/programme/<int:programme_id>/structure/', views.api_programme_structure, name='api_programme_structure'),
    path('api/units/available/', views.api_available_units, name='api_available_units'),
    path('api/programme-units/add/', views.api_add_programme_unit, name='api_add_programme_unit'),
    path('api/programme-units/<int:programme_unit_id>/update/', views.api_update_programme_unit, name='api_update_programme_unit'),
    path('api/programme-units/<int:programme_unit_id>/delete/', views.api_delete_programme_unit, name='api_delete_programme_unit'),
    path('api/programme-units/copy/', views.api_copy_programme_units, name='api_copy_programme_units'),
    
    # Lecturer Management URLs
    path('lecturers/', views.lecturer_list, name='lecturer_list'),
    path('lecturers/add/', views.lecturer_form, name='add_lecturer'),
    path('lecturers/<str:employee_number>/', views.lecturer_detail, name='lecturer_detail'),
    path('lecturers/<str:employee_number>/edit/', views.lecturer_form, name='update_lecturer'),
    path('lecturers/<str:employee_number>/delete/', views.lecturer_delete, name='delete_lecturer'),
    path('lecturers/<str:employee_number>/workload/', views.lecturer_workload, name='lecturer_workload'),
    path('lecturers/bulk/update/', views.lecturer_bulk_update, name='bulk_update_lecturers'),
    path('lecturers/export/csv/', views.export_lecturers, name='export_lecturers'),
    
    # Lecturer Units Management
    path('lecturer/units/', views.lecturer_units, name='lecturer_units'),
    path('lecturer/units/<int:allocation_id>/students/', views.unit_students, name='unit_students'),
    path('lecturer/save-marks/', views.save_student_marks, name='save_student_marks'),
    path('lecturer/units/<int:allocation_id>/exam-list/', views.download_exam_list, name='download_exam_list'),
    path('lecturer/units/<int:allocation_id>/export-marks/', views.download_marks_csv, name='download_marks_csv'),
    
    # Teaching Materials Management
    path('teaching-materials/', views.lecturer_teaching_materials, name='lecturer_teaching_materials'),
    path('lecturer/materials/upload/<int:allocation_id>/', views.upload_teaching_material, name='upload_teaching_material'),
    path('lecturer/materials/update/<int:material_id>/', views.update_teaching_material, name='update_teaching_material'),
    path('lecturer/materials/delete/<int:material_id>/', views.delete_teaching_material, name='delete_teaching_material'),
    path('lecturer/materials/toggle-publish/<int:material_id>/', views.toggle_material_publish, name='toggle_material_publish'),
    path('lecturer/materials/stats/<int:allocation_id>/', views.get_material_stats, name='get_material_stats'),
    
    
    # Teaching Materials Access
    path('teaching-materials/', views.student_teaching_materials, name='student_teaching_materials'),
    path('materials/download/<int:material_id>/', views.download_material, name='download_material'),
    path('materials/view/<int:material_id>/', views.view_material, name='view_material'),
    path('materials/comment/<int:material_id>/', views.add_material_comment, name='add_material_comment'),
    path('materials/unit/<int:enrollment_id>/', views.unit_materials_view, name='unit_materials_view'),
    
    # Profile Management
    path('students-profile/', views.student_profile_view, name='student_profile_view'),
    path('profile/update/', views.student_profile_update, name='student_profile_update'), 
    path('profile/change-password/', views.student_change_password, name='student_change_password'),
    path('profile/delete-picture/', views.student_delete_profile_picture, name='student_delete_profile_picture'),
    
    # Hostel URLs
    # Hostel Application
    path('hostel/application/', views.hostel_application, name='hostel_application'), 
    path('hostel/<int:hostel_id>/', views.hostel_detail, name='hostel_detail'),
    path('hostel/room/<int:room_id>/', views.room_detail, name='room_detail'),
    path('hostel/bed/<int:bed_id>/reserve/', views.reserve_bed, name='reserve_bed'),
    path('hostel/payment/status/<uuid:reservation_id>/', views.check_payment_status, name='check_payment_status'),
    path('hostel/my-allocation/', views.my_hostel_allocation, name='my_hostel_allocation'),
    
    # M-Pesa Callback
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
    path('api/hostels/', views.api_hostels_list, name='api_hostels_list'),
    path('api/hostels/<int:hostel_id>/', views.api_hostel_detail, name='api_hostel_detail'),
    path('api/hostels/<int:hostel_id>/rooms/', views.api_hostel_rooms, name='api_hostel_rooms'),
    path('api/hostels/<int:hostel_id>/reviews/', views.api_hostel_reviews, name='api_hostel_reviews'),
    
    # Rooms & Beds
    path('api/rooms/<int:room_id>/beds/', views.api_room_beds, name='api_room_beds'),
    
    # Booking
    path('api/beds/reserve/', views.api_reserve_bed, name='api_reserve_bed'),
    path('api/payment/status/', views.api_check_payment_status, name='api_check_payment_status'),
    path('api/my-application/', views.api_my_application, name='api_my_application'),
    path('api/my-allocation/', views.api_my_allocation, name='api_my_allocation'),
    
    
    # Dashboard
    path('allocations/dashboard/', views.unit_allocation_dashboard, name='unit_allocation_dashboard'),
    path('allocations/', views.unit_allocation_list, name='unit_allocation_list'),
    path('allocations/create/', views.create_unit_allocation, name='create_unit_allocation'),
    path('allocations/search-units/', views.search_units_ajax, name='search_units_ajax'),
    path('allocations/search-lecturers/', views.search_lecturers_ajax, name='search_lecturers_ajax'),
    path('allocations/<int:allocation_id>/', views.unit_allocation_detail, name='unit_allocation_detail'),
    path('allocations/<int:allocation_id>/edit/', views.edit_unit_allocation, name='edit_unit_allocation'),
    path('allocations/<int:allocation_id>/delete/', views.delete_unit_allocation, name='delete_unit_allocation'),
    
    # Approval Actions
    path('allocations/<int:allocation_id>/approve/', views.approve_allocation, name='approve_allocation'),
    path('allocations/<int:allocation_id>/reject/', views.reject_allocation, name='reject_allocation'),
    
    # AJAX Endpoints
    path('allocations/ajax/lecturers/', views.get_lecturers_ajax, name='get_lecturers_ajax'),
    
    # Student Transcript URLs
    path('student/transcript/', views.student_transcript_view, name='student_transcript'),
    path('student/transcript/download/full/', views.download_full_transcript, name='download_full_transcript'),
    path('student/transcript/download/year/<int:academic_year_id>/', views.download_yearly_transcript, name='download_yearly_transcript'),
    path('student/transcript/download/semester/<int:semester_id>/', views.download_semester_transcript, name='download_semester_transcript'),

    path('admin-marks/entry/', views.admin_marks_entry, name='admin_marks_entry'),
    path('admin-marks/search-student/', views.admin_search_student, name='admin_search_student'),
    path('admin-marks/get-enrollments/', views.admin_get_student_enrollments, name='admin_get_student_enrollments'),
    path('admin-marks/save/', views.admin_save_student_marks, name='admin_save_student_marks'),
    
    path('enrollment-periods/', views.enrollment_period_list, name='enrollment_period_list'),
    path('enrollment-periods/create/', views.enrollment_period_create, name='enrollment_period_create'),
    path('enrollment-periods/<int:period_id>/', views.enrollment_period_detail, name='enrollment_period_detail'),
    path('enrollment-periods/<int:period_id>/update/', views.enrollment_period_update, name='enrollment_period_update'),
    path('enrollment-periods/<int:period_id>/delete/', views.enrollment_period_delete, name='enrollment_period_delete'),
    
    # Main fee structure management
    path('fee-structures/', views.fee_structure_list, name='fee_structure_list'),
    path('fee-structures/add/', views.add_fee_structure, name='add_fee_structure'),
    path('fee-structures/<int:structure_id>/', views.view_fee_structure, name='view_fee_structure'),
    path('fee-structures/<int:structure_id>/update/', views.update_fee_structure, name='update_fee_structure'),
    path('fee-structures/<int:structure_id>/delete/', views.delete_fee_structure, name='delete_fee_structure'),
    path('fee-structures/<int:structure_id>/duplicate/', views.duplicate_fee_structure, name='duplicate_fee_structure'),
    path('fee-structures/bulk-create/', views.bulk_create_fee_structures, name='bulk_create_fee_structures'),
    
    # AJAX API endpoints
    path('api/fee-structures/<int:structure_id>/', views.get_fee_structure_details, name='get_fee_structure_details'),
    path('api/programmes/<int:programme_id>/fee-structures/', views.get_programme_fee_structures, name='get_programme_fee_structures'),
    
    # Fee Payment Management URLs
    path('admin-fee-payments/', views.fee_payment_list, name='fee_payment_list'),
    path('admin-fee-payments/add/', views.admin_add_fee_payment, name='add_fee_payment'),
    path('admin-fee-payments/<int:payment_id>/', views.fee_payment_detail, name='fee_payment_detail'),
    path('admin-fee-payments/<int:payment_id>/update/', views.update_fee_payment, name='update_fee_payment'),
    path('admin-fee-payments/<int:payment_id>/delete/', views.delete_fee_payment, name='delete_fee_payment'),
    path('admin-fee-payments/export/', views.export_fee_payments, name='export_fee_payments'),
    
    # API endpoint for student payment history
    path('api/student-payment-history/<str:registration_number>/', views.student_payment_history, name='student_payment_history'),
    
    # ============= HOSTEL MANAGEMENT URLS =============
    
    # Hostel List & CRUD
    path('admin-hostels/', views.admin_hostel_list, name='admin_hostel_list'),
    path('admin-hostels/add/', views.admin_add_hostel, name='admin_add_hostel'),
    path('admin-hostels/<str:hostel_code>/', views.admin_hostel_detail, name='admin_hostel_detail'),
    path('admin-hostels/<str:hostel_code>/update/', views.admin_update_hostel, name='admin_update_hostel'),
    path('admin-hostels/<str:hostel_code>/delete/', views.admin_delete_hostel, name='admin_delete_hostel'),
    
    # Room Detail
    path('admin-rooms/<int:room_id>/', views.admin_hostel_room_detail, name='admin_hostel_room_detail'),
    
    # Bed Detail
    path('admin-beds/<int:bed_id>/', views.admin_hostel_bed_detail, name='admin_hostel_bed_detail'),
    
    # ============= API ENDPOINTS =============
    
    # Bulk Creation APIs
    path('api/hostels/bulk-create/', views.api_bulk_create_hostels, name='api_bulk_create_hostels'),
    path('api/hostels/<str:hostel_code>/rooms/bulk-create/', views.api_bulk_create_rooms, name='api_bulk_create_rooms'),
    path('api/rooms/<int:room_id>/beds/bulk-create/', views.api_bulk_create_beds, name='api_bulk_create_beds'),
    
    # Statistics APIs
    path('api/hostels/<str:hostel_code>/stats/', views.api_hostel_stats, name='api_hostel_stats'),
    path('api/beds/available/', views.api_available_beds, name='api_available_beds'),
    
    # Application Management
    path('admin-hostel/applications/', views.admin_hostel_application_list, name='admin_hostel_application_list'),
    path('admin-hostel/applications/<int:pk>/', views.admin_hostel_application_detail, name='admin_hostel_application_detail'),
    path('admin-hostel/applications/<int:pk>/approve/', views.admin_approve_application, name='admin_approve_application'),
    path('admin-hostel/applications/<int:pk>/reject/', views.admin_reject_application, name='admin_reject_application'),
    
     # Book Management
    path('admin-library/books/', views.admin_library_book_list, name='admin_library_book_list'),
    path('admin-library/books/<int:pk>/', views.admin_library_book_detail, name='admin_library_book_detail'),
    path('admin-library/books/<int:book_id>/issue/', views.admin_library_issue_book, name='admin_library_issue_book'),
    # Borrowing Management
    path('admin-library/borrowings/', views.admin_library_borrowings, name='admin_library_borrowings'),
    path('admin-library/borrowings/<int:borrowing_id>/return/', views.admin_library_return_book, name='admin_library_return_book'),
    
    # Overdue Management
    path('admin-library/overdue/', views.admin_library_overdue_books, name='admin_library_overdue_books'),
    path('admin-library/borrowings/<int:borrowing_id>/reminder/', views.admin_library_send_reminder, name='admin_library_send_reminder'),
    path('admin-library/overdue/send-all-reminders/', views.admin_library_send_all_reminders,  name='admin_library_send_all_reminders'),
    
    # ============= API ENDPOINTS =============
    path('api/library/borrowing/<int:borrowing_id>/calculate-fine/', views.api_calculate_fine, name='api_calculate_fine'),
    path('api/library/search-students/', views.api_search_students, name='api_search_students'),
    
     # Master Timetable Management
    path('admin-timetable/master/', views.admin_timetable_master, name='admin_timetable_master'),
    
    # API Endpoints
    path('api/timetable/get-units/', views.api_get_programme_units, name='api_get_programme_units'),
    path('api/timetable/get-lecturers/', views.api_get_lecturers, name='api_get_lecturers'),
    path('api/timetable/save-slot/', views.api_save_timetable_slot, name='api_save_timetable_slot'),
    path('api/timetable/delete-slot/', views.api_delete_timetable_slot, name='api_delete_timetable_slot'),
    path('api/timetable/get-slots/', views.api_get_timetable_slots, name='api_get_timetable_slots'),
    path('api/timetable/publish/', views.api_publish_timetable, name='api_publish_timetable'),
    
    # Student Timetable
    path('student/timetable/', views.student_timetable, name='student_timetable'),
    
    # Student ID Management
    path('student-id/', views.student_id_dashboard, name='student_id_dashboard'),
    path('student-id/apply/', views.apply_for_student_id, name='apply_for_student_id'),
    path('student-id/upload-photo/<int:application_id>/', views.upload_id_photo, name='upload_id_photo'),
    path('student-id/application/<int:application_id>/', views.view_id_application, name='view_id_application'),
    path('student-id/payment/<int:application_id>/', views.initiate_id_payment, name='initiate_id_payment'),
    path('student-id/my-cards/', views.my_student_ids, name='my_student_ids'),
    path('student-id/download/<int:card_id>/', views.download_digital_id, name='download_digital_id'),
    path('student-id/notifications/', views.id_notifications, name='id_notifications'),
    path('student-id/check-payment/<int:application_id>/', views.check_payment_status, name='check_payment_status'),
    
    # Public endpoint for ID verification
    path('verify-id-card/<str:card_number>/', views.verify_student_id, name='verify_student_id'),
    
    # M-Pesa Callback (CSRF exempt)
    path('id-payment-callback/', views.student_id_payment_callback, name='student_id_payment_callback'),
    
    # Admin URLs
    path('admin/student-id/applications/', views.admin_id_applications, name='admin_id_applications'),
    path('admin/student-id/application/<int:application_id>/', views.admin_view_application, name='admin_view_id_application'),
    path('admin/student-id/application/<int:application_id>/update-status/', views.update_application_status, name='update_id_status'),
    path('admin/student-id/issue-card/<int:application_id>/', views.issue_student_id, name='issue_student_id'),
    path('admin/student-id/reports/', views.id_card_reports, name='id_card_reports'),
    
    # AI Chat endpoints
    path('api/chat/send/', views.chat_send_message, name='chat_send_message'),
    path('api/chat/mark-alerts-read/', views.mark_alerts_read, name='mark_alerts_read'),
    path('api/chat/check-alerts/', views.check_new_alerts, name='check_alerts'),
    path('api/chat/rate-message/', views.rate_message, name='rate_message'),
    path('api/chat/end-session/', views.end_session, name='end_session'),
    
    # Help & Support URLs
    path('help/faqs/', views.help_faqs, name='help_faqs'),
    path('help/faq/<int:faq_id>/', views.faq_detail, name='faq_detail'),
    path('help/faq/<int:faq_id>/feedback/', views.faq_feedback, name='faq_feedback'),
    
    path('help/contact-support/', views.contact_support, name='contact_support'),
    
    path('help/system-guides/', views.system_guides, name='system_guides'),
    path('help/guide/<int:guide_id>/', views.guide_detail, name='guide_detail'),
    
    path('help/report-issue/', views.report_issue, name='report_issue'),
    path('help/my-tickets/', views.my_tickets, name='my_tickets'),
    path('help/ticket/<str:ticket_number>/', views.ticket_detail, name='ticket_detail'),
    path('help/ticket/<str:ticket_number>/close/', views.close_ticket, name='close_ticket'),
    
]