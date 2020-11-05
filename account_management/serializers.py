from rest_framework import fields
from rest_framework.serializers import Serializer
import restaurant
from restaurant.models import Restaurant, models
from rest_framework import serializers
from .models import HotelStaffInformation, UserAccount

# from drf_extra_fields.fields import Base64ImageField
# from drf_extra_fields.fields import HybridImageField
from django.core.files.base import ContentFile
import base64
import six
import uuid
import imghdr


class UserSignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAccount
        fields = ["phone", "password"]


class Base64ImageField(serializers.ImageField):

    def to_internal_value(self, data):

        # Check if this is a base64 string
        if isinstance(data, six.string_types):
            # Check if the base64 string is in the "data:" format
            if 'data:' in data and ';base64,' in data:
                # Break out the header from the base64 content
                header, data = data.split(';base64,')

            # Try to decode the file. Return validation error if it fails.
            try:
                decoded_file = base64.b64decode(data)
            except TypeError:
                self.fail('invalid_image')

            # Generate file name:
            # 12 characters are more than enough.
            file_name = str(uuid.uuid4())[:12]
            # Get the file name extension:
            file_extension = self.get_file_extension(file_name, decoded_file)

            complete_file_name = "%s.%s" % (file_name, file_extension, )

            data = ContentFile(decoded_file, name=complete_file_name)

        return super(Base64ImageField, self).to_internal_value(data)

    def get_file_extension(self, file_name, decoded_file):

        extension = imghdr.what(file_name, decoded_file)
        extension = "jpg" if extension == "jpeg" else extension

        return extension


class StaffInfoSerializer(serializers.ModelSerializer):
    image = Base64ImageField(
        max_length=None, use_url=True,
    )

    class Meta:
        model = HotelStaffInformation
        fields = ['shift_start', 'shift_end', 'nid', 'shift_days', 'image']

    # def create(self, validated_data):
    #     image = validated_data.pop('image')
    #     return HotelStaffInformation.objects.create(image=image, **validated_data)


class RestaurantUserSignUpSerializer(serializers.Serializer):
    restaurant_id = serializers.IntegerField()
    email = serializers.EmailField(required=False, allow_blank=True)
    first_name = serializers.CharField()
    staff_info = StaffInfoSerializer(required=False)
    phone = serializers.CharField()
    password = serializers.CharField(required=False)


class UserAccountPatchSerializer(serializers.ModelSerializer):
    password = serializers.CharField(required=False)

    class Meta:
        model = UserAccount
        fields = ["password", "first_name", "date_of_birth", "email"]


class UserAccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserAccount
        fields = ['phone', 'first_name', 'last_name', 'date_of_birth', 'email']


class StaffInfoGetSerializer(serializers.ModelSerializer):
    user = UserAccountSerializer(read_only=True)

    class Meta:
        model = HotelStaffInformation
        fields = '__all__'


class ListOfIdSerializer(serializers.Serializer):
    id = serializers.ListSerializer(
        child=serializers.IntegerField(), required=False)


class OtpLoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    otp = serializers.IntegerField(default=1234)
