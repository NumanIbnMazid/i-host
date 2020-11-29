from utils.custom_viewset import CustomViewSet
from restaurant.serializers import HotelStaffInformationSerializer
import uuid
from uuid import uuid4
import restaurant
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model, login
from django.contrib.auth.signals import user_logged_in
from django.shortcuts import render
from django.utils import timezone
from drf_yasg2.utils import swagger_auto_schema
from knox.models import AuthToken
# Create your views here.
from knox.views import LoginView as KnoxLoginView
from rest_framework import permissions, status, viewsets
from rest_framework.authentication import BasicAuthentication
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from restaurant.models import Restaurant
from utils.response_wrapper import ResponseWrapper

from account_management.models import CustomerInfo, HotelStaffInformation
from account_management.models import UserAccount
from account_management.models import UserAccount as User
from account_management.serializers import (CustomerInfoSerializer, OtpLoginSerializer,
                                            RestaurantUserSignUpSerializer, StaffInfoGetSerializer, StaffInfoSerializer,
                                            StaffLoginInfoGetSerializer,
                                            UserAccountPatchSerializer,
                                            UserAccountSerializer,
                                            UserSignupSerializer)

from rest_framework_tracking.mixins import LoggingMixin


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
        user_serializer = UserAccountSerializer(instance=user)
        staff_info = {}
        if user.hotel_staff.first():
            staff_info_serializer = StaffLoginInfoGetSerializer(
                instance=user.hotel_staff.all(), many=True)
            staff_info = staff_info_serializer.data

        return ResponseWrapper(data={'auth': data, 'user': user_serializer.data, 'staff_info': staff_info})


class OtpSignUpView(KnoxLoginView):
    permission_classes = (permissions.AllowAny,)

    # TODO:need to check if otp is same

    @swagger_auto_schema(request_body=OtpLoginSerializer)
    def post(self, request, format=None):
        if request.data.get('otp') != 1234:
            return ResponseWrapper(error_code=status.HTTP_401_UNAUTHORIZED, error_msg=['otp mismatched'])
        token_limit_per_user = self.get_token_limit_per_user()
        user_qs = User.objects.filter(phone=request.data.get('phone')).first()
        if not user_qs:
            user_qs = User.objects.create_user(
                phone=request.data.get('phone'),
                password=uuid.uuid4().__str__()
            )

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
        if self.action in ["create_owner", "create_manager"]:
            #     permission_classes = [permissions.AllowAny]
            # elif self.action in ["retrieve", "update"]:
            #     permission_classes = [permissions.IsAuthenticated]
            # else:
            # permissions.DjangoObjectPermissions.has_permission()
            permission_classes = [permissions.IsAdminUser]
        elif self.action in ["manager_info", "waiter_info"]:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    queryset = HotelStaffInformation.objects.all()
    lookup_field = 'pk'

    def create_owner(self, request, *args, **kwargs):
        return self.create_staff(request, is_owner=True)

    def create_manager(self, request, *args, **kwargs):
        # email = request.data.pop("email")
        return self.create_staff(request, is_manager=True)

    def create_waiter(self, request, *args, **kwargs):
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

        if serializer.data.get("email"):
            user_info_dict['email'] = serializer.data.get("email")

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
        if not user_qs:
            password = make_password(password=password)
            user_qs = User.objects.create(
                password=password,
                **user_info_dict
            )
        else:
            User.objects.filter(phone=phone).update(**user_info_dict)

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

    def update(self, request, **kwargs):
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
        password = request.data.pop("password",None)
        user_qs = User.objects.filter(pk=request.user.pk)

        # if user_qs:
        if password:
            password = make_password(password=password)
            updated = user_qs.update(password=password, **request.data)
        else:
            updated = user_qs.update(**request.data)

        if not updated:
            return ResponseWrapper(error_code=status.HTTP_400_BAD_REQUEST, error_msg=['failed to update'])
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

    def get_otp(self, request, phone, **kwargs):
        return ResponseWrapper(msg='otp sent', status=200)


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


class HotelStaffLogViewSet(LoggingMixin,viewsets.ModelViewSet):
    def get_permissions(self):
        if self.action == "post":
            permission_classes = [permissions.IsAdminUser]
