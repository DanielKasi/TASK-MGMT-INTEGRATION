"use client";

import { useState, useEffect } from "react";
import { UserPlus, Loader2, AlertCircle, Eye } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/platform/v1/components";
import { Button } from "@/platform/v1/components";
import { Label } from "@/platform/v1/components";
import { Alert, AlertDescription } from "@/platform/v1/components";
import { Switch } from "@/platform/v1/components";
import { toast } from "sonner";
import { showErrorToast } from "@/lib/utils";
import { TASK_PROJECT_DISCUSSION_PARTICIPANT_API } from "@/lib/utils.chats";
import UserSearchableSelect from "@/components/selects/user-searchable-select";
import { IProjectChatDiscussionParticipantsFormData } from "@/types/project.type";

interface AddUsersToChatDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  projectId: number;
  projectAssigneeIds?: number[];
  existingParticipantIds?: number[];
  onUsersAdded?: () => void;
}

export function AddUsersToChatDialog({
  isOpen,
  onOpenChange,
  projectId,
  projectAssigneeIds = [],
  existingParticipantIds = [],
  onUsersAdded,
}: AddUsersToChatDialogProps) {
  const [selectedUserIds, setSelectedUserIds] = useState<(string | number)[]>(
    []
  );
  const [isViewerOnly, setIsViewerOnly] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!isOpen) {
      setSelectedUserIds([]);
      setIsViewerOnly(false);
    }
  }, [isOpen]);

  const handleSubmit = async () => {
    if (selectedUserIds.length === 0) {
      toast.error("Please select at least one user");
      return;
    }

    setSubmitting(true);
    try {
      const promises = selectedUserIds.map((userId) => {
        const data: Partial<IProjectChatDiscussionParticipantsFormData> = {
          project: projectId,
          user: Number(userId),
          can_send: !isViewerOnly,
        };
        return TASK_PROJECT_DISCUSSION_PARTICIPANT_API.create({ data });
      });

      await Promise.all(promises);

      const roleText = isViewerOnly ? "viewer(s)" : "participant(s)";
      toast.success(
        `${selectedUserIds.length} ${roleText} added to project chat`
      );
      onUsersAdded?.();
      onOpenChange(false);
    } catch (error) {
      showErrorToast({
        error,
        defaultMessage: "Failed to add users to project chat",
      });
    } finally {
      setSubmitting(false);
    }
  };

  const excludedUserIds = [
    ...new Set([...projectAssigneeIds, ...existingParticipantIds]),
  ];

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <UserPlus className="h-5 w-5" />
            Add Users to Project Chat
          </DialogTitle>
          <DialogDescription>
            Add users to this project discussion. Project assignees are already
            included automatically.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="text-xs">
              Users assigned to this project are automatically included in the
              chat and cannot be added or removed.
            </AlertDescription>
          </Alert>

          <div className="space-y-2">
            <Label htmlFor="users" className="text-sm font-medium">
              Select Users <span className="text-red-500">*</span>
            </Label>
            <UserSearchableSelect
              value={selectedUserIds}
              onValueChange={setSelectedUserIds}
              placeholder="Search and select users..."
              multiple={true}
              disabled={submitting}
              showSelectedItems={true}
              hideSelectedFromList={true}
              className="w-full"
            />
            {selectedUserIds.length > 0 && (
              <p className="text-xs text-muted-foreground">
                {selectedUserIds.length} user
                {selectedUserIds.length > 1 ? "s" : ""} selected
              </p>
            )}
          </div>

          <div className="flex items-center justify-between space-x-2 p-3 rounded-lg border bg-muted/50">
            <div className="space-y-0.5 flex-1">
              <div className="flex items-center gap-2">
                <Eye className="h-4 w-4 text-muted-foreground" />
                <Label
                  htmlFor="viewer-mode"
                  className="text-sm font-medium cursor-pointer"
                >
                  Add as Viewer Only
                </Label>
              </div>
              <p className="text-xs text-muted-foreground">
                Viewers can see messages but cannot send any messages
              </p>
            </div>
            <Switch
              id="viewer-mode"
              checked={isViewerOnly}
              onCheckedChange={setIsViewerOnly}
              disabled={submitting}
            />
          </div>
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={submitting}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={submitting || selectedUserIds.length === 0}
          >
            {submitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Adding...
              </>
            ) : (
              `Add ${selectedUserIds.length > 0 ? `(${selectedUserIds.length})` : "Users"}`
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
