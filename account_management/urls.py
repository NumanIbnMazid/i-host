from account_management.views import LoginView, verify_login
from django.urls import include, path
from knox import views as knox_views

# user_account_get_post_patch_delete = UserAccountManagerViewSet.as_view(
#     {
#         "get": "retrieve",
#         "post": "create",
#         # "patch": "update",
#         "delete": "destroy"
#     }
# )

auth_urlpatterns = [
    path("login/", LoginView.as_view(), name="knox_login"),
    path("logout/", knox_views.LogoutView.as_view(), name="knox_logout"),
    # path("reset_password/", reset_password),
    # path("change_password/",
    #      ChangePasswordViewSet.as_view({"post": "create"})),
    path('logoutall/', knox_views.LogoutAllView.as_view(), name='knox_logoutall'),
    path("verify/", verify_login, name="verify_token"),
]
urlpatterns = [
    path("auth/", include(auth_urlpatterns), name="auth"),
    # path("user_account/", user_account_get_post_patch_delete),


]
