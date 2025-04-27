# core/context_processors.py

def unread_notifications(request):
    """Add unread notification count to context"""
    notification_count = 0
    
    if request.user.is_authenticated:
        try:
            from .models import Notification
            notification_count = Notification.objects.filter(
                user=request.user,
                is_read=False
            ).count()
        except:
            pass
    
    return {'unread_notification_count': notification_count}