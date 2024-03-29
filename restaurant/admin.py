from django.contrib import admin
from .models import *

# Register your models here.
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['id','code', 'title']

class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['id','order_id','order', 'restaurant','grand_total','tax_amount','discount_amount','payable_amount','created_at']
    list_filter = ('restaurant','payment_status')

    def order_id(self,obj):
        return obj.order.id

    def discount_amount(self, obj):
        return obj.order.discount_amount

    def tax_amount(self, obj):
        return obj.order.tax_amount

class FoodOrderLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'staff', 'order_status']

class DiscountAdmin(admin.ModelAdmin):
    list_display = ['id', 'name','restaurant','discount_schedule_type']

class TableAdmin(admin.ModelAdmin):
    list_display = ['id', 'name','table_no', 'restaurant','is_occupied']
    list_filter = ('restaurant','is_occupied')

class FoodOrderAdmin(admin.ModelAdmin):
    list_display = ['id','order_no', 'table', 'status','restaurant','cash_received','payable_amount','created_at']
    list_filter = ('restaurant','status')

class OrderedItemAdmin(admin.ModelAdmin):
    list_display = ['id','food_order', 'food_option', 'status']

class FoodCategoryAdmin(admin.ModelAdmin):
    list_display = ['id','name']


class FoodExtraTypeAdmin(admin.ModelAdmin):
    list_display = ['id','name']

class FoodExtraAdmin(admin.ModelAdmin):
    list_display = ['id','name','food','price']

class FoodAdmin(admin.ModelAdmin):
    list_display = ['id','name','code','restaurant','category', 'discount', 'is_available','is_vat_applicable']
    list_filter = ('restaurant', 'discount','is_available')

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

class CashLogAdmin(admin.ModelAdmin):
    list_display = ['id','restaurant','starting_time']

class WithdrawCashAdmin(admin.ModelAdmin):
    list_display = ['id','cash_log']

class PromoCodePromotionAdmin(admin.ModelAdmin):
    list_display = ['id','code','restaurant', 'created_at']

class PromoCodePromotionLogAdmin(admin.ModelAdmin):
    list_display = ['id','promo_code', 'customer']

class RestaurantAdmin(admin.ModelAdmin):
    list_display = ['id','name','is_service_charge_apply_in_original_food_price','is_vat_charge_apply_in_original_food_price']

class TakewayOrderTypeAdmin(admin.ModelAdmin):
    list_display = ['id','name']

admin.site.register(Restaurant,RestaurantAdmin)
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
admin.site.register(RestaurantMessages,RestaurantMessagesAdmin)
admin.site.register(PaymentType)
admin.site.register(VersionUpdate)
admin.site.register(PrintNode,PrintNodeAdmin)
admin.site.register(TakeAwayOrder,TakeAwayOrderAdmin)
admin.site.register(ParentCompanyPromotion)
admin.site.register(CashLog, CashLogAdmin)
admin.site.register(WithdrawCash, WithdrawCashAdmin)
admin.site.register(PromoCodePromotion, PromoCodePromotionAdmin)
admin.site.register(PromoCodePromotionLog, PromoCodePromotionLogAdmin)
admin.site.register(TakewayOrderType, TakewayOrderTypeAdmin)

