from django.shortcuts import render
from .models import (
    StandaloneTask,
    StandaloneTaskTimeSheet,
    StandaloneTaskPriority,
    StandaloneTaskStatus,
    StandaloneTaskMessage,
    StandaloneTaskExtensionRequest,
    StandaloneTaskDiscussionParticipant,
    StandaloneTaskEmailConfig,
)
from .serializers import (
    StandaloneTaskTimeSheetSerializer,
    StandaloneTaskSerializer,
    StandaloneTaskPrioritySerializer,
    StandaloneTaskStatusSerializer,
    StandaloneTaskMessageSerializer,
    StandaloneTaskExtensionRequestSerializer,
    StandaloneTaskExtensionApprovalReason,
    StandaloneTaskDiscussionParticipantSerializer,
    DefaultTaskStatusConfigSerializer,
    StandaloneTaskEmailConfigSerializer,
)
from rest_framework.views import APIView, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from institution.models import Institution
from utilities.pagination import CustomPageNumberPagination
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse, OpenApiTypes
from django.db.models import Q
from django.db import transaction
from utilities.sortable_api import SortableAPIMixin
from django.utils import timezone
from utilities.helpers import  to_datetime
from django.conf import settings
from django.db import models
from .helpers import send_email_for_task_status_change
from .task import send_project_or_task_email
from utilities.helpers import permission_required
from django.utils.decorators import method_decorator
from django.db.models import Case, When, BooleanField, Q
from django.utils.dateparse import parse_datetime
import json
import os



