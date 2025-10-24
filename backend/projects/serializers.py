from institution.models import Institution
from rest_framework import serializers
from .models import(
    Project,
    ProjectStaffGroupAssignees,
    ProjectStatus,
    ProjectUserAssignees,
    Task,
    TaskDocument,
    TaskStaffGroupAssignees,
    TaskTimeSheet,
    ProjectDocument,
    TaskPriority,
    TaskUserAssignees,
    TaskMessage,
    ProjectMessage,
    TaskExtensionRequest,
    ProjectTaskStatus,
    ProjectDiscussionParticipant,
    TaskDiscussionParticipant,
    ProjectTaskEmailConfig
)
from django.db import transaction
from approval.serializers import BaseApprovableSerializer
from django.utils import timezone
from users.models import CustomUser, StaffGroup
from django.core.exceptions import ValidationError
import json


class ProjectCreateTaskStatusSerializer(BaseApprovableSerializer):
    class Meta:
        model = ProjectTaskStatus
        #exclude = ["project"]  # project will be provided externally
        read_only_fields = ['id', 'deleted_at','created_at','project']
        fields = '__all__'
        

    def create(self, validated_data):
        request = self.context.get("request")
        user_profile = getattr(request.user, "profile", None) if request else None

        # Get the project from context or raise an error
        project = self.context.get("project")
        if not project:
            raise serializers.ValidationError({"error": "Project is required to create a task status."})

        # validated_data.pop("project", None)

        # Set created_by and updated_by from request user profile
        validated_data["created_by"] = user_profile
        validated_data["updated_by"] = user_profile

        # Create the ProjectTaskStatus linked to the project
        return ProjectTaskStatus.objects.create(project=project, **validated_data)

class ProjectTaskStatusSerializer(BaseApprovableSerializer):
    class Meta:
        model = ProjectTaskStatus
        #exclude = ["project"]  # project will be provided externally
        read_only_fields = ['id', 'deleted_at','created_at', 'approval_status', 'is_active']
        fields = '__all__'
        

    def create(self, validated_data):
        request = self.context.get("request")
        user_profile = getattr(request.user, "profile", None) if request else None

        # Set created_by and updated_by from request user profile
        validated_data["created_by"] = user_profile
        validated_data["updated_by"] = user_profile

        # Create the ProjectTaskStatus linked to the project
        return ProjectTaskStatus.objects.create(**validated_data)


class ProjectDocumentSerializer(BaseApprovableSerializer):
    name = serializers.CharField(max_length=255, allow_blank=False)

    class Meta:
        model = ProjectDocument
        fields = "__all__"


class TaskPrioritySerializer(BaseApprovableSerializer):
    class Meta:
        model = TaskPriority
        fields = '__all__'
        read_only_fields = ("id", "deleted_at", "approval_status", "is_active")

    def to_internal_value(self, data):
        weight = data.get("weight")

        if weight is not None:
            
            if isinstance(weight, str):
                
                if "." in weight:
                    raise serializers.ValidationError(
                        {"error": f"Weight: {weight} must be an integer"}
                    )
               
                if not weight.isdigit():
                    raise serializers.ValidationError(
                        {"error": f"Weight: {weight} must be an integer"}
                    )

            elif isinstance(weight, float):
                raise serializers.ValidationError(
                    {"error": f"Weight: {weight} must be an integer"}
                )

        return super().to_internal_value(data)

    def validate_weight(self, value):
        if isinstance(value, float):
            raise serializers.ValidationError(
                {"error": f"Weight: {value} must be an integer"}
            )

        try:
            int(value)
        except (ValueError, TypeError):
            raise serializers.ValidationError(
                {"error": f"Weight: {value} must be an integer"}
            )

        return value



class TaskDocumentSerializer(BaseApprovableSerializer):
    class Meta:
        model = TaskDocument
        fields = "__all__"


class TaskTimeSheetSerializer(BaseApprovableSerializer):
    time_spent = serializers.SerializerMethodField()

    class Meta:
        model = TaskTimeSheet
        fields = [
            "id",
            "task",
            "start_time",
            "end_time",
            "time_spent",
            "notes",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]

    def get_time_spent(self, obj):
        if obj.timespent:
            total_seconds = int(obj.timespent.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours}h {minutes}m {seconds}s"
        return None

    def validate(self, data):
        start_time = data.get("start_time")
        end_time = data.get("end_time")

        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError({"error": "User context is required."})

        current_user_profile = getattr(request.user, "profile", None)

        if not current_user_profile:
            raise serializers.ValidationError({"error": "User must have a profile."})

        task = self.instance.task if self.instance else None

        if task:
            task_managers = task.managers.all()
            if current_user_profile not in task_managers:
                raise serializers.ValidationError(
                    {"error": "Only task managers can update timesheets for this task"}
                )

            if start_time and not self.instance.start_time:
                if task.task_status != "not_started":
                    raise serializers.ValidationError(
                        {"error": "Start time can only be set when the task is not started"}
                    )

        current_start = self.instance.start_time if self.instance else None
        current_end = self.instance.end_time if self.instance else None

        final_start = start_time if start_time is not None else current_start
        final_end = end_time if end_time is not None else current_end

        if final_start and final_end:
            if final_start >= final_end:
                raise serializers.ValidationError({"error": "Start time must be before end time"})

        return data

    def validate_start_time(self, value):
        if (
            self.instance
            and self.instance.start_time
            and value != self.instance.start_time
        ):
            if self.instance.start_time is not None:
                raise serializers.ValidationError(
                    {"error": "Start time can only be set once and cannot be changed"}
                )
        return value

    def create(self, validated_data):
        raise serializers.ValidationError(
            {"error": "Timesheets are automatically created when tasks are created."}
        )

    def update(self, instance, validated_data):
        start_time = validated_data.get("start_time")
        end_time = validated_data.get("end_time")

        request = self.context.get("request")
        current_user_profile = request.user.profile

        if current_user_profile not in instance.task.managers.all():
            raise serializers.ValidationError({"error": "Only task managers can update timesheets"})

        task = instance.task

        if start_time and not instance.start_time:
            if task.task_status == "not_started":
                task.task_status = "in_progress"
                task.save(update_fields=["task_status"])

        if end_time and not instance.end_time:
            if task.task_status == "in_progress":
                task.task_status = "completed"
                task.completion_date = timezone.now().date()
                task.save(update_fields=["task_status", "completion_date"])

        validated_data["updated_by"] = current_user_profile

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance

