from drf_extra_fields.fields import Base64ImageField
import copy
from account_management.models import HotelStaffInformation
from account_management.serializers import StaffInfoGetSerializer
from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault
from utils.calculate_price import calculate_item_price_with_discount, calculate_price

from .models import *


class FoodOptionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodOptionType
        # fields = '__all__'
        exclude = ['deleted_at']


class FoodExtraTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodExtraType
        # fields = '__all__'
        exclude = ['deleted_at']


class FoodExtraSerializer(serializers.ModelSerializer):
    extra_type = FoodExtraTypeSerializer(read_only=True)

    class Meta:
        model = FoodExtra
        # fields = '__all__'
        exclude = ['deleted_at']


class FoodExtraGroupByListSerializer(serializers.ListSerializer):

    def to_representation(self, data):
        iterable = data.all() if isinstance(data, models.Manager) else data
        return [
            {'extras': super(FoodExtraGroupByListSerializer, self).to_representation(
                FoodExtra.objects.filter(extra_type=extra_type, pk__in=list(
                    data.values_list('id', flat=True)
                ))
            ),
                'type_name': extra_type.name,
                'type_id': extra_type.pk
            }
            for extra_type in FoodExtraType.objects.filter(pk__in=list(data.values_list('extra_type_id', flat=True)))
        ]

    # def to_representation(self, data):
    #     iterable = data.all() if isinstance(data, models.Manager) else data
    #     return {

    #         extra_type.name: super(FoodExtraGroupByListSerializer, self).to_representation(
    #             FoodExtra.objects.filter(extra_type=extra_type, pk__in=list(
    #                 data.values_list('id', flat=True)
    #             ))
    #         )
    #         for extra_type in FoodExtraType.objects.filter(pk__in=list(data.values_list('extra_type_id', flat=True)))
    #     }


class FoodExtraGroupByTypeSerializer(serializers.ModelSerializer):
    # extra_type = FoodExtraTypeSerializer(read_only=True)

    class Meta:
        model = FoodExtra
        fields = ['id', 'name', 'price']

        list_serializer_class = FoodExtraGroupByListSerializer


class FoodExtraPostPatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodExtra
        # fields = '__all__'
        exclude = ['deleted_at']


class FoodExtraTypeDetailSerializer(serializers.ModelSerializer):
    extra_type = FoodExtraTypeSerializer(read_only=True)

    class Meta:
        model = FoodExtra
        fields = '__all__'


class FoodCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodCategory
        # fields = '__all__'
        exclude = ['deleted_at']


class FoodOptionSerializer(serializers.ModelSerializer):
    option_type = FoodOptionTypeSerializer(read_only=True)

    class Meta:
        model = FoodOption
        # fields = '__all__'
        exclude = ['deleted_at']


class FoodOptionBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodOption
        # fields = '__all__'
        exclude = ['deleted_at']


"""
class FoodOptionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodOptionType
        fields = '__all__'
"""


class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        # fields = '__all__'
        exclude = ['deleted_at']
    



class TableSerializer(serializers.ModelSerializer):
    staff_assigned = StaffInfoGetSerializer(read_only=True, many=True)

    class Meta:
        model = Table
        # fields = '__all__'
        exclude = ['deleted_at']


class StaffTableSerializer(serializers.ModelSerializer):
    staff_assigned = StaffInfoGetSerializer(read_only=True, many=True)
    my_table = serializers.SerializerMethodField(
        read_only=True, required=False)

    class Meta:
        model = Table
        fields = ['table_no',
                  'restaurant',
                  'name',
                  'staff_assigned',
                  'is_occupied',
                  'my_table',
                  'id',
                  ]
        #ordering = ['table_no']

    def get_my_table(self, obj):
        user = self.context.get('user')
        assigned_pk_list = obj.staff_assigned.values_list('pk', flat=True)
        if user.pk in assigned_pk_list:
            return True
        return False


