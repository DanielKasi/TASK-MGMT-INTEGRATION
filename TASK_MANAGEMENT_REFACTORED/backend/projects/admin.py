from django.contrib import admin
from .models import (
    Project,
    Task,
    TaskDocument,
    TaskTimeSheet,
    ProjectDocument,
    ProjectStaffGroupAssignees,
    ProjectStatus,
    ProjectUserAssignees,
    TaskPriority,
    TaskStaffGroupAssignees,
    TaskUserAssignees,
    TaskMessage,
    ProjectMessage,
    TaskExtensionRequest,
    ProjectTaskStatus,
    TaskDiscussionParticipant,
    ProjectDiscussionParticipant,
    ProjectTaskEmailConfig,
) 


admin.site.register(Project)
admin.site.register(Task)
admin.site.register(TaskDocument)
admin.site.register(TaskTimeSheet)
admin.site.register(ProjectDocument)
admin.site.register(ProjectUserAssignees)
admin.site.register(ProjectStaffGroupAssignees)
admin.site.register(ProjectStatus)
admin.site.register(TaskUserAssignees)
admin.site.register(TaskStaffGroupAssignees)
admin.site.register(TaskPriority)
admin.site.register(TaskMessage)
admin.site.register(ProjectMessage)
admin.site.register(TaskExtensionRequest)
admin.site.register(ProjectTaskStatus)
admin.site.register(ProjectDiscussionParticipant)
admin.site.register(TaskDiscussionParticipant)
admin.site.register(ProjectTaskEmailConfig)