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


from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages


def store_required(view_func):
    """
    Decorator that restricts access to users with the 'store' role.
    Redirects unauthenticated users to login; raises 403 for wrong role.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'store':
            messages.error(request, "You do not have permission to access the Store Management area.")
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper