# from rest_framework.routers import DefaultRouter
from ..views import *
from django.urls import include, path
from rest_framework.routers import DefaultRouter
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
router.register('test_print', PrintOrder)
router.register('restaurant_messages', RestaurantMessagesViewset,
                basename="restaurant_messages")
router.register('payment_type', PaymentTypeViewSet, basename='payment_type')
router.register('pop_up', PopUpViewset, basename='pop_up')
router.register('slider', SliderViewset, basename='slider')
# router.register('discount', DiscountViewSet,
#               basename="discount")

fake_dashboard_urls = [
    path('', include(router.urls)),
    #     path('foods/<int:restaurant>/',
    #          FoodByRestaurantViewSet.as_view({'get': 'list'}), name='foods'),

    path('food_extra/',
         FoodExtraViewSet.as_view({'post': 'create'}, name='create')),
    path('food_extra/<int:pk>/',
         FoodExtraViewSet.as_view({'patch': 'update', 'delete': 'destroy', 'get': 'food_extra_details'}, name='food_extra')),

    path('table/<int:table_id>/add_staff/',
         TableViewSet.as_view({'post': 'add_staff'}), name='add_staff'),
    path('table/',
         TableViewSet.as_view({'post': 'create', }), name='table'),
    path('table/<int:pk>/',
         TableViewSet.as_view({'patch': 'update', 'delete': 'destroy'}), name='table'),
    path('table/<int:table_id>/staff_remove/',
         TableViewSet.as_view({'post': 'remove_staff', }), name='remove_staff'),

    # New Add
    #     path('table/<int:table_id>/quantity_list/',
    #          TableViewSet.as_view({'get': 'quantity_list', }), name='quantity_list'),

    path('restaurant/',
         RestaurantViewSet.as_view({'post': 'create', 'get': 'list'}), name='restaurant_create_and_list'),

    path('restaurant/<int:pk>/',
         RestaurantViewSet.as_view({'patch': 'update', 'get': 'retrieve'}), name='restaurant_update'),

    path('restaurant/<int:pk>/delete_restaurant/',
         RestaurantViewSet.as_view({'delete': 'delete_restaurant'}), name='delete_restaurant'),

    path('restaurant/<int:pk>/today_sell/',
         RestaurantViewSet.as_view({'get': 'today_sell'}), name='today_sell'),

    path('food_option_type/',
         FoodOptionTypeViewSet.as_view({'get': 'list', 'post': 'create'}, name='create')),
    path('food_option_type/<int:pk>/',
         FoodOptionTypeViewSet.as_view({'patch': 'update', 'delete': 'destroy', 'get': 'food_option_type_detail'}, name='food_option')),

    path('food_option/',
         FoodOptionViewSet.as_view({'post': 'create'}, name='create')),
    path('food_option/<int:pk>/',
         FoodOptionViewSet.as_view({'patch': 'update', 'delete': 'destroy', 'get': 'food_option_detail'}, name='food_option')),

    path('food_extra_type/',
         FoodExtraTypeViewSet.as_view({'get': 'list', 'post': 'create'}, name='create')),
    path('food_extra_type/<int:pk>/',
         FoodExtraTypeViewSet.as_view({'patch': 'update', 'delete': 'destroy', 'get': 'food_extra_type_detail'}, name='food_extra_type')),



    path("food_category/",
         FoodCategoryViewSet.as_view({'get': 'list', "post": "create"})),
    path("food_category/<int:pk>/",
         FoodCategoryViewSet.as_view({"patch": "update", "delete": "destroy", "get": "category_details"})),

    path('restaurant/<int:restaurant>/tables/',
         TableViewSet.as_view({'get': 'table_list'}), name='tables'),

    path('restaurant_staff/<int:staff_id>/tables/',
         TableViewSet.as_view({'get': 'staff_table_list'}), name='staff_table_list'),

    #     path('table/<int:table_id>/',
    #          TableViewSet.as_view({'delete': 'destroy'}), name='destroy_tables'),

    path('restaurant/<int:restaurant_id>/order_item_list/',
         RestaurantViewSet.as_view({'get': 'order_item_list'}), name='order_item_list'),

    path('remaining_subscription_feathers/<int:restaurant_id>/',
         RestaurantViewSet.as_view({'get': 'remaining_subscription_feathers'}), name='remaining_subscription_feathers'),

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

    #     path('restaurant/quantity/',
    #          FoodByRestaurantViewSet.as_view({'get': 'quantity'}), name='quantity'),

    path('restaurant/<int:restaurant>/top_foods_by_category/',
         FoodByRestaurantViewSet.as_view({'get': 'top_foods_by_category'}), name='top_foods_by_category'),

    path('restaurant/<int:restaurant>/recommended_foods_by_category/',
         FoodByRestaurantViewSet.as_view({'get': 'recommended_foods_by_category'}), name='recommended_foods_by_category'),

    # path('restaurant/food/mark_as_top_or_recommended/',
    #      FoodByRestaurantViewSet.as_view({'post': 'mark_as_top_or_recommended'}, name='mark_as_top_or_recommended')),


    path('order/create_order/',
         FoodOrderViewSet.as_view({'post': 'create_order'}, name='create_order')),



    # path('re_order',
    # OrderedItemViewSet.as_view({'post': 're_order'}, name='re_order')),

    path('order/cart/items/',
         OrderedItemViewSet.as_view({'post': 'create'}, name='items')),

    path('take_away_order/cart/items/',
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
    path('order/create_invoice/',
         FoodOrderViewSet.as_view({'post': 'create_invoice_for_dashboard'}, name='create_invoice')),
    path('order/confirm_payment/',
         FoodOrderViewSet.as_view({'post': 'payment'}, name='confirm_payment')),

    path('order/placed_status/',
         FoodOrderViewSet.as_view({'post': 'placed_status'}, name='placed_status')),
    path('order/revert_back_to_in_table/',
         FoodOrderViewSet.as_view({'post': 'revert_back_to_in_table'}, name='revert_back_to_in_table')),

    path('ordered_item/<int:pk>/',
         FoodOrderedViewSet.as_view({'get': 'retrieve'}, name='ordered_item')),

    path('food/',
         FoodViewSet.as_view({'post': 'create'}, name='create')),

    path('food/<int:pk>/',
         FoodViewSet.as_view({'get': 'food_details', 'patch': 'update', 'delete': 'destroy'}, name='food')),

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

    path('restaurant/all_discount_list/',
         DiscountViewSet.as_view({'get': 'all_discount_list'}), name='all_discount_list'),

    path('restaurant/<int:restaurant>/discount_list/',
         DiscountViewSet.as_view({'get': 'discount_list'}), name='discount_list'),
    path('restaurant/discount/<int:pk>/',
         DiscountViewSet.as_view({'get': 'discount'}), name='discount'),
    path('restaurant/<int:restaurant_id>/pop_up/',
         PopUpViewset.as_view({'get': 'pop_up_list_by_restaurant'}), name='pop_up_list_by_restaurant'),
    path('restaurant/<int:restaurant_id>/slider/',
         SliderViewset.as_view({'get': 'slider_list_by_restaurant'}), name='slider_list_by_restaurant'),
    path('restaurant_messages_list/<int:restaurant>/',
         RestaurantMessagesViewset.as_view({'get': 'restaurant_messages_list'}, name='restaurant_messages_list')),
    path('force_discount/<int:order_id>',
         DiscountViewSet.as_view({'post':'force_discount'},name='force_discount')),


]

dashboard_urls = [
    path('order/cart/items/',
         OrderedItemViewSet.as_view({'post': 'cart_create_from_dashboard'}, name='cart_create_from_dashboard')),

    path('order/create_take_away_order/',
         FoodOrderViewSet.as_view({'post': 'create_take_away_order'}, name='create_take_away_order')),

    path('category_list/<int:restaurant>',
         FoodViewSet.as_view({'get': 'category_list'}, name='category_list')),
    path('food_list/<int:category_id>',
         FoodViewSet.as_view({'get': 'food_list'}, name='food_list')),

    path('dashboard_food_search/<str:food_name>',
         FoodViewSet.as_view({'get': 'food_search'}, name='food_search')),

    path('restaurant/create_discount/',
         DiscountViewSet.as_view({'post': 'create_discount'}), name='create_discount'),
    path('delete_discount/<int:discount_id>',
         DiscountViewSet.as_view({'delete': 'delete_discount'}), name='delete_discount'),
    path('discount/<int:pk>',
         DiscountViewSet.as_view({'patch': 'update_discount'}), name='update_discount'),
    path('food_discount/',
         DiscountViewSet.as_view({'post': 'food_discount'}), name='food_discount'),


    path('table/<int:table_id>/order_item_list/',
         TableViewSet.as_view({'get': 'order_item_list'}), name='order_item_list'),

    # path('report_by_date_range/',
    #      ReportingViewset.as_view({'post': 'report_by_date_range'}), name='report_by_date_range'),

    path('waiter_report_by_date_range/<int:restaurant>/',
         InvoiceViewSet.as_view({'post': 'waiter_report_by_date_range'}), name='waiter_report_by_date_range'),

    path('month_wise_total_report/<int:restaurant_id>/',
         ReportingViewset.as_view({'get': 'month_wise_total_report'}), name='month_wise_total_report'),

    path('invoice_all_report/<int:restaurant>/',
         InvoiceViewSet.as_view({'post': 'invoice_all_report'}), name='invoice_all_report'),

    path('admin_all_report/',
         ReportingViewset.as_view({'get': 'admin_all_report'}), name='admin_all_report'),

    path('food_report_by_date_range/',
         ReportingViewset.as_view({'post': 'food_report_by_date_range'}), name='food_report_by_date_range'),

    path('top_food_items_by_date_range/<int:restaurant_id>/',
         InvoiceViewSet.as_view({'post': 'top_food_items_by_date_range'}), name='top_food_items_by_date_range'),

    path('dashboard_total_report/<int:restaurant_id>',
         ReportingViewset.as_view({'get': 'dashboard_total_report'}), name='dashboard_total_report'),
    path('subscription/',
         SubscriptionViewset.as_view({'get': 'list', 'post': 'create'}), name='subscription_list'),
    path('subscription_by_restaurant/<int:restaurant_id>/',
         SubscriptionViewset.as_view({'get': 'subscription_by_restaurant'}), name='subscription_by_restaurant'),

    path('subscription/<int:pk>',
         SubscriptionViewset.as_view({'get': 'retrieve', 'patch': 'update', 'delete': 'destroy'}), name='subscription'),
    path('review/<int:pk>/',
         ReviewViewset.as_view({'delete': 'destroy'}, name='destroy')),

    path('review_list/<int:restaurant>/',
         ReviewViewset.as_view({'get': 'review_list'}, name='review_list')),

    path('print_node/',
         PrintNodeViewSet.as_view({'get': 'list', 'post':'print_node_create'}, name='all_print_node')),

    path('print_node/<int:pk>/',
         PrintNodeViewSet.as_view({'patch': 'print_node_update','delete':'print_node_destroy','get':'retrieve'}, name='print_node')),
    path('print_node_list/<int:restaurant_id>/',
         PrintNodeViewSet.as_view({'get': 'print_node_list'}, name='print_node_list')),
    path('take_away_order/<int:restaurant_id>/',
         TakeAwayOrderViewSet.as_view({'get': 'take_away_order'}, name='take_away_order')),
    path('parent_company_promotion/',
         ParentCompanyPromotionViewSet.as_view({'get': 'list','post':'create'}, name='parent_company_promotion')),
    path('parent_company_promotion/<int:pk>/',
         ParentCompanyPromotionViewSet.as_view({'patch': 'update','delete':'destroy'}, name='parent_company_promotion')),
    path('parent_company_promotions/<int:restaurant_id>/',
         ParentCompanyPromotionViewSet.as_view({'get':'parent_company_promotions'}, name='parent_company_promotions')),
    path('cash_log/',
         CashLogViewSet.as_view({'post': 'restaurant_opening'}, name='restaurant_opening')),
    path('cash_log/<int:pk>/',
         CashLogViewSet.as_view({'patch': 'restaurant_closing'}, name='restaurant_closing')),

    path('restaurant_log_status/<int:restaurant_id>/',
         CashLogViewSet.as_view({'get': 'restaurant_log_status'}, name='restaurant_log_status')),

    path('withdraw_create/',
         WithdrawCashViewSet.as_view({'post': 'withdraw_create'}, name='withdraw_create')),

] + fake_dashboard_urls
