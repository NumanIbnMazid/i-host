from os import name, truncate
import restaurant
from django.db import models
from django.db.models import manager

# Create your models here.
"""
    TODO
    food - edit
    table delete - delete
    waiter - delete
    """


class Restaurant(models.Model):
    RESTAURANT_STATUS = [('ACTIVE', 'ACTIVE'), ('INACTIVE', 'INACTIVE')]

    name = models.CharField(max_length=250)
    logo = models.FileField(blank=True)
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


class RestaurantContactPerson(models.Model):
    name = models.CharField(max_length=150)
    designation = models.CharField(max_length=150, null=True, blank=True)
    phone = models.CharField(max_length=25, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.CASCADE, related_name='contact_person')
