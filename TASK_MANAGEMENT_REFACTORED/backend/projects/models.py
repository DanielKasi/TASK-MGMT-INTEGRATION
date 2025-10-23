from django.db import models, transaction
from django.utils import timezone
from django.db.models import UniqueConstraint, Q, JSONField
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


    
class ProjectStatus(BaseModel, BaseApprovableModel):
    institution = models.ForeignKey("institution.Institution", on_delete=models.CASCADE)
    status_name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    weight = models.PositiveIntegerField(default=1)
    color_code = models.CharField(max_length=7, default="#9C9C9C")  


    def __str__(self):
        return self.status_name
    
    def get_institution(self):
        return self.institution

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Project Statuses"
        verbose_name = "Project Status"

class Project(BaseModel, BaseApprovableModel):

    institution = models.ForeignKey(
        "institution.Institution",
        on_delete=models.CASCADE,
        related_name="projects",
        null=True,
        blank=True,
    )

    project_name = models.CharField(max_length=255, blank=False)
    completion_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    milestones = JSONField(default=dict, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    user_manager = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_projects",
        help_text="Single manager for this Project"
    )
    custom_fields = models.JSONField(default=list, null=True, blank=True)
    completed_status = models.ForeignKey(
        "projects.ProjectTaskStatus",
        on_delete=models.CASCADE,
        related_name="project_completed_status",
        null=True,
        blank=True,
    )
    failed_status = models.ForeignKey(
        "projects.ProjectTaskStatus",
        on_delete=models.CASCADE,
        related_name="project_failed_status",
        null=True,
        blank=True,
    )

    project_status = models.ForeignKey(
        ProjectStatus,
        on_delete=models.CASCADE,
        related_name="projects",
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"Project: {self.project_name} under ({self.institution})"

    def get_institution(self):
        return self.institution      

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Projects"
        verbose_name = "Project"
        constraints = [
            UniqueConstraint(
                fields=["institution", "project_name"],
                condition=Q(deleted_at__isnull=True),
                name="unique_active_project_name_per_institution"
            )
        ]

    
class ProjectUserAssignees(BaseModel):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="user_assignees",
    )
    user_assigned = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="assigned_projects",
    )

    class Meta:
        verbose_name_plural = "Project User Assignees"
        constraints = [
            models.UniqueConstraint(
                fields=["project", "user_assigned"],
                name="unique_project_user_assignee"
            )
        ]

class ProjectStaffGroupAssignees(BaseModel):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="staff_group_assignees",
    )
    group_assigned = models.ForeignKey(
        StaffGroup,
        on_delete=models.CASCADE,
        related_name="assigned_projects",
    )

    class Meta:
        verbose_name_plural = "Project Staff Group Assignees"
        constraints = [
            models.UniqueConstraint(
                fields=["project", "group_assigned"],
                name="unique_project_staff_group_assignee"
            )
        ]             

class ProjectDocument(BaseModel, BaseApprovableModel):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    name = models.CharField(max_length=255, blank=False)
    document = models.FileField(upload_to="project_documents/")

    def __str__(self):
        return f"Document for Project: {self.project.project_name} ({self.project.institution})"

    def get_institution(self):
        return self.project.institution      

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Project Documents"
        verbose_name = "Project Document"
        indexes = [
            models.Index(fields=["project"]),
        ]

class ProjectTaskStatus(BaseModel, BaseApprovableModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="project_task_statuses")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    weight = models.PositiveIntegerField(default=1)
    color_code = models.CharField(max_length=7, default="#9C9C9C")  


    def __str__(self):
        return self.name
    
    def get_project(self):
        return self.project

    def get_institution(self):
        return self.project.institution

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Project Task Statuses"
        verbose_name = "Project Task Status"


class TaskPriority(BaseModel, BaseApprovableModel):
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
        verbose_name_plural = "Task Priorities"
        verbose_name = "Task Priority"        

class Task(BaseModel, BaseApprovableModel):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks",
        null=True,
        blank=True,
    )

    task_name = models.CharField(max_length=255, blank=False)
    description = models.TextField(blank=True)

    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    freeze_assignee = models.BooleanField(default=False)
    custom_fields = models.JSONField(default=list, null=True, blank=True)

    applied_project_task_status = models.ForeignKey(
        ProjectTaskStatus,
        on_delete=models.CASCADE,
        related_name="project_tasks_status",
        null=True,        
        blank=True,
    )
    user_manager = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_tasks",
        help_text="Single manager for this task"
    )

    priority = models.ForeignKey(
        TaskPriority,
        on_delete=models.CASCADE,
        related_name="tasks",
        null=True,        blank=True,
    )

    def __str__(self):
        return f"Task: {self.task_name}"

    def get_institution(self):
        return self.user_manager.profile.institution

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Project Tasks"
        verbose_name = "Project Task"
        constraints = [
            UniqueConstraint(
                fields=["project", "task_name"],
                condition=Q(deleted_at__isnull=True),
                name="unique_active_task_name_per_project"
            )
        ]

    def finish_workflow(self, approval: Approval):
        with transaction.atomic():
            if approval.status == "completed":
                if approval.action.name == "create":
                    self.is_active = True
                    self.deleted_at = None

                    if not hasattr(self, "timesheet"):
                        TaskTimeSheet.objects.create(
                            task=self,
                            created_by=self.created_by
                            )
                elif approval.action.name == "update":
                    if hasattr(self, "timesheet"):
                        timesheet = self.timesheet
                        current_status = self.applied_project_task_status.name if self.applied_project_task_status else None

                        if current_status == "in_progress" and timesheet.start_time is None:
                            timesheet.start_time = timezone.now()
                            timesheet.save()
                        elif current_status == "completed" and timesheet.end_time is None:
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

