from account_management.views import *
from django.urls import include, path
from knox import views as knox_views

user_account_get_post_patch_delete = UserAccountManagerViewSet.as_view(
    {
        "get": "retrieve",
        "post": "create",
        # "patch": "update",
        "delete": "destroy"
    }
)

user_account_get_post_patch_delete = RestaurantAccountManagerViewSet.as_view(
    {
        "get": "retrieve",
        "post": "create_owner",
        # "patch": "update",
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


]

auth_urlpatterns = [
    path("login/", LoginView.as_view(), name="knox_login"),
    # path("otp_login/", OtpLoginView.as_view(), name="otp_login"),

    path("logout/", knox_views.LogoutView.as_view(), name="knox_logout"),
    # path("reset_password/", reset_password),
    # path("change_password/",
    #      ChangePasswordViewSet.as_view({"post": "create"})),
    path('logoutall/', knox_views.LogoutAllView.as_view(), name='knox_logoutall'),
    path("verify/", verify_login, name="verify_token"),
]
urlpatterns = [
    path("auth/", include(auth_urlpatterns), name="auth"),
    path("user_account/", user_account_get_post_patch_delete),


]+restaurant_account_management
