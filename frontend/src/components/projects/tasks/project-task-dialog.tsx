"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
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
import {
  IProjectTask,
  IProjectTaskFormData,
  IProject,
} from "@/types/types.utils";
import {
  ICustomField,
  IProjectTaskPriority,
  IProjectTaskStatusFormData,
} from "@/types/project.type";
import { toast } from "sonner";
import {
  PROJECTS_TASKS_API,
  showErrorToast,
  PROJECTS_API,
  PROJECT_TASK_PRIORITY_API,
} from "@/lib/utils";
import { MultiSelectPopover } from "@/components/common/multi-select-popover";
import { USER_GROUPS_API } from "@/lib/api/approvals/utils";
import { IUserGroup } from "@/types/approvals.types";
import { useSelector } from "react-redux";
import { selectUser } from "@/store/auth/selectors-context-aware";
import {ProtectedComponent} from "@/platform/v1/components";
import { PERMISSION_CODES } from "@/constants";
import { Plus, Check, ChevronDown, Lock } from "lucide-react";
import { UserGroupDialog } from "@/components/common/dialogs/create-staff-groups-dialog";
import { RichTextEditor } from "@/components/common/rich-editor";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/platform/v1/components";
import { cn } from "@/lib/utils";
import { Switch } from "@/platform/v1/components";
import RichTextDisplay from "@/components/common/rich-text-display";
import { ProjectTaskPriorityDialog } from "@/components/common/dialogs/create-project-task-priority-dilog";

interface ProjectTaskDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: Partial<IProjectTaskFormData>) => Promise<void>;
  project: IProject;
  initialData?: IProjectTask | null;
}

