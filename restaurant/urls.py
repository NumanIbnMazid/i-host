# from rest_framework.routers import DefaultRouter
from .views import *
from django.urls import include, path
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register('food_option_type', FoodOptionTypeViewSet,
                basename="food_option_extra_type")


router.register('food_extra_type', FoodExtraTypeViewSet,
                basename="food_option_extra_type")

router.register('food_category', FoodCategoryViewSet,
                basename="food_category")

router.register('food_extra', FoodExtraViewSet,
                basename="food_extra")

router.register('food_option', FoodOptionViewSet,
                basename='food_option')


# router.register('table', TableViewSet,
#                basename="table")

router.register('food', FoodViewSet,
                basename="food")

# router.register('discount', DiscountViewSet,
#               basename="discount")

fake_dashboard_urls = []

dashboard_urls = [
    path('order/cart/items/',
         OrderedItemViewSet.as_view({'post': 'cart_create_from_dashboard'}, name='cart_create_from_dashboard')),
    path('category_list/<int:restaurant>',
         FoodViewSet.as_view({'get': 'category_list'}, name='category_list')),

    path('restaurant/create_discount/',
         DiscountViewSet.as_view({'post': 'create_discount'}), name='create_discount'),
    path('delete_discount/<int:discount_id>',
         DiscountViewSet.as_view({'delete': 'discount_delete'}), name='discount_delete'),

] + fake_dashboard_urls


