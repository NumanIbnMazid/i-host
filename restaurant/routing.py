from . import consumers
from django.urls import re_path
from django.core.asgi import get_asgi_application


websocket_urlpatterns = [
    re_path(r'ws/dashboard/(?P<restaurant_id>\w+)/$',
            consumers.DashboardConsumer.as_asgi()),
    re_path(r"", get_asgi_application()),
]
