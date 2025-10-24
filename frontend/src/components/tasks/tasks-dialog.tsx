"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/platform/v1/components";
import { Button } from "@/platform/v1/components";
import { Input } from "@/platform/v1/components";
import { Label } from "@/platform/v1/components";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/platform/v1/components";
import { IStandAloneTask, IStandAloneTaskFormData } from "@/types/types.utils";
import {
  ITaskPriority,
  ITaskStandAloneStatusFormData,
} from "@/types/project.type";
import { toast } from "sonner";
import {
  TASKS_API,
  TASK_PRIORITY_API,
  showErrorToast,
  PROJECTS_API,
} from "@/lib/utils";
import UserSearchableSelect from "@/components/selects/user-searchable-select";
import RelatedUserSearchableSelect from "@/components/selects/related-user-searchable-select";
import { MultiSelectPopover } from "@/components/common/multi-select-popover";
import { USER_GROUPS_API } from "@/lib/api/approvals/utils";
import { IUserGroup } from "@/types/approvals.types";
import { useSelector } from "react-redux";
import { selectUser } from "@/store/auth/selectors-context-aware";
import {ProtectedComponent} from "@/platform/v1/components";
import { PERMISSION_CODES } from "@/constants";
import {
  Plus,
  Lock,
  MoreHorizontal,
  Pencil,
  Trash2,
} from "lucide-react";
import { TaskPriorityDialog } from "@/components/common/dialogs/create-task-priority-dialog";
import { UserGroupDialog } from "@/components/common/dialogs/create-staff-groups-dialog";
import { RichTextEditor } from "@/components/common/rich-editor";
import { Switch } from "@/platform/v1/components";
import RichTextDisplay from "@/components/common/rich-text-display";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/platform/v1/components";
import { TaskStatusDialog } from "@/components/common/dialogs/task-statuses-dialog";

interface StandaloneTaskDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: Partial<IStandAloneTaskFormData>) => Promise<void>;
  initialData?: IStandAloneTask | null;
}

