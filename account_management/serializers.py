from rest_framework.serializers import Serializer
import restaurant
from restaurant.models import Restaurant
from rest_framework import serializers
from .models import UserAccount


class UserSignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAccount
        fields = ["phone", "password"]


class RestaurantUserSignUpSerializer(UserSignupSerializer):
    restaurant_id = serializers.IntegerField(read_only=True)


class UserAccountPatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAccount
        exclude = ["password"]


class UserAccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserAccount
        fields = ['phone', 'first_name', 'last_name']


class OtpLoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
