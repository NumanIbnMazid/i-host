from . import consumers
from django.urls import re_path

websocket_urlpatterns = [
    re_path(r'ws/dashboard/(?P<restaurant_id>\w+)/$',
            consumers.RestaurantOrderListConsumer.as_asgi()),
]
