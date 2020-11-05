from django.db.models import query_utils
from django.http import request
from account_management.models import HotelStaffInformation, UserAccount
from account_management.serializers import ListOfIdSerializer, StaffInfoSerializer
from account_management import serializers
from drf_yasg2.utils import get_serializer_class, swagger_auto_schema
from rest_framework.permissions import IsAdminUser
from rest_framework.serializers import Serializer
from restaurant.models import Food, FoodCategory, FoodExtra, FoodOption, FoodOptionExtraType, FoodOrder, Restaurant, Table
from utils.response_wrapper import ResponseWrapper
from rest_framework import permissions, status, viewsets
<<<<<<< HEAD
from .serializers import FoodCategorySerializer, FoodDetailSerializer, FoodExtraSerializer, FoodOptionExtraTypeSerializer, FoodOptionSerializer, FoodOrderSerializer, FoodSerializer, RestaurantSerializer, RestaurantContactPerson, RestaurantUpdateSerialier, TableSerializer, HotelStaffInformationSerializer
=======
from .serializers import FoodCategorySerializer, FoodDetailSerializer, FoodExtraSerializer, FoodOptionExtraTypeSerializer, FoodOptionSerializer, FoodOrderSerializer, FoodSerializer, FoodsByCategorySerializer, RestaurantSerializer, RestaurantContactPerson, RestaurantUpdateSerialier, TableSerializer
>>>>>>> b2750ae79797839d1f24a2e7dc56d914888cde32
from django.db.models import Q
from utils.custom_viewset import CustomViewSet


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
        if self.action in ["create", 'destroy', 'list']:
            permission_classes = [permissions.IsAdminUser]
        if self.action in ['update', 'restaurant_under_owner']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        serializer = RestaurantSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return ResponseWrapper(data=serializer.data, msg='created')
        else:
            return ResponseWrapper(error_code=400, error_msg=serializer.errors, msg='failed to create restaurent')

    def retrieve(self, request, pk, *args, **kwargs):
        qs = Restaurant.objects.filter(pk=pk).first()
        if qs:
            serializer = RestaurantSerializer(instance=qs)
            return ResponseWrapper(data=serializer.data)
        else:
            return ResponseWrapper(error_msg='invalid restaurant id', error_code=400)

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

        qs = serializer.update(qs.first(), serializer.validated_data)
        if not qs:
            return ResponseWrapper(error_code=404, error_msg=['update failed'])

        restaurant_serializer = RestaurantSerializer(instance=qs)
        return ResponseWrapper(data=restaurant_serializer.data, msg='updated')

    def restaurant_under_owner(self, request, *args, **kwargs):
        owner_qs = UserAccount.objects.filter(pk=request.user.pk).first()
        restaurant_list = owner_qs.hotel_staff.values_list(
            'restaurant', flat=True)
        qs = Restaurant.objects.filter(pk__in=restaurant_list)
        serializer = RestaurantSerializer(instance=qs, many=True)
        return ResponseWrapper(data=serializer.data)

    def list(self, request, *args, **kwargs):
        qs = Restaurant.objects.all()
        serializer = RestaurantSerializer(instance=qs, many=True)
        return ResponseWrapper(data=serializer.data)


# class FoodCategoryViewSet(viewsets.GenericViewSet):
#     serializer_class = FoodCategorySerializer
#     permission_classes = [permissions.IsAdminUser]
#     queryset = FoodCategory.objects.all()
#     lookup_field = 'pk'

#     def list(self, request):
#         qs = self.get_queryset()
#         serializer = self.serializer_class(instance=qs, many=True)
#         # serializer.is_valid()
#         return ResponseWrapper(data=serializer.data, msg='success')

#     def create(self, request):
#         serializer = self.serializer_class(data=request.data)
#         if serializer.is_valid():
#             qs = serializer.save()
#             serializer = self.serializer_class(instance=qs)
#             return ResponseWrapper(data=serializer.data, msg='created')
#         else:
#             return ResponseWrapper(error_msg=serializer.errors, error_code=400)

#     def update(self, request, **kwargs):
#         serializer = self.serializer_class(data=request.data)
#         if serializer.is_valid():
#             qs = serializer.update(instance=self.get_object(
#             ), validated_data=serializer.validated_data)
#             serializer = self.serializer_class(instance=qs)
#             return ResponseWrapper(data=serializer.data)
#         else:
#             return ResponseWrapper(error_msg=serializer.errors, error_code=400)

#     def destroy(self, request, **kwargs):
#         qs = self.queryset.filter(**kwargs).first()
#         if qs:
#             qs.delete()
#             return ResponseWrapper(status=200, msg='deleted')
#         else:
#             return ResponseWrapper(error_msg="failed to delete", error_code=400)


class FoodCategoryViewSet(CustomViewSet):
    serializer_class = FoodCategorySerializer
    # permission_classes = [permissions.IsAuthenticated]
    queryset = FoodCategory.objects.all()
    lookup_field = 'pk'


class FoodOptionExtraTypeViewSet(CustomViewSet):
    serializer_class = FoodOptionExtraTypeSerializer
    # permission_classes = [permissions.IsAuthenticated]
    queryset = FoodOptionExtraType.objects.all()
    lookup_field = 'pk'


class FoodExtraViewSet(CustomViewSet):
    serializer_class = FoodExtraSerializer
    # permission_classes = [permissions.IsAuthenticated]
    queryset = FoodExtra.objects.all()
    lookup_field = 'pk'


class FoodOptionViewSet(CustomViewSet):
    serializer_class = FoodOptionSerializer
    # permission_classes = [permissions.IsAuthenticated]
    queryset = FoodOption.objects.all()
    lookup_field = 'pk'

