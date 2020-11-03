
from utils.response_wrapper import ResponseWrapper
from django.db.models import fields
from rest_framework.serializers import Serializer
from .models import *
from rest_framework import serializers


class FoodCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodCategory
        fields = '__all__'

class RestaurantSerializer(serializers.ModelSerializer):

    class Meta:
        model = Restaurant
        fields = '__all__'


class RestaurantUpdateSerialier(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        exclude = ['status', 'subscription', 'subscription_ends']


class RestaurantContactPerson(serializers.ModelSerializer):
    class Meta:
        model = RestaurantContactPerson
        fields = '__all__'
