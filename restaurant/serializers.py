from django.contrib.postgres import fields
from django.http import request
from drf_extra_fields.fields import Base64FileField, Base64ImageField
import copy
from account_management.models import FcmNotificationStaff, HotelStaffInformation
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
        # fields = '__all__'
        exclude = ['deleted_at']


class FoodCategorySerializer(serializers.ModelSerializer):
    # image = Base64FileField()
    class Meta:
        model = FoodCategory
        # fields = '__all__'
        exclude = ['deleted_at']

    # def create(self, validated_data):
    #     image = validated_data.pop('image', None)
    #     if image:
    #         return FoodCategory.objects.create(image=image, **validated_data)
    #     return FoodCategory.objects.create(**validated_data)


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


class SubscriptionSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Subscription
        fields = '__all__'
        # extra_kwargs = {
        #     'code': {'read_only': False}
        # }

    def create(self, validated_data):
        image = validated_data.pop('image', None)
        if image:
            return Subscription.objects.create(image=image, **validated_data)
        return Subscription.objects.create(**validated_data)


class PaymentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentType
        fields = '__all__'


class RestaurantSerializer(serializers.ModelSerializer):
    review = serializers.SerializerMethodField(read_only=True)
    subscription = SubscriptionSerializer(read_only=True)
    payment_type = PaymentTypeSerializer(read_only=True, many=True)

    class Meta:
        model = Restaurant
        # fields = '__all__'
        exclude = ['deleted_at']

    def get_review(self, obj):
        review_qs = None
        if obj.food_orders:

            reviews_list = list(
                filter(None, obj.food_orders.values_list('reviews__rating', flat=True)))
            if reviews_list:
                return {'value': sum(reviews_list) / reviews_list.__len__(), 'total_reviewers': reviews_list.__len__()}
        return {'value': None, 'total_reviewers': 0}


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
    category_name = serializers.SerializerMethodField(read_only=True)
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
            "category_name",

        ]
        ordering = ['id']

    def get_price(self, obj):
        return calculate_item_price_with_discount(ordered_item_qs=obj)

    def get_category_name(self, obj):
        try:
            return obj.food_option.food.category.name
        except:
            return None

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


# class FoodOrderSerializer(serializers.ModelSerializer):
#     status_detail = serializers.CharField(source='get_status_display')
#     price = serializers.SerializerMethodField()
#     ordered_items = OrderedItemGetDetailsSerializer(many=True, read_only=True)
#
#     # TODO: write a ordered item serializer where each foreign key details are also shown in response
#
#     class Meta:
#         model = FoodOrder
#         fields = ['id',
#                   "remarks",
#                   'status_detail',
#                   "table",
#                   "status",
#                   "price",
#                   'ordered_items',
#                   #   'grand_total_price',
#                   #   "total_price",
#                   #   "discount_amount",
#                   #   "tax_amount",
#                   #   "tax_percentage",
#                   #   "service_charge",
#                   #   "payable_amount",
#                   ]
#
#     def get_price(self, obj):
#         return calculate_price(food_order_obj=obj, include_initial_order=True)


class FreeTableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = ['id', 'table_no']


class FoodOrderByTableSerializer(serializers.ModelSerializer):
    status_details = serializers.CharField(source='get_status_display')
    # table_name = serializers.CharField(source="table.name")
    table_name = serializers.SerializerMethodField(read_only=True)
    table_no = serializers.SerializerMethodField(read_only=True)
    # table_no = serializers.CharField(source="table.table_no")
    waiter = serializers.SerializerMethodField(read_only=True)
    price = serializers.SerializerMethodField()
    ordered_items = serializers.SerializerMethodField(read_only=True)
    restaurant_info = serializers.SerializerMethodField(read_only=True)
    customer = serializers.SerializerMethodField(read_only=True)

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
                  'created_at',
                  'updated_at',
                  'customer',
                  #   'grand_total_price',
                  #   "total_price",
                  #   "discount_amount",
                  #   "tax_amount",
                  #   "tax_percentage",
                  #   "service_charge",
                  #   "payable_amount",
                  ]
        # ordering = ['table']

    def get_ordered_items(self, obj):
        is_apps = self.context.get('is_apps', False)
        request = self.context.get('request')
        if is_apps:
            if request:
                is_waiter_app = request.path.__contains__('/apps/waiter/')
                is_customer_app = request.path.__contains__('/apps/customer/')
                if is_customer_app:
                    qs = obj.ordered_items.exclude(
                        status__in=['4_CANCELLED'])
                elif is_waiter_app:
                    qs = obj.ordered_items.exclude(
                        status__in=['4_CANCELLED', '0_ORDER_INITIALIZED'])
                else:
                    qs = obj.ordered_items.exclude(
                        status__in=['4_CANCELLED'])
            else:
                qs = obj.ordered_items.exclude(
                    status__in=['4_CANCELLED'])
        else:
            qs = obj.ordered_items

        serializer = OrderedItemGetDetailsSerializer(
            instance=qs, many=True)

        return serializer.data

        # OrderedItemGetDetailsSerializer(many=True, read_only=True)

    def get_price(self, obj):
        calculate_price_with_initial_item = self.context.get(
            'calculate_price_with_initial_item', False)
        return calculate_price(food_order_obj=obj, include_initial_order=calculate_price_with_initial_item)

    def get_customer(self, obj):
        if obj.customer:
            return {'id': obj.customer.pk, 'name': obj.customer.name}
        else:
            return None

    def get_waiter(self, obj):
        food_order_log_qs = obj.food_order_logs.filter(
            order_status__in=["5_PAID", "4_CREATE_INVOICE"]).order_by('-created_at').first()
        # if obj.table:
        #     qs = obj.table.staff_assigned.filter(is_waiter=True).first()
        #     if qs:
        #         return {"name": qs.user.first_name, 'id': qs.pk}
        if food_order_log_qs:
            if food_order_log_qs.staff:
                return {'name': food_order_log_qs.staff.name, 'staff_id': food_order_log_qs.staff_id}
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


