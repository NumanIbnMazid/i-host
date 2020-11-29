from django.contrib import admin
from .models import *
# Register your models here.

class HotelStaffInformationAdmin(admin.ModelAdmin):
    list_display = ['user', 'restaurant']

admin.site.register(UserAccount)
admin.site.register(HotelStaffInformation, HotelStaffInformationAdmin)
admin.site.register(PhoneVerification)
