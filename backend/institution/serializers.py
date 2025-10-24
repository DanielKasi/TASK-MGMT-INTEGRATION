from rest_framework import serializers
from approval.serializers import BaseApprovableSerializer
from users.models import CustomUser
from users.serializers import CustomUserSerializer
from .models import (
    Department,
    Institution,
    Branch,
    UserBranch,
    InstitutionKYCDocument,
    InstitutionBankType,
    InstitutionWorkingDays,
    InstitutionBankAccount,
    InstitutionPenaltyConfig,
    BranchPenaltyConfig,
    BranchWorkingDays,
    BranchDay,
    BranchLocationComparisonConfig,
)
import os
from django.db import transaction
import logging
from django.utils import timezone
from settings.serializers import SystemDaySerializer
from settings.models import SystemDay


logger = logging.getLogger(__name__)


class AIQuerySerializer(serializers.Serializer):
    question = serializers.CharField(required=True, allow_blank=False, write_only=True)
    answer = serializers.CharField(read_only=True)
    chat_id = serializers.UUIDField(required=False)

    def validate(self, attrs):
        if not self.instance and not attrs.get("question"):
            raise serializers.ValidationError({"error": "Question is required."})
        return attrs


class InstitutionKYCDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstitutionKYCDocument
        fields = [
            "id",
            "institution",
            "document_title",
            "document_file",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "institution",
            "created_at",
            "updated_at",
        ]


class InstitutionKYCDocumentBulkCreateSerializer(serializers.Serializer):
    document_file = serializers.ListField(
        child=serializers.FileField(), write_only=True, required=True
    )
    document_title = serializers.ListField(
        child=serializers.CharField(max_length=255), write_only=True, required=True
    )

    def validate(self, data):
        if len(data["document_file"]) != len(data["document_title"]):
            raise serializers.ValidationError({"error": "Mismatched file and title counts."})
        return data

    def create(self, validated_data):
        request = self.context["request"]
        institution = request.user.profile.institution

        document_file = validated_data.pop("document_file", [])
        document_title = validated_data.pop("document_title", [])

        documents = [
            InstitutionKYCDocument(
                institution=institution,
                document_title=title,
                document_file=file,
            )
            for title, file in zip(document_title, document_file)
        ]

        return InstitutionKYCDocument.objects.bulk_create(documents)


class InstitutionSerializer(serializers.ModelSerializer):
    institution_owner_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all()
    )
    institution_logo = serializers.ImageField(required=False, allow_null=True)
    approval_status_display = serializers.CharField(
        source="get_approval_status_display", read_only=True
    )

    branches = serializers.SerializerMethodField()

    class Meta:
        model = Institution
        fields = [
            "id",
            "institution_email",
            "institution_name",
            "first_phone_number",
            "second_phone_number",
            "institution_logo",
            "institution_owner_id",
            "theme_color",
            "location",
            "latitude",
            "longitude",
            "country_code",
            "approval_status",
            "approval_status_display",
            "approval_date",
            "branches",
            "is_active",
            "user_inactivity_time",
            "is_attendance_penalties_enabled",
        ]

    def create(self, validated_data):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError(
                {"error": "User must be authenticated to create an Institution."}
            )

        institution_owner = validated_data.pop("institution_owner_id")
        departments_data = self.context.get("departments", [])

        # Log departments data for debugging
        logger.info(f"Creating institution with departments_data: {departments_data}")

        with transaction.atomic():
            # Create the Institution
            institution = Institution.objects.create(
                institution_owner=institution_owner,
                created_by=request.user,
                **validated_data,
            )

            # Create Departments and JobPositions
            for dept_data in departments_data:
                department = Department.objects.create(
                    name=dept_data["name"],
                    description=dept_data.get("description", ""),
                    institution=institution,
                    created_by=request.user,
                    created_at=timezone.now(),
                    updated_at=timezone.now(),
                )
                for job_data in dept_data.get("job_positions", []):
                    JobPosition.objects.create(
                        name=job_data["name"],
                        description=job_data.get("description", ""),
                        department=department,
                        job_position_status="active",
                        created_at=timezone.now(),
                        salary_min=job_data.get("salary_min", 50000),
                        salary_max=job_data.get("salary_max", 100000),
                    )

        logger.info(
            f"Institution {institution.institution_name} created successfully with {len(departments_data)} departments"
        )
        return institution

    def get_branches(self, institution):
        user = self.context.get("user")
        if user and institution.institution_owner == user:
            branches = institution.branches.all()
        else:
            user_branches = UserBranch.objects.filter(user=user).values_list(
                "branch_id", flat=True
            )
            branches = institution.branches.filter(id__in=user_branches)
        return BranchSerializer(branches, many=True).data


