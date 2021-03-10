from rest_framework_tracking.models import APIRequestLog

from restaurant.models import Restaurant, Subscription, PaymentType, CashLog

from django.http import request
from rest_framework import fields
from rest_framework.serializers import Serializer

from rest_framework import serializers
from .models import CustomerFcmDevice, CustomerInfo, HotelStaffInformation, StaffFcmDevice, UserAccount, FcmNotificationCustomer, models
# from restaurant import serializers as restaurant_serializer

from drf_extra_fields.fields import Base64ImageField
from drf_extra_fields.fields import HybridImageField
from django.core.files.base import ContentFile
# from ..utils.base_64_image import Base64ImageField
# from utils.base_64_image import Base64ImageField
import base64
import six
import uuid
# import imghdr


class CustomerInfoSerializer(serializers.ModelSerializer):
    phone = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CustomerInfo
        fields = '__all__'

    def get_phone(self, obj):
        return obj.user.phone


class UserSignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAccount
        fields = ["phone", "password"]


# class Base64ImageField(serializers.ImageField):

#     def to_internal_value(self, data):

#         # Check if this is a base64 string
#         if isinstance(data, six.string_types):
#             # Check if the base64 string is in the "data:" format
#             if 'data:' in data and ';base64,' in data:
#                 # Break out the header from the base64 content
#                 header, data = data.split(';base64,')

#             # Try to decode the file. Return validation error if it fails.
#             try:
#                 decoded_file = base64.b64decode(data)
#             except TypeError:
#                 self.fail('invalid_image')

#             # Generate file name:
#             # 12 characters are more than enough.
#             file_name = str(uuid.uuid4())[:12]
#             # Get the file name extension:
#             file_extension = self.get_file_extension(file_name, decoded_file)

#             complete_file_name = "%s.%s" % (file_name, file_extension, )

#             data = ContentFile(decoded_file, name=complete_file_name)

#         return super(Base64ImageField, self).to_internal_value(data)

#     def get_file_extension(self, file_name, decoded_file):

#         extension = imghdr.what(file_name, decoded_file)
#         extension = "jpg" if extension == "jpeg" else extension

#         return extension


class StaffInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotelStaffInformation
        fields = ['shift_start', 'shift_end', 'nid', 'image', 'name', 'email']


class RestaurantUserSignUpSerializer(serializers.Serializer):
    restaurant_id = serializers.IntegerField()
    email_address = serializers.EmailField(required=False, allow_blank=True)
    name = serializers.CharField()
    phone = serializers.CharField()
    password = serializers.CharField(required=False)
    shift_start = serializers.TimeField(required=False)
    shift_end = serializers.TimeField(required=False)
    nid = serializers.CharField(required=False)
    image = serializers.ImageField(required=False)


class UserAccountPatchSerializer(serializers.ModelSerializer):
    password = serializers.CharField(required=False)

    class Meta:
        model = UserAccount
        fields = ["password", "first_name"]


class UserAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAccount
        fields = ['phone', 'first_name',
                  'id']


class StaffInfoGetSerializer(serializers.ModelSerializer):
    user = UserAccountSerializer(read_only=True)
    phone = serializers.CharField(source='user.phone', read_only=True)
    first_name = serializers.CharField(source='user.first_name')
    table_no = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = HotelStaffInformation
        fields = [
            "id",
            "first_name",
            "name",
            "user",
            "image",
            "is_manager",
            "is_owner",
            "is_waiter",
            "shift_start",
            "shift_end",
            "nid",
            "restaurant",
            "phone",
            "tables",
            "table_no",
            "email",
        ]

    def get_table_no(self, obj):
        if obj:
            return obj.tables.values_list('table_no', flat=True)
        return []




class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = '__all__'


class PaymentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentType
        fields = '__all__'

class CashLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashLog
        fields = '__all__'


class RestaurantSerializer(serializers.ModelSerializer):
    review = serializers.SerializerMethodField(read_only=True)
    subscription = SubscriptionSerializer(read_only=True)
    payment_type = PaymentTypeSerializer(read_only=True, many=True)
    cash_log = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Restaurant
        fields = '__all__'

    def get_review(self, obj):
        review_qs = None
        if obj.food_orders:

            reviews_list = list(
                filter(None, obj.food_orders.values_list('reviews__rating', flat=True)))
            if reviews_list:
                return {'value': sum(reviews_list) / reviews_list.__len__(), 'total_reviewers': reviews_list.__len__()}
        return {'value': None, 'total_reviewers': 0}
    def get_cash_log(self,obj):
        cash_log_qs = CashLog.objects.filter(restaurant_id = obj.id).last()
        if cash_log_qs:
            return {'id': cash_log_qs.id,
                    'starting_time': cash_log_qs.starting_time,
                 'ending_time':cash_log_qs.ending_time,
                 'in_cash_while_opening':cash_log_qs.in_cash_while_opening,
                 'in_cash_while_closing':cash_log_qs.in_cash_while_closing,
                 'total_received_payment':cash_log_qs.total_received_payment,
                 'total_cash_received':cash_log_qs.total_cash_received,
                 'remarks':cash_log_qs.remarks
                 }

        return None


class StaffLoginInfoGetSerializer(serializers.ModelSerializer):
    restaurant = RestaurantSerializer(read_only=True)

    class Meta:
        model = HotelStaffInformation
        fields = [
            "id",
            "user",
            "image",
            "is_manager",
            "is_owner",
            "is_waiter",
            "shift_start",
            "shift_end",
            "nid",
            "restaurant",
            "name",

        ]


class ListOfIdSerializer(serializers.Serializer):
    id = serializers.ListSerializer(
        child=serializers.IntegerField(), required=False)


class OtpLoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    otp = serializers.IntegerField(default=1234)


class LogSerializerPost(serializers.Serializer):
    restaurant = serializers.IntegerField()


class LogSerializerGet(serializers.ModelSerializer):
    class Meta:
        model = APIRequestLog
        exclude = ['response']


class CheckFcmSerializer(serializers.Serializer):
    token = serializers.CharField()

class StaffFcmDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffFcmDevice
        fields = "__all__"


class CustomerFcmDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerFcmDevice
        fields = "__all__"


class CustomerNotificationSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = FcmNotificationCustomer
        fields = [
            "id",
            "title",
            "body",
            "image",
            "restaurant",
            "data"
        ]

    def create(self, validated_data):
        image = validated_data.pop('image', None)
        if image:
            return FcmNotificationCustomer.objects.create(image=image, **validated_data)
        return FcmNotificationCustomer.objects.create(**validated_data)
