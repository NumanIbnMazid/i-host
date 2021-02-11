from calendar import month
from datetime import datetime
import random
from utils.fcm import send_fcm_push_notification_appointment
from utils.sms import send_sms
from re import error
from utils.pagination import CustomLimitPagination
from drf_yasg2 import openapi

from rest_framework_tracking.models import APIRequestLog
from account_management import models

from utils.custom_viewset import CustomViewSet
from restaurant.serializers import HotelStaffInformationSerializer
import uuid
from uuid import uuid4
import restaurant
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model, login
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.shortcuts import render
from django.utils import timezone
from drf_yasg2.utils import swagger_auto_schema
from knox.models import AuthToken
# Create your views here.
from knox.views import LoginView as KnoxLoginView
from knox.views import LogoutView as KnoxLogOutView

from rest_framework import permissions, status, viewsets
from rest_framework.authentication import BasicAuthentication
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from restaurant.models import Restaurant
from utils.response_wrapper import ResponseWrapper
from django.conf import settings
from django.db.models import Count, Min, Q, query_utils

from account_management.models import CustomerFcmDevice, CustomerInfo, OtpUser, StaffFcmDevice, HotelStaffInformation, FcmNotificationCustomer
from account_management.models import UserAccount
from account_management.models import UserAccount as User
from account_management.serializers import (CustomerFcmDeviceSerializer, CustomerInfoSerializer, StaffFcmDeviceSerializer, OtpLoginSerializer,
                                            RestaurantUserSignUpSerializer, StaffInfoGetSerializer, StaffInfoSerializer,
                                            StaffLoginInfoGetSerializer,
                                            UserAccountPatchSerializer,
                                            UserAccountSerializer,
                                            UserSignupSerializer, LogSerializerGet, LogSerializerPost, CustomerNotificationSerializer, CheckFcmSerializer)

from rest_framework_tracking.mixins import LoggingMixin

from restaurant import permissions as custom_permissions


def login_related_info(user):
    user_serializer = UserAccountSerializer(instance=user)
    staff_info = []
    customer_info = None
    try:
        if user.hotel_staff.first():
            staff_info_serializer = StaffLoginInfoGetSerializer(
                instance=user.hotel_staff.all(), many=True)
            staff_info = staff_info_serializer.data
    except:
        pass
    try:
        if user.customer_info:
            customer_info_serialzier = CustomerInfoSerializer(
                instance=user.customer_info)
            customer_info = customer_info_serialzier.data
    except:
        pass
    return customer_info, staff_info, user_serializer


