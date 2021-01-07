from django.contrib import admin
from .models import *
# Register your models here.


class HotelStaffInformationAdmin(admin.ModelAdmin):
    list_display = ['user', 'restaurant']


class CustomerFcmDeviceAdmin(admin.ModelAdmin):
    list_display = ['customer', 'device_type']

class CustomerInfoAdmin(admin.ModelAdmin):
    list_display = ['name','user']


admin.site.register(UserAccount)
admin.site.register(HotelStaffInformation, HotelStaffInformationAdmin)
admin.site.register(PhoneVerification)
admin.site.register(CustomerInfo, CustomerInfoAdmin)
admin.site.register(StaffFcmDevice)
admin.site.register(CustomerFcmDevice, CustomerFcmDeviceAdmin)
admin.site.register(FcmNotificationCustomer)
admin.site.register(FcmNotificationStaff)