"""
class TableViewSet(CustomViewSet):
    serializer_class = TableSerializer
    # permission_classes = [permissions.IsAuthenticated]
    queryset = Table.objects.all()
    lookup_field = 'pk'
"""


class TableViewSet(CustomViewSet):
    serializer_class = TableSerializer
    # permission_classes = [permissions.IsAuthenticated]
    queryset = Table.objects.all()
    lookup_field = 'restaurant'
    http_method_names = ['get']

    def table_list(self, request, restaurant, *args, **kwargs):
        qs = self.queryset.filter(restaurant=restaurant)
        # qs = qs.filter(is_top = True)
        serializer = self.serializer_class(instance=qs, many=True)
        return ResponseWrapper(data=serializer.data, msg='success')

<<<<<<< HEAD
"""
class TableViewSetManager(CustomViewSet):
    serializer_class = HotelStaffInformationSerializer
    # permission_classes = [permissions.IsAuthenticated]
    queryset = HotelStaffInformation.objects.all()
    lookup_field = 'manager'
    http_method_names = ['get']
=======
    @swagger_auto_schema(request_body=ListOfIdSerializer)
    def add_staff(self, request, *args, **kwargs):
        qs = self.get_object()
        id_list = request.data.get('id', [])
        id_list = list(HotelStaffInformation.objects.filter(
            pk__in=id_list).values_list('pk', flat=True))
        if qs:
            for id in id_list:
                qs.staff_assigned.add(id)
            qs.save()
            serializer = self.serializer_class(instance=qs)
            return ResponseWrapper(data=serializer.data)
        else:
            return ResponseWrapper(error_code=400, error_msg='wrong table id')

>>>>>>> b2750ae79797839d1f24a2e7dc56d914888cde32

    def manager_table_list(self, request, manager, *args, **kwargs):
        qs = self.queryset.filter(manager=manager)
        # qs = qs.filter(is_top = True)
        serializer = self.serializer_class(instance=qs, many=True)
        return ResponseWrapper(data=serializer.data, msg='success')

"""
class FoodOrderViewSet(CustomViewSet):
    serializer_class = FoodOrderSerializer
    # permission_classes = [permissions.IsAuthenticated]
    queryset = FoodOrder.objects.all()
    lookup_field = 'pk'


class FoodViewSet(CustomViewSet):
    serializer_class = FoodSerializer

    def get_serializer_class(self):
        if self.action == 'retrieve':
            self.serializer_class = FoodDetailSerializer
        return self.serializer_class
    # permission_classes = [permissions.IsAuthenticated]
    queryset = Food.objects.all()
    lookup_field = 'pk'
    # http_method_names = ['post', 'patch', 'put']


class FoodByRestaurantViewSet(CustomViewSet):
    serializer_class = FoodSerializer

    # queryset = Food.objects.all()

    # permission_classes = [permissions.IsAuthenticated]
<<<<<<< HEAD

=======
>>>>>>> b2750ae79797839d1f24a2e7dc56d914888cde32
    queryset = Food.objects.all()
    lookup_field = 'restaurant'
    http_method_names = ['get']

    def top_foods(self, request, restaurant, *args, **kwargs):
        qs = self.queryset.filter(restaurant=restaurant, is_top=True)
        # qs = qs.filter(is_top = True)
        serializer = self.serializer_class(instance=qs, many=True)
        return ResponseWrapper(data=serializer.data, msg='success')

    def recommended_foods(self, request, restaurant, *args, **kwargs):
        qs = self.queryset.filter(restaurant=restaurant, is_recommended=True)
        # qs = qs.filter(is_top = True)
        serializer = self.serializer_class(instance=qs, many=True)
        return ResponseWrapper(data=serializer.data, msg='success')

<<<<<<< HEAD
    def list(self,request,restaurant,*args,**kwargs):
=======
    def list(self, request, restaurant, *args, **kwargs):
>>>>>>> b2750ae79797839d1f24a2e7dc56d914888cde32
        qs = self.queryset.filter(restaurant=restaurant)
        # qs = qs.filter(is_top = True)
        serializer = self.serializer_class(instance=qs, many=True)
        return ResponseWrapper(data=serializer.data, msg='success')

<<<<<<< HEAD





=======
    def top_foods_by_category(self, request, restaurant, *args, **kwargs):
        qs = FoodCategory.objects.filter(
            foods__restaurant=restaurant,
            foods__is_top=True
        ).prefetch_related('foods')
        # qs = qs.filter(is_top = True)
        serializer = FoodsByCategorySerializer(instance=qs, many=True)
        return ResponseWrapper(data=serializer.data, msg='success')

    def recommended_foods_by_category(self, request, restaurant, *args, **kwargs):
        qs = FoodCategory.objects.filter(
            foods__restaurant=restaurant,
            foods__is_recommended=True
        ).prefetch_related('foods')
        # qs = qs.filter(is_top = True)
        serializer = FoodsByCategorySerializer(instance=qs, many=True)
        return ResponseWrapper(data=serializer.data, msg='success')

    def list_by_category(self, request, restaurant, *args, **kwargs):
        qs = FoodCategory.objects.filter(
            foods__restaurant=restaurant,
        ).prefetch_related('foods')
        # qs = qs.filter(is_top = True)
        serializer = FoodsByCategorySerializer(instance=qs, many=True)
        return ResponseWrapper(data=serializer.data, msg='success')
>>>>>>> b2750ae79797839d1f24a2e7dc56d914888cde32
