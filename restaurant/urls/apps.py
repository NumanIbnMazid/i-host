# from rest_framework.routers import DefaultRouter
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from ..views import *


router = DefaultRouter()


# router.register('food_option_type', FoodOptionTypeViewSet,
#                 basename="food_option_extra_type")


# router.register('food_extra_type', FoodExtraTypeViewSet,
#                 basename="food_option_extra_type")

# router.register('food_category', FoodCategoryViewSet,
#                 basename="food_category")

# router.register('food_extra', FoodExtraViewSet,
#                 basename="food_extra")

# router.register('food_option', FoodOptionViewSet,
#                 basename='food_option')


# router.register('table', TableViewSet,
#                basename="table")

# router.register('food', FoodViewSet,
#                 basename="food")

# router.register('version_update', VersionUpdateViewSet,
#  basename="version_update")
apps_fake = [
    path('', include(router.urls)),
    #     path('foods/<int:restaurant>/',
    #          FoodByRestaurantViewSet.as_view({'get': 'list'}), name='foods'),
    # path('food/',
    #      FoodViewSet.as_view({'post': 'create'}, name='create')),

    path('food/<int:pk>/',
         FoodViewSet.as_view({'get': 'food_details'}, name='food')),
    # path('food_extra/',
    #      FoodExtraViewSet.as_view({'post': 'create'}, name='create')),
    path('food_extra/<int:pk>/',
         FoodExtraViewSet.as_view({'get': 'food_extra_details'}, name='food_extra')),

    path('table/<int:table_id>/add_staff/',
         TableViewSet.as_view({'post': 'add_staff'}), name='add_staff'),
    # path('table/',
    #      TableViewSet.as_view({'post': 'create', }), name='table'),
    # path('table/<int:pk>/',
    #      TableViewSet.as_view({'patch': 'update', 'delete': 'destroy'}), name='table'),
    path('table/<int:table_id>/staff_remove/',
         TableViewSet.as_view({'post': 'remove_staff', }), name='remove_staff'),
    # New Add
    #     path('table/<int:table_id>/quantity_list/',
    #          TableViewSet.as_view({'get': 'quantity_list', }), name='quantity_list'),

    # path('restaurant/',
    #      RestaurantViewSet.as_view({'post': 'create', 'get': 'list'}), name='restaurant_create_and_list'),

    path('restaurant/<int:pk>/',
         RestaurantViewSet.as_view({'get': 'retrieve'}), name='restaurant_update'),

    # path('restaurant/<int:pk>/delete_restaurant/',
    #      RestaurantViewSet.as_view({'delete': 'delete_restaurant'}), name='delete_restaurant'),

    # path('restaurant/<int:pk>/today_sell/',
    #      RestaurantViewSet.as_view({'get': 'today_sell'}), name='today_sell'),



    # path("food_category/",
    #      FoodCategoryViewSet.as_view({"post": "create"})),
    path("food_category/<int:pk>/",
         FoodCategoryViewSet.as_view({"get": "category_details"})),

    path('restaurant/<int:restaurant>/tables/',
         TableViewSet.as_view({'get': 'table_list'}), name='tables'),

    path('restaurant_staff/<int:staff_id>/tables/',
         TableViewSet.as_view({'get': 'staff_table_list'}), name='staff_table_list'),

    path('free_table_list/<int:restaurant>/',
         TableViewSet.as_view({'get': 'free_table_list'}), name='free_table_list'),

    path('restaurant/<int:restaurant_id>/order_item_list/',
         RestaurantViewSet.as_view({'get': 'order_item_list'}), name='order_item_list'),


    #     path('restaurant_under_owner/',
    #          RestaurantViewSet.as_view({'get': 'restaurant_under_owner'}), name='restaurant_under_owner'),

    path('restaurant/<int:restaurant>/foods/',
         FoodByRestaurantViewSet.as_view({'get': 'list'}), name='foods'),

    path('restaurant/<int:restaurant>/top_foods/',
         FoodByRestaurantViewSet.as_view({'get': 'top_foods'}), name='top_foods'),

    path('restaurant/<int:restaurant>/recommended_foods/',
         FoodByRestaurantViewSet.as_view({'get': 'recommended_foods'}), name='recommended_foods'),

    path('restaurant/<int:restaurant>/foods_by_category/',
         FoodByRestaurantViewSet.as_view({'get': 'list_by_category'}), name='foods_by_category'),

    #     path('restaurant/quantity/',
    #          FoodByRestaurantViewSet.as_view({'get': 'quantity'}), name='quantity'),

    path('restaurant/<int:restaurant>/top_foods_by_category/',
         FoodByRestaurantViewSet.as_view({'get': 'top_foods_by_category'}), name='top_foods_by_category'),

    path('restaurant/<int:restaurant>/recommended_foods_by_category/',
         FoodByRestaurantViewSet.as_view({'get': 'recommended_foods_by_category'}), name='recommended_foods_by_category'),

    #     path('restaurant/food/mark_as_top_or_recommended/',
    #          FoodByRestaurantViewSet.as_view({'post': 'mark_as_top_or_recommended'}, name='mark_as_top_or_recommended')),


    path('order/create_order/',
         FoodOrderViewSet.as_view({'post': 'create_order_apps'}, name='create_order_apps')),

    path('order/<int:order_id>/promo_code/',
         FoodOrderViewSet.as_view({'post': 'promo_code'}, name='promo_code')),

    path('order/table_transfer/',
         FoodOrderViewSet.as_view({'post': 'table_transfer'}, name='table_transfer')),

    path('order/status/<int:order_id>/',
         FoodOrderViewSet.as_view({'get': 'order_status'}, name='order_status')),

    path('reorder/', FoodOrderViewSet.as_view(
        {'post': 'food_reorder_by_order_id'}, name='food_reorder_by_order_id')),
    path('customer_order_history/', FoodOrderViewSet.as_view(
        {'get': 'customer_order_history'}, name='customer_order_history')),


    path('order/cart/items/',
         OrderedItemViewSet.as_view({'post': 'create'}, name='items')),
    path('re_order_items',
         OrderedItemViewSet.as_view({'post': 're_order_items'}, name='re_order_items')),


    path('waiter_order/cart/items/',
         OrderedItemViewSet.as_view({'post': 'create'}, name='items')),



    path('order/cart/items/<int:pk>/',
         OrderedItemViewSet.as_view({'patch': 'update', 'delete': 'destroy'}, name='items')),

    path('order/create_order/<int:pk>/',
         FoodOrderViewSet.as_view({'patch': 'update', 'get': 'retrieve'}, name='create_order')),

    path('order/cancel_order/',
         FoodOrderViewSet.as_view({'post': 'apps_cancel_order'}, name='apps_cancel_order')),

    path('order/cart/cancel_items/',
         FoodOrderViewSet.as_view({'post': 'cancel_items'}, name='cancel_items')),

    path('order/status/confirm/',
         FoodOrderViewSet.as_view({'post': 'confirm_status'}, name='confirm_status')),

    #     path('order/status/confirm_status_without_cancel/',
    #          FoodOrderViewSet.as_view({'post': 'confirm_status_without_cancel'}, name='confirm_status_without_cancel')),


    path('order/status/in_table/',
         FoodOrderViewSet.as_view({'post': 'in_table_status'}, name='in_table_status')),
    path('order/create_invoice/',
         FoodOrderViewSet.as_view({'post': 'create_invoice'}, name='create_invoice')),
    path('order/confirm_payment/',
         FoodOrderViewSet.as_view({'post': 'payment'}, name='confirm_payment')),

    path('order/placed_status/',
         FoodOrderViewSet.as_view({'post': 'placed_status'}, name='placed_status')),


    path('ordered_item/<int:pk>/',
         FoodOrderedViewSet.as_view({'get': 'retrieve'}, name='ordered_item')),

    path('food_extra_by_food/<int:pk>/',
         FoodViewSet.as_view({'get': 'food_extra_by_food'}, name='food_extra_by_food')),

    path('food_option_by_food/<int:pk>',
         FoodViewSet.as_view({'get': 'food_option_by_food'}, name='food_option_by_food')),

    path('restaurant/order_invoice/<int:order_id>',
         InvoiceViewSet.as_view({'get': 'order_invoice'}), name='order_invoice'),

    path('restaurant/invoice/<str:invoice_id>',
         InvoiceViewSet.as_view({'get': 'invoice'}), name='invoice'),


    #     path('restaurant/<int:restaurant>/invoice_history/',
    #          InvoiceViewSet.as_view({'get': 'invoice_history'}), name='invoice_history'),
    #     path('restaurant/<int:restaurant>/paid_cancel_invoice_history/',
    #          InvoiceViewSet.as_view({'get': 'paid_cancel_invoice_history'}), name='paid_cancel_invoice_history'),


    path('restaurant/<int:restaurant>/discount_list/',
         DiscountViewSet.as_view({'get': 'discount_list'}), name='discount_list'),

    path('all_restaurant_messages_list',
         RestaurantMessagesViewset.as_view({'get': 'all_restaurant_messages_list'}), name='all_restaurant_messages_list'),

    path('restaurant/discount/<int:pk>/',
         DiscountViewSet.as_view({'get': 'discount'}), name='discount'),

    path('restaurant/<int:restaurant_id>/pop_up/',
         DiscountViewSet.as_view({'get': 'pop_up_list_by_restaurant'}), name='pop_up_list_by_restaurant'),

    # path('discount_pop_up/<int:restaurant>/',
    #      DiscountViewSet.as_view({'get': 'discount_pop_up'}), name='discount_pop_up'),

    path('restaurant/<int:restaurant_id>/slider/',
         SliderViewset.as_view({'get': 'slider_list_by_restaurant'}), name='slider_list_by_restaurant'),

    path('food_search/<str:food_name>',
         FoodViewSet.as_view({'get': 'food_search'}, name='food_search')),

    # path('food_option/',
    #      FoodOptionViewSet.as_view({'post': 'create'}, name='create')),
    path('food_option/<int:pk>/',
         FoodOptionViewSet.as_view({'get': 'food_option_detail'}, name='food_option')),

    # path('food_option_type/',
    #      FoodOptionTypeViewSet.as_view({'post': 'create'}, name='create')),
    path('food_option_type/<int:pk>/',
         FoodOptionTypeViewSet.as_view({'get': 'food_option_type_detail'},
                                       name='food_option')),
    # path('food_extra_type/',
    #      FoodExtraTypeViewSet.as_view({'post': 'create'}, name='create')),
    path('food_extra_type/<int:pk>/',
         FoodExtraTypeViewSet.as_view({'get': 'food_extra_type_detail'}, name='food_extra_type')),

    path('review/',
         ReviewViewset.as_view({'post': 'create'}, name='create')),
    path('restaurant_messages_list/<int:restaurant>/',
         RestaurantMessagesViewset.as_view({'get': 'restaurant_messages_list'}, name='restaurant_messages_list')),

    path('payment_type/<int:restaurant>/',
         PaymentTypeViewSet.as_view({'get': 'restaurant_payment_type'}, name='restaurant_payment_type')),

    path('order_id_by/<int:table_id>/',
         TableViewSet.as_view({'get': 'order_id_by_table', }), name='order_id_by_table'),
    path('version_create',
         VersionUpdateViewSet.as_view({'post': 'create', }), name='create'),


]