class StaffFcmDeviceViewSet(LoggingMixin, CustomViewSet):
    queryset = StaffFcmDevice.objects.all()
    lookup_field = 'hotel_staff'
    serializer_class = StaffFcmDeviceSerializer

    def get_serializer_class(self):
        if self.action in ['check_fcm']:
            self.serializer_class = CheckFcmSerializer
        return self.serializer_class
    permission_classes = [permissions.IsAuthenticated]

    logging_methods = ['GET', 'POST', 'PATCH', 'DELETE']
    http_method_names = ('post',)

    def create(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        if serializer.is_valid():
            staff_fcm_qs = StaffFcmDevice.objects.filter(
                hotel_staff=request.data.get("hotel_staff"))
            staff_fcm_qs.delete()
            qs = serializer.save()
            serializer = self.serializer_class(instance=qs)
            return ResponseWrapper(data=serializer.data, msg='created')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def update(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data, partial=True)
        if serializer.is_valid():
            qs = serializer.update(instance=self.get_object(
            ), validated_data=serializer.validated_data)
            serializer = self.serializer_class(instance=qs)
            return ResponseWrapper(data=serializer.data)
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def check_fcm(self, request, * args, **kwargs):
        token = request.data.get('token')
        token_qs = StaffFcmDevice.objects.filter(
            token=request.data.get('token'), hotel_staff__user=request.user)
        if token_qs:
            return ResponseWrapper(data={"exists": True})
        else:
            return ResponseWrapper(data={"exists": False})


class UserFcmDeviceViewset(LoggingMixin, CustomViewSet):
    queryset = CustomerFcmDevice.objects.all()
    lookup_field = 'customer'
    serializer_class = CustomerFcmDeviceSerializer
    permission_classes = [permissions.IsAuthenticated]

    logging_methods = ['GET', 'POST', 'PATCH', 'DELETE']
    http_method_names = ('post',)

    def create(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        if serializer.is_valid():
            customer_fcm_qs = CustomerFcmDevice.objects.filter(
                customer_id=request.data.get("customer"))
            customer_fcm_qs.delete()
            qs = serializer.save()
            serializer = self.serializer_class(instance=qs)
            return ResponseWrapper(data=serializer.data, msg='created')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def update(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data, partial=True)
        if serializer.is_valid():
            qs = serializer.update(instance=self.get_object(
            ), validated_data=serializer.validated_data)
            serializer = self.serializer_class(instance=qs)
            return ResponseWrapper(data=serializer.data)
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)


class LoginView(KnoxLoginView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = AuthTokenSerializer

    @swagger_auto_schema(request_body=AuthTokenSerializer)
    def post(self, request, format=None):
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)

        token_limit_per_user = self.get_token_limit_per_user()
        if token_limit_per_user is not None:
            now = timezone.now()
            token = request.user.auth_token_set.filter(expiry__gt=now)
            if token.count() >= token_limit_per_user:
                return Response(
                    {"error": "Maximum amount of tokens allowed per user exceeded."},
                    status=status.HTTP_403_FORBIDDEN
                )
        token_ttl = self.get_token_ttl()
        instance, token = AuthToken.objects.create(request.user, token_ttl)
        user_logged_in.send(sender=request.user.__class__,
                            request=request, user=request.user)
        data = self.get_post_response_data(request, token, instance)
        customer_info, staff_info, user_serializer = login_related_info(user)
        return ResponseWrapper(data={'auth': data, 'user': user_serializer.data, 'staff_info': staff_info, 'customer_info': customer_info})


class LogoutView(KnoxLogOutView):
    def post(self, request, format=None):
        is_waiter = request.path.__contains__('/apps/waiter/logout/')
        is_customer = request.path.__contains__('/apps/customer/logout/')
        if is_waiter:
            StaffFcmDevice.objects.filter(
                hotel_staff__user_id=request.user.pk).delete()
        if is_customer:
            CustomerFcmDevice.objects.filter(
                customer__user_id=request.user.pk).delete()
        request._auth.delete()
        user_logged_out.send(sender=request.user.__class__,
                             request=request, user=request.user)

        return ResponseWrapper(status=200)


class OtpSignUpView(KnoxLoginView):
    permission_classes = (permissions.AllowAny,)

    # TODO:need to check if otp is same

    @swagger_auto_schema(request_body=OtpLoginSerializer)
    def post(self, request, format=None):
        phone = request.data.get('phone')
        otp_qs = OtpUser.objects.filter(phone=phone).last()
        if not settings.JAPAN_SERVER:
            if otp_qs.updated_at < (timezone.now() - timezone.timedelta(minutes=5)):
                return ResponseWrapper(error_code=status.HTTP_401_UNAUTHORIZED, error_msg=['otp timeout'])
            if request.data.get('otp') != otp_qs.otp_code:
                return ResponseWrapper(error_code=status.HTTP_401_UNAUTHORIZED, error_msg=['otp mismatched'])
        else:
            if request.data.get('otp') != 1234:
                return ResponseWrapper(error_code=status.HTTP_401_UNAUTHORIZED, error_msg=['otp mismatched'])

        token_limit_per_user = self.get_token_limit_per_user()
        user_qs = User.objects.filter(phone=request.data.get('phone')).first()
        if not user_qs:
            user_qs = User.objects.create_user(
                phone=request.data.get('phone'),
                password=uuid.uuid4().__str__()
            )
            customer_qs, _ = CustomerInfo.objects.get_or_create(user=user_qs)

        if token_limit_per_user is not None:
            now = timezone.now()
            token = user_qs.auth_token_set.filter(expiry__gt=now)
            # token = request.user.auth_token_set.filter(expiry__gt=now)
            if token.count() >= token_limit_per_user:
                return ResponseWrapper(
                    error_msg="Maximum amount of tokens allowed per user exceeded.",
                    status=status.HTTP_403_FORBIDDEN
                )
        token_ttl = self.get_token_ttl()
        instance, token = AuthToken.objects.create(user_qs, token_ttl)
        user_logged_in.send(sender=user_qs.__class__,
                            request=request, user=user_qs)
        data = self.get_post_response_data(request, token, instance)
        return ResponseWrapper(data=data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_login(request):
    return ResponseWrapper(data="Token is Valid", status=200)


class RestaurantAccountManagerViewSet(LoggingMixin, CustomViewSet):
    logging_methods = ['GET', 'POST', 'PATCH', 'DELETE']

    def get_serializer_class(self):
        """
        Return the class to use for the serializer.
        Defaults to using `self.serializer_class`.

        You may want to override this if you need to provide different
        serializations depending on the incoming request.

        (Eg. admins get full serialization, others get basic serialization)
        """

        if self.action in ["create_owner", "create_manager", "create_waiter"]:
            self.serializer_class = RestaurantUserSignUpSerializer
        elif self.action in ["update", 'retrieve']:
            self.serializer_class = StaffInfoSerializer
        else:
            self.serializer_class = UserAccountSerializer

        return self.serializer_class

    def get_permissions(self):
        if self.action in ["create_owner"]:

            permission_classes = [permissions.IsAdminUser]
        if self.action in ["create_manager"]:
            permission_classes = [custom_permissions.IsRestaurantOwnerOrAdmin]

        elif self.action in ["manager_info", "waiter_info"]:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    queryset = HotelStaffInformation.objects.all()
    lookup_field = 'pk'

    def create_owner(self, request, *args, **kwargs):
        staff_qs = HotelStaffInformation.objects.filter(restaurant_id=request.data.get('restaurant_id'),
                                                        user__phone=request.data.get('phone')).first()
        if staff_qs:
            staff_serializer = StaffInfoGetSerializer(instance=staff_qs)
            return ResponseWrapper(error_msg=['User is already a staff, staff id is ' + str(staff_qs.pk)], data=staff_serializer.data)
        return self.create_staff(request, is_owner=True)

    def create_manager(self, request, *args, **kwargs):
        res_qs = HotelStaffInformation.objects.filter(
            restaurant_id=request.data.get('restaurant_id'))
        if not res_qs:
            return ResponseWrapper(msg='invalid restaurant_id')
        manager_count = res_qs.filter(is_manager=True).count()

        restaurant_id = res_qs.first().restaurant_id
        manager_qs = Restaurant.objects.filter(
            id=restaurant_id).select_related('subscription').first()
        manager_limit_qs = manager_qs.subscription.manager_limit

        if not manager_count < manager_limit_qs:
            return ResponseWrapper(
                error_msg=["Your Manager Limit is " +
                           str(manager_limit_qs) + ', Please Update Your Subscription '],
                error_code=400)

        staff_qs = res_qs.filter(user__phone=request.data.get('phone'))
        if staff_qs:
            staff_serializer = StaffInfoGetSerializer(instance=staff_qs)
            return ResponseWrapper(error_msg=['User is already a staff, staff id is ' + str(staff_qs.pk)], data=staff_serializer.data)

        # email = request.data.pop("email")
        # self.check_object_permissions(request, obj=RestaurantUserSignUpSerializer)
        return self.create_staff(request, is_manager=True)

    def create_waiter(self, request, *args, **kwargs):
        res_qs = HotelStaffInformation.objects.filter(
            restaurant_id=request.data.get('restaurant_id'))
        waiter_count = res_qs.filter(is_waiter=True).count()

        restaurant_id = res_qs.first().restaurant_id
        waiter_qs = Restaurant.objects.filter(
            id=restaurant_id).select_related('subscription').first()
        waiter_limit = waiter_qs.subscription.waiter_limit

        if not waiter_count < waiter_limit:
            return ResponseWrapper(
                error_msg=["Your Waiter Limit is " +
                           str(waiter_limit) + ', Please Update Your Subscription '],
                error_code=400)

        staff_qs = res_qs.filter(user__phone=request.data.get('phone'))
        if staff_qs:
            staff_serializer = StaffInfoGetSerializer(instance=staff_qs)
            return ResponseWrapper(error_msg=['User is already a staff, staff id is ' + str(staff_qs.pk)], data=staff_serializer.data)

        # email = request.data.pop("email")

        return self.create_staff(request, is_waiter=True)

    def create_staff(self, request, is_owner=False, is_manager=False, is_waiter=False):
        serializer = RestaurantUserSignUpSerializer(data=request.data)
        if not serializer.is_valid():
            return ResponseWrapper(error_code=400, error_msg=serializer.errors)
        # request.data._mutable = True
        password = serializer.data.get("password")
        restaurant_id = serializer.data.get('restaurant_id')
        user_info_dict = {}

        if serializer.data.get('phone'):
            user_info_dict['phone'] = serializer.data.get("phone")

        if serializer.data.get("name"):
            user_info_dict['first_name'] = serializer.data.get("name")

        staff_info = {}
        if request.data.get('shift_start'):
            staff_info['shift_start'] = request.data.get('shift_start')
        if request.data.get('shift_end'):
            staff_info['shift_end'] = request.data.get('shift_end')
        if serializer.data.get("name"):
            staff_info['name'] = serializer.data.get("name")
        if serializer.data.get("email_address"):
            staff_info['email'] = serializer.data.get("email_address")

        if request.data.get('nid'):
            staff_info['nid'] = request.data.get('nid')
        if request.data.get('shift_days'):
            staff_info['shift_days'] = request.data.get('shift_days')

        if request.data.get('image'):
            staff_info['image'] = request.data.get('image')

        # request.data._mutable = False

        restaurant_qs = Restaurant.objects.filter(pk=restaurant_id).first()

        if not restaurant_qs:
            return ResponseWrapper(error_code=404, error_msg=[{"restaurant_id": "restaurant not found"}])
        phone = request.data["phone"]
        user_qs = User.objects.filter(phone=phone).first()
        error_msg = []
        if not user_qs:
            password = make_password(password=password)
            user_qs = User.objects.create(
                password=password,
                **user_info_dict
            )
        else:
            User.objects.filter(phone=phone).update(**user_info_dict)
            error_msg.append(
                'user already exists so staff is created successfully but password remains unchanged')

        staff_qs = HotelStaffInformation.objects.filter(
            user=user_qs, restaurant=restaurant_qs).first()
        if staff_info:
            staff_serializer = StaffInfoSerializer(
                data=staff_info, partial=True)
            if staff_serializer.is_valid():
                if not staff_qs:
                    staff_qs = HotelStaffInformation.objects.create(user=user_qs, restaurant=restaurant_qs,
                                                                    is_manager=is_manager, is_owner=is_owner,
                                                                    is_waiter=is_waiter)

                staff_qs = staff_serializer.update(
                    staff_qs, staff_serializer.validated_data)

        # user_serializer = UserAccountSerializer(instance=user_qs, many=False)

        staff_serializer = StaffInfoGetSerializer(instance=staff_qs)
        if error_msg:
            return ResponseWrapper(data=staff_serializer.data, error_msg=error_msg, msg="User already exists so password remains unchanged. If you forgot  password please try reset password form the app.")
        return ResponseWrapper(data=staff_serializer.data, status=200)

    # def retrieve(self, request, *args, **kwargs):
    #     if request.user is not None:
    #         # user_serializer = self.serializer_class(instance=request.user)
    #         user_serializer = UserAccountSerializer(instance=request.user)
    #         return ResponseWrapper(data=user_serializer.data, status=200)
    #     else:
    #         return ResponseWrapper(data="No User found", status=400)

    def owner_info(self, request, id, *args, **kwargs):
        owner_qs = HotelStaffInformation.objects.filter(
            restaurant_id=id, is_owner=True)
        serializer = StaffInfoGetSerializer(instance=owner_qs, many=True)
        return ResponseWrapper(data=serializer.data)

    def waiter_info(self, request, id, *args, **kwargs):
        waiter_qs = HotelStaffInformation.objects.filter(
            restaurant_id=id, is_waiter=True)
        serializer = StaffInfoGetSerializer(instance=waiter_qs, many=True)
        return ResponseWrapper(data=serializer.data)

    def delete_staff(self, request, staff_id, *args, **kwargs):
        waiter_qs = HotelStaffInformation.objects.filter(
            pk=staff_id).first()
        if waiter_qs:
            waiter_qs.restaurant = None
            waiter_qs.save()
            waiter_qs.delete()
            return ResponseWrapper(msg="Delete", error_code=200)
        else:
            return ResponseWrapper(msg="waiter is not valid", error_code=400)

    def manager_info(self, request, id, *args, **kwargs):
        manager_qs = HotelStaffInformation.objects.filter(
            restaurant_id=id, is_manager=True)
        serializer = StaffInfoGetSerializer(instance=manager_qs, many=True)
        return ResponseWrapper(data=serializer.data)

    def update(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data, partial=True)
        if serializer.is_valid():
            qs = serializer.update(instance=self.get_object(
            ), validated_data=serializer.validated_data)
            serializer = self.serializer_class(instance=qs)
            qs.user.first_name = request.data.get('name')
            qs.user.save()
            return ResponseWrapper(data=serializer.data)
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)


class UserAccountManagerViewSet(LoggingMixin, viewsets.ModelViewSet):
    logging_methods = ['GET', 'POST', 'PATCH', 'DELETE']

    def get_serializer_class(self):
        """
        Return the class to use for the serializer.
        Defaults to using `self.serializer_class`.

        You may want to override this if you need to provide different
        serializations depending on the incoming request.

        (Eg. admins get full serialization, others get basic serialization)
        """

        if self.action == "create":
            self.serializer_class = UserSignupSerializer
        elif self.action == "update":
            self.serializer_class = UserAccountPatchSerializer
        # elif self.action == "get_otp":

        #     self.serializer_class = None
        else:
            self.serializer_class = UserAccountSerializer

        return self.serializer_class

    def get_permissions(self):
        if self.action == "create" or self.action == "get_otp":
            permission_classes = [permissions.AllowAny]
        elif self.action in ["retrieve", "update"]:
            permission_classes = [permissions.IsAuthenticated]
        else:
            # permissions.DjangoObjectPermissions.has_permission()
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    queryset = User.objects.exclude(status="DEL")

    def create(self, request, *args, **kwargs):
        try:
            # email = request.data.pop("email")
            password = request.data.pop("password")
            phone = request.data["phone"]
            verification_id = uuid.uuid4().__str__()
        except Exception as e:
            return ResponseWrapper(data=e.args, status=401)

        try:
            # temp_user = User.objects.
            # email_exist = User.objects.filter(email=email).exists()
            phone_exist = User.objects.filter(phone=phone).exists()

            if phone_exist:
                return ResponseWrapper(
                    data="Please use different Phone, it’s already been in use", status=400
                )
            password = make_password(password=password)
            user = User.objects.create(
                # email=email,
                password=password,
                # verification_id=verification_id,
                **request.data
            )
            # if user is None:
            #     return ResponseWrapper(data="Account already exist with given Email or Phone", status=401)
        except Exception as err:
            # logger.exception(msg="error while account cration")
            return ResponseWrapper(
                data="Account creation failed", status=401
            )

        # send_registration_confirmation_email(email)
        user_serializer = UserAccountSerializer(instance=user, many=False)
        return ResponseWrapper(data=user_serializer.data, status=200)

    def update(self, request, *args, **kwargs):
        password = request.data.pop("password", None)
        user_qs = User.objects.filter(pk=request.user.pk)
        first_name = request.data.get('first_name')
        customer_qs, created_customer = CustomerInfo.objects.get_or_create(
            user=user_qs.first())

        # if user_qs:
        if password:
            password = make_password(password=password)
            updated = user_qs.update(password=password, **request.data)
        else:
            updated = user_qs.update(**request.data)
        customer_qs.name = first_name
        customer_qs.save()

        if not updated:
            return ResponseWrapper(error_code=status.HTTP_400_BAD_REQUEST, error_msg=['failed to update'])
        is_apps = request.path.__contains__('/apps/')
        if is_apps:
            customer_info, staff_info, user_serializer = login_related_info(
                user_qs.first())
            return ResponseWrapper(data={'user': user_serializer.data, 'staff_info': staff_info,
                                         'customer_info': customer_info})

        else:
            user_serializer = UserAccountSerializer(
                instance=user_qs.first(), many=False)
        return ResponseWrapper(data=user_serializer.data, status=200)

    def retrieve(self, request, *args, **kwargs):
        if request.user is not None:
            # user_serializer = self.serializer_class(instance=request.user)
            user_serializer = UserAccountSerializer(instance=request.user)
            return ResponseWrapper(data=user_serializer.data, status=200)
        else:
            return ResponseWrapper(data={}, status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, *args, **kwargs):
        if request.user is not None:
            user_serializer = UserAccountSerializer(
                instance=request.user, data={}, partial=True
            )
            user_serializer.update(
                instance=request.user, validated_data={"status": "DEL"}
            )
            if user_serializer.is_valid():
                return ResponseWrapper(data=user_serializer.data, status=200)
        return ResponseWrapper(data="Active account not found", status=400)

    def get_otp(self, request, phone, *args, **kwargs):
        otp = random.randint(1000, 9999)
        otp_qs, _ = OtpUser.objects.get_or_create(phone=str(phone))
        if request.user.pk:
            otp_qs.user = request.user
        otp_qs.otp_code = otp
        otp_qs.save()

        if send_sms(body=f'Your OTP code for I-HOST is {otp} . Thanks for using I-HOST.', phone=str(phone)):
            return ResponseWrapper(msg='otp sent', data={'name': None, 'id': None, 'phone': phone}, status=200)
        else:
            return ResponseWrapper(error_msg='otp sending failed')


class CustomerInfoViewset(LoggingMixin, viewsets.ModelViewSet):
    queryset = CustomerInfo.objects.all()
    lookup_field = 'user'
    logging_methods = ['GET', 'POST', 'PATCH', 'DELETE']
    # http_method_names = ['GET', 'POST', 'PATCH', ]
    serializer_class = CustomerInfoSerializer

    def get_permissions(self):
        if self.action == "list":
            permission_classes = [permissions.IsAdminUser]
        elif self.action in ["retrieve", "update", "create"]:
            permission_classes = [permissions.IsAuthenticated]
        else:
            # permissions.DjangoObjectPermissions.has_permission()
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]