class ProjectStatusSerializer(BaseApprovableSerializer):
    class Meta:
        model = ProjectStatus
        fields = '__all__'
        read_only_fields = ['id', 'deleted_at','created_at', 'approval_status', 'is_active']

        
    def to_internal_value(self, data):
        weight = data.get("weight")

        if weight is not None:
            
            if isinstance(weight, str):
                
                if "." in weight:
                    raise serializers.ValidationError(
                        {"error": f"Weight: {weight} must be an integer"}
                    )
               
                if not weight.isdigit():
                    raise serializers.ValidationError(
                        {"error": f"Weight: {weight} must be an integer"}
                    )

            elif isinstance(weight, float):
                raise serializers.ValidationError(
                    {"error": f"Weight: {weight} must be an integer"}
                )

        return super().to_internal_value(data)

    def validate_weight(self, value):
        if isinstance(value, float):
            raise serializers.ValidationError(
                {"error": f"Weight: {value} must be an integer"}
            )

        try:
            int(value)
        except (ValueError, TypeError):
            raise serializers.ValidationError(
                {"error": f"Weight: {value} must be an integer"}
            )

        return value


class ProjectSerializer(BaseApprovableSerializer):
    project_documents = serializers.SerializerMethodField()
    user_manager = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
        help_text="Manager user ID"
    )

    user_assignees = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of assignee user IDs"
    )
    staff_group_assignees = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of staff group assignee IDs"
    )
    documents = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False,
        help_text="List of documents to upload with the project"
    )
    document_names = serializers.ListField(
        child=serializers.CharField(max_length=255, allow_blank=False),
        write_only=True,
        required=False,
        help_text="List of names for the uploaded documents"
    )
    project_task_statuses = serializers.SerializerMethodField()
    project_name = serializers.CharField(max_length=255, allow_blank=False)
    project_status = serializers.PrimaryKeyRelatedField(queryset=ProjectStatus.objects.all())
    milestones = serializers.JSONField(default=dict)
    institution = serializers.PrimaryKeyRelatedField(
        queryset=Institution.objects.all(),
        required=False,
        write_only=True
    )
    custom_fields = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True,
        help_text="List of custom field objects"
    )

    class Meta:
        model = Project
        exclude = ['deleted_at']
        # fields = '__all__'
        read_only_fields = ['id', 'deleted_at','created_at', 'updated_at', 'project_documents', 'approval_status']
        validators = []

    def get_project_task_statuses(self, obj):
        active_statuses = obj.project_task_statuses.filter(deleted_at__isnull=True)  
        return ProjectTaskStatusSerializer(active_statuses, many=True, context=self.context).data
    

    def validate_custom_fields(self, value):
        if not isinstance(value, list):
            raise ValidationError({"error": "custom_fields must be a list of objects."})

        valid_types = ["text", "number", "bool", "date", "select"]

        for idx, field in enumerate(value):
            if not isinstance(field, dict):
                raise ValidationError({
                    "error": f"Field at index {idx} must be an object."
                })

            # Check required properties
            required_props = ["label", "type", "required", "multiple"]
            missing_props = [prop for prop in required_props if prop not in field]
            if missing_props:
                raise ValidationError({
                    "error": f"Field at index {idx} missing required properties: {', '.join(missing_props)}."
                })

            # Validate label
            if not isinstance(field["label"], str) or not field["label"].strip():
                raise ValidationError({
                    "error": f"Field at index {idx}: 'label' must be a non-empty string."
                })

            # Validate type
            if field["type"] not in valid_types:
                raise ValidationError({
                    "error": f"Field at index {idx}: invalid type '{field['type']}'. Must be one of: {', '.join(valid_types)}."
                })

            # Validate required is boolean
            if not isinstance(field["required"], bool):
                raise ValidationError({
                    "error": f"Field at index {idx}: 'required' must be a boolean."
                })

            # Validate multiple is boolean (only relevant for 'select', but required for all)
            if not isinstance(field["multiple"], bool):
                raise ValidationError({
                    "error": f"Field at index {idx}: 'multiple' must be a boolean."
                })

            # For 'select', validate 'options'
            if field["type"] == "select":
                if "options" not in field:
                    raise ValidationError({
                        "error": f"Field at index {idx}: 'select' type must have an 'options' list."
                    })
                if not isinstance(field["options"], list):
                    raise ValidationError({
                        "error": f"Field at index {idx}: 'options' must be a list."
                    })
                if not field["options"]:
                    raise ValidationError({
                        "error": f"Field at index {idx}: 'options' list cannot be empty."
                    })
                if not all(isinstance(opt, str) for opt in field["options"]):
                    raise ValidationError({
                        "error": f"Field at index {idx}: all 'options' must be strings."
                    })

            # Validate default_value (if provided)
            if "default_value" in field and field["default_value"] is not None:
                default = field["default_value"]
                field_type = field["type"]
                multiple = field["multiple"]

                if field_type == "text":
                    if not isinstance(default, str):
                        raise ValidationError({
                            "error": f"Field at index {idx}: 'default_value' must be a string for 'text' type."
                        })

                elif field_type == "number":
                    if not isinstance(default, (int, float)):
                        raise ValidationError({
                            "error": f"Field at index {idx}: 'default_value' must be a number for 'number' type."
                        })

                elif field_type == "bool":
                    if not isinstance(default, bool):
                        raise ValidationError({
                            "error": f"Field at index {idx}: 'default_value' must be a boolean for 'bool' type."
                        })

                elif field_type == "date":
                    if not isinstance(default, str):
                        raise ValidationError({
                            "error": f"Field at index {idx}: 'default_value' must be a string (ISO date) for 'date' type."
                        })
                    from datetime import datetime
                    try:
                        datetime.strptime(default, "%Y-%m-%d")
                    except ValueError:
                        raise ValidationError({
                            "error": f"Field at index {idx}: 'default_value' must be in 'YYYY-MM-DD' format for 'date' type."
                        })

                elif field_type == "select":
                    if multiple:
                        # default_value must be a list of strings
                        if not isinstance(default, list):
                            raise ValidationError({
                                "error": f"Field at index {idx}: 'default_value' must be a list for multi-select."
                            })
                        if not all(isinstance(item, str) for item in default):
                            raise ValidationError({
                                "error": f"Field at index {idx}: all items in 'default_value' must be strings for multi-select."
                            })
                        # All values must be in options
                        valid_options = set(field["options"])
                        invalid_values = [val for val in default if val not in valid_options]
                        if invalid_values:
                            raise ValidationError({
                                "error": f"Field at index {idx}: invalid default values for multi-select: {invalid_values}. Must be subset of {field['options']}."
                            })
                    else:
                        # single select: default_value must be a string in options
                        if not isinstance(default, str):
                            raise ValidationError({
                                "error": f"Field at index {idx}: 'default_value' must be a string for single-select."
                            })
                        if default not in field["options"]:
                            raise ValidationError({
                                "error": f"Field at index {idx}: 'default_value' ('{default}') is not in options: {field['options']}."
                            })

        return value

    def get_project_documents(self, obj):
        documents = obj.documents.filter(deleted_at__isnull=True)
        return ProjectDocumentSerializer(documents, many=True).data

    def to_internal_value(self, data):
        import json
        processed_data = {}

        # custom_fields removed from single_value_fields
        single_value_fields = [
            'institution', 'project_name', 'project_status',
            'start_date', 'end_date', 'milestones', 'description',
            'completion_date', 'user_manager'
        ]

        def get_list(key):
            if hasattr(data, "getlist"):
                return data.getlist(key, [])
            return data.get(key, []) or []

        processed_data['user_assignees'] = get_list('user_assignees[]') or get_list('user_assignees')
        processed_data['staff_group_assignees'] = get_list('staff_group_assignees[]') or get_list('staff_group_assignees')
        processed_data['document_names'] = get_list('document_names[]') or get_list('document_names')
        processed_data['documents'] = []

        custom_fields_raw = get_list('custom_fields[]') or get_list('custom_fields')

        if custom_fields_raw:
            import json
            parsed_fields = []
            for item in custom_fields_raw:
                if isinstance(item, str):
                    try:
                        parsed_fields.append(json.loads(item))
                    except Exception as e:
                        raise serializers.ValidationError({"custom_fields": f"Invalid JSON format: {str(e)}"})
                elif isinstance(item, dict):
                    parsed_fields.append(item)
            processed_data['custom_fields'] = parsed_fields
        else:
            processed_data['custom_fields'] = []

        for key, value in data.items():
            if key in [
                'user_assignees', 'user_assignees[]',
                'staff_group_assignees', 'staff_group_assignees[]',
                'document_names', 'document_names[]', 'documents', 'documents[]',
                'custom_fields', 'custom_fields[]'  # Skip custom_fields here since we handled it above
            ]:
                continue

            if key in single_value_fields:
                if isinstance(value, list) and len(value) == 1:
                    processed_data[key] = value[0]
                elif isinstance(value, list) and len(value) > 1:
                    raise serializers.ValidationError({"error": f"{key} Expected a single value, received multiple values."})
                else:
                    processed_data[key] = value
            else:
                processed_data[key] = value if isinstance(value, list) else [value]

        request = self.context.get('request')
        if request and hasattr(request, "FILES"):
            processed_data['documents'] = (
                request.FILES.getlist('documents') or request.FILES.getlist('documents[]') or []
            )


        return super().to_internal_value(processed_data)


    def _parse_array_field(self, field_value):
        if field_value is None:
            return []
        if isinstance(field_value, str):
            # Handle comma-separated string
            return [int(x.strip()) for x in field_value.split(',') if x.strip().isdigit()] if field_value.strip() else []
        if isinstance(field_value, list):
            result = []
            for item in field_value:
                if isinstance(item, str) and item.strip().isdigit():
                    result.append(int(item.strip()))
                elif isinstance(item, (int, float)):
                    result.append(int(item))
            return result
        return []

    # def validate_project_name(self, value):
    #     if Project.objects.filter(project_name=value).exists():
    #         raise serializers.ValidationError("A project with this name already exists.")
    #     return value

    def validate(self, data):
        institution = data.get("institution")
        request = self.context.get('request')
        if not institution and request and hasattr(request.user, 'profile') and request.user.profile.institution:
            institution = request.user.profile.institution
            data['institution'] = institution

        if not institution:
            raise serializers.ValidationError({"error": "Institution is required"})

        project_status = data.get("project_status")
        if project_status and project_status.institution != institution:
            raise serializers.ValidationError(
                {"error": f"Project status with ID {project_status.id} does not belong to the selected institution"}
            )

        user_assignees = self._parse_array_field(data.get("user_assignees", []))
        for assignee_id in user_assignees:
            try:
                assignee = CustomUser.objects.get(id=assignee_id)
                if hasattr(assignee, 'profile') and assignee.profile.institution == institution:
                    continue
                raise serializers.ValidationError(
                    {"error": f"Assignee with ID {assignee_id} does not belong to the selected institution"}
                )
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError(
                    {"error": f"User with ID {assignee_id} does not exist"}
                )

        staff_group_assignees = self._parse_array_field(data.get("staff_group_assignees", []))
        for group_id in staff_group_assignees:
            try:
                group = StaffGroup.objects.get(id=group_id)
                if group.institution == institution:
                    continue
                raise serializers.ValidationError(
                    {"error": f"Staff group with ID {group_id} does not belong to the selected institution"}
                )
            except StaffGroup.DoesNotExist:
                raise serializers.ValidationError(
                    {"error": f"Staff group with ID {group_id} does not exist"}
                )
            
        documents = data.get("documents", [])
        document_names = data.get("document_names", [])
        if len(documents) != len(document_names):
            raise serializers.ValidationError(
                {"error": "The number of document names must match the number of uploaded documents"}
            )

        for document in documents:
            if not isinstance(document, (str, bytes)) and hasattr(document, 'size'):
                if document.size > 10 * 1024 * 1024:  # 10MB limit
                    raise serializers.ValidationError(
                        {"error": f"File {document.name} exceeds maximum size of 10MB"}
                    )
            else:
                raise serializers.ValidationError(
                    {"error": f"Invalid file format for {document.name}"}
                )

        for name in document_names:
            if not name.strip():
                raise serializers.ValidationError(
                    {"error": "Document names cannot be empty"}
                )

        data['user_assignees'] = user_assignees
        data['staff_group_assignees'] = staff_group_assignees
        return data

    def _create_project_documents(self, project, documents, document_names):
        """Helper method to create project documents with names."""
        for doc, name in zip(documents, document_names):
            try:
                document = ProjectDocument.objects.create(
                    project=project,
                    name=name,
                    document=doc
                )

            except Exception as e:
                raise

    def _create_project_relations(self, project, user_assignees, staff_group_assignees):
        """Helper method to create project relation records."""

        for user_id in user_assignees:
            try:
                assignee = CustomUser.objects.get(id=user_id)
                ProjectUserAssignees.objects.create(project=project, user_assigned=assignee)
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError({"error": f"User with ID {user_id} does not exist"})
            except Exception as e:
                raise

        for group_id in staff_group_assignees:
            try:
                group = StaffGroup.objects.get(id=group_id)
                ProjectStaffGroupAssignees.objects.create(project=project, group_assigned=group)
            except StaffGroup.DoesNotExist:
                raise serializers.ValidationError({"error": f"Staff group with ID {group_id} does not exist"})
            except Exception as e:
                raise

    @transaction.atomic
    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user.profile
        validated_data["updated_by"] = self.context["request"].user.profile

        user_assignees = validated_data.pop("user_assignees", [])
        staff_group_assignees = validated_data.pop("staff_group_assignees", [])
        documents = validated_data.pop("documents", [])
        document_names = validated_data.pop("document_names", [])
        custom_fields = validated_data.pop("custom_fields", [])
        project_task_statuses = validated_data.pop("project_task_statuses", [])

        request = self.context.get('request')
        if request and hasattr(request.user, 'profile') and request.user.profile.institution:
            validated_data['institution'] = request.user.profile.institution
        else:
            raise serializers.ValidationError({"error": "Unable to determine institution from user profile"})

        if custom_fields:
            validated_data['custom_fields'] = custom_fields

        project = Project.objects.create(**validated_data)
        
        self._create_project_relations(project, user_assignees, staff_group_assignees)

        if documents and document_names:
            self._create_project_documents(project, documents, document_names)

        return project

    @transaction.atomic
    def update(self, instance, validated_data):
        validated_data["updated_by"] = self.context["request"].user.profile
        user_assignees = validated_data.pop("user_assignees", None)
        staff_group_assignees = validated_data.pop("staff_group_assignees", None)
        documents = validated_data.pop("documents", [])
        document_names = validated_data.pop("document_names", [])
        custom_fields = validated_data.pop("custom_fields", None)

        if documents and len(documents) != len(document_names):
            raise serializers.ValidationError(
                {"error": "The number of document names must match the number of uploaded documents"}
            )

        instance.approval_status = 'under_update'
        instance.save(update_fields=['approval_status'])
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if custom_fields is not None:
            validated_data['custom_fields'] = custom_fields


        if user_assignees is not None:
            instance.user_assignees.all().delete()
            self._create_project_relations(instance, user_assignees, [])
        if staff_group_assignees is not None:
            instance.staff_group_assignees.all().delete()
            self._create_project_relations(instance, [], staff_group_assignees)

        # Create new documents
        if documents:
            self._create_project_documents(instance, documents, document_names)

        return instance

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.project_status:
            rep["project_status"] = {
                "id": instance.project_status.id,
                "status_name": instance.project_status.status_name,
                "color_code": instance.project_status.color_code,
                "weight": instance.project_status.weight
            }
        else:
            rep["project_status"] = None

        if instance.user_manager:
            rep["user_manager"] = {
                "id": instance.user_manager.id,
                "name": instance.user_manager.fullname
            }
        else:
            rep["user_manager"] = None


        rep["user_assignees"] = [
            {"id": assignee.user_assigned.id, "name": assignee.user_assigned.fullname}
            for assignee in instance.user_assignees.all()
        ]

        rep["staff_group_assignees"] = [
            {"id": assignee.group_assigned.id, "name": assignee.group_assigned.name}
            for assignee in instance.staff_group_assignees.all()
        ]

        rep["project_documents"] = self.get_project_documents(instance)

        if instance.completed_status:
            rep["completed_status"] = {
                "id": instance.completed_status.id,
                "status_name": instance.completed_status.name,
                "color_code": instance.completed_status.color_code,
                "weight": instance.completed_status.weight
            }
        else:
            rep["completed_status"] = None

        
        if instance.failed_status:
            rep["failed_status"] = {
                "id": instance.failed_status.id,
                "status_name": instance.failed_status.name,
                "color_code": instance.failed_status.color_code,
                "weight": instance.failed_status.weight
            }
        else:
            rep["failed_status"] = None

        # TODO: Remove this nesting and frontend handles the API call
        rep["project_tasks"] = TaskSerializer(instance.tasks, many=True).data

        return rep

