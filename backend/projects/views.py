from django.shortcuts import render
from users.models import CustomUser
from .models import (
    Project,
    ProjectStatus,
    Task,
    TaskTimeSheet,
    TaskPriority,
    TaskUserAssignees,
    ProjectMessage,
    TaskMessage,
    TaskExtensionRequest,
    ProjectTaskStatus,
    ProjectDiscussionParticipant,
    TaskDiscussionParticipant,
    ProjectTaskEmailConfig,
)
from .serializers import (
    ProjectSerializer,
    ProjectStatusSerializer,
    TaskTimeSheetSerializer,
    TaskSerializer,
    TaskPrioritySerializer,
    MainDashboardSerializer,
    ProjectAnalyticsDashboardSerializer,
    TaskAnalyticsDashboardSerializer,
    ProjectUsersReadSerializer,
    UserProjectSerializer,
    ProjectMessageSerializer,
    TaskMessageSerializer,
    TaskExtensionRequestSerializer,
    TaskExtensionApprovalReason,
    ProjectTaskStatusSerializer,
    ProjectCreateTaskStatusSerializer,
    DefaultProjectTaskStatusSerializer,
    DefaultStatusConfigSerializer,
    ProjectDiscussionParticipantSerializer,
    TaskDiscussionParticipantSerializer,
    ProjectTaskEmailConfigSerializer,
)
from rest_framework.views import APIView, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from institution.models import Institution
from utilities.pagination import CustomPageNumberPagination
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse, OpenApiTypes
from django.db.models import Count, Q
from django.db import transaction
from utilities.sortable_api import SortableAPIMixin
from django.utils import timezone
from rest_framework.parsers import MultiPartParser, FormParser
from utilities.helpers import  to_datetime
from django.conf import settings
from django.db.models import Count, Avg, F, Q
from django.db.models.functions import ExtractYear, ExtractMonth
from datetime import datetime
from django.db import models
from .helpers import send_email_for_task_status_change
from .task import send_project_or_task_email
from utilities.helpers import permission_required
from django.utils.decorators import method_decorator
from django.db.models import Prefetch
from users.models import StaffGroup
from django.db.models import Case, When, BooleanField, Q
from django.utils.dateparse import parse_datetime
import json
import os

