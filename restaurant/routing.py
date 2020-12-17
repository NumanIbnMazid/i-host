from . import consumers
from django.urls import path
from django.core.asgi import get_asgi_application


websocket_urlpatterns = [
    path(r'ws/dashboard/<int:restaurant_id>/',
         consumers.DashboardConsumer.as_asgi()),
    # re_path(r"", get_asgi_application()),
]
