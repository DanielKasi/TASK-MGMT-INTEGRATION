#!/bin/bash

# Script to fix remaining import issues
echo "Fixing remaining import issues..."

# Fix RichTextDisplay imports
find src -name "*.tsx" -o -name "*.ts" | xargs sed -i 's/import {RichTextDisplay} from "@\/platform\/v1\/components";/import { RichTextDisplay } from "@\/components\/common\/rich-text-display";/g'

# Fix other remaining platform imports
find src -name "*.tsx" -o -name "*.ts" | xargs sed -i 's/import { PaginatedTable } from "@\/platform\/v1\/components";/import { PaginatedTable } from "@\/components\/PaginatedTable";/g'
find src -name "*.tsx" -o -name "*.ts" | xargs sed -i 's/import { PaginatedTableWrapper } from "@\/platform\/v1\/components";/import { PaginatedTableWrapper } from "@\/components\/PaginatedTable";/g'
find src -name "*.tsx" -o -name "*.ts" | xargs sed -i 's/import LoadingComponent from "@\/platform\/v1\/components";/import LoadingComponent from "@\/components\/LoadingComponent";/g'
find src -name "*.tsx" -o -name "*.ts" | xargs sed -i 's/import PhoneNumberInput from "@\/platform\/v1\/components";/import PhoneNumberInput from "@\/components\/phone-number-input";/g'
find src -name "*.tsx" -o -name "*.ts" | xargs sed -i 's/import { Steps } from "@\/platform\/v1\/components";/import { Steps } from "@\/components\/generic\/steps";/g'
find src -name "*.tsx" -o -name "*.ts" | xargs sed -i 's/import AnnouncementCarousel from "@\/platform\/v1\/components";/import AnnouncementCarousel from "@\/components\/dashboard\/announcements-carousel";/g'
find src -name "*.tsx" -o -name "*.ts" | xargs sed -i 's/import RedirectsWatcher from "@\/platform\/v1\/components";/import RedirectsWatcher from "@\/components\/common\/redirects-watcher";/g'
find src -name "*.tsx" -o -name "*.ts" | xargs sed -i 's/import DashboardSideBar from "@\/platform\/v1\/components";/import DashboardSideBar from "@\/components\/dashboard\/dashboard-sidebar";/g'
find src -name "*.tsx" -o -name "*.ts" | xargs sed -i 's/import AIAssistantWidget from "@\/platform\/v1\/components";/import AIAssistantWidget from "@\/components\/ai-assistant-widget";/g'
find src -name "*.tsx" -o -name "*.ts" | xargs sed -i 's/import StandaloneTaskDialog from "@\/platform\/v1\/components";/import StandaloneTaskDialog from "@\/components\/tasks\/tasks-dialog";/g'
find src -name "*.tsx" -o -name "*.ts" | xargs sed -i 's/import PermissionDenied from "@\/platform\/v1\/components";/import PermissionDenied from "@\/components\/PermissionDenied";/g'
find src -name "*.tsx" -o -name "*.ts" | xargs sed -i 's/import PaginatedSearchableSelect from "@\/platform\/v1\/components";/import PaginatedSearchableSelect from "@\/components\/generic\/paginated-searchable-select";/g'

# Fix specific component imports that have wrong export patterns
find src -name "*.tsx" -o -name "*.ts" | xargs sed -i 's/import AddUsersToChatDialog from "@\/components\/common\/dialogs\/add-users-to-chat-dialog";/import { AddUsersToChatDialog } from "@\/components\/common\/dialogs\/add-users-to-chat-dialog";/g'
find src -name "*.tsx" -o -name "*.ts" | xargs sed -i 's/import ManageParticipantsDialog from "@\/components\/common\/dialogs\/manage-task-chat-participants-dialog";/import { ManageParticipantsDialog } from "@\/components\/common\/dialogs\/manage-task-chat-participants-dialog";/g'
find src -name "*.tsx" -o -name "*.ts" | xargs sed -i 's/import DialogSkeleton from "@\/components\/dialogs\/dialog-skeleton";/import { DialogSkeleton } from "@\/components\/dialogs\/dialog-skeleton";/g'

# Fix Editor and Spinner imports
find src -name "*.tsx" -o -name "*.ts" | xargs sed -i 's/import { Editor } from "@\/platform\/v1\/components";/import { Editor } from "@\/components\/blocks\/editor-00\/editor";/g'
find src -name "*.tsx" -o -name "*.ts" | xargs sed -i 's/import { Spinner } from "@\/platform\/v1\/components";/import { Spinner } from "@\/components\/ui\/spinner";/g'

echo "Fixed remaining import issues."