class StaffIdListSerializer(serializers.Serializer):
    staff_list = serializers.ListSerializer(child=serializers.IntegerField())


class FoodExtraBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodExtra
        # fields = '__all__'
        exclude = ['deleted_at']


class OrderedItemSerializer(serializers.ModelSerializer):
    food_extra = FoodExtraTypeDetailSerializer(many=True, read_only=True)

    class Meta:
        model = OrderedItem
        fields = '__all__'


class OrderedItemGetDetailsSerializer(serializers.ModelSerializer):
    food_extra = FoodExtraBasicSerializer(many=True, read_only=True)
    food_option = FoodOptionSerializer(read_only=True)
    food_name = serializers.CharField(
        source="food_option.food.name", read_only=True)
    food_image = serializers.ImageField(
        source="food_option.food.image", read_only=True)
    # food_image = serializers.SerializerMethodField(read_only=True)
    price = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = OrderedItem
        fields = [
            "id",
            "quantity",
            "food_order",
            "status",
            "food_name",
            "food_image",
            "food_option",
            "food_extra",
            "price",

        ]
        ordering = ['id']

    def get_price(self, obj):
        return calculate_item_price_with_discount(ordered_item_qs=obj)

    # def get_food_image(self,obj):
    #   if obj.food_options.food.image:
    #      return serializers.ImageField(source="food_option.food.image")
    # else:
    # return None


class FoodOrderConfirmSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    food_items = serializers.ListSerializer(child=serializers.IntegerField())


class PaymentSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()


class ReorderSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    table_id = serializers.IntegerField()
    # ordred_items = serializers.ListSerializer(child=serializers.IntegerField)


class OrderedItemUserPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderedItem
        # fields = '__all__'
        exclude = ['status']


class OrderedItemDashboardPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderedItem
        fields = '__all__'


class FoodOrderCancelSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()


class FoodOptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodOption
        fields = '__all__'


class FoodOrderSerializer(serializers.ModelSerializer):
    status_detail = serializers.CharField(source='get_status_display')
    price = serializers.SerializerMethodField()
    ordered_items = OrderedItemGetDetailsSerializer(many=True, read_only=True)

    # TODO: write a ordered item serializer where each foreign key details are also shown in response

    class Meta:
        model = FoodOrder
        fields = ['id',
                  "remarks",
                  'status_detail',
                  "table",
                  "status",
                  "price",
                  'ordered_items',
                  #   'grand_total_price',
                  #   "total_price",
                  #   "discount_amount",
                  #   "tax_amount",
                  #   "tax_percentage",
                  #   "service_charge",
                  #   "payable_amount",
                  ]

    def get_price(self, obj):
        return calculate_price(food_order_obj=obj, include_initial_order=True)


class FoodOrderByTableSerializer(serializers.ModelSerializer):
    status_details = serializers.CharField(source='get_status_display')
    # table_name = serializers.CharField(source="table.name")
    table_name = serializers.SerializerMethodField(read_only=True)
    table_no = serializers.SerializerMethodField(read_only=True)
    # table_no = serializers.CharField(source="table.table_no")
    waiter = serializers.SerializerMethodField(read_only=True)
    price = serializers.SerializerMethodField()
    ordered_items = OrderedItemGetDetailsSerializer(many=True, read_only=True)
    restaurant_info = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = FoodOrder
        fields = ['id',
                  "remarks",
                  "table",
                  "status",
                  'status_details',
                  "price",
                  'ordered_items',
                  'table_name',
                  'table_no',
                  'waiter',
                  'restaurant_info',
                  #   'grand_total_price',
                  #   "total_price",
                  #   "discount_amount",
                  #   "tax_amount",
                  #   "tax_percentage",
                  #   "service_charge",
                  #   "payable_amount",
                  ]
        # ordering = ['table']

    def get_price(self, obj):
        return calculate_price(food_order_obj=obj)

    def get_waiter(self, obj):
        if obj.table:
            qs = obj.table.staff_assigned.filter(is_waiter=True).first()
            if qs:
                return {"name": qs.user.first_name, 'id': qs.pk}
        return {}

    def get_restaurant_info(self, obj):
        restaurant_qs = None
        if obj.table:
            restaurant_qs = obj.table.restaurant

        else:
            ordered_items_qs = obj.ordered_items.first()
            if ordered_items_qs:
                restaurant_qs = ordered_items_qs.food_option.food.restaurant

        if restaurant_qs:
            return {
                'id': restaurant_qs.pk,
                'name': restaurant_qs.name,
                'phone': restaurant_qs.phone,
                'vat_registration_no': restaurant_qs.vat_registration_no,
                'trade_licence_no': restaurant_qs.trade_licence_no
            }
        else:
            return {}

    def get_table_name(self, obj):
        if obj.table:
            return obj.table.name
        else:
            return None

    def get_table_no(self, obj):
        if obj.table:
            return obj.table.table_no
        else:
            return None


