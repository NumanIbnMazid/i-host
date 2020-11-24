import decimal
import json
from . import permissions as custom_permissions

from account_management import serializers
from account_management.models import HotelStaffInformation, UserAccount, CustomerInfo
from account_management.serializers import (ListOfIdSerializer,
                                            StaffInfoSerializer)
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count, Min, Q, query_utils
from django.db.models.aggregates import Sum
from django.http import request
from django.utils import timezone
from drf_yasg2.utils import get_serializer_class, swagger_auto_schema
from rest_framework import permissions, status, viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.serializers import Serializer
from utils.custom_viewset import CustomViewSet
from utils.response_wrapper import ResponseWrapper

from restaurant.models import (Food, FoodCategory, FoodExtra, FoodExtraType,
                               FoodOption, FoodOptionType, FoodOrder, Invoice,
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
                          FoodWithPriceSerializer, InvoiceSerializer,
                          OrderedItemSerializer, OrderedItemUserPostSerializer,
                          PaymentSerializer, ReportingDateRangeGraphSerializer,
                          RestaurantContactPerson, RestaurantSerializer,
                          RestaurantUpdateSerialier, StaffIdListSerializer,
                          StaffTableSerializer, TableSerializer,
                          TableStaffSerializer,
                          TopRecommendedFoodListSerializer)
from rest_framework_tracking.mixins import LoggingMixin


class RestaurantViewSet(LoggingMixin, CustomViewSet):
    queryset = Restaurant.objects.all()
    lookup_field = 'pk'
    logging_methods = ['GET', 'POST', 'PATCH', 'DELETE']
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
        if self.action in ['update', 'restaurant_under_owner', 'user_order_history']:
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
            status__in=['5_PAID', '6_CANCELLED']).order_by('table_id')
        ordered_table_set = set(qs.values_list('table_id', flat=True))
        table_qs = Table.objects.filter(
            restaurant=restaurant_id).exclude(pk__in=ordered_table_set).order_by('id')
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

    def today_sell(self, request, pk, *args, **kwargs):
        today_date = timezone.now().date()
        qs = Invoice.objects.filter(
            created_at=today_date, payment_status='1_PAID')
        grand_total_list = qs.values_list('grand_total', flat=True)
        total = sum(grand_total_list)
        return ResponseWrapper(data={'total_sell': total}, msg="success")



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

class FoodCategoryViewSet(LoggingMixin, CustomViewSet):

    serializer_class = FoodCategorySerializer
    # permission_classes = [permissions.IsAuthenticated]
    queryset = FoodCategory.objects.all()
    lookup_field = 'pk'
    logging_methods = ['GET', 'POST', 'PATCH', 'DELETE']


class FoodOptionTypeViewSet(LoggingMixin,CustomViewSet):
    serializer_class = FoodOptionTypeSerializer
    # permission_classes = [permissions.IsAuthenticated]
    queryset = FoodOptionType.objects.all()
    lookup_field = 'pk'
    logging_methods = ['GET', 'POST', 'PATCH', 'DELETE']

    def list(self, request):
        qs = self.get_queryset().exclude(name='single_type')
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(instance=qs, many=True)
        # serializer = self.serializer_class(instance=qs, many=True)
        # serializer.is_valid()
        return ResponseWrapper(data=serializer.data, msg='success')


class FoodOrderedViewSet(LoggingMixin,CustomViewSet):
    serializer_class = FoodOrderSerializer
    queryset = FoodOrder.objects.all()
    lookup_field = 'pk'
    logging_methods = ['GET', 'POST', 'PATCH', 'DELETE']
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    # def ordered_item_list(self, request, ordered_id, *args, **kwargs):
    #     qs = FoodOrder.objects.filter(pk=ordered_id)
    #     # qs =self.queryset.filter(pk=ordered_id).prefetch_realted('ordered_items')
    #     serializer = self.get_serializer(instance=qs, many=True)
    #     return ResponseWrapper(data=serializer.data, msg="success")


class FoodExtraTypeViewSet(LoggingMixin,CustomViewSet):
    serializer_class = FoodExtraTypeSerializer
    # permission_classes = [permissions.IsAuthenticated]
    queryset = FoodExtraType.objects.all()
    lookup_field = 'pk'
    logging_methods = ['GET', 'POST', 'PATCH', 'DELETE']