class TaskListCreateView(APIView, SortableAPIMixin):
    permission_classes = [IsAuthenticated]
    allowed_ordering_fields = ['task_name', 'created_at', 'task_status__weight','start_date', 'end_date']
    default_ordering = ['-created_at']

    @extend_schema(
        parameters=[
            {"name": "search", "type": "str", "description": "Search by task name or description"},
            {"name": "created_at", "type": "date", "description": "Filter by creation date"},
            {"name": "project", "type": "int", "description": "Filter by project ID"},
            {"name": "task_status", "type": "int", "description": "Filter by task status ID"},
            {"name": "priority", "type": "int", "description": "Filter by priority ID"},
            {"name": "approval_status", "type": "str", "description": "Filter by approval status (pending/approved/rejected)"},
            {"name": "ordering", "type": "str", "description": "Sort by fields (e.g., 'task_name,-created_at')"},
        ],
        responses={
            200: OpenApiResponse(
                response=TaskSerializer(many=True),
                description="List of tasks.",
            ),
            400: OpenApiResponse(description="Invalid ordering field."),
            404: OpenApiResponse(description="Institution not found."),
        },
        tags=["Project Task Management"],
    )
    @method_decorator(permission_required('can_view_all_tasks'))
    def get(self, request):
        user = request.user.profile
        search_query = request.query_params.get("search", None)
        created_at = request.query_params.get("created_at", None)
        project_id = request.query_params.get("project", None)
        task_status_id = request.query_params.get("task_status", None)
        priority_id = request.query_params.get("priority", None)
        approval_status = request.query_params.get("approval_status", None)
        user_id = request.query_params.get("user", None)
        progress_status = request.query_params.get("progress_status", None)
        unassigned = request.query_params.get("unassigned", None)

        unassigned_values  = ("true", "false", "1", "0", "")
        if unassigned is not None and unassigned not in unassigned_values:
            return Response(
                {"error": "Invalid 'unassigned' parameter. Use 'true' or 'false'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        is_unassigned = unassigned in ("true", "1")

        # Date range filters
        start_date_after = request.query_params.get("start_date_after")
        start_date_before = request.query_params.get("start_date_before")
        end_date_after = request.query_params.get("end_date_after")
        end_date_before = request.query_params.get("end_date_before")

        # Validate progress_status
        valid_statuses = {"completed", "overdue", "not_started", "in_progress"}
        if progress_status and progress_status not in valid_statuses:
            return Response({
                "error": f"Invalid progress_status. Must be one of: {', '.join(valid_statuses)}"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        institution = request.user.profile.institution

        tasks = Task.objects.filter(
            user_manager__profile__institution=institution,
            deleted_at__isnull=True
        )

        # Apply date range filters (before progress status annotation)
        datetime_filters = []

        if start_date_after:
            dt = parse_datetime(start_date_after)
            if dt is None:
                return Response(
                    {"error": "Invalid start_date_after format. Use ISO 8601 (e.g., '2025-10-07T10:30:00+03:00')"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            tasks = tasks.filter(start_date__gte=dt)

        if start_date_before:
            dt = parse_datetime(start_date_before)
            if dt is None:
                return Response(
                    {"error": "Invalid start_date_before format. Use ISO 8601 (e.g., '2025-10-07T10:30:00+03:00')"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            tasks = tasks.filter(start_date__lte=dt)

        if end_date_after:
            dt = parse_datetime(end_date_after)
            if dt is None:
                return Response(
                    {"error": "Invalid end_date_after format. Use ISO 8601 (e.g., '2025-10-07T10:30:00+03:00')"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            tasks = tasks.filter(end_date__gte=dt)

        if end_date_before:
            dt = parse_datetime(end_date_before)
            if dt is None:
                return Response(
                    {"error": "Invalid end_date_before format. Use ISO 8601 (e.g., '2025-10-07T10:30:00+03:00')"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            tasks = tasks.filter(end_date__lte=dt)

        # Apply progress status filtering
        if progress_status:
            now = timezone.now()  # timezone-aware datetime
            tasks = tasks.annotate(
                is_completed=Case(
                    When(completion_date__isnull=False, then=True),
                    default=False,
                    output_field=BooleanField()
                ),
                is_overdue=Case(
                    When(
                        completion_date__isnull=True,
                        end_date__isnull=False,
                        end_date__lt=now,
                        then=True
                    ),
                    default=False,
                    output_field=BooleanField()
                ),
                is_not_started=Case(
                    When(
                        completion_date__isnull=True,
                        start_date__isnull=True,
                        then=True
                    ),
                    When(
                        completion_date__isnull=True,
                        start_date__gt=now,
                        then=True
                    ),
                    default=False,
                    output_field=BooleanField()
                )
            )

            if progress_status == "completed":
                tasks = tasks.filter(completion_date__isnull=False)
            elif progress_status == "overdue":
                tasks = tasks.filter(is_overdue=True)
            elif progress_status == "not_started":
                tasks = tasks.filter(is_not_started=True)
            elif progress_status == "in_progress":
                tasks = tasks.filter(
                    completion_date__isnull=True,
                    is_overdue=False,
                    is_not_started=False
                )

        # Apply other filters
        if user_id:
            tasks = tasks.filter(
                Q(user_assignees__user_assigned__id=user_id) |
                Q(user_manager=user_id) |
                Q(
                    staff_group_assignees__group_assigned__staffgroupuser__user__id=user_id,
                    staff_group_assignees__group_assigned__staffgroupuser__deleted_at__isnull=True
                )
            ).distinct()

        if is_unassigned:
            tasks = tasks.filter(project__isnull=True)
        elif project_id:
            tasks = tasks.filter(project__id=project_id)

        if search_query:
            tasks = tasks.filter(
                Q(task_name__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        if created_at:
            tasks = tasks.filter(created_at=created_at)

        if task_status_id:
            tasks = tasks.filter(task_status__id=task_status_id)

        if priority_id:
            tasks = tasks.filter(priority__id=priority_id)

        if approval_status:
            tasks = tasks.filter(approval_status=approval_status)

        # Sorting
        try:
            tasks = self.apply_sorting(tasks, request)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Pagination
        paginator = CustomPageNumberPagination()
        paginated_qs = paginator.paginate_queryset(tasks, request)
        serializer = TaskSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        request=TaskSerializer,
        responses={
            201: OpenApiResponse(
                response=TaskSerializer,
                description="Task created successfully.",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors.",
            ),
            404: OpenApiResponse(description="Institution not found."),
        },
        tags=["Project Task Management"],
    )
    @method_decorator(permission_required('can_create_tasks'))
    @transaction.atomic
    def post(self, request):
        try:
            user_profile = request.user.profile
            institution = user_profile.institution
        except (AttributeError, Institution.DoesNotExist):
            return Response(
                {"error": "User profile or institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        task_serializer = TaskSerializer(data=request.data, context={"request": request})
        task_serializer.is_valid(raise_exception=True)
        instance = task_serializer.save()
        instance.confirm_create()

        # Send assignment notification email
        user_manager = task_serializer.validated_data.get("user_manager")
        user_assignee_ids = task_serializer.validated_data.get("user_assignees", [])

        frontend_url = settings.FRONTEND_URL
        task_url = f"{frontend_url}/task-mgt/task/{instance.id}"

        send_project_or_task_email.delay_on_commit(
            [user_manager.id] if user_manager else [],
            list(user_assignee_ids),
            url=task_url,
            task_id=instance.id,
            is_update=False,
        )

        return Response(TaskSerializer(instance, context={"request": request}).data, status=status.HTTP_201_CREATED)

class TaskDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=TaskSerializer,
                description="Task details.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Task not found.",
            ),
        },
        tags=["Project Task Management"],
    )
    @method_decorator(permission_required('can_view_tasks'))
    def get(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        task = get_object_or_404(Task, pk=pk,user_manager__profile__institution=institution, deleted_at__isnull=True)
        serializer = TaskSerializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Task marked for deletion and sent for approval.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Task not found.",
            ),
        },
        tags=["Project Task Management"],
    )
    @method_decorator(permission_required('can_delete_tasks'))
    @transaction.atomic
    def delete(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        task = get_object_or_404(Task, pk=pk, user_manager__profile__institution=institution, deleted_at__isnull=True)
        task.approval_status = 'under_deletion'
        task.save(update_fields=['approval_status'])
        task.confirm_delete()
        return Response(
            {"message": "Task submitted for deletion approval."},
            status=status.HTTP_200_OK
        )

    @extend_schema(
        request=TaskSerializer,
        responses={
            200: OpenApiResponse(
                response=TaskSerializer,
                description="Task updated successfully.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Task not found.",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors.",
            ),
        },
        tags=["Project Task Management"],
    )
    @method_decorator(permission_required('can_edit_tasks'))
    @transaction.atomic
    def patch(self, request, pk):
        # Get institution safely
        try:
            user_profile = request.user.profile
            institution = user_profile.institution
        except (AttributeError, Institution.DoesNotExist):
            return Response(
                {"error": "User profile or institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Fetch task
        task = get_object_or_404(
            Task,
            pk=pk,
            user_manager__profile__institution=institution,
            deleted_at__isnull=True
        )

        # Capture OLD state BEFORE update
        old_manager = task.user_manager
        old_assignee_ids = set(task.user_assignees.values_list("user_assigned_id", flat=True))
        old_start = to_datetime(task.start_date)
        old_end = to_datetime(task.end_date)

        # Extract new dates
        new_start_date = request.data.get("start_date")
        new_end_date = request.data.get("end_date")
        new_start = to_datetime(new_start_date)
        new_end = to_datetime(new_end_date)
        # Set approval status
        task.approval_status = 'under_update'
        task.save(update_fields=['approval_status'])

        # Validate and save
        serializer = TaskSerializer(
            task,
            data=request.data,
            partial=True,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        instance.confirm_update()

        # Send status change email (completion/failure)
        send_email_for_task_status_change(instance)

        # Determine if this update resulted in completion or failure
        is_completed = False
        is_failed = False
        if instance.applied_project_task_status == instance.project.completed_status:
            is_completed = True
        elif instance.applied_project_task_status == instance.project.failed_status:
            is_failed = True

        is_terminal_state = is_completed or is_failed

        # Build task URL
        frontend_url = settings.FRONTEND_URL
        task_url = f"{frontend_url}/task-mgt/task/{instance.id}"

        # Get NEW values from validated_data
        new_manager = serializer.validated_data.get("user_manager")
        new_assignee_ids = serializer.validated_data.get("user_assignees", [])

        # Determine changes
        manager_changed = (new_manager != old_manager)
        added_assignee_ids = set(new_assignee_ids) - set(old_assignee_ids)

        # 1. Notify ONLY newly added users — but NOT if task is completed/failed
        if not is_terminal_state and (manager_changed or added_assignee_ids):
            changed_manager = [new_manager.id] if manager_changed and new_manager else []
            send_project_or_task_email.delay_on_commit(
                user_manager_ids=changed_manager,
                user_assignee_ids=list(added_assignee_ids),
                url=task_url,
                task_id=instance.id,
                is_update=False,
            )

        # 2. UPDATE team if timeline changed — but NOT if task is completed/failed
        if not is_terminal_state and (new_start != old_start or new_end != old_end):
            timeline_manager_list = [old_manager.id] if old_manager else []
            send_project_or_task_email.delay_on_commit(
                user_manager_ids=timeline_manager_list,
                user_assignee_ids=list(old_assignee_ids),
                url=task_url,
                task_id=instance.id,
                is_update=True,
            )

        return Response(serializer.data, status=status.HTTP_200_OK)

class TaskTimeSheetView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="Start or End Task",
        summary="Start or end a task",
        request=TaskTimeSheetSerializer,
        responses={
            200: TaskTimeSheetSerializer,
            400: OpenApiResponse(description="Bad Request"),
            401: OpenApiResponse(description="Unauthorized"),
            403: OpenApiResponse(description="Forbidden"),
        },
        tags=["Projects Mgt"],
    )
    @method_decorator(permission_required('can_update_task_timesheets'))
    @transaction.atomic
    def patch(self, request, task_timesheet_id):
        task_timesheet = TaskTimeSheet.objects.filter(id=task_timesheet_id, deleted_at__isnull=True).first()

        if not task_timesheet:
            return Response(
                {"error": "Task timesheet not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.user.profile not in task_timesheet.task.managers.all():
            return Response(
                {"error": "You do not have permission to update this task timesheet."},
                status=status.HTTP_403_FORBIDDEN,
            )

        task_timesheet.approval_status = 'under_update'
        task_timesheet.save(update_fields=['approval_status'])


        serializer = TaskTimeSheetSerializer(
            task_timesheet,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        if serializer.is_valid():
            serializer.save(updated_by=request.user.profile)
            task_timesheet.confirm_update()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DashboardAnalyticsView(APIView):
    @extend_schema(
        tags=['Dashboard'],
        summary='Retrieve dashboard analytics for user institution',
        description='Provides analytics data for projects and tasks filtered by the user\'s institution, including counts by status, priority, and other metrics.',
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'projects': {
                        'type': 'object',
                        'properties': {
                            'total': {'type': 'integer'},
                            'by_status': {
                                'type': 'array',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'status': {'type': 'string'},
                                        'count': {'type': 'integer'}
                                    }
                                }
                            }
                        }
                    },
                    'tasks': {
                        'type': 'object',
                        'properties': {
                            'total': {'type': 'integer'},
                            'by_status': {
                                'type': 'array',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'status': {'type': 'string'},
                                        'count': {'type': 'integer'}
                                    }
                                }
                            },
                            'by_priority': {
                                'type': 'array',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'priority': {'type': 'string'},
                                        'count': {'type': 'integer'}
                                    }
                                }
                            }
                        }
                    },
                    'active_projects': {'type': 'integer'},
                    'overdue_tasks': {'type': 'integer'}
                }
            },
            400: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        examples=[
            OpenApiExample(
                'Success Response',
                value={
                    'projects': {
                        'total': 5,
                        'by_status': [
                            {'status': 'not_started', 'count': 2},
                            {'status': 'in_progress', 'count': 2},
                            {'status': 'completed', 'count': 1},
                            {'status': 'on_hold', 'count': 0},
                            {'status': 'cancelled', 'count': 0}
                        ]
                    },
                    'tasks': {
                        'total': 15,
                        'by_status': [
                            {'status': 'not_started', 'count': 6},
                            {'status': 'in_progress', 'count': 5},
                            {'status': 'completed', 'count': 3},
                            {'status': 'on_hold', 'count': 1}
                        ],
                        'by_priority': [
                            {'priority': 'low', 'count': 3},
                            {'priority': 'medium', 'count': 7},
                            {'priority': 'high', 'count': 4},
                            {'priority': 'urgent', 'count': 1}
                        ]
                    },
                    'active_projects': 4,
                    'overdue_tasks': 2
                }
            ),
            OpenApiExample(
                'Error Response',
                value={
                    'error': 'User has no associated institution'
                },
                status_codes=['400']
            )
        ]
    )
    def get(self, request):
        # Get user's institution
        institution = getattr(request.user.profile, 'institution', None)
        if not institution:
            return Response({'error': 'User has no associated institution'}, status=status.HTTP_400_BAD_REQUEST)

        # Project analytics filtered by institution
        project_counts = Project.objects.filter(
            deleted_at__isnull=True,
            institution=institution
        ).aggregate(total=Count('id'))
        project_status_counts = Project.objects.filter(
            deleted_at__isnull=True,
            institution=institution
        ).values('project_status').annotate(count=Count('id'))
        active_projects = Project.objects.filter(
            deleted_at__isnull=True,
            institution=institution
        ).exclude(project_status__in=['completed', 'cancelled']).count()

        # Task analytics filtered by institution
        task_counts = Task.objects.filter(
            deleted_at__isnull=True,
            project__institution=institution
        ).aggregate(total=Count('id'))
        task_status_counts = Task.objects.filter(
            deleted_at__isnull=True,
            project__institution=institution
        ).values('task_status').annotate(count=Count('id'))
        task_priority_counts = Task.objects.filter(
            deleted_at__isnull=True,
            project__institution=institution
        ).values('priority').annotate(count=Count('id'))
        overdue_tasks = Task.objects.filter(
            deleted_at__isnull=True,
            project__institution=institution,
            end_date__lt=timezone.now().date(),
            task_status__in=['not_started', 'in_progress', 'on_hold']
        ).count()

        # Format response
        response_data = {
            'projects': {
                'total': project_counts['total'],
                'by_status': [
                    {
                        'status': status['project_status'],
                        'count': status['count']
                    } for status in project_status_counts
                ]
            },
            'tasks': {
                'total': task_counts['total'],
                'by_status': [
                    {
                        'status': status['task_status'],
                        'count': status['count']
                    } for status in task_status_counts
                ],
                'by_priority': [
                    {
                        'priority': priority['priority'],
                        'count': priority['count']
                    } for priority in task_priority_counts
                ]
            },
            'active_projects': active_projects,
            'overdue_tasks': overdue_tasks
        }

        return Response(response_data, status=status.HTTP_200_OK)

class ProjectStatusListCreateView(APIView, SortableAPIMixin):
    permission_classes = [IsAuthenticated]
    allowed_ordering_fields = ['status_name', 'created_at', 'weight']
    default_ordering = ['weight']

    @extend_schema(
        request=ProjectStatusSerializer,
        responses={
            201: OpenApiResponse(
                response=ProjectStatusSerializer,
                description="Project status created successfully.",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors.",
            ),
        },
        tags=["Project Management"],
    )
    @method_decorator(permission_required('can_create_project_statuses'))
    @transaction.atomic()
    def post(self, request):
        serializer = ProjectStatusSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            instance = serializer.save()
            instance.confirm_create()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        parameters=[
            {"name": "search", "type": "str", "description": "Search by status name or description"},
            {"name": "created_at", "type": "date", "description": "Filter by creation date"},
            {"name": "status", "type": "str", "description": "Filter by approval status (pending/approved/rejected)"},
            {"name": "ordering", "type": "str", "description": "Sort by fields (e.g., 'status_name,-created_at')"},
        ],
        responses={
            200: OpenApiResponse(
                response=ProjectStatusSerializer(many=True),
                description="List of project statuses.",
            ),
            400: OpenApiResponse(description="Invalid ordering field."),
            404: OpenApiResponse(description="Institution not found."),
        },
        tags=["Project Management"],
    )
    @method_decorator(permission_required('can_view_project_statuses'))
    def get(self, request):
        user = request.user.profile
        search_query = request.query_params.get("search", None)
        created_at = request.query_params.get("created_at", None)
        status_filter = request.query_params.get("status", None)

        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        statuses = ProjectStatus.objects.filter(
            institution=institution, deleted_at__isnull=True
        )

        if search_query:
            statuses = statuses.filter(
                Q(status_name__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        if created_at:
            statuses = statuses.filter(created_at=created_at)

        if status_filter in ['pending', 'approved', 'rejected']:
            statuses = statuses.filter(approval_status=status_filter)

        try:
            statuses = self.apply_sorting(statuses, request)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        paginator = CustomPageNumberPagination()
        paginated_qs = paginator.paginate_queryset(statuses, request)
        serializer = ProjectStatusSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)

class ProjectStatusDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=ProjectStatusSerializer,
                description="Project status details.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Project status not found.",
            ),
        },
        tags=["Project Management"],
    )
    @method_decorator(permission_required('can_view_project_statuses'))
    def get(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        status_obj = get_object_or_404(ProjectStatus, pk=pk, institution=institution, deleted_at__isnull=True)
        serializer = ProjectStatusSerializer(status_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Project status marked for deletion and sent for approval.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Project status not found.",
            ),
        },
        tags=["Project Management"],
    )
    @method_decorator(permission_required('can_delete_project_statuses'))
    @transaction.atomic()
    def delete(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        status_obj = get_object_or_404(ProjectStatus, pk=pk, institution=institution, deleted_at__isnull=True)
        status_obj.approval_status = 'under_deletion'
        status_obj.save(update_fields=['approval_status'])
        status_obj.confirm_delete()
        return Response(
            {"message": "Project status submitted for deletion approval."},
            status=status.HTTP_200_OK
        )

    @extend_schema(
        request=ProjectStatusSerializer,
        responses={
            200: OpenApiResponse(
                response=ProjectStatusSerializer,
                description="Project status updated successfully.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Project status not found.",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors.",
            ),
        },
        tags=["Project Management"],
    )
    @method_decorator(permission_required('can_edit_project_statuses'))
    @transaction.atomic()
    def patch(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        status_obj = get_object_or_404(ProjectStatus, pk=pk, institution=institution, deleted_at__isnull=True)
        status_obj.approval_status = 'under_update'
        status_obj.save(update_fields=['approval_status'])
        serializer = ProjectStatusSerializer(status_obj, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            instance = serializer.save()
            instance.confirm_update()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProjectListCreateView(APIView, SortableAPIMixin):
    permission_classes = [IsAuthenticated]
    allowed_ordering_fields = ['project_name', 'created_at', 'start_date', 'end_date']
    default_ordering = ['-created_at']

    @extend_schema(
        request=ProjectSerializer,
        responses={
            201: OpenApiResponse(
                response=ProjectSerializer,
                description="Project created successfully.",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors.",
            ),
        },
        tags=["Project Management"],
    )
    @method_decorator(permission_required('can_create_projects'))
    @transaction.atomic()
    def post(self, request):
        project_serializer = ProjectSerializer(data=request.data, context={"request": request})
        project_serializer.is_valid(raise_exception=True)
        project = project_serializer.save()

        import json
        raw_statuses = request.data.get("project_task_statuses", [])

        if isinstance(raw_statuses, str):
            try:
                raw_statuses = json.loads(raw_statuses)
            except json.JSONDecodeError:
                return Response({"error": "Invalid JSON in project_task_statuses."}, status=400)

        if not isinstance(raw_statuses, list):
            return Response({"error": "project_task_statuses must be a list."}, status=400)

        for status_data in raw_statuses:
            if not isinstance(status_data, dict):
                return Response({"error": "Each project task status must be a dictionary."}, status=400)

            task_status_serializer = ProjectCreateTaskStatusSerializer(
                data=status_data,
                context={"request": request, "project": project}
            )
            task_status_serializer.is_valid(raise_exception=True)
            task_status_serializer.save()

        user_manager = project_serializer.validated_data.get("user_manager")
        user_assignee_ids = project_serializer.validated_data.get("user_assignees", [])

        frontend_url = settings.FRONTEND_URL
        project_url = f"{frontend_url}/projects/{project.id}"

        send_project_or_task_email.delay_on_commit(
            [user_manager.id] if user_manager else [],
            list(user_assignee_ids),
            url=project_url,
            project_id=project.id,
            is_update=False,
        )

        return Response(ProjectSerializer(project, context={"request": request}).data, status=201)


    @extend_schema(
        parameters=[
            {"name": "search", "type": "str", "description": "Search by project name or description"},
            {"name": "status", "type": "int", "description": "Filter by project status ID"},
            {"name": "created_at", "type": "date", "description": "Filter by creation date"},
            {"name": "approval_status", "type": "str", "description": "Filter by approval status (pending/approved/rejected)"},
            {"name": "ordering", "type": "str", "description": "Sort by fields (e.g., 'project_name,-created_at')"},
        ],
        responses={
            200: OpenApiResponse(
                response=ProjectSerializer(many=True),
                description="List of projects.",
            ),
            400: OpenApiResponse(description="Invalid ordering field."),
            404: OpenApiResponse(description="Institution not found."),
        },
        tags=["Project Management"],
    )
    @method_decorator(permission_required('can_view_all_projects'))
    def get(self, request):
        user = request.user.profile
        search_query = request.query_params.get("search", None)
        status_query = request.query_params.get("status", None)
        project_id = request.query_params.get("project", None)
        created_at = request.query_params.get("created_at", None)
        approval_status = request.query_params.get("approval_status", None)
        user_id = request.query_params.get("user_id", None)

        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        projects = Project.objects.filter(
            institution=institution, deleted_at__isnull=True
        )

        if user_id:
            projects = projects.filter(
                Q(user_manager=user_id) |
                Q(user_assignees__user_assigned__id=user_id) |
                Q(staff_group_assignees__group_assigned__staffgroupuser__deleted_at__isnull=True) |
                Q(staff_group_assignees__group_assigned__staffgroupuser__user__id=user_id)
            ).distinct()

        if search_query:
            projects = projects.filter(
                Q(project_name__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        if status_query:
            projects = projects.filter(project_status__id=status_query)

        if created_at:
            projects = projects.filter(created_at=created_at)

        if project_id:
            projects = projects.filter(id=project_id)

        if approval_status in ['pending', 'approved', 'rejected']:
            projects = projects.filter(approval_status=approval_status)

        try:
            projects = self.apply_sorting(projects, request)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        paginator = CustomPageNumberPagination()
        paginated_qs = paginator.paginate_queryset(projects, request)
        serializer = ProjectSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)


class ProjectDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=ProjectSerializer,
                description="Project details.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Project not found.",
            ),
        },
        tags=["Project Management"],
    )
    @method_decorator(permission_required('can_view_projects'))
    def get(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        project = get_object_or_404(Project, pk=pk, institution=institution, deleted_at__isnull=True)
        serializer = ProjectSerializer(project)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Project marked for deletion and sent for approval.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Project not found.",
            ),
        },
        tags=["Project Management"],
    )
    @method_decorator(permission_required('can_delete_projects'))
    @transaction.atomic()
    def delete(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        project = get_object_or_404(Project, pk=pk, institution=institution, deleted_at__isnull=True)
        project.approval_status = 'under_deletion'
        project.save(update_fields=['approval_status'])
        project.confirm_delete()
        return Response(
            {"message": "Project submitted for deletion approval."},
            status=status.HTTP_200_OK
        )

    @extend_schema(
        request=ProjectSerializer,
        responses={
            200: OpenApiResponse(
                response=ProjectSerializer,
                description="Project updated successfully.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Project not found.",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors.",
            ),
        },
        tags=["Project Management"],
    )
    @method_decorator(permission_required('can_edit_projects'))
    @transaction.atomic()
    def patch(self, request, pk):
        # Get institution safely
        try:
            user_profile = request.user.profile
            institution = user_profile.institution
        except (AttributeError, Institution.DoesNotExist):
            return Response(
                {"error": "User profile or institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Fetch project
        project = get_object_or_404(
            Project,
            pk=pk,
            institution=institution,
            deleted_at__isnull=True
        )

        # Capture OLD state BEFORE update
        old_manager = project.user_manager
        old_assignee_ids = set(project.user_assignees.values_list("user_assigned_id", flat=True))
        old_start = to_datetime(project.start_date)
        old_end = to_datetime(project.end_date)

        # Extract new dates
        new_start_date = request.data.get("start_date")
        new_end_date = request.data.get("end_date")
        new_start = to_datetime(new_start_date)
        new_end = to_datetime(new_end_date)

        # Set approval status
        project.approval_status = 'under_update'
        project.save(update_fields=['approval_status'])

        # Validate and save project updates
        serializer = ProjectSerializer(
            project,
            data=request.data,
            partial=True,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        updated_project = serializer.save()
        updated_project.confirm_update()

        # Handle project statuses(replace all)
        raw_statuses = request.data.get("project_task_statuses")

        if raw_statuses is not None:
            import json

            if isinstance(raw_statuses, str):
                try:
                    raw_statuses = json.loads(raw_statuses)
                except json.JSONDecodeError:
                    return Response({"error": "Invalid JSON in project_task_statuses."}, status=400)

            if not isinstance(raw_statuses, list):
                return Response({"error": "project_task_statuses must be a list."}, status=400)

            validated_statuses = []
            for status_data in raw_statuses:
                if not isinstance(status_data, dict):
                    return Response({"error": "Each project task status must be a dictionary."}, status=400)

                task_status_serializer = ProjectCreateTaskStatusSerializer(
                    data=status_data,
                    context={"request": request, "project": project}
                )
                task_status_serializer.is_valid(raise_exception=True)
                task_status_serializer.confirm_create()
                validated_statuses.append(task_status_serializer.validated_data)

            from django.utils import timezone
            ProjectTaskStatus.objects.filter(project=project).update(deleted_at=timezone.now())

            for status_data in validated_statuses:
                ProjectTaskStatus.objects.create(
                    project=project,
                    name=status_data['name'],
                    description=status_data.get('description', ''),
                    weight=status_data.get('weight', 0),
                    color_code=status_data.get('color_code', '#9C9C9C'),
                    created_by=request.user.profile,
                    updated_by=request.user.profile
                )

        # Handle notifications and emails
        frontend_url = settings.FRONTEND_URL
        project_url = f"{frontend_url}/projects/{updated_project.id}"

        new_manager = serializer.validated_data.get("user_manager")
        new_assignee_ids = serializer.validated_data.get("user_assignees", [])

        manager_changed = (new_manager != old_manager)
        changed_manager = [new_manager.id] if manager_changed and new_manager else []
        added_assignee_ids = set(new_assignee_ids) - set(old_assignee_ids)

        # Notify new or changed users
        if manager_changed or added_assignee_ids:
            send_project_or_task_email.delay_on_commit(
                user_manager_ids=changed_manager,
                user_assignee_ids=list(added_assignee_ids),
                url=project_url,
                project_id=updated_project.id,
                is_update=False,
            )

        # Notify timeline change
        if new_start != old_start or new_end != old_end:
            old_team_manager_ids = [old_manager.id] if old_manager else []
            send_project_or_task_email.delay_on_commit(
                user_manager_ids=old_team_manager_ids,
                user_assignee_ids=list(old_assignee_ids),
                url=project_url,
                project_id=updated_project.id,
                is_update=True,
            )

        return Response(ProjectSerializer(updated_project, context={"request": request}).data, status=200)


class TaskPriorityListCreateView(APIView, SortableAPIMixin):
    permission_classes = [IsAuthenticated]
    allowed_ordering_fields = ['name', 'created_at', 'weight']
    default_ordering = ['weight']

    @extend_schema(
        parameters=[
            {"name": "search", "type": "str", "description": "Search by status name or description"},
            {"name": "created_at", "type": "date", "description": "Filter by creation date"},
            {"name": "status", "type": "str", "description": "Filter by approval status (pending/approved/rejected)"},
            {"name": "ordering", "type": "str", "description": "Sort by fields (e.g., 'name,-created_at')"},
        ],
        responses={
            200: OpenApiResponse(
                response=TaskPrioritySerializer(many=True),
                description="List of task priority.",
            ),
            400: OpenApiResponse(description="Invalid ordering field."),
            404: OpenApiResponse(description="Institution not found."),
        },
        tags=["Project Task Priority Management"],
    )
    @method_decorator(permission_required('can_view_task_priority'))
    def get(self, request):
        user = request.user.profile
        search_query = request.query_params.get("search", None)
        created_at = request.query_params.get("created_at", None)
        color_code = request.query_params.get("color_code", None)

        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        priorities = TaskPriority.objects.filter(
            institution=institution, deleted_at__isnull=True
        )

        if search_query:
            priorities = priorities.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        if created_at:
            priorities = priorities.filter(created_at=created_at)

        if color_code:
            priorities = priorities.filter(approval_status=color_code)

        try:
            priorities = self.apply_sorting(priorities, request)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        paginator = CustomPageNumberPagination()
        paginated_qs = paginator.paginate_queryset(priorities, request)
        serializer = TaskPrioritySerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)


    @extend_schema(
        request=TaskPrioritySerializer,
        responses={
            201: OpenApiResponse(
                response=TaskPrioritySerializer,
                description="Task Priority created successfully.",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors.",
            ),
        },
        tags=["Project Task Priority Management"],
    )
    @method_decorator(permission_required('can_create_task_priority'))
    @transaction.atomic()
    def post(self, request):
        serializer = TaskPrioritySerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            instance = serializer.save()
            instance.confirm_create()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskPriorityDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=TaskPrioritySerializer,
                description="Task priority details.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Task priority not found.",
            ),
        },
        tags=["Project Task Priority Management"],
    )
    @method_decorator(permission_required('can_view_task_priority'))
    def get(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        status_obj = get_object_or_404(TaskPriority, pk=pk, institution=institution, deleted_at__isnull=True)
        serializer = TaskPrioritySerializer(status_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Task priority marked for deletion and sent for approval.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Task priority not found.",
            ),
        },
        tags=["Project Task Priority Management"],
    )
    @method_decorator(permission_required('can_delete_task_priority'))
    @transaction.atomic()
    def delete(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        status_obj = get_object_or_404(TaskPriority, pk=pk, institution=institution, deleted_at__isnull=True)
        status_obj.approval_status = 'under_deletion'
        status_obj.save(update_fields=['approval_status'])
        status_obj.confirm_delete()
        return Response(
            {"message": "Task priority submitted for deletion approval."},
            status=status.HTTP_200_OK
        )


    @extend_schema(
        request=TaskPrioritySerializer,
        responses={
            200: OpenApiResponse(
                response=TaskPrioritySerializer,
                description="Task priority updated successfully.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Task priority not found.",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors.",
            ),
        },
        tags=["Project Task Priority Management"],
    )
    @method_decorator(permission_required('can_edit_task_priority'))
    @transaction.atomic()
    def patch(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        status_obj = get_object_or_404(TaskPriority, pk=pk, institution=institution, deleted_at__isnull=True)
        status_obj.approval_status = 'under_update'
        status_obj.save(update_fields=['approval_status'])
        serializer = TaskPrioritySerializer(status_obj, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            instance = serializer.save()
            instance.confirm_update()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MainDashboardView(APIView):

    @extend_schema(
        summary="Get main dashboard analytics",
        description=(
            "Returns key metrics for the authenticated user's institution, "
            "including total active projects, total active tasks, and a yearly "
            "distribution of project creation. Only non-deleted records are counted."
        ),
        responses=MainDashboardSerializer,
        tags=["Dashboard Analytics Management"],
    )
    def get(self, request):

        institution = getattr(request.user.profile, 'institution', None)
        if not institution:
            return Response({"error": "User has no associated institution."},status=status.HTTP_400_BAD_REQUEST)

        # Count active projects (not soft-deleted)
        total_project = Project.objects.filter(deleted_at__isnull=True, institution=institution).count()

        # Count active tasks in active projects or standalone tasks
        total_task = Task.objects.filter(
            deleted_at__isnull=True
        ).filter(
            Q(project__deleted_at__isnull=True, project__institution=institution)
            | Q(project__isnull=True, task_status__institution=institution)
        ).count()

        # Aggregate project count by year of creation
        project_count_by_year = (
            Project.objects.filter(deleted_at__isnull=True,institution=institution)
            .annotate(year=ExtractYear('created_at'))
            .values('year')
            .annotate(project_count=Count('id'))
            .order_by('year')
        )
        # Prepare data for serialization
        data = {
            "total_task": total_task,
            "total_project": total_project,
            "project_count_by_year": list(project_count_by_year),
        }

        serializer = MainDashboardSerializer(data)
        return Response(serializer.data)


class ProjectAnalyticsDashboardView(APIView):

    @extend_schema(
        summary="Get project dashboard analytics",
        description=(
            "Returns key project analytic metrics for the authenticated user's institution, "
            "including total projects/tasks, average duration, assigned employees, "
            "status overviews, progress tracking, and recent projects."
        ),
        responses=ProjectAnalyticsDashboardSerializer,
        tags=["Dashboard Analytics Management"],
    )
    def get(self, request):
        institution = getattr(request.user.profile, 'institution', None)
        if not institution:
            return Response(
                {"error": "User has no associated institution."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1. Total active projects
        total_projects = Project.objects.filter(
            deleted_at__isnull=True,
            institution=institution
        ).count()

        # 2. Total active tasks in active projects
        total_task = Task.objects.filter(deleted_at__isnull=True,project__deleted_at__isnull=True, project__institution=institution).count()


        # 3. Average project duration (in days)
        # Only include projects with both start_date and end_date
        duration_data = Project.objects.filter(
            deleted_at__isnull=True,
            institution=institution,
            start_date__isnull=False,
            end_date__isnull=False
        ).aggregate(
            avg_duration=Avg(
                F('end_date') - F('start_date'),  # Returns a timedelta
                output_field=models.DurationField()
            )
        )
        # Convert timedelta to days (round to nearest integer)
        avg_duration = duration_data['avg_duration']
        average_duration = int(avg_duration.total_seconds() // 86400) if avg_duration else 0

        # 4. Employees assigned (distinct CustomUser assigned to TASKS)
        employees_assigned = TaskUserAssignees.objects.filter(
            task__deleted_at__isnull=True,
            task__project__deleted_at__isnull=True,
            task__project__institution=institution
        ).values('user_assigned').distinct().count()

        # 5. Project status overview
        project_status_overview = Project.objects.filter(
            deleted_at__isnull=True,
            institution=institution,
            project_status__isnull=False
        ).values(
            status=F('project_status__status_name')
        ).annotate(count=Count('id')).order_by('-count')

        # 6. Task status overview
        task_overview = Task.objects.filter(
            deleted_at__isnull=True,
            project__deleted_at__isnull=True,
            project__institution=institution,
            applied_project_task_status__isnull=False
        ).values(
            status=F('applied_project_task_status__name')
        ).annotate(count=Count('id')).order_by('-count')

        # 7. Project progress (percentage of completed tasks per project)
        active_projects = Project.objects.filter(
            deleted_at__isnull=True,
            institution=institution
        ).select_related('project_status').order_by('-created_at')[:5]

        project_progress = []
        for project in active_projects:
            total_proj_tasks = project.tasks.filter(deleted_at__isnull=True).count()
            if total_proj_tasks == 0:
                progress = 0
            else:
                # Count completed tasks usin completion_date
                completed_tasks = project.tasks.filter(
                    deleted_at__isnull=True,
                    completion_date__isnull=False
                ).count()
                progress = int((completed_tasks / total_proj_tasks) * 100)

            project_progress.append({
                'project': project.project_name,
                'progress': progress
            })

        # 8. Recent projects (last 5 by created_at)
        recent_projects = Project.objects.filter(
            deleted_at__isnull=True,
            institution=institution
        ).select_related('project_status').order_by('-created_at')[:5]

        recent_projects_data = []
        for proj in recent_projects:
            # Calculate progress
            total_tasks = proj.tasks.filter(deleted_at__isnull=True).count()
            if total_tasks == 0:
                progress = 0
            else:
                completed = proj.tasks.filter(
                    deleted_at__isnull=True,
                    completion_date__isnull=False
                ).count()
                progress = int((completed / total_tasks) * 100)

            recent_projects_data.append({
                'name': proj.project_name,
                'start_date': proj.start_date,
                'end_date': proj.end_date,
                'progress': progress,
                'status': proj.project_status.status_name if proj.project_status else "Unknown"
            })

        # Build final response
        data = {
            "total_projects": total_projects,
            "total_tasks": total_task,
            "average_duration": average_duration,
            "employees_assigned": employees_assigned,
            "project_status_overview": list(project_status_overview),
            "project_progress": project_progress,
            "task_overview": list(task_overview),
            "recent_projects": recent_projects_data,
        }

        serializer = ProjectAnalyticsDashboardSerializer(data)
        return Response(serializer.data)


class TaskAnalyticsDashboardView(APIView):

    @extend_schema(
        summary="Get Task dashboard analytics",
        description=(
            "Returns key task analytic metrics for the authenticated user's institution, "
            "including total tasks, status overviews, task trends over time, and recent tasks."
        ),
        responses=TaskAnalyticsDashboardSerializer,
        tags=["Dashboard Analytics Management"],
    )
    @method_decorator(permission_required('can_view_task_dashboard'))
    def get(self, request):
        institution = getattr(request.user.profile, 'institution', None)
        if not institution:
            return Response(
                {"error": "User has no associated institution."},
                status=status.HTTP_400_BAD_REQUEST
            )

        total_tasks = Task.objects.filter(
            deleted_at__isnull=True
        ).filter(
            Q(project__deleted_at__isnull=True, project__institution=institution)
            | Q(project__isnull=True, task_status__institution=institution)
        ).count()

        # 2. Task status overview
        task_status_overview = (
            Task.objects.filter(
                deleted_at__isnull=True,
                task_status__isnull=False
            )
            .filter(
                Q(project__isnull=True) |  # standalone tasks
                Q(project__deleted_at__isnull=True, project__institution=institution)  # project tasks
            )
            .values(
                status=F('task_status__name')
            )
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        # 3. Task count by month (last 12 months or all time)
        task_over_time = (
            Task.objects.filter(
                deleted_at__isnull=True,
                created_at__isnull=False
            )
            .filter(
                Q(project__isnull=True) |
                Q(project__deleted_at__isnull=True, project__institution=institution)
            )
            .annotate(
                year=ExtractYear('created_at'),
                month=ExtractMonth('created_at')
            )
            .values('year', 'month')
            .annotate(task_count=Count('id'))
            .order_by('year', 'month')
        )

        # 4. Recent tasks (last 5 by creation date)
        recent_tasks_qs = (
            Task.objects.filter(
                deleted_at__isnull=True
            )
            .filter(
                Q(project__isnull=True) |
                Q(project__deleted_at__isnull=True, project__institution=institution)
            )
            .select_related('task_status')
            .order_by('-created_at')[:5]
        )

        recent_tasks = []
        for task in recent_tasks_qs:
            # Calculate progress: 100 if completed, 0 otherwise
            if task.completion_date:
                progress = 100
            else:
                progress = 0

            recent_tasks.append({
                'name': task.task_name,
                'start_date': task.start_date,
                'end_date': task.end_date,
                'progress': progress,
                'status': task.task_status.name if task.task_status else "Unknown"
            })

        # Build final response data
        data = {
            "total_tasks": total_tasks,
            "task_status_overview": list(task_status_overview),
            "task_over_time": list(task_over_time),
            "recent_tasks": recent_tasks,
        }

        serializer = TaskAnalyticsDashboardSerializer(data)
        return Response(serializer.data)


class ProjectUsersApiView(APIView):
   
    @extend_schema(
        responses={200: ProjectUsersReadSerializer},
        description="Retrieve users that belong to the project (directly or via staff groups)",
        summary="Get all users associated with a project.",
        tags=["Project Management"],
    )
    def get(self, request, pk):
        project = get_object_or_404(
            Project.objects.prefetch_related(
                'user_assignees__user_assigned',
                Prefetch(
                    'staff_group_assignees__group_assigned',
                    queryset=StaffGroup.objects.prefetch_related('users')
                ),
            ),
            id=pk
        )

        user_ids = set()

        # Direct assignees
        user_ids.update(
            project.user_assignees.values_list('user_assigned_id', flat=True)
        )

        # Staff group members
        for group_assignee in project.staff_group_assignees.all():
            user_ids.update(
                group_assignee.group_assigned.users.values_list('id', flat=True)
            )

        # Optional: include project manager
        if project.user_manager_id:
            user_ids.add(project.user_manager_id)

        users = CustomUser.objects.filter(id__in=user_ids)
        user_data = UserProjectSerializer(users, many=True).data

        return Response({
            "project_id": pk,
            "users": user_data,
            "total_users": len(user_data),
        }, status=status.HTTP_200_OK)


class TaskMessageListCreateApiView(APIView):
    permission_classes = [IsAuthenticated]
    allowed_ordering_fields = ['content', 'created_at']
    default_ordering = ['-created_at']
    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=TaskMessageSerializer(many=True),
                description="List of task messages.",
            ),
            400: OpenApiResponse(description="Invalid ordering field."),
            404: OpenApiResponse(description="Institution not found."),
        },
        tags=["Project Thread Management"],
    )
    def get(self, request):
        user = request.user.profile
        task_id = request.query_params.get("task", None)
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        task_messages = TaskMessage.objects.filter(
            institution=institution, deleted_at__isnull=True
        )

        if task_id:
            task_messages = task_messages.filter(task_id=task_id)


        paginator = CustomPageNumberPagination()
        paginated_qs = paginator.paginate_queryset(task_messages, request)
        serializer = TaskMessageSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)



    @extend_schema(
        request=TaskMessageSerializer,
        responses={
            201: OpenApiResponse(
                response=TaskMessageSerializer,
                description="Task Message created successfully.",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors.",
            ),
        },
        tags=["Project Thread Management"],
    )
    def post(self, request):
        # Get user's institution
        try:
            user_institution = request.user.profile.institution
        except (Institution.DoesNotExist, AttributeError):
            return Response(
                {"error": "Institution not found for user."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = TaskMessageSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        task = serializer.validated_data['task']

        try:
            task_institution = task.user_manager.profile.institution
        except (AttributeError, Institution.DoesNotExist):
            return Response(
                {"error": "Task institution could not be determined."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        if user_institution != task_institution:
            return Response(
                {"error": "User's institution does not match the task instituion"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user
        is_creator = (task.created_by_id == user.id)
        is_manager = (task.user_manager_id == user.id)
        is_assignee = task.user_assignees.filter(user_assigned=user).exists()
        is_institution_owner = (
            hasattr(user_institution, 'institution_owner') and
            user_institution.institution_owner == user
        )
        is_discussion_participant = TaskDiscussionParticipant.objects.filter(
            task=task,
            user=user,
            can_send=True
        ).exists()
        has_project_send_permission = user.has_permission("can_send_task_messages")
        if not (
            is_creator
            or is_manager
            or is_assignee
            or is_institution_owner
            or is_discussion_participant
            or has_project_send_permission
        ):
            print(f"User: {user} should not be able to send message to task {task}")
            return Response(
                {"error": "You do not have permission send messages to this task discussion."},
                status=status.HTTP_403_FORBIDDEN
            )

        instance = serializer.save()
        instance.confirm_create()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class TaskMessageDetailApiView(APIView):
    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=TaskMessageSerializer,
                description="Task message details.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Task message  not found.",
            ),
        },
        tags=["Project Thread Management"],
    )
    def get(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        task_message = get_object_or_404(TaskMessage, pk=pk, institution=institution, deleted_at__isnull=True)
        serializer = TaskMessageSerializer(task_message)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Task message marked for deletion and sent for approval.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Task message priority not found.",
            ),
        },
        tags=["Project Thread Management"],
    )
    def delete(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        task_message = get_object_or_404(TaskMessage, pk=pk, institution=institution, deleted_at__isnull=True)
        task_message.approval_status = 'under_deletion'
        task_message.save(update_fields=['approval_status'])
        task_message.confirm_delete()
        return Response(
            {"message": "Task message submitted for deletion approval."},
            status=status.HTTP_200_OK
        )

    @extend_schema(
        request=TaskMessageSerializer,
        responses={
            200: OpenApiResponse(
                response=TaskMessageSerializer,
                description="Task message updated successfully.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Task message  not found.",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors.",
            ),
        },
        tags=["Project Thread Management"],
    )
    def patch(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        task_message = get_object_or_404(TaskMessage, pk=pk, institution=institution, deleted_at__isnull=True)
        task_message.approval_status = 'under_update'
        task_message.save(update_fields=['approval_status'])
        serializer = TaskMessageSerializer(task_message, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            instance = serializer.save()
            instance.confirm_update()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class ProjectMessageListCreateApiView(APIView):
    permission_classes = [IsAuthenticated]
    allowed_ordering_fields = ['content', 'created_at']
    default_ordering = ['-created_at']
    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=ProjectMessageSerializer(many=True),
                description="List of project messages.",
            ),
            400: OpenApiResponse(description="Invalid ordering field."),
            404: OpenApiResponse(description="Institution not found."),
        },
        tags=["Project Thread Management"],
    )
    def get(self, request):
        user = request.user.profile
        project_id = request.query_params.get("project", None)
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        project_messages = ProjectMessage.objects.filter(
            institution=institution, deleted_at__isnull=True
        )

        if project_id:
            project_messages = project_messages.filter(project_id=project_id)


        paginator = CustomPageNumberPagination()
        paginated_qs = paginator.paginate_queryset(project_messages, request)
        serializer = ProjectMessageSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)



    @extend_schema(
        request=ProjectMessageSerializer,
        responses={
            201: OpenApiResponse(
                response=ProjectMessageSerializer,
                description="Project Message created successfully.",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors.",
            ),
        },
        tags=["Project Thread Management"],
    )
    def post(self, request):
    # Get user's institution (same as in get())
        try:
            user_institution = request.user.profile.institution
        except (Institution.DoesNotExist, AttributeError):
            return Response(
                {"error": "Institution not found for user."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ProjectMessageSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        project = serializer.validated_data['project']

        if user_institution != project.institution:
            return Response(
                {"error": "User's institution does not match the project instituion"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user
        is_creator = (project.created_by_id == user.id)
        is_manager = (project.user_manager_id == user.id)
        is_assignee = project.user_assignees.filter(user_assigned=user).exists()
        is_institution_owner = (
            hasattr(user_institution, 'institution_owner') and
            user_institution.institution_owner == user
        )
        is_discussion_participant = ProjectDiscussionParticipant.objects.filter(
            project=project,
            user=user,
            can_send=True
        ).exists()
        has_project_send_permission = user.has_permission("can_send_project_messages")
        if not (
            is_creator
            or is_manager
            or is_assignee
            or is_institution_owner
            or is_discussion_participant
            or has_project_send_permission
        ):
            return Response(
                {"error": "You do not have permission to send messages to this project discussion."},
                status=status.HTTP_403_FORBIDDEN
            )

        instance = serializer.save()
        instance.confirm_create()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProjectMessageDetailApiView(APIView):
    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=ProjectMessageSerializer,
                description="Project message details.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Project message  not found.",
            ),
        },
        tags=["Project Thread Management"],
    )
    def get(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        project_message = get_object_or_404(ProjectMessage, pk=pk, institution=institution, deleted_at__isnull=True)
        serializer = ProjectMessageSerializer(project_message)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Project message marked for deletion and sent for approval.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Project message priority not found.",
            ),
        },
        tags=["Project Thread Management"],
    )
    def delete(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        project_message = get_object_or_404(ProjectMessage, pk=pk, institution=institution, deleted_at__isnull=True)
        project_message.approval_status = 'under_deletion'
        project_message.save(update_fields=['approval_status'])
        project_message.confirm_delete()
        return Response(
            {"message": "Project message submitted for deletion approval."},
            status=status.HTTP_200_OK
        )

    @extend_schema(
        request=ProjectMessageSerializer,
        responses={
            200: OpenApiResponse(
                response=ProjectMessageSerializer,
                description="Project message updated successfully.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Project message  not found.",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors.",
            ),
        },
        tags=["Project Thread Management"],
    )
    def patch(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        project_message = get_object_or_404(ProjectMessage, pk=pk, institution=institution, deleted_at__isnull=True)
        project_message.approval_status = 'under_update'
        project_message.save(update_fields=['approval_status'])
        serializer = ProjectMessageSerializer(project_message, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            instance = serializer.save()
            instance.confirm_update()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskExtensionRequestListCreateView(APIView):

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=TaskExtensionRequestSerializer(many=True),
                description="List of task extension requests.",
            ),
            400: OpenApiResponse(description="Invalid ordering field."),
            404: OpenApiResponse(description="Institution not found."),
        },
        tags=["Project Task Extension Management"],
    )
    def get(self, request):
        user = request.user.profile
        task_id = request.query_params.get("task", None)
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        tasks_extensions = TaskExtensionRequest.objects.filter(
            institution=institution,
            deleted_at__isnull=True,
            approved=False,
            accepted=False
        ).order_by('-created_at')

        if task_id:
            tasks_extensions = tasks_extensions.filter(task_id=task_id)

        paginator = CustomPageNumberPagination()
        paginated_qs = paginator.paginate_queryset(tasks_extensions, request)
        serializer = TaskExtensionRequestSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)


    @extend_schema(
        request=TaskExtensionRequestSerializer,
        responses={
            201: OpenApiResponse(
                response=TaskExtensionRequestSerializer,
                description="Task extension created successfully.",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors.",
            ),
        },
        tags=["Project Task Extension Management"],
    )
    def post(self, request):
        serializer = TaskExtensionRequestSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        instance = serializer.save()
        instance.confirm_create()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class TaskExtensionRequestDetail(APIView):

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=TaskExtensionRequestSerializer,
                description="Task extension request details.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="TAsk extension request  not found.",
            ),
        },
        tags=["Project Task Extension Management"],
    )
    def get(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        task_extension = get_object_or_404(TaskExtensionRequest, pk=pk, institution=institution, deleted_at__isnull=True)
        serializer = TaskExtensionRequestSerializer(task_extension)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Task extension request marked for deletion and sent for approval.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Institution not found.",
            ),
        },
        tags=["Project Task Extension Management"],
    )
    def delete(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        task_extension_request = get_object_or_404(TaskExtensionRequest, pk=pk, institution=institution, deleted_at__isnull=True)
        task_extension_request.approval_status = 'under_deletion'
        task_extension_request.save(update_fields=['approval_status'])
        task_extension_request.confirm_delete()
        return Response(
            {"message": "Task extension request submitted for deletion approval."},
            status=status.HTTP_200_OK
        )


    @extend_schema(
        request=TaskExtensionRequestSerializer,
        responses={
            200: OpenApiResponse(
                response=TaskExtensionRequestSerializer,
                description="Task Extension request updated successfully.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Task Extension request  not found.",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors.",
            ),
        },
        tags=["Project Task Extension Management"],
    )
    def patch(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        task_extension_request = get_object_or_404(TaskExtensionRequest, pk=pk, institution=institution, deleted_at__isnull=True)
        task_extension_request.approval_status = 'under_update'
        task_extension_request.save(update_fields=['approval_status'])
        serializer = TaskExtensionRequestSerializer(task_extension_request, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            instance = serializer.save()
            instance.confirm_update()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskExtensionRequestApprove(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=TaskExtensionApprovalReason,
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Task Extension request accepted successfully.",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={"message": "Task extended successfully"},
                        response_only=True,
                    )
                ],
            ),
            400: OpenApiResponse(description="Bad request (e.g., invalid data)."),
            403: OpenApiResponse(description="Permission denied."),
            404: OpenApiResponse(description="Task Extension request not found."),
        },
        tags=["Project Task Extension Management"],
    )
    def post(self, request):
        serializer = TaskExtensionApprovalReason(data=request.data)
        serializer.is_valid(raise_exception=True)

        extension_request = serializer.validated_data["task_extension_request"]
        approval_reason = serializer.validated_data["approval_reason"]
        task = extension_request.task
        user_profile = request.user.profile
        institution = user_profile.institution

        all_assignees = [a.user_assigned for a in task.user_assignees.all()]
        user_manager = task.user_manager
        all_users = all_assignees + [user_manager]

        is_creator = (task.created_by and task.created_by.id == request.user.id)
        is_institution_owner = (institution.institution_owner == request.user)
        has_permission = request.user.has_permission("can_approve_extension_request")
        is_part_of_task = request.user in all_users

        if not (
            is_creator
            or is_institution_owner
            or (has_permission and not is_part_of_task)
        ):
            return Response(
                {"error": "You do not have permission to approve this request."},
                status=status.HTTP_403_FORBIDDEN
            )


        extension_request.approval_status = 'under_update'

        if extension_request.new_start_date:
            task.start_date = extension_request.new_start_date
        if extension_request.new_end_date:
            task.end_date = extension_request.new_end_date
        task.save(update_fields=["start_date", "end_date", "approval_status"])
        
        extension_request.approved = True
        extension_request.accepted = True
        extension_request.approval_reason = approval_reason
        extension_request.save(update_fields=["approved", "accepted", "approval_reason", ])
        extension_request.confirm_update()
        return Response({"message": "Task extended successfully"}, status=status.HTTP_200_OK)