class FoodOrderSerializer(FoodOrderByTableSerializer):
    status_detail = serializers.CharField(source='get_status_display')

    # TODO: write a ordered item serializer where each foreign key details are also shown in response

    class Meta(FoodOrderByTableSerializer.Meta):
        fields = ['id',
                  "remarks",
                  'status_detail',
                  "table",
                  "status",
                  "price",
                  'ordered_items'
                  ]


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


class FoodSerializer(serializers.ModelSerializer):
    category = FoodCategorySerializer(read_only=True)

    class Meta:
        model = Food
        fields = '__all__'


class FoodPostSerializer(serializers.ModelSerializer):
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
            'ingredients',
            'category',
            'id',
            'discount',

        ]


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
            'rating',
            'order_counter',

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


class FoodGroupByCategoryListSerializer(serializers.ListSerializer):

    def to_representation(self, data):
        iterable = data.all() if isinstance(data, models.Manager) else data
        return [
            {
                'foods': super(FoodGroupByCategoryListSerializer, self).to_representation(
                    Food.objects.filter(
                        category=obj, pk__in=list(
                            data.values_list('id', flat=True)
                        )
                    )
                ),
                'name': obj.name,
                'id': obj.pk,
                'image': obj.image.url if obj.image else None


                # 'image': obj.image   .update(dict(FoodCategorySerializer(obj).data))

            }
            for obj in FoodCategory.objects.filter(pk__in=list(data.values_list('category_id', flat=True)))
        ]


# class FoodsByCategorySerializer(serializers.ModelSerializer):
#     foods = FoodWithPriceSerializer(many=True)

#     class Meta:
#         model = FoodCategory
#         fields = ['id', 'name', 'image', 'foods']


class FoodsByCategorySerializer(FoodWithPriceSerializer):
    class Meta(FoodWithPriceSerializer.Meta):
        list_serializer_class = FoodGroupByCategoryListSerializer


class FoodDetailSerializer(serializers.ModelSerializer):
    category = FoodCategorySerializer(read_only=True)
    food_extras = FoodExtraGroupByTypeSerializer(read_only=True, many=True)
    food_options = serializers.SerializerMethodField(read_only=True)
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
            'rating',
            'order_counter',

        ]

    def get_price(self, obj):
        option_qs = obj.food_options.order_by('price').first()
        if option_qs:
            return round(option_qs.price, 2)
        else:
            return None

    def get_food_options(self, obj):
        serializer = FoodOptionSerializer(
            obj.food_options.order_by('price'), many=True)
        return serializer.data


class RestaurantPostSerialier(serializers.ModelSerializer):
    logo = Base64ImageField()

    class Meta:
        model = Restaurant
        exclude = ['deleted_at']

    def create(self, validated_data):
        logo = validated_data.pop('logo', None)
        payment_type = validated_data.pop('payment_type', [])

        if logo:
            qs = Restaurant.objects.create(logo=logo, **validated_data)
        else:
            qs = Restaurant.objects.create(**validated_data)
        qs.payment_type.set(payment_type)
        qs.save()
        return qs

    def update(self, instance, validated_data):
        logo = validated_data.pop('logo', None)

        if logo:
            instance.logo = logo
            instance.save()
        return super(RestaurantPostSerialier, self).update(instance, validated_data)


class RestaurantUpdateSerialier(serializers.ModelSerializer):
    logo = Base64ImageField()

    class Meta:
        model = Restaurant
        exclude = ['status', 'subscription', 'subscription_ends', 'deleted_at']

        def update(self, instance, validated_data):
            logo = validated_data.pop('logo', None)

            if logo:
                instance.logo = logo
                instance.save()
            return super(RestaurantPostSerialier, self).update(instance, validated_data)


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

            total_items += order_qs.ordered_items.exclude(
                status='4_CANCELLED').count()

            if order_qs:
                total_served_items += order_qs.ordered_items.filter(
                    status='3_IN_TABLE').count()
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
        fields = ['order_info', 'id', 'order', 'grand_total',
                  'payable_amount', 'updated_at', 'created_at', 'payment_status']

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
    image = Base64ImageField()

    class Meta:
        model = Discount
        # fields ='__all__'
        exclude = ['deleted_at']

    def create(self, validated_data):
        image = validated_data.pop('image', None)
        if image:
            return Discount.objects.create(image=image, **validated_data)
        return Discount.objects.create(**validated_data)