class TaskUserAssignees(BaseModel):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="user_assignees",
    )
    user_assigned = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="assigned_tasks",
    )

    class Meta:
        verbose_name_plural = "Task User Assignees"
        constraints = [
            models.UniqueConstraint(
                fields=["task", "user_assigned"],
                name="unique_task_user_assignee"
            )
        ]

class TaskStaffGroupAssignees(BaseModel):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="staff_group_assignees",
    )
    group_assigned = models.ForeignKey(
        StaffGroup,
        on_delete=models.CASCADE,
        related_name="assigned_group_tasks",
    )

    class Meta:
        verbose_name_plural = "Task Staff Group Assignees"
        constraints = [
            models.UniqueConstraint(
                fields=["task", "group_assigned"],
                name="unique_task_staff_group_assignee"
            )
        ] 

class TaskDocument(BaseModel, BaseApprovableModel):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    name = models.CharField(max_length=255, blank=False)

    document = models.FileField(upload_to="task_documents/")

    def __str__(self):
        return f"Document for Task: {self.task.task_name} in Project: {self.task.project.project_name} ({self.task.project.institution})"

    def get_institution(self):
        return self.task.project.institution      

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Task Documents"
        verbose_name = "Task Document"
        indexes = [
            models.Index(fields=["task"]),
        ]


class TaskTimeSheet(BaseModel, BaseApprovableModel):
    task = models.OneToOneField(
        Task,
        on_delete=models.CASCADE,
        related_name="timesheet",
    )

    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)

    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Timesheet for Task: {self.task.task_name} by {self.created_by.user.email if self.created_by else 'Unknown'} in Project: {self.task.project.project_name if self.task.project else None} ({self.task.project.institution if self.task.project else None})"
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
        return self.task.project.institution      

class TaskMessage(BaseModel, BaseApprovableModel):
    institution = models.ForeignKey("institution.Institution", on_delete=models.CASCADE)
    task = models.ForeignKey(
        Task, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="task_messages",
        help_text="User who sent the message "
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
        return self.task.project.institution

class ProjectMessage(BaseModel, BaseApprovableModel):
    institution = models.ForeignKey("institution.Institution", on_delete=models.CASCADE)
    project = models.ForeignKey(
        Project, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_messages",
        help_text="User who sent the message "
    )
    content = models.TextField(
        validators=[MaxLengthValidator(2000)],
        help_text="Message content (max 2000 characters)"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project', 'created_at']),
        ]
    
    def get_institution(self):
        return self.project.institution

class TaskDiscussionParticipant(BaseModel, BaseApprovableModel):
    task = models.ForeignKey(
        Task,  
        on_delete=models.CASCADE,
        related_name='discussion_participants'
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='task_discussion_participations'
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
        verbose_name = "Task Discussion Participant"
        verbose_name_plural = "Task Discussion Participants"

    def __str__(self):
        return f"{self.user.email} in {self.task}"
    
    def get_institution(self):
        return self.task.project.institution


class ProjectDiscussionParticipant(BaseModel, BaseApprovableModel):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='participants'
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='project_discussion_participations'
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
        unique_together = ('project', 'user')
        verbose_name = "Project Discussion Participant"
        verbose_name_plural = "Project Discussion Participants"

    def get_institution(self):
        return self.project.institution

    def __str__(self):
        return f"{self.user.email} in {self.project}"


class TaskExtensionRequest(BaseModel, BaseApprovableModel):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="extension_requests")
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
        return self.task.project.institution
    

class ProjectTaskEmailConfig(BaseApprovableModel):
    class Intent(models.TextChoices):
        FAILURE = "failure", "Failure"
        COMPLETION = "completion", "Completion"

    project = models.ForeignKey(
        'projects.Project', on_delete=models.PROTECT,
        related_name='project_task_email_configs'
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
        verbose_name = "Project Task Email Config"
        verbose_name_plural = " Project Task Email Configs"
        constraints = [
            models.UniqueConstraint(
                fields=['project', 'intent'],
                name='unique_email_config_per_project_task_intent'
            )
        ]
    
    def get_institution(self):
        return self.project.institution