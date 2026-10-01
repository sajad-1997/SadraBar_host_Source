"""
Security monitoring module for tracking suspicious activities and security events.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.cache import cache


User = get_user_model()


class SecurityEvent(models.Model):
    """Track security-related events for monitoring and auditing."""
    
    EVENT_TYPES = [
        ('login_success', 'Login Success'),
        ('login_failure', 'Login Failure'),
        ('password_change', 'Password Change'),
        ('permission_denied', 'Permission Denied'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('rate_limit_exceeded', 'Rate Limit Exceeded'),
        ('module_access_denied', 'Module Access Denied'),
        ('quota_exceeded', 'Quota Exceeded'),
        ('unusual_location', 'Unusual Location'),
        ('brute_force_attempt', 'Brute Force Attempt'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES, db_index=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='low')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='security_events')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    path = models.CharField(max_length=500, blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        verbose_name = 'Security Event'
        verbose_name_plural = 'Security Events'
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['severity', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_event_type_display()} - {self.user or 'Anonymous'} - {self.created_at}"


class LoginAttempt(models.Model):
    """Track login attempts for brute force detection."""
    
    username = models.CharField(max_length=150, db_index=True)
    ip_address = models.GenericIPAddressField(db_index=True)
    success = models.BooleanField(default=False)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        verbose_name = 'Login Attempt'
        verbose_name_plural = 'Login Attempts'
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['username', 'created_at']),
            models.Index(fields=['ip_address', 'created_at']),
        ]
    
    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{status} - {self.username} - {self.ip_address}"


class SecurityMonitor:
    """Service class for security monitoring operations."""
    
    @staticmethod
    def log_event(event_type, user=None, ip_address=None, severity='low', 
                  path='', details=None, user_agent=''):
        """Log a security event."""
        SecurityEvent.objects.create(
            event_type=event_type,
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            path=path,
            details=details or {},
            severity=severity
        )
    
    @staticmethod
    def log_login_attempt(username, ip_address, success, user_agent=''):
        """Log a login attempt."""
        LoginAttempt.objects.create(
            username=username,
            ip_address=ip_address,
            success=success,
            user_agent=user_agent
        )
    
    @staticmethod
    def check_brute_force(username, ip_address, max_attempts=5, window_minutes=15):
        """Check if brute force attack is detected."""
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff = timezone.now() - timedelta(minutes=window_minutes)
        
        # Check by username
        username_attempts = LoginAttempt.objects.filter(
            username=username,
            success=False,
            created_at__gte=cutoff
        ).count()
        
        # Check by IP
        ip_attempts = LoginAttempt.objects.filter(
            ip_address=ip_address,
            success=False,
            created_at__gte=cutoff
        ).count()
        
        return username_attempts >= max_attempts or ip_attempts >= max_attempts
    
    @staticmethod
    def get_recent_security_events(hours=24, severity=None):
        """Get recent security events."""
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff = timezone.now() - timedelta(hours=hours)
        queryset = SecurityEvent.objects.filter(created_at__gte=cutoff)
        
        if severity:
            queryset = queryset.filter(severity=severity)
        
        return queryset.order_by('-created_at')
    
    @staticmethod
    def get_security_summary(hours=24):
        """Get summary of security events."""
        from django.db.models import Count
        
        events = SecurityEvent.objects.filter(
            created_at__gte=timezone.now() - timezone.timedelta(hours=hours)
        )
        
        summary = {
            'total': events.count(),
            'by_type': dict(events.values('event_type').annotate(count=Count('id')).values_list('event_type', 'count')),
            'by_severity': dict(events.values('severity').annotate(count=Count('id')).values_list('severity', 'count')),
            'critical': events.filter(severity='critical').count(),
            'high': events.filter(severity='high').count(),
        }
        
        return summary
    
    @staticmethod
    def detect_suspicious_activity(user):
        """Detect suspicious activity patterns for a user."""
        from django.db.models import Count
        
        recent_events = SecurityEvent.objects.filter(
            user=user,
            created_at__gte=timezone.now() - timezone.timedelta(hours=1)
        )
        
        # Check for multiple failed logins
        failed_logins = recent_events.filter(event_type='login_failure').count()
        if failed_logins >= 3:
            return True, f"Multiple failed login attempts: {failed_logins}"
        
        # Check for permission denials
        permission_denials = recent_events.filter(event_type='permission_denied').count()
        if permission_denials >= 5:
            return True, f"Multiple permission denials: {permission_denials}"
        
        return False, None
