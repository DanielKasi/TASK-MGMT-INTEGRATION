#!/bin/bash

# Script to revert platform imports back to original paths
# This will fix the build errors by reverting custom component imports

echo "Reverting platform imports back to original paths..."

# Find all files that import from platform/v1/components and revert specific components
find src -name "*.tsx" -o -name "*.ts" | xargs grep -l "from \"@/platform/v1/components\"" | while read file; do
    echo "Processing $file..."
    
    # Revert specific component imports
    sed -i 's/import { ConfirmationDialog } from "@\/platform\/v1\/components";/import { ConfirmationDialog } from "@\/components\/confirmation-dialog";/g' "$file"
    sed -i 's/import { RichTextEditor } from "@\/platform\/v1\/components";/import RichTextEditor from "@\/components\/editor\/rich-text-editor";/g' "$file"
    sed -i 's/import { RichTextDisplay } from "@\/platform\/v1\/components";/import { RichTextDisplay } from "@\/components\/common\/rich-text-display";/g' "$file"
    sed -i 's/import { MultiSelectPopover } from "@\/platform\/v1\/components";/import { MultiSelectPopover } from "@\/components\/common\/multi-select-popover";/g' "$file"
    sed -i 's/import { PaginatedTable } from "@\/platform\/v1\/components";/import { PaginatedTable } from "@\/components\/PaginatedTable";/g' "$file"
    sed -i 's/import { TableSkeleton } from "@\/platform\/v1\/components";/import { TableSkeleton } from "@\/components\/common\/table-skeleton";/g' "$file"
    sed -i 's/import { LoadingComponent } from "@\/platform\/v1\/components";/import LoadingComponent from "@\/components\/LoadingComponent";/g' "$file"
    sed -i 's/import { PhoneNumberInput } from "@\/platform\/v1\/components";/import PhoneNumberInput from "@\/components\/phone-number-input";/g' "$file"
    sed -i 's/import { LocationAutocomplete } from "@\/platform\/v1\/components";/import { LocationAutocomplete } from "@\/components\/location-autocomplete";/g' "$file"
    sed -i 's/import { Steps } from "@\/platform\/v1\/components";/import { Steps } from "@\/components\/generic\/steps";/g' "$file"
    sed -i 's/import { TasksCards } from "@\/platform\/v1\/components";/import { TasksCards } from "@\/components\/dashboard-tasks";/g' "$file"
    sed -i 's/import { MetricCards } from "@\/platform\/v1\/components";/import { MetricCards } from "@\/components\/dashboard\/metric-cards";/g' "$file"
    sed -i 's/import { AnnouncementCarousel } from "@\/platform\/v1\/components";/import AnnouncementCarousel from "@\/components\/dashboard\/announcements-carousel";/g' "$file"
    sed -i 's/import { SimpleCalendarWidget } from "@\/platform\/v1\/components";/import { SimpleCalendarWidget } from "@\/components\/calendar-widget";/g' "$file"
    sed -i 's/import { RedirectsWatcher } from "@\/platform\/v1\/components";/import RedirectsWatcher from "@\/components\/common\/redirects-watcher";/g' "$file"
    sed -i 's/import { DashboardSideBar } from "@\/platform\/v1\/components";/import DashboardSideBar from "@\/components\/dashboard\/dashboard-sidebar";/g' "$file"
    sed -i 's/import { InstitutionBranchSelector } from "@\/platform\/v1\/components";/import { InstitutionBranchSelector } from "@\/components\/institution-branch-selector";/g' "$file"
    sed -i 's/import { AIAssistantWidget } from "@\/platform\/v1\/components";/import AIAssistantWidget from "@\/components\/ai-assistant-widget";/g' "$file"
    sed -i 's/import { TaskAuditTrail } from "@\/platform\/v1\/components";/import { TaskAuditTrail } from "@\/components\/projects\/tasks\/task-audit-log";/g' "$file"
    sed -i 's/import { RelatedUserSearchableSelect } from "@\/platform\/v1\/components";/import RelatedUserSearchableSelect from "@\/components\/selects\/related-user-searchable-select";/g' "$file"
    sed -i 's/import { StaffGroupsSearchableSelect } from "@\/platform\/v1\/components";/import StaffGroupsSearchableSelect from "@\/components\/selects\/staff-groups-searchable-select";/g' "$file"
    sed -i 's/import { CustomFieldsModal } from "@\/platform\/v1\/components";/import { CustomFieldsModal } from "@\/components\/common\/dialogs\/project-custom-fields-dialog";/g' "$file"
    sed -i 's/import { ProjectTaskStatusDialog } from "@\/platform\/v1\/components";/import { ProjectTaskStatusDialog } from "@\/components\/common\/dialogs\/project-task-status-dialog";/g' "$file"
    sed -i 's/import { ProjectTaskPriorityDialog } from "@\/platform\/v1\/components";/import { ProjectTaskPriorityDialog } from "@\/components\/common\/dialogs\/create-project-task-priority-dilog";/g' "$file"
    sed -i 's/import { TaskPriorityDialog } from "@\/platform\/v1\/components";/import { TaskPriorityDialog } from "@\/components\/common\/dialogs\/create-task-priority-dialog";/g' "$file"
    sed -i 's/import { TaskStatusDialog } from "@\/platform\/v1\/components";/import { TaskStatusDialog } from "@\/components\/common\/dialogs\/task-statuses-dialog";/g' "$file"
    sed -i 's/import { StandaloneTaskDialog } from "@\/platform\/v1\/components";/import StandaloneTaskDialog from "@\/components\/tasks\/tasks-dialog";/g' "$file"
    sed -i 's/import { UserGroupDialog } from "@\/platform\/v1\/components";/import { UserGroupDialog } from "@\/components\/common\/dialogs\/create-staff-groups-dialog";/g' "$file"
    sed -i 's/import { PermissionDenied } from "@\/platform\/v1\/components";/import PermissionDenied from "@\/components\/PermissionDenied";/g' "$file"
    sed -i 's/import { DraggableTaskCard } from "@\/platform\/v1\/components";/import { DraggableTaskCard } from "@\/components\/common\/draggable-task-card";/g' "$file"
    sed -i 's/import { AddUsersToChatDialog } from "@\/platform\/v1\/components";/import AddUsersToChatDialog from "@\/components\/common\/dialogs\/add-users-to-chat-dialog";/g' "$file"
    sed -i 's/import { ManageParticipantsDialog } from "@\/platform\/v1\/components";/import ManageParticipantsDialog from "@\/components\/common\/dialogs\/manage-task-chat-participants-dialog";/g' "$file"
    sed -i 's/import { DialogSkeleton } from "@\/platform\/v1\/components";/import DialogSkeleton from "@\/components\/dialogs\/dialog-skeleton";/g' "$file"
    sed -i 's/import { TaskStatusSearchableSelect } from "@\/platform\/v1\/components";/import TaskStatusSearchableSelect from "@\/components\/tasks\/selects\/tasks-configuration-searchable-select";/g' "$file"
    sed -i 's/import { UserSearchableSelect } from "@\/platform\/v1\/components";/import UserSearchableSelect from "@\/components\/selects\/user-searchable-select";/g' "$file"
    sed -i 's/import { RoleSearchableSelect } from "@\/platform\/v1\/components";/import RoleSearchableSelect from "@\/components\/selects\/role-searchable-select";/g' "$file"
    sed -i 's/import { UserProfileSearchableSelect } from "@\/platform\/v1\/components";/import UserProfileSearchableSelect from "@\/components\/selects\/user-profile-searchable-select";/g' "$file"
    sed -i 's/import { ApprovalWorkflow } from "@\/platform\/v1\/components";/import { ApprovalWorkflow } from "@\/components\/approvals\/approval-workflow";/g' "$file"
    
    # Revert default imports
    sed -i 's/import RoleSearchableSelect from "@\/platform\/v1\/components";/import RoleSearchableSelect from "@\/components\/selects\/role-searchable-select";/g' "$file"
    sed -i 's/import UserProfileSearchableSelect from "@\/platform\/v1\/components";/import UserProfileSearchableSelect from "@\/components\/selects\/user-profile-searchable-select";/g' "$file"
    sed -i 's/import RelatedUserSearchableSelect from "@\/platform\/v1\/components";/import RelatedUserSearchableSelect from "@\/components\/selects\/related-user-searchable-select";/g' "$file"
    sed -i 's/import StaffGroupsSearchableSelect from "@\/platform\/v1\/components";/import StaffGroupsSearchableSelect from "@\/components\/selects\/staff-groups-searchable-select";/g' "$file"
    sed -i 's/import UserSearchableSelect from "@\/platform\/v1\/components";/import UserSearchableSelect from "@\/components\/selects\/user-searchable-select";/g' "$file"
    sed -i 's/import TaskStatusSearchableSelect from "@\/platform\/v1\/components";/import TaskStatusSearchableSelect from "@\/components\/tasks\/selects\/tasks-configuration-searchable-select";/g' "$file"
    sed -i 's/import PaginatedSearchableSelect from "@\/platform\/v1\/components";/import PaginatedSearchableSelect from "@\/components\/generic\/paginated-searchable-select";/g' "$file"
done

echo "Reverted platform imports. Running build..."