class InstitutionBankTypeSerializer(BaseApprovableSerializer):
    class Meta:
        model = InstitutionBankType

        fields = [
            "id",
            "institution",
            "bank_fullname",
            "bank_code",
            "br_code",
            "created_by",
            "created_at",
            "updated_by",
            "updated_at",
            "is_active",
        ]

        read_only_fields = [
            "id",
            "institution",
            "created_by",
            "created_at",
            "updated_by",
            "updated_at",
        ]

    def create(self, validated_data):
        request = self.context.get("request")

        user = (
            request.user.profile if request and request.user.is_authenticated else None
        )

        if not user:
            raise serializers.ValidationError(
                {"error": "User must be authenticated to create a bank type."}
            )

        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            raise serializers.ValidationError({"error": "Institution not found."})

        validated_data["institution"] = institution
        return super().create(validated_data)


class InstitutionBankAccountSerializer(BaseApprovableSerializer):
    institution_bank = serializers.PrimaryKeyRelatedField(
        queryset=InstitutionBankType.objects.all()
    )
    paid_branches = serializers.SerializerMethodField()

    class Meta:
        model = InstitutionBankAccount
        fields = [
            "id",
            "institution_bank",
            "account_name",
            "account_number",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "paid_branches",
            "is_active",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "paid_branches",
        ]

    paid_branches = serializers.SerializerMethodField()

    def get_paid_branches(self, obj):
        from .serializers import BranchSerializer

        return BranchSerializer(obj.paid_branches.all(), many=True).data

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["institution_bank"] = InstitutionBankTypeSerializer(
            instance.institution_bank
        ).data
        return rep


class InstitutionWorkingDaysSerializer(BaseApprovableSerializer):
    days = serializers.PrimaryKeyRelatedField(
        queryset=SystemDay.objects.all(),
        many=True,
    )

    class Meta:
        model = InstitutionWorkingDays
        fields = [
            "id",
            "institution",
            "days",
            "created_by",
            "created_at",
            "updated_by",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "institution",
            "created_by",
            "created_at",
            "updated_by",
            "updated_at",
        ]

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user.profile if request.user else None

        if not user:
            raise serializers.ValidationError({"error": "User has not profile"})

        try:
            institution = Institution.objects.get(id=user.institution.id)
        except Institution.DoesNotExist:
            raise serializers.ValidationError({"error": "Institution not found."})

        try:
            existing_working_days = InstitutionWorkingDays.objects.get(
                institution=institution
            )
            raise serializers.ValidationError(
                {"error": "Working days already exist for this institution."}
            )
        except InstitutionWorkingDays.DoesNotExist:
            pass

        created_by = request.user if request and request.user.is_authenticated else None

        validated_data["institution"] = institution
        validated_data["created_by"] = created_by

        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get("request")
        user = (
            request.user.profile if request and request.user.is_authenticated else None
        )

        if not user:
            raise serializers.ValidationError(
                {"error": "User must be authenticated to update working days."}
            )

        instance.days.set(validated_data.get("days", instance.days.all()))
        instance.updated_by = (
            request.user if request and request.user.is_authenticated else None
        )
        instance.save()

        return instance

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["days"] = SystemDaySerializer(instance.days, many=True).data
        return rep


class BranchDaySerializer(serializers.ModelSerializer):
    day_name = serializers.CharField(source="day.day_name", read_only=True)
    day_id = serializers.PrimaryKeyRelatedField(
        queryset=SystemDay.objects.all(), source="day", write_only=True, required=False
    )

    class Meta:
        model = BranchDay
        fields = ["id", "day_id", "day_name", "day_type"]


