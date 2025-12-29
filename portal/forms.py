from django import forms
from django.core.exceptions import ValidationError
from .models import AcademicYear, Semester, Intake


class AcademicYearForm(forms.ModelForm):
    """Form for creating and updating Academic Years"""
    
    class Meta:
        model = AcademicYear
        fields = ['name', 'start_date', 'end_date', 'is_current', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2024/2025',
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'is_current': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
        labels = {
            'name': 'Academic Year Name',
            'start_date': 'Start Date',
            'end_date': 'End Date',
            'is_current': 'Set as Current Academic Year',
            'is_active': 'Active',
        }
        help_texts = {
            'name': 'Format: YYYY/YYYY (e.g., 2024/2025)',
            'is_current': 'Only one academic year can be current at a time',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        # Validate dates
        if start_date and end_date:
            if end_date <= start_date:
                raise ValidationError('End date must be after start date.')
        
        return cleaned_data


class SemesterForm(forms.ModelForm):
    """Form for creating and updating Semesters"""
    
    class Meta:
        model = Semester
        fields = [
            'academic_year', 'name', 'semester_number', 'start_date', 'end_date',
            'registration_start_date', 'registration_end_date', 'is_current', 'is_active'
        ]
        widgets = {
            'academic_year': forms.Select(attrs={
                'class': 'form-select',
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Semester 1 - 2024/2025',
            }),
            'semester_number': forms.Select(attrs={
                'class': 'form-select',
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'registration_start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'registration_end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'is_current': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
        labels = {
            'academic_year': 'Academic Year',
            'name': 'Semester Name',
            'semester_number': 'Semester Number',
            'start_date': 'Semester Start Date',
            'end_date': 'Semester End Date',
            'registration_start_date': 'Registration Start Date',
            'registration_end_date': 'Registration End Date',
            'is_current': 'Set as Current Semester',
            'is_active': 'Active',
        }
        help_texts = {
            'name': 'Full name of the semester including academic year',
            'is_current': 'Only one semester can be current at a time',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Order academic years by start date (newest first)
        self.fields['academic_year'].queryset = AcademicYear.objects.all().order_by('-start_date')
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        reg_start = cleaned_data.get('registration_start_date')
        reg_end = cleaned_data.get('registration_end_date')
        
        # Validate semester dates
        if start_date and end_date:
            if end_date <= start_date:
                raise ValidationError('Semester end date must be after start date.')
        
        # Validate registration dates
        if reg_start and reg_end:
            if reg_end <= reg_start:
                raise ValidationError('Registration end date must be after registration start date.')
        
        # Registration should start before semester starts
        if reg_start and start_date:
            if reg_start >= start_date:
                raise ValidationError('Registration should start before the semester begins.')
        
        # Registration should end before or when semester starts
        if reg_end and start_date:
            if reg_end > start_date:
                self.add_error('registration_end_date', 
                             'Registration should end before or when the semester starts.')
        
        return cleaned_data


class IntakeForm(forms.ModelForm):
    """Form for creating and updating Intakes"""
    
    class Meta:
        model = Intake
        fields = [
            'academic_year', 'name', 'month', 'intake_number',
            'start_date', 'application_deadline', 'is_active'
        ]
        widgets = {
            'academic_year': forms.Select(attrs={
                'class': 'form-select',
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., September 2024 Intake',
            }),
            'month': forms.Select(attrs={
                'class': 'form-select',
            }),
            'intake_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., SEP/2024',
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'application_deadline': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
        labels = {
            'academic_year': 'Academic Year',
            'name': 'Intake Name',
            'month': 'Intake Month',
            'intake_number': 'Intake Number/Code',
            'start_date': 'Intake Start Date',
            'application_deadline': 'Application Deadline',
            'is_active': 'Active',
        }
        help_texts = {
            'name': 'Full name of the intake (e.g., September 2024 Intake)',
            'intake_number': 'Unique identifier (e.g., SEP/2024, JAN/2025)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Order academic years by start date (newest first)
        self.fields['academic_year'].queryset = AcademicYear.objects.all().order_by('-start_date')
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        deadline = cleaned_data.get('application_deadline')
        
        # Validate dates
        if start_date and deadline:
            if deadline >= start_date:
                raise ValidationError('Application deadline must be before the intake start date.')
        
        return cleaned_data
    
    

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Lecturer, User, Department


class UserForm(forms.ModelForm):
    """Form for User model (base user information)"""
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        }),
        required=False,
        help_text='Leave blank to keep current password (for updates) or auto-generate (for new users)'
    )
    
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        }),
        required=False
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email', 
            'phone_number', 'id_number', 'profile_picture'
        ]
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter username'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter last name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email address'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., +254712345678'
            }),
            'id_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter national ID number'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password:
            if password != confirm_password:
                raise forms.ValidationError("Passwords do not match.")
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        
        if password:
            user.set_password(password)
        elif not user.pk:  # New user without password
            # Generate a random password
            import secrets
            import string
            alphabet = string.ascii_letters + string.digits
            temp_password = ''.join(secrets.choice(alphabet) for i in range(12))
            user.set_password(temp_password)
        
        if commit:
            user.save()
        return user


class LecturerForm(forms.ModelForm):
    """Form for Lecturer model (lecturer-specific information)"""
    
    class Meta:
        model = Lecturer
        fields = [
            'employee_number', 'department', 'designation', 
            'qualification', 'specialization', 'office_location',
            'consultation_hours', 'hire_date', 'contract_end_date',
            'is_active'
        ]
        widgets = {
            'employee_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., LEC/2024/001'
            }),
            'department': forms.Select(attrs={
                'class': 'form-select'
            }),
            'designation': forms.Select(attrs={
                'class': 'form-select'
            }),
            'qualification': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., PhD in Computer Science'
            }),
            'specialization': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Machine Learning, Data Science'
            }),
            'office_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Block A, Room 201'
            }),
            'consultation_hours': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'e.g., Monday 2-4 PM, Wednesday 10-12 AM'
            }),
            'hire_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'contract_end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set department queryset to active departments only
        self.fields['department'].queryset = Department.objects.filter(
            is_active=True
        ).select_related('school').order_by('school__name', 'name')
        
        # Make contract_end_date not required
        self.fields['contract_end_date'].required = False
        self.fields['specialization'].required = False
        self.fields['office_location'].required = False
        self.fields['consultation_hours'].required = False
    
    def clean_employee_number(self):
        employee_number = self.cleaned_data.get('employee_number')
        
        # Check if employee number already exists (excluding current instance)
        if self.instance.pk:
            existing = Lecturer.objects.filter(
                employee_number=employee_number
            ).exclude(pk=self.instance.pk)
        else:
            existing = Lecturer.objects.filter(employee_number=employee_number)
        
        if existing.exists():
            raise forms.ValidationError(
                f'Employee number {employee_number} already exists.'
            )
        
        return employee_number
    
    def clean(self):
        cleaned_data = super().clean()
        hire_date = cleaned_data.get('hire_date')
        contract_end_date = cleaned_data.get('contract_end_date')
        
        if hire_date and contract_end_date:
            if contract_end_date <= hire_date:
                raise forms.ValidationError(
                    'Contract end date must be after hire date.'
                )
        
        return cleaned_data