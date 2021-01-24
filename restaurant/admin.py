from django.contrib import admin
from .models import *

# Register your models here.
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['id','code', 'title']

class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['id', 'created_at', 'updated_at', 'restaurant']

class FoodOrderLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'staff', 'order_status']

class DiscountAdmin(admin.ModelAdmin):
    list_display = ['id', 'name','restaurant']

class TableAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'restaurant','is_occupied']


class FoodOrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'table', 'status','restaurant','created_at']

class OrderedItemAdmin(admin.ModelAdmin):
    list_display = ['id','food_order', 'food_option', 'status']

class FoodCategoryAdmin(admin.ModelAdmin):
    list_display = ['id','name']
class FoodExtraTypeAdmin(admin.ModelAdmin):
    list_display = ['id','name']

class FoodExtraAdmin(admin.ModelAdmin):
    list_display = ['id','name','food','price']

class FoodAdmin(admin.ModelAdmin):
    list_display = ['id','name','restaurant','category']

class FoodOptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'price', 'food']

class PopUpAdmin(admin.ModelAdmin):
    list_display = ['id','title','restaurant','serial_no']

class SliderAdmin(admin.ModelAdmin):
    list_display = ['id','title','restaurant','serial_no']

class ReviewAdmin(admin.ModelAdmin):
    list_display = ['id','order','rating','review_text']
class RestaurantMessagesAdmin(admin.ModelAdmin):
    list_display = ['id','title','message','restaurant']

class PrintNodeAdmin(admin.ModelAdmin):
    list_display = ['id','printer_id','restaurant']

class TakeAwayOrderAdmin(admin.ModelAdmin):
    list_display = ['id','restaurant']

admin.site.register(Restaurant)
admin.site.register(FoodOrderLog,FoodOrderLogAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(RestaurantContactPerson)
admin.site.register(RestaurantPromoCategory)

admin.site.register(FoodCategory, FoodCategoryAdmin)
admin.site.register(Food, FoodAdmin)
admin.site.register(FoodOptionType)
admin.site.register(FoodExtraType, FoodExtraTypeAdmin)

admin.site.register(FoodExtra, FoodExtraAdmin)

admin.site.register(FoodOption, FoodOptionAdmin)
admin.site.register(Table, TableAdmin)
admin.site.register(FoodOrder,FoodOrderAdmin)
admin.site.register(OrderedItem, OrderedItemAdmin)
admin.site.register(Invoice,InvoiceAdmin)
admin.site.register(Discount, DiscountAdmin)
admin.site.register(PopUp, PopUpAdmin)
admin.site.register(Slider, SliderAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(RestaurantMessages, RestaurantMessagesAdmin)
admin.site.register(PaymentType)
admin.site.register(VersionUpdate)
admin.site.register(PrintNode,PrintNodeAdmin)
admin.site.register(TakeAwayOrder,TakeAwayOrderAdmin)