urlpatterns = [
    path('', include(router.urls)),
    #     path('foods/<int:restaurant>/',
    #          FoodByRestaurantViewSet.as_view({'get': 'list'}), name='foods'),
    path('table/<int:table_id>/add_staff/',
         TableViewSet.as_view({'post': 'add_staff'}), name='add_staff'),
    path('table/',
         TableViewSet.as_view({'post': 'create', }), name='table'),
    path('table/<int:pk>/',
         TableViewSet.as_view({'patch': 'update', 'delete': 'destroy'}), name='table'),
    path('table/<int:table_id>/staff_remove/',
         TableViewSet.as_view({'post': 'remove_staff', }), name='remove_staff'),
    # New Add
    path('table/<int:table_id>/quantity_list/',
         TableViewSet.as_view({'get': 'quantity_list', }), name='quantity_list'),


    path('restaurant/',
         RestaurantViewSet.as_view({'post': 'create', 'get': 'list'}), name='restaurant_create_and_list'),

    path('restaurant/<int:pk>/',
         RestaurantViewSet.as_view({'patch': 'update', 'get': 'retrieve'}), name='restaurant_update'),

    path('restaurant/<int:pk>/delete_restaurant/',
         RestaurantViewSet.as_view({'delete': 'delete_restaurant'}), name='delete_restaurant'),

    path('restaurant/<int:pk>/today_sell/',
         RestaurantViewSet.as_view({'get': 'today_sell'}), name='today_sell'),



    path("food_category/",
         FoodCategoryViewSet.as_view({"post": "create", "get": "list"})),
    path("food_category/<int:pk>/",
         FoodCategoryViewSet.as_view({"patch": "update", "delete": "destroy"})),

    path('restaurant/<int:restaurant>/tables/',
         TableViewSet.as_view({'get': 'table_list'}), name='tables'),

    path('restaurant_staff/<int:staff_id>/tables/',
         TableViewSet.as_view({'get': 'staff_table_list'}), name='staff_table_list'),

    path('table/<int:table_id>/order_item_list/',
         TableViewSet.as_view({'get': 'order_item_list'}), name='order_item_list'),
    #     path('table/<int:table_id>/',
    #          TableViewSet.as_view({'delete': 'destroy'}), name='destroy_tables'),

    path('restaurant/<int:restaurant_id>/order_item_list/',
         RestaurantViewSet.as_view({'get': 'order_item_list'}), name='order_item_list'),


    path('restaurant_under_owner/',
         RestaurantViewSet.as_view({'get': 'restaurant_under_owner'}), name='restaurant_under_owner'),

    path('restaurant/<int:restaurant>/foods/',
         FoodByRestaurantViewSet.as_view({'get': 'list'}), name='foods'),

    path('restaurant/<int:restaurant>/top_foods/',
         FoodByRestaurantViewSet.as_view({'get': 'top_foods'}), name='top_foods'),

    path('restaurant/<int:restaurant>/recommended_foods/',
         FoodByRestaurantViewSet.as_view({'get': 'recommended_foods'}), name='recommended_foods'),

    path('restaurant/<int:restaurant>/foods_by_category/',
         FoodByRestaurantViewSet.as_view({'get': 'list_by_category'}), name='foods_by_category'),

    path('restaurant/quantity/',
         FoodByRestaurantViewSet.as_view({'get': 'quantity'}), name='quantity'),

    path('restaurant/<int:restaurant>/top_foods_by_category/',
         FoodByRestaurantViewSet.as_view({'get': 'top_foods_by_category'}), name='top_foods_by_category'),

    path('restaurant/<int:restaurant>/recommended_foods_by_category/',
         FoodByRestaurantViewSet.as_view({'get': 'recommended_foods_by_category'}), name='recommended_foods_by_category'),

    path('restaurant/food/mark_as_top_or_recommended/',
         FoodByRestaurantViewSet.as_view({'post': 'mark_as_top_or_recommended'}, name='mark_as_top_or_recommended')),


    path('order/create_order/',
         FoodOrderViewSet.as_view({'post': 'create_order'}, name='create_order')),

    path('order/create_take_away_order/',
         FoodOrderViewSet.as_view({'post': 'create_take_away_order'}, name='create_take_away_order')),


    # path('re_order',
    # OrderedItemViewSet.as_view({'post': 're_order'}, name='re_order')),

    path('order/cart/items/',
         OrderedItemViewSet.as_view({'post': 'create'}, name='items')),


    path('order/cart/items/<int:pk>/',
         OrderedItemViewSet.as_view({'patch': 'update', 'delete': 'destroy'}, name='items')),

    path('order/create_order/<int:pk>/',
         FoodOrderViewSet.as_view({'patch': 'update', 'get': 'retrieve'}, name='create_order')),

    path('order/cancel_order/',
         FoodOrderViewSet.as_view({'post': 'cancel_order'}, name='cancel_order')),

    path('order/cart/cancel_items/',
         FoodOrderViewSet.as_view({'post': 'cancel_items'}, name='cancel_items')),

    path('order/status/confirm/',
         FoodOrderViewSet.as_view({'post': 'confirm_status'}, name='confirm_status')),

    path('order/status/confirm_status_without_cancel/',
         FoodOrderViewSet.as_view({'post': 'confirm_status_without_cancel'}, name='confirm_status_without_cancel')),


    path('order/status/in_table/',
         FoodOrderViewSet.as_view({'post': 'in_table_status'}, name='in_table_status')),
    # path('order/create_invoice/',
    #     FoodOrderViewSet.as_view({'post': 'create_invoice'}, name='create_invoice')),
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


    path('restaurant/<int:restaurant>/invoice_history/',
         InvoiceViewSet.as_view({'get': 'invoice_history'}), name='invoice_history'),
    path('restaurant/<int:restaurant>/paid_cancel_invoice_history/',
         InvoiceViewSet.as_view({'get': 'paid_cancel_invoice_history'}), name='paid_cancel_invoice_history'),

    path('restaurant/<int:restaurant>/discount_list/',
         DiscountViewSet.as_view({'get': 'discount_list'}), name='discount_list'),

    # path('update_discount/<int:pk>',
    #    DiscountViewSet.as_view({'patch': 'update_discount'}), name='update_discount'),

    path('dashboard/', include(dashboard_urls)),


]