class BranchWorkingDaysSerializer(BaseApprovableSerializer):
    branch_days = BranchDaySerializer(many=True)

    class Meta:
        model = BranchWorkingDays
        fields = ["id", "branch", "branch_days"]
        read_only_fields = ["id", "branch"]

    def update(self, instance, validated_data):
        branch_days_data = validated_data.pop("branch_days", [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        instance.branch_days.all().delete()

        for bd_data in branch_days_data:
            day = bd_data.get("day")
            day_type = bd_data.get("day_type", "PHYSICAL")

            if not day:
                continue

            BranchDay.objects.create(
                branch_working_days=instance, day=day, day_type=day_type
            )

        instance.refresh_from_db()
        return instance





class BranchSerializer(BaseApprovableSerializer):
    institution_name = serializers.SerializerMethodField()
    institution_logo = serializers.ImageField(
        source="Institution.Institution_logo", read_only=True
    )

    class Meta:
        model = Branch
        fields = [
            "id",
            "institution",
            "paying_bank_account",
            "institution_name",
            "institution_logo",
            "branch_name",
            "branch_phone_number",
            "branch_location",
            "branch_latitude",
            "branch_longitude",
            "branch_email",
            "branch_opening_time",
            "branch_closing_time",
            "is_active",
        ]

    def get_institution_logo(self, obj):
        if (
            hasattr(obj, "institution")
            and obj.institution
            and obj.institution.institution_logo
        ):
            return obj.institution.institution_logo.url
        return None

    def get_institution_name(self, obj):
        if hasattr(obj, "institution") and obj.institution:
            return obj.institution.institution_name
        return None

    def create(self, validated_data):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError(
                {"error": "User must be authenticated to create a branch."}
            )
        validated_data["created_by"] = request.user
        return super().create(validated_data)


class InstitutionWithBranchesSerializer(InstitutionSerializer):
    branches = serializers.SerializerMethodField()

    class Meta(InstitutionSerializer.Meta):
        model = Institution
        fields = InstitutionSerializer.Meta.fields + ["branches"]

    def get_branches(self, institution):
        user = self.context.get("user")

        if user and institution.institution_owner == user:
            branches = institution.branches.all()
        else:
            user_branches = UserBranch.objects.filter(user=user).values_list(
                "branch_id", flat=True
            )
            branches = institution.branches.filter(id__in=user_branches)

        return BranchSerializer(branches, many=True).data


class UserBranchSerializer(serializers.ModelSerializer):
    user_details = CustomUserSerializer(source="user", read_only=True)
    branch_details = BranchSerializer(source="branch", read_only=True)

    class Meta:
        model = UserBranch
        fields = [
            "id",
            "user",
            "branch",
            "is_default",
            "user_details",
            "branch_details",
        ]

    def create(self, validated_data):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError(
                {"error": "User must be authenticated to create a user branch."}
            )
        return UserBranch.objects.create(created_by=request.user, **validated_data)


class DepartmentSerializer(BaseApprovableSerializer):
    institution_details = InstitutionSerializer(source="institution", read_only=True)


    class Meta:
        model = Department
        fields = [
            "id",
            "name",
            "description",
            "institution",
            # "",
            "institution_details",
        ]


class OwnerSerializer(serializers.Serializer):
    email = serializers.EmailField()
    full_name = serializers.CharField(max_length=255)
    phone_number = serializers.CharField(max_length=20, required=False)
    gender = serializers.ChoiceField(
        choices=[("male", "Male"), ("female", "Female"), ("other", "Other")],
        required=False,
        allow_blank=True,
    )


class BranchActivationSerializer(serializers.Serializer):
    branch_name = serializers.CharField(max_length=100)
    branch_location = serializers.CharField(max_length=200)
    branch_phone_number = serializers.CharField(max_length=20, required=False)
    branch_email = serializers.EmailField(required=False)


class DepartmentActivationSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(max_length=500, required=False)




class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField()
    message = serializers.CharField(required=False)
    details = serializers.JSONField(required=False)


class SuccessResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()
    data = serializers.DictField()


class InstitutionPenaltyConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstitutionPenaltyConfig
        fields = "__all__"
        extra_kwargs = {
            "penalty_type": {
                "error_messages": {
                    "unique": "This penalty type already exists for this institution."
                }
            }
        }
        validators = []  # ✅ disable DRF's auto UniqueTogetherValidator

    def validate(self, attrs):
        institution = attrs.get("institution") or self.instance.institution
        penalty_type = attrs.get("penalty_type") or self.instance.penalty_type

        if (
            InstitutionPenaltyConfig.objects.exclude(
                pk=getattr(self.instance, "pk", None)
            )
            .filter(institution=institution, penalty_type=penalty_type)
            .exists()
        ):
            raise serializers.ValidationError(
                {"error": "This penalty type already exists for this institution."}
            )
        return attrs


class BranchPenaltyConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = BranchPenaltyConfig
        fields = "__all__"
        validators = []  # ✅ disable DRF's auto UniqueTogetherValidator

    def validate(self, attrs):
        branch = attrs.get("branch") or self.instance.branch
        penalty_type = attrs.get("penalty_type") or self.instance.penalty_type

        if (
            BranchPenaltyConfig.objects.exclude(pk=getattr(self.instance, "pk", None))
            .filter(branch=branch, penalty_type=penalty_type)
            .exists()
        ):
            raise serializers.ValidationError(
                {"error": "This penalty type already exists for this branch."}
            )
        return attrs


class BranchLocationComparisonConfigSerializer(BaseApprovableSerializer):
    branch_name = serializers.CharField(source="branch.branch_name", read_only=True)

    class Meta:
        model = BranchLocationComparisonConfig
        fields = "__all__"





class AIAssistantSerializer(serializers.Serializer):
    question = serializers.CharField(required=True, allow_blank=False, write_only=True)
    answer = serializers.CharField(read_only=True)
    session_id = serializers.CharField(max_length=100, required=False)
    chat_id = serializers.UUIDField(required=False)

    def validate(self, attrs):
        if not self.instance and not attrs.get("question"):
            raise serializers.ValidationError({"error": "Question is required."})
        return attrs


class AIChatMessageSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=["user", "assistant"])
    message = serializers.CharField()
    timestamp = serializers.DateTimeField()


class AIChatSerializer(serializers.Serializer):
    chat_id = serializers.UUIDField()
    title = serializers.CharField()
    messages = AIChatMessageSerializer(many=True)


class UserChatsSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    chats = AIChatSerializer(many=True)
