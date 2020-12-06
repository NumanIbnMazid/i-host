from django.contrib import admin
from .models import *

# Register your models here.
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['id', 'created_at', 'updated_at']

class TableAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'restaurant']
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
admin.site.register(Table, TableAdmin)
admin.site.register(FoodOrder)
admin.site.register(OrderedItem)
admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(Discount)
