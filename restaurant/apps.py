from django.apps import AppConfig


class RestaurantConfig(AppConfig):
    name = 'restaurant'

    def ready(self):
        from actstream import registry
        registry.register(self.get_model('FoodOrder'),
                          self.get_model('Table'),
                          self.get_model('Restaurant'))
        # registry.register(self.get_model(''))

# a = action.send(FoodOrder.objects.first(), verb='staff', action_object=order_qs.first(),request_body={'msg':'success'})