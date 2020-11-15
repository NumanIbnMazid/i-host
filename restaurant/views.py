from account_management import serializers
from account_management.models import HotelStaffInformation, UserAccount
from account_management.serializers import (ListOfIdSerializer,
                                            StaffInfoSerializer)
from django.db.models import Min, Q, query_utils
from django.http import request
from drf_yasg2.utils import get_serializer_class, swagger_auto_schema
from rest_framework import permissions, status, viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.serializers import Serializer
from utils.custom_viewset import CustomViewSet
from utils.response_wrapper import ResponseWrapper

from restaurant.models import (Food, FoodCategory, FoodExtra, FoodExtraType,
                               FoodOption, FoodOptionType, FoodOrder,
                               OrderedItem, Restaurant, Table)

from .serializers import (FoodCategorySerializer, FoodDetailSerializer,
                          FoodExtraPostPatchSerializer, FoodExtraSerializer,
                          FoodExtraTypeDetailSerializer,
                          FoodExtraTypeSerializer, FoodOptionBaseSerializer,
                          FoodOptionSerializer, FoodOptionTypeSerializer,
                          FoodOrderByTableSerializer,
                          FoodOrderCancelSerializer,
                          FoodOrderConfirmSerializer, FoodOrderSerializer,
                          FoodOrderUserPostSerializer,
                          FoodsByCategorySerializer, FoodSerializer,
                          FoodWithPriceSerializer, OrderedItemSerializer,
                          OrderedItemUserPostSerializer,
                          RestaurantContactPerson, RestaurantSerializer,
                          RestaurantUpdateSerialier, StaffIdListSerializer,
                          StaffTableSerializer, TableSerializer,
                          TableStaffSerializer)


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

    def order_item_list(self, request, restaurant_id, *args, **kwargs):
        qs = FoodOrder.objects.filter(table__restaurant=restaurant_id).exclude(
            status__in=['4_PAID', '5_CANCELLED'])
        orderd_table_set = set(qs.values_list('table_id', flat=True))
        table_qs = Table.objects.filter(
            restaurant=restaurant_id).exclude(pk__in=orderd_table_set)
        # all_table_set = set(table_qs.values_list('pk',flat=True))
        # empty_table_set = all_table_set - orderd_table_set
        empty_table_data = []
        for empty_table in table_qs:
            empty_table_data.append(
                {
                    'table': empty_table.pk,
                    'table_no': empty_table.table_no,
                    'table_name': empty_table.name,
                    'status': '',
                    'price': {},
                    'ordered_items': []
                }
            )
        serializer = FoodOrderByTableSerializer(instance=qs, many=True)

        return ResponseWrapper(data=serializer.data+empty_table_data, msg="success")

    def delete_restaurant(self, request, pk, *args, **kwargs):
        qs = self.queryset.filter(**kwargs).first()
        if qs:
            qs.delete()
            return ResponseWrapper(status=200, msg='deleted')
        else:
            return ResponseWrapper(error_msg="failed to delete", error_code=400)


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


class FoodOptionTypeViewSet(CustomViewSet):
    serializer_class = FoodOptionTypeSerializer
    # permission_classes = [permissions.IsAuthenticated]
    queryset = FoodOptionType.objects.all()
    lookup_field = 'pk'

    def list(self, request):
        qs = self.get_queryset().exclude(name='single_type')
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(instance=qs, many=True)
        # serializer = self.serializer_class(instance=qs, many=True)
        # serializer.is_valid()
        return ResponseWrapper(data=serializer.data, msg='success')


class FoodOrderedViewSet(CustomViewSet):
    serializer_class = FoodOrderSerializer
    qureyset = FoodOrder.objects.all()
    lookup_field = 'ordered_id'

    def ordered_item_list(self, request, ordered_id, *args, **kwargs):
        qs = FoodOrder.objects.filter(pk=ordered_id)
        #qs =self.queryset.filter(pk=ordered_id).prefetch_realted('ordered_items')
        serializer = self.get_serializer(instance=qs, many=True)
        return ResponseWrapper(data=serializer.data, msg="success")


class FoodExtraTypeViewSet(CustomViewSet):
    serializer_class = FoodExtraTypeSerializer
    # permission_classes = [permissions.IsAuthenticated]
    queryset = FoodExtraType.objects.all()
    lookup_field = 'pk'