export default function StandaloneTaskDialog({
  isOpen,
  onClose,
  onSave,
  initialData,
}: StandaloneTaskDialogProps) {
  const currentUser = useSelector(selectUser);
  const [isTaskStatusDialogOpen, setIsTaskStatusDialogOpen] = useState(false);
  const [editingStatus, setEditingStatus] =
  useState<ITaskStandAloneStatusFormData | null>(null);
  const [formData, setFormData] = useState<Partial<IStandAloneTaskFormData>>({
    task_name: "",
    description: "",
    user_manager: 0,
    user_assignees: [],
    staff_group_assignees: [],
    start_date: "",
    end_date: "",
    freeze_assignee: false,
    priority: 0,
    is_active: true,
    task_statuses: [],
  });

  const [errors, setErrors] = useState<
    Partial<Record<keyof IStandAloneTaskFormData, string>>
  >({});
  const [loading, setLoading] = useState(false);
  const [taskPriorities, setTaskPriorities] = useState<ITaskPriority[]>([]);
  const [userGroups, setUserGroups] = useState<IUserGroup[]>([]);
  const [taskPriorityDialogOpen, setTaskPriorityDialogOpen] = useState(false);
  const [openDialog, setOpenDialog] = useState(false);
  const [loadingOptions, setLoadingOptions] = useState(false);

  const canEditFrozenAssignees = useMemo(() => {
    if (!initialData) return true;
    if (!formData.freeze_assignee) return true;

    const isTaskCreator =
      currentUser && initialData.created_by === currentUser.id;
    const isTaskLeader =
      currentUser && initialData.user_manager?.id === currentUser.id;

    return isTaskCreator || isTaskLeader;
  }, [initialData, currentUser, formData.freeze_assignee]);

  const isEditMode = !!initialData;

  const canEditEndDate =
    !isEditMode ||
    (initialData && currentUser && initialData.created_by === currentUser.id);

  const handleAddTaskStatus = (statusData: ITaskStandAloneStatusFormData) => {
    if (editingStatus) {
      setFormData((prev) => ({
        ...prev,
        task_statuses:
          prev.task_statuses?.map((status) =>
            status.name === editingStatus.name ? statusData : status
          ) || [],
      }));
      toast.success("Task status updated");
      setEditingStatus(null);
    } else {
      setFormData((prev) => ({
        ...prev,
        task_statuses: [...(prev.task_statuses || []), statusData],
      }));
      toast.success("Task status added");
    }
  };

  const handleDeleteTaskStatus = (statusName: string) => {
    setFormData((prev) => ({
      ...prev,
      task_statuses:
        prev.task_statuses?.filter((status) => status.name !== statusName) ||
        [],
    }));
  };

  const openCreateDialog = () => {
    setOpenDialog(true);
  };

  const closeDialog = () => {
    setOpenDialog(false);
  };

  const handleSaveComplete = async () => {
    try {
      const userGroupsRes = await USER_GROUPS_API.fetchAll();
      setUserGroups(userGroupsRes.results || []);
    } catch (error) {
      showErrorToast({ error, defaultMessage: "Failed to reload user groups" });
    }
    closeDialog();
  };

  useEffect(() => {
    const loadOptions = async () => {
      if (!isOpen) return;

      try {
        setLoadingOptions(true);
        const [prioritiesRes, userGroupsRes] = await Promise.all([
          TASK_PRIORITY_API.getPaginatedTaskPriority({}),
          USER_GROUPS_API.fetchAll(),
        ]);

        setTaskPriorities(prioritiesRes.results || []);
        setUserGroups(userGroupsRes.results || []);
      } catch (error) {
        showErrorToast({ error, defaultMessage: "Failed to load options" });
      } finally {
        setLoadingOptions(false);
      }
    };

    loadOptions();
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) {
      setFormData({
        task_name: "",
        description: "",
        user_manager: 0,
        user_assignees: [],
        staff_group_assignees: [],
        start_date: "",
        end_date: "",
        freeze_assignee: false,
        priority: 0,
        is_active: true,
        task_statuses: [],
      });
    }
  }, [isOpen]);

  useEffect(() => {
    const fetchTaskStatuses = async () => {
      try {
        if (initialData?.id && initialData.task_statuses) {
          const appliedStatusId = initialData.applied_task_status?.id;

          setFormData((prev) => ({
            ...prev,
            task_statuses: initialData.task_statuses?.map((st) => ({
              ...st,
              is_current: st.id === appliedStatusId,
            })) || [],
          }));
        } else {
          const response = await PROJECTS_API.getDefaultTaskStatuses();
          setFormData((prev) => ({
            ...prev,
            task_statuses: response.map((st, idx) => ({
              ...st,
              id: idx,
              is_current: false,
            })),
          }));
        }
      } catch (error) {
        toast.error("Failed to load task statuses");
      }
    };
    fetchTaskStatuses();
  }, [isOpen, initialData]);



  useEffect(() => {
    if (initialData) {
      const formatDateTimeLocal = (dateString: string | null) => {
        if (!dateString) return "";
        const date = new Date(dateString);
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, "0");
        const day = String(date.getDate()).padStart(2, "0");
        const hours = String(date.getHours()).padStart(2, "0");
        const minutes = String(date.getMinutes()).padStart(2, "0");
        return `${year}-${month}-${day}T${hours}:${minutes}`;
      };

      const startDateTime = formatDateTimeLocal(initialData.start_date);
      const endDateTime = formatDateTimeLocal(initialData.end_date);

      setFormData((prev) => ({
        ...prev,
        task_name: initialData.task_name || prev.task_name || "",
        description: initialData.description || prev.description || "",
        user_manager: initialData.user_manager?.id || prev.user_manager || 0,
        user_assignees:
          initialData.user_assignees?.map((a) => a.id) ||
          prev.user_assignees ||
          [],
        staff_group_assignees:
          initialData.staff_group_assignees?.map((g) => g.id) ||
          prev.staff_group_assignees ||
          [],
        start_date: startDateTime || prev.start_date || "",
        end_date: endDateTime || prev.end_date || "",
        priority:
          initialData.priority?.id ||
          prev.priority ||
          taskPriorities[0]?.id ||
          0,
        is_active: initialData.is_active ?? prev.is_active ?? true,
        completion_date:
          initialData.completion_date || prev.completion_date || undefined,
        freeze_assignee:
          initialData.freeze_assignee ?? prev.freeze_assignee ?? true,
          task_statuses: prev.task_statuses || [],
      }));
    } else {
      setFormData((prev) => ({
        ...prev,
        task_name: prev.task_name || "",
        description: prev.description || "",
        user_manager: prev.user_manager || 0,
        user_assignees: prev.user_assignees || [],
        staff_group_assignees: prev.staff_group_assignees || [],
        start_date: prev.start_date || "",
        end_date: prev.end_date || "",
        priority: prev.priority || taskPriorities[0]?.id || 0,
        is_active: prev.is_active ?? true,
        freeze_assignee: prev.freeze_assignee ?? true,
      }));
    }
  }, [initialData, taskPriorities]);

  const openTaskPriorityDialog = () => {
    setTaskPriorityDialogOpen(true);
  };

  const handleTaskPrioritySaved = async () => {
    try {
      const prioritiesRes = await TASK_PRIORITY_API.getPaginatedTaskPriority(
        {}
      );
      setTaskPriorities(prioritiesRes.results || []);
    } catch (error) {
      showErrorToast({ error, defaultMessage: "Failed to reload priorities" });
    }
    setTaskPriorityDialogOpen(false);
  };

  const handleInputChange = (
    field: keyof IStandAloneTaskFormData,
    value:
      | string
      | number
      | boolean
      | number[]
      | Record<string, any>
      | undefined
      | null
  ) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setErrors((prev) => ({ ...prev, [field]: undefined }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: Partial<Record<keyof IStandAloneTaskFormData, string>> =
      {};

    if (!formData.task_name) newErrors.task_name = "Task name is required.";
    if (
      !formData.task_statuses?.length ||
      formData.task_statuses.every((st) => !st.is_current)
    )
      newErrors.task_statuses = "A task status is required.";
    if (!formData.priority) newErrors.priority = "Priority is required.";

    if (
      formData.start_date &&
      formData.end_date &&
      new Date(formData.start_date) > new Date(formData.end_date)
    ) {
      newErrors.end_date = "End date must be after start date.";
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setLoading(true);
    try {
      const dataToSubmit: Partial<IStandAloneTaskFormData> = {
        ...formData,
      };

      dataToSubmit.task_statuses = [
        ...(dataToSubmit.task_statuses?.map((st) => ({
          ...st,
        })) || []),
      ];

      if (formData.start_date) {
        dataToSubmit.start_date = formData.start_date;
      } else {
        delete dataToSubmit.start_date;
      }

      if (formData.end_date) {
        dataToSubmit.end_date = formData.end_date;
      } else {
        delete dataToSubmit.end_date;
      }

      if (!dataToSubmit.completion_date) delete dataToSubmit.completion_date;

      if (!initialData) {
        await TASKS_API.create({
          projectId: 0,
          data: {
            ...dataToSubmit,
            task_statuses: [
              ...(dataToSubmit.task_statuses?.map((st) => ({ ...st })) || []),
            ],
          },
        });
      } else {
        const updateData = { ...dataToSubmit };
        delete updateData.task_statuses;
        if (updateData.freeze_assignee) {
          delete updateData.user_manager;
          delete updateData.user_assignees;
          delete updateData.staff_group_assignees;
        }
        await TASKS_API.update({
          taskId: initialData.id,
          data: updateData,
        });
      }

      toast.success(`Task ${initialData ? "updated" : "created"} successfully`);
      await onSave(dataToSubmit);
      onClose();
    } catch (err) {
      showErrorToast({
        error: err,
        defaultMessage: `Failed to ${initialData ? "update" : "create"} task`,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <ProtectedComponent
      permissionCode={
        initialData
          ? PERMISSION_CODES.CAN_EDIT_TASKS
          : PERMISSION_CODES.CAN_CREATE_TASKS
      }
    >
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-[90vw] sm:max-w-2xl md:max-w-3xl lg:max-w-5xl p-4 sm:p-6">
          <DialogHeader>
            <DialogTitle className="text-lg sm:text-xl md:text-2xl">
              {initialData ? "Edit Task" : "Add New Task"}
            </DialogTitle>
            <DialogDescription className="text-xs sm:text-sm">
              {initialData
                ? "Update task details"
                : "Create a new standalone task"}
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-6">
            <div className="space-y-4 px-2 sm:px-4 overflow-y-auto max-h-[60vh] sm:max-h-[60svh] md:max-h-[60svh]">
              <div className="space-y-2">
                <Label htmlFor="task_name" className="text-xs sm:text-sm">
                  Task Name *
                </Label>
                <Input
                  id="task_name"
                  value={formData.task_name || ""}
                  onChange={(e) =>
                    handleInputChange("task_name", e.target.value)
                  }
                  placeholder="Enter task name"
                  className="text-xs sm:text-sm"
                />
                {errors.task_name && (
                  <p className="text-red-600 text-xs">{errors.task_name}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="description" className="text-xs sm:text-sm">
                  Description *
                </Label>
                <RichTextEditor
                  value={formData.description || ""}
                  onChange={(value) => handleInputChange("description", value)}
                  placeholder="Enter your description..."
                  disabled={false}
                  maxLength={1000}
                />
                {errors.description && (
                  <p className="text-red-600 text-xs">{errors.description}</p>
                )}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                <div className="space-y-2">
                  <Label htmlFor="start_date">
                    Start Date & Time <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="start_date"
                    type="datetime-local"
                    value={formData.start_date || ""}
                    onChange={(e) =>
                      handleInputChange("start_date", e.target.value)
                    }
                    className={errors.start_date ? "border-red-500" : ""}
                  />
                  {errors.start_date && (
                    <p className="text-sm text-red-500">{errors.start_date}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="end_date">
                    End Date & Time <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="end_date"
                    type="datetime-local"
                    value={formData.end_date || ""}
                    onChange={(e) =>
                      handleInputChange("end_date", e.target.value)
                    }
                    min={formData.start_date || undefined}
                    disabled={!canEditEndDate}
                    className={`text-sm ${errors.end_date ? "border-red-500" : ""}`}
                  />
                  {errors.end_date && (
                    <p className="text-sm text-red-500">{errors.end_date}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label
                    htmlFor="completion_date"
                    className="text-xs sm:text-sm"
                  >
                    Completion Date
                  </Label>
                  <Input
                    id="completion_date"
                    type="date"
                    value={formData.completion_date || ""}
                    onChange={(e) =>
                      handleInputChange(
                        "completion_date",
                        e.target.value || null
                      )
                    }
                    className="text-xs sm:text-sm"
                  />
                </div>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="priority" className="text-xs sm:text-sm">
                      Priority *
                    </Label>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="h-6 w-6 p-0"
                      onClick={openTaskPriorityDialog}
                    >
                      <Plus className="h-3 w-3 sm:h-4 sm:w-4" />
                    </Button>
                  </div>

                  <Select
                    value={formData.priority?.toString() || ""}
                    onValueChange={(value) =>
                      handleInputChange("priority", Number(value))
                    }
                  >
                    <SelectTrigger className="rounded-xl text-xs sm:text-sm">
                      <SelectValue placeholder="Select priority" />
                    </SelectTrigger>
                    <SelectContent className="text-xs sm:text-sm">
                      {taskPriorities.map((priority) => (
                        <SelectItem
                          key={priority.id}
                          value={priority.id.toString()}
                        >
                          <div className="flex items-center gap-2 sm:gap-3">
                            <div
                              className="w-2 h-2 sm:w-3 sm:h-3 rounded-full"
                              style={{ backgroundColor: priority.color_code }}
                            />
                            {priority.name}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {errors.priority && (
                    <p className="text-red-600 text-xs">{errors.priority}</p>
                  )}
                </div>
              </div>

              {formData.freeze_assignee && (
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-start gap-2">
                  <Lock className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
                  <p className="text-xs text-amber-800">
                    Assignees are locked and cannot be modified after task
                    creation.
                  </p>
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                <div className="space-y-4">
                  <div className="flex flex-col-reverse min-h-[120px]">
                    <div>
                      <Label className="text-base font-medium mb-2 block">
                        Task Leader
                      </Label>
                      {formData.freeze_assignee && !canEditFrozenAssignees ? (
                        <ProtectedComponent
                          permissionCode={
                            PERMISSION_CODES.CAN_EDIT_FROZEN_ASSIGNEES
                          }
                        >
                          <UserSearchableSelect
                            disabled={false}
                            value={
                              formData.user_manager
                                ? [formData.user_manager]
                                : []
                            }
                            onValueChange={(values) => {
                              const newValue =
                                values.length > 0 ? Number(values[0]) : 0;
                              handleInputChange("user_manager", newValue);
                              handleInputChange("user_assignees", []);
                            }}
                            placeholder="Select task leader"
                            multiple={false}
                            className="text-xs sm:text-sm"
                          />
                        </ProtectedComponent>
                      ) : null}

                      {(!formData.freeze_assignee ||
                        canEditFrozenAssignees) && (
                        <UserSearchableSelect
                          disabled={false}
                          value={
                            formData.user_manager ? [formData.user_manager] : []
                          }
                          onValueChange={(values) => {
                            const newValue =
                              values.length > 0 ? Number(values[0]) : 0;
                            handleInputChange("user_manager", newValue);
                            handleInputChange("user_assignees", []);
                          }}
                          placeholder="Select task leader"
                          multiple={false}
                          className="text-xs sm:text-sm"
                        />
                      )}

                      {formData.freeze_assignee && !canEditFrozenAssignees && (
                        <div className="h-10 px-3 py-2 border rounded-xl bg-gray-50 flex items-center text-sm text-gray-700">
                          {initialData?.user_manager?.name || "Not assigned"}
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="flex flex-col-reverse min-h-[120px]">
                    <div>
                      <Label className="text-base font-medium mb-2 block">
                        Assign To (Optional)
                      </Label>
                      {formData.freeze_assignee && !canEditFrozenAssignees ? (
                        <ProtectedComponent
                          permissionCode={
                            PERMISSION_CODES.CAN_EDIT_FROZEN_ASSIGNEES
                          }
                        >
                          <RelatedUserSearchableSelect
                            value={formData.user_assignees || []}
                            relatedUserId={formData.user_manager || null}
                            onValueChange={(values) =>
                              handleInputChange(
                                "user_assignees",
                                values.map((val) => Number(val))
                              )
                            }
                            placeholder={
                              formData.user_manager
                                ? "Select assignees from leader's branch"
                                : "Please select a task leader first"
                            }
                            multiple={true}
                            disabled={!formData.user_manager}
                            className="text-xs sm:text-sm"
                          />
                        </ProtectedComponent>
                      ) : null}

                      {(!formData.freeze_assignee ||
                        canEditFrozenAssignees) && (
                        <RelatedUserSearchableSelect
                          value={formData.user_assignees || []}
                          relatedUserId={formData.user_manager || null}
                          onValueChange={(values) =>
                            handleInputChange(
                              "user_assignees",
                              values.map((val) => Number(val))
                            )
                          }
                          placeholder={
                            formData.user_manager
                              ? "Select assignees from leader's branch"
                              : "Please select a task leader first"
                          }
                          multiple={true}
                          disabled={!formData.user_manager}
                          className="text-xs sm:text-sm"
                        />
                      )}

                      {formData.freeze_assignee && !canEditFrozenAssignees && (
                        <div className="h-10 px-3 py-2 border rounded-xl bg-gray-50 flex items-center text-sm text-gray-700">
                          {initialData?.user_assignees?.length
                            ? initialData.user_assignees
                                .map((a) => a.name)
                                .join(", ")
                            : "Not assigned"}
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label className="text-base font-medium">
                      Assignee Groups (Optional)
                    </Label>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="h-6 w-6 p-0"
                      onClick={openCreateDialog}
                    >
                      <Plus className="h-3 w-3 sm:h-4 sm:w-4" />
                    </Button>
                  </div>
                  <div className="relative min-h-[80px]">
                    {formData.freeze_assignee && !canEditFrozenAssignees ? (
                      <ProtectedComponent
                        permissionCode={
                          PERMISSION_CODES.CAN_EDIT_FROZEN_ASSIGNEES
                        }
                      >
                        <MultiSelectPopover
                          disabled={false}
                          items={userGroups.map((group) => ({
                            id: group.id,
                            name: group.name,
                            label: `${group.name} (${group.users.length} users)`,
                          }))}
                          selectedIds={formData.staff_group_assignees || []}
                          onSelectionChange={(ids) =>
                            handleInputChange("staff_group_assignees", ids)
                          }
                          placeholder="Select assignee groups..."
                          emptyMessage="No user groups available"
                          className="text-xs sm:text-sm w-full"
                        />
                      </ProtectedComponent>
                    ) : null}

                    {(!formData.freeze_assignee || canEditFrozenAssignees) && (
                      <MultiSelectPopover
                        disabled={false}
                        items={userGroups.map((group) => ({
                          id: group.id,
                          name: group.name,
                          label: `${group.name} (${group.users.length} users)`,
                        }))}
                        selectedIds={formData.staff_group_assignees || []}
                        onSelectionChange={(ids) =>
                          handleInputChange("staff_group_assignees", ids)
                        }
                        placeholder="Select assignee groups..."
                        emptyMessage="No user groups available"
                        className="text-xs sm:text-sm w-full"
                      />
                    )}

                    {formData.freeze_assignee && !canEditFrozenAssignees && (
                      <div className="h-10 px-3 py-2 border rounded-xl bg-gray-50 flex items-center text-sm text-gray-700">
                        {initialData?.staff_group_assignees?.length
                          ? initialData.staff_group_assignees
                              .map((g) => g.name)
                              .join(", ")
                          : "Not assigned"}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 mb-6">
                <Label className="text-lg font-semibold text-gray-900 block">
                  Task Statuses
                </Label>
                {!isEditMode && (
                  <Button
                    type="button"
                    variant="default"
                    onClick={() => setIsTaskStatusDialogOpen(true)}
                    className="w-auto ml-4 text-white p-2 rounded-md h-8 flex items-center justify-center"
                    aria-label="Add Task Status"
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                )}
              </div>

              <div className="grid gap-4 md:grid-cols-3">
                {(formData.task_statuses || []).map((status) => {
                  return (
                    <div
                      key={status.name}
                      className={`relative rounded-lg bg-[#F4F4F9] p-4 border border-gray-100 transition-all ${
                        status.is_current ? "ring-2 ring-primary" : ""
                      }`}
                    >
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex items-center gap-2 flex-1">
                          <div
                            className="w-3 h-3 rounded-full flex-shrink-0 -mt-12"
                            style={{
                              backgroundColor: status.color_code || "#6B7280",
                            }}
                          />
                          <div className="flex-1">
                            <h3 className="font-medium text-black">
                              {status.name}
                            </h3>
                            {status.description && (
                              <RichTextDisplay
                                htmlContent={status.description || "—"}
                                className="text-xs sm:text-sm text-gray-600 mt-2 sm:mt-3"
                              />
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Switch
                            id={`status-${status.name}`}
                            checked={status.is_current}
                            onCheckedChange={(checked) => {
                              if (checked) {
                                setFormData((prev) => ({
                                  ...prev,
                                  task_statuses: prev.task_statuses?.map(
                                    (st) => {
                                      if (st.id === status.id) {
                                        return { ...st, is_current: true };
                                      }
                                      return { ...st, is_current: false };
                                    }
                                  ),
                                }));
                              }
                            }}
                            className="scale-75"
                          />
                          {!isEditMode && (
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-8 w-8 text-gray-600 hover:bg-transparent"
                                >
                                  <MoreHorizontal className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end" className="w-40">
                                <DropdownMenuItem
                                  onClick={() => {
                                    setEditingStatus(status);
                                    setIsTaskStatusDialogOpen(true);
                                  }}
                                  className="cursor-pointer"
                                >
                                  <Pencil className="h-4 w-4 mr-2" />
                                  Edit
                                </DropdownMenuItem>
                                <DropdownMenuItem
                                  onClick={() =>
                                    handleDeleteTaskStatus(status.name)
                                  }
                                  className="cursor-pointer text-red-600 focus:text-red-600"
                                >
                                  <Trash2 className="h-4 w-4 mr-2" />
                                  Remove
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="flex justify-end gap-4 sm:gap-6 px-2 sm:px-4">
              <Button
                type="submit"
                className="w-full sm:w-auto rounded-full text-xs sm:text-sm"
                disabled={loading}
              >
                {loading
                  ? "Saving..."
                  : initialData
                    ? "Update Task"
                    : "Create Task"}
              </Button>
            </div>
          </form>

          <TaskStatusDialog
            open={isTaskStatusDialogOpen}
            onOpenChange={(open) => {
              if (!open) setEditingStatus(null);
              setIsTaskStatusDialogOpen(open);
            }}
            onSave={handleAddTaskStatus}
            initialData={editingStatus}
          />

          <TaskPriorityDialog
            isOpen={taskPriorityDialogOpen}
            onClose={() => setTaskPriorityDialogOpen(false)}
            onSave={handleTaskPrioritySaved}
            initialData={null}
          />

          <UserGroupDialog
            isOpen={openDialog}
            onClose={closeDialog}
            onSave={handleSaveComplete}
          />
        </DialogContent>
      </Dialog>
    </ProtectedComponent>
  );
}
