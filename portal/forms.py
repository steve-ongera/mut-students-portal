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