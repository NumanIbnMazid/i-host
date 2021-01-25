import uuid
from os import name, truncate

from django.contrib.postgres.fields import ArrayField
from django.db.models import JSONField

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import manager
from django.db.models.fields import DecimalField
from django.db.models.fields.related import OneToOneField
from softdelete.models import SoftDeleteModel

import restaurant

# Create your models here.
"""
    TODO
    food - edit
    table delete - delete
    waiter - delete
    """


class Subscription(models.Model):
    code = models.CharField(max_length=5, unique=True)
    details = models.CharField(null=True, blank=True, max_length=1500)
    image = models.ImageField(null=True, blank=True)
    title = models.CharField(max_length=250, null=True, blank=True)
    table_limit = models.IntegerField()
    waiter_limit = models.IntegerField()
    manager_limit = models.IntegerField()
    restaurant_limit = models.IntegerField()
    allow_popup = models.BooleanField()
    bi_report = models.BooleanField()

    def __str__(self):
        if self.title:
            return str(self.title)
        else:
            return 'title null'


class Restaurant(SoftDeleteModel):
    RESTAURANT_STATUS = [('ACTIVE', 'ACTIVE'), ('INACTIVE', 'INACTIVE')]

    name = models.CharField(max_length=250)
    logo = models.ImageField(blank=True)
    address = models.CharField(max_length=500, null=True, blank=True)
    latitude = models.DecimalField(
        max_digits=50, decimal_places=45, null=True, blank=True)
    longitude = models.DecimalField(
        max_digits=50, decimal_places=45, null=True, blank=True)
    service_charge_is_percentage = models.BooleanField(default=False)
    service_charge = models.FloatField(
        default=00.00)
    tax_percentage = models.FloatField(
        default=00.00)
    created_at = models.DateTimeField(auto_now_add=True)
    website = models.URLField(null=True, blank=True)
    status = models.CharField(
        choices=RESTAURANT_STATUS, max_length=25, default="ACTIVE")
    subscription = models.ForeignKey(
        Subscription, on_delete=models.SET_NULL, null=True, related_name='restaurants')
    subscription_ends = models.DateField()
    phone = models.CharField(null=True, blank=True, max_length=50)
    vat_registration_no = models.CharField(
        max_length=250, null=True, blank=True)
    trade_licence_no = models.CharField(max_length=250, null=True, blank=True)
    payment_type = models.ManyToManyField(
        to='restaurant.PaymentType', blank=True)

    def __str__(self):
        if self.name:
            return str(self.name)
        else:
            return 'name null'


class RestaurantContactPerson(models.Model):
    name = models.CharField(max_length=150)
    designation = models.CharField(max_length=150, null=True, blank=True)
    phone = models.CharField(max_length=25, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.CASCADE, related_name='contact_persons')

    # def __str__(self):
    #     return self.name


class RestaurantPromoCategory(models.Model):
    category_name = models.CharField(max_length=80)

    # def __str__(self):
    #     return self.category_name


class FoodCategory(SoftDeleteModel):
    name = models.CharField(max_length=250)
    image = models.FileField(null=True, blank=True)
    # restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE,related_name='food_category')

    # def __str__(self):
    #     return self.name


class Food(SoftDeleteModel):
    name = models.CharField(max_length=200)
    image = models.ImageField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.CASCADE, related_name='foods')
    category = models.ForeignKey(
        FoodCategory, null=True, blank=True, on_delete=models.PROTECT, related_name='foods')
    # promotion_category = models.ManyToManyField(
    #     RestaurantPromoCategory, blank=True)
    is_top = models.BooleanField(default=False)
    is_recommended = models.BooleanField(default=False)
    ingredients = models.TextField(null=True, blank=True)
    rating = models.FloatField(null=True, blank=True)
    order_counter = models.IntegerField(default=0)
    discount = models.ForeignKey(
        to="restaurant.Discount", null=True, blank=True, on_delete=models.SET_NULL, related_name='foods')

    # def __str__(self):
    #     return self.name


class FoodOptionType(SoftDeleteModel):
    name = models.CharField(max_length=50)

    # def __str__(self):
    #     return self.name


class FoodExtraType(SoftDeleteModel):
    name = models.CharField(max_length=50)

    # def __str__(self):
    #     return self.name


class FoodExtra(SoftDeleteModel):
    name = models.CharField(max_length=50)
    price = models.FloatField(default=0)
    food = models.ForeignKey(Food, on_delete=models.CASCADE,
                             related_name='food_extras')
    extra_type = models.ForeignKey(
        FoodExtraType, on_delete=models.CASCADE, related_name='food_extras')

    # def __str__(self):
    #     return self.name


