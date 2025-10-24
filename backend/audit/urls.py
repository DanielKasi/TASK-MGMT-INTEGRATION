from django.urls import path
from .views import AuditLogListApiView

urlpatterns = [
    path("auditlogs/", AuditLogListApiView.as_view(), name="auditlogs"),
]
