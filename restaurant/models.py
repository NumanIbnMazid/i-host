from os import name, truncate

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import manager
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
    name = models.CharField(max_length=90)
    code = models.CharField(max_length=5, unique=True)
    details = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


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
    service_charge = models.DecimalField(
        max_digits=8, decimal_places=2, default=00.00)
    tax_percentage = models.DecimalField(
        max_digits=4, decimal_places=2, default=00.00)
    created_at = models.DateTimeField(auto_now_add=True)
    website = models.URLField(null=True, blank=True)
    status = models.CharField(
        choices=RESTAURANT_STATUS, max_length=25, default="ACTIVE")
    subscription = models.ForeignKey(
        Subscription, on_delete=models.SET_NULL, null=True, related_name='restaurants')
    subscription_ends = models.DateField()

    def __str__(self):
        return self.name


class RestaurantContactPerson(models.Model):
    name = models.CharField(max_length=150)
    designation = models.CharField(max_length=150, null=True, blank=True)
    phone = models.CharField(max_length=25, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.CASCADE, related_name='contact_persons')

    def __str__(self):
        return self.name


class RestaurantPromoCategory(models.Model):
    category_name = models.CharField(max_length=80)

    def __str__(self):
        return self.category_name


class FoodCategory(SoftDeleteModel):
    name = models.CharField(max_length=250)
    image = models.ImageField(null=True, blank=True)
    # restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE,related_name='food_category')

    def __str__(self):
        return self.name


class Food(SoftDeleteModel):
    name = models.CharField(max_length=200)
    image = models.ImageField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.CASCADE, related_name='food')
    category = models.ForeignKey(
        FoodCategory, null=True, blank=True, on_delete=models.PROTECT, related_name='foods')
    # promotion_category = models.ManyToManyField(
    #     RestaurantPromoCategory, blank=True)
    is_top = models.BooleanField(default=False)
    is_recommended = models.BooleanField(default=False)
    ingredients = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class FoodOptionType(SoftDeleteModel):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class FoodExtraType(SoftDeleteModel):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class FoodExtra(SoftDeleteModel):
    name = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    food = models.ForeignKey(Food, on_delete=models.CASCADE,
                             related_name='food_extras')
    extra_type = models.ForeignKey(
        FoodExtraType, on_delete=models.CASCADE, related_name='food_extras')

    def __str__(self):
        return self.name


class FoodOption(SoftDeleteModel):
    name = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    food = models.ForeignKey(
        Food, on_delete=models.CASCADE, related_name='food_options')
    option_type = models.ForeignKey(
        FoodOptionType, on_delete=models.CASCADE, related_name='food_options')

    def __str__(self):
        return self.name


class Table(models.Model):
    table_no = models.IntegerField(null=True, blank=True)
    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.CASCADE, related_name='tables')
    name = models.CharField(max_length=50, null=True, blank=True)
    staff_assigned = models.ManyToManyField(
        to='account_management.HotelStaffInformation', blank=True)
    is_occupied = models.BooleanField(default=False)

    def __str__(self):
        return self.name+'  ' + self.id.__str__()


class FoodOrder(models.Model):
    ORDER_STATUS = [
        ("0_ORDER_INITIALIZED", "Table Scanned"),
        ("1_ORDER_PLACED", "User Confirmed"),
        ("2_ORDER_CONFIRMED", "In Kitchen"),
        ("3_IN_TABLE", "Food Served"),
        ("4_PAID", "Payment Done"),
        ("5_CANCELLED", "Cancelled"),

    ]
    remarks = models.TextField(null=True, blank=True)
    table = models.ForeignKey(
        Table, on_delete=models.SET_NULL, null=True, related_name='food_orders')
    status = models.CharField(choices=ORDER_STATUS,
                              default="0_ORDER_INITIALIZED", max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.status


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
