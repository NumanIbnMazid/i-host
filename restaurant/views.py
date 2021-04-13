from restaurant.libs.generate_order_no import generate_order_no
from asgiref.sync import async_to_sync, sync_to_async
import copy
import decimal
from decimal import getcontext, Decimal, ROUND_HALF_UP
import json
from datetime import date, datetime, timedelta
import base64
from xhtml2pdf import pisa
from django.template.loader import render_to_string
from django.template.loader import get_template
from django.template import Context
from weasyprint import CSS, HTML
from django.http import HttpResponse
import tempfile
from rest_framework.views import APIView
from account_management import models, serializers
from account_management.models import (CustomerInfo, FcmNotificationStaff,
                                       HotelStaffInformation, StaffFcmDevice,
                                       UserAccount, FcmNotificationCustomer, CustomerFcmDevice)
from account_management.serializers import (ListOfIdSerializer,
                                            StaffInfoGetSerializer,
                                            StaffInfoSerializer, CustomerNotificationSerializer)
from dateutil.relativedelta import relativedelta
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count, Min, Q, query_utils
from django.db.models.aggregates import Sum
from django.http import request
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg2 import openapi
from drf_yasg2.utils import swagger_auto_schema
from rest_framework import filters, permissions, status, viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.serializers import Serializer
from rest_framework_tracking.mixins import LoggingMixin
from utils.custom_viewset import CustomViewSet
from utils.fcm import send_fcm_push_notification_appointment
from utils.pagination import CustomLimitPagination, NoLimitPagination
from utils.print_node import print_node
from utils.response_wrapper import ResponseWrapper
from actstream import action
from actstream.models import Action

# from restaurant.models import (Discount, Food, FoodCategory, FoodExtra,
#                                FoodExtraType, FoodOption, FoodOptionType,
#                                FoodOrder, FoodOrderLog, Invoice, OrderedItem,
#                                PaymentType, PopUp, Restaurant,
#                                RestaurantMessages, Review, Slider,
#                                Subscription, Table, VersionUpdate, PrintNode, TakeAwayOrder,
#                                ParentCompanyPromotion, CashLog,WithdrawCash,  )
from restaurant.models import *

from . import permissions as custom_permissions
from .serializers import (
    CollectPaymentSerializer, DiscountByFoodSerializer,
    DiscountSerializer, FcmNotificationStaffSerializer,
    FoodCategorySerializer,
    FoodDetailsByDiscountSerializer,
    FoodDetailSerializer, FoodExtraPostPatchSerializer,
    FoodExtraSerializer, FoodExtraTypeDetailSerializer,
    FoodExtraTypeSerializer, FoodOptionBaseSerializer,
    FoodOptionSerializer, FoodOptionTypeSerializer,
    FoodOrderByTableSerializer,
    FoodOrderCancelSerializer,
    FoodOrderConfirmSerializer, FoodOrderSerializer,
    FoodOrderUserPostSerializer, FoodPostSerializer,
    FoodsByCategorySerializer, FoodSerializer,
    FoodWithPriceSerializer, FreeTableSerializer,
    HotelStaffInformationSerializer,
    InvoiceGetSerializer, InvoiceSerializer,
    OnlyFoodOrderIdSerializer,
    OrderedItemDashboardPostSerializer,
    OrderedItemGetDetailsSerializer,
    OrderedItemSerializer, OrderedItemTemplateSerializer,
    OrderedItemUserPostSerializer, PaymentSerializer,
    PaymentTypeSerializer, PopUpSerializer,
    ReOrderedItemSerializer, ReorderSerializer,
    ReportByDateRangeSerializer,
    ReportDateRangeSerializer,
    ReportingDateRangeGraphSerializer,
    RestaurantContactPerson,
    RestaurantMessagesSerializer,
    RestaurantPostSerialier, RestaurantSerializer,
    RestaurantUpdateSerialier, ReviewSerializer,
    SliderSerializer, StaffFcmSerializer,
    StaffIdListSerializer, StaffTableSerializer,
    SubscriptionSerializer, TableSerializer,
    TableStaffSerializer,
    TakeAwayFoodOrderPostSerializer,
    TopRecommendedFoodListSerializer, ReOrderedItemSerializer, SliderSerializer,
    SubscriptionSerializer, ReviewSerializer, RestaurantMessagesSerializer,

    SubscriptionSerializer, ReviewSerializer, RestaurantMessagesSerializer, FoodPostSerializer,
    ReportByDateRangeSerializer, VersionUpdateSerializer, HotelStaffInformationSerializer,
    ServedOrderSerializer,
    TopRecommendedFoodListSerializer,
    VersionUpdateSerializer, CustomerOrderDetailsSerializer,
    FcmNotificationListSerializer, DiscountPopUpSerializer, DiscountSliderSerializer,
    FoodOrderStatusSerializer, PrintNodeSerializer, TakeAwayOrderSerializer,
    ParentCompanyPromotionSerializer, RestaurantParentCompanyPromotionSerializer,
    FoodOrderPromoCodeSerializer, DiscountPostSerializer, PaymentWithAmaountSerializer,
    CashLogSerializer, RestaurantOpeningSerializer, RestaurantClosingSerializer,
    WithdrawCashSerializer, ForceDiscountSerializer, PromoCodePromotionSerializer,
    PromoCodePromotionDetailsSerializer, TakewayOrderTypeSerializer
)
from .signals import order_done_signal, kitchen_items_print_signal


class FoodOrderCore:
    def invoice_generator(self, order_qs, payment_status, *args, **kwargs):
        # adjust cart for unique items
        self.adjust_cart_for_unique_items(order_qs)

        #is_apps = request.path.__contains__('/apps/')
        serializer = FoodOrderByTableSerializer(instance=order_qs)
        grand_total = serializer.data.get(
            'price', {}).get('grand_total_price')
        payable_amount = serializer.data.get(
            'price', {}).get('payable_amount')

        if order_qs.invoices.first():
            invoice_qs = order_qs.invoices.first()
            invoice_qs.order_info = json.loads(
                json.dumps(serializer.data, cls=DjangoJSONEncoder))
            invoice_qs.grand_total = grand_total
            invoice_qs.payment_status = payment_status
            invoice_qs.payable_amount = payable_amount
            invoice_qs.save()
        else:
            invoice_qs = Invoice.objects.create(
                restaurant_id=serializer.data.get(
                    'restaurant_info', {}).get('id'),
                order=order_qs,
                order_info=json.loads(json.dumps(
                    serializer.data, cls=DjangoJSONEncoder)),
                grand_total=grand_total,
                payable_amount=payable_amount,
                payment_status=payment_status
            )
        return invoice_qs

    def adjust_cart_for_unique_items(self, order_qs, *args, **kwargs):
        ordered_items_qs = order_qs.ordered_items.all().exclude(status='4_CANCELLED')
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


class RestaurantViewSet(LoggingMixin, CustomViewSet):
    queryset = Restaurant.objects.all()
    lookup_field = 'pk'
    logging_methods = ['GET', 'POST', 'PATCH', 'DELETE']
    # serializer_class = RestaurantContactPerson

    def get_serializer_class(self):
        if self.action == 'create':
            self.serializer_class = RestaurantPostSerialier
        elif self.action == 'update':
            # self.serializer_class = RestaurantUpdateSerialier
            self.serializer_class = RestaurantPostSerialier

        else:
            self.serializer_class = RestaurantSerializer

        return self.serializer_class

    def get_permissions(self):
        permission_classes = []
        if self.action in ["create", 'delete_restaurant', 'list']:
            permission_classes = [permissions.IsAdminUser]
        elif self.action in ['update', 'restaurant_under_owner', 'user_order_history']:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['today_sell']:
            permission_classes = [
                custom_permissions.IsRestaurantStaff]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            # qs = serializer
            serializer = RestaurantSerializer(instance=serializer.save())
            return ResponseWrapper(data=serializer.data, msg='created')
        else:
            return ResponseWrapper(error_code=400, error_msg=serializer.errors, msg='failed to create restaurant')

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
        if self.request.user.is_staff:
            serializer = RestaurantPostSerialier(
                data=request.data, partial=True)
        else:
            serializer = RestaurantUpdateSerialier(
                data=request.data, partial=True)

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
        is_apps = request.path.__contains__('/apps/')
        serializer = FoodOrderByTableSerializer(instance=qs, many=True, context={
                                                'is_apps': is_apps, 'request': request})

        return ResponseWrapper(data=serializer.data+empty_table_data, msg="success")

    def delete_restaurant(self, request, pk, *args, **kwargs):
        self.check_object_permissions(request, obj=pk)
        qs = self.queryset.filter(pk=pk).first()
        if qs:
            qs.deleted_at = timezone.now()
            qs.save()
            qs.tables.update(deleted_at=timezone.now())
            # table_qs.deleted_at=timezone.now()
            # table_qs.save()
            return ResponseWrapper(status=200, msg='deleted')
        else:
            return ResponseWrapper(error_msg="failed to delete", error_code=400)

    def today_sell(self, request, pk, *args, **kwargs):
        self.check_object_permissions(request, obj=pk)
        today_date = timezone.now().date()
        qs = Invoice.objects.filter(
            created_at__icontains=today_date, payment_status='1_PAID', restaurant_id=pk)
        order_qs = FoodOrder.objects.filter(
            created_at__icontains=today_date, status='5_PAID', restaurant_id=pk).count()

        payable_amount_list = qs.values_list('payable_amount', flat=True)
        total = sum(payable_amount_list)

        return ResponseWrapper(data={'total_sell': round(total, 2), 'total_order': order_qs}, msg="success")

    def remaining_subscription_feathers(self, request, restaurant_id, *args, **kwargs):
        restaurant_qs = Restaurant.objects.filter(id=restaurant_id).first()
        restaurant_id = restaurant_qs.pk
        table_count = Table.objects.filter(restaurant_id=restaurant_id).count()
        waiter_staff_qs = HotelStaffInformation.objects.filter(
            restaurant_id=restaurant_id)
        waiter_count = waiter_staff_qs.filter(is_waiter=True).count()
        manager_staff_qs = HotelStaffInformation.objects.filter(
            restaurant_id=restaurant_id)
        manager_count = manager_staff_qs.filter(is_manager=True).count()
        staff_qs = Restaurant.objects.filter(
            id=restaurant_id).select_related('subscription').first()
        waiter_limit_count = staff_qs.subscription.waiter_limit
        manager_limit_count = staff_qs.subscription.manager_limit
        table_limit_count = staff_qs.subscription.table_limit
        exist_table = table_limit_count - table_count
        exist_waiter = waiter_limit_count - waiter_count
        exist_manager = manager_limit_count - manager_count

        return ResponseWrapper(data={'waiter': exist_waiter,
                                     'manager': exist_manager,
                                     'table': exist_table, })


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
    # logging_methods = ['GET', 'POST', 'PATCH', 'DELETE']

    def get_permissions(self):
        permission_classes = []
        if self.action in ['create', 'destroy', 'patch']:
            permission_classes = [
                permissions.IsAdminUser]
        # else:
        #     permission_classes = permissions.IsAuthenticated
        return [permission() for permission in permission_classes]

    def category_details(self, request, pk, *args, **kwargs):
        qs = FoodCategory.objects.filter(id=pk).last()
        serializer = self.serializer_class(instance=qs)
        return ResponseWrapper(data=serializer.data, msg='success')