class TaskSerializer(BaseApprovableSerializer):
    user_manager = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
        help_text="Manager user ID"
    )
    user_assignees = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        default=[],
        help_text="List of assignee user IDs"
    )
    staff_group_assignees = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        default=[],
        help_text="List of staff group assignee IDs"
    )
    documents = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False,
        default=[],
        help_text="List of documents to upload with the task"
    )
    document_names = serializers.ListField(
        child=serializers.CharField(max_length=255, allow_blank=False),
        write_only=True,
        required=False,
        default=[],
        help_text="List of names for the uploaded documents"
    )
    task_name = serializers.CharField(max_length=255, allow_blank=False)
    applied_project_task_status = serializers.PrimaryKeyRelatedField(queryset=ProjectTaskStatus.objects.all(), required=False, allow_null=True)
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all(), required=False, allow_null=True)
    priority = serializers.PrimaryKeyRelatedField(queryset=TaskPriority.objects.all(), required=False, allow_null=True)
    progress_status = serializers.CharField(read_only=True)
    progress_status_display = serializers.CharField(read_only=True)

    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'approval_status', 'deleted_at', 'is_active']
        validators = []

    def _parse_array_field(self, field_value):
        if field_value is None:
            return []
        if isinstance(field_value, str):
            return [int(x.strip()) for x in field_value.split(',') if x.strip().isdigit()] if field_value.strip() else []
        if isinstance(field_value, list):
            result = []
            for item in field_value:
                if isinstance(item, str) and item.strip().isdigit():
                    result.append(int(item.strip()))
                elif isinstance(item, (int, float)):
                    result.append(int(item))
            return result
        return field_value

    def to_internal_value(self, data):
        internal_data = {}

        def get_list_value(key, fallback_key=None):
            if hasattr(data, 'getlist'):
                value = data.getlist(key, [])
                if not value and fallback_key:
                    value = data.getlist(fallback_key, [])
                return value
            else:
                value = data.get(key, [])
                if not value and fallback_key:
                    value = data.get(fallback_key, [])
                return value if isinstance(value, list) else []

        for field in ['task_name', 'description', 'start_date', 'end_date',
                    'created_by','updated_by', 'freeze_assignee','project',
                    'task_status', 'priority', 'user_manager','custom_fields','applied_project_task_status']:
            if field in data:
                internal_data[field] = data[field]

        if 'custom_fields' in internal_data and isinstance(internal_data['custom_fields'], str):
            import json
            try:
                internal_data['custom_fields'] = json.loads(internal_data['custom_fields'])
            except Exception:
                raise serializers.ValidationError({
                    "custom_fields": "Invalid JSON format"
                })

        internal_data['user_assignees'] = self._parse_array_field(
            get_list_value('user_assignees[]', 'user_assignees')
        )
        internal_data['staff_group_assignees'] = self._parse_array_field(
            get_list_value('staff_group_assignees[]', 'staff_group_assignees')
        )
        internal_data['document_names'] = get_list_value('document_names[]', 'document_names')
        internal_data['documents'] = get_list_value('documents[]', 'documents')

        return super().to_internal_value(internal_data)


    def validate_custom_fields(self, value):

        if isinstance(value, dict):
            return value

        if not isinstance(value, list):
            raise ValidationError({"error": "custom_fields must be a list of objects."})

        valid_types = ["text", "number", "bool", "date", "select"]

        for idx, field in enumerate(value):
            if not isinstance(field, dict):
                raise ValidationError({
                    "error": f"Field at index {idx} must be an object."
                })

            # Check required properties
            required_props = ["label", "type", "required", "multiple"]
            missing_props = [prop for prop in required_props if prop not in field]
            if missing_props:
                raise ValidationError({
                    "error": f"Field at index {idx} missing required properties: {', '.join(missing_props)}."
                })

            # Validate label
            if not isinstance(field["label"], str) or not field["label"].strip():
                raise ValidationError({
                    "error": f"Field at index {idx}: 'label' must be a non-empty string."
                })

            # Validate type
            if field["type"] not in valid_types:
                raise ValidationError({
                    "error": f"Field at index {idx}: invalid type '{field['type']}'. Must be one of: {', '.join(valid_types)}."
                })

            # Validate required is boolean
            if not isinstance(field["required"], bool):
                raise ValidationError({
                    "error": f"Field at index {idx}: 'required' must be a boolean."
                })

            # Validate multiple is boolean (only relevant for 'select', but required for all)
            if not isinstance(field["multiple"], bool):
                raise ValidationError({
                    "error": f"Field at index {idx}: 'multiple' must be a boolean."
                })

            # For 'select', validate 'options'
            if field["type"] == "select":
                if "options" not in field:
                    raise ValidationError({
                        "error": f"Field at index {idx}: 'select' type must have an 'options' list."
                    })
                if not isinstance(field["options"], list):
                    raise ValidationError({
                        "error": f"Field at index {idx}: 'options' must be a list."
                    })
                if not field["options"]:
                    raise ValidationError({
                        "error": f"Field at index {idx}: 'options' list cannot be empty."
                    })
                if not all(isinstance(opt, str) for opt in field["options"]):
                    raise ValidationError({
                        "error": f"Field at index {idx}: all 'options' must be strings."
                    })

            # Validate default_value (if provided)
            if "default_value" in field and field["default_value"] is not None:
                default = field["default_value"]
                field_type = field["type"]
                multiple = field["multiple"]

                if field_type == "text":
                    if not isinstance(default, str):
                        raise ValidationError({
                            "error": f"Field at index {idx}: 'default_value' must be a string for 'text' type."
                        })

                elif field_type == "number":
                    if not isinstance(default, (int, float)):
                        raise ValidationError({
                            "error": f"Field at index {idx}: 'default_value' must be a number for 'number' type."
                        })

                elif field_type == "bool":
                    if not isinstance(default, bool):
                        raise ValidationError({
                            "error": f"Field at index {idx}: 'default_value' must be a boolean for 'bool' type."
                        })

                elif field_type == "date":
                    if not isinstance(default, str):
                        raise ValidationError({
                            "error": f"Field at index {idx}: 'default_value' must be a string (ISO date) for 'date' type."
                        })
                    from datetime import datetime
                    try:
                        datetime.strptime(default, "%Y-%m-%d")
                    except ValueError:
                        raise ValidationError({
                            "error": f"Field at index {idx}: 'default_value' must be in 'YYYY-MM-DD' format for 'date' type."
                        })

                elif field_type == "select":
                    if multiple:
                        # default_value must be a list of strings
                        if not isinstance(default, list):
                            raise ValidationError({
                                "error": f"Field at index {idx}: 'default_value' must be a list for multi-select."
                            })
                        if not all(isinstance(item, str) for item in default):
                            raise ValidationError({
                                "error": f"Field at index {idx}: all items in 'default_value' must be strings for multi-select."
                            })
                        # All values must be in options
                        valid_options = set(field["options"])
                        invalid_values = [val for val in default if val not in valid_options]
                        if invalid_values:
                            raise ValidationError({
                                "error": f"Field at index {idx}: invalid default values for multi-select: {invalid_values}. Must be subset of {field['options']}."
                            })
                    else:
                        # single select: default_value must be a string in options
                        if not isinstance(default, str):
                            raise ValidationError({
                                "error": f"Field at index {idx}: 'default_value' must be a string for single-select."
                            })
                        if default not in field["options"]:
                            raise ValidationError({
                                "error": f"Field at index {idx}: 'default_value' ('{default}') is not in options: {field['options']}."
                            })

        return value

    def validate(self, data):
        request = self.context.get('request')
        institution = None
        if request and hasattr(request.user, 'profile') and request.user.profile.institution:
            institution = request.user.profile.institution
        else:
            raise serializers.ValidationError({"error": "Unable to determine institution from user profile"})

        task_status = data.get("task_status")
        if task_status and task_status.institution != institution:
            raise serializers.ValidationError(
                {"error": f"Task status with ID {task_status.id} does not belong to the user's institution"}
            )

        priority = data.get("priority")
        if priority and priority.institution != institution:
            raise serializers.ValidationError(
                {"error": f"Priority with ID {priority.id} does not belong to the user's institution"}
            )

        user_assignees = data.get("user_assignees", [])
        for assignee_id in user_assignees:
            try:
                assignee = CustomUser.objects.get(id=assignee_id)
                if hasattr(assignee, 'profile') and assignee.profile.institution == institution:
                    continue
                raise serializers.ValidationError(
                    {"error": f"Assignee with ID {assignee_id} does not belong to the user's institution"}
                )
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError(
                    {"error": f"User with ID {assignee_id} does not exist"}
                )

        staff_group_assignees = data.get("staff_group_assignees", [])
        for group_id in staff_group_assignees:
            try:
                group = StaffGroup.objects.get(id=group_id)
                if group.institution == institution:
                    continue
                raise serializers.ValidationError(
                    {"error": f"Staff group with ID {group_id} does not belong to the user's institution"}
                )
            except StaffGroup.DoesNotExist:
                raise serializers.ValidationError(
                    {"error": f"Staff group with ID {group_id} does not exist"}
                )

        documents = data.get("documents", [])
        document_names = data.get("document_names", [])
        if len(documents) != len(document_names):
            raise serializers.ValidationError(
                {"error": "The number of document names must match the number of uploaded documents"}
            )

        for document in documents:
            if not isinstance(document, (str, bytes)) and hasattr(document, 'size'):
                if document.size > 10 * 1024 * 1024:
                    raise serializers.ValidationError(
                        {"error": f"File {document.name} exceeds maximum size of 10MB"}
                    )
            else:
                raise serializers.ValidationError(
                    {"error": f"Invalid file format for {document.name}"}
                )

        for name in document_names:
            if not name.strip():
                raise serializers.ValidationError(
                    {"error": "Document names cannot be empty"}
                )

        return data

    def _create_task_documents(self, task, documents, document_names):
        for doc, name in zip(documents, document_names):
            try:
                document = TaskDocument.objects.create(
                    task=task,
                    name=name,
                    document=doc
                )
            except Exception as e:
                raise

    def _create_task_relations(self, task, user_assignees, staff_group_assignees):

        for user_id in user_assignees:
            try:
                assignee = CustomUser.objects.get(id=user_id)
                TaskUserAssignees.objects.create(task=task, user_assigned=assignee)
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError({"error": f"User with ID {user_id} does not exist"})
            except Exception as e:
                raise

        for group_id in staff_group_assignees:
            try:
                group = StaffGroup.objects.get(id=group_id)
                TaskStaffGroupAssignees.objects.create(task=task, group_assigned=group)
            except StaffGroup.DoesNotExist:
                raise serializers.ValidationError({"error": f"Staff group with ID {group_id} does not exist"})
            except Exception as e:
                raise

    @transaction.atomic
    def create(self, validated_data):
        user_assignees = validated_data.pop("user_assignees", [])
        staff_group_assignees = validated_data.pop("staff_group_assignees", [])
        documents = validated_data.pop("documents", [])
        document_names = validated_data.pop("document_names", [])
        validated_data["created_by"] = self.context["request"].user.profile
        validated_data["updated_by"] = self.context["request"].user.profile
        
        task = Task.objects.create(**validated_data)

        self._create_task_relations(task, user_assignees, staff_group_assignees)

        if documents and document_names:
            self._create_task_documents(task, documents, document_names)

        return task

    @transaction.atomic
    def update(self, instance, validated_data):
        request = self.context.get("request")

        user_assignees = validated_data.pop("user_assignees", None)
        staff_group_assignees = validated_data.pop("staff_group_assignees", None)
        documents = validated_data.pop("documents", [])
        document_names = validated_data.pop("document_names", [])
        new_freeze_assignee = validated_data.get("freeze_assignee", instance.freeze_assignee)

        validated_data["updated_by"] = request.user.profile

        if documents and len(documents) != len(document_names):
            raise serializers.ValidationError({
                "error": "The number of document names must match the number of uploaded documents."
            })

        is_creator = (instance.created_by and instance.created_by.id == request.user.id)
        institution = request.user.profile.institution
        is_institution_owner = (institution.institution_owner == request.user)
        has_permission = request.user.has_permission("can_edit_tasks")
        is_allowed = (is_creator or is_institution_owner or has_permission)
        if "freeze_assignee" in validated_data:

            if not (is_creator or is_institution_owner or has_permission):
                raise serializers.ValidationError({
                    "error": "Only the task creator, institution owner, or someone with the 'can_edit_tasks' permission can modify 'freeze_assignee'."
                })

        assignee_update_requested = bool(user_assignees or staff_group_assignees)

        if instance.freeze_assignee and assignee_update_requested:
            raise serializers.ValidationError({
                "error": "Cannot modify assignees because 'freeze_assignee' is enabled for this task."
            })

        instance.approval_status = "under_update"
        instance.save(update_fields=["approval_status"])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if not (new_freeze_assignee or is_allowed):  
            raise serializers.ValidationError({
                "error": "Only the task creator, institution owner, or someone with the 'can_edit_tasks' permission can modify assignees on a task."
            })

        if user_assignees:
            instance.user_assignees.all().delete()
            self._create_task_relations(instance, user_assignees, [])

        if staff_group_assignees:
            instance.staff_group_assignees.all().delete()
            self._create_task_relations(instance, [], staff_group_assignees)
        

        if documents:
            self._create_task_documents(instance, documents, document_names)

        return instance

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.applied_project_task_status:
            rep["applied_project_task_status"] = {
                "id": instance.applied_project_task_status.id,
                "color_code": instance.applied_project_task_status.color_code,
                "weight": instance.applied_project_task_status.weight,
                "name": instance.applied_project_task_status.name
            }
        else:
            rep["applied_project_task_status"] = None

        if instance.project:
            rep["project"] = {
                "id": instance.project.id,
                "project_name": instance.project.project_name
            }
        else:
            rep["project"] = None

        if instance.priority:
            rep["priority"] = {
                "id": instance.priority.id,
                "name": instance.priority.name,
                "color": instance.priority.color_code,
                "weight": instance.priority.weight
            }
        else:
            rep["priority"] = None

        if instance.user_manager:
            rep["user_manager"] = {
                "id": instance.user_manager.id,
                "name": instance.user_manager.fullname
            }
        else:
            rep["user_manager"] = None

        rep["user_assignees"] = [
            {"id": assignee.user_assigned.id, "name": assignee.user_assigned.fullname}
            for assignee in instance.user_assignees.all()
        ]

        rep["staff_group_assignees"] = [
            {"id": assignee.group_assigned.id, "name": assignee.group_assigned.name}
            for assignee in instance.staff_group_assignees.all()
        ]

        rep["task_documents"] = [
            {"id": doc.id, "name": doc.name, "document": doc.document.url}
            for doc in instance.documents.filter(deleted_at__isnull=True)
        ]

        return rep

