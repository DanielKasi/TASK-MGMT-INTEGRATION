from django.contrib import admin
from .models import (
    StandaloneTask,
    StandaloneTaskDocument,
    StandaloneTaskTimeSheet,
    StandaloneTaskPriority,
    StandaloneTaskStaffGroupAssignees,
    StandaloneTaskStatus,
    StandaloneTaskUserAssignees,
    StandaloneTaskMessage,
    StandaloneTaskExtensionRequest,
    StandaloneTaskDiscussionParticipant,
    StandaloneTaskEmailConfig,
) 


admin.site.register(StandaloneTask)
admin.site.register(StandaloneTaskDocument)
admin.site.register(StandaloneTaskTimeSheet)
admin.site.register(StandaloneTaskUserAssignees)
admin.site.register(StandaloneTaskStaffGroupAssignees)
admin.site.register(StandaloneTaskStatus)
admin.site.register(StandaloneTaskPriority)
admin.site.register(StandaloneTaskMessage)
admin.site.register(StandaloneTaskExtensionRequest)
admin.site.register(StandaloneTaskDiscussionParticipant)
admin.site.register(StandaloneTaskEmailConfig)