class FoodOptionTypeViewSet(LoggingMixin, CustomViewSet):
    serializer_class = FoodOptionTypeSerializer
    # permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        permission_classes = []
        if self.action in ['create', 'destroy', 'patch']:
            permission_classes = [
                permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    queryset = FoodOptionType.objects.all()
    lookup_field = 'pk'
    logging_methods = ['GET', 'POST', 'PATCH', 'DELETE']

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset().exclude(name='single_type')
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(instance=qs, many=True)
        # serializer = self.serializer_class(instance=qs, many=True)
        # serializer.is_valid()
        return ResponseWrapper(data=serializer.data, msg='success')

    def food_option_type_detail(self, request, pk, *args, **kwargs):
        qs = FoodOptionType.objects.filter(id=pk).first()
        serializer = self.serializer_class(instance=qs)
        return ResponseWrapper(data=serializer.data, msg='success')


class FoodOrderedViewSet(LoggingMixin, CustomViewSet):
    serializer_class = FoodOrderSerializer
    queryset = FoodOrder.objects.all()
    lookup_field = 'pk'
    logging_methods = ['GET', 'POST', 'PATCH', 'DELETE']
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        is_apps = request.path.__contains__('/apps/')
        calculate_price_with_initial_item = request.path.__contains__(
            '/apps/customer/ordered_item/')
        serializer = self.get_serializer(
            instance, context={'is_apps': is_apps, 'request': request, "calculate_price_with_initial_item": calculate_price_with_initial_item})
        return ResponseWrapper(serializer.data)

    # def ordered_item_list(self, request, ordered_id, *args, **kwargs):
    #     qs = FoodOrder.objects.filter(pk=ordered_id)
    #     # qs =self.queryset.filter(pk=ordered_id).prefetch_realted('ordered_items')
    #     serializer = self.get_serializer(instance=qs, many=True)
    #     return ResponseWrapper(data=serializer.data, msg="success")


class FoodExtraTypeViewSet(LoggingMixin, CustomViewSet):
    serializer_class = FoodExtraTypeSerializer
    # permission_classes = [permissions.IsAuthenticated]
    queryset = FoodExtraType.objects.all()
    lookup_field = 'pk'
    logging_methods = ['GET', 'POST', 'PATCH', 'DELETE']

    def get_permissions(self):
        permission_classes = []
        if self.action in ['create', 'destroy', 'patch']:
            permission_classes = [
                permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    def food_extra_type_detail(self, request, pk, *args, **kwargs):
        qs = FoodExtraType.objects.get(id=pk)
        serializer = self.serializer_class(instance=qs)
        return ResponseWrapper(data=serializer.data, msg='success')


class FoodExtraViewSet(LoggingMixin, CustomViewSet):

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

    def get_permissions(self):
        permission_classes = []
        if self.action in ['create', 'update', 'destroy']:
            permission_classes = [
                custom_permissions.IsRestaurantManagementOrAdmin]
        # else:
        #     permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

    # http_method_names = ['post', 'patch', 'get']

    def food_extra_details(self, request, pk, *args, **kwargs):
        qs = FoodExtra.objects.filter(pk=pk).last()
        serializer = FoodExtraSerializer(instance=qs)
        return ResponseWrapper(data=serializer.data, msg='success')

    def create(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        food_qs = Food.objects.filter(id=request.data.get('food')).first()
        if not food_qs:
            return ResponseWrapper(error_msg=['Food id is not valid'], error_code=406)
        restaurant_id = food_qs.restaurant_id
        self.check_object_permissions(request, obj=restaurant_id)
        if serializer.is_valid():
            qs = serializer.save()
            serializer = FoodExtraTypeDetailSerializer(instance=qs)
            return ResponseWrapper(data=serializer.data, msg='created')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def update(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data, partial=True)
        food_qs = Food.objects.filter(id=request.data.get('food')).first()
        if not food_qs:
            return ResponseWrapper(error_msg=['Food id is not valid'], error_code=404)
        restaurant_id = food_qs.restaurant_id
        self.check_object_permissions(request, obj=restaurant_id)
        if serializer.is_valid():
            qs = serializer.update(instance=self.get_object(
            ), validated_data=serializer.validated_data)
            serializer = FoodExtraTypeDetailSerializer(instance=qs)
            return ResponseWrapper(data=serializer.data)
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)


class FoodOptionViewSet(LoggingMixin, CustomViewSet):

    def get_serializer_class(self):
        if self.action in ['create', 'update']:
            self.serializer_class = FoodOptionBaseSerializer
        else:
            self.serializer_class = FoodOptionSerializer
        return self.serializer_class

    def get_permissions(self):
        permission_classes = []
        if self.action in ['create', 'update', 'destroy']:
            permission_classes = [
                custom_permissions.IsRestaurantManagementOrAdmin]

        return [permission() for permission in permission_classes]

    # permission_classes = [permissions.IsAuthenticated]

    queryset = FoodOption.objects.all()
    lookup_field = 'pk'
    logging_methods = ['GET', 'POST', 'PATCH', 'DELETE']

    def create(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        food_qs = Food.objects.filter(id=request.data.get('food')).first()
        if not food_qs:
            return ResponseWrapper(error_msg=['Food id is not valid'], error_code=404)
        restaurant_id = food_qs.restaurant_id
        self.check_object_permissions(request, obj=restaurant_id)
        if serializer.is_valid():
            option_type_id = request.data.get('option_type')
            food_id = request.data.get('food')
            default_option_type_qs = FoodOptionType.objects.filter(
                name='single_type').first()
            if default_option_type_qs:
                if default_option_type_qs.pk == option_type_id:
                    food_option_qs = FoodOption.objects.filter(
                        food_id=food_id, option_type_id=option_type_id)
                    if food_option_qs.count() > 1:
                        for temp_qs in food_option_qs[:(food_option_qs.count()-1)]:
                            temp_qs.delete()
                    qs = food_option_qs.last()

                    temp_food_option_qs = FoodOption.objects.filter(
                        food_id=food_id).exclude(option_type__name='single_type')
                    if temp_food_option_qs:
                        temp_food_option_qs.delete()
                    if qs:
                        qs.price = request.data.get('price', qs.price)
                        qs.save()
                        serializer = FoodOptionSerializer(instance=qs)
                        return ResponseWrapper(data=serializer.data, msg='created')

            qs = serializer.save()
            serializer = FoodOptionSerializer(instance=qs)
            return ResponseWrapper(data=serializer.data, msg='created')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def update(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data, partial=True)
        food_qs = Food.objects.filter(id=request.data.get('food')).first()
        if not food_qs:
            return ResponseWrapper(error_msg=['Food id is not valid'], error_code=404)
        restaurant_id = food_qs.restaurant_id
        self.check_object_permissions(request, obj=restaurant_id)
        if serializer.is_valid():
            qs = serializer.update(instance=self.get_object(
            ), validated_data=serializer.validated_data)
            serializer = FoodOptionSerializer(instance=qs)
            return ResponseWrapper(data=serializer.data)
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def food_option_detail(self, request, pk, *args, **kwargs):
        food_option_qs = FoodOption.objects.filter(id=pk).first()
        serializer = FoodOptionSerializer(instance=food_option_qs)
        return ResponseWrapper(data=serializer.data, msg='success')


class TableViewSet(LoggingMixin, CustomViewSet):
    serializer_class = TableSerializer

    # permission_classes = [permissions.IsAuthenticated]
    queryset = Table.objects.all()
    lookup_field = 'pk'
    logging_methods = ['GET', 'POST', 'PATCH', 'DELETE']
    # http_method_names = ['get', 'post', 'patch']

    def get_permissions(self):
        permission_classes = []
        if self.action in ['table_list']:
            permission_classes = [
                custom_permissions.IsRestaurantStaff
            ]
        elif self.action in ['create', 'add_staff']:
            permission_classes = [
                custom_permissions.IsRestaurantManagementOrAdmin
            ]
        elif self.action in ['staff_table_list', 'order_item_list']:
            permission_classes = [
                custom_permissions.IsRestaurantStaff
            ]
        elif self.action in ['remove_staff']:
            permission_classes = [
                custom_permissions.IsRestaurantManagementOrAdmin
            ]
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

    # def get_pagination_class(self):
    #     if self.action in ['table_list']:
    #         # url = self.request.path
    #         # if url.__contains__('/dashboard/'):
    #         return CustomLimitPagination

    # pagination_class = property(get_pagination_class)

    def create(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        restaurant_qs = Restaurant.objects.filter(
            id=request.data.get('restaurant')).first()

        restaurant_id = restaurant_qs.id
        if not restaurant_id:
            return ResponseWrapper(error_msg=['Restaurant is not valid'], error_code=404)
        self.check_object_permissions(request, obj=restaurant_id)

        res_qs = Restaurant.objects.filter(id=request.data.get(
            'restaurant')).select_related('subscription').last()
        table_count = res_qs.tables.count()
        # table_count = Table.objects.filter(restaurant_id=res_qs.id).count()
        table_limit_qs = res_qs.subscription.table_limit
        if not table_count <= table_limit_qs:
            return ResponseWrapper(error_msg=["Your Table Limit is "+str(table_limit_qs)+', Please Update Your Subscription '], error_code=400)
        if serializer.is_valid():
            qs = serializer.save()
            serializer = self.serializer_class(instance=qs)
            return ResponseWrapper(data=serializer.data, msg='created')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def table_list(self, request, restaurant, *args, **kwargs):
        # url = request.path
        # is_dashboard = url.__contains__('/dashboard/')
        restaurant_qs = Restaurant.objects.filter(id=restaurant).first()
        restaurant_id = restaurant_qs.id
        if not restaurant_id:
            return ResponseWrapper(error_msg=['Restaurant is not valid'], error_code=404)
        self.check_object_permissions(request, obj=restaurant_id)
        qs = self.queryset.filter(restaurant=restaurant_id)
        # if is_dashboard:
        #     page_qs = self.paginate_queryset(qs)
        #     serializer = self.get_serializer(
        #         instance=page_qs, many=True, context={'user': request.user})
        #
        #     paginated_data = self.get_paginated_response(serializer.data)
        #
        #     return ResponseWrapper(paginated_data.data)

        # qs = qs.filter(is_top = True)
        serializer = self.get_serializer(
            instance=qs, many=True, context={'user': request.user})

        return ResponseWrapper(data=serializer.data, msg='success')

    # @swagger_auto_schema(request_body=ListOfIdSerializer)
    def add_staff(self, request, table_id, *args, **kwargs):
        qs = self.get_queryset().filter(pk=table_id).first()
        restaurant_id = qs.restaurant_id
        if not restaurant_id:
            return ResponseWrapper(error_msg=['Restaurant is not valid'], error_code=404)
        self.check_object_permissions(request, obj=restaurant_id)

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
        qs = self.get_queryset().filter(staff_assigned=staff_id).order_by('table_no')
        if not qs:
            return ResponseWrapper(error_msg=['Not a Valid Restaurant Staff'], error_code=404)
        restaurant_id = qs.first().restaurant_id
        if not restaurant_id:
            return ResponseWrapper(error_msg=['Restaurant is not valid'], error_code=404)
        self.check_object_permissions(request, obj=restaurant_id)
        # qs = qs.filter(is_top = True)
        serializer = self.get_serializer(instance=qs, many=True)
        return ResponseWrapper(data=serializer.data, msg='successful')
#r
    def remove_staff(self, request, table_id, *args, **kwargs):
        qs = self.get_queryset().filter(pk=table_id).first()
        restaurant_id = qs.restaurant_id
        if not restaurant_id:
            return ResponseWrapper(error_msg=['Restaurant is not valid'], error_code=404)
        self.check_object_permissions(request, obj=restaurant_id)

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

        qs = FoodOrder.objects.filter(table=table_id)
        restaurant_id = qs.first().restaurant_id
        if not restaurant_id:
            return ResponseWrapper(error_msg=['Restaurant is not valid'], error_code=404)
        self.check_object_permissions(request, obj=restaurant_id)

        # qs =self.queryset.filter(pk=ordered_id).prefetch_realted('ordered_items')
        is_apps = request.path.__contains__('/apps/')

        serializer = FoodOrderByTableSerializer(instance=qs, many=True, context={
                                                'is_apps': is_apps, 'request': request})
        # serializer = self.get_serializer(instance=qs, many=True)
        return ResponseWrapper(data=serializer.data, msg="success")

    def apps_running_order_item_list(self, request, table_id, *args, **kwargs):
        qs = FoodOrder.objects.filter(table=table_id).exclude(
            status__in=['5_PAID', '6_CANCELLED', '0_ORDER_INITIALIZED']).last()
        # qs =self.queryset.filter(pk=ordered_id).prefetch_realted('ordered_items')
        is_apps = request.path.__contains__('/apps/')

        serializer = FoodOrderByTableSerializer(instance=qs, many=False, context={
                                                'is_apps': is_apps, 'request': request})
        # serializer = self.get_serializer(instance=qs, many=True)
        return ResponseWrapper(data=serializer.data, msg="success")

    def destroy(self, request, *args, **kwargs):
        qs = self.queryset.filter(**kwargs).first()
        if qs:
            if qs.food_orders.count() == qs.food_orders.filter(status__in=['5_PAID', '6_CANCELLED']).count():
                qs.delete()
                return ResponseWrapper(status=200, msg='deleted')
            else:
                return ResponseWrapper(error_code=status.HTTP_406_NOT_ACCEPTABLE, error_msg=['order is running'])

        else:
            return ResponseWrapper(error_msg="table not found", error_code=400)

    def free_table_list(self, request, restaurant, *args, **kwargs):

        qs = Table.objects.filter(restaurant_id=restaurant, is_occupied=False)
        serializer = FreeTableSerializer(
            instance=qs, many=True)
        return ResponseWrapper(data=serializer.data, msg='success')

    def order_id_by_table(self, request, table_id, *args, **kwargs):
        table_qs = FoodOrder.objects.filter(table_id=table_id).last()
        if not table_qs:
            return ResponseWrapper(msg='Wrong Table ID')
        if not table_qs.table.is_occupied:
            return ResponseWrapper(msg='No Order in table')
        serializer = OnlyFoodOrderIdSerializer(instance=table_qs)
        return ResponseWrapper(data=serializer.data, msg='success')


class FoodOrderViewSet(LoggingMixin, CustomViewSet, FoodOrderCore):

    # permission_classes = [permissions.IsAuthenticated]
    queryset = FoodOrder.objects.all()
    lookup_field = 'pk'
    logging_methods = ['GET', 'POST', 'PATCH', 'DELETE']

    def get_serializer_class(self):
        if self.action in ['create_order']:
            self.serializer_class = FoodOrderUserPostSerializer
        if self.action in ['create_take_away_order']:
            self.serializer_class = TakeAwayFoodOrderPostSerializer
        elif self.action in ['add_items']:
            self.serializer_class = OrderedItemUserPostSerializer
        elif self.action in ['cancel_order', 'apps_cancel_order']:
            self.serializer_class = FoodOrderCancelSerializer
        elif self.action in ['placed_status', 'revert_back_to_in_table']:
            self.serializer_class = PaymentWithAmaountSerializer
        elif self.action in ['confirm_status', 'cancel_items', 'confirm_status_without_cancel']:
            self.serializer_class = FoodOrderConfirmSerializer
        elif self.action in ['in_table_status']:
            self.serializer_class = FoodOrderConfirmSerializer
        elif self.action in ['payment']:
            self.serializer_class = PaymentSerializer
        elif self.action in ['create_invoice_for_dashboard', 'create_invoice']:
            self.serializer_class = PaymentWithAmaountSerializer
        elif self.action in ['retrieve']:
            self.serializer_class = FoodOrderByTableSerializer
        elif self.action in ['food_reorder_by_order_id', 'table_transfer']:
            self.serializer_class = ReorderSerializer
        elif self.action in ['promo_code']:
            self.serializer_class = FoodOrderPromoCodeSerializer
        else:
            self.serializer_class = FoodOrderUserPostSerializer

        return self.serializer_class

    def get_permissions(self):
        permission_classes = []
        if self.action in ['apps_cancel_order', 'create_order', 'order_status', "create_order_apps", 'customer_order_history', 'add_items', 'cancel_order', 'placed_status', 'confirm_status', 'cancel_items', 'in_table_status', 'create_invoice','promo_code']:
            permission_classes = [permissions.IsAuthenticated]
        if self.action in ['create_take_away_order']:
            permission_classes = [
                custom_permissions.IsRestaurantManagementOrAdmin]
        if self.action in ['payment', 'table_transfer', 'confirm_status_without_cancel', 'revert_back_to_in_table', 'create_invoice_for_dashboard']:
            permission_classes = [
                custom_permissions.IsRestaurantStaff
            ]
        # elif self.action == "retrieve" or self.action == "update":
        #     permission_classes = [permissions.AllowAny]
        # else:
        #     permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    # def get_pagination_class(self):
    #     if self.action in ['customer_order_history']:
    #         return CustomLimitPagination
    #
    # pagination_class = property(get_pagination_class)

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

    def promo_code(self, request, order_id, *args, **kwargs):
        # serializer = self.get_serializer(data = request.data)
        today = timezone.datetime.now().date()
        start_date = today - timedelta(days=1)
        food_order_qs = FoodOrder.objects.filter(pk=order_id).last()
        if food_order_qs.discount_given:
            return ResponseWrapper(error_msg=['Force Discount Already Applied'], error_code=400)

        restaurant_id = food_order_qs.restaurant_id
        parent_promo_code = ParentCompanyPromotion.objects.filter(code=request.data.get('applied_promo_code'),restaurant__in = [restaurant_id],
                                                           start_date__lte=start_date, end_date__gte=today).last()
        promo_code = PromoCodePromotion.objects.filter(code = request.data.get('applied_promo_code'),
                                                    restaurant_id = restaurant_id,start_date__lte=start_date, end_date__gte=today).last()
        if not parent_promo_code == None:
            if not parent_promo_code:
                return ResponseWrapper(msg='Promo code not valid', status=200)

        # if not promo_code == None:
        if not promo_code:
            return ResponseWrapper(msg='Promo code not valid', status=200)

        # promo_code = food_order_qs.applied_promo_code
        if parent_promo_code:
            food_order_qs.applied_promo_code = request.data.get('applied_promo_code')
            food_order_qs.save()
        else:
            promo_code_log_qs = PromoCodePromotionLog.objects.filter(customer_id=request.user.pk,
                                                                  promo_code_id = promo_code)
            total_promo_code = promo_code_log_qs.count()
            if promo_code.max_limit <= total_promo_code:
                return ResponseWrapper(msg='Maximum time Promo Code Already Used', status=200)

            amount = food_order_qs.payable_amount

            if not (promo_code.minimum_purchase_amount < amount and promo_code.max_amount > amount):
                return ResponseWrapper(msg='promo code not valid for this order', status=200)

            promo_code_log = PromoCodePromotionLog.objects.create(customer_id = request.user.pk,
                                                                  promo_code_id= promo_code.id
                                                                )
            food_order_qs.applied_promo_code = request.data.get('applied_promo_code')
            food_order_qs.save()

        return ResponseWrapper(msg='Promo Code Applied', status=200)

    def create_order(self, request, *args, **kwargs):
        # serializer_class = self.get_serializer_class()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            table_qs = Table.objects.filter(
                pk=request.data.get('table')).last()

            if not table_qs.is_occupied:
                table_qs.is_occupied = True
                table_qs.save()
                qs = serializer.save()
                qs.restaurant = table_qs.restaurant
                qs.order_no = generate_order_no(
                    restaurant_id=table_qs.restaurant.pk, order_qs=qs)
                qs.save()
                serializer = self.serializer_class(instance=qs)
            else:
                return ResponseWrapper(error_msg=['table already occupied'], error_code=400)
            order_done_signal.send(
                sender=self.__class__.create,
                restaurant_id=table_qs.restaurant_id,
            )
            return ResponseWrapper(data=serializer.data, msg='created')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter("is_waiter", openapi.IN_QUERY,
                          type=openapi.TYPE_BOOLEAN)
    ])
    def create_order_apps(self, request, *args, **kwargs):
        # serializer_class = self.get_serializer_class()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            table_qs = Table.objects.filter(
                pk=request.data.get('table')).last()

            # ____ Customer Running Order Checking______
            is_customer = request.path.__contains__(
                '/apps/customer/order/create_order/')

            if (not is_customer) and table_qs.is_occupied:
                return ResponseWrapper(error_msg=['table already occupied'], error_code=400)

            if is_customer:
                food_order_qs = FoodOrder.objects.filter(customer__user=request.user.pk,
                                                         restaurant_id=table_qs.restaurant_id).exclude(
                    status__in=['5_PAID', '6_CANCELLED']).last()

                if food_order_qs:
                    if table_qs.is_occupied and (table_qs.pk != food_order_qs.table.pk):
                        return ResponseWrapper(error_msg=['table already occupied'], error_code=400)

                    running_order_table_qs = food_order_qs.table
                    running_order_table_qs.is_occupied = False
                    running_order_table_qs.save()
                    food_order_qs.table_id = table_qs.id
                    table_qs.is_occupied = True
                    table_qs.save()
                    food_order_qs.save()
                    serializer = self.serializer_class(instance=food_order_qs)
                    # return ResponseWrapper(data=serializer.data, msg='Success')
                elif table_qs.is_occupied:
                    return ResponseWrapper(error_msg=['table already occupied'], error_code=400)
                else:
                    serializer = self.create_fresh_order(
                        request, serializer, table_qs)

            else:
                serializer = self.create_fresh_order(
                    request, serializer, table_qs)

            order_done_signal.send(
                sender=self.__class__.create,
                restaurant_id=table_qs.restaurant_id,

            )

            return ResponseWrapper(data=serializer.data, msg='created')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def create_fresh_order(self, request, serializer, table_qs):
        table_qs.is_occupied = True
        table_qs.save()
        qs = serializer.save()
        qs.restaurant = table_qs.restaurant
        qs.order_no = generate_order_no(
            restaurant_id=table_qs.restaurant.pk, order_qs=qs
        )
        qs.save()
        if request.query_params.get('is_waiter', 'false') == 'false':
            self.save_customer_info(request, qs)
        serializer = self.serializer_class(instance=qs)
        return serializer

    def save_customer_info(self, request, qs, *args, **kwargs):
        # if request.data.get('table'):
        #     staff_account = qs.table.restaurant.hotel_staff.filter(
        #         user_id=request.user.pk
        #     )
        #     if not staff_account:
        user_qs = UserAccount.objects.filter(
            pk=request.user.pk).select_related('customer_info').prefetch_related('hotel_staff').first()
        if user_qs:
            try:
                customer_qs = user_qs.customer_info
                if customer_qs:
                    qs.customer = customer_qs
                    qs.save()
            except:
                pass
    def create_take_away_order(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)
        restaurant_id = request.data.get('restaurant')
        takeway_order_type_id = request.data.get('takeway_order_type')
        self.check_object_permissions(request, obj=restaurant_id)
        food_order_dict = {}
        if restaurant_id:
            food_order_dict['restaurant_id'] = restaurant_id
        if takeway_order_type_id:
            food_order_dict['takeway_order_type_id'] = takeway_order_type_id
            takeway_order_type_qs = TakewayOrderType.objects.filter(
                id=takeway_order_type_id)
            if not takeway_order_type_qs.exists():
                return ResponseWrapper(error_msg=['Invalid Takeway Order Type Given!'], error_code=400)
        if request.data.get('table'):
            food_order_dict['table_id'] = request.data.get('table')

        table_qs = Table.objects.filter(
            pk=food_order_dict.get('table_id')).first()
        if table_qs:
            if table_qs.is_occupied:
                return ResponseWrapper(error_code=status.HTTP_406_NOT_ACCEPTABLE, error_msg=['table already occupied'])
            else:
                table_qs.is_occupied = True
                table_qs.save()

        order_no = generate_order_no(restaurant_id=restaurant_id)
        qs = FoodOrder.objects.create(order_no=order_no, **food_order_dict)
        take_away_order_qs = TakeAwayOrder.objects.filter(
            restaurant_id=restaurant_id).first()
        if take_away_order_qs:
            add_running_order = take_away_order_qs.running_order.add(qs.id)
        else:
            take_away_order = TakeAwayOrder.objects.create(
                restaurant_id=restaurant_id)
            add_running_order = take_away_order.running_order.add(qs.id)

        serializer = FoodOrderUserPostSerializer(instance=qs)

        order_done_signal.send(
            sender=self.__class__.create,
            restaurant_id=restaurant_id,
            order_id=qs.id
        )
        return ResponseWrapper(data=serializer.data, msg='created')

    def add_items(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return ResponseWrapper(data=serializer.data, msg='created')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def cancel_order(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

        order_qs = FoodOrder.objects.filter(pk=request.data.get(
            'order_id')).exclude(status='5_PAID').first()
        if not order_qs:
            return ResponseWrapper(
                error_msg=['Order order not found'], error_code=400)

        order_qs.status = '6_CANCELLED'
        order_qs.save()
        order_qs.ordered_items.update(status="4_CANCELLED")
        table_qs = order_qs.table

        customer_fcm_device_qs = CustomerFcmDevice.objects.filter(
            customer__food_orders__id=order_qs.pk
        )

        # customer_id = customer_fcm_device_qs.values_list('pk').last()
        if send_fcm_push_notification_appointment(
            tokens_list=list(
                customer_fcm_device_qs.values_list('token', flat=True)),
            table_no=table_qs.table_no if table_qs else None,
            status='OrderCancel',
            order_no=order_qs.order_no
        ):
            pass

        if table_qs:
            if table_qs.is_occupied:
                table_qs.is_occupied = False
                table_qs.save()
        take_away_order_qs = TakeAwayOrder.objects.filter(
            running_order=order_qs.id).first()
        if take_away_order_qs:
            take_away_order_qs.running_order.remove(order_qs.id)

        staff_qs = HotelStaffInformation.objects.filter(
            user=request.user.pk, restaurant=order_qs.restaurant_id).first()
        if staff_qs:
            action.send(staff_qs, verb=order_qs.status,
                        action_object=order_qs, target=order_qs.restaurant, request_body=request.data, url=request.path)

        if staff_qs:
            if staff_qs.is_waiter:
                food_order_log = FoodOrderLog.objects.create(
                    order=order_qs, staff=staff_qs, order_status=order_qs.status)

        order_done_signal.send(
            sender=self.__class__.create,
            restaurant_id=order_qs.restaurant_id,
            order_id=order_qs.pk,
        )
        is_apps = request.path.__contains__('/apps/')

        serializer = FoodOrderByTableSerializer(
            instance=order_qs, context={'is_apps': is_apps, 'request': request})
        #  FoodOrderUserPostSerializer
        return ResponseWrapper(data=serializer.data, msg='Cancel')

    def apps_cancel_order(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

        order_qs = FoodOrder.objects.filter(pk=request.data.get(
            'order_id')).exclude(status='5_PAID').first()
        if not order_qs:
            return ResponseWrapper(
                error_msg=['Order order not found'], error_code=400)

        order_qs.status = '6_CANCELLED'
        order_qs.save()
        order_qs.ordered_items.update(status="4_CANCELLED")
        table_qs = order_qs.table
        if table_qs:
            if table_qs.is_occupied:
                table_qs.is_occupied = False
                table_qs.save()

        staff_qs = HotelStaffInformation.objects.filter(
            user=request.user.pk, restaurant=order_qs.restaurant_id).first()
        if staff_qs:
            action.send(staff_qs, verb=order_qs.status,
                        action_object=order_qs, target=order_qs.restaurant, request_body=request.data, url=request.path)

        if staff_qs.is_waiter:
            food_order_log = FoodOrderLog.objects.create(
                order=order_qs, staff=staff_qs, order_status=order_qs.status)
        # else:
        #     return ResponseWrapper(error_msg='Please Call Restaurant Staff', error_code=404)

        order_done_signal.send(
            sender=self.__class__.create,
            restaurant_id=order_qs.restaurant_id,
            order_id=order_qs.pk,
        )

        customer_fcm_device_qs = CustomerFcmDevice.objects.filter(
            customer__food_orders__id=order_qs.pk
        )

        # customer_id = customer_fcm_device_qs.values_list('pk').last()
        if send_fcm_push_notification_appointment(
            tokens_list=list(
                customer_fcm_device_qs.values_list('token', flat=True)),
            status='OrderCancel',
            order_no=order_qs.order_no
        ):
            pass

        is_apps = request.path.__contains__('/apps/')

        serializer = FoodOrderByTableSerializer(
            instance=order_qs, context={'is_apps': is_apps, 'request': request})
        #  FoodOrderUserPostSerializer
        return ResponseWrapper(data=serializer.data, msg='Cancel')

    def cancel_items(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            order_qs = FoodOrder.objects.filter(pk=request.data.get(
                'order_id')).exclude(status=['5_PAID', '6_CANCELLED']).first()
            if not order_qs:
                return ResponseWrapper(error_msg=['Order is invalid'], error_code=400)

            all_items_qs = OrderedItem.objects.filter(
                food_order=order_qs).exclude(status__in=["4_CANCELLED"])
            cancelled_items_names = []
            if all_items_qs:
                all_items_qs.filter(pk__in=request.data.get(
                    'food_items')).update(status='4_CANCELLED')
                cancel_items = OrderedItem.objects.filter(
                    pk__in=request.data.get('food_items'), status__in=['4_CANCELLED'])
                cancelled_items_names = cancel_items.values_list(
                    'food_option__food__name', flat=True)

            # order_qs.status = '3_IN_TABLE'
            # order_qs.save()

            order_done_signal.send(
                sender=self.__class__.create,
                restaurant_id=order_qs.restaurant_id,
                order_id=order_qs.pk,
            )

            if not order_qs.status == ['0_ORDER_INITIALIZED', '1_ORDER_PLACED']:
                customer_fcm_device_qs = CustomerFcmDevice.objects.filter(
                    customer__food_orders__id=order_qs.pk
                )

                # customer_id = customer_fcm_device_qs.values_list('pk').last()
                if send_fcm_push_notification_appointment(
                        tokens_list=list(
                            customer_fcm_device_qs.values_list('token', flat=True)),
                        status='OrderItemsCancel', food_names=cancelled_items_names

                ):
                    pass

            is_apps = request.path.__contains__('/apps/')
            serializer = FoodOrderByTableSerializer(
                instance=order_qs, context={'is_apps': is_apps, 'request': request})

            return ResponseWrapper(data=serializer.data, msg='Served')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def revert_back_to_in_table(self, request,  *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            order_qs = FoodOrder.objects.filter(pk=request.data.get("order_id")).exclude(
                status__in=['6_CANCELLED']).first()
            if not order_qs:
                return ResponseWrapper(error_msg=['Order is invalid'], error_code=400)

            else:
                if order_qs.status in ['3_IN_TABLE', '4_CREATE_INVOICE', '5_PAID']:
                    order_qs.status = '2_ORDER_CONFIRMED'
                    order_qs.save()

                order_done_signal.send(
                    sender=self.__class__.revert_back_to_in_table,
                    restaurant_id=order_qs.restaurant_id,
                    order_id=order_qs.pk,
                )
                is_apps = request.path.__contains__('/apps/')
                serializer = FoodOrderByTableSerializer(
                    instance=order_qs, context={'is_apps': is_apps, 'request': request})
                return ResponseWrapper(data=serializer.data, msg='Placed')
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

                # if order_qs.status in ['0_ORDER_INITIALIZED']:
                order_qs.status = '1_ORDER_PLACED'
                order_qs.save()

                order_done_signal.send(
                    sender=self.__class__.create,
                    restaurant_id=order_qs.restaurant_id,
                    order_id=order_qs.pk,
                )
                is_apps = request.path.__contains__('/apps/')
                serializer = FoodOrderByTableSerializer(
                    instance=order_qs, context={'is_apps': is_apps, 'request': request})
                # --------- for fcm----------
                table_id = order_qs.table_id
                table_qs = Table.objects.filter(pk=table_id).first()
                if not table_qs:
                    return ResponseWrapper(data=serializer.data, msg='Placed')

                staff_fcm_device_qs = StaffFcmDevice.objects.filter(
                    hotel_staff__tables=table_id)
                staff_id_list = staff_fcm_device_qs.values_list(
                    'pk', flat=True)

                if not send_fcm_push_notification_appointment(
                        tokens_list=list(staff_fcm_device_qs.values_list(
                            'token', flat=True)),
                        table_no=table_qs.table_no if table_qs else None,
                        status="Received",
                        staff_id_list=staff_id_list,
                ):
                    return ResponseWrapper(error_msg=['Failed to notify'], error_code=400)

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
        qs = all_items_qs.filter(pk__in=request.data.get(
            'food_items'))
        if qs:
            kitchen_items_print_signal.send(
                sender=self.__class__.confirm_status,
                qs=qs,
            )
        qs.update(status='2_ORDER_CONFIRMED')
        all_items_qs.exclude(pk__in=request.data.get(
            'food_items')).update(status='4_CANCELLED')

        # order_qs.status = '2_ORDER_CONFIRMED'
        # order_qs.save()
        # serializer = FoodOrderByTableSerializer(instance=order_qs)
        # if order_qs.status in ["0_ORDER_INITIALIZED", "1_ORDER_PLACED"]:
        order_qs.status = '2_ORDER_CONFIRMED'
        order_qs.save()

        order_done_signal.send(
            sender=self.__class__.create,
            restaurant_id=order_qs.restaurant_id,
            order_id=order_qs.pk,
        )
        customer_fcm_device_qs = CustomerFcmDevice.objects.filter(
            customer__food_orders__id=order_qs.pk
        )

        # customer_id = customer_fcm_device_qs.values_list('pk').last()
        if send_fcm_push_notification_appointment(
                tokens_list=list(
                    customer_fcm_device_qs.values_list('token', flat=True)),
                status='Cooking',
                order_no=order_qs.order_no
        ):
            pass

        is_apps = request.path.__contains__('/apps/')

        serializer = FoodOrderByTableSerializer(
            instance=order_qs, context={'is_apps': is_apps, 'request': request})

        return ResponseWrapper(data=serializer.data, msg='Confirmed')

    def confirm_status_without_cancel(self, request,  *args, **kwargs):
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
            food_order=order_qs.pk, pk__in=request.data.get(
                'food_items'), status__in=["1_ORDER_PLACED"])
        if all_items_qs:
            kitchen_items_print_signal.send(
                sender=self.__class__.confirm_status,
                qs=all_items_qs
            )
        all_items_qs.update(status='2_ORDER_CONFIRMED')
        # all_items_qs.exclude(pk__in=request.data.get(
        #     'food_items')).update(status='4_CANCELLED')

        # order_qs.status = '2_ORDER_CONFIRMED'
        # order_qs.save()
        # serializer = FoodOrderByTableSerializer(instance=order_qs)
        # if order_qs.status in ["0_ORDER_INITIALIZED", "1_ORDER_PLACED"]:
        order_qs.status = '2_ORDER_CONFIRMED'
        order_qs.save()
        invoice_qs = order_qs.invoices.last()
        if invoice_qs:
            invoice_qs = self.invoice_generator(
                order_qs, payment_status=invoice_qs.payment_status)

        order_done_signal.send(
            sender=self.__class__.create,
            restaurant_id=order_qs.restaurant_id,
            order_id=order_qs.pk,
        )
        is_apps = request.path.__contains__('/apps/')

        serializer = FoodOrderByTableSerializer(
            instance=order_qs, context={'is_apps': is_apps, 'request': request})

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
                food_order=order_qs).exclude(status__in=["0_ORDER_INITIALIZED"]).order_by("status")
            confirmed_items_qs = all_items_qs.filter(
                status__in=["2_ORDER_CONFIRMED"])
            if confirmed_items_qs:
                confirmed_items_qs.filter(pk__in=request.data.get(
                    'food_items')).update(status='3_IN_TABLE')

            # if order_qs.status in ["2_ORDER_CONFIRMED", "1_ORDER_PLACED", "0_ORDER_INITIALIZED"]:
            if all_items_qs:
                if all_items_qs.first().status == "4_CANCELLED":
                    order_qs.status = "6_CANCELLED"
                    table_qs = order_qs.table
                    if table_qs:
                        if table_qs.is_occupied:
                            table_qs.is_occupied = False
                            table_qs.save()

                else:
                    order_qs.status = all_items_qs.first().status
            order_qs.save()

            order_done_signal.send(
                sender=self.__class__.create,
                restaurant_id=order_qs.restaurant_id,
                order_id=order_qs.pk,
            )
            is_apps = request.path.__contains__('/apps/')
            serializer = FoodOrderByTableSerializer(
                instance=order_qs, context={'is_apps': is_apps, 'request': request})

            return ResponseWrapper(data=serializer.data, msg='Served')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def apps_order_info_price_details(self, request, pk, *args, **kwargs):
        order_qs = FoodOrder.objects.filter(
            pk=pk).last()
        if not order_qs:
            return ResponseWrapper(error_msg=['invalid order'], error_code=400)

        order_done_signal.send(
            sender=self.__class__.create,
            restaurant_id=order_qs.restaurant_id,
            order_id=order_qs.pk,
        )
        is_apps = request.path.__contains__('/apps/')

        serializer = FoodOrderByTableSerializer(
            instance=order_qs, context={'is_apps': is_apps, 'request': request})

        return ResponseWrapper(data=serializer.data, msg='order payment info')

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

                # cash_received = request.data.get('cash_received')
                # if cash_received>0:
                #     if cash_received < order_qs.payable_amount and cash_received>0:
                #         return ResponseWrapper(error_msg=['You Cash Amount is less then You Bill'], status=400)
                #     order_qs.cash_received = cash_received

                order_qs.save()

                staff_qs = HotelStaffInformation.objects.filter(
                    user=request.user.pk, restaurant_id=order_qs.restaurant_id).first()
                if staff_qs:
                    action.send(staff_qs, verb=order_qs.status,
                                action_object=order_qs, target=order_qs.restaurant, request_body=request.data, url=request.path)
                    if staff_qs.is_waiter:
                        food_order_log = FoodOrderLog.objects.create(
                            order=order_qs, staff=staff_qs, order_status=order_qs.status)

                invoice_qs = self.invoice_generator(
                    order_qs, payment_status="0_UNPAID")

                serializer = InvoiceSerializer(instance=invoice_qs)
                # order_done_signal.send(
                #     sender=self.__class__.create,
                #     restaurant_id=order_qs.restaurant_id,
                # )
                order_done_signal.send(
                    sender=self.__class__.create,
                    restaurant_id=order_qs.restaurant_id,
                    order_id=order_qs.pk,
                )
            return ResponseWrapper(data=serializer.data.get('order_info'), msg='Invoice Created')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)


    def create_invoice_for_dashboard(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        # payment_method = request.data.get('payment_method')
        # payment_method_qs = PaymentType.objects.filter(id=payment_method).first()
        # payment_method_cash_qs = PaymentType.objects.filter(name='Cash').first()
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

                # cash_received = request.data.get('cash_received')
                #
                # if payment_method == None or payment_method == 0:
                #     order_qs.payment_method = payment_method_cash_qs
                # else:
                #     order_qs.payment_method = payment_method_qs
                #
                # # if payment_method_qs:
                # #     if payment_method_qs.name =='Cash' and not cash_received:
                # #         return ResponseWrapper(error_msg=[' Cash Amount is not Given'], status=400)
                # if cash_received:
                #     if cash_received < order_qs.payable_amount:
                #         return ResponseWrapper(error_msg=['You Cash Amount is less then You Bill'], status=400)
                #     order_qs.cash_received = cash_received



                order_qs.save()

                staff_qs = HotelStaffInformation.objects.filter(
                    user=request.user.pk, restaurant_id=order_qs.restaurant_id).first()
                if staff_qs:
                    action.send(staff_qs, verb=order_qs.status,
                                action_object=order_qs, target=order_qs.restaurant, request_body=request.data, url=request.path)
                    if staff_qs.is_waiter:
                        food_order_log = FoodOrderLog.objects.create(
                            order=order_qs, staff=staff_qs, order_status=order_qs.status)

                invoice_qs = self.invoice_generator(
                    order_qs, payment_status="0_UNPAID")

                serializer = InvoiceSerializer(instance=invoice_qs)
                # order_done_signal.send(
                #     sender=self.__class__.create,
                #     restaurant_id=order_qs.restaurant_id,
                # )
                order_done_signal.send(
                    sender=self.__class__.create,
                    restaurant_id=order_qs.restaurant_id,
                    order_id=order_qs.pk,
                )
            return ResponseWrapper(data=serializer.data.get('order_info'), msg='Invoice Created')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)


    def payment(self, request,  *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        payment_method = request.data.get('payment_method')
        payment_method_qs = PaymentType.objects.filter(id=payment_method).first()
        payment_method_cash_qs = PaymentType.objects.filter(name='Cash').first()

        if serializer.is_valid():
            order_qs = FoodOrder.objects.filter(pk=request.data.get("order_id"),
                                                status__in=["4_CREATE_INVOICE"]).first()
            if not order_qs:
                return ResponseWrapper(error_msg=['please create invoice before payment'], error_code=400)

            remaining_item_counter = OrderedItem.objects.filter(
                food_order=order_qs.pk).exclude(status__in=["0_ORDER_INITIALIZED", "3_IN_TABLE", '4_CANCELLED']).count()

            if remaining_item_counter > 0:
                return ResponseWrapper(error_msg=['Order is running'], error_code=400)

            else:
                order_qs.status = '5_PAID'

                cash_received = request.data.get('cash_received')

                if payment_method == None or payment_method == 0:
                    order_qs.payment_method = payment_method_cash_qs
                else:
                    order_qs.payment_method = payment_method_qs

                # if payment_method_qs:
                #     if payment_method_qs.name =='Cash' and not cash_received:
                #         return ResponseWrapper(error_msg=[' Cash Amount is not Given'], status=400)
                if cash_received:
                    if cash_received < order_qs.payable_amount:
                        return ResponseWrapper(error_msg=['You Cash Amount is less then You Bill'], status=400)
                    order_qs.cash_received = cash_received


                order_qs.save()
                table_qs = order_qs.table
                if table_qs:
                    table_qs.is_occupied = False
                    table_qs.save()
                take_away_order_qs = TakeAwayOrder.objects.filter(
                    running_order=order_qs.id).first()
                if take_away_order_qs:
                    take_away_order_qs.running_order.remove(order_qs.id)

                staff_qs = HotelStaffInformation.objects.filter(
                    user=request.user.pk, restaurant=order_qs.restaurant_id).first()
                if staff_qs:
                    action.send(staff_qs, verb=order_qs.status,
                                action_object=order_qs, target=order_qs.restaurant, request_body=request.data,
                                url=request.path)

                if staff_qs.is_waiter:
                    food_order_log = FoodOrderLog.objects.create(
                        order=order_qs, staff=staff_qs, order_status=order_qs.status)

                invoice_qs = self.invoice_generator(
                    order_qs, payment_status='1_PAID')

                serializer = InvoiceSerializer(instance=invoice_qs)
                order_done_signal.send(
                    sender=self.__class__.create,
                    restaurant_id=invoice_qs.restaurant_id,
                    order_id=order_qs.pk,
                )
            return ResponseWrapper(data=serializer.data.get('order_info'), msg='Paid')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def food_reorder_by_order_id(self, request,  *args, **kwargs):
        table_id = request.data.get('table_id')
        serializer = self.get_serializer(data=request.data)

        order_qs = OrderedItem.objects.filter(
            food_order=request.data.get("order_id"), status='3_IN_TABLE')
        if not order_qs:
            return ResponseWrapper(msg='Order id is not Valid', error_code=400)
        table_qs = Table.objects.filter(id=table_id).last()

        if table_qs.is_occupied:
            return ResponseWrapper(msg='Table is already occupied')

        reorder_qs = FoodOrder.objects.create(
            table_id=request.data.get("table_id"))
        table_qs.is_occupied = True
        table_qs.save()
        for item in order_qs:
            OrderedItem.objects.create(quantity=item.quantity, food_option=item.food_option,
                                       food_order=reorder_qs)

        order_done_signal.send(
            sender=self.__class__.create,
            restaurant_id=reorder_qs.restaurant_id,
            order_id=order_qs.pk,
        )
        is_apps = request.path.__contains__('/apps/')

        serializer = FoodOrderByTableSerializer(instance=reorder_qs, context={
                                                'is_apps': is_apps, 'request': request})
        return ResponseWrapper(data=serializer.data, msg='Success')

    def table_transfer(self, request,  *args, **kwargs):
        food_order_qs = FoodOrder.objects.filter(
            id=request.data.get('order_id')).first()
        if not food_order_qs:
            return ResponseWrapper(msg='Invalid Food Order')
        table_qs = Table.objects.filter(id=request.data.get('table_id')).last()
        if table_qs.is_occupied:
            return ResponseWrapper(msg='Table is already occupied')
        food_order_qs.table.is_occupied = False
        food_order_qs.table.save()

        food_order_qs.table_id = table_qs.id
        table_qs.is_occupied = True
        table_qs.save()
        food_order_qs.save()

        is_apps = request.path.__contains__('/apps/')
        serializer = FoodOrderByTableSerializer(instance=food_order_qs, context={
                                                'is_apps': is_apps, 'request': request})
        return ResponseWrapper(data=serializer.data, msg='Table Transfer')

    def customer_order_history(self, request, *args, **kwargs):
        order_qs = FoodOrder.objects.filter(
            customer__user=request.user.pk, status='5_PAID').order_by('-created_at')
       # page_qs = self.paginate_queryset(order_qs)
        serializer = CustomerOrderDetailsSerializer(
            instance=order_qs, many=True)
        # paginated_data = self.get_paginated_response(serializer.data)

        return ResponseWrapper(data=serializer.data, msg='success')

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        is_apps = request.path.__contains__('/apps/')
        serializer = self.get_serializer(
            instance, context={'is_apps': is_apps, 'request': request})
        return ResponseWrapper(serializer.data)

    def order_status(self, request, order_id, *args, **kwargs):
        food_order_qs = FoodOrder.objects.filter(pk=order_id).last()
        serializer = FoodOrderStatusSerializer(instance=food_order_qs)
        return ResponseWrapper(data=serializer.data, msg='success')


class OrderedItemViewSet(LoggingMixin, CustomViewSet, FoodOrderCore):
    queryset = OrderedItem.objects.all()
    lookup_field = 'pk'
    logging_methods = ['GET', 'POST', 'PATCH', 'DELETE']

    def get_permissions(self):
        if self.action in ['create', 'cart_create_from_dashboard', 'destroy', 'update']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action in ['create', 'update']:
            self.serializer_class = OrderedItemUserPostSerializer

        elif self.action in ['cart_create_from_dashboard']:
            self.serializer_class = OrderedItemDashboardPostSerializer

        elif self.action in ['re_order_items']:
            self.serializer_class = ReOrderedItemSerializer
        else:
            self.serializer_class = OrderedItemSerializer

        return self.serializer_class

    def destroy(self, request, *args, **kwargs):
        item_qs = OrderedItem.objects.filter(
            **kwargs).exclude(status__in=["4_CANCELLED"], food_order__status__in=['5_PAID', '6_CANCELLED']).last()
        if not item_qs:
            return ResponseWrapper(error_msg=['item is invalid or cancelled'], error_code=400)
        order_qs = item_qs.food_order
        if not order_qs:
            return ResponseWrapper(error_msg=['Order is invalid'], error_code=400)

        item_qs.status = '4_CANCELLED'
        item_qs.save()
        order_id = item_qs.food_order
        invoice_qs = order_id.invoices.last()
        if invoice_qs:
            invoice_qs = self.invoice_generator(
                order_qs, payment_status=invoice_qs.payment_status)

        restaurant_id = order_qs.restaurant_id
        order_done_signal.send(
            sender=self.__class__.create,
            restaurant_id=restaurant_id,
            order_id=order_qs.pk,
        )

        if order_qs.status not in ['0_ORDER_INITIALIZED']:
            customer_fcm_device_qs = CustomerFcmDevice.objects.filter(
                customer__food_orders__id=order_qs.pk
            )

            # customer_id = customer_fcm_device_qs.values_list('pk').last()
            send_fcm_push_notification_appointment(
                    tokens_list=list(
                        customer_fcm_device_qs.values_list('token', flat=True)),
                    status='OrderItemCancel', food_name=item_qs.food_option.food.name

            )

        is_apps = request.path.__contains__('/apps/')
        calculate_price_with_initial_item = request.path.__contains__(
            '/apps/customer/order/cart/items/')

        serializer = FoodOrderByTableSerializer(
            instance=order_qs, context={'is_apps': is_apps, 'request': request,
                                        'calculate_price_with_initial_item': calculate_price_with_initial_item})

        return ResponseWrapper(data=serializer.data, msg='Served')

    def update(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data, partial=True)
        if serializer.is_valid():
            qs = serializer.update(instance=self.get_object(
            ), validated_data=serializer.validated_data)
            order_qs = qs.food_order

            invoice_qs = order_qs.invoices.last()
            if invoice_qs:
                invoice_qs = self.invoice_generator(
                    order_qs, payment_status=invoice_qs.payment_status)

            restaurant_id = order_qs.restaurant_id
            order_done_signal.send(
                sender=self.__class__.create,
                restaurant_id=restaurant_id,
                order_id=order_qs.pk,
            )
            is_apps = request.path.__contains__('/apps/')
            calculate_price_with_initial_item = request.path.__contains__(
                '/apps/customer/order/cart/items/')
            if calculate_price_with_initial_item:
                serializer = FoodOrderSerializer(instance=order_qs, context={
                                                 'is_apps': is_apps, 'request': request,
                                                 'calculate_price_with_initial_item': calculate_price_with_initial_item})
            else:
                serializer = FoodOrderByTableSerializer(instance=order_qs, context={
                    'is_apps': is_apps, 'request': request,
                    'calculate_price_with_initial_item': calculate_price_with_initial_item})

            return ResponseWrapper(data=serializer.data)
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, many=True)

        if serializer.is_valid():
            is_invalid_order = True
            is_staff_order = False
            is_waiter_staff_order = False
            if request.data:
                food_order = request.data[0].get('food_order')
                food_order_qs = FoodOrder.objects.filter(pk=food_order)
                restaurant_id = food_order_qs.first().table.restaurant_id
                is_staff = request.path.__contains__('/waiter_order/')
                if is_staff:
                    if HotelStaffInformation.objects.filter(Q(is_manager=True) | Q(is_owner=True), user=request.user.pk, restaurant_id=restaurant_id):
                        food_order_qs = food_order_qs.first()
                        is_staff_order = True
                    elif HotelStaffInformation.objects.filter(is_waiter=True, user=request.user.pk, restaurant_id=restaurant_id):
                        food_order_qs = food_order_qs.first()
                        is_waiter_staff_order = True

                else:
                    food_order_qs = food_order_qs.exclude(
                        status__in=['5_PAID', '6_CANCELLED']).first()
                if food_order_qs:
                    is_invalid_order = False
            if is_invalid_order:
                return ResponseWrapper(error_code=400, error_msg=['order is invalid'])

            qs = serializer.save()

            restaurant_id = food_order_qs.restaurant_id
            is_take_away_order= request.path.__contains__('take_away_order/cart/items/')

            if is_staff_order:
                order_pk_list = list()
                for item in qs:
                    order_pk_list.append(item.pk)
                qs = OrderedItem.objects.filter(pk__in=order_pk_list)
                qs.update(status='2_ORDER_CONFIRMED')
                # if is_take_away_order:
                #     qs.update(status='2_ORDER_CONFIRMED')
                food_order_qs.status = '2_ORDER_CONFIRMED'
                food_order_qs.save()

            elif is_waiter_staff_order:
                order_pk_list = list()
                for item in qs:
                    order_pk_list.append(item.pk)
                qs = OrderedItem.objects.filter(pk__in=order_pk_list)
                qs.update(status='1_ORDER_PLACED')
                food_order_qs.status = '1_ORDER_PLACED'
                food_order_qs.save()

            # order_order_qs= FoodOrder.objects.filter(status = '0_ORDER_INITIALIZED',pk=request.data.get('id'))
            # if order_order_qs:
            #     order_order_qs.update(status='0_ORDER_INITIALIZED')



            order_done_signal.send(
                sender=self.__class__.create,
                restaurant_id=restaurant_id,
                order_id=food_order_qs.pk,
            )
            is_apps = request.path.__contains__('/apps/')

            serializer = FoodOrderByTableSerializer(instance=food_order_qs, context={
                                                    'is_apps': is_apps, 'request': request})
            return ResponseWrapper(data=serializer.data, msg='created')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def cart_create_from_dashboard(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, many=True)
        if not serializer.is_valid():
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)
        if not request.data:
            return ResponseWrapper(error_code=400, error_msg='empty request body')
        food_order = request.data[0].get('food_order')
        food_order_qs = FoodOrder.objects.filter(pk=food_order).first()

        if food_order_qs.table:
            restaurant_id = food_order_qs.table.restaurant_id
        else:
            restaurant_id = food_order_qs.restaurant.pk

        if not HotelStaffInformation.objects.filter(Q(is_manager=True) | Q(is_owner=True), user=request.user.pk,
                                                    restaurant_id=restaurant_id):
            return ResponseWrapper(error_code=status.HTTP_401_UNAUTHORIZED, error_msg='not a valid manager or owner')

        # order_details = request.data
        # for order_detail in order_details:
        #     food_option = order_detail.get('food_option')
        #     food_qs = Food.objects.filter(food_options=food_option).first()
        #     if not food_qs.is_available:
        #         return ResponseWrapper(error_msg=['Food is not Available'], error_code=400)
        # OrderedItem.objects.create(quantity=item.quantity, food_option=item.food_option,


        list_of_qs = serializer.save()
        invoice_qs = food_order_qs.invoices.last()
        if invoice_qs:
            invoice_qs = self.invoice_generator(
                food_order_qs, payment_status=invoice_qs.payment_status)

        serializer = OrderedItemGetDetailsSerializer(
            instance=list_of_qs, many=True)
        order_done_signal.send(
            sender=self.__class__.create,
            restaurant_id=restaurant_id,
            order_id=food_order_qs.pk,
        )
        return ResponseWrapper(data=serializer.data, msg='created')

    def re_order_items(self, request, *args, **kwargs):
        # serializer = self.get_serializer(data=request.data, many = True)
        new_quantity = request.data.get('quantity')
        re_order_item_qs = OrderedItem.objects.filter(
            id=request.data.get("order_item_id")).first()
        if re_order_item_qs.food_order.status == '5_PAID':
            return ResponseWrapper(error_msg=['Order is already paid'], error_code=406)

        if re_order_item_qs.status in ['2_ORDER_CONFIRMED', '3_IN_TABLE']:
            # for item in re_order_item_qs:
            re_order_item_qs = OrderedItem.objects.create(quantity=new_quantity, food_option=re_order_item_qs.food_option,
                                                          food_order=re_order_item_qs.food_order, status='1_ORDER_PLACED')
            re_order_item_qs.food_order.status = '1_ORDER_PLACED'
            re_order_item_qs.save()

        elif re_order_item_qs.status in ['0_ORDER_INITIALIZED', '1_ORDER_PLACED']:
            update_quantity = re_order_item_qs.quantity + new_quantity
            re_order_item_qs.quantity = update_quantity
            re_order_item_qs.food_order.status = '1_ORDER_PLACED'
            re_order_item_qs.save()
        else:
            return ResponseWrapper(error_msg=['Order Item is already Cancelled'], error_code=406)

        # food_order_qs = OrderedItem.objects.filter(food_order_id = re_order_item_qs.food_order_id)

        order_done_signal.send(
            sender=self.__class__.re_order_items,
            restaurant_id=re_order_item_qs.food_order.restaurant_id,
            order_id=re_order_item_qs.food_order.pk,
        )
        is_apps = request.path.__contains__('/apps/')
        serializer = FoodOrderByTableSerializer(
            instance=re_order_item_qs.food_order, context={'is_apps': is_apps, 'request': request})
        return ResponseWrapper(data=serializer.data, msg='Success')


class FoodViewSet(LoggingMixin, CustomViewSet):
    serializer_class = FoodWithPriceSerializer

    def get_serializer_class(self):
        if self.action in ['retrieve']:
            self.serializer_class = FoodDetailSerializer
        elif self.action in ['food_search']:
            self.serializer_class = FoodSerializer
        elif self.action in ['food_search_code']:
            self.serializer_class = FoodSerializer
        # elif self.action in ['check_food_discount']:
        #     self.serializer_class = FoodDiscountCheckerSerializer
        elif self.action in ['create', 'update', 'destroy']:
            self.serializer_class = FoodPostSerializer

        return self.serializer_class
    # permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['food_search', 'food_search_code', 'food_list', 'check_food_discount']:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['create', 'update', 'destroy']:
            permission_classes = [
                custom_permissions.IsRestaurantManagementOrAdmin]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

    queryset = Food.objects.all()
    lookup_field = 'pk'
    logging_methods = ['GET', 'POST', 'PATCH', 'DELETE']
    # http_method_names = ['post', 'patch', 'get', 'delete']

    def check_food_discount(self, request, order_id, *args, **kwargs):
        qs = FoodOrder.objects.filter(id=order_id)

        if not qs:
            return ResponseWrapper(msg='Invalid order id', error_code=400)

        if qs.last().discount_amount:
            return ResponseWrapper(data={
                "is_discount": True,
                "msg": "Discount is given"
            }, msg='success')
        else:
            return ResponseWrapper(data={
                "is_discount": False,
                "msg": "Discount is not given"
            }, msg='success')


    def create(self, request):
        staff_qs = HotelStaffInformation.objects.filter(Q(is_manager=True) | Q(is_owner=True), user=request.user.pk,
                                                        restaurant_id=request.data.get('restaurant'))
        if not staff_qs:
            return ResponseWrapper(msg='Your are not Valid Restaurant owner or manager', error_code=400)
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        if serializer.is_valid():
            qs = serializer.save()
            serializer = self.serializer_class(instance=qs)
            # serializer = self.serializer_class(instance=qs)
            return ResponseWrapper(data=serializer.data, msg='created')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def update(self, request, **kwargs):
        staff_qs = HotelStaffInformation.objects.filter(Q(is_manager=True) | Q(is_owner=True), user=request.user.pk,
                                                        restaurant_id=request.data.get('restaurant'))
        if not staff_qs:
            return ResponseWrapper(msg='Your are not Valid Restaurant owner or manager', error_code=400)
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data, partial=True)
        if serializer.is_valid():
            qs = serializer.update(instance=self.get_object(
            ), validated_data=serializer.validated_data)
            serializer = self.serializer_class(instance=qs)
            return ResponseWrapper(data=serializer.data)
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    # @method_decorator(cache_page(60*15))
    def food_details(self, request, pk, *args,  **kwargs):
        qs = Food.objects.filter(pk=pk).select_related(
            'category').prefetch_related("food_extras").last()
        serializer = FoodDetailSerializer(instance=qs)
        return ResponseWrapper(data=serializer.data, msg='success')

    def category_list(self, request, *args, restaurant, **kwargs):
        qs = FoodCategory.objects.filter(
            foods__restaurant_id=restaurant).distinct().order_by('name')
        serializer = FoodCategorySerializer(instance=qs, many=True)
        return ResponseWrapper(data=serializer.data, msg='success')

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter("restaurant", openapi.IN_QUERY,
                          type=openapi.TYPE_INTEGER)
    ])
    def food_list(self, request, *args, category_id, **kwargs):

        restaurant_id = int(request.query_params.get('restaurant'))
        """
        if not (
            self.request.user.is_staff or HotelStaffInformation.objects.filter(
                Q(is_owner=True) | Q(is_manager=True),
                user_id=request.user.pk, restaurant_id=restaurant_id
            )
        ):
            return ResponseWrapper(error_code=status.HTTP_401_UNAUTHORIZED, error_msg=["can't get food list"])
            """

        category_qs = Food.objects.filter(
            category=category_id, restaurant_id=restaurant_id)

        serializer = FoodDetailSerializer(instance=category_qs, many=True)
        return ResponseWrapper(data=serializer.data, msg='success')

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter("restaurant", openapi.IN_QUERY,
                          type=openapi.TYPE_INTEGER)
    ])
    def food_search(self, request, *args, food_name, **kwargs):
        restaurant_id = int(request.query_params.get('restaurant'))
        is_dashboard = request.path.__contains__('/dashboard/')
        food_name = food_name
        if food_name == ' ':
            return ResponseWrapper(error_msg=['Food Name is not given'], status=400)
        food_name_qs = Food.objects.filter(
            Q(name__icontains=food_name) | Q(category__name__icontains=food_name), restaurant_id=restaurant_id,
                is_available=True)
        dashboard_food_name_qs = Food.objects.filter(
            Q(name__icontains=food_name) | Q(category__name__icontains=food_name), restaurant_id=restaurant_id)
        if is_dashboard:
            serializer = FoodDetailSerializer(instance=dashboard_food_name_qs, many=True)
        else:
            serializer = FoodsByCategorySerializer(
                instance=food_name_qs, many=True)

        return ResponseWrapper(data=serializer.data, msg='success')

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter("restaurant", openapi.IN_QUERY,
                          type=openapi.TYPE_INTEGER)
    ])
    def food_search_code(self, request, *args, food_code, **kwargs):
        """
        food_search_code() => Search Food By Code
        """
        restaurant_id = int(request.query_params.get('restaurant'))
        is_dashboard = request.path.__contains__('/dashboard/')
        food_code = food_code
        if food_code == ' ':
            return ResponseWrapper(error_msg=['Food Code is not given'], status=400)
        food_code_qs = Food.objects.filter(
            Q(code__icontains=food_code) | Q(category__name__icontains=food_code), restaurant_id=restaurant_id,
                is_available=True)
        dashboard_food_code_qs = Food.objects.filter(
            Q(code__icontains=food_code) | Q(category__name__icontains=food_code), restaurant_id=restaurant_id)
        if is_dashboard:
            serializer = FoodDetailSerializer(instance=dashboard_food_code_qs, many=True)
        else:
            serializer = FoodsByCategorySerializer(
                instance=food_code_qs, many=True)

        return ResponseWrapper(data=serializer.data, msg='success')

    def food_extra_by_food(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = FoodExtraSerializer(instance.food_extras.all(), many=True)
        return ResponseWrapper(data=serializer.data)

    def food_option_by_food(self, request, *args, **kwargs):
        instance = self.get_object()

        serializer = FoodOptionSerializer(
            instance.food_options.all(), many=True)
        return ResponseWrapper(data=serializer.data)

    def update(self, request, pk, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data, partial=True)
        if serializer.is_valid():
            old_qs = Food.objects.filter(pk=pk).first()
            qs = serializer.update(
                instance=old_qs, validated_data=serializer.validated_data)
            serializer = FoodDetailSerializer(instance=qs)
            return ResponseWrapper(data=serializer.data)
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)


