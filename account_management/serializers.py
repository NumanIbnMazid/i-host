from rest_framework import fields
from rest_framework.serializers import Serializer
import restaurant
from restaurant.models import Restaurant, models
from rest_framework import serializers
from .models import HotelStaffInformation, UserAccount


class UserSignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAccount
        fields = ["phone", "password"]


class StaffInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotelStaffInformation
        fields = ['shift_start', 'shift_end', 'nid', 'shift_days']


class StaffInfoGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotelStaffInformation
        fields = '__all__'


class RestaurantUserSignUpSerializer(serializers.Serializer):
    restaurant_id = serializers.IntegerField()
    staff_info = StaffInfoSerializer(required=False)

    class Meta(UserSignupSerializer.Meta):
        fields = UserSignupSerializer.Meta.fields + \
            ['restaurant_id', 'staff_info']


class UserAccountPatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAccount
        fields = ["password", "first_name", "date_of_birth"]


class UserAccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserAccount
        fields = ['phone', 'first_name', 'last_name', 'date_of_birth']


class OtpLoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    otp = serializers.IntegerField(default=1234)
