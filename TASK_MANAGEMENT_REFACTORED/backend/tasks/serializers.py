from institution.models import Institution
from rest_framework import serializers
from .models import(
    StandaloneTask,
    StandaloneTaskDocument,
    StandaloneTaskStaffGroupAssignees,
    StandaloneTaskTimeSheet,
    StandaloneTaskPriority,
    StandaloneTaskStatus,
    StandaloneTaskUserAssignees,
    StandaloneTaskMessage,
    StandaloneTaskExtensionRequest,
    StandaloneTaskDiscussionParticipant,
    StandaloneTaskEmailConfig,
)
from django.db import transaction
from approval.serializers import BaseApprovableSerializer
from django.utils import timezone
from users.models import CustomUser, StaffGroup
from django.core.exceptions import ValidationError
import json


class StandaloneTaskStatusSerializer(BaseApprovableSerializer):
    class Meta:
        model = StandaloneTaskStatus
        fields = '__all__'
        extra_kwargs = {
            "institution": {"required": False},  
            "task": {"required": False},
        }
        read_only_fields = ['deleted_at', 'approval_status', 'is_active']
        validators = []

    def validate(self, attrs):
        # Remove is_current from attrs since it's not a model field
        self.is_current = attrs.pop('is_current', False)
        
        request = self.context.get("request")
        user_profile = getattr(request.user, "profile", None)

        if not user_profile:
            raise serializers.ValidationError({"error": "User must have a profile."})

        if not attrs.get("institution"):
            attrs["institution"] = user_profile.institution

        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        user_profile = getattr(request.user, "profile", None)
        task = self.context.get("task")

        if not task:
            raise serializers.ValidationError({"error": "Task is required to create a task status."})

        validated_data["task"] = task
        validated_data["institution"] = validated_data.get("institution", user_profile.institution)
        validated_data["created_by"] = user_profile
        validated_data["updated_by"] = user_profile

        instance = StandaloneTaskStatus.objects.create(**validated_data)
        # Store is_current on the instance for later use
        instance._is_current = self.is_current
        return instance
    
    def get_is_current(self):
        return getattr(self, 'is_current', False)

class StandaloneTaskPrioritySerializer(BaseApprovableSerializer):
    class Meta:
        model = StandaloneTaskPriority
        fields = '__all__'
        read_only_fields = ['deleted_at', 'approval_status', 'is_active']

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



class StandaloneTaskDocumentSerializer(BaseApprovableSerializer):
    class Meta:
        model = StandaloneTaskDocument
        fields = "__all__"


class StandaloneTaskTimeSheetSerializer(BaseApprovableSerializer):
    time_spent = serializers.SerializerMethodField()

    class Meta:
        model = StandaloneTaskTimeSheet
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