class HotelStaffLogViewSet(CustomViewSet):
    logging_methods = ['GET', 'POST', 'PATCH', 'DELETE']
    pagination_class = CustomLimitPagination

    queryset = APIRequestLog.objects.all()

    def get_serializer_class(self):
        self.serializer_class = LogSerializerGet

        if self.action == "hotel_staff_logger":
            self.serializer_class = LogSerializerPost

        return self.serializer_class

    def get_permissions(self):
        if self.action in ["hotel_staff_logger"]:

            # permission_classes = [permissions.IsAdminUser,custom_permissions.IsRestaurantOwner]

            permission_classes = [
                custom_permissions.IsRestaurantManagementOrAdmin]
            permission_classes = [permissions.IsAuthenticated,
                                  custom_permissions.IsRestaurantManagementOrAdmin]
        else:
            permission_classes = [permissions.IsAdminUser]

        return [permission() for permission in permission_classes]

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter("start_date", openapi.IN_QUERY,
                          type=openapi.FORMAT_DATE),
        openapi.Parameter("end_date", openapi.IN_QUERY,
                          type=openapi.FORMAT_DATE)
    ])
    def hotel_staff_logger(self, request, *args, **kwargs):
        restaurant_id = request.data.get('restaurant')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        log_qs = self.get_queryset().filter(user__hotel_staff__restaurant_id=restaurant_id,
                                            requested_at__gte=start_date, requested_at__lte=end_date).distinct().order_by('-id')

        page_qs = self.paginate_queryset(log_qs)
        serializer = LogSerializerGet(instance=page_qs, many=True)
        paginated_data = self.get_paginated_response(serializer.data)

        return ResponseWrapper(paginated_data.data)
        # return ResponseWrapper(serializer.data)

        # return ResponseWrapper(data=waiter_qs.data,status=200)


