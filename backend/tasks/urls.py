from django.urls import path
from .views import (
    StandaloneTaskListCreateView,
    StandaloneTaskDetailView,
    StandaloneTaskStatusListCreateView,
    StandaloneTaskStatusDetailView,
    StandaloneTaskPriorityListCreateView,
    StandaloneTaskPriorityDetailView,
    StandaloneTaskMessageListCreateApiView,
    StandaloneTaskMessageDetailApiView,
    StandaloneTaskExtensionRequestListCreateView,
    StandaloneTaskExtensionRequestDetail,
    StandaloneTaskDisscusionParticipantListCreateApiView,
    StandaloneTasskDisscusionParticipantDetailsApiView,
    StandaloneTaskExtensionRequestApprove,
    StandaloneTaskExtensionRequestReject,
    SetTaskStatusDefaultsView,
    StandaloneTaskTimeSheetView,
    StandaloneTaskEmailConfigListCreateView,
    StandaloneTaskEmailConfigDetailView,
    StandaloneTaskProgressStatus,
)

urlpatterns = [
    path(
        "tasks/", StandaloneTaskListCreateView.as_view(), name="task-list-create"
    ),
    path("tasks/<int:pk>/details/", StandaloneTaskDetailView.as_view(), name="task-detail"),
    path(
        "start-end-task/<int:task_timesheet_id>/",
        StandaloneTaskTimeSheetView.as_view(),
        name="task-timesheet",
    ),
    path("task-status/", StandaloneTaskStatusListCreateView.as_view(), name="task-status"),
    path("task-status/<int:pk>/details/", StandaloneTaskStatusDetailView.as_view(), name="task-status-detail"),
    path("task-priority/", StandaloneTaskPriorityListCreateView.as_view(), name="task-priority"),
    path("task-priority/<int:pk>/details/", StandaloneTaskPriorityDetailView.as_view(), name="task-prioriy-detail"),
    path("task-messages/", StandaloneTaskMessageListCreateApiView.as_view(), name="task-messages"),
    path("task-messages/<int:pk>/", StandaloneTaskMessageDetailApiView.as_view(), name="task-messages-detail"),
    path("task-extension/", StandaloneTaskExtensionRequestListCreateView.as_view(), name="task-extension"),
    path("task-extension/<int:pk>/", StandaloneTaskExtensionRequestDetail.as_view(), name="task-extension-detail"),
    path("task-extension/approve/", StandaloneTaskExtensionRequestApprove.as_view(), name="task-extension-approve"),
    path("task-extension/reject/", StandaloneTaskExtensionRequestReject.as_view(), name="task-extension-reject"),
    path("task-discussion-participant/", StandaloneTaskDisscusionParticipantListCreateApiView.as_view(), name="task-discussion-participant"),
    path("task-discussion-participant/<int:pk>/details/", StandaloneTasskDisscusionParticipantDetailsApiView.as_view(), name="task-discussion-participant-detail"),
    path("default-task-status/", SetTaskStatusDefaultsView.as_view(), name="standalone-task-status"),
    path("task-config/", StandaloneTaskEmailConfigListCreateView.as_view(), name="task-config"),
    path("task-config/<int:pk>/details/", StandaloneTaskEmailConfigDetailView.as_view(), name="task-config-detail"),
    path("task-state/", StandaloneTaskProgressStatus.as_view(), name="task-state"),
]

