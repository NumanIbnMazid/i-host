from django.contrib import admin
from .models import HotelStaffInformation, UserAccount
# Register your models here.
admin.site.register(UserAccount)
admin.site.register(HotelStaffInformation)