class CustomerNotificationViewSet(LoggingMixin, CustomViewSet):
    queryset = FcmNotificationCustomer.objects.all()
    lookup_field = 'pk'
    serializer_class = CustomerNotificationSerializer
    logging_methods = ['DELETE', 'POST', 'PATCH', 'GET']
    permission_classes = [permissions.IsAuthenticated,
                          custom_permissions.IsRestaurantManagementOrAdmin]
    http_method_names = ('post', 'get', 'delete')

    def create(self, request, *args, **kwargs):
        # if not HotelStaffInformation.objects.filter(Q(is_manager=True) | Q(is_owner=True), user=request.user.pk,
        #                                             restaurant_id=request.data.get('restaurant')):
        #     return ResponseWrapper(error_code=status.HTTP_401_UNAUTHORIZED, error_msg=['user is not manager or owner'])
        restaurant_id = request.data.get('restaurant')
        self.check_object_permissions(request, obj=restaurant_id)

        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        if serializer.is_valid():
            qs = serializer.save()
            customer_qs = CustomerFcmDevice.objects.order_by('-pk')[:1000]
            tokens = customer_qs.values_list('token', flat=True)
            send_fcm_push_notification_appointment(
                status="SendCustomerAdvertisement", qs=qs, tokens_list=tokens)
            serializer = self.serializer_class(instance=qs)
            return ResponseWrapper(data=serializer.data, msg='created')
        else:
            return ResponseWrapper(error_msg=serializer.errors, error_code=400)

    def customer_notification_by_restaurant(self, request, restaurant, *args, **kwargs):
        restaurant_qs = FcmNotificationCustomer.objects.filter(
            restaurant_id=restaurant).order_by('-created_at')
        serializer = CustomerNotificationSerializer(
            instance=restaurant_qs, many=True)
        return ResponseWrapper(data=serializer.data)
