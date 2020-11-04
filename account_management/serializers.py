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





class RestaurantUserSignUpSerializer(serializers.Serializer):
    restaurant_id = serializers.IntegerField()
    email = serializers.EmailField()
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

class OtpLoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    otp = serializers.IntegerField(default=1234)
