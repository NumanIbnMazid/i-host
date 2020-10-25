from account_management.models import UserAccount
from account_management.models import UserAccount as User
from account_management.serializers import UserAccountPatchSerializer, UserAccountSerializer, UserSignupSerializer
from django.shortcuts import render
from rest_framework import permissions

# Create your views here.
from knox.views import LoginView as KnoxLoginView
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import uuid
from rest_framework import viewsets
from django.contrib.auth import login
from utils.response_wrapper import ResponseWrapper
from rest_framework.authtoken.serializers import AuthTokenSerializer
from drf_yasg2.utils import swagger_auto_schema


class LoginView(KnoxLoginView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = AuthTokenSerializer

    @swagger_auto_schema(request_body=AuthTokenSerializer)
    def post(self, request, format=None):
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        return super(LoginView, self).post(request, format=None)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_login(request):
    return ResponseWrapper(data="Token is Valid", status=200)


class UserAccountManagerViewSet(viewsets.ModelViewSet):

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
        else:
            self.serializer_class = UserAccountSerializer

        return self.serializer_class

    def get_permissions(self):
        if self.action == "create":
            permission_classes = [permissions.AllowAny]
        elif self.action == "retrieve" or self.action == "update":
            permission_classes = [permissions.IsAuthenticated]
        else:
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

            user = User.objects.create_user(
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

    def retrieve(self, request, *args, **kwargs):
        if request.user is not None:
            # user_serializer = self.serializer_class(instance=request.user)
            user_serializer = UserAccountSerializer(instance=request.user)
            return ResponseWrapper(data=user_serializer.data, status=200)
        else:
            return ResponseWrapper(data="No User found", status=400)

#     # @swagger_auto_schema(request_body=TravellerAccountDetailSerializer)
#     # def update(self, request, *args, **kwargs):
#     #     if request.user is not None:
#     #         user = User.objects.get(id=request.user.id)
#     #         # print(user.primary_traveller_id)
#     #         # print(user.primary_traveller.pk)
#     #         traveller = TravellerAccount.objects.get(
#     #             traveller_id=user.primary_traveller.pk)
#     #         # print(traveller)
#     #         if "present_address" in request.data:
#     #             present_address = request.data.pop("present_address")
#     #             present_address_serializer = AddressInformationSerializer(
#     #                 present_address)
#     #             if traveller.present_address is None:
#     #                 present_address_record = present_address_serializer.create(
#     #                     validated_data=present_address)
#     #                 traveller.present_address = present_address_record
#     #                 traveller.save()
#     #             else:
#     #                 present_address_serializer.update(instance=traveller.present_address,
#     #                                                   validated_data=present_address)
#     #         if "permanent_address" in request.data:
#     #             permanent_address = request.data.pop("permanent_address")
#     #             permanent_address_serializer = AddressInformationSerializer(
#     #                 permanent_address)
#     #             if traveller.permanent_address is None:
#     #                 permanent_address_record = present_address_serializer.create(
#     #                     validated_data=present_address)
#     #                 traveller.permanent_address = permanent_address_record
#     #                 traveller.save()
#     #             else:
#     #                 permanent_address_serializer.update(instance=traveller.permanent_address,
#     #                                                     validated_data=permanent_address)

#     #         # print("address saved")
#     #         traveller_serializer = TravellerAccountDetailSerializer(traveller)
#     #         traveller_serializer.update(
#     #             instance=traveller, validated_data=request.data)
#     #         return ResponseWrapper(data=traveller_serializer.data, status=200)

#     #         # user_primary_traveller_serializer = TravellerAccountDetailSerializer(
#     #         #     instance=user.primary_traveller, data=request.data, partial=True
#     #         # )
#     #         # user_primary_traveller_serializer.update(instance=user.primary_traveller, validated_data=request.data)
#     #         # # self.serializer_class.update(instance=request.user,validated_data=request.data)
#     #         # if user_primary_traveller_serializer.is_valid():
#     #         #     return ResponseWrapper(data=user_primary_traveller_serializer.data, status=200)

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
