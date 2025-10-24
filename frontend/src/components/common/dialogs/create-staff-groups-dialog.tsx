"use client";

import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/platform/v1/components";
import { Input } from "@/platform/v1/components";
import { Button } from "@/platform/v1/components";
import { Textarea } from "@/platform/v1/components";
import { Separator } from "@/platform/v1/components";
import { showErrorToast, showSuccessToast } from "@/lib/utils";
import { USER_GROUPS_API } from "@/lib/api/approvals/utils";
import RoleSearchableSelect from "@/components/selects/role-searchable-select";
import UserProfileSearchableSelect from "@/components/selects/user-profile-searchable-select";
import type { IUserGroup, IUserGroupFormData } from "@/types/approvals.types";
import { RichTextEditor } from "../rich-editor";

interface UserGroupDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: () => void;
  initialData?: IUserGroup | null;
}

export function UserGroupDialog({
  isOpen,
  onClose,
  onSave,
  initialData,
}: UserGroupDialogProps) {
  const [groupName, setGroupName] = useState("");
  const [groupDescription, setGroupDescription] = useState("");
  const [selectedUserIds, setSelectedUserIds] = useState<number[]>([]);
  const [selectedRoleIds, setSelectedRoleIds] = useState<number[]>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (initialData) {
      setGroupName(initialData.name);
      setGroupDescription(initialData.description || "");
      setSelectedUserIds(initialData.users);
      setSelectedRoleIds(initialData.roles);
    } else {
      resetForm();
    }
  }, [initialData, isOpen]);

  const resetForm = () => {
    setGroupName("");
    setGroupDescription("");
    setSelectedUserIds([]);
    setSelectedRoleIds([]);
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const handleSave = async () => {
    if (!groupName.trim()) {
      showErrorToast({ error: null, defaultMessage: "Group name is required" });
      return;
    }

    if (selectedUserIds.length === 0 && selectedRoleIds.length === 0) {
      showErrorToast({
        error: null,
        defaultMessage: "Please select at least one user or role",
      });
      return;
    }

    try {
      setSaving(true);

      const groupData: IUserGroupFormData = {
        name: groupName,
        description: groupDescription,
        users: selectedUserIds,
        roles: selectedRoleIds,
        is_active: true,
        approval_status: "under_creation",
      };

      if (initialData) {
        await USER_GROUPS_API.update({
          id: initialData.id,
          payload: groupData,
        });
        showSuccessToast("User group updated successfully!");
      } else {
        await USER_GROUPS_API.create(groupData);
        showSuccessToast("User group created successfully!");
      }

      onSave();
      handleClose();
    } catch (e: any) {
      showErrorToast({
        error: e,
        defaultMessage: "Failed to save user group",
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="w-[95vw] sm:max-w-lg max-w-[400px]">
        <DialogHeader>
          <DialogTitle className="text-lg sm:text-xl">
            {initialData ? "Edit Staff Group" : "Create Staff Group"}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 sm:space-y-6 py-4 max-h-[70vh] sm:max-h-[80vh] overflow-y-auto px-2 sm:px-4">
          <div className="space-y-4">
            <div>
              <label className="block text-xs sm:text-sm font-medium mb-1 sm:mb-2">
                Group Name <span className="text-destructive">*</span>
              </label>
              <Input
                placeholder="e.g., Finance Team, HR Managers..."
                value={groupName}
                onChange={(e) => setGroupName(e.target.value)}
                className="text-xs sm:text-sm"
              />
            </div>

            <div>
              <label className="block text-xs sm:text-sm font-medium mb-1 sm:mb-2">
                Description
              </label>
              <RichTextEditor
                value={groupDescription || ""}
                onChange={(value) => setGroupDescription(value || "")}
                placeholder="Optional description of this user group..."
                disabled={false}
                maxLength={1000}
                className="text-xs sm:text-sm"
              />
            </div>
          </div>

          <Separator />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 items-end">
            <div>
              <label className="block text-xs sm:text-sm font-medium mb-1 sm:mb-2">
                Roles
              </label>
              <RoleSearchableSelect
                value={selectedRoleIds}
                onValueChange={(values) =>
                  setSelectedRoleIds(values.map((val) => Number(val)))
                }
                placeholder="Select roles..."
                multiple={true}
              />
            </div>

            <div>
              <label className="block text-xs sm:text-sm font-medium mb-1 sm:mb-2">
                Users
              </label>
              <UserProfileSearchableSelect
                value={selectedUserIds}
                onValueChange={(values) =>
                  setSelectedUserIds(values.map((val) => Number(val)))
                }
                placeholder="Select users..."
                multiple={true}
              />
            </div>
          </div>
        </div>

        <DialogFooter className="space-x-2 mt-4 sm:mt-6">
          <Button
            variant="outline"
            onClick={handleClose}
            disabled={saving}
            className="w-full sm:w-auto text-xs sm:text-sm"
          >
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={saving}
            className="w-full sm:w-auto text-xs sm:text-sm"
          >
            {saving
              ? "Saving..."
              : initialData
                ? "Update Group"
                : "Create Group"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
