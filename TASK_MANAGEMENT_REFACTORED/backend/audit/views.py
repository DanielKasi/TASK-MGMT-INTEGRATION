from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_spectacular.utils import extend_schema
from django.db.models import Q
from .serializers import AuditLogSerializer
from .models import AuditLog
from users.models import Profile
from utilities.pagination import CustomPageNumberPagination

class AuditLogListApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    allowed_ordering_fields = ['timestamp']
    default_ordering = ['-timestamp']

    @extend_schema(
        responses={200: AuditLogSerializer(many=True)},
        description="Retrieve audit logs for an institution with optional filters.",
        summary="Get audit logs",
        tags=["Audit Log Management"],
    )
    def get(self, request):
        search_query = request.query_params.get("search", None)
        user_id = request.query_params.get("user", None)
        action = request.query_params.get("action", None)
        start_date = request.query_params.get("start_date", None)
        end_date = request.query_params.get("end_date", None)
        content_type = request.query_params.get("content_type")
        object_id = request.query_params.get("object_id")

        try:
            user_institution = request.user.profile.institution
        except Profile.DoesNotExist:
            return Response(
                {"error": "Logged-in user does not have a profile."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        auditlogs = AuditLog.objects.filter(institution=user_institution)

        if user_id:
            auditlogs = auditlogs.filter(user_id=user_id)

        if action:
            if action not in dict(AuditLog.ACTION_CHOICES):
                return Response({"error": f"Invalid action '{action}'"}, status=400)
            auditlogs = auditlogs.filter(action=action)

        if content_type:
            auditlogs = auditlogs.filter(content_type__model=content_type.lower())

        if start_date:
            auditlogs = auditlogs.filter(timestamp__date__gte=start_date)
        if end_date:
            auditlogs = auditlogs.filter(timestamp__date__lte=end_date)

        if search_query:
            auditlogs = auditlogs.filter(
                Q(description__icontains=search_query) |
                Q(changes__icontains=search_query)
            )
        
        if object_id:
            auditlogs = auditlogs.filter(object_id=object_id)

        paginator = CustomPageNumberPagination()
        paginated_logs = paginator.paginate_queryset(auditlogs, request)
        serializer = AuditLogSerializer(paginated_logs, many=True)
        return paginator.get_paginated_response(serializer.data)