class FoodExtraViewSet(LoggingMixin,CustomViewSet):

    # permission_classes = [permissions.IsAuthenticated]
    queryset = FoodExtra.objects.all()
    lookup_field = 'pk'
    logging_methods = ['GET', 'POST', 'PATCH', 'DELETE']

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update':
            self.serializer_class = FoodExtraPostPatchSerializer
        else:
            self.serializer_class = FoodExtraSerializer

        return self.serializer_class

    # http_method_names = ['post', 'patch', 'get']
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


class FoodOptionViewSet(LoggingMixin,CustomViewSet):

    def get_serializer_class(self):
        if self.action in ['create', 'update']:
            self.serializer_class = FoodOptionBaseSerializer
        else:
            self.serializer_class = FoodOptionSerializer
        return self.serializer_class

    # permission_classes = [permissions.IsAuthenticated]

    queryset = FoodOption.objects.all()
    lookup_field = 'pk'
    logging_methods = ['GET', 'POST', 'PATCH', 'DELETE']

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


class TableViewSet(LoggingMixin,CustomViewSet):
    serializer_class = TableSerializer

    # permission_classes = [permissions.IsAuthenticated]
    queryset = Table.objects.all()
    lookup_field = 'pk'
    logging_methods = ['GET', 'POST', 'PATCH', 'DELETE']
    # http_method_names = ['get', 'post', 'patch']

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
        # qs =self.queryset.filter(pk=ordered_id).prefetch_realted('ordered_items')

        serializer = FoodOrderByTableSerializer(instance=qs, many=True)
        #serializer = self.get_serializer(instance=qs, many=True)
        return ResponseWrapper(data=serializer.data, msg="success")

    def destroy(self, request, **kwargs):
        qs = self.queryset.filter(**kwargs).first()
        if qs:
            if qs.food_orders.count() == qs.food_orders.filter(status__in=['5_PAID', '6_CANCELLED']).count():
                qs.delete()
                return ResponseWrapper(status=200, msg='deleted')
            else:
                return ResponseWrapper(error_code=status.HTTP_406_NOT_ACCEPTABLE, error_msg=['order is running'])

        else:
            return ResponseWrapper(error_msg="table not found", error_code=400)