class FoodOrderForStaffSerializer(serializers.ModelSerializer):
    # status = serializers.CharField(source='get_status_display')
    price = serializers.SerializerMethodField()

    class Meta:
        model = FoodOrder
        fields = ['id',
                  "remarks",
                  "table",
                  "status",
                  "price",
                  #   'grand_total_price',
                  #   "total_price",
                  #   "discount_amount",
                  #   "tax_amount",
                  #   "tax_percentage",
                  #   "service_charge",
                  #   "payable_amount",
                  ]

    # def get_status(self, obj):
    #     return obj.get_status_display()
    def get_price(self, obj):
        return calculate_price(food_order_obj=obj)


class FoodOrderUserPostSerializer(serializers.ModelSerializer):
    ordered_items = OrderedItemSerializer(
        many=True, read_only=True, required=False)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = FoodOrder
        fields = ['ordered_items', 'table', 'remarks', 'status', 'id']


class TakeAwayFoodOrderPostSerializer(serializers.Serializer):
    restaurant = serializers.IntegerField()
    table = serializers.IntegerField(required=False)


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
    image = Base64ImageField()

    class Meta:
        model = Food
        fields = [
            "name",
            "image",
            "description",
            "restaurant",
            "is_top",
            "is_recommended",
            'price',
            'ingredients',
            'category',
            'id',
            'discount',
        ]

        # extra_kwargs = {
        # 'price': {'max_digits': 16, 'decimal_places': 2}

    # }
    def get_price(self, obj):
        option_qs = obj.food_options.order_by('price').first()
        if option_qs:
            return round(option_qs.price, 2)
        else:
            return None
    def create(self, validated_data):
        image = validated_data.pop('image', None)
        if image:
            return Food.objects.create(image=image, **validated_data)
        return Food.objects.create(**validated_data)
    


class FoodsByCategorySerializer(serializers.ModelSerializer):
    foods = FoodWithPriceSerializer(many=True)

    class Meta:
        model = FoodCategory
        fields = ['id', 'name', 'image', 'foods']


class FoodDetailSerializer(serializers.ModelSerializer):
    category = FoodCategorySerializer(read_only=True)
    food_extras = FoodExtraGroupByTypeSerializer(read_only=True, many=True)
    food_options = FoodOptionSerializer(read_only=True, many=True)
    price = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Food
        fields = [
            'id',
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
            'price',
        ]

    def get_price(self, obj):
        option_qs = obj.food_options.order_by('price').first()
        if option_qs:
            return round(option_qs.price, 2)
        else:
            return None


class RestaurantUpdateSerialier(serializers.ModelSerializer):
    logo = Base64ImageField()
    class Meta:
        model = Restaurant
        exclude = ['status', 'subscription', 'subscription_ends', 'deleted_at']
    
        def update(self, validated_data):
            logo = validated_data.pop('logo', None)
            if logo:
                return Restaurant.objects.create(logo=logo, **validated_data)
            return Restaurant.objects.create(**validated_data)


class RestaurantContactPersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestaurantContactPerson
        fields = '__all__'


class HotelStaffInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotelStaffInformation
        fields = '__all__'


class TableStaffSerializer(serializers.ModelSerializer):
    # staff_assigned = StaffInfoGetSerializer(read_only=True, many=True)
    # order_item = OrderedItemSerializer(read_only=True, many=True)
    order_info = serializers.SerializerMethodField(read_only=True)

    # id = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Table
        fields = ['table_no', 'restaurant',
                  'is_occupied', 'name', 'order_info', 'id']

    def get_order_info(self, obj):
        total_items = 0
        total_served_items = 0

        if obj.is_occupied:
            order_qs = obj.food_orders.exclude(
                status__in=["5_PAID", "6_CANCELLED"]).order_by('-id').first()
            # item_qs = OrderedItem.objects.filter(food_order=order_qs)

            if not order_qs:
                return {}

            total_items += order_qs.ordered_items.count()

            if order_qs:
                total_served_items += order_qs.ordered_items.count()
            serializer = FoodOrderForStaffSerializer(order_qs)
            temp_data_dict = serializer.data
            price = temp_data_dict.pop('price', {})
            temp_data_dict.update(price)
            temp_data_dict['total_items'] = total_items
            temp_data_dict['total_served_items'] = total_served_items
            return temp_data_dict
        else:
            return {}


class FoodExtraByFoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodExtra
        fields = '__all__'


class TopRecommendedFoodListSerializer(serializers.Serializer):
    food_id = serializers.ListSerializer(child=serializers.IntegerField())
    is_top = serializers.BooleanField()
    is_recommended = serializers.BooleanField()


class InvoiceSerializer(serializers.ModelSerializer):
    order_info = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Invoice
        fields = ['order_info']

    def get_order_info(self, obj):
        # data_dict = obj.__dict__
        obj.__dict__.pop('_state', None)
        order_info = obj.__dict__.pop('order_info', {})
        order_info['invoice'] = obj.__dict__
        return order_info


class InvoiceGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = '__all__'


class ReportingDateRangeGraphSerializer(serializers.Serializer):
    from_date = serializers.DateField(required=False)
    to_date = serializers.DateField(required=False)
    order_status = serializers.ChoiceField(choices=[("0_ORDER_INITIALIZED", "Table Scanned"),
                                                    ("1_ORDER_PLACED",
                                                     "User Confirmed"),
                                                    ("2_ORDER_CONFIRMED",
                                                     "In Kitchen"),
                                                    ("3_IN_TABLE", "Food Served"),
                                                    ("5_PAID", "Payment Done"),
                                                    ("6_CANCELLED", "Cancelled"), ], default="5_PAID", required=False)


class DiscountByFoodSerializer(serializers.Serializer):
    discount_id = serializers.IntegerField()
    food_id_lists = serializers.ListSerializer(
        child=serializers.IntegerField())


class DiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        # fields ='__all__'
        exclude = ['deleted_at']


class FoodDetailsByDiscountSerializer(serializers.ModelSerializer):
    discount = DiscountSerializer(read_only=True, many=True)

    class Meta:
        model = Food
        fields = ['id','image', 'discount']


class ReportDateRangeSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    restaurant_id = serializers.IntegerField(required=True)


class StaffFcmSerializer(serializers.Serializer):
    table_id = serializers.IntegerField()


class CollectPaymentSerializer(serializers.Serializer):
    table_id = serializers.IntegerField()
    payment_method = serializers.CharField()


class PopUpSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = PopUp
        fields = '__all__'

    def create(self, validated_data):
        image = validated_data.pop('image', None)
        if image:
            return PopUp.objects.create(image=image, **validated_data)
        return PopUp.objects.create(**validated_data)
