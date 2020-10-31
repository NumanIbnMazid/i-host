# from rest_framework.routers import DefaultRouter
from .views import RestaurantViewSet
from django.urls import include, path


urlpatterns = [
    path('restaurant/',
         RestaurantViewSet.as_view({'post': 'create'}), name='restaurant_create'),
    path('restaurant/<int:pk>/',
         RestaurantViewSet.as_view({'patch': 'update', 'get': 'retrieve'}), name='restaurant_update'),
]
