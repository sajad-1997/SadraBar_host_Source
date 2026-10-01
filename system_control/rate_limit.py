"""
Rate limiting middleware for API and view protection.
Implements IP-based and user-based rate limiting.
"""
from django.core.cache import cache
from django.http import HttpResponse
from django.conf import settings


class RateLimitMiddleware:
    """
    Middleware to enforce rate limiting on requests.
    Limits requests per IP address and per authenticated user.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.enabled = getattr(settings, 'RATE_LIMIT_ENABLE', True)
        self.requests_per_minute = getattr(settings, 'RATE_LIMIT_REQUESTS', 10)
    
    def __call__(self, request):
        if not self.enabled:
            return self.get_response(request)
        
        # Skip rate limiting for exempt paths
        exempt_paths = ['/static/', '/media/', '/admin/', '/favicon.ico']
        if any(request.path.startswith(path) for path in exempt_paths):
            return self.get_response(request)
        
        # Get identifier (IP or user ID)
        if request.user.is_authenticated:
            identifier = f"user_{request.user.id}"
        else:
            identifier = f"ip_{self._get_client_ip(request)}"
        
        # Check rate limit
        cache_key = f"rate_limit_{identifier}"
        requests = cache.get(cache_key, 0)
        
        if requests >= self.requests_per_minute:
            return HttpResponse(
                "Too many requests. Please try again later.",
                status=429
            )
        
        # Increment counter
        cache.set(cache_key, requests + 1, 60)  # 60 seconds window
        
        return self.get_response(request)
    
    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
