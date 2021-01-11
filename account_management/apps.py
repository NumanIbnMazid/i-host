from django.apps import AppConfig


class AccountManagementConfig(AppConfig):
    name = 'account_management'

    def ready(self):
        from actstream import registry
        registry.register(self.get_model('HotelStaffInformation'))