apps_url = [
    path('table/<int:table_id>/order_item_list/',
         TableViewSet.as_view({'get': 'apps_running_order_item_list'}), name='apps_running_order_item_list'),
    path('call_waiter/', FcmCommunication.as_view({"post": "call_waiter"})),
    path('collect_payment/',
         FcmCommunication.as_view({"post": "collect_payment"})),
    #     fcm_notification_history_for_staff
    path('fcm_notification_history/<int:staff_id>/',
         FcmCommunication.as_view({"get": "fcm_notification_history_for_staff"})),
    path('order/order_info_price_details/<int:pk>/',
         FoodOrderViewSet.as_view({'get': 'apps_order_info_price_details'}, name='apps_order_info_price_details')),
    path('user_version_requirement',
         VersionUpdateViewSet.as_view({'get': 'user_version_requirement', }), name='user_version_requirement'),
    path('waiter_version_requirement',
         VersionUpdateViewSet.as_view({'get': 'waiter_version_requirement', }), name='waiter_version_requirement'),
    path('served_order_report/<int:waiter_id>/',
        ReportingViewset.as_view({'get': 'waiter_served_report'}), name='waiter_served_report'),
    path('cancel_order_report/<int:waiter_id>/',
        ReportingViewset.as_view({'get': 'waiter_cancel_report'}), name='waiter_cancel_report'),

    ]+apps_fake