class StandaloneTaskListCreateView(APIView, SortableAPIMixin):
    permission_classes = [IsAuthenticated]
    allowed_ordering_fields = ['task_name', 'created_at', 'task_status__weight','start_date', 'end_date']
    default_ordering = ['-created_at']

    @extend_schema(
        parameters=[
            {"name": "search", "type": "str", "description": "Search by task name or description"},
            {"name": "created_at", "type": "date", "description": "Filter by creation date"},
            {"name": "task_status", "type": "int", "description": "Filter by task status ID"},
            {"name": "priority", "type": "int", "description": "Filter by priority ID"},
            {"name": "approval_status", "type": "str", "description": "Filter by approval status (pending/approved/rejected)"},
            {"name": "ordering", "type": "str", "description": "Sort by fields (e.g., 'task_name,-created_at')"},
        ],
        responses={
            200: OpenApiResponse(
                response=StandaloneTaskSerializer(many=True),
                description="List of tasks.",
            ),
            400: OpenApiResponse(description="Invalid ordering field."),
            404: OpenApiResponse(description="Institution not found."),
        },
        tags=["Standalone Task Management"],
    )
    @method_decorator(permission_required('can_view_all_tasks'))
    def get(self, request):
        user = request.user.profile
        search_query = request.query_params.get("search", None)
        created_at = request.query_params.get("created_at", None)
        task_status_id = request.query_params.get("task_status", None)
        priority_id = request.query_params.get("priority", None)
        approval_status = request.query_params.get("approval_status", None)
        user_id = request.query_params.get("user", None)
        progress_status = request.query_params.get("progress_status", None)

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

        tasks = StandaloneTask.objects.filter(
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
        serializer = StandaloneTaskSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        request=StandaloneTaskSerializer,
        responses={
            201: OpenApiResponse(
                response=StandaloneTaskSerializer,
                description="Task created successfully.",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors.",
            ),
            404: OpenApiResponse(description="Institution not found."),
        },
        tags=["Standalone Task Management"],
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

        task_serializer = StandaloneTaskSerializer(data=request.data, context={"request": request})
        task_serializer.is_valid(raise_exception=True)
        instance = task_serializer.save()
        instance.confirm_create()

        raw_statuses = request.data.get("task_statuses", [])
        if isinstance(raw_statuses, str):
            try:
                raw_statuses = json.loads(raw_statuses)
            except json.JSONDecodeError:
                return Response({"error": "Invalid JSON in task_statuses."}, status=400)

        if not isinstance(raw_statuses, list):
            return Response({"error": "task_statuses must be a list."}, status=400)

        # Validate that only one status has is_current=true
        current_status_count = 0
        for status_data in raw_statuses:
            if not isinstance(status_data, dict):
                return Response(
                    {"error": f"Each task status must be a dictionary, got {type(status_data).__name__}"},
                    status=400,
                )
            if status_data.get('is_current', False):
                current_status_count += 1
        
        if current_status_count > 1:
            return Response(
                {"error": "Only one task status can have is_current set to true."},
                status=400
            )

        created_statuses = []
        current_status = None

        for status_data in raw_statuses:
            # Extract is_current before cleaning
            is_current = status_data.get('is_current', False)
            
            # Remove is_current 
            status_data_clean = {k: v for k, v in status_data.items() if k != 'is_current'}

            status_serializer = StandaloneTaskStatusSerializer(
                data=status_data_clean,
                context={"request": request, "task": instance}  
            )
            status_serializer.is_valid(raise_exception=True)
            created_status = status_serializer.save()
            created_statuses.append(created_status)

            # Track the first (and only) current status
            if is_current and current_status is None:
                current_status = created_status

        # Apply current status or fallback to lowest weight
        applied_status = current_status
        if not applied_status:
            applied_status = StandaloneTaskStatus.objects.filter(
                task=instance,  
                institution=institution,
                deleted_at__isnull=True
            ).order_by("weight").first()
        instance.applied_task_status = applied_status
        instance.save(update_fields=["applied_task_status"])

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

        return Response(StandaloneTaskSerializer(instance, context={"request": request}).data, status=status.HTTP_201_CREATED)

class StandaloneTaskDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=StandaloneTaskSerializer,
                description="Task details.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Task not found.",
            ),
        },
        tags=["Standalone Task Management"],
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
        task = get_object_or_404(StandaloneTask, pk=pk, user_manager__profile__institution=institution, deleted_at__isnull=True)
        serializer = StandaloneTaskSerializer(task)
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
        tags=["Standalone Task Management"],
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
        task = get_object_or_404(StandaloneTask, pk=pk, user_manager__profile__institution=institution, deleted_at__isnull=True)
        task.approval_status = 'under_deletion'
        task.save(update_fields=['approval_status'])
        task.confirm_delete()
        return Response(
            {"message": "Task submitted for deletion approval."},
            status=status.HTTP_200_OK
        )

    @extend_schema(
        request=StandaloneTaskSerializer,
        responses={
            200: OpenApiResponse(
                response=StandaloneTaskSerializer,
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
        tags=["Standalone Task Management"],
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
            StandaloneTask,
            pk=pk,
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
        serializer = StandaloneTaskSerializer(
            task,
            data=request.data,
            partial=True,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        instance.confirm_update()

        # Handle task statuses (replace all)
        raw_statuses = request.data.get("task_statuses")

        if raw_statuses is not None:
            import json

            if isinstance(raw_statuses, str):
                try:
                    raw_statuses = json.loads(raw_statuses)
                except json.JSONDecodeError:
                    return Response({"error": "Invalid JSON in task_statuses."}, status=400)

            if not isinstance(raw_statuses, list):
                return Response({"error": "task_statuses must be a list."}, status=400)

            # Validate that only one status has is_current=true
            current_status_count = 0
            for status_data in raw_statuses:
                if not isinstance(status_data, dict):
                    return Response({"error": "Each task status must be a dictionary."}, status=400)
                if status_data.get('is_current', False):
                    current_status_count += 1
            
            if current_status_count > 1:
                return Response(
                    {"error": "Only one task status can have is_current set to true."},
                    status=400
                )

            # Replace all existing statuses
            from django.utils import timezone
            StandaloneTaskStatus.objects.filter(task=task, institution=institution).update(deleted_at=timezone.now())
            print(f"Creating new Raw Statuses")

            current_status = None
            for status_data in raw_statuses:
                # Extract is_current before cleaning
                is_current = status_data.get('is_current', False)
                
                # Remove is_current from data (not a model field)
                status_data_clean = {k: v for k, v in status_data.items() if k != 'is_current'}

                # Create the status
                created_status = StandaloneTaskStatus.objects.create(
                    institution=institution,
                    task=task,
                    name=status_data_clean['name'],
                    description=status_data_clean.get('description', ''),
                    weight=status_data_clean.get('weight', 0),
                    color_code=status_data_clean.get('color_code', '#9C9C9C'),
                    created_by=request.user.profile,
                    updated_by=request.user.profile
                )

                # Track the current status
                if is_current and current_status is None:
                    current_status = created_status

            # Apply current status or fallback to lowest weight
            applied_status = current_status
            if not applied_status:
                applied_status = StandaloneTaskStatus.objects.filter(
                    task=instance,  
                    institution=institution,
                    deleted_at__isnull=True
                ).order_by("weight").first()
            instance.applied_task_status = applied_status
            instance.save(update_fields=["applied_task_status"])

        # Send status change email (completion/failure)
        send_email_for_task_status_change(instance)

        # Determine if this update resulted in completion or failure
        is_completed = False
        is_failed = False
        
        if instance.applied_task_status == instance.completed_status:
            is_completed = True
        elif instance.applied_task_status == instance.failed_status:
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


class StandaloneTaskTimeSheetView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="Start or End Task",
        summary="Start or end a task",
        request=StandaloneTaskTimeSheetSerializer,
        responses={
            200: StandaloneTaskTimeSheetSerializer,
            400: OpenApiResponse(description="Bad Request"),
            401: OpenApiResponse(description="Unauthorized"),
            403: OpenApiResponse(description="Forbidden"),
        },
        tags=["Standalone Task TimeSheetView"],
    )
    @method_decorator(permission_required('can_update_task_timesheets'))
    @transaction.atomic
    def patch(self, request, task_timesheet_id):
        task_timesheet = StandaloneTaskTimeSheet.objects.filter(id=task_timesheet_id, deleted_at__isnull=True).first()

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
        task_timesheet.save(update_fields=["approval_status"])

        serializer = StandaloneTaskTimeSheetSerializer(
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



class StandaloneTaskStatusListCreateView(APIView, SortableAPIMixin):
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
                response=StandaloneTaskStatusSerializer(many=True),
                description="List of tasks statuses.",
            ),
            400: OpenApiResponse(description="Invalid ordering field."),
            404: OpenApiResponse(description="Institution not found."),
        },
        tags=["Standalone Task Status Management"],
    )
    @method_decorator(permission_required('can_view_task_statuses'))
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

        statuses = StandaloneTaskStatus.objects.filter(
            institution=institution, deleted_at__isnull=True
        )

        if search_query:
            statuses = statuses.filter(
                Q(name__icontains=search_query) |
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
        serializer = StandaloneTaskStatusSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)


    @extend_schema(
        request=StandaloneTaskStatusSerializer,
        responses={
            201: OpenApiResponse(
                response=StandaloneTaskStatusSerializer,
                description="Task status created successfully.",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors.",
            ),
        },
        tags=["Standalone Task Status Management"],
    )
    @method_decorator(permission_required('can_create_task_statuses'))
    @transaction.atomic()
    def post(self, request):
        serializer = StandaloneTaskStatusSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            instance = serializer.save()
            instance.confirm_create()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StandaloneTaskStatusDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=StandaloneTaskStatusSerializer,
                description="Task status details.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Task status not found.",
            ),
        },
        tags=["Standalone Task Status Management"],
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
        status_obj = get_object_or_404(StandaloneTaskStatus, pk=pk, institution=institution, deleted_at__isnull=True)
        serializer = StandaloneTaskStatusSerializer(status_obj)
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
        tags=["Standalone Task Status Management"],
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
        status_obj = get_object_or_404(StandaloneTaskStatus, pk=pk, institution=institution, deleted_at__isnull=True)
        status_obj.approval_status = 'under_deletion'
        status_obj.save(update_fields=['approval_status'])
        status_obj.confirm_delete()
        return Response(
            {"message": "Task status submitted for deletion approval."},
            status=status.HTTP_200_OK
        )


    @extend_schema(
        request=StandaloneTaskStatusSerializer,
        responses={
            200: OpenApiResponse(
                response=StandaloneTaskStatusSerializer,
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
        tags=["Standalone Task Status Management"],
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
        status_obj = get_object_or_404(StandaloneTaskStatus, pk=pk, institution=institution, deleted_at__isnull=True)
        status_obj.approval_status = 'under_update'
        status_obj.save(update_fields=['approval_status'])
        serializer = StandaloneTaskStatusSerializer(status_obj, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            instance = serializer.save()
            instance.confirm_update()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StandaloneTaskPriorityListCreateView(APIView, SortableAPIMixin):
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
                response=StandaloneTaskPrioritySerializer(many=True),
                description="List of task priority.",
            ),
            400: OpenApiResponse(description="Invalid ordering field."),
            404: OpenApiResponse(description="Institution not found."),
        },
        tags=["Standalone Task Priority Management"],
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

        priorities = StandaloneTaskPriority.objects.filter(
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
        serializer = StandaloneTaskPrioritySerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)


    @extend_schema(
        request=StandaloneTaskPrioritySerializer,
        responses={
            201: OpenApiResponse(
                response=StandaloneTaskPrioritySerializer,
                description="Task Priority created successfully.",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors.",
            ),
        },
        tags=["Standalone Task Priority Management"],
    )
    @method_decorator(permission_required('can_create_task_priority'))
    @transaction.atomic()
    def post(self, request):
        serializer = StandaloneTaskPrioritySerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            instance = serializer.save()
            instance.confirm_create()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StandaloneTaskPriorityDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=StandaloneTaskPrioritySerializer,
                description="Task priority details.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Task priority not found.",
            ),
        },
        tags=["Standalone Task Priority Management"],
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
        status_obj = get_object_or_404(StandaloneTaskPriority, pk=pk, institution=institution, deleted_at__isnull=True)
        serializer = StandaloneTaskPrioritySerializer(status_obj)
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
        tags=["Standalone Task Priority Management"],
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
        status_obj = get_object_or_404(StandaloneTaskPriority, pk=pk, institution=institution, deleted_at__isnull=True)
        status_obj.approval_status = 'under_deletion'
        status_obj.save(update_fields=['approval_status'])
        status_obj.confirm_delete()
        return Response(
            {"message": "Task priority submitted for deletion approval."},
            status=status.HTTP_200_OK
        )


    @extend_schema(
        request=StandaloneTaskPrioritySerializer,
        responses={
            200: OpenApiResponse(
                response=StandaloneTaskPrioritySerializer,
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
        tags=["Standalone Task Priority Management"],
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
        status_obj = get_object_or_404(StandaloneTaskPriority, pk=pk, institution=institution, deleted_at__isnull=True)
        status_obj.approval_status = 'under_update'
        status_obj.save(update_fields=['approval_status'])
        serializer = StandaloneTaskPrioritySerializer(status_obj, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            instance = serializer.save()
            instance.confirm_update()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StandaloneTaskMessageListCreateApiView(APIView):
    permission_classes = [IsAuthenticated]
    allowed_ordering_fields = ['content', 'created_at']
    default_ordering = ['-created_at']
    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=StandaloneTaskMessageSerializer(many=True),
                description="List of task messages.",
            ),
            400: OpenApiResponse(description="Invalid ordering field."),
            404: OpenApiResponse(description="Institution not found."),
        },
        tags=["Standalone Task Message Management"],
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

        task_messages = StandaloneTaskMessage.objects.filter(
            institution=institution, deleted_at__isnull=True
        )

        if task_id:
            task_messages = task_messages.filter(task_id=task_id)


        paginator = CustomPageNumberPagination()
        paginated_qs = paginator.paginate_queryset(task_messages, request)
        serializer = StandaloneTaskMessageSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)



    @extend_schema(
        request=StandaloneTaskMessageSerializer,
        responses={
            201: OpenApiResponse(
                response=StandaloneTaskMessageSerializer,
                description="Task Message created successfully.",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors.",
            ),
        },
        tags=["Standalone Task Message Management"],
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

        serializer = StandaloneTaskMessageSerializer(data=request.data, context={"request": request})
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
        is_discussion_participant = StandaloneTaskDiscussionParticipant.objects.filter(
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

        instance  = serializer.save()
        instance.confirm_create()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class StandaloneTaskMessageDetailApiView(APIView):
    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=StandaloneTaskMessageSerializer,
                description="Task message details.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Task message  not found.",
            ),
        },
        tags=["Standalone Task Message Management"],
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
        task_message = get_object_or_404(StandaloneTaskMessage, pk=pk, institution=institution, deleted_at__isnull=True)
        serializer = StandaloneTaskMessageSerializer(task_message)
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
        tags=["Standalone Task Message Management"],
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
        task_message = get_object_or_404(StandaloneTaskMessage, pk=pk, institution=institution, deleted_at__isnull=True)
        task_message.approval_status = 'under_deletion'
        task_message.save(update_fields=['approval_status'])
        task_message.confirm_delete()
        return Response(
            {"message": "Task message submitted for deletion approval."},
            status=status.HTTP_200_OK
        )

    @extend_schema(
        request=StandaloneTaskMessageSerializer,
        responses={
            200: OpenApiResponse(
                response=StandaloneTaskMessageSerializer,
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
        tags=["Standalone Task Message Management"],
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
        task_message = get_object_or_404(StandaloneTaskMessage, pk=pk, institution=institution, deleted_at__isnull=True)
        task_message.approval_status = 'under_update'
        task_message.save(update_fields=['approval_status'])
        serializer = StandaloneTaskMessageSerializer(task_message, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            instance = serializer.save()
            instance.confirm_update()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class StandaloneTaskExtensionRequestListCreateView(APIView):

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=StandaloneTaskExtensionRequestSerializer(many=True),
                description="List of task extension requests.",
            ),
            400: OpenApiResponse(description="Invalid ordering field."),
            404: OpenApiResponse(description="Institution not found."),
        },
        tags=["Standalone Task Extension Request Management"],
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

        tasks_extensions = StandaloneTaskExtensionRequest.objects.filter(
            institution=institution,
            deleted_at__isnull=True,
            approved=False,
            accepted=False
        ).order_by('-created_at')

        if task_id:
            tasks_extensions = tasks_extensions.filter(task_id=task_id)

        paginator = CustomPageNumberPagination()
        paginated_qs = paginator.paginate_queryset(tasks_extensions, request)
        serializer = StandaloneTaskExtensionRequestSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)


    @extend_schema(
        request=StandaloneTaskExtensionRequestSerializer,
        responses={
            201: OpenApiResponse(
                response=StandaloneTaskExtensionRequestSerializer,
                description="Task extension created successfully.",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors.",
            ),
        },
        tags=["Standalone Task Extension Request Management"],
    )
    def post(self, request):
        serializer = StandaloneTaskExtensionRequestSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        instance = serializer.save()
        instance.confirm_create()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class StandaloneTaskExtensionRequestDetail(APIView):

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=StandaloneTaskExtensionRequestSerializer,
                description="Task extension request details.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="TAsk extension request  not found.",
            ),
        },
        tags=["Standalone Task Extension Request Management"],
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
        task_extension = get_object_or_404(StandaloneTaskExtensionRequest, pk=pk, institution=institution, deleted_at__isnull=True)
        serializer = StandaloneTaskExtensionRequestSerializer(task_extension)
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
        tags=["Standalone Task Extension Request Management"],
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
        task_extension_request = get_object_or_404(StandaloneTaskExtensionRequest, pk=pk, institution=institution, deleted_at__isnull=True)
        task_extension_request.approval_status = 'under_deletion'
        task_extension_request.save(update_fields=['approval_status'])
        task_extension_request.confirm_delete()
        return Response(
            {"message": "Task extension request submitted for deletion approval."},
            status=status.HTTP_200_OK
        )


    @extend_schema(
        request=StandaloneTaskExtensionRequestSerializer,
        responses={
            200: OpenApiResponse(
                response=StandaloneTaskExtensionRequestSerializer,
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
        tags=["Standalone Task Extension Request Management"],
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
        task_extension_request = get_object_or_404(StandaloneTaskExtensionRequest, pk=pk, institution=institution, deleted_at__isnull=True)
        task_extension_request.approval_status = 'under_update'
        task_extension_request.save(update_fields=['approval_status'])
        serializer = StandaloneTaskExtensionRequestSerializer(task_extension_request, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            instance = serializer.save()
            instance.confirm_update()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StandaloneTaskExtensionRequestApprove(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=StandaloneTaskExtensionApprovalReason,
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
        tags=["Standalone Task Extension Request Management"],
    )
    def post(self, request):
        serializer = StandaloneTaskExtensionApprovalReason(data=request.data)
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

        if extension_request.new_start_date:
            task.start_date = extension_request.new_start_date
        if extension_request.new_end_date:
            task.end_date = extension_request.new_end_date
        task.save(update_fields=["start_date", "end_date"])

        extension_request.approved = True
        extension_request.accepted = True
        extension_request.approval_reason = approval_reason
        extension_request.save(update_fields=["approved", "accepted", "approval_reason"])

        task_leader = task.user_manager
        task_assignee_objects = task.user_assignees.all()

        frontend_url = settings.FRONTEND_URL
        task_url = f"{frontend_url}/task-mgt/task/{task.id}"

        task_assignee_ids = []
        for task_assignee in task_assignee_objects:
            task_assignee_ids.append(task_assignee.user_assigned.id)

        send_project_or_task_email.delay_on_commit(
            [task_leader.id],
            list(task_assignee_ids),
            url=task_url,
            task_id=task.id,
            is_accepted=True
        )

        return Response({"message": "Task extended successfully"}, status=status.HTTP_200_OK)


class StandaloneTaskExtensionRequestReject(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=StandaloneTaskExtensionApprovalReason,
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
        tags=["Standalone Task Extension Request Management"],
    )
    def post(self, request):
        serializer = StandaloneTaskExtensionApprovalReason(data=request.data)
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

        extension_request.approved = True
        extension_request.accepted = False
        extension_request.approval_reason = approval_reason
        extension_request.save(update_fields=["approved", "accepted", "approval_reason"])

        # Experimental feature for email notification on rejection or acceptance

        task_leader = task.user_manager
        task_assignee_objects = task.user_assignees.all()

        frontend_url = settings.FRONTEND_URL
        task_url = f"{frontend_url}/task-mgt/task/{task.id}"

        task_assignee_ids = []
        for task_assignee in task_assignee_objects:
            print(f"Task assignees: {task_assignee.user_assigned.id}")
            task_assignee_ids.append(task_assignee.user_assigned.id)

        send_project_or_task_email.delay_on_commit(
            [task_leader.id],
            list(task_assignee_ids),
            url=task_url,
            task_id=task.id,
            is_rejected=True
        )

        return Response({"message": "Extension request rejected"}, status=status.HTTP_200_OK)


class StandaloneTaskDisscusionParticipantListCreateApiView(APIView):
    
    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=StandaloneTaskDiscussionParticipantSerializer(many=True),
                description="List of task discussion participant.",
            ),
            404: OpenApiResponse(description="Institution not found."),
        },
        tags=["Standalone Task Disscusion Participant Management"],
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

        task_discussion_participants = StandaloneTaskDiscussionParticipant.objects.filter(
            task__user_manager__profile__institution=institution, deleted_at__isnull=True
        )
        paginator = CustomPageNumberPagination()
        paginated_qs = paginator.paginate_queryset(task_discussion_participants, request)
        serializer = StandaloneTaskDiscussionParticipantSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        request=StandaloneTaskDiscussionParticipantSerializer,
        responses={
            201: OpenApiResponse(
                response=StandaloneTaskDiscussionParticipantSerializer,
                description="Task Discussion Participant created successfully.",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request, validation errors.",
            ),
        },
        tags=["Standalone Task Disscusion Participant Management"],
    )
    @transaction.atomic()
    def post(self, request):
        serializer = StandaloneTaskDiscussionParticipantSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            instance = serializer.save()
            instance.confirm_create()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    

class StandaloneTasskDisscusionParticipantDetailsApiView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=StandaloneTaskDiscussionParticipantSerializer,
                description="Task discussion participant details.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Task discussion participant not found.",
            ),
        },
        tags=["Standalone Task Disscusion Participant Management"],
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

        task_discussion_participant = get_object_or_404(StandaloneTaskDiscussionParticipant, pk=pk, task__user_manager__profile__institution=institution, deleted_at__isnull=True)
        serializer = StandaloneTaskDiscussionParticipantSerializer(task_discussion_participant)
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
        tags=["Standalone Task Disscusion Participant Management"],
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
        task_discussion_participant = get_object_or_404(StandaloneTaskDiscussionParticipant, pk=pk, task__user_manager__profile__institution=institution, deleted_at__isnull=True)       
        task_discussion_participant.approval_status = 'under_deletion'
        task_discussion_participant.save(update_fields=['approval_status'])
        task_discussion_participant.confirm_delete()
        return Response(
            {"message": "Task Discussion Particaipant submitted for deletion approval."},
            status=status.HTTP_200_OK
        )


    @extend_schema(
        request=StandaloneTaskDiscussionParticipantSerializer,
        responses={
            200: OpenApiResponse(
                response=StandaloneTaskDiscussionParticipantSerializer,
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
        tags=["Standalone Task Disscusion Participant Management"],
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
        task_discussion_participant = get_object_or_404(StandaloneTaskDiscussionParticipant, pk=pk, task__user_manager__profile__institution=institution, deleted_at__isnull=True)    
        task_discussion_participant.approval_status = 'under_update'
        task_discussion_participant.save(update_fields=['approval_status'])
        serializer = StandaloneTaskDiscussionParticipantSerializer(task_discussion_participant, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            instance = serializer.save()
            instance.confirm_update()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SetTaskStatusDefaultsView(APIView):

    @extend_schema(
        summary="Configure default completed and failed statuses",
        description="Set the default status IDs to be used for marking tasks as completed or failed.",
        request=DefaultTaskStatusConfigSerializer,
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Task Defaults set successfully..",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={"message": "Task Defaults set successfully."},
                        response_only=True,
                    )
                ],
            ),
            400: OpenApiResponse(description="Bad request (e.g., invalid data)."),
            403: OpenApiResponse(description="Permission denied."),
            404: OpenApiResponse(description="Task  not found."),
        },
        tags=["Standalone Task Management"],
    )
    def post(self, request):
        serializer = DefaultTaskStatusConfigSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        completed_id = serializer.validated_data['completed_status']
        failed_id = serializer.validated_data['failed_status']
        task_id = serializer.validated_data['task']

        user = request.user.profile
        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            return Response(
                {"error": "Institution not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        task = get_object_or_404(StandaloneTask, pk=task_id, user_manager__profile__institution=institution, deleted_at__isnull=True)
        completed_status = get_object_or_404(StandaloneTaskStatus, pk=completed_id, task=task, deleted_at__isnull=True)
        failed_status = get_object_or_404(StandaloneTaskStatus, pk=failed_id, task=task, deleted_at__isnull=True)

        task.approval_status = 'under_update'
        task.save(update_fields=["approval_status"])
        
        # Set project completed and failed statuses
        task.completed_status = completed_status
        task.failed_status = failed_status

        task.save(update_fields=["completed_status", "failed_status"])
        task.confirm_update()
        return Response({"message": "Task Defaults set successfully."}, status=status.HTTP_200_OK)


class StandaloneTaskEmailConfigListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=StandaloneTaskEmailConfigSerializer(many=True),
        responses={
            201: OpenApiResponse(
                response=StandaloneTaskEmailConfigSerializer(many=True),
                description="Task Email configs created successfully."
            ),
            400: OpenApiResponse(description="Bad request, validation errors."),
        },
        tags=["Standalone Task Email Config"],
    )
    @transaction.atomic
    def post(self, request):
        # Expect a list of objects
        if not isinstance(request.data, list):
            return Response(
                {"error": "Expected a list of task email configurations."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = StandaloneTaskEmailConfigSerializer(
            data=request.data,
            many=True,
            context={"request": request}
        )

        if serializer.is_valid():
            try:
                instances = serializer.save()
                # instances.confirm_create()
                return Response(
                    StandaloneTaskEmailConfigSerializer(instances, many=True).data,
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
                response=StandaloneTaskEmailConfigSerializer(many=True),
                description="List of Task Email configs."
            ),
            404: OpenApiResponse(description="Institution not found."),
        },
        tags=["Standalone Task Email Config"],
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

        queryset = StandaloneTaskEmailConfig.objects.filter(
            deleted_at__isnull=True
        )

        # Filtering
        task_id = request.query_params.get("task")
        intent = request.query_params.get("intent")

        if task_id and task_id.isdigit():
            queryset = queryset.filter(task_id=task_id)
        if intent:
            if intent in dict(StandaloneTaskEmailConfig.Intent.choices):
                queryset = queryset.filter(intent=intent)
            else:
                return Response({"error": "Invalid intent value."}, status=status.HTTP_400_BAD_REQUEST)

        # Pagination
        paginator = CustomPageNumberPagination()
        paginated_qs = paginator.paginate_queryset(queryset, request)
        serializer = StandaloneTaskEmailConfigSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)


class StandaloneTaskEmailConfigDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(response=StandaloneTaskEmailConfigSerializer, description="Task Email config details."),
            404: OpenApiResponse(description="Task Email config not found."),
        },
        tags=["Standalone Task Email Config"],
    )
    def get(self, request, pk):
        task_email_config = get_object_or_404(StandaloneTaskEmailConfig, pk=pk, deleted_at__isnull=True)
        serializer = StandaloneTaskEmailConfigSerializer(task_email_config)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Task Email config marked for deletion and sent for approval."),
            404: OpenApiResponse(description="Task Email config not found."),
        },
        tags=["Standalone Task Email Config"],
    )
    @transaction.atomic
    def delete(self, request, pk):
        task_email_config = get_object_or_404(StandaloneTaskEmailConfig, pk=pk, deleted_at__isnull=True)
        task_email_config.approval_status = 'under_deletion'
        task_email_config.save(update_fields=['approval_status'])
        task_email_config.confirm_delete()
        return Response(
            {"message": "Task Email config submitted for deletion approval."},
            status=status.HTTP_200_OK
        )

    @extend_schema(
        request=StandaloneTaskEmailConfigSerializer,
        responses={
            200: OpenApiResponse(response=StandaloneTaskEmailConfigSerializer, description="Task Email config updated successfully."),
            400: OpenApiResponse(description="Bad request, validation errors."),
            404: OpenApiResponse(description="Task Email config not found."),
        },
        tags=["Standalone Task Email Config"],
    )
    @transaction.atomic
    def patch(self, request, pk):
        task_email_config = get_object_or_404(StandaloneTaskEmailConfig, pk=pk, deleted_at__isnull=True)
        # Set approval status before validation (as per your workflow)
        task_email_config.approval_status = 'under_update'
        task_email_config.save(update_fields=['approval_status'])

        serializer = StandaloneTaskEmailConfigSerializer(
            task_email_config,
            data=request.data,
            context={"request": request},
            partial=True
        )
        if serializer.is_valid():
            updated_instance = serializer.save()
            # updated_instance.confrim_update()
            return Response(StandaloneTaskEmailConfigSerializer(updated_instance).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StandaloneTaskProgressStatus(APIView, SortableAPIMixin):
    @extend_schema(
    parameters=[
        {
            "name": "task",
            "type": "int",
            "description": "Filter tasks by task ID.",
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
            response=StandaloneTaskSerializer(many=True),
            description="Paginated list of tasks matching the filters.",
        ),
        400: OpenApiResponse(description="Invalid ordering field or parameter."),
        404: OpenApiResponse(description="Institution not found for the authenticated user."),
    },
    tags=["Standalone Task Status Management"],
    )
    @method_decorator(permission_required('can_view_all_tasks'))
    def get(self, request):
        user = request.user.profile
        task_id = request.query_params.get("task", None)
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

        tasks = StandaloneTask.objects.filter(
            user_manager__profile__institution=institution,
            deleted_at__isnull=True
        )

        if task_id:
            tasks = tasks.filter(id=task_id)

        # Filter by progress_status if specified
        if progress_status in ['completed', 'failed']:
            filtered_tasks = []
            for task in tasks:

                if progress_status == 'completed':
                    if task.completed_status is not None and \
                    task.applied_task_status == task.completed_status:
                        filtered_tasks.append(task)
                        
                elif progress_status == 'failed':
                    if task.failed_status is not None and \
                    task.applied_task_status == task.failed_status:
                        filtered_tasks.append(task)

            tasks = filtered_tasks

        if isinstance(tasks, models.QuerySet):
            try:
                tasks = self.apply_sorting(tasks, request)
            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        paginator = CustomPageNumberPagination()
        paginated_qs = paginator.paginate_queryset(tasks, request)
        serializer = StandaloneTaskSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)