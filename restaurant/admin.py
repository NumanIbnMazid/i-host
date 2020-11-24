from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Restaurant)
admin.site.register(Subscription)
admin.site.register(RestaurantContactPerson)
admin.site.register(RestaurantPromoCategory)

admin.site.register(FoodCategory)
admin.site.register(Food)
admin.site.register(FoodOptionType)
admin.site.register(FoodExtraType)

admin.site.register(FoodExtra)

admin.site.register(FoodOption)
admin.site.register(Table)
admin.site.register(FoodOrder)
admin.site.register(OrderedItem)
admin.site.register(Invoice)
