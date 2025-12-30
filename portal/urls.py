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


]