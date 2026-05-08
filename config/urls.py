from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", include("apps.admin_api.urls")),
    path("admin/", admin.site.urls),
    path("admin-panel/", include("apps.admin_panel.urls")),
    path("", include("apps.market.urls")),
    path("", include("apps.accounts.urls")),
    path("", include("apps.planner.urls")),
    path("", include("apps.orders.urls")),
    path("", include("apps.expenses.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
