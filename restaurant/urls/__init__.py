from .apps import apps_url
from .dashboard import dashboard_urls
from django.urls import include, path


urlpatterns = [
    path('dashboard/', include(dashboard_urls)),
    # path('apps/', include(apps_url)),
    path('apps/customer/', include(apps_url)),
    path('apps/waiter/', include(apps_url)),


]
