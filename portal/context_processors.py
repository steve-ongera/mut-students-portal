
# ============= CONTEXT PROCESSORS =============
# Create context_processors.py to add data to all templates

def semester_reporting_context(request):
    """
    Add semester reporting context to all templates
    """
    if request.user.is_authenticated and hasattr(request.user, 'student_profile'):
        from portal.models import Semester, SemesterReport
        from .utils import get_student_eligibility_for_reporting
        
        student = request.user.student_profile
        current_semester = Semester.objects.filter(is_current=True).first()
        
        # Check if reported for current semester
        has_reported = SemesterReport.objects.filter(
            student=student,
            to_semester=current_semester,
            status__in=['pending', 'approved']
        ).exists() if current_semester else False
        
        # Check eligibility
        is_eligible, failed_count, message = get_student_eligibility_for_reporting(student)
        
        return {
            'current_semester': current_semester,
            'has_reported_current_semester': has_reported,
            'is_eligible_to_report': is_eligible,
            'failed_units_count': failed_count,
        }
    
    return {}


# context_processors.py
from django.utils import timezone
from django.db.models import Count, Q, Avg
from datetime import timedelta
import uuid

def ai_chatbot_context(request):
    """
    Context processor for AI chatbot functionality
    Provides chatbot data to all templates
    """
    context = {
        'ai_enabled': True,
        'chat_session': None,
        'unread_ai_alerts': [],
        'ai_personalization': None,
        'quick_actions': [],
        'ai_stats': {},
    }
    
    # Import models here to avoid circular imports
    from portal.models import (
        ChatSession, ChatMessage, AIPersonalization, 
        ProactiveAIAlert, QuickAction, Student
    )
    
    try:
        # Get or create chat session
        session_id = request.session.get('chat_session_id')
        
        if session_id:
            try:
                chat_session = ChatSession.objects.get(session_id=session_id, status='active')
            except ChatSession.DoesNotExist:
                chat_session = None
        else:
            chat_session = None
        
        # Create new session if needed
        if not chat_session:
            chat_session = ChatSession.objects.create(
                user=request.user if request.user.is_authenticated else None,
                is_authenticated=request.user.is_authenticated,
                user_role=getattr(request.user, 'role', '') if request.user.is_authenticated else '',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                device_type=detect_device_type(request),
                context_data=get_user_context(request),
            )
            request.session['chat_session_id'] = str(chat_session.session_id)
        
        # Update last activity
        chat_session.last_activity = timezone.now()
        chat_session.save(update_fields=['last_activity'])
        
        context['chat_session'] = chat_session
        
        # Get recent messages (last 10)
        recent_messages = ChatMessage.objects.filter(
            session=chat_session
        ).select_related('matched_knowledge').order_by('-timestamp')[:10]
        
        context['recent_messages'] = list(reversed(recent_messages))
        context['message_count'] = chat_session.message_count
        
        # For authenticated users
        if request.user.is_authenticated:
            # Get or create personalization
            personalization, created = AIPersonalization.objects.get_or_create(
                user=request.user,
                defaults={
                    'student': getattr(request.user, 'student_profile', None)
                }
            )
            context['ai_personalization'] = personalization
            
            # Get unread AI alerts
            unread_alerts = ProactiveAIAlert.objects.filter(
                user=request.user,
                is_read=False,
                is_dismissed=False
            ).order_by('-priority', '-sent_at')[:5]
            
            context['unread_ai_alerts'] = unread_alerts
            context['unread_alerts_count'] = unread_alerts.count()
            
            # Get student-specific data if student
            if hasattr(request.user, 'student_profile'):
                student = request.user.student_profile
                context['student_data'] = {
                    'registration_number': student.registration_number,
                    'programme': student.programme.name,
                    'current_year': student.current_year,
                    'current_semester': student.current_semester,
                    'gpa': float(student.cumulative_gpa),
                }
        
        # Get quick actions relevant to user
        quick_actions = QuickAction.objects.filter(
            is_active=True
        ).order_by('display_order')
        
        if request.user.is_authenticated:
            user_role = getattr(request.user, 'role', '')
            quick_actions = quick_actions.filter(
                Q(applicable_roles__contains=[user_role]) | 
                Q(applicable_roles=[])
            )
        else:
            quick_actions = quick_actions.filter(requires_authentication=False)
        
        context['quick_actions'] = quick_actions[:6]
        
        # AI Statistics (for admin/monitoring)
        if request.user.is_authenticated and request.user.is_staff:
            from django.db.models import Avg
            today = timezone.now().date()
            
            context['ai_stats'] = {
                'total_sessions_today': ChatSession.objects.filter(
                    started_at__date=today
                ).count(),
                'active_sessions': ChatSession.objects.filter(
                    status='active',
                    last_activity__gte=timezone.now() - timedelta(hours=1)
                ).count(),
                'avg_satisfaction': ChatSession.objects.filter(
                    satisfaction_rating__isnull=False,
                    started_at__date=today
                ).aggregate(avg=Avg('satisfaction_rating'))['avg'] or 0,
            }
    
    except Exception as e:
        # Log error but don't break the site
        print(f"AI Context Processor Error: {e}")
        import traceback
        traceback.print_exc()
    
    return context


def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def detect_device_type(request):
    """Detect device type from user agent"""
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    
    if 'mobile' in user_agent or 'android' in user_agent:
        return 'mobile'
    elif 'tablet' in user_agent or 'ipad' in user_agent:
        return 'tablet'
    else:
        return 'desktop'


def get_user_context(request):
    """Build context data for the user"""
    context_data = {
        'timestamp': timezone.now().isoformat(),
        'page_url': request.path,
    }
    
    if request.user.is_authenticated:
        context_data.update({
            'user_id': request.user.id,
            'username': request.user.username,
            'role': getattr(request.user, 'role', ''),
        })
        
        # Add student-specific context
        if hasattr(request.user, 'student_profile'):
            student = request.user.student_profile
            context_data.update({
                'registration_number': student.registration_number,
                'programme_id': student.programme.id,
                'programme_code': student.programme.code,
                'current_year': student.current_year,
                'current_semester': student.current_semester,
            })
    
    return context_data