# Main Dashborad Analytics

class ProjectCountByYearSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    project_count = serializers.IntegerField()

class MainDashboardSerializer(serializers.Serializer):
    total_task = serializers.IntegerField()
    total_project = serializers.IntegerField()
    project_count_by_year = ProjectCountByYearSerializer(many=True)


# Project Analytics

class ProjectStatusOverviewSerializer(serializers.Serializer):
    status = serializers.CharField()
    count = serializers.IntegerField(min_value=0)


class ProjectProgressSerializer(serializers.Serializer):
    project = serializers.CharField()
    progress = serializers.IntegerField(min_value=0, max_value=100)


class TaskOverviewSerializer(serializers.Serializer):
    status = serializers.CharField()
    count = serializers.IntegerField(min_value=0)


class RecentProjectsSerializer(serializers.Serializer):
    name = serializers.CharField()
    start_date = serializers.DateField(allow_null=True)
    end_date = serializers.DateField(allow_null=True)
    progress = serializers.IntegerField(min_value=0, max_value=100)
    status = serializers.CharField()


class ProjectAnalyticsDashboardSerializer(serializers.Serializer):
    total_projects = serializers.IntegerField(min_value=0)
    total_tasks = serializers.IntegerField(min_value=0)
    average_duration = serializers.IntegerField(
        min_value=0,
        help_text="Average project duration in days"
    )
    employees_assigned = serializers.IntegerField(min_value=0)
    project_status_overview = ProjectStatusOverviewSerializer(many=True)
    project_progress = ProjectProgressSerializer(many=True)
    task_overview = TaskOverviewSerializer(many=True)
    recent_projects = RecentProjectsSerializer(many=True)