class FoodByRestaurantViewSet(LoggingMixin, CustomViewSet):
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
            restaurant=restaurant).prefetch_related('food_options', 'food_extras').distinct()
        # qs = qs.filter(is_top = True)
        serializer = FoodDetailSerializer(instance=qs, many=True)
        return ResponseWrapper(data=serializer.data, msg='success')

    def top_foods_by_category(self, request, restaurant, *args, **kwargs):
        # qs = FoodCategory.objects.filter(
        #     foods__restaurant_id=restaurant,
        #     foods__is_top=True
        # ).prefetch_related('foods').distinct()
        qs = Food.objects.filter(
            restaurant_id=restaurant, is_top=True).select_related('category')
        # qs = qs.filter(is_top = True)
        serializer = FoodsByCategorySerializer(instance=qs, many=True)
        return ResponseWrapper(data=serializer.data, msg='success')

    def recommended_foods_by_category(self, request, restaurant, *args, **kwargs):
        # qs = FoodCategory.objects.filter(
        #     foods__restaurant_id=restaurant,
        #     foods__is_recommended=True
        # ).prefetch_related('foods').distinct()
        qs = Food.objects.filter(
            restaurant_id=restaurant, is_recommended=True).select_related('category')
        # qs = qs.filter(is_top = True)
        serializer = FoodsByCategorySerializer(instance=qs, many=True)
        return ResponseWrapper(data=serializer.data, msg='success')

    # @method_decorator(cache_page(60*15))
    def list_by_category(self, request, restaurant, *args, **kwargs):
        # qs = FoodCategory.objects.filter(
        #     foods__restaurant_id=restaurant,
        # ).prefetch_related('foods', 'foods__food_options').distinct()
        qs = Food.objects.filter(
            restaurant_id=restaurant,is_available = True).select_related('category')

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

    def get_serializer_class(self):
        if self.action in ['report_by_date_range']:
            self.serializer_class = ReportDateRangeSerializer

        # if self.action in ['waiter_report_by_date_range']:
        #     self.serializer_class = ReportDateRangeSerializer

        return self.serializer_class

    def get_permissions(self):
        permission_classes = []
        if self.action in [""]:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['waiter_served_report']:
            permission_classes = [
                custom_permissions.IsRestaurantStaff
            ]
        # elif self.action == "retrieve" or self.action == "update":
        #     permission_classes = [permissions.AllowAny]
        # else:
        #     permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    """
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
    """

    # @swagger_auto_schema(
    #     request_body=ReportDateRangeSerializer
    # )
    #
    # def waiter_report_by_date_range(self, request,restaurant, *args, **kwargs):
    #     start_date = request.data.get('start_date', timezone.now().date())
    #     end_date = request.data.get('end_date', timezone.now().date())
    #     if request.data.get('end_date'):
    #         end_date = datetime.strptime(end_date, '%Y-%m-%d')
    #     end_date += timedelta(days=1)
    #     order_log_qs = FoodOrderLog.objects.filter(order__restaurant_id=restaurant,
    #                                                       created_at__gte=start_date, created_at__lte=end_date
    #                                                       ).distinct()
    #     total_waiter = order_log_qs.values_list('staff').distinct().count()
    #     order_qs = order_log_qs.values_list('order__payable_amount', flat=True)
    #     total_amount = round(sum(order_qs), 2)
    #     staff_list = order_log_qs.values_list('staff',flat=True).distinct()
    #     staff_report_list = list()
    #     staff_list.values_list('staff__user__first_name')
    #     for staff in staff_list:
    #         temp_order_log_qs = order_log_qs.filter(staff_id=staff)
    #
    #         payment_amount_list = temp_order_log_qs.values_list('order__payable_amount',flat=True)
    #         total_payment_amount = round(sum(payment_amount_list),2)
    #         staff_qs = HotelStaffInformation.objects.filter(pk=staff).first()
    #         staff_serializer = StaffInfoGetSerializer(instance=staff_qs)
    #         staff_report_dict = {
    #             'total_payment_amount':total_payment_amount,
    #             'staff_info': staff_serializer.data,
    #             'total_served_order':temp_order_log_qs.count(),
    #         }
    #
    #     return ResponseWrapper(data = {'total_waiter' :total_waiter,
    #                                    'total_amount':total_amount,
    #                                    'staff info':staff_report_dict,
    #                                    },   msg= 'success')

    def report_by_date_range(self, request, *args, **kwargs):
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        # restaurant_id =Invoice.objects.filter(inv)
        # if not HotelStaffInformation.objects.filter(Q(is_manager=True) | Q(is_owner=True), user=request.user.pk,
        #                                           restaurant_id=restaurant_id):
        #   return ResponseWrapper(error_code=status.HTTP_401_UNAUTHORIZED, error_msg='not a valid manager or owner')

        food_items_date_range_qs = Invoice.objects.filter(
            created_at__gte=start_date, created_at__lte=end_date, payment_status='1_PAID')
        sum_of_payable_amount = sum(
            food_items_date_range_qs.values_list('payable_amount', flat=True))
        response = {'total_sell': round(sum_of_payable_amount, 2)}

        return ResponseWrapper(data=response, msg='success')

    @swagger_auto_schema(
        request_body=ReportDateRangeSerializer
    )
    def food_report_by_date_range(self, request, *args, **kwargs):
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        restaurant_id = request.data.get('restaurant_id')
        food_items_date_range_qs = Invoice.objects.filter(restaurant_id=restaurant_id,
                                                          created_at__gte=start_date, created_at__lte=end_date, payment_status='1_PAID')

        order_items_list = food_items_date_range_qs.values_list(
            'order_info__ordered_items', flat=True)
        food_dict = {}
        food_report_list = []
        food_option_report = {}
        food_extra_report = {}

        for items_per_invoice in order_items_list:
            for item in items_per_invoice:

                food_id = item.get("food_option", {}).get("food")
                if (not food_id) or (not item.get('status') == "3_IN_TABLE"):
                    continue

                name = item.get('food_name')
                price = item.get('price', 0)
                quantity = item.get('quantity', 0)

                if not food_dict.get(food_id):
                    food_dict[food_id] = {}

                if not food_dict.get(food_id, {}).get(name):
                    food_dict[food_id]['name'] = name

                if not food_dict.get(food_id, {}).get(price):
                    food_dict[food_id]['price'] = price
                else:
                    food_dict[food_id]['price'] += price

                if not food_dict.get(food_id, {}).get(quantity):
                    food_dict[food_id]['quantity'] = quantity
                else:
                    food_dict[food_id]['quantity'] += quantity
                # food_option_report[food_id]['food_option_report'] = food_option
                # food_option_report[food_id]['food_extra'] = food_extra_name

                # calculation of food option

                food_option_name = item.get("food_option", {}).get("name")
                food_option_id = item.get("food_option", {}).get("id")

                if food_option_id and food_option_name:
                    if not food_dict.get(food_id, {}).get('food_option'):
                        food_dict[food_id]['food_option'] = {}
                    if not food_dict.get(food_id, {}).get('food_option', {}).get(food_option_id):
                        food_dict[food_id]['food_option'][food_option_id] = {
                            'name': food_option_name, 'quantity': quantity}
                    else:
                        food_dict[food_id]['food_option'][food_option_id]['quantity'] += quantity

                # calculation of food extra

                food_extra_list = item.get('food_extra', [])

                for food_extra in food_extra_list:
                    food_extra_name = food_extra.get("name")
                    food_extra_id = food_extra.get("id")

                    if food_extra_id and food_extra_name:
                        if not food_dict.get(food_id, {}).get('food_extra'):
                            food_dict[food_id]['food_extra'] = {}
                        if not food_dict.get(food_id, {}).get("food_extra", {}).get(food_extra_id):
                            food_dict[food_id]["food_extra"][food_extra_id] = {
                                'name': food_extra_name, 'quantity': quantity}
                        else:
                            food_dict[food_id]["food_extra"][food_extra_id]['quantity'] += quantity

        for item in food_dict.values():
            if item.get('food_extra', {}):
                item['food_extra'] = item.get('food_extra', {}).values()

            if item.get('food_option', {}):
                item['food_option'] = item.get('food_option', {}).values()

        # for food_option in order_items_list:
        #     for option in food_option:

        #         food_id = option.get("food_option", {}).get("food")
        #         if (not food_id) or (not item.get('status')=="3_IN_TABLE"):
        #             continue

        #         food_option_name = option.get("food_option", {}).get("name")
        #         food_option_quantity = option.get('quantity', 0)
        #         if not food_option_report.get(food_id):
        #             food_option_report[food_id] ={}
        #         if not food_option_report.get(food_id,{}).get(food_option_name):
        #             food_option_report[food_id]['name'] = food_option_name
        #         if not food_option_report.get(food_id,{}).get(food_option_quantity):
        #             food_option_report[food_id]['quantity'] = food_option_quantity
        #         else:
        #             food_option_report[food_id]['quantity'] += food_option_quantity

        # for food_extra in order_items_list:
        #     for extra in food_extra:
        #         food_id = extra.get("food_extra", {})
        #         if (not food_id) or (not item.get('status') == "3_IN_TABLE"):
        #             continue
        #         for extra_info in extra:
        #             food_extra_info= extra_info.get("food_extra",{})
        #             if not food_option_report.get(food_id):
        #                 food_extra_report[food_id]['food_extra'] = food_extra_info

        # response = {'food_report': food_dict.values(), }
        return ResponseWrapper(data=food_dict.values(), msg='success')

    def first_date_of_months_up_to_current_month_of_current_year(self, *args, **kwargs):
        first_day = timezone.now().date().replace(day=1)
        first_day_of_all_month = {}
        for month_flag in range(first_day.month):
            first_day_of_all_month[month_flag] = (
                first_day - relativedelta(months=(first_day.month-(month_flag+1))))

        return first_day_of_all_month


    def get_takeway_order_type_report_data(self, restaurant_id=None):
        """
        Generates Takeway Order Type Report Data
        parameter => restaurant_id(int)
        return => object {
            'total_amount_received_by_takeway_order_type': list[object],
            'current_month_total_takeway_order_type_distribution': list[object],
            'last_month_total_takeway_order_type_distribution': list[object],
            'weekly_total_takeway_order_type_distribution': list[object],
            'daily_total_takeway_order_type_distribution': list[object],
        }
        """

        # Set Decimal Precision
        getcontext().prec = 3

        # report data placeholder
        tw_report_data = {
            'total_amount_received_by_takeway_order_type': None,
            'current_month_total_takeway_order_type_distribution': None,
            'last_month_total_takeway_order_type_distribution': None,
            'weekly_total_takeway_order_type_distribution': None,
            'daily_total_takeway_order_type_distribution': None,
        }

        # takeway order type report
        takeway_order_type_total_amount = []
        this_month_total_takeway_order_type_distribution = []
        last_month_total_takeway_order_type_distribution = []
        weekly_total_takeway_order_type_distribution = []
        daily_total_takeway_order_type_distribution = []

        restaurant_qs = Restaurant.objects.filter(id=restaurant_id)

        today = timezone.datetime.now()
        this_month = timezone.now().date().replace(day=1)
        last_month = (this_month - timedelta(days=1)).replace(day=1)

        week = 7

        for day in range(week):
            day_int = (today.weekday() + 1) % 7
            start_of_week = today - timezone.timedelta(day_int-day)

        takeway_order_type_details_list = restaurant_qs.values_list(
            'takeway_order_type', 'takeway_order_type__name', 'takeway_order_type__image'
        )

        for takeway_order_type, takeway_order_type_name, takeway_order_type_image in takeway_order_type_details_list:
            tw_order_qs = FoodOrder.objects.filter(
                takeway_order_type=takeway_order_type, restaurant_id=restaurant_id, status='5_PAID'
            )
            total_order = tw_order_qs.count()
            takeway_order_type_payable_amount_list = tw_order_qs.values_list(
                'payable_amount', flat=True
            )
            takeway_order_type_amount = sum(takeway_order_type_payable_amount_list)
            takeway_order_type_total_amount.append(
                {
                    'id': takeway_order_type, 
                    'name': takeway_order_type_name, 
                    'image': takeway_order_type_image,
                    'amount': Decimal(takeway_order_type_amount),
                    'total_order': total_order
                }
            )

            # Current Month takeway Order report
            this_month_food_tw_order_qs = FoodOrder.objects.filter(
                status='5_PAID', 
                created_at__year=timezone.now().year,
                created_at__month=timezone.now().month, 
                restaurant_id=restaurant_id,
                takeway_order_type=takeway_order_type
            )
            current_month_total_order = this_month_food_tw_order_qs.count()
            this_month_takeway_order_type_payable_amount_list = this_month_food_tw_order_qs.values_list(
                'payable_amount', flat=True
            )
            this_month_takeway_order_type_amount = sum(this_month_takeway_order_type_payable_amount_list)
            this_month_total_takeway_order_type_distribution.append(
                {
                    'id': takeway_order_type, 
                    'name': takeway_order_type_name, 
                    'image': takeway_order_type_image,
                    'amount': Decimal(this_month_takeway_order_type_amount),
                    'total_order': current_month_total_order
                }
            )

            # Last month Takeway Order Report
            last_month_food_tw_order_qs = FoodOrder.objects.filter(
                status='5_PAID', 
                created_at__year=last_month.year,
                created_at__month=last_month.month,
                restaurant_id=restaurant_id,
                takeway_order_type=takeway_order_type
            )
            takeway_order_type_last_month_total_order = last_month_food_tw_order_qs.count()
            last_month_takeway_order_type_payable_amount_list = last_month_food_tw_order_qs.values_list(
                'payable_amount', flat=True
            )
            last_month_takeway_order_type_amount = sum(last_month_takeway_order_type_payable_amount_list)
            last_month_total_takeway_order_type_distribution.append(
                {
                    'id': takeway_order_type, 
                    'name': takeway_order_type_name, 
                    'image': takeway_order_type_image,
                    'amount': Decimal(last_month_takeway_order_type_amount),
                    'total_order': takeway_order_type_last_month_total_order
                }
            )

            # Weekly takeway Order Type Report
            first_day_of_week = start_of_week - timedelta(days=7)
            last_day_of_week = first_day_of_week + timedelta(days=6)

            weekly_tw_order_qs = FoodOrder.objects.filter(
                created_at__gte=first_day_of_week.date(),
                created_at__lte=last_day_of_week.date(), 
                status='5_PAID',
                restaurant_id=restaurant_id, 
                takeway_order_type=takeway_order_type
            )
            weekly_total_order = weekly_tw_order_qs.count()
            weekly_takeway_order_type_payable_amount_list = weekly_tw_order_qs.values_list(
                'payable_amount', flat=True
            )
            weekly_takeway_order_type_amount = sum(weekly_takeway_order_type_payable_amount_list)
            weekly_total_takeway_order_type_distribution.append(
                {
                    'id': takeway_order_type, 
                    'name': takeway_order_type_name, 
                    'image': takeway_order_type_image, 
                    'amount': Decimal(weekly_takeway_order_type_amount),
                    'total_order': weekly_total_order
                }
            )

            # Daily Takeway Order Type Report
            datetime_today = datetime.strptime(
                str(today.date()) + " 00:00:00", '%Y-%m-%d %H:%M:%S'
            )
            daily_tw_order_qs = FoodOrder.objects.filter(
                created_at__gte=datetime_today, 
                status='5_PAID',
                restaurant_id=restaurant_id, 
                takeway_order_type=takeway_order_type
            )
            daily_total_order = daily_tw_order_qs.count()
            daily_takeway_order_type_payable_amount_list = daily_tw_order_qs.values_list(
                'payable_amount', flat=True
            )
            daily_takeway_order_type_amount = sum(daily_takeway_order_type_payable_amount_list)
            daily_total_takeway_order_type_distribution.append(
                {
                    'id': takeway_order_type, 
                    'name': takeway_order_type_name, 
                    'image': takeway_order_type_image, 
                    'amount': Decimal(daily_takeway_order_type_amount),
                    'total_order': daily_total_order
                }
            )

        # assign to data nodes
        tw_report_data["total_amount_received_by_takeway_order_type"] = takeway_order_type_total_amount
        tw_report_data["current_month_total_takeway_order_type_distribution"] = this_month_total_takeway_order_type_distribution
        tw_report_data["last_month_total_takeway_order_type_distribution"] = last_month_total_takeway_order_type_distribution
        tw_report_data["weekly_total_takeway_order_type_distribution"] = weekly_total_takeway_order_type_distribution
        tw_report_data["daily_total_takeway_order_type_distribution"] = daily_total_takeway_order_type_distribution

        return tw_report_data

    def dashboard_total_report(self, request, restaurant_id, *args, **kwargs):
        # Set Decimal Precision
        # getcontext().prec = 3

        today = timezone.datetime.now()
        this_month = timezone.now().date().replace(day=1)

        last_month = (this_month - timedelta(days=1)).replace(day=1)

        week = 7
        weekly_day_wise_income_list = list()
        weekly_day_wise_order_list = list()

        for day in range(week):

            # start_of_week = today + timedelta(days=day + (today.weekday() - 1))
            day_int = (today.weekday() + 1) % 7
            start_of_week = today - timezone.timedelta(day_int-day)

            invoice_qs = Invoice.objects.filter(
                created_at__contains=start_of_week.date(), payment_status='1_PAID', restaurant_id=restaurant_id)
            total_list = invoice_qs.values_list('payable_amount', flat=True)
            # this_day_total_order = FoodOrder.objects.filter(
            #     created_at__contains=start_of_week.date(), status='5_PAID', restaurant_id=restaurant_id).count()

            this_day_total_order = Invoice.objects.filter(
                created_at__contains=start_of_week.date(), payment_status='1_PAID', restaurant_id=restaurant_id).count()

            this_day_total = round(sum(total_list), 2)
            weekly_day_wise_income_list.append(this_day_total)
            weekly_day_wise_order_list.append(this_day_total_order)

        this_month_invoice_qs = Invoice.objects.filter(
            created_at__year=timezone.now().year, created_at__month=timezone.now().month,
            payment_status='1_PAID', restaurant_id=restaurant_id)
        # this_month_order_qs = FoodOrder.objects.filter(
        #     created_at__year=timezone.now().year, created_at__month=timezone.now().month, status='5_PAID', restaurant_id=restaurant_id).count()
        this_month_order_qs = Invoice.objects.filter(
            created_at__year=timezone.now().year, created_at__month=timezone.now().month,
            payment_status='1_PAID', restaurant_id=restaurant_id).count()

        last_month_invoice_qs = Invoice.objects.filter(
            created_at__year=last_month.year, created_at__month=last_month.month, payment_status='1_PAID', restaurant_id=restaurant_id)
        # last_month_total_order = FoodOrder.objects.filter(
        #     created_at__year=last_month.year, created_at__month=last_month.month, status='5_PAID', restaurant_id=restaurant_id).count()

        last_month_total_order = Invoice.objects.filter(
            created_at__year=last_month.year, created_at__month=last_month.month, payment_status='1_PAID',
            restaurant_id=restaurant_id).count()


        all_months_upto_this_month = self.first_date_of_months_up_to_current_month_of_current_year()
        yearly_sales_report = {}
        month_wise_income = []
        month_wise_order = []
        payment_method_total_amount = []
        this_month_total_payment_method_distribution = []
        last_month_total_payment_method_distribution = []
        weekly_total_payment_method_distribution = []
        daily_total_payment_method_distribution = []

        for first_date in all_months_upto_this_month.values():
            month_name = first_date.strftime("%B")
            invoice_qs = Invoice.objects.filter(
                created_at__year=first_date.year, created_at__month=first_date.month, payment_status='1_PAID', restaurant_id=restaurant_id)
            payable_amount_list = invoice_qs.values_list(
                'payable_amount', flat=True)
            monthly_total_payable = round(sum(payable_amount_list), 2)
            # order_count = FoodOrder.objects.filter(
            #     created_at__year=first_date.year, created_at__month=first_date.month, status='5_PAID', restaurant_id=restaurant_id).count()

            order_count = Invoice.objects.filter(
                created_at__year=first_date.year, created_at__month=first_date.month, payment_status='1_PAID',
                restaurant_id=restaurant_id).count()

            yearly_sales_report[month_name] = {
                'total_payable_amount': monthly_total_payable, 'order_count': order_count}
            month_wise_income.append(monthly_total_payable)
            month_wise_order.append(order_count)
        if month_wise_order.__len__() < 12:
            remaining_month_count = 12-month_wise_order.__len__()
            for i in range(remaining_month_count):
                month_wise_income.append(0)
                month_wise_order.append(0)

        this_month_payable_amount_list = this_month_invoice_qs.values_list(
            'payable_amount', flat=True)
        this_month_total = sum(this_month_payable_amount_list)

        last_month_payable_amount_list = last_month_invoice_qs.values_list(
            'payable_amount', flat=True)
        last_month_total = sum(last_month_payable_amount_list)


        restaurant_qs = Restaurant.objects.filter(id = restaurant_id)
        # payment_method_list = restaurant_qs.values_list('payment_type', flat=True)
        payment_method_details_list = restaurant_qs.values_list('payment_type','payment_type__name')
        for payment_method, payment_method_name in payment_method_details_list:
            # order_qs = FoodOrder.objects.filter(payment_method =payment_method, restaurant_id = restaurant_id,
            #                                     status= '5_PAID')
            order_qs = Invoice.objects.filter(order__payment_method=payment_method, restaurant_id=restaurant_id,
                                                payment_status='1_PAID')
            total_order = order_qs.count()
            payment_method_payable_amount_list = order_qs.values_list('payable_amount', flat=True)
            payment_method_amount = round(sum(payment_method_payable_amount_list),2)
            payment_method_total_amount.append({'id': payment_method,'name':payment_method_name,
                                                'amount':payment_method_amount,
                                                'total_order': total_order})

            # this_month_food_order_qs = FoodOrder.objects.filter(status= '5_PAID', created_at__year=timezone.now().year,
            #                                                     created_at__month=timezone.now().month, restaurant_id = restaurant_id,
            #                                                     payment_method =payment_method)

            this_month_food_order_qs = Invoice.objects.filter(payment_status= '1_PAID', created_at__year=timezone.now().year,
                                                                created_at__month=timezone.now().month, restaurant_id = restaurant_id,
                                                                order__payment_method =payment_method)
            current_month_total_order = this_month_food_order_qs.count()
            this_month_payment_method_payable_amount_list = this_month_food_order_qs.values_list('payable_amount', flat=True)
            this_month_payment_method_amount = round(sum(this_month_payment_method_payable_amount_list),2)
            this_month_total_payment_method_distribution.append({'id': payment_method,'name':payment_method_name,
                                                'amount':this_month_payment_method_amount,
                                                'total_order': current_month_total_order}
                                                                )

            # last_month_food_order_qs = FoodOrder.objects.filter(status='5_PAID', created_at__year=last_month.year,
            #                                                     created_at__month=last_month.month,
            #                                                     restaurant_id=restaurant_id,
            #                                                     payment_method=payment_method)
            last_month_food_order_qs = Invoice.objects.filter(payment_status='1_PAID', created_at__year=last_month.year,
                                                                created_at__month=last_month.month,
                                                                restaurant_id=restaurant_id,
                                                                order__payment_method=payment_method)

            payment_method_last_month_total_order = last_month_food_order_qs.count()
            last_month_payment_method_payable_amount_list = last_month_food_order_qs.values_list('payable_amount',
                                                                                                 flat=True)
            last_month_payment_method_amount = round(sum(last_month_payment_method_payable_amount_list),2)
            last_month_total_payment_method_distribution.append({
                'id':payment_method, 'name':payment_method_name,
                'amount':last_month_payment_method_amount,
                 'total_order': payment_method_last_month_total_order})


            # for day in range(week):
            #     # start_of_week = today + timedelta(days=day + (today.weekday() - 1))
            #     day_int = (today.weekday() + 1) % 7
            #     first_day_of_week = today - timezone.timedelta(day_int - day)
            first_day_of_week = start_of_week- timedelta(days=7)
            last_day_of_week = first_day_of_week + timedelta(days=6)


            # weekly_order_qs = FoodOrder.objects.filter(
            #     created_at__gte=first_day_of_week.date(),
            #     created_at__lte = last_day_of_week.date(), status='5_PAID',
            #     restaurant_id=restaurant_id, payment_method = payment_method)


            weekly_order_qs = Invoice.objects.filter(
                created_at__gte=first_day_of_week.date(),
                created_at__lte = last_day_of_week.date(), payment_status='5_PAID',
                restaurant_id=restaurant_id, order__payment_method = payment_method)

            weekly_total_order = weekly_order_qs.count()
            weekly_payment_method_payable_amount_list = weekly_order_qs.values_list('payable_amount',
                                                                                             flat=True)
            weekly_payment_method_amount = round(sum(weekly_payment_method_payable_amount_list),2)
            weekly_total_payment_method_distribution.append(
                {'id':payment_method,'name':payment_method_name,'amount':weekly_payment_method_amount,
                 'total_order': weekly_total_order}
            )

            # Daily payment Type Report
            datetime_today = datetime.strptime(str(today.date()) + " 00:00:00", '%Y-%m-%d %H:%M:%S')
            # daily_order_qs = FoodOrder.objects.filter(
            #     created_at__gte=datetime_today,
            #     status='5_PAID',
            #     restaurant_id=restaurant_id,
            #     payment_method=payment_method
            # )
            daily_order_qs = Invoice.objects.filter(created_at__gte=datetime_today,
                payment_status='1_PAID',restaurant_id=restaurant_id,
                order__payment_method=payment_method
            )
            daily_total_order = daily_order_qs.count()
            daily_payment_method_payable_amount_list = daily_order_qs.values_list('payable_amount', flat=True)
            daily_payment_method_amount = sum(daily_payment_method_payable_amount_list)
            daily_total_payment_method_distribution.append(
                {
                    'id': payment_method, 
                    'name': payment_method_name, 
                    'amount': round(daily_payment_method_amount, 2),
                    'total_order': daily_total_order
                }
            )

        # Get takeway Order Type report
        takeway_order_type_report_data = self.get_takeway_order_type_report_data(restaurant_id=restaurant_id)


        return ResponseWrapper(
            data={
                'current_month_total_sell': round(this_month_total, 2),
                'current_month_total_order': this_month_order_qs,
                'last_month_total_sell': round(last_month_total, 2),
                'last_month_total_order': last_month_total_order,
                'week_data': {"day_wise_income": weekly_day_wise_income_list, "day_wise_order": weekly_day_wise_order_list},
                #  "yearly_sales_report": yearly_sales_report,
                'payment_method_distribution':{
                    'total_amount_received_by_payment_method': payment_method_total_amount,
                    'current_month_total_payment_method_distribution':this_month_total_payment_method_distribution,
                    'last_month_total_payment_method_distribution':last_month_total_payment_method_distribution,
                    'weekly_total_payment_method_distribution':weekly_total_payment_method_distribution,
                    'daily_total_payment_method_distribution': daily_total_payment_method_distribution
                },
                'takeway_order_type_distribution': {
                    'total_amount_received_by_takeway_order_type': takeway_order_type_report_data.get("total_amount_received_by_takeway_order_type", None),
                    'current_month_total_takeway_order_type_distribution': takeway_order_type_report_data.get("current_month_total_takeway_order_type_distribution", None),
                    'last_month_total_takeway_order_type_distribution': takeway_order_type_report_data.get("last_month_total_takeway_order_type_distribution", None),
                    'weekly_total_takeway_order_type_distribution': takeway_order_type_report_data.get("weekly_total_takeway_order_type_distribution", None),
                    'daily_total_takeway_order_type_distribution': takeway_order_type_report_data.get("daily_total_takeway_order_type_distribution", None),
                },
                "month_data": {"month_wise_income": month_wise_income, "month_wise_order": month_wise_order}
            },
            msg="success"
        )

    def get_dashboard_daily_report(self, request, restaurant_id, *args, **kwargs):

        # define daily report data schema
        daily_report_data_schema = {
            "payment_method_summary": {},
            "dining_order_summary": {},
            "takeway_order_summary": {},
            "takeway_order_details_summary": {}
        }

        today = timezone.datetime.now()
        # (******* Uncomment after testing *******)
        datetime_today = datetime.strptime(str(today.date()) + " 00:00:00", '%Y-%m-%d %H:%M:%S')
        # tester datetime today (******* Comment after after testing *******)
        # datetime_today = datetime.strptime("2021-03-01" + " 00:00:00", '%Y-%m-%d %H:%M:%S')

        # check validity of restaurant
        restaurant_qs = Restaurant.objects.filter(id=restaurant_id)
        if restaurant_qs.exists():
            # grab the restaurant object
            restaurant = restaurant_qs.last()

            # invoice filter
            invoice_qs = Invoice.objects.filter(
                created_at__gte=datetime_today, payment_status__iexact="1_PAID", restaurant_id=restaurant_id
            )

            # ------- Overall Order Summary -------
            total_order_count_overall = invoice_qs.count()
            payable_amount_overall = sum(invoice_qs.values_list('payable_amount', flat=True))
            tax_overall = sum(invoice_qs.values_list('order__tax_amount', flat=True))
            discount_overall = sum(invoice_qs.values_list('order__discount_amount', flat=True))
            # => assign to data schema
            daily_report_data_schema["total_order"] = total_order_count_overall
            daily_report_data_schema["total_sell"] = round(payable_amount_overall, 2)
            daily_report_data_schema["total_tax"] = round(tax_overall, 2)
            daily_report_data_schema["total_discount"] = round(discount_overall, 2)

            # ------- Payment Method Summary -------
            payment_method_details_list = restaurant_qs.values_list('payment_type', 'payment_type__name')

            for payment_method, payment_method_name in payment_method_details_list:
                order_invoice_qs = Invoice.objects.filter(
                    order__payment_method=payment_method, restaurant_id=restaurant_id, payment_status__iexact="1_PAID", created_at__gte=datetime_today
                )
                payment_method_total_order = order_invoice_qs.count()
                payment_method_amount = sum(order_invoice_qs.values_list('payable_amount', flat=True))
                payment_method_total_tax = sum(order_invoice_qs.values_list("order__tax_amount", flat=True))
                payment_method_total_discount = sum(order_invoice_qs.values_list("order__discount_amount", flat=True))
                payment_method_sell_percentage = (payment_method_amount / payable_amount_overall) * 100
                # => assign to data schema
                daily_report_data_schema["payment_method_summary"][payment_method_name] = {
                    "total_order": payment_method_total_order,
                    "total_sell": round(payment_method_amount, 2),
                    "total_tax": round(payment_method_total_tax, 2),
                    "total_discount": round(payment_method_total_discount, 2),
                    "sell_percentage": round(payment_method_sell_percentage, 2)
                }

            # ------- Dining Order Summary -------
            dining_invoice_qs = Invoice.objects.filter(
                ~Q(order__table=None),
                Q(payment_status__iexact="1_PAID", restaurant_id=restaurant_id, created_at__gte=datetime_today
            ))
            dining_total_order = dining_invoice_qs.count()
            dining_total_sell = sum(dining_invoice_qs.values_list("payable_amount", flat=True))
            dining_total_tax = sum(dining_invoice_qs.values_list("order__tax_amount", flat=True))
            dining_total_discount = sum(dining_invoice_qs.values_list("order__discount_amount", flat=True))
            dining_total_sell_percentage = (dining_total_sell / payable_amount_overall) * 100
            # => assign to data schema
            daily_report_data_schema["dining_order_summary"] = {
                "total_order": dining_total_order,
                "total_sell": round(dining_total_sell, 2),
                "total_tax": round(dining_total_tax, 2),
                "total_discount": round(dining_total_discount, 2),
                "sell_percentage": round(dining_total_sell_percentage, 2)
            }
            
            # ------- Takeway Order Summary -------
            takeway_invoice_qs = Invoice.objects.filter(
                Q(order__table=None),
                Q(payment_status__iexact="1_PAID", restaurant_id=restaurant_id, created_at__gte=datetime_today
            ))
            takeway_total_order = takeway_invoice_qs.count()
            takeway_total_sell = sum(takeway_invoice_qs.values_list("payable_amount", flat=True))
            takeway_total_tax = sum(takeway_invoice_qs.values_list("order__tax_amount", flat=True))
            takeway_total_discount = sum(takeway_invoice_qs.values_list("order__discount_amount", flat=True))
            takeway_total_sell_percentage = (takeway_total_sell / payable_amount_overall) * 100
            # => assign to data schema
            daily_report_data_schema["takeway_order_summary"] = {
                "total_order": takeway_total_order,
                "total_sell": round(takeway_total_sell, 2),
                "total_tax": round(takeway_total_tax, 2),
                "total_discount": round(takeway_total_discount, 2),
                "sell_percentage": round(takeway_total_sell_percentage, 2)
            }

            # ------- Takeway Order Details Summary -------
            takeway_order_type_details_list = restaurant_qs.values_list(
                'takeway_order_type', 'takeway_order_type__name'
            )

            for takeway_order_type, takeway_order_type_name in takeway_order_type_details_list:
                takeway_order_type_invoice_qs = takeway_invoice_qs.filter(
                    order__takeway_order_type=takeway_order_type
                )
                takeway_order_type_total_order = takeway_order_type_invoice_qs.count()
                takeway_order_type_amount = sum(takeway_order_type_invoice_qs.values_list('payable_amount', flat=True))
                takeway_order_type_total_tax = sum(takeway_order_type_invoice_qs.values_list("order__tax_amount", flat=True))
                takeway_order_type_total_discount = sum(takeway_order_type_invoice_qs.values_list("order__discount_amount", flat=True))
                takeway_order_type_sell_percentage = (takeway_order_type_amount / payable_amount_overall) * 100
                # => assign to data schema
                daily_report_data_schema["takeway_order_details_summary"][takeway_order_type_name] = {
                    "total_order": takeway_order_type_total_order,
                    "total_sell": round(takeway_order_type_amount, 2),
                    "total_tax": round(takeway_order_type_total_tax, 2),
                    "total_discount": round(takeway_order_type_total_discount, 2),
                    "sell_percentage": round(takeway_order_type_sell_percentage, 2)
                }

            return ResponseWrapper(data=daily_report_data_schema, msg="success")
        else:
            return ResponseWrapper(error_msg="Invalid Restaurant ID", error_code=400)

    def waiter_served_report(self, request, waiter_id, *args, **kwargs):

        waiter_qs = HotelStaffInformation.objects.filter(id=waiter_id).first()
        if not waiter_qs:
            return ResponseWrapper(msg=['You are not a staff'])
        restaurant_id = waiter_qs.restaurant_id
        self.check_object_permissions(request, obj=restaurant_id)
        today = timezone.now().date()
        before_thirty_day = today - timedelta(days=30)
        today += timedelta(days=1)

        # staff_order_log_qs = FoodOrderLog.objects.filter(
        #     staff_id=waiter_qs.pk, order__status='5_PAID', created_at__gte=before_thirty_day, created_at__lte=today)

        staff_order_log_qs = waiter_qs.actor_actions.filter(actor_object_id=waiter_qs.pk, verb='5_PAID',
                                                            timestamp__gte=before_thirty_day, timestamp__lte=today)
        serializer = ServedOrderSerializer(
            instance=staff_order_log_qs, many=True)
        return ResponseWrapper(data=serializer.data, msg='success')

    def waiter_cancel_report(self, request, waiter_id, *args, **kwargs):

        waiter_qs = HotelStaffInformation.objects.filter(id=waiter_id).first()
        if not waiter_qs:
            return ResponseWrapper(msg=['You are not a staff'])
        restaurant_id = waiter_qs.restaurant_id
        self.check_object_permissions(request, obj=restaurant_id)
        today = timezone.now().date()
        before_thirty_day = today - timedelta(days=30)
        today += timedelta(days=1)

        # staff_order_log_qs = FoodOrderLog.objects.filter(
        #     staff_id=waiter_qs.pk, order__status='6_CANCELLED', created_at__gte=before_thirty_day, created_at__lte=today)

        staff_order_log_qs = waiter_qs.actor_actions.filter(actor_object_id=waiter_qs.pk, verb='6_CANCELLED',
                                                            timestamp__gte=before_thirty_day, timestamp__lte=today)

        serializer = ServedOrderSerializer(
            instance=staff_order_log_qs, many=True)
        return ResponseWrapper(data=serializer.data, msg='success')

    def admin_all_report(self, request, *args, **kwargs):
       # today = timezone.datetime.now()
        this_month = timezone.datetime.now().month
        total_restaurant = Restaurant.objects.all().count()
        total_order = FoodOrder.objects.filter(status='5_PAID').count()
        total_cancel_order = FoodOrder.objects.filter(
            status='6_CANCELLED').count()
        total_invoice_qs = Invoice.objects.filter(payment_status='1_PAID')
        total_payable_amount_list = total_invoice_qs.values_list(
            'payable_amount', flat=True)
        total_amaount = sum(total_payable_amount_list)
        this_month_total_restaurant = Restaurant.objects.filter(
            created_at__month=this_month).count()
        this_month_total_order = FoodOrder.objects.filter(
            status='5_PAID', created_at__month=this_month).count()
        this_month_cancel_order = FoodOrder.objects.filter(
            status='6_CANCELLED', created_at__month=this_month).count()
        this_month_total_invoice_qs = Invoice.objects.filter(
            created_at__month=this_month, payment_status='1_PAID')
        this_month_total_payable_amount_list = this_month_total_invoice_qs.values_list(
            'payable_amount', flat=True)
        this_month_total_amaount = sum(this_month_total_payable_amount_list)

        return ResponseWrapper(data={'total_restaurant': total_restaurant,
                                     'total_order': total_order,
                                     'total_cancel_order': total_cancel_order,
                                     'total_amaount': total_amaount,
                                     'this_month_total_restaurant': this_month_total_restaurant,
                                     'this_month_total_order': this_month_total_order,
                                     'this_month_cancel_order': this_month_cancel_order,
                                     'this_month_total_amaount': this_month_total_amaount,
                                     }, msg="success")

    def month_wise_total_report(self, request, restaurant_id, *args, **kwargs):
        today = timezone.datetime.now()
        this_month = timezone.datetime.now().month

        months = 12
        monthly_wise_income_list = list()
        monthly_wise_order_list = list()

        for month in range(months):
            # start_of_month = today + timedelta(days=month + (today.weekday() - 1))
            month_qs = (this_month + 1) % 12
            start_of_month = this_month - timezone.timedelta(month_qs-month)

            invoice_qs = Invoice.objects.filter(
                created_at__contains=start_of_month.date(), payment_status='1_PAID', restaurant_id=restaurant_id)
            total_list = invoice_qs.values_list('payable_amount', flat=True)
            this_month_total_order = FoodOrder.objects.filter(
                created_at__contains=start_of_month.date(), status='5_PAID', restaurant_id=restaurant_id).count()

            this_month_total = sum(total_list)
            monthly_wise_income_list.append(this_month_total)
            monthly_wise_order_list.append(monthly_wise_order_list)

        return ResponseWrapper(data={'total_restaurant': monthly_wise_income_list,
                                     'total_order': this_month_total_order,
                                     }, msg="success")


class InvoiceViewSet(LoggingMixin, CustomViewSet):
    serializer_class = InvoiceSerializer
    # pagination_class = CustomLimitPagination

    def get_serializer_class(self):
        if self.action in ['invoice_history']:
            self.serializer_class = InvoiceSerializer
        elif self.action in ['invoice_all_report', 'top_food_items_by_date_range', 'generate_datewise_filtered_report_pdf']:
            self.serializer_class = ReportByDateRangeSerializer
        elif self.action in ['waiter_report_by_date_range']:
            self.serializer_class = ReportDateRangeSerializer
        return self.serializer_class

    def get_pagination_class(self):
        if self.action in ['invoice_history', 'paid_cancel_invoice_history', 'invoice', 'invoice_all_report', 'top_food_items_by_date_range', 'waiter_report_by_date_range']:
            return CustomLimitPagination
        elif self.action in ['generate_datewise_filtered_report_pdf']:
            return CustomLimitPagination
        else:
            return None

    queryset = Invoice.objects.all()
    lookup_field = 'pk'
    logging_methods = ['GET', 'POST', 'PATCH', 'DELETE']
    pagination_class = property(get_pagination_class)

    def generate_datewise_filtered_report_pdf(self, request, restaurant_id, *args, **kwargs):
        template_path = 'report/report-pdf.html'
        today = timezone.datetime.now()
        datetime_str = today.strftime("%Y%m%d%H%M%S")
        target_filename = f"report_{datetime_str}.pdf"

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{target_filename}"'

        report_data = self.invoice_all_report(request=request, restaurant=restaurant_id, getOnlyData=True)

        # print(report_data, "\n Report Data XXXXXXXXXXXXXXXXXXXXX")

        html = render_to_string(template_path, {'report_data': report_data})
        # print(html)

        pisaStatus = pisa.CreatePDF(html, dest=response)

        # return ResponseWrapper(data=response, msg='success')
        return response

    # @swagger_auto_schema(
    #     request_body=ReportByDateRangeSerializer
    # )
    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter("limit", openapi.IN_QUERY,
                          type=openapi.TYPE_INTEGER),
        openapi.Parameter("offset", openapi.IN_QUERY,
                          type=openapi.TYPE_INTEGER)
    ])
    def waiter_report_by_date_range(self, request, restaurant, *args, **kwargs):
        start_date = request.data.get('start_date', timezone.now().date())
        end_date = request.data.get('end_date', timezone.now().date())
        if request.data.get('end_date'):
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        end_date += timedelta(days=1)
        food_order_qs = FoodOrder.objects.filter(
            restaurant_id=restaurant, status="5_PAID")
        order_log_qs = FoodOrderLog.objects.filter(order__restaurant_id=restaurant,
                                                   created_at__gte=start_date, created_at__lte=end_date
                                                   ).distinct()

        food_qs_id_list = list(food_order_qs.values_list('pk', flat=True))

        food_order_action_qs = Action.objects.filter(action_object_content_type__model='foodorder',
                                                     action_object_object_id__in=food_qs_id_list, timestamp__gte=start_date, timestamp__lte=end_date)
        staff_list = HotelStaffInformation.objects.filter(restaurant=restaurant, is_waiter=True).values_list("pk",
                                                                                                             flat=True).distinct()

        total_waiter = staff_list.__len__()
        total_payable_amount = food_order_qs.values_list(
            'payable_amount', flat=True)
        total_amount = round(sum(total_payable_amount), 2)
        staff_report_list = list()
        for staff in staff_list:
            temp_food_order_action_qs = food_order_action_qs.filter(
                actor_object_id=staff)
            allowed_order_id_list = list(temp_food_order_action_qs.values_list(
                'action_object_object_id', flat=True))
            payment_amount_list = food_order_qs.filter(
                pk__in=allowed_order_id_list).values_list('payable_amount', flat=True)
            total_payment_amount = round(sum(payment_amount_list), 2)
            staff_qs = HotelStaffInformation.objects.filter(pk=staff).first()
            staff_serializer = StaffInfoGetSerializer(instance=staff_qs)
            staff_report_dict = {
                'total_payment_amount': total_payment_amount,
                'staff_info': staff_serializer.data,
                'total_served_order': allowed_order_id_list.__len__(),
            }
            staff_report_list.append(staff_report_dict)

        staff_report_desc_sorted = sorted(staff_report_list,
                                          key=lambda i: i['total_served_order'], reverse=True)

        page_qs = self.paginate_queryset(staff_report_desc_sorted)
        # paginated_data = self.get_paginated_response(page_qs)
        staff_report_details = dict(self.get_paginated_response(page_qs).data)
        staff_report_details['total_waiter'] = total_waiter
        staff_report_details['total_amaount'] = total_amount

        return ResponseWrapper(data=staff_report_details)

 
    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter("limit", openapi.IN_QUERY,
                          type=openapi.TYPE_INTEGER),
        openapi.Parameter("offset", openapi.IN_QUERY,
                          type=openapi.TYPE_INTEGER)
    ])
    def invoice_all_report(self, request=None, restaurant=None, getOnlyData=False, *args, **kwargs):
        start_date = request.data.get('start_date', timezone.now().date())
        end_date = request.data.get('end_date', timezone.now().date())
        category_list = request.data.get("category", [])
        item_list = request.data.get('item', [])
        waiter_list = request.data.get('waiter', [])
        # start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if request.data.get('end_date'):
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        end_date += timedelta(days=1)
        if item_list:
            food_items_date_range_qs = Invoice.objects.filter(Q(order__ordered_items__status='3_IN_TABLE') & Q(order__ordered_items__food_option__food_id__in=item_list), restaurant_id=restaurant,
                                                              created_at__gte=start_date, created_at__lte=end_date,payment_status='1_PAID').order_by('-created_at').distinct()
        elif category_list:
            food_items_date_range_qs = Invoice.objects.filter(restaurant_id=restaurant,
                                                              created_at__gte=start_date, created_at__lte=end_date,
                                                              order__ordered_items__food_option__food__category_id__in=category_list,
                                                              payment_status='1_PAID'
                                                              ).order_by('-created_at').distinct()
        elif waiter_list:
            food_items_date_range_qs = Invoice.objects.filter(order__restaurant_id=restaurant, created_at__gte=start_date, created_at__lte=end_date,
                                                              order__food_order_logs__staff_id__in=waiter_list,payment_status='1_PAID'
                                                              ).order_by('-created_at').distinct()
        else:
            food_items_date_range_qs = Invoice.objects.filter(restaurant_id=restaurant,
                                                              created_at__gte=start_date, created_at__lte=end_date,
                                                              payment_status='1_PAID'
                                                              ).order_by('-created_at').distinct()

        total_order = food_items_date_range_qs.count()
        total_payable_amount = food_items_date_range_qs.values_list(
            'payable_amount', flat=True
        )

        total_amaount = sum(total_payable_amount)


        if getOnlyData == True:
            restaurant_qs = Restaurant.objects.filter(
                id=restaurant
            )
            restaurant_name = "Undefined"
            if restaurant_qs.exists():
                restaurant_name = restaurant_qs.last().name
            result = {
                "RestaurantName": restaurant_name,
                "FilterKeysData": {
                    "StartDate": start_date,
                    "EndDate": end_date.strftime("%Y-%m-%d"),
                    "CategoryList": category_list,
                    "ItemList": item_list,
                    "WaiterList": waiter_list
                },
                "ReportObjectList": food_items_date_range_qs,
                "TotalAmount": round(total_amaount, 2),
                "TotalOrder": total_order
            }

            return result
        else:
            
            page_qs = self.paginate_queryset(food_items_date_range_qs)

            serializer = InvoiceSerializer(instance=page_qs, many=True)
            paginated_data = self.get_paginated_response(serializer.data)
            order_details = dict(self.get_paginated_response(serializer.data).data)

            order_details['total_amaount'] = round(total_amaount, 2)
            order_details['total_order'] = total_order

            return ResponseWrapper(data=order_details)

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter("limit", openapi.IN_QUERY,
                          type=openapi.TYPE_INTEGER),
        openapi.Parameter("offset", openapi.IN_QUERY,
                          type=openapi.TYPE_INTEGER)
    ])
    def top_food_items_by_date_range(self, request, restaurant_id, *args, **kwargs):
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        category_list = request.data.get("category", [])
        item_list = request.data.get('item', [])

        if request.data.get('end_date'):
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        end_date += timedelta(days=1)

        # food_items_date_range_qs = Invoice.objects.filter(restaurant_id=restaurant_id,
        #                                                   created_at__gte=start_date, created_at__lte=end_date,
        #                                                   payment_status='1_PAID')
        #
        if item_list:
            food_items_date_range_qs = Invoice.objects.filter(Q(order__ordered_items__status='3_IN_TABLE') & Q(order__ordered_items__food_option__food_id__in=item_list), restaurant_id=restaurant_id,
                                                              created_at__gte=start_date, created_at__lte=end_date).distinct()
        elif category_list:
            food_items_date_range_qs = Invoice.objects.filter(restaurant_id=restaurant_id,
                                                              created_at__gte=start_date, created_at__lte=end_date,
                                                              order__ordered_items__food_option__food__category_id__in=category_list
                                                              ).distinct()
        else:
            food_items_date_range_qs = Invoice.objects.filter(restaurant_id=restaurant_id,
                                                              created_at__gte=start_date, created_at__lte=end_date
                                                              ).distinct()

        order_items_list = food_items_date_range_qs.values_list(
            'order_info__ordered_items', flat=True)
        food_dict = {}
        food_report_list = []
        food_option_report = {}
        food_extra_report = {}

        for items_per_invoice in order_items_list:
            for item in items_per_invoice:

                food_id = item.get("food_option", {}).get("food")
                if (not food_id) or (not item.get('status') == "3_IN_TABLE"):
                    continue

                name = item.get('food_name')
                price = item.get('price', 0)
                quantity = item.get('quantity', 0)

                if not food_dict.get(food_id):
                    food_dict[food_id] = {}

                if not food_dict.get(food_id, {}).get(name):
                    food_dict[food_id]['name'] = name

                if not food_dict.get(food_id, {}).get(price):
                    food_dict[food_id]['price'] = price
                else:
                    food_dict[food_id]['price'] += price

                if not food_dict.get(food_id, {}).get(quantity):
                    food_dict[food_id]['quantity'] = quantity
                else:
                    food_dict[food_id]['quantity'] += quantity
                # food_option_report[food_id]['food_option_report'] = food_option
                # food_option_report[food_id]['food_extra'] = food_extra_name

                # calculation of food option

                food_option_name = item.get("food_option", {}).get("name")
                food_option_id = item.get("food_option", {}).get("id")

                if food_option_id and food_option_name:
                    if not food_dict.get(food_id, {}).get('food_option'):
                        food_dict[food_id]['food_option'] = {}
                    if not food_dict.get(food_id, {}).get('food_option', {}).get(food_option_id):
                        food_dict[food_id]['food_option'][food_option_id] = {
                            'name': food_option_name, 'quantity': quantity}
                    else:
                        food_dict[food_id]['food_option'][food_option_id]['quantity'] += quantity

                # calculation of food extra

                food_extra_list = item.get('food_extra', [])

                for food_extra in food_extra_list:
                    food_extra_name = food_extra.get("name")
                    food_extra_id = food_extra.get("id")

                    if food_extra_id and food_extra_name:
                        if not food_dict.get(food_id, {}).get('food_extra'):
                            food_dict[food_id]['food_extra'] = {}
                        if not food_dict.get(food_id, {}).get("food_extra", {}).get(food_extra_id):
                            food_dict[food_id]["food_extra"][food_extra_id] = {
                                'name': food_extra_name, 'quantity': quantity}
                        else:
                            food_dict[food_id]["food_extra"][food_extra_id]['quantity'] += quantity

        for item in food_dict.values():
            if item.get('food_extra', {}):
                item['food_extra'] = item.get('food_extra', {}).values()

            if item.get('food_option', {}):
                item['food_option'] = item.get('food_option', {}).values()
        response_data_list = food_dict.values()

        response_data_desc_sorted = sorted(response_data_list,
                                           key=lambda i: i['quantity'], reverse=True)

        page_qs = self.paginate_queryset(response_data_desc_sorted)

        paginated_data = self.get_paginated_response(page_qs)
        return ResponseWrapper(paginated_data.data)

        # return ResponseWrapper(data=response_data_desc_sorted, msg='success')

    def invoice_history(self, request, restaurant, *args, **kwargs):
        invoice_qs = Invoice.objects.filter(
            restaurant_id=restaurant).order_by('-updated_at')
        page_qs = self.paginate_queryset(invoice_qs)

        serializer = InvoiceSerializer(instance=page_qs, many=True)
        paginated_data = self.get_paginated_response(serializer.data)

        return ResponseWrapper(paginated_data.data)

    def paid_cancel_invoice_history(self, request, restaurant, *args, **kwargs):
        invoice_qs = Invoice.objects.filter(restaurant_id=restaurant, order__status__in=[
            '5_PAID', '6_CANCELLED']).order_by('-updated_at')
        page_qs = self.paginate_queryset(invoice_qs)
        serializer = InvoiceSerializer(instance=page_qs, many=True)
        paginated_data = self.get_paginated_response(serializer.data)

        return ResponseWrapper(paginated_data.data)

    def order_invoice(self, request, order_id, *args, **kwargs):
        qs = Invoice.objects.filter(order_id=order_id).last()
        serializer = InvoiceSerializer(instance=qs, many=False)
        return ResponseWrapper(data=serializer.data)

    def invoice(self, request, invoice_id, *args, **kwargs):
        invoice_qs = Invoice.objects.filter(
            pk__icontains=invoice_id).order_by('-updated_at')
        page_qs = self.paginate_queryset(invoice_qs)

        serializer = InvoiceSerializer(instance=page_qs, many=True)
        paginated_data = self.get_paginated_response(serializer.data)

        return ResponseWrapper(paginated_data.data)


class DiscountViewSet(LoggingMixin, CustomViewSet):
    serializer_class = DiscountSerializer

    def get_serializer_class(self):
        if self.action in ['create_discount', 'update_discount']:
            self.serializer_class = DiscountPostSerializer
        if self.action in ['retrieve']:
            self.serializer_class = DiscountSerializer
        elif self.action in ['food_discount']:
            self.serializer_class = DiscountByFoodSerializer
        elif self.action in ['force_discount']:
            self.serializer_class = ForceDiscountSerializer

        return self.serializer_class

    def get_permissions(self):
        permission_classes = []
        if self.action in ['discount_delete', 'delete_discount', 'create_discount','update_discount','discount_list']:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['force_discount']:
            permission_classes = [
                custom_permissions.IsRestaurantManagementOrAdmin]

        # else:
        #     permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    def get_pagination_class(self):
        if self.action in ['discount_list', 'all_discount_list']:

            return CustomLimitPagination

    queryset = Discount.objects.all()
    lookup_field = 'pk'
    logging_methods = ['GET', 'POST', 'PATCH']
    http_method_names = ['post', 'patch', 'get', 'delete']
    pagination_class = property(get_pagination_class)

    def discount_list(self, request, restaurant, *args, **kwargs):
        discount_qs = Discount.objects.filter(restaurant_id=restaurant)
        page_qs = self.paginate_queryset(discount_qs)

        serializer = DiscountSerializer(instance=page_qs, many=True)
        paginated_data = self.get_paginated_response(serializer.data)

        return ResponseWrapper(paginated_data.data)

    def pop_up_list_by_restaurant(self, request, restaurant_id, *args, **kwargs):
        today = timezone.datetime.now().date()
        start_date = today - timedelta(days=1)
        current_time = timezone.now()
        discount_qs = Discount.objects.filter(Q(restaurant_id=restaurant_id, is_popup=True,
                                              start_date__lte=today, end_date__gte=today,
                                              discount_schedule_type='Date_wise') | Q(restaurant_id = restaurant_id,is_popup=True,
                                                                                      discount_slot_closing_time__gte=current_time,
                                                                                      discount_slot_start_time__lte=current_time,
                                                                                      discount_schedule_type='Time_wise')).exclude(food=None, image=None)
        # time_wise_discount_qs = Discount.objects.filter(restaurant_id=restaurant_id,
        #                                                 discount_slot_closing_time__gte=current_time,
        #                                                 discount_slot_start_time__lte=current_time,
        #                                                 discount_schedule_type='Time_wise').exclude(food=None)

        serializer = DiscountPopUpSerializer(instance=discount_qs, many=True)
        return ResponseWrapper(data=serializer.data, msg='success')

    def all_discount_list(self, request, *args, **kwargs):
        discount_qs = Discount.objects.all()
        page_qs = self.paginate_queryset(discount_qs)

        serializer = DiscountSerializer(instance=page_qs, many=True)
        paginated_data = self.get_paginated_response(serializer.data)

        return ResponseWrapper(paginated_data.data)

    def discount(self, request, pk, *args, **kwargs):
        qs = Discount.objects.filter(id=pk)
        serializer = DiscountSerializer(instance=qs, many=True)
        return ResponseWrapper(data=serializer.data)

    def create_discount(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)
        if not request.data:
            return ResponseWrapper(error_code=400, error_msg='empty request body')

        restaurant_id = request.data.get('restaurant')
        food = request.data.get('food')
        if not HotelStaffInformation.objects.filter(Q(is_manager=True) | Q(is_owner=True), user=request.user.pk,
                                                    restaurant_id=restaurant_id):
            return ResponseWrapper(error_code=status.HTTP_401_UNAUTHORIZED, error_msg='user is not manager or owner')
        is_popup = request.data.get('is_popup')
        is_slider = request.data.get('is_slider')
        if is_popup or is_slider:
            if not food:
                return ResponseWrapper(error_msg=['Food is required'], status=404)

        qs = serializer.save()

        # food_id_lists = request.data.get('food_id_list')
        # if food_id_lists:
        #     for food_id_list in food_id_lists:
        #         food_qs = Food.objects.filter(pk=food_id_list)
        #         food_qs.update(discount=qs.id)

        if food:
            food_qs = Food.objects.filter(pk=food)
            food_qs.update(discount=qs.id)

        serializer = self.get_serializer(instance=qs)
        return ResponseWrapper(data=serializer.data, msg='created')

    def food_discount(self, request,  *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

        food_qs = Food.objects.filter(pk__in=request.data.get('food_id_lists'))
        if not food_qs:
            return ResponseWrapper(error_msg=['Food is invalid'], error_code=400)
        discount_qs = Discount.objects.filter(
            pk=request.data.get('discount_id')).first()
        if not discount_qs:
            return ResponseWrapper(error_msg=['Discount is invalid'], error_code=400)

        updated = food_qs.update(discount_id=discount_qs)
        if not updated:
            return ResponseWrapper(error_msg=['Food Discount is not update'], error_code=400)

        serializer = FoodDetailsByDiscountSerializer(
            instance=updated)

        return ResponseWrapper(data=serializer.data, msg='success')

    def update_discount(self, request, pk, **kwargs):
        serializer = self.get_serializer(data=request.data, partial=True)

        if not serializer.is_valid():
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)
        if not request.data:
            return ResponseWrapper(error_code=400, error_msg='empty request body')
        discount_qs=Discount.objects.filter(pk=pk).last()

        restaurant_id = discount_qs.restaurant
        if not HotelStaffInformation.objects.filter(Q(is_manager=True) | Q(is_owner=True), user=request.user.pk,
                                                    restaurant_id=restaurant_id):
            return ResponseWrapper(error_code=status.HTTP_401_UNAUTHORIZED, error_msg=['user is not manager or owner'])
        food_id_list = request.data.get('food_id_list')
        food_id = request.data.get('food')

        if food_id_list:
            food_qs = Food.objects.filter(pk__in=request.data.get('food_id_list')).first().restaurant

            if food_qs != restaurant_id:
                return ResponseWrapper(error_msg=['Food is not Valid'], status=400)

        if food_id:
            food_qs = Food.objects.filter(pk=request.data.get('food')).first().restaurant

            if food_qs != restaurant_id:
                return ResponseWrapper(error_msg=['Food is not Valid'], status=400)

        if serializer.is_valid():
            qs = serializer.update(instance=self.get_object(
            ), validated_data=serializer.validated_data)
            serializer = DiscountSerializer(instance=qs)
            return ResponseWrapper(data=serializer.data, msg="success")
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def delete_discount(self, request, discount_id, *args, **kwargs):
        discount_qs = Discount.objects.filter(id=discount_id)
        restaurant_id = discount_qs.first().restaurant_id
        qs = HotelStaffInformation.objects.filter(Q(is_manager=True) | Q(
            is_owner=True), user=request.user.pk, restaurant=restaurant_id)
        if qs:
            discount_qs.delete()
            return ResponseWrapper(status=200, msg='deleted')
        else:
            return ResponseWrapper(error_msg="failed to delete", error_code=400)
    def force_discount(self, request, order_id, *args, **kwargs):
        qs = FoodOrder.objects.filter(pk = order_id).last()
        if not qs:
            return ResponseWrapper(error_msg=['Food order is not valid'], error_code=400)

        if qs.applied_promo_code:
            return ResponseWrapper(error_msg= 'Promo code is already applied',error_code=400)
        discount_given = request.data.get('force_discount_amount')
        discount_amount_is_percentage = request.data.get('discount_amount_is_percentage')
        if discount_given <0:
            return ResponseWrapper(error_msg=['Discount amount is not valid'], error_code=400)
        if discount_given > qs.payable_amount:
            return ResponseWrapper(error_msg=['Discount amount is grater then payable amount'], error_code=400)
        if discount_amount_is_percentage == True and discount_given > 100:
            return ResponseWrapper(error_msg=['Discount Amount is must less then 100'], error_code=400)

        discount_amount_is_percentage = request.data.get('discount_amount_is_percentage')
        qs.discount_given = discount_given
        qs.discount_amount_is_percentage = discount_amount_is_percentage
        qs.save
        serializer = FoodOrderByTableSerializer(instance=qs)
        return ResponseWrapper(data=serializer.data, msg='success')





class FcmCommunication(viewsets.GenericViewSet):
    serializer_class = StaffFcmSerializer

    def get_serializer_class(self):
        if self.action in ['call_waiter']:
            self.serializer_class = StaffFcmSerializer
        elif self.action in ['collect_payment']:
            self.serializer_class = CollectPaymentSerializer

        return self.serializer_class

    def call_waiter(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

        table_id = request.data.get('table_id')
        table_qs = Table.objects.filter(pk=table_id).first()
        if not table_qs:
            return ResponseWrapper(error_msg=["no table found with this table id"], error_code=status.HTTP_404_NOT_FOUND)

        staff_fcm_device_qs = StaffFcmDevice.objects.filter(
            hotel_staff__tables=table_id)
        staff_id_list = staff_fcm_device_qs.values_list(
            'pk', flat=True)
        if send_fcm_push_notification_appointment(
            tokens_list=list(staff_fcm_device_qs.values_list(
                'token', flat=True)),
                table_no=table_qs.table_no if table_qs else None,
                status="CallStaff",
                staff_id_list=staff_id_list,
        ):
            return ResponseWrapper(msg='Success')
        else:
            return ResponseWrapper(error_msg=["failed to notify"], error_code=400)

    def collect_payment(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

        table_id = request.data.get('table_id')
        payment_method = request.data.get('payment_method')
        table_qs = Table.objects.filter(pk=table_id).first()
        if not table_qs:
            return ResponseWrapper(error_msg=["no table found with this table id"], error_code=status.HTTP_404_NOT_FOUND)
        if payment_method:
            payment_qs = PaymentType.objects.filter(name = payment_method).last()
            food_order_qs = FoodOrder.objects.filter(table_id = table_id).last()
            food_order_qs.payment_method = payment_qs
            food_order_qs.save()


        staff_fcm_device_qs = StaffFcmDevice.objects.filter(
            hotel_staff__tables=table_id)
        staff_id_list = staff_fcm_device_qs.values_list(
            'pk', flat=True)
        if send_fcm_push_notification_appointment(
            tokens_list=list(staff_fcm_device_qs.values_list(
                'token', flat=True)),
                table_no=table_qs.table_no if table_qs else None,
                status="CallStaffForPayment",
                msg=payment_method,
                staff_id_list=staff_id_list,

        ):
            return ResponseWrapper(msg='Success')
        else:
            return ResponseWrapper(error_msg="failed to notify", error_code=400)

    def fcm_notification_history_for_staff(self, request, staff_id, *args, **kwargs):
        qs = FcmNotificationStaff.objects.filter(
            staff_device__hotel_staff_id=staff_id, created_at__gte=timezone.now().date()).order_by('-created_at')
        serializer = FcmNotificationStaffSerializer(instance=qs, many=True)
        return ResponseWrapper(data=serializer.data)


class PopUpViewset(LoggingMixin, CustomViewSet):

    queryset = PopUp.objects.all()
    lookup_field = 'pk'
    serializer_class = PopUpSerializer
    logging_methods = ['DELETE', 'POST', 'PATCH']
    http_method_names = ['post', 'patch', 'get', 'delete']

    def get_permissions(self):
        permission_classes = []
        if self.action in ['create', 'update', 'destroy']:
            permission_classes = [
                custom_permissions.IsRestaurantManagementOrAdmin]
        return [permission() for permission in permission_classes]

    # def pop_up_list_by_restaurant(self, request, restaurant_id, *args, **kwargs):
    #     popup_qs = PopUp.objects.filter(
    #         restaurant=restaurant_id).order_by('serial_no')
    #     serializer = PopUpSerializer(instance=popup_qs, many=True)
    #     return ResponseWrapper(data=serializer.data)


class SliderViewset(LoggingMixin, CustomViewSet):

    queryset = Slider.objects.all()
    lookup_field = 'pk'
    serializer_class = SliderSerializer
    logging_methods = ['DELETE', 'POST', 'PATCH']
    http_method_names = ['post', 'patch', 'get', 'delete']

    def get_permissions(self):
        permission_classes = []
        if self.action in ['create', 'update', 'destroy']:
            permission_classes = [
                custom_permissions.IsRestaurantManagementOrAdmin]
        return [permission() for permission in permission_classes]

    def slider_list_by_restaurant(self, request, restaurant_id, *args, **kwargs):
        today = timezone.datetime.now().date()
        start_date = today - timedelta(days=1)
        # end_date = today + timedelta(days=1)
        current_time = timezone.now()
        slider_qs = Discount.objects.filter(Q(restaurant_id=restaurant_id, is_slider=True,
                                              start_date__lte=today, end_date__gte=today,
                                              discount_schedule_type='Date_wise') | Q(restaurant_id = restaurant_id,is_slider=True,
                                                                                      discount_slot_closing_time__gte=current_time,
                                                                                      discount_slot_start_time__lte=current_time,
                                                                                      discount_schedule_type='Time_wise')).exclude(food=None, image=None)
        serializer = DiscountSliderSerializer(instance=slider_qs, many=True)
        return ResponseWrapper(data=serializer.data)


class SubscriptionViewset(LoggingMixin, CustomViewSet):
    queryset = Subscription.objects.all()
    lookup_field = 'pk'
    serializer_class = SubscriptionSerializer
    logging_methods = ['DELETE', 'POST', 'PATCH']

    def get_permissions(self):
        permission_classes = []
        if self.action in ['create', 'update', 'destroy']:
            permission_classes = [
                permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    def update(self, request, **kwargs):

        instance = self.get_object()
        if instance.code == request.data.get('code'):
            request.data.pop('code', None)
        return super(SubscriptionViewset, self).update(request, **kwargs)

    def subscription_by_restaurant(self, request, restaurant_id, *args, **kwargs):
        restaurant_qs = Restaurant.objects.filter(pk=restaurant_id).first()
        restaurant_qs = restaurant_qs.subscription
        serializer = SubscriptionSerializer(instance=restaurant_qs)
        return ResponseWrapper(data=serializer.data)

class ReviewViewset(LoggingMixin, CustomViewSet):
    queryset = Review.objects.all()
    lookup_field = 'pk'
    serializer_class = ReviewSerializer
    #logging_methods = ['GET','DELETE', 'POST', 'PATCH']

    def get_permissions(self):
        permission_classes = []
        if self.action in ['create']:
            permission_classes = [
                permissions.IsAuthenticated]

        elif self.action in ['destroy']:
            permission_classes = [
                permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    def review_list(self, request, restaurant, *args, **kwargs):
        restaurant_qs = Review.objects.filter(order__restaurant_id=restaurant)
        serializer = ReviewSerializer(instance=restaurant_qs, many=True)
        return ResponseWrapper(data=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        if serializer.is_valid():
            qs = serializer.save()
            food_list_qs = Food.objects.filter(
                food_options__ordered_items__food_order_id=qs.order.pk)
            for index, food_qs in enumerate(food_list_qs):
                food_rating = food_qs.rating
                if food_rating == None:
                    food_rating = 0
                new_rating = ((food_rating * food_qs.order_counter) +
                              qs.rating)/(1+food_qs.order_counter)
                # food_qs.rating = new_rating
                # food_qs.save()
                food_list_qs[index].rating = new_rating
                food_list_qs[index].order_counter = (1+food_qs.order_counter)

            Food.objects.bulk_update(food_list_qs, ['rating', 'order_counter'])
            serializer = self.serializer_class(instance=qs)
            return ResponseWrapper(data=serializer.data, msg='created')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)


class RestaurantMessagesViewset(LoggingMixin, CustomViewSet):
    queryset = RestaurantMessages.objects.all()
    lookup_field = 'pk'
    serializer_class = RestaurantMessagesSerializer
    #logging_methods = ['GET','DELETE', 'POST', 'PATCH']

    def get_permissions(self):
        permission_classes = []
        if self.action in ['restaurant_messages_list', 'last_restaurant_messages_list']:
            permission_classes = [permissions.IsAuthenticated]
        # else:
        #     permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    def restaurant_messages_list(self, request, restaurant, *args, **kwargs):
        restaurant_qs = FcmNotificationCustomer.objects.filter(
            restaurant_id=restaurant)
        serializer = FcmNotificationListSerializer(
            instance=restaurant_qs, many=True)
        return ResponseWrapper(data=serializer.data, msg='success')

    def all_restaurant_messages_list(self, request, *args, **kwargs):
        notification_list_qs = FcmNotificationCustomer.objects.all().order_by(
            '-created_at')[:10]
        serializer = FcmNotificationListSerializer(
            instance=notification_list_qs, many=True)
        return ResponseWrapper(data=serializer.data, msg='success')

class PaymentTypeViewSet(LoggingMixin, CustomViewSet):
    queryset = PaymentType.objects.all()
    lookup_field = 'pk'
    serializer_class = PaymentTypeSerializer

    def restaurant_payment_type(self, request, restaurant, *args, **kwargs):
        restaurant = Restaurant.objects.filter(id=restaurant).last()
        qs = restaurant.payment_type.all()
        serializer = PaymentTypeSerializer(instance=qs, many=True)
        return ResponseWrapper(data=serializer.data)


class VersionUpdateViewSet(LoggingMixin, CustomViewSet):
    queryset = VersionUpdate.objects.all()
    lookup_field = 'pk'
    logging_methods = ['GET', 'POST', 'PATCH', 'DELETE']

    def get_permissions(self):
        permission_classes = []
        if self.action in ['create', 'list']:
            permission_classes = [
                permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action == 'create':
            self.serializer_class = VersionUpdateSerializer
        elif self.action == 'list':
            self.serializer_class = VersionUpdateSerializer
        else:
            self.serializer_class = VersionUpdateSerializer

        return self.serializer_class

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            qs = serializer.save()
            serializer = VersionUpdateSerializer(instance=qs)
            return ResponseWrapper(data=serializer.data, msg='created')
        else:
            return ResponseWrapper(error_code=400, error_msg=serializer.errors, msg='failed to create Version')

    def user_version_requirement(self, request, *args, **kwargs):
        qs = VersionUpdate.objects.filter(
            is_customer_app=True).order_by('-updated_at').first()

        #serializer = VersionUpdateSerializer(instance=qs, many=True)
        serializer = VersionUpdateSerializer(instance=qs)
        return ResponseWrapper(data=serializer.data, msg='success')

    def waiter_version_requirement(self, request, *args, **kwargs):
        qs = VersionUpdate.objects.filter(
            is_waiter_app=True).order_by('-updated_at').first()

        #serializer = VersionUpdateSerializer(instance=qs, many=True)
        serializer = VersionUpdateSerializer(instance=qs)
        return ResponseWrapper(data=serializer.data, msg='success')


class PrintOrder(CustomViewSet):
    queryset = OrderedItem.objects.exclude(
        status__in=["0_ORDER_INITIALIZED", "4_CANCELLED"])
    lookup_field = 'food_order'
    serializer_class = OrderedItemSerializer
    http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        import base64

        from django.template.loader import render_to_string
        from weasyprint import CSS, HTML
        items_qs = OrderedItem.objects.all().exclude(food_extra=None)
        # order_by('-pk')[:50]
        serializer = OrderedItemTemplateSerializer(
            instance=items_qs, many=True)
        now = datetime.now()
        context = {
            'table_no': 12,
            'order_id': 12,
            # 'time': str(timezone.now().date()) + '  ' + str(timezone.now().time()),
            'date': str(now.strftime('%d/%m/%Y')),
            'time': str(now.strftime("%I:%M %p")),
            'items_data': serializer.data
        }
        html_string = render_to_string('invoice.html', context)
        # @page { size: Letter; margin: 0cm }
        css = CSS(
            string='@page { size: 80mm 350mm; margin: 0mm }')
        pdf_byte_code = HTML(string=html_string).write_pdf('ll.pdf',
                                                           stylesheets=[
                                                               css], zoom=1
                                                           )
        pdf_obj_encoded = base64.b64encode(pdf_byte_code)
        pdf_obj_encoded = pdf_obj_encoded.decode('utf-8')
        # success = print_node(pdf_obj=pdf_obj_encoded)

        return ResponseWrapper(data={'success': True})


class PrintNodeViewSet(LoggingMixin, CustomViewSet):
    serializer_class = PrintNodeSerializer
    queryset = PrintNode.objects.all()
    lookup_field = 'pk'

    def get_serializer_class(self):
        return self.serializer_class

    def get_permissions(self):
        permission_classes = []
        if self.action in ['print_node_create', 'print_node_update', 'print_node_destroy']:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    http_method_names = ['post', 'patch', 'get', 'delete']

    def print_node_create(self, request):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        if serializer.is_valid():
            qs = serializer.save()
            serializer = self.serializer_class(instance=qs)
            return ResponseWrapper(data=serializer.data, msg='created')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def print_node_update(self, request, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data, partial=True)
        if serializer.is_valid():
            qs = serializer.update(instance=self.get_object(
            ), validated_data=serializer.validated_data)
            serializer = self.serializer_class(instance=qs)
            return ResponseWrapper(data=serializer.data)
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def print_node_destroy(self, request, **kwargs):
        qs = self.queryset.filter(**kwargs).first()
        if qs:
            qs.delete()
            return ResponseWrapper(status=200, msg='deleted')
        else:
            return ResponseWrapper(error_msg="failed to delete", error_code=400)

    def list(self, request, *args, **kwargs):
        qs = PrintNode.objects.all()
        serializer = PrintNodeSerializer(instance=qs, many=True)
        return ResponseWrapper(data=serializer.data, msg='success')

    def print_node_list(self, request, restaurant_id, *args, **kwargs):
        qs = PrintNode.objects.filter(restaurant_id=restaurant_id)
        serializer = PrintNodeSerializer(instance=qs, many=True)
        return ResponseWrapper(data=serializer.data, msg='success')


class TakeAwayOrderViewSet(LoggingMixin, CustomViewSet):
    serializer_class = TakeAwayOrderSerializer
    queryset = TakeAwayOrder.objects.all()
    lookup_field = 'pk'

    def get_serializer_class(self):
        return self.serializer_class

    def get_permissions(self):
        permission_classes = []
        if self.action in ['take_away_order']:
            permission_classes = [custom_permissions.IsRestaurantStaff]
        return [permission() for permission in permission_classes]

    http_method_names = ['post', 'patch', 'get', 'delete']

    def take_away_order(self, request, restaurant_id, *args, **kwargs):
        qs = TakeAwayOrder.objects.filter(restaurant_id=restaurant_id).first()
        if not qs:
            return ResponseWrapper(msg='No Take Away Order is Available')
        serializer = TakeAwayOrderSerializer(instance=qs.running_order.exclude(
            status__in=['5_PAID', '6_CANCELLED']), many=True)
        return ResponseWrapper(data=serializer.data, msg='success')


class ParentCompanyPromotionViewSet(LoggingMixin, CustomViewSet):
    serializer_class = ParentCompanyPromotionSerializer
    queryset = ParentCompanyPromotion.objects.all()
    lookup_field = 'pk'
    http_method_names = ['post', 'patch', 'get', 'delete']

    def get_permissions(self):
        permission_classes = []
        if self.action in ['create', 'destroy', 'patch', 'list']:
            permission_classes = [
                # custom_permissions.IsRestaurantManagementOrAdmin]
                permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    def parent_company_promotions(self, request, restaurant_id, *args, **kwargs):
        qs = ParentCompanyPromotion.objects.filter(restaurant=restaurant_id)
        serializer = ParentCompanyPromotionSerializer(instance=qs, many=True)
        return ResponseWrapper(data=serializer.data, msg='Success')



class CashLogViewSet(LoggingMixin, CustomViewSet):
    serializer_class = CashLogSerializer
    queryset = CashLog.objects.all()
    lookup_field = 'pk'


    def get_serializer_class(self):
        if self.action in ['restaurant_opening']:
            self.serializer_class = RestaurantOpeningSerializer
        elif self.action in ['restaurant_closing']:
            self.serializer_class = RestaurantClosingSerializer

        return self.serializer_class

    # def get_permissions(self):
    #     if self.action in ['create', 'update', 'destroy', 'restaurant_opening']:
    #         permission_classes = [
    #             custom_permissions.IsRestaurantManagementOrAdmin]
    #
    #     return [permission() for permission in permission_classes]
    http_method_names = ['post', 'patch', 'get', 'delete']

    def restaurant_log_status(self,request, restaurant_id, *args,**kwargs):
        restaurant_qs = Restaurant.objects.filter(pk = restaurant_id).last()
        if not restaurant_qs:
            return ResponseWrapper(error_msg=['Restaurant is not valid'], status=400)
        cash_log = restaurant_qs.cash_logs.last()
        if not cash_log:
            return ResponseWrapper(msg='Restaurant is not open', status=200)
        elif cash_log.ending_time:
            return ResponseWrapper(msg='Restaurant is already close', status=200)
        else:
            return ResponseWrapper(msg='Restaurant is open', status=200)

    def restaurant_opening(self, request):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        restaurant_id = request.data.get('restaurant')
        in_cash_while_opening = request.data.get('in_cash_while_opening')
        if serializer.is_valid():
            cashlog_qs = CashLog.objects.create(restaurant_id = restaurant_id, in_cash_while_opening= in_cash_while_opening)
            cashlog_qs.save()
            serializer = CashLogSerializer(instance=cashlog_qs)
            return ResponseWrapper(data=serializer.data, msg='created')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def restaurant_closing(self, request,pk, *args, **kwargs):
        today_date = timezone.now().date()
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        ending_time = request.data.get('ending_time')
        if not ending_time:
            ending_time = timezone.now()
        restaurant = request.data.get('restaurant')
        remarks = request.data.get('remarks')

        if serializer.is_valid():
            cash_log_qs = CashLog.objects.filter(id = pk).last()

            if not cash_log_qs.starting_time:
                return ResponseWrapper(error_msg=['Restaurant is not opening'], error_code=400)
            if cash_log_qs.ending_time:
                return ResponseWrapper(error_msg=['Restaurant is already closed'], error_code=400)

            qs = serializer.update(instance=self.get_object(
            ), validated_data=serializer.validated_data)

            opening_time = qs.starting_time
            closing_time = ending_time
            closing_time += timedelta(days =1)

            # fs = FoodOrder.objects.filter(created_at__gte=opening_time, created_at__lte=closing_time)

            invoice_qs = Invoice.objects.filter(
                created_at__gte=opening_time, created_at__lte=closing_time, payment_status='1_PAID', restaurant_id=request.data.get('restaurant'))

            payable_amount_list = invoice_qs.values_list('payable_amount', flat=True)
            total = sum(payable_amount_list)
            cash_log_qs.total_received_payment = total
            cash_log_qs.ending_time= ending_time
            # else:
            #     cash_log_qs.ending_time = timezone.now()
            cash_log_qs.restaurant_id= restaurant
            cash_log_qs.remarks= remarks

            food_order_qs = FoodOrder.objects.filter(created_at__gte=opening_time, created_at__lte=closing_time, status='5_PAID',
                                                     restaurant_id=request.data.get('restaurant'), payment_method__name = 'Cash')
            total_payable_amount = sum(food_order_qs.values_list('payable_amount', flat=True))
            cash_log_qs.total_cash_received = total_payable_amount
            withdraw_cash_qs = WithdrawCash.objects.filter(cash_log_id = cash_log_qs).last()
            if not withdraw_cash_qs:
                cash_log_qs.in_cash_while_closing = cash_log_qs.in_cash_while_opening + cash_log_qs.total_cash_received
            else:
                cash_log_qs.in_cash_while_closing = cash_log_qs.in_cash_while_opening + cash_log_qs.total_cash_received - withdraw_cash_qs.amount

            cash_log_qs.save()

            serializer = CashLogSerializer(instance=cash_log_qs)
            return ResponseWrapper(data=serializer.data, msg='success')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def cash_log_list(self,request, restaurant_id, *args,**kwargs):
        restaurant_qs = CashLog.objects.filter(restaurant_id = restaurant_id).order_by('id')
        if not restaurant_qs:
            return ResponseWrapper(error_msg=['Not Cash Log'], error_code=400)
        serializer = CashLogSerializer(instance=restaurant_qs, many=True)
        return ResponseWrapper(data=serializer.data, msg='Success')


class WithdrawCashViewSet(LoggingMixin, CustomViewSet):
    serializer_class = WithdrawCashSerializer
    queryset = WithdrawCash.objects.all()
    lookup_field = 'pk'


    def get_serializer_class(self):
        # if self.action in ['restaurant_opening']:
        #     self.serializer_class = RestaurantOpeningSerializer
        # elif self.action in ['restaurant_closing']:
        #     self.serializer_class = RestaurantClosingSerializer

        return self.serializer_class

    http_method_names = ['post', 'patch', 'get', 'delete']

    def withdraw_create(self, request):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        if serializer.is_valid():
            qs = serializer.save()
            serializer = self.serializer_class(instance=qs)
            return ResponseWrapper(data=serializer.data, msg='created')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

class PromoCodePromotionViewSet(LoggingMixin, CustomViewSet):
    serializer_class = PromoCodePromotionSerializer
    queryset = PromoCodePromotion.objects.all()
    lookup_field = 'pk'
    http_method_names = ['post', 'patch', 'get', 'delete']

    def get_permissions(self):
        permission_classes = []
        if self.action in ['create', 'destroy', 'patch', 'list','promo_code_list']:
            permission_classes = [
                custom_permissions.IsRestaurantManagementOrAdmin]
        return [permission() for permission in permission_classes]


    def create(self, request):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        restaurant_id=request.data.get('restaurant')
        restaurant_qs = Restaurant.objects.filter(id = restaurant_id).first()
        if not restaurant_qs:
            return ResponseWrapper(error_msg=['Restaurant is not valid'], error_code=400)
        self.check_object_permissions(request, obj=restaurant_id)
        if serializer.is_valid():
            qs = serializer.save()
            serializer = PromoCodePromotionDetailsSerializer(instance=qs)
            return ResponseWrapper(data=serializer.data, msg='created')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def update(self, request, pk, **kwargs):
        promo_code_qs = PromoCodePromotion.objects.filter(id = pk).first()
        restaurant_id = promo_code_qs.restaurant_id
        if not restaurant_id:
            return ResponseWrapper(error_msg=['Restaurant is not valid'], error_code=400)
        self.check_object_permissions(request, obj=restaurant_id)

        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data, partial=True)
        instance = self.get_object()
        if instance.code == request.data.get('code'):
            request.data.pop('code', None)
        if serializer.is_valid():
            qs = serializer.update(instance=self.get_object(
            ), validated_data=serializer.validated_data)
            serializer = PromoCodePromotionDetailsSerializer(instance=qs)
            return ResponseWrapper(data=serializer.data)
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def destroy(self, request,pk, **kwargs):
        qs = self.queryset.filter(**kwargs).first()
        restaurant_id = qs.restaurant_id
        if not restaurant_id:
            return ResponseWrapper(error_msg=['Restaurant is not valid'], error_code=400)
        self.check_object_permissions(request, obj=restaurant_id)
        if qs:
            qs.delete()
            return ResponseWrapper(status=200, msg='deleted')
        else:
            return ResponseWrapper(error_msg="failed to delete", error_code=400)
    def promo_code_list(self,request, restaurant_id, *args,**kwargs):
        restaurant_qs = Restaurant.objects.filter(pk = restaurant_id).first()
        if not restaurant_qs:
            return ResponseWrapper(error_msg=['Restaurant id is not valid'], error_code=400)
        restaurant_id = restaurant_qs.pk
        self.check_object_permissions(request, obj=restaurant_id)
        promo_code_qs = restaurant_qs.promo_code_promotions

        serializer = PromoCodePromotionDetailsSerializer(instance=promo_code_qs, many=True)
        return ResponseWrapper(data=serializer.data, msg='Success')

    # def parent_company_promotions(self, request, restaurant_id, *args, **kwargs):
    #     qs = ParentCompanyPromotion.objects.filter(restaurant=restaurant_id)
    #     serializer = ParentCompanyPromotionSerializer(instance=qs, many=True)
    #     return ResponseWrapper(data=serializer.data, msg='Success')


# TakewayOrderType Viewset

class TakewayOrderTypeViewSet(LoggingMixin, CustomViewSet):
    serializer_class = TakewayOrderTypeSerializer
    queryset = TakewayOrderType.objects.all()
    lookup_field = 'pk'
    logging_methods = ['GET', 'POST', 'PATCH', 'DELETE']
    # http_method_names = ['post', 'patch', 'get', 'delete']

    def get_permissions(self):
        permission_classes = []
        if self.action in ['create', 'update', 'destroy', 'list']:
            permission_classes = [
                permissions.IsAdminUser
            ]
        return [permission() for permission in permission_classes]


    def create(self, request):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        if serializer.is_valid():
            qs = serializer.save()
            serializer = TakewayOrderTypeSerializer(instance=qs)
            return ResponseWrapper(data=serializer.data, msg='created')
        else:
            return ResponseWrapper(error_code=400, error_msg=serializer.errors, msg='failed to create Takeway Order Type')

    def update(self, request, pk, **kwargs):
        takeway_order_type_qs = TakewayOrderType.objects.filter(id=pk).first()
        # self.check_object_permissions(request, obj=restaurant_id)

        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data, partial=True)
        instance = self.get_object()
        if instance.name == request.data.get('name'):
            request.data.pop('name', None)
        if serializer.is_valid():
            qs = serializer.update(instance=self.get_object(
            ), validated_data=serializer.validated_data)
            serializer = TakewayOrderTypeSerializer(instance=qs)
            return ResponseWrapper(data=serializer.data)
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def destroy(self, request,pk, **kwargs):
        qs = self.queryset.filter(**kwargs).first()
        # self.check_object_permissions(request, obj=restaurant_id)
        if qs:
            qs.delete()
            return ResponseWrapper(status=200, msg='deleted')
        else:
            return ResponseWrapper(error_msg="failed to delete", error_code=400)

    def list(self, request, *args, **kwargs):
        """
        Fetch all takeway order types
        return => list [obj{ id(int), image(str), name(str) }]
        """
        qs = TakewayOrderType.objects.all()
        serializer = TakewayOrderTypeSerializer(instance=qs, many=True)
        return ResponseWrapper(data=serializer.data)

    def restaurant_takeway_order_type(self, request, restaurant, *args, **kwargs):
        """
        Get all takeway order types for specific restaurant.
        """
        restaurant = Restaurant.objects.filter(id=restaurant).last()
        qs = restaurant.takeway_order_type.all()
        serializer = TakewayOrderTypeSerializer(instance=qs, many=True)
        return ResponseWrapper(data=serializer.data)

