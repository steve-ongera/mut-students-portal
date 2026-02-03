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
    path('library/dashboard/', views.librarian_dashboard, name='librarian_dashboard'),
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
    
    #Student Finance URLs
    path('finance/fee-statement/', views.student_fee_statement, name='student_fee_statement'),
    path('finance/make-payment/', views.student_make_payment, name='student_make_payment'),
    path('finance/payment-history/', views.student_payment_history, name='student_payment_history'),
    path('finance/receipt/<int:payment_id>/', views.student_payment_receipt, name='student_payment_receipt'),
    path('finance/receipts/', views.student_all_receipts, name='student_all_receipts'),
    path('finance/fee-structure/', views.student_fee_structure, name='student_fee_structure'),
    
    # AJAX endpoints
    path('api/verify-payment/', views.verify_payment, name='verify_payment'),
    
    # Students Library URLs
    path('library/search/', views.library_search_books, name='library_search_books'),
    path('library/reserve/<int:book_id>/', views.reserve_book, name='reserve_book'),
    path('library/borrowings/', views.my_borrowings, name='my_borrowings'),
    path('library/reservations/', views.book_reservations, name='library_reservations'),
    path('library/reservations/cancel/<int:borrowing_id>/', views.cancel_reservation, name='cancel_reservation'),
    path('library/fines/', views.library_fines, name='library_fines'),
    path('library/digital-resources/', views.digital_resources, name='digital_resources'),
    
    # AJAX endpoints
    path('api/book/<int:book_id>/availability/', views.check_book_availability, name='check_book_availability'),
    
    # School Overview
    path('school-profile/', views.school_profile, name='school_profile'),
    path('dean/departments/', views.departments_list, name='departments_list'),
    path('dean/departments/<int:department_id>/', views.dean_department_detail, name='dean_department_detail'),
    path('academic-staff/', views.academic_staff, name='academic_staff'),
    path('academic-staff/<int:lecturer_id>/', views.staff_detail, name='staff_detail'),
    path('student-population/', views.student_population, name='student_population'),
    path('school-calendar/', views.school_calendar, name='school_calendar'),
    
    # Academic Management
    path('programme-development/', views.programme_development, name='programme_development'),
    path('programme-development/<int:programme_id>/', views.programme_detail, name='programme_detail'),
    path('curriculum-review/', views.curriculum_review, name='curriculum_review'),
    path('curriculum-review/unit/<int:unit_id>/', views.unit_detail, name='unit_detail'),
    path('academic-standards/', views.academic_standards, name='academic_standards'),
    path('accreditation/', views.accreditation, name='accreditation'),
    path('external-examiners/', views.external_examiners, name='external_examiners'),
    
    
    # ============================================================================
    # QUALITY ASSURANCE URLS
    # ============================================================================
    path('quality-assurance/teaching-evaluations/', views.dean_teaching_evaluations_view, name='teaching_evaluations'),
    path('quality-assurance/programme-reviews/', views.dean_programme_reviews_view, name='programme_reviews'),
    path('quality-assurance/audit-reports/', views.dean_audit_reports_view, name='audit_reports'),
    path('quality-assurance/compliance-monitoring/', views.dean_compliance_monitoring_view, name='compliance_monitoring'),
    path('quality-assurance/quality-metrics/', views.dean_quality_metrics_view, name='quality_metrics'),

    # ============================================================================
    # RESEARCH & INNOVATION URLS
    # ============================================================================
    path('research/strategy/', views.dean_research_strategy_view,  name='research_strategy'),
    path('research/grant-management/',  views.dean_grant_management_view, name='grant_management'),
    path('research/publications/', views.dean_publications_view,  name='publications'),
    path('research/research-centers/', views.dean_research_centers_view, name='research_centers'), 
    path('research/innovation-projects/', views.dean_innovation_projects_view, name='innovation_projects'),

    # ============================================================================
    # HUMAN RESOURCES URLS
    # ============================================================================
    path('hr/staff-recruitment/', views.dean_staff_recruitment_view, name='staff_recruitment'),
    path('hr/performance-appraisal/', views.dean_performance_appraisal_view, name='performance_appraisal'),
    path('hr/promotions/', views.dean_promotions_view,  name='promotions'),
    path('hr/staff-development/',  views.dean_staff_development_view, name='staff_development'),
    path('hr/disciplinary-matters/',  views.dean_disciplinary_matters_view,  name='disciplinary_matters'),

    # ============================================================================
    # FINANCIAL MANAGEMENT URLS
    # ============================================================================
    path('finance/school-budget/', views.dean_school_budget_view, name='school_budget'),
    path('finance/resource-allocation/', views.dean_resource_allocation_view, name='resource_allocation'),
    path('finance/expenditure-control/', views.dean_expenditure_control_view, name='expenditure_control'),
    path('finance/revenue-generation/', views.dean_revenue_generation_view, name='revenue_generation'),
    path('finance/financial-reports/', views.dean_financial_reports_view,  name='financial_reports'),

    # ============================================================================
    # PARTNERSHIPS & LINKAGES URLS
    # ============================================================================
    path('partnerships/industry-linkages/', views.dean_industry_linkages_view, name='industry_linkages'),
    path('partnerships/international-partners/', views.dean_international_partners_view, name='international_partners'),
    path('partnerships/mous/', views.dean_mous_view, name='mous'),
    path('partnerships/collaborative-projects/', views.dean_collaborative_projects_view, name='collaborative_projects'),
    path('partnerships/alumni-relations/', views.dean_alumni_relations_view, name='alumni_relations'),

    # ============================================================================
    # STRATEGIC PLANNING URLS
    # ============================================================================
    path('strategic/strategic-goals/', views.dean_strategic_goals_view, name='strategic_goals'),
    path('strategic/performance-indicators/', views.dean_performance_indicators_view,  name='performance_indicators'),
    path('strategic/annual-plans/',  views.dean_annual_plans_view, name='annual_plans'),
    path('strategic/progress-reports/',  views.dean_progress_reports_view, name='progress_reports'),
    path('strategic/future-planning/', views.dean_future_planning_view, name='future_planning'),

    # ============================================================================
    # APPROVALS & AUTHORIZATIONS URLS
    # ============================================================================
    path('approvals/', views.dean_approvals_view, name='approvals'),
    path('approvals/department-budgets/', views.dean_department_budgets_approval_view, name='department_budgets_approval'),
    path('approvals/staff-appointments/', views.dean_staff_appointments_approval_view, name='staff_appointments_approval'),
    path('approvals/research-grants/', views.dean_research_grants_approval_view, name='research_grants_approval'),
    
    
    # Assessment Management URLs
    path('lecturer/assessments/', views.lecturer_assessments, name='lecturer_assessments'),
    path('lecturer/assessments/create/', views.create_assessment, name='create_assessment'),
    path('lecturer/assessments/<int:assessment_id>/edit/', views.edit_assessment, name='edit_assessment'),
    path('lecturer/assessments/<int:assessment_id>/detail/', views.assessment_detail, name='assessment_detail'),
    path('lecturer/assessments/<int:assessment_id>/delete/', views.delete_assessment, name='delete_assessment'),
    path('lecturer/assessments/<int:assessment_id>/extend/', views.extend_assessment, name='extend_assessment'),
    path('lecturer/assessments/<int:assessment_id>/participants/', views.assessment_participants, name='assessment_participants'),
    
    
    # Grading URLs
    path('lecturer/grading/', views.grading_dashboard, name='grading_dashboard'),
    path('lecturer/grading/<int:assessment_id>/', views.grade_students, name='grade_students'),
    path('lecturer/grading/<int:assessment_id>/bulk-upload/', views.bulk_upload_marks, name='bulk_upload_marks'),
    path('lecturer/grading/<int:assessment_id>/download-template/', views.download_grading_template, name='download_grading_template'),
    
    # Final Exams URLs
    path('lecturer/final-exams/', views.final_exams, name='final_exams'),
    path('lecturer/final-exams/create/', views.create_final_exam, name='create_final_exam'),
    path('lecturer/final-exams/<int:exam_id>/grade/', views.grade_final_exam, name='grade_final_exam'),
    
    # Moderation URLs
    path('lecturer/moderation/', views.moderation_dashboard, name='moderation_dashboard'),
    path('lecturer/moderation/<int:assessment_id>/request/', views.request_moderation, name='request_moderation'),
    path('lecturer/moderation/<int:assessment_id>/view/', views.view_moderation, name='view_moderation'),
    
    # Result Submission URLs
    path('lecturer/results/', views.results_dashboard, name='results_dashboard'),
    path('lecturer/results/<int:unit_allocation_id>/submit/', views.submit_results, name='submit_results'),
    path('lecturer/results/<int:unit_allocation_id>/preview/', views.preview_results, name='preview_results'),
    path('lecturer/results/<int:unit_allocation_id>/history/', views.submission_history, name='submission_history'),

    # Students Management URLs
    path('lecturer/students/', views.students_dashboard, name='students_dashboard'),
    path('lecturer/students/class-lists/', views.class_lists, name='class_lists'),
    path('lecturer/students/class/<int:unit_allocation_id>/', views.class_detail, name='class_detail'),
    path('lecturer/students/class/<int:unit_allocation_id>/export/', views.export_class_list, name='export_class_list'),
    
    # Student Performance URLs
    path('lecturer/students/performance/', views.student_performance_overview, name='student_performance_overview'),
    path('lecturer/students/performance/<str:registration_number>/', views.student_performance_detail, name='student_performance_detail'),
    path('lecturer/students/performance/<str:registration_number>/unit/<int:unit_id>/', views.student_unit_performance, name='student_unit_performance'),
    
    # Academic Advising URLs
    path('lecturer/students/advising/', views.academic_advising, name='academic_advising'),
    path('lecturer/students/advising/<str:registration_number>/', views.student_advising_detail, name='student_advising_detail'),
    path('lecturer/students/advising/<str:registration_number>/add-note/', views.add_advising_note, name='add_advising_note'),
    path('lecturer/students/advising/notes/<int:note_id>/edit/', views.edit_advising_note, name='edit_advising_note'),
    
    # Special Needs URLs
    path('lecturer/students/special-needs/', views.special_needs, name='special_needs'),
    path('lecturer/students/special-needs/<str:registration_number>/', views.special_needs_detail, name='special_needs_detail'),
    path('lecturer/students/special-needs/<str:registration_number>/update/', views.update_special_needs, name='update_special_needs'),
    
    # ============= RESEARCH URLS =============
    path('research/projects/', 
         views.research_projects_list, 
         name='lecturer_research_projects'),
    
    path('research/projects/<int:project_id>/', 
         views.research_project_detail, 
         name='lecturer_research_project_detail'),
    
    path('research/publications/', 
         views.publications_list, 
         name='lecturer_publications'),
    
    path('research/publications/<int:publication_id>/', 
         views.publication_detail, 
         name='lecturer_publication_detail'),
    
    path('research/grants/', 
         views.research_grants_list, 
         name='lecturer_research_grants'),
    
    # ============= DEPARTMENT URLS =============
    path('department/unit-allocations/', 
         views.unit_allocations_list, 
         name='lecturer_unit_allocations'),
    
    path('department/unit-allocations/<int:allocation_id>/', 
         views.unit_allocation_detail, 
         name='lecturer_unit_allocation_detail'),
    
    path('department/staff-development/', 
         views.staff_development_list, 
         name='lecturer_staff_development'),
    
    # ============= REPORTS URLS =============
    path('reports/teaching-load/', 
         views.teaching_load_report, 
         name='lecturer_teaching_load_report'),
    
    path('reports/student-results/', 
         views.student_results_report, 
         name='lecturer_student_results_report'),
    
    path('reports/research-output/', 
         views.research_output_report, 
         name='lecturer_research_output_report'),
    
    path('reports/annual/', 
         views.annual_report, 
         name='lecturer_annual_report'),
    
    # Main semester reporting management page
    path('admin-semester-reporting/', 
         views.semester_reporting_management, 
         name='semester_reporting_management'),
    
    # API endpoints for semester reports
    path('api/semester-reports/bulk-approve/', 
         views.bulk_approve_reports, 
         name='bulk_approve_reports'),
    
    path('api/semester-reports/bulk-reject/', views.bulk_reject_reports, name='bulk_reject_reports'),
    path('api/semester-reports/programme-approve/', views.approve_programme_reports, name='approve_programme_reports'),
    
    path('api/semester-reports/<int:report_id>/details/', views.get_report_details, name='get_report_details'),
    path('api/semester-reports/<int:report_id>/approve/', views.individual_approve_report, name='individual_approve_report'),
    path('api/semester-reports/<int:report_id>/reject/', views.individual_reject_report, name='individual_reject_report'),
    
    
    # Main unit enrollment management page
    path('admin-unit-enrollments/', views.unit_enrollment_management, name='unit_enrollment_management'),
    
    # API endpoints for unit enrollments
    path('api/unit-enrollments/bulk-approve/', views.bulk_approve_enrollments, name='bulk_approve_enrollments'),
    path('api/unit-enrollments/bulk-reject/', views.bulk_reject_enrollments, name='bulk_reject_enrollments'),
    path('api/unit-enrollments/programme-approve/', views.approve_programme_enrollments, name='approve_programme_enrollments'),
    path('api/unit-enrollments/<int:enrollment_id>/details/', views.get_enrollment_details,  name='get_enrollment_details'),
    path('api/unit-enrollments/<int:enrollment_id>/approve/', views.individual_approve_enrollment, name='individual_approve_enrollment'),
    path('api/unit-enrollments/<int:enrollment_id>/reject/', views.individual_reject_enrollment, name='individual_reject_enrollment'),
    path('api/unit-enrollments/statistics/', views.get_enrollment_statistics, name='get_enrollment_statistics'),

    # ============= CATALOG MANAGEMENT =============
    path('catalog/', views.book_catalog_list, name='book_catalog_list'),
    path('catalog/add/', views.add_book, name='add_book'),
    path('catalog/detail/<int:book_id>/', views.book_detail, name='book_detail'),
    path('catalog/edit/<int:book_id>/', views.edit_book, name='edit_book'),
    path('catalog/delete/<int:book_id>/', views.delete_book, name='delete_book'),
    path('catalog/categories/', views.manage_categories, name='manage_categories'),
    path('catalog/inventory/', views.inventory_management, name='inventory_management'),
    path('catalog/inventory/update/<int:book_id>/', views.update_stock, name='update_stock'),
    
    # ============= CIRCULATION =============
    path('circulation/issue/', views.book_issuance, name='book_issuance'),
    path('circulation/returns/', views.book_returns, name='book_returns'),
    path('circulation/renew/<int:borrowing_id>/', views.renew_borrowing, name='renew_borrowing'),
    path('circulation/overdue/', views.overdue_management, name='overdue_management'),
    
    # AJAX endpoints for circulation
    path('api/search-student/', views.search_student_for_borrowing, name='search_student_for_borrowing'),
    path('api/search-book/', views.search_book_for_borrowing, name='search_book_for_borrowing'),
    
    # ============= FINES & PAYMENTS =============
    path('fines/', views.fine_management, name='fine_management'),
    path('fines/payment/<int:borrowing_id>/', views.process_fine_payment, name='process_fine_payment'),
    path('fines/waive/<int:borrowing_id>/', views.waive_fine, name='waive_fine'),
    
    # ============= REPORTS =============
    path('reports/', views.library_reports, name='library_reports'),
    path('reports/usage/', views.usage_statistics, name='usage_statistics'),
    path('reports/collection/', views.collection_analysis, name='collection_analysis'),
    path('reports/circulation/', views.circulation_report, name='circulation_report'),
    
    # ============= FEE MANAGEMENT =============
    path('finance-module/fee-structure/', views.finance_fee_structure_list, name='finance_fee_structure_list'),
     # API Endpoints
    path('api/fee-structure/programme/<int:programme_id>/', views.get_programme_fee_structure, name='api_programme_fee_structure'),
    path('api/fee-structure/create/', views.create_fee_structure, name='api_create_fee_structure'),
    path('api/fee-structure/<int:fee_structure_id>/update/', views.update_fee_structure, name='api_update_fee_structure'),
    path('api/fee-structure/<int:fee_structure_id>/delete/', views.delete_fee_structure, name='api_delete_fee_structure'),
    path('api/fee-structure/duplicate/', views.duplicate_fee_structure, name='api_duplicate_fee_structure'),
    path('api/programme/<int:programme_id>/years/', views.get_programme_years, name='api_programme_years'),
    path('finance/fee-structure/create/', views.fee_structure_create, name='fee_structure_create'),
    
    path('finance/student-balances/', views.student_balances, name='student_balances'),
    path('finance/student-balances/<int:student_id>/', views.student_balance_detail, name='student_balance_detail'),
    
    # ============= PAYMENT PROCESSING =============
    path('finance/payment/process/', views.payment_processing, name='payment_processing'),
    path('finance/payment/receipt/<int:payment_id>/', views.payment_receipt, name='payment_receipt'),
    path('finance/payments/', views.payment_list, name='payment_list'),
    
    # ============= FINANCIAL REPORTING =============
    path('finance/reports/daily-collections/', views.daily_collections_report, name='daily_collections_report'),
    path('finance/reports/monthly-collections/', views.monthly_collections_report, name='monthly_collections_report'),
    path('finance/reports/revenue-analysis/', views.revenue_analysis, name='revenue_analysis'),
    path('finance/reports/debtors/', views.debtors_report, name='debtors_report'),
    
    # ============= BUDGET MANAGEMENT =============
    path('finance/budget/', views.budget_list, name='budget_list'),
    path('finance/budget/<int:budget_id>/', views.budget_detail, name='budget_detail'),
    path('finance/expenditure/', views.expenditure_tracking, name='expenditure_tracking'),
    
    # ============= AJAX/API ENDPOINTS =============
    path('finance/api/student-balance/<int:student_id>/', views.get_student_balance, name='get_student_balance'),
    path('finance/api/search-students/', views.search_students, name='search_students'),
    
    # ============= EXPORTS =============
    path('finance/export/debtors-csv/', views.export_debtors_csv, name='export_debtors_csv'),
    
    # ============= HOSTEL MANAGEMENT =============
    path('hostel/profile/', views.hostel_profile, name='hostel_profile'),
    path('hostel/profile/<int:hostel_id>/', views.hostel_profile, name='hostel_profile'),
    path('rooms/', views.room_management, name='room_management'),
    path('rooms/add/', views.add_room, name='add_room'),
    path('beds/allocation/', views.bed_allocation_management, name='bed_allocation'),
    path('capacity/planning/', views.capacity_planning, name='capacity_planning'),
    path('hostel/rules/', views.hostel_rules, name='hostel_rules'),
    
    # ============= APPLICATIONS =============
    path('applications/new/', views.new_applications, name='new_applications'),
    path('applications/review/<int:application_id>/', views.application_review, name='application_review'),
    path('applications/approved/', views.approved_applications, name='approved_applications'),
    path('applications/rejected/', views.rejected_applications, name='rejected_applications'),
    path('applications/waiting-list/', views.waiting_list, name='waiting_list'),
    
    # ============= OCCUPANCY MANAGEMENT =============
    path('occupancy/current/', views.current_occupants, name='current_occupants'),
    path('occupancy/vacant/', views.vacant_rooms, name='vacant_rooms'),
    path('occupancy/rate/', views.occupancy_rate, name='occupancy_rate'),
    path('occupancy/check-in-out/', views.check_in_check_out, name='check_in_check_out'),
    path('occupancy/transfers/', views.room_transfers, name='room_transfers'),
    
    # ============= MAINTENANCE =============
    path('maintenance/requests/', views.maintenance_requests, name='maintenance_requests'),
    path('maintenance/request/<int:request_id>/', views.maintenance_request_detail, name='maintenance_request_detail'),
    path('maintenance/work-orders/', views.work_orders, name='work_orders'),
    path('maintenance/preventive/', views.preventive_maintenance, name='preventive_maintenance'),
    path('maintenance/schedule/', views.maintenance_schedule, name='maintenance_schedule'),
    path('maintenance/facility-inspection/', views.facility_inspection, name='facility_inspection'),
    
    # ============= HOSTEL FEES =============
    path('fees/structure/', views.fee_structure, name='fee_structure'),
    path('fees/collection/', views.fee_collection, name='fee_collection'),
    path('fees/outstanding/', views.outstanding_fees, name='outstanding_fees'),
    path('fees/receipts/', views.receipts, name='receipts'),
    path('fees/refunds/', views.refunds, name='refunds'),
    
    # ============= SECURITY & SAFETY =============
    path('security/personnel/', views.security_personnel, name='security_personnel'),
    path('security/visitors/', views.visitor_management, name='visitor_management'),
    path('security/emergency-procedures/', views.emergency_procedures, name='emergency_procedures'),
    path('security/incidents/', views.incident_reports, name='incident_reports'),
    path('security/safety-inspections/', views.safety_inspections, name='safety_inspections'),
    
    # ============= STUDENT WELFARE =============
    path('welfare/issues/', views.welfare_issues, name='welfare_issues'),
    path('welfare/counseling/', views.counseling_services, name='counseling_services'),
    path('welfare/health/', views.health_services, name='health_services'),
    path('welfare/recreation/', views.recreational_activities, name='recreational_activities'),
    path('welfare/complaints/', views.student_complaints, name='student_complaints'),
    
    # ============= DISCIPLINARY MATTERS =============
    path('disciplinary/violations/', views.rule_violations, name='rule_violations'),
    path('disciplinary/cases/', views.disciplinary_cases, name='disciplinary_cases'),
    path('disciplinary/warnings/', views.warning_letters, name='warning_letters'),
    path('disciplinary/suspensions/', views.suspensions, name='suspensions'),
    path('disciplinary/records/', views.disciplinary_records, name='disciplinary_records'),
    
    # ============= REPORTS =============
    path('reports/occupancy/', views.occupancy_reports, name='occupancy_reports'),
    path('reports/financial/', views.financial_reports, name='financial_reports'),
    path('reports/maintenance/', views.maintenance_reports, name='maintenance_reports'),
    path('reports/incidents/', views.incident_reports_summary, name='incident_reports_summary'),
    path('reports/monthly/', views.monthly_reports, name='monthly_reports'),
    
    # ============= AJAX/API ENDPOINTS =============
    path('ajax/available-beds/', views.get_available_beds_ajax, name='get_available_beds_ajax'),
    path('ajax/allocate-bed/', views.allocate_bed_ajax, name='allocate_bed_ajax'),
    path('ajax/update-maintenance/', views.update_maintenance_status_ajax, name='update_maintenance_status_ajax'),
    
    # ============= EXPORT FUNCTIONS =============
    path('export/occupancy/', views.export_occupancy_report, name='export_occupancy_report'),
    path('export/maintenance/', views.export_maintenance_report, name='export_maintenance_report'),
    
    # Student Records
    path('students/', views.registrar_student_list_view, name='registrar_student_list'),
    path('students/<int:student_id>/', views.registrar_student_detail_view, name='registrar_student_detail'),
    path('students/create/', views.registrar_student_create_view, name='registrar_student_create'),
    path('students/<int:student_id>/update/', views.registrar_student_update_view, name='registrar_student_update'),
    path('students/<int:student_id>/transcript/', views.registrar_transcript_view, name='registrar_transcript'),
    
    # Admissions
    path('admissions/', views.registrar_admissions_dashboard_view, name='registrar_admissions_dashboard'),
    path('admissions/intakes/', views.registrar_intake_management_view, name='registrar_intake_management'),
    path('admissions/letters/', views.registrar_admission_letters_view, name='registrar_admission_letters'),
    
    # Examinations
    path('examinations/', views.registrar_examinations_dashboard_view, name='registrar_examinations_dashboard'),
    path('examinations/results/', views.registrar_results_processing_view, name='registrar_results_processing'),
    path('examinations/publish/<int:semester_id>/<int:programme_unit_id>/', views.registrar_publish_results_view, name='registrar_publish_results'),
    
    # Graduation
    path('graduation/', views.registrar_graduation_dashboard_view, name='registrar_graduation_dashboard'),
    path('graduation/list/', views.registrar_graduation_list_view, name='registrar_graduation_list'),
    path('graduation/classification/', views.registrar_degree_classification_view, name='registrar_degree_classification'),
    
    # Academic Policies
    path('academic-calendar/', views.registrar_academic_calendar_view, name='registrar_academic_calendar'),
    path('policies/', views.registrar_policies_view, name='registrar_policies'),
    
    # Reports
    path('reports/', views.registrar_reports_dashboard_view, name='registrar_reports_dashboard'),
    path('reports/enrollment/', views.registrar_enrollment_statistics_view, name='registrar_enrollment_statistics'),
    path('reports/performance/', views.registrar_performance_report_view, name='registrar_performance_report'),
    
    # International Students
    path('international-students/', views.registrar_international_students_view, name='registrar_international_students'),
    
    # Semester Reporting & Progression
    path('semester-reports/', views.registrar_semester_reports_view, name='registrar_semester_reports'),
    path('semester-reports/<int:report_id>/approve/', views.registrar_approve_semester_report_view, name='registrar_approve_semester_report'),
    
    # Resit Management
    path('resit-management/', views.registrar_resit_management_view, name='registrar_resit_management'),
    
    # Student ID Cards
    path('id-cards/', views.registrar_id_card_applications_view, name='registrar_id_card_applications'),
    path('id-cards/<int:application_id>/approve/', views.registrar_id_card_approve_view, name='registrar_id_card_approve'),
    
    # Announcements
    path('announcements/', views.registrar_announcements_view, name='registrar_announcements'),
    path('announcements/create/', views.registrar_announcement_create_view, name='registrar_announcement_create'),
    
    # Export Functions
    path('export/students/csv/', views.registrar_export_students_csv_view, name='registrar_export_students_csv'),
    path('export/results/<int:semester_id>/csv/', views.registrar_export_results_csv_view, name='registrar_export_results_csv'),
       
]