# Task Analytics
class RecentTaskSerializer(serializers.Serializer):
    name = serializers.CharField()
    start_date = serializers.DateTimeField(allow_null=True)
    end_date = serializers.DateTimeField(allow_null=True)
    progress = serializers.IntegerField(
        min_value=0,
        max_value=100,
        help_text="Completion percentage (0-100)"
    )
    status = serializers.CharField()


class TaskCountByMonthSerializer(serializers.Serializer):
    month = serializers.IntegerField(min_value=1, max_value=12)
    task_count = serializers.IntegerField(min_value=0)
    year = serializers.IntegerField(min_value=1900, max_value=2100)


class TaskAnalyticsDashboardSerializer(serializers.Serializer):
    total_tasks = serializers.IntegerField(min_value=0)  # plural for consistency
    task_status_overview = TaskOverviewSerializer(many=True)
    task_over_time = TaskCountByMonthSerializer(many=True)
    recent_tasks = RecentTaskSerializer(many=True)


 # All users that belong to a project
class UserProjectSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='fullname')

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email']

class ProjectUsersReadSerializer(serializers.Serializer):
    project_id = serializers.IntegerField()
    users = UserProjectSerializer(many=True)
    total_users = serializers.IntegerField()


class TaskMessageSerializer(BaseApprovableSerializer):
    author_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = TaskMessage
        fields = [
            'id',
            'task',
            'author',
            'author_name',
            'content',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['author', 'created_at', 'updated_at', 'author_name']

    def get_author_name(self, obj):
        if obj.author:
            return obj.author.fullname
        return "Deleted User"

    def validate_content(self, value):
        if len(value) > 2000:
            raise serializers.ValidationError("Message cannot exceed 2000 characters.")
        return value.strip()

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user = request.user
            validated_data['author'] = user

            # Attach the institution automatically
            if hasattr(user, 'profile') and getattr(user.profile, 'institution', None):
                validated_data['institution'] = user.profile.institution
            else:
                raise serializers.ValidationError({"institution": "User has no associated institution."})

            validated_data['created_by'] = user.profile
            validated_data['updated_by'] = user.profile


        return super().create(validated_data)



class ProjectMessageSerializer(BaseApprovableSerializer):
    author_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ProjectMessage
        fields = [
            'id',
            'project',
            'author',
            'author_name',
            'content',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['author', 'created_at', 'updated_at', 'author_name']

    def get_author_name(self, obj):
        if obj.author:
            return obj.author.fullname
        return "Deleted User"

    def validate_content(self, value):
        if len(value) > 2000:
            raise serializers.ValidationError("Message cannot exceed 2000 characters.")
        return value.strip()

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user
        project = validated_data['project']
        validated_data['institution'] = project.institution
        validated_data['created_by'] = user.profile
        validated_data['updated_by'] = user.profile

        if request and hasattr(request, 'user'):
            validated_data['author'] = request.user
        return super().create(validated_data)


class TaskExtensionRequestSerializer(serializers.ModelSerializer):
    task = serializers.PrimaryKeyRelatedField(
        queryset=Task.objects.all(),
        error_messages={
            "does_not_exist": "The specified task does not exist.",
            "incorrect_type": "Task ID must be an integer."
        }
    )
    class Meta:
        model = TaskExtensionRequest
        fields = ['id','task', 'new_start_date', 'new_end_date', 'request_reason', 'approval_reason','approved', 'accepted', 'requested_by', 'created_at', 'updated_at']
        read_only_fields = ['requested_by', 'institution', 'approved']

    def validate(self, data):
        task = data['task']
        request = self.context.get('request')
        institution = None
        if request and hasattr(request.user, 'profile') and request.user.profile.institution:
            institution = request.user.profile.institution
        else:
            raise serializers.ValidationError({"error": "Unable to determine institution from user profile"})

        # check if task belongs to the same institution as the user
        task_institution = task.get_institution()
        same_institution = (task_institution == institution)
        if not same_institution:
            raise serializers.ValidationError({"error": "This task does not belong to your institution."})

        # check if the request maker is the leader of the task
        is_task_leader = (task.user_manager == request.user)
        if not is_task_leader:
            raise serializers.ValidationError({"error": "You are not the leader of this task to make this request"})


        if data.get('new_end_date') and data.get('new_start_date'):
            if data['new_end_date'] < data['new_start_date']:
                raise serializers.ValidationError("End date cannot be before start date.")
        return data

    def create(self, validated_data):
        request = self.context['request']
        validated_data['created_by'] = request.user.profile
        validated_data['updated_by'] = request.user.profile
        validated_data['requested_by'] = request.user
        validated_data['institution'] = validated_data['task'].project.institution if validated_data['task'].project is not None else request.user.profile.institution
        validated_data.pop("accepted", None)
        validated_data.pop("approval_reason", None)
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        validated_data["updated_by"] = self.context["request"].user.profile
        validated_data["approval_status"] = "under_update"
        validated_data.pop("accepted", None)
        validated_data.pop("approval_reason", None)
        return super().update(instance, validated_data)
    
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.task:
            rep["task"] = {
                "id": instance.task.id,
                "name": instance.task.task_name,
                "description": instance.task.description,
                "old_start_date": instance.task.start_date,
                "old_end_date": instance.task.end_date
            }
        else:
            rep["task"] = None

        if instance.requested_by:
            rep["requested_by"] = {
                "id": instance.requested_by.id,
                "name": instance.requested_by.fullname
            }
        else:
            rep["requested_by"] = None
        return rep

class TaskExtensionApprovalReason(serializers.Serializer):
    task_extension_request = serializers.PrimaryKeyRelatedField(
        queryset=TaskExtensionRequest.objects.all(),
        error_messages={
            "does_not_exist": "The specified task extension request does not exist.",
            "incorrect_type": "Task extension request ID must be an integer."
        }
    )
    approval_reason = serializers.CharField()


class DefaultProjectTaskStatusSerializer(serializers.Serializer):
    name = serializers.CharField()
    description = serializers.CharField()
    weight = serializers.IntegerField()
    color_code = serializers.CharField()


class DefaultStatusConfigSerializer(serializers.Serializer):
    project = serializers.IntegerField(min_value=1)
    completed_status = serializers.IntegerField(min_value=1)
    failed_status = serializers.IntegerField(min_value=1)

    def validate(self, attrs):
        if attrs['completed_status'] == attrs['failed_status']:
            raise serializers.ValidationError(
                "Completed and failed status IDs must be different."
            )
        return attrs



class TaskDiscussionParticipantSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        write_only=False  
    )

    class Meta:
        model = TaskDiscussionParticipant
        fields = "__all__"
        read_only_fields = ('id', 'added_by', 'deleted_at')
        validators = []

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data

    def create(self, validated_data):
        request = self.context["request"]
        task = validated_data["task"]
        user = validated_data["user"]

        # check for existing participant, even if soft-deleted
        existing_participant = TaskDiscussionParticipant.objects.filter(
            task=task,
            user=user
        ).first()

        if existing_participant:
            if getattr(existing_participant, "deleted_at", None):
                existing_participant.deleted_at = None
                existing_participant.can_send = validated_data.get("can_send", existing_participant.can_send)
                existing_participant.added_by = request.user
                existing_participant.save(update_fields=["deleted_at", "can_send", "added_by"])
                return existing_participant

            raise serializers.ValidationError({
                "user": "This user is already an active participant in this discussion."
            })

        # normal creation for new participant
        validated_data["added_by"] = request.user
        validated_data["created_by"] = request.user.profile
        validated_data["updated_by"] = request.user.profile

        return super().create(validated_data)


    def to_representation(self, instance):
        rep = super().to_representation(instance)

        if instance.user:
            rep["user"] = {
                "id": instance.user.id,
                "name": instance.user.fullname
            }
        else:
            rep["user"] = None

        return rep

class ProjectDiscussionParticipantSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        write_only=False
    )

    class Meta:
        model = ProjectDiscussionParticipant
        fields = "__all__"
        read_only_fields = ('id', 'added_by', 'deleted_at')
        validators = []

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data

    
    def create(self, validated_data):
        request = self.context["request"]
        project = validated_data["project"]
        user = validated_data["user"]

        # check for existing participant, even if soft-deleted
        existing_participant = ProjectDiscussionParticipant.objects.filter(
            project=project,
            user=user
        ).first()

        if existing_participant:
            if getattr(existing_participant, "deleted_at", None):
                existing_participant.deleted_at = None
                existing_participant.can_send = validated_data.get("can_send", existing_participant.can_send)
                existing_participant.added_by = request.user
                existing_participant.save(update_fields=["deleted_at", "can_send", "added_by"])
                return existing_participant

            raise serializers.ValidationError({
                "user": "This user is already an active participant in this discussion."
            })

        # normal creation for new participant
        validated_data["added_by"] = request.user
        validated_data["created_by"] = request.user.profile
        validated_data["updated_by"] = request.user.profile

        return super().create(validated_data)

    def to_representation(self, instance):
        rep = super().to_representation(instance)

        if instance.user:
            rep["user"] = {
                "id": instance.user.id,
                "name": instance.user.fullname
            }
        else:
            rep["user"] = None

        return rep
    

class ProjectTaskEmailConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectTaskEmailConfig
        fields = "__all__"
        read_only_fields = ("id", "deleted_at", "approval_status", "is_active")

    def create(self, validated_data):
        request = self.context.get("request")
        if not request or not request.user:
            raise serializers.ValidationError({"error": "No authenticated user found in request context"})

        try:
            profile = request.user.profile
        except AttributeError as e:
            raise serializers.ValidationError({"error": "User profile  is not configured"})

        # Ensure protected fields aren't injected
        validated_data.pop("deleted_at", None)
        validated_data.pop("id", None)

        # Inject audit and ownership fields
       
        validated_data["created_by"] = request.user
        validated_data["updated_by"] = request.user

        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get("request")
        if not request or not request.user:
            raise serializers.ValidationError({"error": "No authenticated user found in request context"})

        # Prevent updating read-only fields
        validated_data.pop("deleted_at", None)
        validated_data.pop("id", None)

        validated_data["updated_by"] = request.user
        validated_data["approval_status"] = "under_update"

        return super().update(instance, validated_data)