class StandaloneTaskSerializer(BaseApprovableSerializer):
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
    task_statuses = serializers.SerializerMethodField() 
    task_name = serializers.CharField(max_length=255, allow_blank=False)
    priority = serializers.PrimaryKeyRelatedField(queryset=StandaloneTaskPriority.objects.all(), required=False, allow_null=True)
    progress_status = serializers.CharField(read_only=True)
    progress_status_display = serializers.CharField(read_only=True)

    class Meta:
        model = StandaloneTask
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'approval_status', 'deleted_at']
        validators = []

    def get_task_statuses(self, obj):
        active_statuses = obj.standalone_task_statuses.filter(deleted_at__isnull=True)  
        return StandaloneTaskStatusSerializer(active_statuses, many=True, context=self.context).data
    
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

        # ✅ Only real fields on StandaloneTask
        for field in [
            'task_name', 'description', 'start_date', 'end_date',
            'created_by', 'updated_by', 'freeze_assignee',
            'priority', 'user_manager', 'custom_fields',
            'applied_task_status', 'completed_status', 'failed_status'
        ]:
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

        # ✅ FIXED: validate applied_task_status instead of task_status
        applied_task_status = data.get("applied_task_status")
        if applied_task_status and applied_task_status.institution != institution:
            raise serializers.ValidationError(
                {"error": f"Task status with ID {applied_task_status.id} does not belong to the user's institution"}
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
                # ⚠️ Optional improvement: avoid .name if not available
                doc_name = getattr(document, 'name', 'unknown')
                raise serializers.ValidationError(
                    {"error": f"Invalid file format for {doc_name}"}
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
                document = StandaloneTaskDocument.objects.create(
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
                StandaloneTaskUserAssignees.objects.create(task=task, user_assigned=assignee)
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError({"error": f"User with ID {user_id} does not exist"})
            except Exception as e:
                raise

        for group_id in staff_group_assignees:
            try:
                group = StaffGroup.objects.get(id=group_id)
                StandaloneTaskStaffGroupAssignees.objects.create(task=task, group_assigned=group)
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
        # REMOVED: task_statuses = validated_data.pop("task_statuses", [])  ← ❌ unnecessary

        task = StandaloneTask.objects.create(**validated_data)

        self._create_task_relations(task, user_assignees, staff_group_assignees)

        if documents and document_names:
            self._create_task_documents(task, documents, document_names)

        return task

    @transaction.atomic
    def update(self, instance, validated_data):
        request = self.context.get("request")
        print(f"Request User: {request.user}")

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
        print(f"Is allowed: {is_allowed}")
        if "freeze_assignee" in validated_data:

            if not (is_creator or is_institution_owner or has_permission):
                raise serializers.ValidationError({
                    "error": "Only the task creator, institution owner, or someone with the 'can_edit_tasks' permission can modify 'freeze_assignee'."
                })

        print(f"Original Freeze Assignee: {instance.freeze_assignee}")
        print(f"New Freeze Assignee: {new_freeze_assignee}")
        print(f"User assignees: {user_assignees}")
        print(f"Staff group assignees: {staff_group_assignees}")

        assignee_update_requested = bool(user_assignees or staff_group_assignees)
        print(f"Assignee Update Request: {assignee_update_requested}")

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
            print("Updating user assignees...")
            instance.user_assignees.all().delete()
            self._create_task_relations(instance, user_assignees, [])

        if staff_group_assignees:
            print("Updating staff group assignees...")
            instance.staff_group_assignees.all().delete()
            self._create_task_relations(instance, [], staff_group_assignees)
        

        if documents:
            self._create_task_documents(instance, documents, document_names)

        return instance

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        
        if instance.applied_task_status:
            rep["applied_task_status"] = {
                "id": instance.applied_task_status.id,
                "color_code": instance.applied_task_status.color_code,
                "weight": instance.applied_task_status.weight,
                "name": instance.applied_task_status.name
            }
        else:
            rep["applied_task_status"] = None

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

        rep["staff_group_assignees"] = [
            {"id": assignee.group_assigned.id, "name": assignee.group_assigned.name}
            for assignee in instance.staff_group_assignees.all()
        ]

        rep["task_documents"] = [
            {"id": doc.id, "name": doc.name, "document": doc.document.url}
            for doc in instance.documents.filter(deleted_at__isnull=True)
        ]

        return rep

class StandaloneTaskMessageSerializer(BaseApprovableSerializer):
    author_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = StandaloneTaskMessage
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



class StandaloneTaskExtensionRequestSerializer(serializers.ModelSerializer):
    task = serializers.PrimaryKeyRelatedField(
        queryset=StandaloneTask.objects.all(),
        error_messages={
            "does_not_exist": "The specified task does not exist.",
            "incorrect_type": "Task ID must be an integer."
        }
    )
    class Meta:
        model = StandaloneTaskExtensionRequest
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
        validated_data['institution'] = request.user.profile.institution
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

class StandaloneTaskExtensionApprovalReason(serializers.Serializer):
    task_extension_request = serializers.PrimaryKeyRelatedField(
        queryset=StandaloneTaskExtensionRequest.objects.all(),
        error_messages={
            "does_not_exist": "The specified task extension request does not exist.",
            "incorrect_type": "Task extension request ID must be an integer."
        }
    )
    approval_reason = serializers.CharField()



class StandaloneTaskDiscussionParticipantSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        write_only=False  
    )

    class Meta:
        model = StandaloneTaskDiscussionParticipant
        fields = "__all__"
        read_only_fields = ('id', 'added_by', 'deleted_at', 'approval_status', 'is_active')
        validators = []

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data

    def create(self, validated_data):
        request = self.context["request"]
        task = validated_data["task"]
        user = validated_data["user"]

        # check for existing participant, even if soft-deleted
        existing_participant = StandaloneTaskDiscussionParticipant.objects.filter(
            task=task,
            user=user
        ).first()

        print(f"Existing user : {existing_participant}")

        if existing_participant:
            if getattr(existing_participant, "deleted_at", None):
                existing_participant.deleted_at = None
                existing_participant.can_send = validated_data.get("can_send", existing_participant.can_send)
                existing_participant.added_by = request.user
                existing_participant.save(update_fields=["deleted_at", "can_send", "added_by"])
                return existing_participant

            raise serializers.ValidationError({
                "error": "This user is already an active participant in this discussion."
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

class DefaultTaskStatusConfigSerializer(serializers.Serializer):
    task = serializers.IntegerField(min_value=1)
    completed_status = serializers.IntegerField(min_value=1)
    failed_status = serializers.IntegerField(min_value=1)

    def validate(self, attrs):
        if attrs['completed_status'] == attrs['failed_status']:
            raise serializers.ValidationError(
                {"error": "Completed and failed status IDs must be different."} 
            )
        return attrs


class StandaloneTaskEmailConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = StandaloneTaskEmailConfig
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