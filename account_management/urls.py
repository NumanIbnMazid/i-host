from account_management.views import *
from django.urls import include, path
from knox import views as knox_views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('customer_info', CustomerInfoViewset,
                basename="customer_info")
user_account_get_post_patch_delete = UserAccountManagerViewSet.as_view(
    {
        "get": "retrieve",
        # "post": "create",
        "patch": "update",
        "delete": "destroy"
    }
)


restaurant_account_management = [
    path("restaurant/create_owner/", RestaurantAccountManagerViewSet.as_view({
        "post": "create_owner",
    }), name="create_owner"),
    path("restaurant/create_manager/", RestaurantAccountManagerViewSet.as_view({
        "post": "create_manager",
    }), name="create_manager"),
    path("restaurant/create_waiter/", RestaurantAccountManagerViewSet.as_view({
        "post": "create_waiter",
    }), name="create_waiter"),
    path("restaurant/staff/<int:pk>/", RestaurantAccountManagerViewSet.as_view({
        "get": "retrieve", 'patch': "update"
    }), name="staff_info"),

    path("restaurant/<int:id>/owner_info/", RestaurantAccountManagerViewSet.as_view({
        "get": "owner_info"
    }), name="owner_info"),

    path("restaurant/<int:id>/waiter_info/", RestaurantAccountManagerViewSet.as_view({
        "get": "waiter_info"
    }), name="waiter_info"),

    path("restaurant/<int:staff_id>/delete_waiter/", RestaurantAccountManagerViewSet.as_view({
        "delete": "delete_waiter"}), name="delete_waiter"),

    path("restaurant/<int:staff_id>/delete_manager/", RestaurantAccountManagerViewSet.as_view({
        "delete": "delete_waiter"}), name="delete_waiter"),
    path("restaurant/<int:staff_id>/delete_owner/", RestaurantAccountManagerViewSet.as_view({
        "delete": "delete_waiter"}), name="delete_waiter"),

    path("restaurant/<int:id>/manager_info/", RestaurantAccountManagerViewSet.as_view({
        "get": "manager_info"
    }), name="manager_info"),
]

auth_urlpatterns = [
    path("login/", LoginView.as_view(), name="knox_login"),

    path("otp_auth/", OtpSignUpView.as_view(), name="otp_login"),
    path("get_otp/<str:phone>/",
         UserAccountManagerViewSet.as_view({'get': 'get_otp'}), name="get_otp"),

    path("logout/", knox_views.LogoutView.as_view(), name="knox_logout"),
    # path("reset_password/", reset_password),
    # path("change_password/",
    #      ChangePasswordViewSet.as_view({"post": "create"})),
    path('logoutall/', knox_views.LogoutAllView.as_view(), name='knox_logoutall'),
    path("verify/", verify_login, name="verify_token"),
]
urlpatterns = [
    path('', include(router.urls)),
    path("auth/", include(auth_urlpatterns), name="auth"),
    path("user_account/", user_account_get_post_patch_delete),


]+restaurant_account_management