export default function ProjectTaskDialog({
  isOpen,
  onClose,
  onSave,
  project,
  initialData,
}: ProjectTaskDialogProps) {
  const currentUser = useSelector(selectUser);
  const [formData, setFormData] = useState<Partial<IProjectTaskFormData>>({
    project: project?.id,
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
    custom_fields: {},
  });

  const [errors, setErrors] = useState<
    Partial<Record<keyof IProjectTaskFormData, string>>
  >({});
  const [loading, setLoading] = useState(false);
  const [taskStatuses, setTaskStatuses] = useState<
    IProjectTaskStatusFormData[]
  >([]);
  const [userGroups, setUserGroups] = useState<IUserGroup[]>([]);
  const [openDialog, setOpenDialog] = useState(false);
  const [loadingOptions, setLoadingOptions] = useState(false);
  const [projectTaskPriorityDialogOpen, setProjectTaskPriorityDialogOpen] =
    useState(false);
  const [projectTaskPriorities, setProjectTaskPriorities] = useState<IProjectTaskPriority[]>(
    []
  );

  const openProjectTaskPriorityDialog = () => {
    setProjectTaskPriorityDialogOpen(true);
  };

  const handleProjectTaskPrioritySaved = async () => {
    try {
      const prioritiesRes =
        await PROJECT_TASK_PRIORITY_API.getPaginatedProjectTaskPriority({});
      setProjectTaskPriorities(prioritiesRes.results || []);
    } catch (error) {
      showErrorToast({
        error,
        defaultMessage: "Failed to reload priorities",
      });
    }
    setProjectTaskPriorityDialogOpen(false);
  };

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

  // Create combined list of project leader and assignees for restricted selection
  const getProjectUsers = useCallback(() => {
    if (!project) return [];

    const users = [];

    // Add project leader if exists
    if (project.user_manager) {
      users.push({
        id: project.user_manager.id,
        name: project.user_manager.name,
        label: `${project.user_manager.name} (Project Leader)`,
      });
    }

    // Add project assignees
    if (project.user_assignees) {
      project.user_assignees.forEach((assignee) => {
        // Avoid duplicates if assignee is also the leader
        if (!project.user_manager || assignee.id !== project.user_manager.id) {
          users.push({
            id: assignee.id,
            name: assignee.name,
            label: assignee.name,
          });
        }
      });
    }

    return users;
  }, [project]);

  // Single select component for task leader
  const SingleSelectPopover = ({
    items,
    selectedId,
    onSelectionChange,
    disabled = false,
    placeholder = "Select item...",
    emptyMessage = "No items available",
  }: {
    items: Array<{ id: number; name: string; label?: string }>;
    selectedId: number | null;
    onSelectionChange: (id: number | null) => void;
    placeholder?: string;
    disabled?: boolean;
    emptyMessage?: string;
  }) => {
    const [open, setOpen] = useState(false);

    const selectedItem = items.find((item) => item.id === selectedId);

    const handleSelect = (id: number) => {
      if (disabled) return;
      onSelectionChange(selectedId === id ? null : id);
      setOpen(false);
    };

    return (
      <Popover open={open} onOpenChange={disabled ? undefined : setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            role="combobox"
            aria-expanded={open}
            disabled={disabled}
            className="w-full h-[40px] justify-between text-left font-normal bg-transparent rounded-xl"
          >
            <span className="truncate">
              {selectedItem
                ? selectedItem.label || selectedItem.name
                : placeholder}
            </span>
            <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-full p-0" align="start">
          <div className="max-h-60 overflow-auto">
            {items.length === 0 ? (
              <div className="p-4 text-sm text-muted-foreground text-center">
                {emptyMessage}
              </div>
            ) : (
              <div className="p-1">
                {items.map((item) => (
                  <div
                    key={item.id}
                    className={cn(
                      "flex items-center space-x-2 rounded-sm px-2 py-1.5 text-sm cursor-pointer hover:bg-accent",
                      selectedId === item.id && "bg-accent"
                    )}
                    onClick={() => handleSelect(item.id)}
                  >
                    <div
                      className={cn(
                        "flex h-4 w-4 items-center justify-center rounded-sm border border-primary",
                        selectedId === item.id
                          ? "bg-primary text-primary-foreground"
                          : "opacity-50"
                      )}
                    >
                      {selectedId === item.id && <Check className="h-3 w-3" />}
                    </div>
                    <span className="flex-1">{item.label || item.name}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </PopoverContent>
      </Popover>
    );
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
          // PROJECT_TASK_STATUS_API.getPaginatedTaskStatuses({}),
          PROJECT_TASK_PRIORITY_API.getPaginatedProjectTaskPriority({}),
          USER_GROUPS_API.fetchAll(),
        ]);

        setProjectTaskPriorities(prioritiesRes.results || []);
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
        project: project?.id,
        task_name: "",
        description: "",
        user_manager: 0,
        user_assignees: [],
        staff_group_assignees: [],
        start_date: "",
        end_date: "",
        freeze_assignee: false,
        is_active: true,
        custom_fields: {},
      });
    }
  }, [isOpen, project?.id]);

  useEffect(() => {
    const fetchTaskStatuses = async () => {
      try {
        if (project?.id) {
          const response = await PROJECTS_API.getPaginatedProjectsTaskStatuses({
            page: 1,
            project: project.id,
          });
          setTaskStatuses(
            response.results.map((st) => ({
              ...st,
              is_current: initialData?.applied_project_task_status?.id
                ? Number(st.id) === initialData.applied_project_task_status?.id
                : false,
            }))
          );
        }
      } catch (error) {
        toast.error("Failed to load task statuses");
      }
    };
    fetchTaskStatuses();
  }, [isOpen, initialData, project?.id]);

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
      let parsedCustomFields = {};
      if (initialData.custom_fields) {
        try {
          parsedCustomFields =
            typeof initialData.custom_fields === "string"
              ? JSON.parse(initialData.custom_fields)
              : initialData.custom_fields;
        } catch (e) {
          console.error("Failed to parse custom_fields:", e);
        }
      }

      setFormData((prev) => ({
        ...prev,
        project: project?.id,
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
        is_active: initialData.is_active ?? prev.is_active ?? true,
        completion_date:
          initialData.completion_date || prev.completion_date || undefined,
        custom_fields: parsedCustomFields || prev.custom_fields || {},
        freeze_assignee:
          initialData.freeze_assignee ?? prev.freeze_assignee ?? true,
      }));
    } else {
      setFormData((prev) => ({
        ...prev,
        project: project?.id,
        task_name: prev.task_name || "",
        description: prev.description || "",
        user_manager: prev.user_manager || 0,
        user_assignees: prev.user_assignees || [],
        staff_group_assignees: prev.staff_group_assignees || [],
        start_date: prev.start_date || "",
        end_date: prev.end_date || "",
        is_active: prev.is_active ?? true,
        custom_fields: prev.custom_fields || {},
        freeze_assignee: prev.freeze_assignee ?? true,
      }));
    }
  }, [initialData, project?.id, taskStatuses]);

  const handleInputChange = (
    field: keyof IProjectTaskFormData,
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

  const renderCustomField = (field: ICustomField, index: number) => {
    const customFieldsObj =
      typeof formData.custom_fields === "object" &&
      formData.custom_fields !== null
        ? formData.custom_fields
        : {};

    const fieldValue = customFieldsObj[field.label];

    switch (field.type) {
      case "text":
        return (
          <div key={index} className="space-y-2">
            <Label
              htmlFor={`custom-${field.label}`}
              className="text-xs sm:text-sm"
            >
              {field.label}{" "}
              {field.required && <span className="text-red-500">*</span>}
            </Label>
            <Input
              id={`custom-${field.label}`}
              value={fieldValue || ""}
              onChange={(e) =>
                handleInputChange("custom_fields", {
                  ...customFieldsObj,
                  [field.label]: e.target.value,
                })
              }
              placeholder={`Enter ${field.label}`}
              className="text-xs sm:text-sm"
              required={field.required}
            />
          </div>
        );

      case "number":
        return (
          <div key={index} className="space-y-2">
            <Label
              htmlFor={`custom-${field.label}`}
              className="text-xs sm:text-sm"
            >
              {field.label}{" "}
              {field.required && <span className="text-red-500">*</span>}
            </Label>
            <Input
              id={`custom-${field.label}`}
              type="number"
              value={fieldValue || ""}
              onChange={(e) =>
                handleInputChange("custom_fields", {
                  ...customFieldsObj,
                  [field.label]: e.target.value,
                })
              }
              placeholder={`Enter ${field.label}`}
              className="text-xs sm:text-sm"
              required={field.required}
            />
          </div>
        );

      case "bool":
        return (
          <div key={index} className="space-y-2">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id={`custom-${field.label}`}
                checked={fieldValue || false}
                onChange={(e) =>
                  handleInputChange("custom_fields", {
                    ...customFieldsObj,
                    [field.label]: e.target.checked,
                  })
                }
                className="rounded border-gray-300"
              />
              <Label
                htmlFor={`custom-${field.label}`}
                className="text-xs sm:text-sm"
              >
                {field.label}{" "}
                {field.required && <span className="text-red-500">*</span>}
              </Label>
            </div>
          </div>
        );

      case "date":
        return (
          <div key={index} className="space-y-2">
            <Label
              htmlFor={`custom-${field.label}`}
              className="text-xs sm:text-sm"
            >
              {field.label}{" "}
              {field.required && <span className="text-red-500">*</span>}
            </Label>
            <Input
              id={`custom-${field.label}`}
              type="date"
              value={fieldValue || ""}
              onChange={(e) =>
                handleInputChange("custom_fields", {
                  ...customFieldsObj,
                  [field.label]: e.target.value,
                })
              }
              className="text-xs sm:text-sm"
              required={field.required}
            />
          </div>
        );

      case "select":
        if (field.multiple) {
          // Multiple select using MultiSelectPopover
          const selectedValues = Array.isArray(fieldValue) ? fieldValue : [];
          const selectItems = (field.options || []).map((opt, idx) => ({
            id: idx,
            name: String(opt),
            label: String(opt),
          }));

          return (
            <div key={index} className="space-y-2">
              <Label className="text-xs sm:text-sm">
                {field.label}{" "}
                {field.required && <span className="text-red-500">*</span>}
              </Label>
              <MultiSelectPopover
                items={selectItems}
                selectedIds={selectedValues}
                onSelectionChange={(ids) => {
                  const selectedOptions = ids.map((id) =>
                    String(field.options?.[id] || "")
                  );
                  handleInputChange("custom_fields", {
                    ...customFieldsObj,
                    [field.label]: selectedOptions,
                  });
                }}
                placeholder={`Select ${field.label}...`}
                emptyMessage={`No ${field.label} options available`}
                className="text-xs sm:text-sm"
              />
            </div>
          );
        } else {
          // Single select
          return (
            <div key={index} className="space-y-2">
              <Label
                htmlFor={`custom-${field.label}`}
                className="text-xs sm:text-sm"
              >
                {field.label}{" "}
                {field.required && <span className="text-red-500">*</span>}
              </Label>
              <Select
                value={fieldValue || ""}
                onValueChange={(value) =>
                  handleInputChange("custom_fields", {
                    ...customFieldsObj,
                    [field.label]: value,
                  })
                }
              >
                <SelectTrigger className="rounded-xl text-xs sm:text-sm">
                  <SelectValue placeholder={`Select ${field.label}`} />
                </SelectTrigger>
                <SelectContent className="text-xs sm:text-sm">
                  {(field.options || []).map((option, optIdx) => (
                    <SelectItem key={optIdx} value={String(option)}>
                      {String(option)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          );
        }

      default:
        return null;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: Partial<Record<keyof IProjectTaskFormData, string>> = {};

    if (!formData.task_name) newErrors.task_name = "Task name is required.";

    // Validate custom fields
    if (project?.custom_fields) {
      const customFieldsObj =
        typeof formData.custom_fields === "object" &&
        formData.custom_fields !== null
          ? formData.custom_fields
          : {};

      project.custom_fields.forEach((field) => {
        if (field.required) {
          const value = customFieldsObj[field.label];
          if (
            !value ||
            (Array.isArray(value) && value.length === 0) ||
            value === ""
          ) {
            newErrors[`custom_${field.label}` as keyof IProjectTaskFormData] =
              `${field.label} is required.`;
            toast.error(`${field.label} is required`);
          }
        }
      });
    }

    if (
      formData.start_date &&
      formData.end_date &&
      new Date(formData.start_date) > new Date(formData.end_date)
    ) {
      newErrors.end_date = "End date must be after start date.";
    }

    // Validate dates against project dates
    if (formData.start_date && project?.start_date) {
      const taskStartDate = new Date(formData.start_date);
      const projectStartDate = new Date(project.start_date);

      if (taskStartDate < projectStartDate) {
        newErrors.start_date = `Task start date cannot be before project start date (${projectStartDate.toLocaleDateString()})`;
        toast.error(newErrors.start_date);
      }
    }

    if (formData.end_date && project?.end_date) {
      const taskEndDate = new Date(formData.end_date);
      const projectEndDate = new Date(project.end_date);
      projectEndDate.setHours(23, 59, 59, 999);

      if (taskEndDate > projectEndDate) {
        newErrors.end_date = `Task end date cannot be after project end date (${projectEndDate.toLocaleDateString()})`;
        toast.error(newErrors.end_date);
      }
    }

    // Check if a task status is selected
    const selectedStatus = taskStatuses.find((st) => st.is_current);
    if (!selectedStatus) {
      newErrors.task_statuses = "Please select a task status";
      toast.error("Please select a task status");
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setLoading(true);
    try {
      const dataToSubmit: Partial<IProjectTaskFormData> = {
        ...formData,
        project: project?.id,
      };

      const selectedStatus = taskStatuses.find((st) => st.is_current);
      if (selectedStatus) {
        dataToSubmit.applied_project_task_status = selectedStatus.id;
      }

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

      if (
        formData.custom_fields &&
        typeof formData.custom_fields === "object" &&
        Object.keys(formData.custom_fields).length > 0
      ) {
        dataToSubmit.custom_fields = JSON.stringify(formData.custom_fields);
      } else {
        delete dataToSubmit.custom_fields;
      }

      if (!initialData) {
        await PROJECTS_TASKS_API.create({
          projectId: project.id,
          data: dataToSubmit,
        });
      } else {
        const updateData = { ...dataToSubmit };
        if (updateData.freeze_assignee) {
          delete updateData.user_manager;
          delete updateData.user_assignees;
          delete updateData.staff_group_assignees;
        }
        await PROJECTS_TASKS_API.update({
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
              {initialData ? "Edit Project Task" : "Add New Project Task"}
            </DialogTitle>
            <DialogDescription className="text-xs sm:text-sm">
              {initialData
                ? "Update project task details"
                : `Create a new task for ${project?.project_name || "this project"}`}
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
                    min={
                      project?.start_date
                        ? `${project.start_date}T00:00`
                        : undefined
                    }
                    max={
                      project?.end_date
                        ? `${project.end_date}T23:59`
                        : undefined
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
                    min={
                      formData.start_date ||
                      (project?.start_date
                        ? `${project.start_date}T00:00`
                        : undefined)
                    }
                    max={
                      project?.end_date
                        ? `${project.end_date}T23:59`
                        : undefined
                    }
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
                      onClick={openProjectTaskPriorityDialog}
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
                      {projectTaskPriorities.map((priority) => (
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

              {/* Managers and Assignees - Only from Project Team */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                <div className="space-y-4">
                  <div className="flex flex-col-reverse min-h-[120px]">
                    <div>
                      <Label className="text-base font-medium mb-2 block">
                        Task Leader (from Project Team)
                      </Label>
                      {formData.freeze_assignee && !canEditFrozenAssignees ? (
                        <ProtectedComponent
                          permissionCode={
                            PERMISSION_CODES.CAN_EDIT_FROZEN_ASSIGNEES
                          }
                        >
                          <SingleSelectPopover
                            items={getProjectUsers()}
                            disabled={false}
                            selectedId={formData.user_manager || null}
                            onSelectionChange={(id) => {
                              handleInputChange("user_manager", id || 0);
                              handleInputChange("user_assignees", []);
                            }}
                            placeholder="Select task leader from project team"
                            emptyMessage="No project members available"
                          />
                        </ProtectedComponent>
                      ) : null}

                      {(!formData.freeze_assignee ||
                        canEditFrozenAssignees) && (
                        <SingleSelectPopover
                          items={getProjectUsers()}
                          disabled={false}
                          selectedId={formData.user_manager || null}
                          onSelectionChange={(id) => {
                            handleInputChange("user_manager", id || 0);
                            handleInputChange("user_assignees", []);
                          }}
                          placeholder="Select task leader from project team"
                          emptyMessage="No project members available"
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
                        Assign To (from Project Team - Optional)
                      </Label>
                      {formData.freeze_assignee && !canEditFrozenAssignees ? (
                        <ProtectedComponent
                          permissionCode={
                            PERMISSION_CODES.CAN_EDIT_FROZEN_ASSIGNEES
                          }
                        >
                          <MultiSelectPopover
                            items={getProjectUsers()}
                            disabled={false}
                            selectedIds={formData.user_assignees || []}
                            onSelectionChange={(ids) =>
                              handleInputChange("user_assignees", ids)
                            }
                            placeholder="Select assignees from project team"
                            emptyMessage="No project members available"
                            className="text-xs sm:text-sm"
                          />
                        </ProtectedComponent>
                      ) : null}

                      {(!formData.freeze_assignee ||
                        canEditFrozenAssignees) && (
                        <MultiSelectPopover
                          items={getProjectUsers()}
                          disabled={false}
                          selectedIds={formData.user_assignees || []}
                          onSelectionChange={(ids) =>
                            handleInputChange("user_assignees", ids)
                          }
                          placeholder="Select assignees from project team"
                          emptyMessage="No project members available"
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

              {/* Project Task Statuses */}
              <div className="flex items-center gap-2 mb-6">
                <Label className="text-lg font-semibold text-gray-900 block">
                  Project Task Statuses
                </Label>
              </div>

              <div className="grid gap-4 md:grid-cols-3">
                {taskStatuses.map((status) => {
                  return (
                    <div
                      key={status.id}
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
                            id={`status-${status.id}`}
                            checked={status.is_current}
                            onCheckedChange={(checked) => {
                              if (checked) {
                                setTaskStatuses((prev) =>
                                  prev.map((st) => ({
                                    ...st,
                                    is_current: st.id === status.id,
                                  }))
                                );
                              }
                            }}
                            className="scale-75"
                          />
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
              {errors.task_statuses && (
                <p className="text-red-600 text-xs">{errors.task_statuses}</p>
              )}

              {/* Custom Fields */}
              {project?.custom_fields && project.custom_fields.length > 0 && (
                <>
                  <div className="border-t pt-4 mt-6">
                    <Label className="text-lg font-semibold text-gray-900 block mb-4">
                      Custom Fields
                    </Label>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                    {project.custom_fields.map((field, index) =>
                      renderCustomField(field, index)
                    )}
                  </div>
                </>
              )}
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
          <ProjectTaskPriorityDialog
            isOpen={projectTaskPriorityDialogOpen}
            onClose={() => setProjectTaskPriorityDialogOpen(false)}
            onSave={handleProjectTaskPrioritySaved}
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
