from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def lecturer_required(view_func):
    """Decorator to check if user is a lecturer"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to access this page.')
            return redirect('login')
        
        if request.user.role != 'lecturer':
            messages.error(request, 'Access denied. This page is only for lecturers.')
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper