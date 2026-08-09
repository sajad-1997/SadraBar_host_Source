from django import template
from django.conf import settings

register = template.Library()

@register.simple_tag(takes_context=True)
def pwa_splash_screen(context):
    """Returns splash screen HTML if this is a PWA install"""
    request = context.get('request')
    if request:
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        # Detect if this is a mobile device launching as PWA
        if any(x in user_agent.lower() for x in ['mobile', 'android', 'iphone']):
            return '''
            <div id="pwa-splash" class="pwa-splash">
                <img src="/static/pwa/icons/icon-192x192.png" alt="صدرابار">
                <h1>صدرابار خراسان</h1>
            </div>
            <script>
                window.addEventListener('load', function() {
                    setTimeout(function() {
                        var splash = document.getElementById('pwa-splash');
                        if (splash) {
                            splash.style.opacity = '0';
                            splash.style.transition = 'opacity 0.5s ease';
                            setTimeout(function() { splash.remove(); }, 500);
                        }
                    }, 1000);
                });
            </script>
            '''
    return ''