class FoodOption(SoftDeleteModel):
    name = models.CharField(max_length=50)
    price = models.FloatField(default=0)
    food = models.ForeignKey(
        Food, on_delete=models.CASCADE, related_name='food_options')
    option_type = models.ForeignKey(
        FoodOptionType, on_delete=models.CASCADE, related_name='food_options')

    def __str__(self):
        return self.option_type.name


class Table(SoftDeleteModel):
    table_no = models.IntegerField(null=True, blank=True)
    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.CASCADE, related_name='tables')
    name = models.CharField(max_length=50, null=True, blank=True)
    staff_assigned = models.ManyToManyField(
        to='account_management.HotelStaffInformation', blank=True, related_name='tables')
    is_occupied = models.BooleanField(default=False)

    # def __str__(self):
    #     return self.name
    #            #+'' + self.id.__str__()
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['restaurant', 'table_no'], name='restaurant and table no constrains'),
        ]


class FoodOrder(SoftDeleteModel):
    ORDER_STATUS = [
        ("0_ORDER_INITIALIZED", "Table Scanned"),
        ("1_ORDER_PLACED", "User Confirmed"),
        ("2_ORDER_CONFIRMED", "In Kitchen"),
        ("3_IN_TABLE", "Food Served"),
        ("4_CREATE_INVOICE", "Create Invoice"),

        ("5_PAID", "Payment Done"),
        ("6_CANCELLED", "Cancelled"),

    ]
    order_no = models.CharField(max_length=200, null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    table = models.ForeignKey(
        Table, on_delete=models.SET_NULL, null=True, related_name='food_orders')
    status = models.CharField(choices=ORDER_STATUS,
                              default="0_ORDER_INITIALIZED", max_length=120)

    grand_total_price = models.FloatField(null=True, blank=True, default=0)
    total_price = models.FloatField(null=True, blank=True, default=0)
    discount_amount = models.FloatField(null=True, blank=True, default=0)
    tax_amount = models.FloatField(null=True, blank=True, default=0)
    tax_percentage = models.FloatField(null=True, blank=True, default=0)
    service_charge = models.FloatField(null=True, blank=True, default=0)
    payable_amount = models.FloatField(null=True, blank=True, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    customer = models.ForeignKey(
        to='account_management.CustomerInfo', on_delete=models.SET_NULL, null=True, blank=True, related_name='food_orders')
    restaurant = models.ForeignKey(
        to=Restaurant, on_delete=models.SET_NULL, null=True, blank=True, related_name='food_orders')
    applied_promo_code = models.CharField(max_length=250,null=True,blank=True)

    def __str__(self):
        if self.order_no:
            return str(self.order_no)
        else:
            return 'order no null'

    # class Meta:
    #     constraints = [
    #         models.UniqueConstraint(
    #             fields=['restaurant', 'order_no'], name='restaurant and order_no constrains'),
    #     ]


class FoodOrderLog(SoftDeleteModel):
    order = models.ForeignKey(
        to=FoodOrder, on_delete=models.SET_NULL, null=True, related_name='food_order_logs')
    staff = models.ForeignKey(
        to="account_management.HotelStaffInformation", on_delete=models.SET_NULL, null=True, related_name='food_order_logs')
    order_status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)


class OrderedItem(models.Model):
    ITEM_STATUS = [
        ("0_ORDER_INITIALIZED", "Table Scanned"),
        ("1_ORDER_PLACED", "User Confirmed"),
        ("2_ORDER_CONFIRMED", "In Kitchen"),
        ("3_IN_TABLE", "Food Served"),
        ("4_CANCELLED", "Cancelled"),

    ]
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    food_option = models.ForeignKey(
        FoodOption, on_delete=models.PROTECT, related_name='ordered_items')
    food_extra = models.ManyToManyField(
        FoodExtra, blank=True, related_name='ordered_items')
    food_order = models.ForeignKey(
        FoodOrder, on_delete=models.CASCADE, related_name='ordered_items')

    status = models.CharField(
        choices=ITEM_STATUS, default="0_ORDER_INITIALIZED", max_length=120)

    """
    
    
    order - > extra sort type wise
    food extra option type separate
    customer table separate
    
    """


class Invoice(SoftDeleteModel):
    STATUS = [("1_PAID", "Paid"), ("0_UNPAID", "Unpaid")]
    id = models.UUIDField(
        primary_key=True, editable=False, default=uuid.uuid4)
    restaurant = models.ForeignKey(
        to=Restaurant, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.ForeignKey(FoodOrder, null=True,
                              blank=True, on_delete=models.SET_NULL, related_name='invoices')
    grand_total = models.FloatField(
        null=True, blank=True)
    payable_amount = models.FloatField(default=0.0)
    order_info = models.JSONField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(
        choices=STATUS, max_length=25, default="0_UNPAID")


class Discount(models.Model):
    DISCOUNT_TYPE = [
        ("PERCENTAGE", "percentage"), ("AMOUNT", "amount")]

    name = models.CharField(max_length=200)
    image = models.ImageField(blank=True)
    description = models.CharField(
        max_length=500, default=None, null=True)
    # discount_promo_code = models.CharField(max_length=100)
    url = models.CharField(
        max_length=250, default=None, null=True, blank=True)
    start_date = models.DateTimeField(
        null=False, blank=False)
    end_date = models.DateTimeField(null=True, blank=True)
    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.SET_NULL, related_name='discount', null=True)
    is_popup = models.BooleanField(default=False)
    is_slider = models.BooleanField(default=False)

    serial_no = models.IntegerField(default=0)
    clickable = models.BooleanField(default=False)
    food = models.ForeignKey(
        Food, on_delete=models.SET_NULL, related_name='discount_slider', null=True)

    # discount_slot_start_time = models.TimeField(null=True, blank=True)
    # discounut_slot_closing_time = models.TimeField(null=True, blank=True)

    # discount_type = models.CharField(choices=DISCOUNT_TYPE,
    #                                  max_length=50, default="PERCENTAGE")
    amount = models.FloatField()
    # max_discount_amount = models.FloatField(null=True, blank=True)
    # number_of_uses = models.PositiveIntegerField(default=0)
    # maximum_number_of_uses = models.PositiveIntegerField(null=True, blank=True)
    # user_unique = models.BooleanField(default=False)

    # number_of_times_allowed_by_each_user = models.PositiveIntegerField(
    #     null=True, blank=True)

    # def __str__(self):
    #     return self.name


class ParentCompanyPromotion(models.Model):
    PROMO_TYPE = [
        ("PERCENTAGE", "percentage"), ("AMOUNT", "amount")]
    code = models.CharField(max_length=200, unique=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    promo_type = models.CharField(choices=PROMO_TYPE, max_length=50)
    max_amount = models.FloatField(default=0)
    minimum_purchase_amount = models.FloatField(default=0)
    amount = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    restaurant = models.ManyToManyField(Restaurant)


class PopUp(models.Model):
    restaurant = models.ForeignKey(to=Restaurant, on_delete=models.CASCADE)
    image = models.ImageField()
    title = models.CharField(max_length=25)
    description = models.TextField(null=True, blank=True)
    serial_no = models.IntegerField(default=0)
    clickable = models.BooleanField(default=False)
    foods = ArrayField(models.IntegerField(
        null=True, blank=True), null=True, blank=True)


class Slider(models.Model):
    restaurant = models.ForeignKey(to=Restaurant, on_delete=models.CASCADE)
    image = models.ImageField()
    title = models.CharField(max_length=25)
    description = models.TextField(null=True, blank=True)
    serial_no = models.IntegerField(default=0)
    clickable = models.BooleanField(default=False)
    food = models.ForeignKey(
        Food, on_delete=models.SET_NULL, related_name='sliders', null=True)


class Review(models.Model):
    order = OneToOneField(to=FoodOrder, related_name='reviews',
                          on_delete=models.SET_NULL, null=True)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)])
    review_text = models.TextField(null=True, blank=True)


class RestaurantMessages(models.Model):
    restaurant = models.ForeignKey(to=Restaurant, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, null=True, blank=True)
    message = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)


class PaymentType(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    image = models.ImageField()

    def __str__(self):
        return self.name


class VersionUpdate(models.Model):
    version_no = models.CharField(max_length=500, null=True, blank=True)
    force_update = models.BooleanField(default=False)
    is_customer_app = models.BooleanField(default=False)
    is_waiter_app = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # def __str__(self):
    #     return self.version_id


class PrintNode(models.Model):
    restaurant = models.ForeignKey(
        to=Restaurant, on_delete=models.SET_NULL, null=True, related_name='print_nodes')
    printer_id = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.restaurant.name


class TakeAwayOrder(models.Model):
    restaurant = models.ForeignKey(
        to=Restaurant, on_delete=models.SET_NULL, null=True, related_name='take_away_orders')
    running_order = models.ManyToManyField(
        to='FoodOrder', blank=True, related_name='take_away_orders')
    assigned_staff = models.ManyToManyField(
        to='account_management.HotelStaffInformation', blank=True, related_name='take_away_orders')
    # def __str__(self):
    #     return self.restaurant
