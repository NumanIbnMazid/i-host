# from rest_framework.routers import DefaultRouter
from .views import RestaurantViewSet
from django.urls import include, path


urlpatterns = [
    path('restaurant/',
         RestaurantViewSet.as_view({'post': 'create', 'get': 'list'}), name='restaurant_create_and_list'),
    path('restaurant/<int:pk>/',
         RestaurantViewSet.as_view({'patch': 'update', 'get': 'retrieve'}), name='restaurant_update'),

    path('restaurant_under_owner/',
         RestaurantViewSet.as_view({'get': 'restaurant_under_owner'}), name='restaurant_under_owner'),
]
