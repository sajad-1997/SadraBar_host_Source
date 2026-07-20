"""
WSGI config for SadraBar project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""
import traceback
import sys
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SadraBar.settings')

application = get_wsgi_application()



try:
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
except Exception:
    with open("/home/mpwygdcu/error.log", "w") as f:
        f.write(traceback.format_exc())
    raise