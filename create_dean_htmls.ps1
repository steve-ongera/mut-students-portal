# PowerShell Script to Create Empty HTML Files for Dean Views
# Save this as create_dean_htmls.ps1

# Function to create directory if it doesn't exist
function Ensure-Directory {
    param([string]$Path)
    if (!(Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
        Write-Host "Created directory: $Path" -ForegroundColor Green
    }
}

# Function to create empty HTML file
function Create-HTMLFile {
    param(
        [string]$Path,
        [string]$Title,
        [string]$Category
    )
    $htmlContent = @"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>$Title - Dean Portal</title>
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Bootstrap Icons -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css">
    <!-- Custom CSS -->
    <link rel="stylesheet" href="../../static/css/dean.css">
</head>
<body>
    <!-- Navigation will be included via template inheritance -->
    
    <div class="container-fluid">
        <div class="row">
            <!-- Sidebar will be included -->
            <main class="col-md-9 ms-sm-auto col-lg-10 px-md-4">
                <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
                    <h1 class="h2">$Title</h1>
                    <div class="btn-toolbar mb-2 mb-md-0">
                        <!-- Page-specific actions will go here -->
                    </div>
                </div>
                
                <!-- Page content will go here -->
                <div class="alert alert-info">
                    <i class="bi bi-info-circle"></i> 
                    $Title page is under development. Content will be loaded dynamically.
                </div>
                
                <!-- Placeholder for dynamic content -->
                <div class="row">
                    <div class="col-12">
                        <div class="card">
                            <div class="card-header">
                                <h5 class="card-title mb-0">$Category</h5>
                            </div>
                            <div class="card-body">
                                <p class="card-text">
                                    This page will display $Title information.
                                    Data will be populated from the Django backend.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    </div>
    
    <!-- Bootstrap JS Bundle with Popper -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <!-- Custom JS -->
    <script src="../../static/js/dean.js"></script>
</body>
</html>
"@
    
    $htmlContent | Out-File -FilePath $Path -Encoding UTF8
    Write-Host "Created: $Path" -ForegroundColor Cyan
}

# Base directory structure
$baseDir = "templates/dean"

# Create base directories
$directories = @(
    "$baseDir/school_overview",
    "$baseDir/academic_management",
    "$baseDir/quality_assurance",
    "$baseDir/research",
    "$baseDir/hr",
    "$baseDir/finance",
    "$baseDir/partnerships",
    "$baseDir/strategic",
    "$baseDir/approvals"
)

foreach ($dir in $directories) {
    Ensure-Directory -Path $dir
}

# ==================== SCHOOL OVERVIEW HTML FILES ====================
Write-Host "`nCreating School Overview HTML files..." -ForegroundColor Yellow

Create-HTMLFile -Path "$baseDir/school_overview/school_profile.html" `
    -Title "School Profile" -Category "School Overview"

Create-HTMLFile -Path "$baseDir/school_overview/departments_list.html" `
    -Title "Departments" -Category "School Overview"

Create-HTMLFile -Path "$baseDir/school_overview/department_detail.html" `
    -Title "Department Details" -Category "School Overview"

Create-HTMLFile -Path "$baseDir/school_overview/academic_staff.html" `
    -Title "Academic Staff" -Category "School Overview"

Create-HTMLFile -Path "$baseDir/school_overview/staff_detail.html" `
    -Title "Staff Profile" -Category "School Overview"

Create-HTMLFile -Path "$baseDir/school_overview/student_population.html" `
    -Title "Student Population" -Category "School Overview"

Create-HTMLFile -Path "$baseDir/school_overview/school_calendar.html" `
    -Title "School Calendar" -Category "School Overview"

# ==================== ACADEMIC MANAGEMENT HTML FILES ====================
Write-Host "`nCreating Academic Management HTML files..." -ForegroundColor Yellow

Create-HTMLFile -Path "$baseDir/academic_management/programme_development.html" `
    -Title "Programme Development" -Category "Academic Management"

Create-HTMLFile -Path "$baseDir/academic_management/programme_detail.html" `
    -Title "Programme Details" -Category "Academic Management"

Create-HTMLFile -Path "$baseDir/academic_management/curriculum_review.html" `
    -Title "Curriculum Review" -Category "Academic Management"

Create-HTMLFile -Path "$baseDir/academic_management/unit_detail.html" `
    -Title "Unit Details" -Category "Academic Management"

Create-HTMLFile -Path "$baseDir/academic_management/academic_standards.html" `
    -Title "Academic Standards" -Category "Academic Management"

Create-HTMLFile -Path "$baseDir/academic_management/accreditation.html" `
    -Title "Accreditation" -Category "Academic Management"

Create-HTMLFile -Path "$baseDir/academic_management/external_examiners.html" `
    -Title "External Examiners" -Category "Academic Management"

# ==================== QUALITY ASSURANCE HTML FILES ====================
Write-Host "`nCreating Quality Assurance HTML files..." -ForegroundColor Yellow

Create-HTMLFile -Path "$baseDir/quality_assurance/teaching_evaluations.html" `
    -Title "Teaching Evaluations" -Category "Quality Assurance"

Create-HTMLFile -Path "$baseDir/quality_assurance/programme_reviews.html" `
    -Title "Programme Reviews" -Category "Quality Assurance"

Create-HTMLFile -Path "$baseDir/quality_assurance/audit_reports.html" `
    -Title "Audit Reports" -Category "Quality Assurance"

Create-HTMLFile -Path "$baseDir/quality_assurance/compliance_monitoring.html" `
    -Title "Compliance Monitoring" -Category "Quality Assurance"

Create-HTMLFile -Path "$baseDir/quality_assurance/quality_metrics.html" `
    -Title "Quality Metrics" -Category "Quality Assurance"

# ==================== RESEARCH & INNOVATION HTML FILES ====================
Write-Host "`nCreating Research & Innovation HTML files..." -ForegroundColor Yellow

Create-HTMLFile -Path "$baseDir/research/research_strategy.html" `
    -Title "Research Strategy" -Category "Research & Innovation"

Create-HTMLFile -Path "$baseDir/research/grant_management.html" `
    -Title "Grant Management" -Category "Research & Innovation"

Create-HTMLFile -Path "$baseDir/research/publications.html" `
    -Title "Publications" -Category "Research & Innovation"

Create-HTMLFile -Path "$baseDir/research/research_centers.html" `
    -Title "Research Centers" -Category "Research & Innovation"

Create-HTMLFile -Path "$baseDir/research/innovation_projects.html" `
    -Title "Innovation Projects" -Category "Research & Innovation"

# ==================== HUMAN RESOURCES HTML FILES ====================
Write-Host "`nCreating Human Resources HTML files..." -ForegroundColor Yellow

Create-HTMLFile -Path "$baseDir/hr/staff_recruitment.html" `
    -Title "Staff Recruitment" -Category "Human Resources"

Create-HTMLFile -Path "$baseDir/hr/performance_appraisal.html" `
    -Title "Performance Appraisal" -Category "Human Resources"

Create-HTMLFile -Path "$baseDir/hr/promotions.html" `
    -Title "Promotions" -Category "Human Resources"

Create-HTMLFile -Path "$baseDir/hr/staff_development.html" `
    -Title "Staff Development" -Category "Human Resources"

Create-HTMLFile -Path "$baseDir/hr/disciplinary_matters.html" `
    -Title "Disciplinary Matters" -Category "Human Resources"

# ==================== FINANCIAL MANAGEMENT HTML FILES ====================
Write-Host "`nCreating Financial Management HTML files..." -ForegroundColor Yellow

Create-HTMLFile -Path "$baseDir/finance/school_budget.html" `
    -Title "School Budget" -Category "Financial Management"

Create-HTMLFile -Path "$baseDir/finance/resource_allocation.html" `
    -Title "Resource Allocation" -Category "Financial Management"

Create-HTMLFile -Path "$baseDir/finance/expenditure_control.html" `
    -Title "Expenditure Control" -Category "Financial Management"

Create-HTMLFile -Path "$baseDir/finance/revenue_generation.html" `
    -Title "Revenue Generation" -Category "Financial Management"

Create-HTMLFile -Path "$baseDir/finance/financial_reports.html" `
    -Title "Financial Reports" -Category "Financial Management"

# ==================== PARTNERSHIPS HTML FILES ====================
Write-Host "`nCreating Partnerships HTML files..." -ForegroundColor Yellow

Create-HTMLFile -Path "$baseDir/partnerships/industry_linkages.html" `
    -Title "Industry Linkages" -Category "Partnerships"

Create-HTMLFile -Path "$baseDir/partnerships/international_partners.html" `
    -Title "International Partners" -Category "Partnerships"

Create-HTMLFile -Path "$baseDir/partnerships/mous.html" `
    -Title "MOUs" -Category "Partnerships"

Create-HTMLFile -Path "$baseDir/partnerships/collaborative_projects.html" `
    -Title "Collaborative Projects" -Category "Partnerships"

Create-HTMLFile -Path "$baseDir/partnerships/alumni_relations.html" `
    -Title "Alumni Relations" -Category "Partnerships"

# ==================== STRATEGIC PLANNING HTML FILES ====================
Write-Host "`nCreating Strategic Planning HTML files..." -ForegroundColor Yellow

Create-HTMLFile -Path "$baseDir/strategic/strategic_goals.html" `
    -Title "Strategic Goals" -Category "Strategic Planning"

Create-HTMLFile -Path "$baseDir/strategic/performance_indicators.html" `
    -Title "Performance Indicators" -Category "Strategic Planning"

Create-HTMLFile -Path "$baseDir/strategic/annual_plans.html" `
    -Title "Annual Plans" -Category "Strategic Planning"

Create-HTMLFile -Path "$baseDir/strategic/progress_reports.html" `
    -Title "Progress Reports" -Category "Strategic Planning"

Create-HTMLFile -Path "$baseDir/strategic/future_planning.html" `
    -Title "Future Planning" -Category "Strategic Planning"

# ==================== APPROVALS HTML FILES ====================
Write-Host "`nCreating Approvals HTML files..." -ForegroundColor Yellow

Create-HTMLFile -Path "$baseDir/approvals/dashboard.html" `
    -Title "Approvals Dashboard" -Category "Approvals"

Create-HTMLFile -Path "$baseDir/approvals/department_budgets.html" `
    -Title "Department Budgets Approval" -Category "Approvals"

Create-HTMLFile -Path "$baseDir/approvals/staff_appointments.html" `
    -Title "Staff Appointments Approval" -Category "Approvals"

Create-HTMLFile -Path "$baseDir/approvals/research_grants.html" `
    -Title "Research Grants Approval" -Category "Approvals"

# ==================== CREATE BASE TEMPLATES ====================
Write-Host "`nCreating base templates..." -ForegroundColor Magenta

# Create base template for inheritance
$baseTemplate = @"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Dean Portal - University Management System{% endblock %}</title>
    
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Bootstrap Icons -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css">
    <!-- DataTables CSS -->
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.4/css/dataTables.bootstrap5.min.css">
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <!-- Custom CSS -->
    {% load static %}
    <link rel="stylesheet" href="{% static 'css/dean.css' %}">
    
    {% block extra_css %}{% endblock %}
</head>
<body>
    <!-- Navbar -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container-fluid">
            <a class="navbar-brand" href="{% url 'dean_dashboard' %}">
                <i class="bi bi-building"></i> Dean Portal
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="{% url 'dean_dashboard' %}">
                            <i class="bi bi-speedometer2"></i> Dashboard
                        </a>
                    </li>
                    <!-- More nav items will be added -->
                </ul>
                <ul class="navbar-nav">
                    <li class="nav-item dropdown">
                        <a class="nav-link dropdown-toggle" href="#" id="userDropdown" role="button" data-bs-toggle="dropdown">
                            <i class="bi bi-person-circle"></i> {{ request.user.get_full_name }}
                        </a>
                        <ul class="dropdown-menu">
                            <li><a class="dropdown-item" href="#"><i class="bi bi-person"></i> Profile</a></li>
                            <li><a class="dropdown-item" href="#"><i class="bi bi-gear"></i> Settings</a></li>
                            <li><hr class="dropdown-divider"></li>
                            <li><a class="dropdown-item" href="{% url 'logout' %}"><i class="bi bi-box-arrow-right"></i> Logout</a></li>
                        </ul>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container-fluid">
        <div class="row">
            <!-- Sidebar -->
            <nav id="sidebar" class="col-md-3 col-lg-2 d-md-block bg-light sidebar">
                <div class="position-sticky pt-3">
                    <h6 class="sidebar-heading d-flex justify-content-between align-items-center px-3 mt-4 mb-1 text-muted">
                        <span>SCHOOL OVERVIEW</span>
                    </h6>
                    <ul class="nav flex-column">
                        <li class="nav-item">
                            <a class="nav-link" href="{% url 'school_profile' %}">
                                <i class="bi bi-building"></i> School Profile
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="{% url 'departments_list' %}">
                                <i class="bi bi-diagram-3"></i> Departments
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="{% url 'academic_staff' %}">
                                <i class="bi bi-people"></i> Academic Staff
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="{% url 'student_population' %}">
                                <i class="bi bi-person-video3"></i> Student Population
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="{% url 'school_calendar' %}">
                                <i class="bi bi-calendar"></i> School Calendar
                            </a>
                        </li>
                    </ul>

                    <!-- More sidebar sections will be added for other modules -->
                    
                </div>
            </nav>

            <!-- Main content -->
            <main class="col-md-9 ms-sm-auto col-lg-10 px-md-4">
                <!-- Messages -->
                {% if messages %}
                <div class="mt-3">
                    {% for message in messages %}
                    <div class="alert alert-{{ message.tags }} alert-dismissible fade show" role="alert">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                    {% endfor %}
                </div>
                {% endif %}

                <!-- Page header -->
                <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
                    <h1 class="h2">{% block page_title %}{% endblock %}</h1>
                    <div class="btn-toolbar mb-2 mb-md-0">
                        {% block page_actions %}{% endblock %}
                    </div>
                </div>

                <!-- Page content -->
                {% block content %}{% endblock %}
            </main>
        </div>
    </div>

    <!-- Bootstrap JS Bundle with Popper -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <!-- jQuery -->
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <!-- DataTables -->
    <script src="https://cdn.datatables.net/1.13.4/js/jquery.dataTables.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.4/js/dataTables.bootstrap5.min.js"></script>
    <!-- Custom JS -->
    <script src="{% static 'js/dean.js' %}"></script>
    
    {% block extra_js %}{% endblock %}
</body>
</html>
"@

$baseTemplate | Out-File -FilePath "$baseDir/base.html" -Encoding UTF8
Write-Host "Created: $baseDir/base.html" -ForegroundColor Green

# Create dashboard template
Create-HTMLFile -Path "$baseDir/dashboard.html" `
    -Title "Dean Dashboard" -Category "Dashboard"

Write-Host "`n=== HTML File Creation Complete ===" -ForegroundColor Green
Write-Host "Total files created: 34 HTML templates" -ForegroundColor Green
Write-Host "Location: templates/dean/" -ForegroundColor Green
Write-Host "`nYou can now start developing your Django templates!" -ForegroundColor Yellow