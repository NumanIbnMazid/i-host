"""
ASGI config for ihost project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/asgi/
"""

from channels.routing import ProtocolTypeRouter
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ihost.settings')

# application = get_asgi_application()


application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "https": get_asgi_application(),
    # Just HTTP for now. (We can add other protocols later.)
})
