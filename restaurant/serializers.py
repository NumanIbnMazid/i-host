from account_management.serializers import StaffInfoGetSerializer
from os import read
from django.db.models.fields.related import RelatedField
from account_management.models import HotelStaffInformation, UserManager
from utils.response_wrapper import ResponseWrapper
from django.db.models import fields
from rest_framework.serializers import Serializer
from .models import *
from django.db.models import Q, query_utils, Min
from rest_framework import serializers


class FoodOptionExtraTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodOptionExtraType
        fields = '__all__'


class FoodExtraSerializer(serializers.ModelSerializer):
    extra_type = FoodOptionExtraTypeSerializer(read_only=True)

    class Meta:
        model = FoodExtra
        fields = '__all__'


class FoodExtraPostPatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodExtra
        fields = '__all__'


class FoodCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodCategory
        fields = '__all__'


class FoodOptionSerializer(serializers.ModelSerializer):
    option_type = FoodOptionExtraTypeSerializer(read_only=True)

    class Meta:
        model = FoodOption
        fields = '__all__'


class RestaurantSerializer(serializers.ModelSerializer):

    class Meta:
        model = Restaurant
        fields = '__all__'


class TableSerializer(serializers.ModelSerializer):
    staff_assigned = StaffInfoGetSerializer(read_only=True, many=True)

    class Meta:
        model = Table
        fields = '__all__'


class OrderedItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderedItem
        fields = '__all__'


class OrderedItemUserPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderedItem
        # fields = '__all__'
        exclude = ['status']


class FoodOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodOrder
        fields = '__all__'


class FoodOrderUserPostSerializer(serializers.ModelSerializer):
    ordered_items = OrderedItemSerializer(
        many=True, read_only=True, required=False)

    class Meta:
        model = FoodOrder
        fields = ['ordered_items', 'table', 'remarks']


class AddItemsSerializer(serializers.Serializer):
    ordered_items = OrderedItemUserPostSerializer(
        many=True, required=True)


class FoodSerializer(serializers.ModelSerializer):
    category = FoodCategorySerializer(read_only=True)

    class Meta:
        model = Food
        fields = '__all__'


class FoodWithPriceSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Food
        fields = [
            "name",
            "image",
            "description",
            "restaurant",
            "is_top",
            "is_recommended",
            # "food_options",
            'price',
            'ingredients',
        ]

    def get_price(self, obj):
        option_qs = obj.food_options.order_by('price').first()
        if option_qs:
            return option_qs.price
        else:
            return None


class FoodsByCategorySerializer(serializers.ModelSerializer):
    foods = FoodWithPriceSerializer(many=True)

    class Meta:
        model = FoodCategory
        fields = ['id', 'name', 'image', 'foods']


class FoodDetailSerializer(serializers.ModelSerializer):
    category = FoodCategorySerializer(read_only=True)
    food_extras = FoodExtraSerializer(read_only=True, many=True)
    food_options = FoodOptionSerializer(read_only=True, many=True)

    class Meta:
        model = Food
        fields = [
            "name",
            "image",
            "description",
            "restaurant",
            "category",
            "is_top",
            "is_recommended",
            "food_extras",
            "food_options",
            'ingredients',
        ]


class RestaurantUpdateSerialier(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        exclude = ['status', 'subscription', 'subscription_ends']


class RestaurantContactPersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestaurantContactPerson
        fields = '__all__'


class HotelStaffInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotelStaffInformation
        fields = '__all__'
