from restaurant.models import Restaurant

from django.http import request
from rest_framework import fields
from rest_framework.serializers import Serializer

from rest_framework import serializers
from .models import CustomerInfo, HotelStaffInformation, UserAccount, models

from drf_extra_fields.fields import Base64ImageField
from drf_extra_fields.fields import HybridImageField
from django.core.files.base import ContentFile
import base64
import six
import uuid
import imghdr


class CustomerInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerInfo
        fields = '__all__'


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
        fields = ['shift_start', 'shift_end', 'nid', 'image', 'name']


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
        fields = ["password"]


class UserAccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserAccount
        fields = ['phone',
                  'id']


class StaffInfoGetSerializer(serializers.ModelSerializer):
    user = UserAccountSerializer(read_only=True)
    phone = serializers.CharField(source='user.phone', read_only=True)
    # first_name = serializers.CharField(source='user.first_name')

    class Meta:
        model = HotelStaffInformation
        fields = [
            "id",
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
        ]


class RestaurantSerializer(serializers.ModelSerializer):

    class Meta:
        model = Restaurant
        fields = '__all__'


class StaffLoginInfoGetSerializer(serializers.ModelSerializer):
    restaurant = RestaurantSerializer(read_only=True)

    class Meta:
        model = HotelStaffInformation
        fields = [
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