class FoodExtraViewSet(CustomViewSet):

    # permission_classes = [permissions.IsAuthenticated]
    queryset = FoodExtra.objects.all()
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update':
            self.serializer_class = FoodExtraPostPatchSerializer
        else:
            self.serializer_class = FoodExtraSerializer

        return self.serializer_class

    #http_method_names = ['post', 'patch', 'get']
    def create(self, request):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        if serializer.is_valid():
            qs = serializer.save()
            serializer = FoodExtraTypeDetailSerializer(instance=qs)
            return ResponseWrapper(data=serializer.data, msg='created')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def update(self, request, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data, partial=True)
        if serializer.is_valid():
            qs = serializer.update(instance=self.get_object(
            ), validated_data=serializer.validated_data)
            serializer = FoodExtraTypeDetailSerializer(instance=qs)
            return ResponseWrapper(data=serializer.data)
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)


class FoodOptionViewSet(CustomViewSet):

    def get_serializer_class(self):
        if self.action in ['create', 'update']:
            self.serializer_class = FoodOptionBaseSerializer
        else:
            self.serializer_class = FoodOptionSerializer
        return self.serializer_class

    # permission_classes = [permissions.IsAuthenticated]

    queryset = FoodOption.objects.all()
    lookup_field = 'pk'

    def create(self, request):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        if serializer.is_valid():
            qs = serializer.save()
            serializer = FoodOptionSerializer(instance=qs)
            return ResponseWrapper(data=serializer.data, msg='created')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def update(self, request, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data, partial=True)
        if serializer.is_valid():
            qs = serializer.update(instance=self.get_object(
            ), validated_data=serializer.validated_data)
            serializer = FoodOptionSerializer(instance=qs)
            return ResponseWrapper(data=serializer.data)
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)


class TableViewSet(CustomViewSet):
    serializer_class = TableSerializer

    #permission_classes = [permissions.IsAuthenticated]
    queryset = Table.objects.all()
    lookup_field = 'pk'
    #http_method_names = ['get', 'post', 'patch']

    def get_permissions(self):
        if self.action in ['table_list']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action in ['add_staff']:
            self.serializer_class = StaffIdListSerializer
        elif self.action in ['remove_staff']:
            self.serializer_class = StaffIdListSerializer
        elif self.action in ['staff_table_list']:
            self.serializer_class = TableStaffSerializer
        elif self.action in ['order_item_list']:
            self.serializer_class = FoodOrderSerializer
        elif self.action in ['table_list']:
            self.serializer_class = StaffTableSerializer

        else:
            self.serializer_class = TableSerializer
        return self.serializer_class

    def table_list(self, request, restaurant, *args, **kwargs):

        qs = self.queryset.filter(restaurant=restaurant)
        # qs = qs.filter(is_top = True)
        serializer = self.get_serializer(
            instance=qs, many=True, context={'user': request.user})
        return ResponseWrapper(data=serializer.data, msg='success')

    # @swagger_auto_schema(request_body=ListOfIdSerializer)
    def add_staff(self, request, table_id, *args, **kwargs):
        qs = self.get_queryset().filter(pk=table_id).first()
        id_list = request.data.get('staff_list', [])
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

    def staff_table_list(self, request, staff_id, *args, **kwargs):
        qs = self.queryset.filter(staff_assigned=staff_id)
        # qs = qs.filter(is_top = True)
        serializer = self.get_serializer(instance=qs, many=True)
        return ResponseWrapper(data=serializer.data, msg='successful')

    def remove_staff(self, request, table_id, *args, **kwargs):
        qs = self.get_queryset().filter(pk=table_id).first()
        id_list = request.data.get('staff_list', [])
        id_list = list(HotelStaffInformation.objects.filter(
            pk__in=id_list).values_list('pk', flat=True))
        if qs:
            for id in id_list:
                qs.staff_assigned.remove(id)
            qs.save()
            serializer = self.serializer_class(instance=qs)
            return ResponseWrapper(msg='removed')
        else:
            return ResponseWrapper(error_code=400, error_msg='wrong table id')

    def order_item_list(self, request, table_id, *args, **kwargs):
        qs = FoodOrder.objects.filter(pk=table_id)
        #qs =self.queryset.filter(pk=ordered_id).prefetch_realted('ordered_items')
        serializer = self.get_serializer(instance=qs, many=True)
        return ResponseWrapper(data=serializer.data, msg="success")

    def delete_table(self, request, table_id, *args, **kwargs):
        qs = self.queryset.filter(**kwargs).first()
        if qs:
            qs.delete()
            return ResponseWrapper(status=200, msg='deleted')
        else:
            return ResponseWrapper(error_msg="failed to delete", error_code=400)

    # def table_order_list(self, request, restaurant,*args, **kwargs):
    #     qs = Table.objects.filter(restaurant=restaurant)
    #
    #     serializer = self.get_serializer(instance=qs,many=True)
    #     return ResponseWrapper(data=serializer.data,msg="success")