class TaskExtensionRequestReject(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=TaskExtensionApprovalReason,
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Task Extension request rejected successfully.",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={"message": "Extension request rejected"},
                        response_only=True,
                    )
                ],
            ),
            400: OpenApiResponse(description="Bad request (e.g., invalid data)."),
            403: OpenApiResponse(description="Permission denied."),
            404: OpenApiResponse(description="Task Extension request not found."),
        },
        tags=["Project Task Extension Management"],
    )
    def post(self, request):
        serializer = TaskExtensionApprovalReason(data=request.data)
        serializer.is_valid(raise_exception=True)

        extension_request = serializer.validated_data["task_extension_request"]
        approval_reason = serializer.validated_data["approval_reason"]
        task = extension_request.task
        user_profile = request.user.profile

        if task.created_by != user_profile:
            return Response(
                {"error": "You do not have permission to reject this request."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        extension_request.approval_status = 'under_update'
        extension_request.save(update_fields=["approval_status"])

        extension_request.approved = True
        extension_request.accepted = False
        extension_request.approval_reason = approval_reason
        extension_request.save(update_fields=["approved", "accepted", "approval_reason"])
        extension_request.confirm_update()

        # Experimental feature for email notification on rejection or acceptance

        # task_leader = task.user_manager
        # task_assignee_objects = task.user_assignees.all()

        # task_url = ""
        # task_assignee_ids = []
        # for task_assignee in task_assignee_objects:
        #     print(f"Task assignees: {task_assignee.user_assigned.id}")
        #     task_assignee_ids.append(task_assignee.user_assigned.id)

        # send_project_or_task_email.delay_on_commit(
        #     [task_leader.id],
        #     list(task_assignee_ids),
        #     url=task_url,
        #     task_id=task.id,
        #     is_update=False,
        # )

        return Response({"message": "Extension request rejected"}, status=status.HTTP_200_OK)


class ProjectTaskStatusDefaultsView(APIView):
    extend_schema(
        summary="Get default project statuses",
        description="Returns the canonical list of project statuses: todo, ongoing, onhold, completed, failed.",
        responses={200: DefaultProjectTaskStatusSerializer(many=True)},
        tags=["Default Project Task Statuses"],
    )
    def get(self, request, *args, **kwargs):
        json_path = os.path.join(settings.BASE_DIR, 'users', 'fixtures', 'project_task_statuses.json')

        try:
            with open(json_path, 'r') as file:
                data = json.load(file)

            # Validate and serialize the data
            serializer = DefaultProjectTaskStatusSerializer(data=data['statuses'], many=True)

            if serializer.is_valid():
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"error": "Invalid status data format"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except FileNotFoundError:
            return Response(
                {"error": "Status configuration file not found"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except json.JSONDecodeError:
            return Response(
                {"error": "Invalid JSON format in status configuration file"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            return Response(
                {"error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Configure default completed and failed statuses",
        description="Set the default status IDs to be used for marking tasks as completed or failed.",
        request=DefaultStatusConfigSerializer,
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Project Defaults set successfully..",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={"message": "Project Defaults set successfully."},
                        response_only=True,
                    )
                ],
            ),
            400: OpenApiResponse(description="Bad request (e.g., invalid data)."),
            403: OpenApiResponse(description="Permission denied."),
            404: OpenApiResponse(description="Project  not found."),
        },
        tags=["Default Project Task Statuses"],
    )
    def post(self, request):
        serializer = DefaultStatusConfigSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        completed_id = serializer.validated_data['completed_status']
        failed_id = serializer.validated_data['failed_status']
        project_id = serializer.validated_data['project']

        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        project = get_object_or_404(Project, pk=project_id, institution=institution, deleted_at__isnull=True)
        completed_status = get_object_or_404(ProjectTaskStatus, pk=completed_id, project=project, deleted_at__isnull=True)
        failed_status = get_object_or_404(ProjectTaskStatus, pk=failed_id, project=project, deleted_at__isnull=True)

        # Set project completed and failed statuses
        project.approval_status = 'under_update'
        project.save(update_fields=["approval_status"])

        project.completed_status = completed_status
        project.failed_status = failed_status

        project.save(update_fields=["completed_status", "failed_status"])
        project.confirm_update()
        return Response({"message": "Project Defaults set successfully."}, status=status.HTTP_200_OK)



class ProjectTaskStatusListView(APIView):
    @extend_schema(
        summary="Get project task statuses",
        description="Returns the list of project task statuses defined for the user's institution.",
        responses={200: ProjectTaskStatusSerializer(many=True)},
        tags=["Project Task Statuses"],
    )
    def get(self, request):
        project_id = request.query_params.get("project", None)

        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        project_task_statuses = ProjectTaskStatus.objects.filter(
            project__institution=institution,
            deleted_at__isnull=True
        )

        if project_id:
            project_task_statuses = project_task_statuses.filter(project=project_id)

        paginator = CustomPageNumberPagination()
        paginated_qs = paginator.paginate_queryset(project_task_statuses, request)
        serializer = ProjectTaskStatusSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        request=ProjectTaskStatusSerializer,
        responses={
            201: OpenApiResponse(
                response=ProjectTaskStatusSerializer,
                description="Task status created successfully.",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors.",
            ),
        },
        tags=["Project Task Statuses"],
    )
    @method_decorator(permission_required('can_create_task_statuses'))
    @transaction.atomic()
    def post(self, request):
        serializer = ProjectTaskStatusSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            instance = serializer.save()
            instance.confirm_create()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProjectTaskStatusDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=ProjectTaskStatusSerializer,
                description="Task status details.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Task status not found.",
            ),
        },
        tags=["Project Task Statuses"],
    )
    @method_decorator(permission_required('can_view_task_statuses'))
    def get(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        status_obj = get_object_or_404(ProjectTaskStatus, pk=pk, deleted_at__isnull=True)
        serializer = ProjectTaskStatusSerializer(status_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Task status marked for deletion and sent for approval.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Task status not found.",
            ),
        },
        tags=["Project Task Statuses"],
    )
    @method_decorator(permission_required('can_delete_task_statuses'))
    @transaction.atomic()
    def delete(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        status_obj = get_object_or_404(ProjectTaskStatus, pk=pk, deleted_at__isnull=True)
        status_obj.approval_status = 'under_deletion'
        status_obj.save(update_fields=['approval_status'])
        status_obj.confirm_delete()
        return Response(
            {"message": "Task status submitted for deletion approval."},
            status=status.HTTP_200_OK
        )


    @extend_schema(
        request=ProjectTaskStatusSerializer,
        responses={
            200: OpenApiResponse(
                response=ProjectTaskStatusSerializer,
                description="Task status updated successfully.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Task status not found.",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors.",
            ),
        },
        tags=["Project Task Statuses"],
    )
    @method_decorator(permission_required('can_edit_task_statuses'))
    @transaction.atomic()
    def patch(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        status_obj = get_object_or_404(ProjectTaskStatus, pk=pk, deleted_at__isnull=True)
        status_obj.approval_status = 'under_update'
        status_obj.save(update_fields=['approval_status'])
        serializer = ProjectTaskStatusSerializer(status_obj, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            instance = serializer.save()
            instance.confirm_update()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProjectDiscussionParticipantListCreateApiView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=ProjectDiscussionParticipantSerializer(many=True),
                description="List of project discussion participant.",
            ),
            404: OpenApiResponse(description="Institution not found."),
        },
        tags=["Project Discussion Participant Management"],
    )
    def get(self, request):
        user = request.user.profile

        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        project_discussion_participants = ProjectDiscussionParticipant.objects.filter(
            project__institution=institution, deleted_at__isnull=True
        )
        paginator = CustomPageNumberPagination()
        paginated_qs = paginator.paginate_queryset(project_discussion_participants, request)
        serializer = ProjectDiscussionParticipantSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        request=ProjectDiscussionParticipantSerializer,
        responses={
            201: OpenApiResponse(
                response=ProjectDiscussionParticipantSerializer,
                description="Project Discussion Participant created successfully.",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors.",
            ),
        },
        tags=["Project Discussion Participant Management"],
    )
    @transaction.atomic()
    def post(self, request):
        serializer = ProjectDiscussionParticipantSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            instance = serializer.save()
            # instance.confirm_create()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProjectDisscusionParticipantDetailsApiView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=ProjectDiscussionParticipantSerializer,
                description="Project discussion participant details.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Project discussion participant not found.",
            ),
        },
        tags=["Project Discussion Participant Management"],
    )
    def get(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        project_discussion_participant = get_object_or_404(ProjectDiscussionParticipant, pk=pk, project__institution=institution, deleted_at__isnull=True)
        serializer = ProjectDiscussionParticipantSerializer(project_discussion_participant)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Project Discussion Participant marked for deletion and sent for approval.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Project Discussion Participant",
            ),
        },
        tags=["Project Discussion Participant Management"],
    )
    @transaction.atomic()
    def delete(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        project_discussion_participant = get_object_or_404(ProjectDiscussionParticipant, pk=pk, project__institution=institution, deleted_at__isnull=True)
        project_discussion_participant.approval_status = 'under_deletion'
        project_discussion_participant.save(update_fields=['approval_status'])
        project_discussion_participant.confirm_delete()
        return Response(
            {"message": "Project Discussion Particaipant submitted for deletion approval."},
            status=status.HTTP_200_OK
        )


    @extend_schema(
        request=ProjectDiscussionParticipantSerializer,
        responses={
            200: OpenApiResponse(
                response=ProjectDiscussionParticipantSerializer,
                description="Project Discussion Participant updated successfully.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Project Discussion Participant not found.",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors.",
            ),
        },
        tags=["Project Discussion Participant Management"],
    )
    @transaction.atomic()
    def patch(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        project_discussion_participant = get_object_or_404(ProjectDiscussionParticipant, pk=pk, project__institution=institution, deleted_at__isnull=True)
        project_discussion_participant.approval_status = 'under_update'
        project_discussion_participant.save(update_fields=['approval_status'])
        serializer = ProjectDiscussionParticipantSerializer(project_discussion_participant, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            instance = serializer.save()
            instance.confirm_update()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class TaskDisscusionParticipantListCreateApiView(APIView):

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=TaskDiscussionParticipantSerializer(many=True),
                description="List of task discussion participant.",
            ),
            404: OpenApiResponse(description="Institution not found."),
        },
        tags=["Project Discussion Participant Management"],
    )
    def get(self, request):
        user = request.user.profile

        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        task_discussion_participants = TaskDiscussionParticipant.objects.filter(
            task__user_manager__profile__institution=institution, deleted_at__isnull=True
        )
        paginator = CustomPageNumberPagination()
        paginated_qs = paginator.paginate_queryset(task_discussion_participants, request)
        serializer = TaskDiscussionParticipantSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        request=TaskDiscussionParticipantSerializer,
        responses={
            201: OpenApiResponse(
                response=TaskDiscussionParticipantSerializer,
                description="Task Discussion Participant created successfully.",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors.",
            ),
        },
        tags=["Project Discussion Participant Management"],
    )
    @transaction.atomic()
    def post(self, request):
        serializer = TaskDiscussionParticipantSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            instance = serializer.save()
            instance.confirm_create()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class TasskDisscusionParticipantDetailsApiView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=TaskDiscussionParticipantSerializer,
                description="Task discussion participant details.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Task discussion participant not found.",
            ),
        },
        tags=["Project Discussion Participant Management"],
    )
    def get(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        task_discussion_participant = get_object_or_404(TaskDiscussionParticipant, pk=pk, task__user_manager__profile__institution=institution, deleted_at__isnull=True)
        serializer = TaskDiscussionParticipantSerializer(task_discussion_participant)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Task Discussion Participant marked for deletion and sent for approval.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Task Discussion Participant",
            ),
        },
        tags=["Project Discussion Participant Management"],
    )
    @transaction.atomic()
    def delete(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        task_discussion_participant = get_object_or_404(TaskDiscussionParticipant, pk=pk, task__user_manager__profile__institution=institution, deleted_at__isnull=True)
        task_discussion_participant.approval_status = 'under_deletion'
        task_discussion_participant.save(update_fields=['approval_status'])
        task_discussion_participant.confirm_delete()
        return Response(
            {"message": "Task Discussion Particaipant submitted for deletion approval."},
            status=status.HTTP_200_OK
        )


    @extend_schema(
        request=TaskDiscussionParticipantSerializer,
        responses={
            200: OpenApiResponse(
                response=TaskDiscussionParticipantSerializer,
                description="Task Discussion Participant updated successfully.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Task Discussion Participant not found.",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors.",
            ),
        },
        tags=["Project Discussion Participant Management"],
    )
    @transaction.atomic()
    def patch(self, request, pk):
        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        task_discussion_participant = get_object_or_404(TaskDiscussionParticipant, pk=pk, task__user_manager__profile__institution=institution, deleted_at__isnull=True)
        task_discussion_participant.approval_status = 'under_update'
        task_discussion_participant.save(update_fields=['approval_status'])
        serializer = TaskDiscussionParticipantSerializer(task_discussion_participant, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            instance = serializer.save()
            instance.confirm_update()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class ProjectTaskEmailConfigListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=ProjectTaskEmailConfigSerializer(many=True),
        responses={
            201: OpenApiResponse(
                response=ProjectTaskEmailConfigSerializer(many=True),
                description="Task Email configs created successfully."
            ),
            400: OpenApiResponse(description="Bad request, validation errors."),
        },
        tags=["Project Task Email Config"],
    )
    @transaction.atomic
    def post(self, request):
        # Expect a list of objects
        if not isinstance(request.data, list):
            return Response(
                {"error": "Expected a list of task email configurations."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ProjectTaskEmailConfigSerializer(
            data=request.data,
            many=True,
            context={"request": request}
        )

        if serializer.is_valid():
            try:
                instances = serializer.save()
                return Response(
                    ProjectTaskEmailConfigSerializer(instances, many=True).data,
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response(
                    {"error": f"Failed to create task email configs: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        parameters=[
            {"name": "task", "type": "int", "description": "Filter by task ID"},
            {"name": "intent", "type": "str", "description": "Filter by intent (e.g., 'failure', 'completion')"},
            {"name": "ordering", "type": "str", "description": "Order by fields like 'intent' or '-created_at'"},
        ],
        responses={
            200: OpenApiResponse(
                response=ProjectTaskEmailConfigSerializer(many=True),
                description="List of Task Email configs."
            ),
            404: OpenApiResponse(description="Institution not found."),
        },
        tags=["Project Task Email Config"],
    )
    def get(self, request):
        user = request.user
        try:
            profile = user.profile
            institution = profile.institution
            if not institution:
                return Response({"error": "Institution not found for user."}, status=status.HTTP_404_NOT_FOUND)
        except AttributeError:
            return Response({"error": "User profile or institution missing."}, status=status.HTTP_404_NOT_FOUND)

        queryset = ProjectTaskEmailConfig.objects.filter(
            deleted_at__isnull=True
        )

        # Filtering
        task_id = request.query_params.get("task")
        intent = request.query_params.get("intent")

        if task_id and task_id.isdigit():
            queryset = queryset.filter(task_id=task_id)
        if intent:
            if intent in dict(ProjectTaskEmailConfig.Intent.choices):
                queryset = queryset.filter(intent=intent)
            else:
                return Response({"error": "Invalid intent value."}, status=status.HTTP_400_BAD_REQUEST)

        # Pagination
        paginator = CustomPageNumberPagination()
        paginated_qs = paginator.paginate_queryset(queryset, request)
        serializer = ProjectTaskEmailConfigSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)


class ProjectTaskEmailConfigDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(response=ProjectTaskEmailConfigSerializer, description="Task Email config details."),
            404: OpenApiResponse(description="Task Email config not found."),
        },
        tags=["Project Task Email Config"],
    )
    def get(self, request, pk):
        task_email_config = get_object_or_404(ProjectTaskEmailConfig, pk=pk, deleted_at__isnull=True)
        serializer = ProjectTaskEmailConfigSerializer(task_email_config)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Task Email config marked for deletion and sent for approval."),
            404: OpenApiResponse(description="Task Email config not found."),
        },
        tags=["Project Task Email Config"],
    )
    @transaction.atomic
    def delete(self, request, pk):
        task_email_config = get_object_or_404(ProjectTaskEmailConfig, pk=pk, deleted_at__isnull=True)
        task_email_config.approval_status = 'under_deletion'
        task_email_config.save(update_fields=['approval_status'])
        task_email_config.confirm_delete()
        return Response(
            {"message": "Task Email config submitted for deletion approval."},
            status=status.HTTP_200_OK
        )

    @extend_schema(
        request=ProjectTaskEmailConfigSerializer,
        responses={
            200: OpenApiResponse(response=ProjectTaskEmailConfigSerializer, description="Task Email config updated successfully."),
            400: OpenApiResponse(description="Bad request, validation errors."),
            404: OpenApiResponse(description="Task Email config not found."),
        },
        tags=["Project Task Email Config"],
    )
    @transaction.atomic
    def patch(self, request, pk):
        task_email_config = get_object_or_404(ProjectTaskEmailConfig, pk=pk, deleted_at__isnull=True)
        # Set approval status before validation (as per your workflow)
        task_email_config.approval_status = 'under_update'
        task_email_config.save(update_fields=['approval_status'])

        serializer = ProjectTaskEmailConfigSerializer(
            task_email_config,
            data=request.data,
            context={"request": request},
            partial=True
        )
        if serializer.is_valid():
            updated_instance = serializer.save()
            updated_instance.confirm_update()
            return Response(ProjectTaskEmailConfigSerializer(updated_instance).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProjectTaskProgressStatus(APIView, SortableAPIMixin):
    @extend_schema(
    parameters=[
        {
            "name": "project",
            "type": "int",
            "description": "Filter tasks by project ID.",
            "required": False,
        },
        {
            "name": "progress_status",
            "type": "str",
            "description": "Filter tasks by progress state. Valid values: 'completed', 'failed'.",
            "required": False,
        },
        {
            "name": "ordering",
            "type": "str",
            "description": "Comma-separated field names to sort by (e.g., 'created_at' or '-task_name').",
            "required": False,
        },
    ],
    responses={
        200: OpenApiResponse(
            response=TaskSerializer(many=True),
            description="Paginated list of tasks matching the filters.",
        ),
        400: OpenApiResponse(description="Invalid ordering field or parameter."),
        404: OpenApiResponse(description="Institution not found for the authenticated user."),
    },
    tags=["Project Task Statuses"],
    )
    @method_decorator(permission_required('can_view_all_tasks'))
    def get(self, request):
        user = request.user.profile
        project_id = request.query_params.get("project", None)
        progress_status = request.query_params.get("progress_status", None)

        try:
            institution = user.institution
            if institution is None:
                raise Institution.DoesNotExist
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        tasks = Task.objects.filter(
            user_manager__profile__institution=institution,
            deleted_at__isnull=True
        )

        if project_id:
            tasks = tasks.filter(project_id=project_id)

        # Filter by progress_status if specified
        if progress_status in ['completed', 'failed']:
            filtered_tasks = []
            for task in tasks:
                project = task.project

                if progress_status == 'completed':
                    if project.completed_status is not None and \
                    task.applied_project_task_status == project.completed_status:
                        filtered_tasks.append(task)

                elif progress_status == 'failed':
                    if project.failed_status is not None and \
                    task.applied_project_task_status == project.failed_status:
                        filtered_tasks.append(task)

            tasks = filtered_tasks

        if isinstance(tasks, models.QuerySet):
            try:
                tasks = self.apply_sorting(tasks, request)
            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        paginator = CustomPageNumberPagination()
        paginated_qs = paginator.paginate_queryset(tasks, request)
        serializer = TaskSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)