from django.db import models, transaction
from django.utils import timezone
from django.db.models import UniqueConstraint, Q
from approval.models import Approval, BaseApprovableModel
from users.models import CustomUser, StaffGroup
from django.core.validators import MaxLengthValidator


class BaseModel(models.Model):
    created_by = models.ForeignKey(
        "users.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created_by",
    )
    updated_by = models.ForeignKey(
        "users.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_updated_by",
    )

    class Meta:
        abstract = True


class StandaloneTaskStatus(BaseModel, BaseApprovableModel):
    institution = models.ForeignKey("institution.Institution", on_delete=models.CASCADE)
    task = models.ForeignKey("tasks.StandaloneTask", on_delete=models.CASCADE, related_name="standalone_task_statuses", null=True, blank=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    weight = models.PositiveIntegerField(default=1)
    color_code = models.CharField(max_length=7, default="#9C9C9C")

    def __str__(self):
        return self.name

    def get_institution(self):
        return self.institution

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Standalone Task Statuses"
        verbose_name = "Standalone Task Status"


class StandaloneTaskPriority(BaseModel, BaseApprovableModel):
    institution = models.ForeignKey("institution.Institution", on_delete=models.CASCADE)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    weight = models.PositiveIntegerField(default=1)
    color_code = models.CharField(max_length=7, default="#9C9C9C")

    def __str__(self):
        return self.name

    def get_institution(self):
        return self.institution

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Standalone Task Priorities"
        verbose_name = "Standalone Task Priority"


class StandaloneTask(BaseModel, BaseApprovableModel):
    task_name = models.CharField(max_length=255, blank=False)
    description = models.TextField(blank=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    freeze_assignee = models.BooleanField(default=False)
    custom_fields = models.JSONField(default=list, null=True, blank=True)

    applied_task_status = models.ForeignKey(
        StandaloneTaskStatus,
        on_delete=models.CASCADE,
        related_name="standalone_tasks_status",
        null=True,
        blank=True,
    )
    user_manager = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_standalone_tasks",
        help_text="Single manager for this task"
    )
    completed_status = models.ForeignKey(
        "tasks.StandaloneTaskStatus",
        on_delete=models.CASCADE,
        related_name="standalone_completed_tasks",  
        null=True,
        blank=True,
    )
    failed_status = models.ForeignKey(
        "tasks.StandaloneTaskStatus",
        on_delete=models.CASCADE,
        related_name="standalone_failed_tasks",  
        null=True,
        blank=True,
    )

    priority = models.ForeignKey(
        StandaloneTaskPriority,
        on_delete=models.CASCADE,
        related_name="standalone_tasks",
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"Task: {self.task_name}"

    def get_institution(self):
        if self.user_manager and hasattr(self.user_manager, 'profile'):
            return self.user_manager.profile.institution
        return None

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Standalone Tasks"
        verbose_name = "Standalone Task"
        # Removed invalid constraint that referenced non-existent 'project' field
        # constraints = [...]  ← DELETED

    def finish_workflow(self, approval: Approval):
        with transaction.atomic():
            if approval.status == "completed":
                if approval.action.name == "create":
                    self.is_active = True
                    self.deleted_at = None

                    if not hasattr(self, "timesheet"):
                        StandaloneTaskTimeSheet.objects.create(
                            task=self,
                            created_by=self.created_by
                        )
                elif approval.action.name == "update":
                    if hasattr(self, "timesheet"):
                        timesheet = self.timesheet
                        current_status_name = self.applied_task_status.name if self.applied_task_status else None
                        if current_status_name == "in_progress" and timesheet.start_time is None:
                            timesheet.start_time = timezone.now()
                            timesheet.save()
                        elif current_status_name == "completed" and timesheet.end_time is None:
                            timesheet.end_time = timezone.now()
                            self.completion_date = timezone.now().date()
                            self.save(update_fields=["completion_date"])
                            timesheet.save()

                elif approval.action.name == "delete":
                    self.is_active = False
                    self.deleted_at = timezone.now()
                    self.save()

            elif approval.status == "rejected":
                if approval.action.name == "create":
                    self.approval_status = "active"
                    self.is_active = False
                    self.deleted_at = None
                elif approval.action.name == "update":
                    self.approval_status = "active"
                    self.is_active = True
                    self.deleted_at = None
                elif approval.action.name == "delete":
                    self.approval_status = "active"
                    self.is_active = True
                    self.deleted_at = None

            self.save(
                update_fields=[
                    "approval_status",
                    "is_active",
                    "deleted_at",
                ]
            )

    @property
    def progress_status(self):
        now = timezone.now()
        completed = self.completion_date is not None
        start = self.start_date
        end = self.end_date

        if completed:
            return "completed"

        if end and end < now:
            return "overdue"

        if start is None or start > now:
            return "not_started"

        return "in_progress"

    @property
    def progress_status_display(self):
        return {
            "completed": "Completed",
            "overdue": "Overdue",
            "not_started": "Not Started",
            "in_progress": "In Progress"
        }[self.progress_status]


class StandaloneTaskUserAssignees(BaseModel):
    task = models.ForeignKey(
        StandaloneTask,
        on_delete=models.CASCADE,
        related_name="user_assignees",
    )
    user_assigned = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="standalone_assigned_tasks",  
    )

    class Meta:
        verbose_name_plural = "Standalone Task User Assignees"
        constraints = [
            models.UniqueConstraint(
                fields=["task", "user_assigned"],
                name="unique_standalone_task_user_assignee"  
            )
        ]


class StandaloneTaskStaffGroupAssignees(BaseModel):
    task = models.ForeignKey(
        StandaloneTask,
        on_delete=models.CASCADE,
        related_name="staff_group_assignees",
    )
    group_assigned = models.ForeignKey(
        StaffGroup,
        on_delete=models.CASCADE,
        related_name="standalone_assigned_group_tasks",  
    )

    class Meta:
        verbose_name_plural = "Standalone Task Staff Group Assignees"
        constraints = [
            models.UniqueConstraint(
                fields=["task", "group_assigned"],
                name="unique_standalone_task_staff_group_assignee"  
            )
        ]


class StandaloneTaskDocument(BaseModel, BaseApprovableModel):
    task = models.ForeignKey(
        StandaloneTask,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    name = models.CharField(max_length=255, blank=False)
    document = models.FileField(upload_to="task_documents/")

    def __str__(self):
        return f"Document for Standalone Task: {self.task.task_name}"

    def get_institution(self):
        if self.task.user_manager and hasattr(self.task.user_manager, 'profile'):
            return self.task.user_manager.profile.institution
        return None

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Standalone Task Documents"
        verbose_name = "Standalone Task Document"
        indexes = [
            models.Index(fields=["task"]),
        ]


class StandaloneTaskTimeSheet(BaseModel, BaseApprovableModel):
    task = models.OneToOneField(
        StandaloneTask,
        on_delete=models.CASCADE,
        related_name="timesheet",
    )
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        created_by_email = self.created_by.user.email if self.created_by and self.created_by.user else 'Unknown'
        return f"Timesheet for Standalone Task: {self.task.task_name} by {created_by_email}"

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Time Sheets"
        verbose_name = "Time Sheet"

    @property
    def timespent(self):
        return (
            self.end_time - self.start_time
            if self.end_time and self.start_time
            else None
        )

    def get_institution(self):
        if self.task.user_manager and hasattr(self.task.user_manager, 'profile'):
            return self.task.user_manager.profile.institution
        return None


class StandaloneTaskMessage(BaseModel, BaseApprovableModel):
    institution = models.ForeignKey("institution.Institution", on_delete=models.CASCADE)
    task = models.ForeignKey(
        StandaloneTask,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="standalone_task_messages",  
        help_text="User who sent the message"
    )
    content = models.TextField(
        validators=[MaxLengthValidator(2000)],
        help_text="Message content (max 2000 characters)"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['task', 'created_at']),
        ]

    def get_institution(self):
        return self.institution

class StandaloneTaskDiscussionParticipant(BaseModel, BaseApprovableModel):
    task = models.ForeignKey(
        StandaloneTask,
        on_delete=models.CASCADE,
        related_name='discussion_participants'
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="standalone_task_discussion_participations",  
    )
    can_send = models.BooleanField(
        default=False,
        help_text="If False, user can only view messages."
    )
    added_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        unique_together = ('task', 'user')
        verbose_name = "Standalone Task Discussion Participant"
        verbose_name_plural = "Standalone Task Discussion Participants"

    def __str__(self):
        return f"{self.user.email} in {self.task}"
    
    def get_institution(self):
        if self.task.user_manager and hasattr(self.task.user_manager, 'profile'):
            return self.task.user_manager.profile.institution
        return None


class StandaloneTaskExtensionRequest(BaseModel, BaseApprovableModel):
    task = models.ForeignKey(StandaloneTask, on_delete=models.CASCADE, related_name="extension_requests")
    requested_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    institution = models.ForeignKey("institution.Institution", on_delete=models.CASCADE)
    request_reason = models.TextField(blank=True)
    approved = models.BooleanField(default=False)
    accepted = models.BooleanField(default=False, null=True, blank=True)
    approval_reason = models.TextField(blank=True, null=True)
    new_start_date = models.DateTimeField(null=True, blank=True)
    new_end_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Extension for {self.task.task_name}"
    
    def get_institution(self):
        if self.task.user_manager and hasattr(self.task.user_manager, 'profile'):
            return self.task.user_manager.profile.institution
        return None
    

class StandaloneTaskEmailConfig(BaseApprovableModel):
    class Intent(models.TextChoices):
        FAILURE = "failure", "Failure"
        COMPLETION = "completion", "Completion"

    task = models.ForeignKey(
        'tasks.StandaloneTask', on_delete=models.PROTECT,
        related_name='email_configs'
    )

    intent = models.CharField(
        max_length=20,
        choices=Intent.choices,
    )

    task_issuer = models.BooleanField(default=False)
    task_leader = models.BooleanField(default=False)
    task_assignees = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Task Email Config"
        verbose_name_plural = "Task Email Configs"
        constraints = [
            models.UniqueConstraint(
                fields=['task', 'intent'],
                name='unique_email_config_per_task_intent'
            )
        ]
        
    def get_institution(self):
        if self.task.user_manager and hasattr(self.task.user_manager, 'profile'):
            return self.task.user_manager.profile.institution
        return None