class FoodOrderViewSet(CustomViewSet):

    # permission_classes = [permissions.IsAuthenticated]
    queryset = FoodOrder.objects.all()
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.action in ['create_order']:
            self.serializer_class = FoodOrderUserPostSerializer
        elif self.action in ['add_items']:
            self.serializer_class = OrderedItemUserPostSerializer
        elif self.action in ['cancel_order']:
            self.serializer_class = FoodOrderCancelSerializer
        elif self.action in ['placed_status']:
            self.serializer_class = FoodOrderConfirmSerializer
        elif self.action in ['confirm_status']:
            self.serializer_class = FoodOrderConfirmSerializer
        elif self.action in ['in_table_status']:
            self.serializer_class = FoodOrderConfirmSerializer
        elif self.action in ['paid_status']:
            self.serializer_class = FoodOrderConfirmSerializer
        else:
            self.serializer_class = FoodOrderUserPostSerializer

        return self.serializer_class

    # def list(self,request,)

    # def book_table(self, request):
    #     # serializer_class = self.get_serializer_class()
    #     serializer = self.get_serializer(data=request.data)
    #     if serializer.is_valid():
    #         table_qs = Table.objects.filter(
    #             pk=request.data.get('table')).last()
    #         if not table_qs:
    #             return ResponseWrapper(error_msg=['table does not exists'], error_code=400)
    #         if not table_qs.is_occupied:
    #             table_qs.is_occupied = True
    #             table_qs.save()
    #             serializer = TableSerializer(instance=table_qs)
    #         else:
    #             return ResponseWrapper(error_msg=['table already occupied'], error_code=400)
    #         return ResponseWrapper(data=serializer.data, msg='created')
    #     else:
    #         return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def create_order(self, request):
        # serializer_class = self.get_serializer_class()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            table_qs = Table.objects.filter(
                pk=request.data.get('table')).last()
            if not table_qs.is_occupied:
                table_qs.is_occupied = True
                table_qs.save()
                qs = serializer.save()
                serializer = self.serializer_class(instance=qs)
            else:
                return ResponseWrapper(error_msg=['table already occupied'], error_code=400)
            return ResponseWrapper(data=serializer.data, msg='created')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def add_items(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return ResponseWrapper(data=serializer.data, msg='created')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def cancel_order(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            order_qs = FoodOrder.objects.filter(pk=request.data.get(
                'order_id')).exclude(status='4_PAID').first()
            if order_qs:
                order_qs.status = '5_CANCELLED'
                order_qs.save()
                order_qs.ordered_items.update(status="4_CANCELLED")
                table_qs = order_qs.table
                if table_qs.is_occupied:
                    table_qs.is_occupied = False
                    table_qs.save()

            else:
                return ResponseWrapper(
                    error_msg=['Order order not found'], error_code=400)

            serializer = FoodOrderUserPostSerializer(instance=order_qs)
            return ResponseWrapper(data=serializer.data, msg='Cancel')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def placed_status(self, request,  *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            order_qs = FoodOrder.objects.filter(pk=request.data.get("order_id"),
                                                status__in=['0_ORDER_INITIALIZED'
                                                            ]).first()
            if not order_qs:
                return ResponseWrapper(error_msg=['Order is invalid'], error_code=400)


            all_items_qs = OrderedItem.objects.filter(
                food_order=order_qs.pk, status__in=["0_ORDER_INITIALIZED"])
            all_items_qs.update(status='1_ORDER_PLACED')


            order_qs.status = '1_ORDER_PLACED'
            order_qs.save()
            serializer = FoodOrderByTableSerializer(instance=order_qs)

            return ResponseWrapper(data=serializer.data, msg='Placed')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def confirm_status(self, request,  *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            order_qs = FoodOrder.objects.filter(pk=request.data.get("order_id"),
                                                status__in=['1_ORDER_PLACED',
                                                            "2_ORDER_CONFIRMED",
                                                            "3_IN_TABLE"
                                                            ]).first()
            if not order_qs:
                return ResponseWrapper(error_msg=['Order is invalid'], error_code=400)


            all_items_qs = OrderedItem.objects.filter(
                food_order=order_qs.pk, status__in=["1_ORDER_PLACED"])
            all_items_qs.filter(pk__in=request.data.get(
                'food_items')).update(status='2_ORDER_CONFIRMED')
            all_items_qs.exclude(pk__in=request.data.get(
                'food_items')).update(status='4_CANCELLED')

            order_qs.status = '2_ORDER_CONFIRMED'
            order_qs.save()
            serializer = FoodOrderByTableSerializer(instance=order_qs)

            order_qs.status = '2_ORDER_CONFIRMED'
            order_qs.save()
            serializer = FoodOrderByTableSerializer(instance=order_qs)

            return ResponseWrapper(data=serializer.data, msg='Confirmed')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def in_table_status(self, request,  *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            order_qs = FoodOrder.objects.filter(pk=request.data.get("order_id"),
                                                status__in=['1_ORDER_PLACED',
                                                            "2_ORDER_CONFIRMED",
                                                            "3_IN_TABLE"
                                                            ]).first()
            if not order_qs:
                return ResponseWrapper(error_msg=['Order is invalid'], error_code=400)

            all_items_qs = OrderedItem.objects.filter(
                food_order=order_qs.pk, status__in=["2_ORDER_CONFIRMED"])
            all_items_qs.filter(pk__in=request.data.get(
                'food_items')).update(status='3_IN_TABLE')

            order_qs.status = '3_IN_TABLE'
            order_qs.save()
            serializer = FoodOrderByTableSerializer(instance=order_qs)

            return ResponseWrapper(data=serializer.data, msg='Served')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def paid_status(self, request,  *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            order_qs = FoodOrder.objects.filter(pk=request.data.get("order_id"),
                                                status__in=["3_IN_TABLE"]).first()
            if not order_qs:
                return ResponseWrapper(error_msg=['Order is invalid'], error_code=400)

            all_items_qs = OrderedItem.objects.exclude(
                food_order=order_qs.pk, status__in=["3_IN_TABLE",'4_CANCELLED']).count()

            if all_items_qs > 0:
                return ResponseWrapper(error_msg=['Order is running'], error_code=400)
            else:
                order_qs.status = '4_PAID'
                order_qs.save()
                serializer = FoodOrderByTableSerializer(instance=order_qs)

            return ResponseWrapper(data=serializer.data, msg='Paid')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

class OrderedItemViewSet(CustomViewSet):
    queryset = OrderedItem.objects.all()
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.action in ['create', 'update']:
            self.serializer_class = OrderedItemUserPostSerializer
        else:
            self.serializer_class = OrderedItemSerializer

        return self.serializer_class

    def create(self, request):
        serializer = self.get_serializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()

            return ResponseWrapper(data=serializer.data, msg='created')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)


class FoodViewSet(CustomViewSet):
    serializer_class = FoodWithPriceSerializer

    def get_serializer_class(self):
        if self.action == 'retrieve':
            self.serializer_class = FoodDetailSerializer

        return self.serializer_class
    # permission_classes = [permissions.IsAuthenticated]
    queryset = Food.objects.all()
    lookup_field = 'pk'
    http_method_names = ['post', 'patch', 'get', 'delete']

    def food_extra_by_food(self, request, *args, **kwargs):
        instance = self.get_object()

        serializer = FoodExtraSerializer(instance.food_extras.all(), many=True)
        return ResponseWrapper(data=serializer.data)

    def food_option_by_food(self, request, *args, **kwargs):
        instance = self.get_object()

        serializer = FoodOptionSerializer(
            instance.food_options.all(), many=True)
        return ResponseWrapper(data=serializer.data)

    def update(self, request, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data, partial=True)
        if serializer.is_valid():
            qs = serializer.update(instance=self.get_object(
            ), validated_data=serializer.validated_data)
            serializer = FoodDetailSerializer(instance=qs)
            return ResponseWrapper(data=serializer.data)
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)


class FoodByRestaurantViewSet(CustomViewSet):
    serializer_class = FoodsByCategorySerializer

    # queryset = Food.objects.all()

    # permission_classes = [permissions.IsAuthenticated]

    queryset = Food.objects.all().order_by('-id')
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

    def list(self, request, restaurant, *args, **kwargs):
        qs = self.queryset.filter(
            restaurant=restaurant).prefetch_related('food_options', 'food_extras')
        # qs = qs.filter(is_top = True)
        serializer = FoodDetailSerializer(instance=qs, many=True)
        return ResponseWrapper(data=serializer.data, msg='success')

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

        # food_price = FoodOption.objects.all().values_list('food__category__name',
        #                                                   'food__name').annotate(Min('price')).order_by('price')[0:].prefetch_related('foods')
        # new_price = Food.objects.filter().annotate(Min('food_options__price')).order_by(
        #     'food_options__price')[0:].prefetch_related('food_options')

        # print(food_price)
        # print(new_price)

        serializer = FoodsByCategorySerializer(instance=qs, many=True)
        return ResponseWrapper(data=serializer.data, msg='success')


"""
class FoodOrderViewSet(CustomViewSet):
    serializer_class = TableOrderDetailseSrializer

    queryset = FoodOrder.objects.all()
    lookup_field = 'table'
    http_method_names = ['get']
    def order_list(self, request, table, *args, **kwargs):
        qs = self.queryset.filter(
            table=table).prefetch_related('ordered_items')
        # qs = qs.filter(is_top = True)
        serializer = OrderedItemSrializer(instance=qs, many=True)
        return ResponseWrapper(data=serializer.data, msg='success')

"""
