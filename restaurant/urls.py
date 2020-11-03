# from rest_framework.routers import DefaultRouter
from .views import FoodCategoryViewSet, RestaurantViewSet
from django.urls import include, path


urlpatterns = [
    path('restaurant/',
         RestaurantViewSet.as_view({'post': 'create', 'get': 'list'}), name='restaurant_create_and_list'),
    path('restaurant/<int:pk>/',
         RestaurantViewSet.as_view({'patch': 'update', 'get': 'retrieve'}), name='restaurant_update'),
    path("food_category/",
         FoodCategoryViewSet.as_view({"post": "create", "get": "list"})),
    path("food_category/<int:pk>/",
         FoodCategoryViewSet.as_view({"patch": "update", "delete": "destroy"})),

    path('restaurant_under_owner/',
         RestaurantViewSet.as_view({'get': 'restaurant_under_owner'}), name='restaurant_under_owner'),
]
