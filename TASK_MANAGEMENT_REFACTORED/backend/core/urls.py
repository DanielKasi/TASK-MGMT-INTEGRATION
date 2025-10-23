from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.conf import settings
from django.conf.urls.static import static
from institution.views import home

urlpatterns = [
    path("", home, name="home"),
    path("login", home, name="fix-login"),
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/user/", include("users.urls")),
    path("api/institution/", include("institution.urls")),
    # path("api/workflow/", include("workflows.urls")),
    path("api/projects/", include("projects.urls")),
    path("api/calendar/", include("calendar2.urls")),
    path("api/approval/", include("approval.urls")),
    path("api/communication/", include("communication.urls")),
    path("api/settings/", include("settings.urls")),
    path("api/audit/", include("audit.urls")),
    path("api/tasks/", include("tasks.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
