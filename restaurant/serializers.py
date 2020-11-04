
from utils.response_wrapper import ResponseWrapper
from django.db.models import fields
from rest_framework.serializers import Serializer
from .models import *
from rest_framework import serializers


class FoodOptionExtraTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodOptionExtraType
        fields = '__all__'


class FoodExtraSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodExtra
        fields = '__all__'


class FoodCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodCategory
        fields = '__all__'


class FoodOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodOption
        fields = '__all__'


class RestaurantSerializer(serializers.ModelSerializer):

    class Meta:
        model = Restaurant
        fields = '__all__'


class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = '__all__'


class FoodOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodOrder
        fields = '__all__'


class OrderedItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderedItem
        fields = '__all__'


class FoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Food
        fields = '__all__'
        
class RestaurantUpdateSerialier(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        exclude = ['status', 'subscription', 'subscription_ends']


class RestaurantContactPerson(serializers.ModelSerializer):
    class Meta:
        model = RestaurantContactPerson
        fields = '__all__'


class RestaurantContactPerson(serializers.ModelSerializer):
    class Meta:
        model = RestaurantContactPerson
        fields = '__all__'

