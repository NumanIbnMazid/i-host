from django.contrib import admin
from .models import Restaurant, Subscription,Food
# Register your models here.
admin.site.register(Restaurant)
admin.site.register(Subscription)
admin.site.register(Food)