class FoodOrderViewSet(LoggingMixin,CustomViewSet):

    # permission_classes = [permissions.IsAuthenticated]
    queryset = FoodOrder.objects.all()
    lookup_field = 'pk'
    logging_methods = ['GET', 'POST', 'PATCH', 'DELETE']

    def get_serializer_class(self):
        if self.action in ['create_order', "create_take_away_order"]:
            self.serializer_class = FoodOrderUserPostSerializer
        elif self.action in ['add_items']:
            self.serializer_class = OrderedItemUserPostSerializer
        elif self.action in ['cancel_order']:
            self.serializer_class = FoodOrderCancelSerializer
        elif self.action in ['placed_status']:
            self.serializer_class = PaymentSerializer
        elif self.action in ['confirm_status', 'cancel_items']:
            self.serializer_class = FoodOrderConfirmSerializer
        elif self.action in ['in_table_status']:
            self.serializer_class = FoodOrderConfirmSerializer
        elif self.action in ['payment', 'create_invoice']:
            self.serializer_class = PaymentSerializer
        else:
            self.serializer_class = FoodOrderUserPostSerializer

        return self.serializer_class

    def get_permissions(self):
        permission_classes = []
        if self.action in ["create_take_away_order"]:
            permission_classes = [permissions.IsAuthenticated]
        # elif self.action == "retrieve" or self.action == "update":
        #     permission_classes = [permissions.AllowAny]
        # else:
        #     permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]




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

    def create_take_away_order(self, request):
        serializer = self.get_serializer(data=request.data, partial=True)
        if serializer.is_valid():
            qs = serializer.save()
            serializer = self.serializer_class(instance=qs)
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
                'order_id')).exclude(status='5_PAID').first()
            if order_qs:
                order_qs.status = '6_CANCELLED'
                order_qs.save()
                order_qs.ordered_items.update(status="4_CANCELLED")
                table_qs = order_qs.table
                if table_qs:
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

    def cancel_items(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            order_qs = FoodOrder.objects.filter(pk=request.data.get(
                'order_id')).exclude(status=['0_ORDER_INITIALIZED', '5_PAID', '6_CANCELLED']).first()
            if not order_qs:
                return ResponseWrapper(error_msg=['Order is invalid'], error_code=400)

            all_items_qs = OrderedItem.objects.filter(
                food_order=order_qs).exclude(status__in=["0_ORDER_INITIALIZED", "4_CANCELLED"])
            if all_items_qs:
                all_items_qs.filter(pk__in=request.data.get(
                    'food_items')).update(status='4_CANCELLED')

            #order_qs.status = '3_IN_TABLE'
            # order_qs.save()
            serializer = FoodOrderByTableSerializer(instance=order_qs)

            return ResponseWrapper(data=serializer.data, msg='Served')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def placed_status(self, request,  *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            order_qs = FoodOrder.objects.filter(pk=request.data.get("order_id")).exclude(
                status__in=['5_PAID', '6_CANCELLED']).first()
            if not order_qs:
                return ResponseWrapper(error_msg=['Order is invalid'], error_code=400)

            order_item_counter = OrderedItem.objects.filter(
                food_order=order_qs.pk, status='0_ORDER_INITIALIZED').count()

            if order_item_counter == 0:
                return ResponseWrapper(
                    error_msg=["No order item"],
                    error_code=400)
            else:
                all_items_qs = OrderedItem.objects.filter(
                    food_order=order_qs.pk, status__in=["0_ORDER_INITIALIZED"])
                all_items_qs.update(status='1_ORDER_PLACED')

                if order_qs.status in ['0_ORDER_INITIALIZED']:
                    order_qs.status = '1_ORDER_PLACED'
                    order_qs.save()
                serializer = FoodOrderByTableSerializer(instance=order_qs)

                return ResponseWrapper(data=serializer.data, msg='Placed')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def confirm_status(self, request,  *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

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

        # order_qs.status = '2_ORDER_CONFIRMED'
        # order_qs.save()
        # serializer = FoodOrderByTableSerializer(instance=order_qs)
        if order_qs.status in ["0_ORDER_INITIALIZED", "1_ORDER_PLACED"]:
            order_qs.status = '2_ORDER_CONFIRMED'
            order_qs.save()

        serializer = FoodOrderByTableSerializer(instance=order_qs)

        return ResponseWrapper(data=serializer.data, msg='Confirmed')


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
                food_order=order_qs, status__in=["2_ORDER_CONFIRMED"])
            if all_items_qs:
                all_items_qs.filter(pk__in=request.data.get(
                    'food_items')).update(status='3_IN_TABLE')

            if order_qs.status in ["2_ORDER_CONFIRMED", "1_ORDER_PLACED", "0_ORDER_INITIALIZED"]:
                order_qs.status = '3_IN_TABLE'
                order_qs.save()
            serializer = FoodOrderByTableSerializer(instance=order_qs)

            return ResponseWrapper(data=serializer.data, msg='Served')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def create_invoice(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            """
            making sure that food order is in "3_IN_TABLE", "4_CREATE_INVOICE", "5_PAID" state
            because in other state there is no need to generate invoice because food state is required in other state
            and merging will disrupt the flow.
            """
            order_qs = FoodOrder.objects.filter(pk=request.data.get("order_id"),
                                                status__in=["3_IN_TABLE", "4_CREATE_INVOICE", "5_PAID"]).first()
            if not order_qs:
                return ResponseWrapper(error_msg=['please ask waiter to update to in table status or ask them to create invoice for you'], error_code=400)

            remaining_item_counter = OrderedItem.objects.filter(
                food_order=order_qs.pk).exclude(status__in=["3_IN_TABLE", '4_CANCELLED']).count()

            if remaining_item_counter > 0:
                return ResponseWrapper(error_msg=['Order is running. Please make sure all the order is either in table or is cancelled'], error_code=400)

            else:
                order_qs.status = '4_CREATE_INVOICE'
                order_qs.save()
                invoice_qs = self.invoice_generator(
                    order_qs, payment_status="0_UNPAID")

                serializer = InvoiceSerializer(instance=invoice_qs)
            return ResponseWrapper(data=serializer.data.get('order_info'), msg='Invoice Created')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def invoice_generator(self, order_qs, payment_status):
        # adjust cart for unique items
        self.adjust_cart_for_unique_items(order_qs)

        serializer = FoodOrderByTableSerializer(instance=order_qs)
        grand_total = serializer.data.get(
            'price', {}).get('grand_total_price')

        if order_qs.invoices.first():
            invoice_qs = order_qs.invoices.first()
            invoice_qs.order_info = json.loads(
                json.dumps(serializer.data, cls=DjangoJSONEncoder))
            invoice_qs.grand_total = grand_total
            invoice_qs.payment_status = payment_status
            invoice_qs.save()
        else:
            invoice_qs = Invoice.objects.create(
                restaurant_id=serializer.data.get(
                    'restaurant_info', {}).get('id'),
                order=order_qs,
                order_info=json.loads(json.dumps(serializer.data, cls=DjangoJSONEncoder)), grand_total=grand_total, payment_status=payment_status)
        return invoice_qs

    def adjust_cart_for_unique_items(self, order_qs):
        ordered_items_qs = order_qs.ordered_items.all()
        food_option_extra_tuple_list = ordered_items_qs.values_list(
            'food_option', 'food_extra')

        food_option_list = ordered_items_qs.values_list(
            'food_option', flat=True).distinct()
        for food_option in food_option_list:
            ordered_items_by_food_options_qs = ordered_items_qs.filter(
                food_option=food_option)
            if ordered_items_by_food_options_qs.count() > 1:
                temp_order_list = []
                temp_extra_list = []

                for order_items_qs in ordered_items_by_food_options_qs:
                    extras = list(
                        order_items_qs.food_extra.values_list('pk', flat=True))
                    if extras in temp_extra_list:
                        first_order_qs = temp_order_list[temp_extra_list.index(
                            extras)]
                        first_order_qs.quantity += order_items_qs.quantity
                        first_order_qs.save()
                        order_items_qs.delete()

                    else:
                        temp_extra_list.append(extras)
                        temp_order_list.append(order_items_qs)

    def payment(self, request,  *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            order_qs = FoodOrder.objects.filter(pk=request.data.get("order_id"),
                                                status__in=["4_CREATE_INVOICE"]).first()
            if not order_qs:
                return ResponseWrapper(error_msg=['please create invoice before payment'], error_code=400)

            remaining_item_counter = OrderedItem.objects.filter(
                food_order=order_qs.pk).exclude(status__in=["3_IN_TABLE", '4_CANCELLED']).count()

            if remaining_item_counter > 0:
                return ResponseWrapper(error_msg=['Order is running'], error_code=400)

            else:
                order_qs.status = '5_PAID'
                order_qs.save()
                table_qs = order_qs.table
                if table_qs:
                    table_qs.is_occupied = False
                    table_qs.save()

                invoice_qs = self.invoice_generator(
                    order_qs, payment_status='1_PAID')

                serializer = InvoiceSerializer(instance=invoice_qs)
            return ResponseWrapper(data=serializer.data.get('order_info'), msg='Paid')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)


class OrderedItemViewSet(LoggingMixin,CustomViewSet):
    queryset = OrderedItem.objects.all()
    lookup_field = 'pk'
    logging_methods = ['GET', 'POST', 'PATCH', 'DELETE']

    def get_permissions(self):
        if self.action in ['create']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action in ['create', 'update']:
            self.serializer_class = OrderedItemUserPostSerializer

        else:
            self.serializer_class = OrderedItemSerializer

        return self.serializer_class

    def create(self, request):
        serializer = self.get_serializer(data=request.data, many=True)

        if serializer.is_valid():
            is_invalid_order = True
            if request.data:
                food_order = request.data[0].get('food_order')
                food_order_qs = FoodOrder.objects.filter(pk=food_order)
                restaurant_id = food_order_qs.first().table.restaurant_id

                if HotelStaffInformation.objects.filter(user=request.user.pk, restaurant_id=restaurant_id, is_manager=True):
                    food_order_qs = food_order_qs.first()
                else:
                    food_order_qs = food_order_qs.exclude(
                        status__in=['5_PAID', '6_CANCELLED']).first()
                if food_order_qs:
                    is_invalid_order = False
            if is_invalid_order:
                return ResponseWrapper(error_code=400, error_msg=['order is invalid'])

            qs = serializer.save()

            restaurant_id = food_order_qs.table.restaurant_id

            if HotelStaffInformation.objects.filter(user=request.user.pk, restaurant_id=restaurant_id, is_manager=True):
                order_pk_list = list()
                for item in qs:
                    order_pk_list.append(item.pk)
                qs = OrderedItem.objects.filter(pk__in=order_pk_list)
                qs.update(status='2_ORDER_CONFIRMED')

            # order_order_qs= FoodOrder.objects.filter(status = '0_ORDER_INITIALIZED',pk=request.data.get('id'))
            # if order_order_qs:
            #     order_order_qs.update(status='0_ORDER_INITIALIZED')

            serializer = OrderedItemSerializer(instance=qs, many=True)
            return ResponseWrapper(data=serializer.data, msg='created')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)


class FoodViewSet(LoggingMixin,CustomViewSet):
    serializer_class = FoodWithPriceSerializer

    def get_serializer_class(self):
        if self.action == 'retrieve':
            self.serializer_class = FoodDetailSerializer

        return self.serializer_class
    # permission_classes = [permissions.IsAuthenticated]

    queryset = Food.objects.all()
    lookup_field = 'pk'
    logging_methods = ['GET', 'POST', 'PATCH', 'DELETE']
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


class FoodByRestaurantViewSet(LoggingMixin,CustomViewSet):
    serializer_class = FoodsByCategorySerializer

    # queryset = Food.objects.all()

    # permission_classes = [permissions.IsAuthenticated]

    queryset = Food.objects.all().order_by('-id')
    lookup_field = 'restaurant'
    logging_methods = ['GET', 'POST', 'PATCH', 'DELETE']
    http_method_names = ['get']

    def top_foods(self, request, restaurant, *args, **kwargs):
        qs = self.queryset.filter(restaurant=restaurant, is_top=True)
        # qs = qs.filter(is_top = True)
        serializer = FoodDetailSerializer(instance=qs, many=True)
        return ResponseWrapper(data=serializer.data, msg='success')

    def recommended_foods(self, request, restaurant, *args, **kwargs):
        qs = self.queryset.filter(restaurant=restaurant, is_recommended=True)
        # qs = qs.filter(is_top = True)
        serializer = FoodDetailSerializer(instance=qs, many=True)
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

    # @swagger_auto_schema(request_body=TopRecommendedFoodListSerializer)
    def mark_as_top_or_recommended(self, request, *args, **kwargs):
        serializer = TopRecommendedFoodListSerializer(
            data=request.data, partial=True)
        if not serializer.is_valid():
            return ResponseWrapper(msg="data is not valid")
        else:
            temp_dict = request.data.pop('food_id')
            qs = Food.objects.filter(pk__in=request.data.get('food_id'))
            qs.update(**temp_dict)
            return ResponseWrapper(msg='updated', status=200)


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


class ReportingViewset(LoggingMixin, viewsets.ViewSet):
    logging_methods = ['GET', 'POST', 'PATCH', 'DELETE']
    def get_permissions(self):
        permission_classes = []
        if self.action == "create":
            permission_classes = [permissions.IsAuthenticated]
        # elif self.action == "retrieve" or self.action == "update":
        #     permission_classes = [permissions.AllowAny]
        # else:
        #     permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    @swagger_auto_schema(
        request_body=ReportingDateRangeGraphSerializer
    )
    def create(self, request):
        from_date = request.data.get('from_date')
        to_date = request.data.get('to_date')
        # by default show all if no order status given
        order_status = request.data.get('order_status', '')
        user_id = request.user.pk
        # serializer = ReportingDateRangeGraphSerializer(request.data)
        order_date_range_qs = self.get_queryset(
            from_date, to_date, order_status, user_id)

        response = {'total_ordered_item': 22,
                    'food_quantity_sold': {'burger': 12}}
        return ResponseWrapper(data=response)

    def get_queryset(self, from_date, to_date, order_status, user_id):
        restaurant_id = UserAccount.objects.get(
            pk=user_id).hotel_staff.restaurant.pk
        if not (from_date and to_date):
            # by default show all if no order status given
            order_date_range_qs = FoodOrder.objects.filter(table__restaurant__id=restaurant_id,
                                                           status__icontains=order_status, created_at__lte=timezone.now().date())
        elif not from_date:
            order_date_range_qs = FoodOrder.objects.filter(table__restaurant__id=restaurant_id,
                                                           status__icontains=order_status, created_at__lte=to_date)
        elif not to_date:
            order_date_range_qs = FoodOrder.objects.filter(table__restaurant__id=restaurant_id,

                                                           status__icontains=order_status, created_at__gte=from_date)
        else:
            order_date_range_qs = FoodOrder.objects.filter(table__restaurant__id=restaurant_id,
                                                           status__icontains=order_status, created_at__gte=from_date, created_at__lte=to_date)
        return order_date_range_qs


class InvoiceViewSet(LoggingMixin, CustomViewSet):
    queryset = Invoice.objects.all()
    lookup_field = 'pk'
    logging_methods = ['GET', 'POST', 'PATCH', 'DELETE']

    def invoice_history(self, request, restaurant, *args, **kwargs):
        qs = Invoice.objects.filter(restaurant=restaurant)
        serializer = InvoiceSerializer(instance=qs, many=True)
        return ResponseWrapper(data=serializer.data)

    def paid_cancel_invoice_history(self, request, restaurant, *args, **kwargs):
        qs = Invoice.objects.filter(restaurant= restaurant, order__status__in=['5_PAID','6_CANCELLED'])
        serializer = InvoiceSerializer(instance=qs, many=True)
        return ResponseWrapper(data=serializer.data)
