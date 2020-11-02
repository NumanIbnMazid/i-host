from account_management.models import HotelStaffInformation
from account_management.serializers import StaffInfoSerializer
from account_management import serializers
from drf_yasg2.utils import get_serializer_class
from rest_framework.permissions import IsAdminUser
from rest_framework.serializers import Serializer
from restaurant.models import Restaurant
from utils.response_wrapper import ResponseWrapper
from rest_framework import permissions, status, viewsets
from .serializers import RestaurantSerializer, RestaurantContactPerson, RestaurantUpdateSerialier
from django.db.models import Q


class RestaurantViewSet(viewsets.ModelViewSet):
    queryset = Restaurant.objects.all()
    lookup_field = 'pk'
    # serializer_class = RestaurantContactPerson

    def get_serializer_class(self):
        if self.action == 'create':
            self.serializer_class = RestaurantSerializer
        elif self.action == 'update':
            self.serializer_class = RestaurantUpdateSerialier
        else:
            self.serializer_class = RestaurantSerializer

        return self.serializer_class

    def get_permissions(self):
        if self.action in ["create", 'destroy']:
            permission_classes = [permissions.IsAdminUser]
        if self.action in ['update']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        serializer = RestaurantSerializer(data=request.data)
        if not serializer.is_valid():
            return ResponseWrapper(error_code=400, error_msg=serializer.errors)
        qs = Restaurant.objects.create(**request.data)
        restaurant_serializer = RestaurantSerializer(instance=qs)
        return ResponseWrapper(data=restaurant_serializer.data, msg='created')

    def update(self, request, pk, *args, **kwargs):
        if not (
            self.request.user.is_staff or HotelStaffInformation.objects.filter(
                Q(is_owner=True) | Q(is_manager=True),
                user_id=request.user.pk, restaurant_id=pk
            )
        ):
            return ResponseWrapper(error_code=status.HTTP_401_UNAUTHORIZED, error_msg="can't update please consult with manager or owner of the hotel")
        serializer = RestaurantUpdateSerialier(data=request.data, partial=True)
        if not serializer.is_valid():
            return ResponseWrapper(error_code=400, error_msg=serializer.errors)
        qs = Restaurant.objects.filter(pk=pk)
        if not qs:
            return ResponseWrapper(error_code=404, error_msg=[{"restaurant_id": "restaurant not found"}])

        if qs.update(**request.data):
            qs = qs.first()
        else:
            return ResponseWrapper(error_code=404, error_msg=['update failed'])

        restaurant_serializer = RestaurantSerializer(instance=qs)
        return ResponseWrapper(data=restaurant_serializer.data, msg='updated')