class FoodDetailsByDiscountSerializer(serializers.ModelSerializer):
    discount = DiscountSerializer(read_only=True, many=True)

    class Meta:
        model = Food
        fields = ['id', 'image', 'discount']


class ReportDateRangeSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)


class ReportByDateRangeSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    category = serializers.ListSerializer(child=serializers.IntegerField())
    item = serializers.ListSerializer(child=serializers.IntegerField())
    waiter = serializers.ListSerializer(child=serializers.IntegerField())


class StaffFcmSerializer(serializers.Serializer):
    table_id = serializers.IntegerField()


class OnlyFoodOrderIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodOrder
        fields = ['id']


class CollectPaymentSerializer(serializers.Serializer):
    table_id = serializers.IntegerField()
    payment_method = serializers.CharField()


class PopUpSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    food = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PopUp
        fields = '__all__'

    def create(self, validated_data):
        image = validated_data.pop('image', None)
        if image:
            return PopUp.objects.create(image=image, **validated_data)
        return PopUp.objects.create(**validated_data)

    def get_food(self, obj):
        if obj.foods:
            return obj.foods[0]
        else:
            return None


class SliderSerializer(serializers.ModelSerializer):
    discoutn_percentage = serializers.SerializerMethodField(read_only=True)
    image = Base64ImageField()

    class Meta:
        model = Slider
        fields = '__all__'

    def get_discoutn_percentage(self, obj):
        discount_percentage = 0
        if obj.food:
            if obj.food.discount:
                discount_percentage = obj.food.discount.amount
        return discount_percentage

    def create(self, validated_data):
        image = validated_data.pop('image', None)
        if image:
            return Slider.objects.create(image=image, **validated_data)
        return Slider.objects.create(**validated_data)


class ReOrderedItemSerializer(serializers.Serializer):
    order_item_id = serializers.IntegerField()
    quantity = serializers.IntegerField(default=1)


class ReviewSerializer(serializers.ModelSerializer):
    customer_info = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Review
        fields = '__all__'

    def get_customer_info(self, obj):
        customer_qs = None
        if obj.order:
            customer_qs = obj.order.customer

        if customer_qs:
            return {
                'id': customer_qs.pk,
                'name': customer_qs.name,
            }
        else:
            return {}


class RestaurantMessagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestaurantMessages
        fields = '__all__'

class RestaurantMessagesListSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name')
    class Meta:
        model = RestaurantMessages
        fields = ['id','restaurant','restaurant_name','title','message','updated_at']


class FcmNotificationStaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = FcmNotificationStaff
        fields = '__all__'


class VersionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VersionUpdate
        exclude = ['created_at', 'updated_at']


class FoodOptionsTemplateSerializer(serializers.ModelSerializer):
    food_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = FoodOption
        fields = ['name', 'food_name']

    def get_food_name(self, obj):
        return obj.food.name


class OrderedItemTemplateSerializer(serializers.ModelSerializer):
    food_extra = serializers.SerializerMethodField(read_only=True)
    food_option = FoodOptionsTemplateSerializer(read_only=True)
    # table = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = OrderedItem
        fields = '__all__'

    def get_food_extra(self, obj):
        if obj.food_extra.count():
            return '('+' ,'.join(list(obj.food_extra.values_list('name', flat=True)))+')'
        else:
            return None

    def get_table(self, obj):
        if obj.food_order:
            return obj.food_order.table.table_no
        return None


class ServedOrderSerializer(serializers.ModelSerializer):
    order = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = FoodOrderLog
        fields = ['staff', 'order', 'created_at']

    def get_order(self, obj):
        if obj.order:
            table_no = obj.order.table.table_no
            order_id = obj.order.pk
            order_status = obj.order.status
            order_amaount = obj.order.payable_amount
            return {'table_id': table_no, 'order_id': order_id,
                    'order_status': order_status,
                    'order_amaount': order_amaount
                    }


class CustomerOrderDetailsSerializer(serializers.ModelSerializer):
   # table = serializers.SerializerMethodField(read_only=True)
    order_id = serializers.IntegerField(source='id')
    restaurant_name = serializers.CharField(source='restaurant.name')

    class Meta:
        model = FoodOrder
        fields = ['order_id', 'restaurant_name',
                  'payable_amount', 'created_at']

    # def get_table(self, obj):
    #     if obj.table:
    #         table_id = obj.table.id
    #         table_no = obj.table.table_no
    #         restaurant_name = obj.table.restaurant.name
    #         return {'table_id':table_id,
    #                 'table_no':table_no,
    #                 'restaurant_name':restaurant_name}
