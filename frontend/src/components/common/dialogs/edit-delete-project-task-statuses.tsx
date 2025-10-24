"use client";

import React, { useState, useEffect } from "react";
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
import { toast } from "sonner";
import { PROJECTS_API, showErrorToast } from "@/lib/utils";
import { IProjectTaskStatuses } from "@/types/project.type";
import { Edit, Trash2, X } from "lucide-react";
import { ConfirmationDialog } from "@/components/confirmation-dialog";
import { RichTextEditor } from "@/components/common/rich-editor";
import RichTextDisplay from "@/components/common/rich-text-display";
import {ProtectedComponent} from "@/platform/v1/components";
import { PERMISSION_CODES } from "@/constants";

interface ProjectTaskStatusDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: () => Promise<void>;
  projectId: number;
  statuses: IProjectTaskStatuses[];
}

export default function ProjectTaskStatusDialog({
  isOpen,
  onClose,
  onSave,
  projectId,
  statuses,
}: ProjectTaskStatusDialogProps) {
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    color_code: "#3b82f6",
  });
  const [editingStatus, setEditingStatus] =
    useState<IProjectTaskStatuses | null>(null);
  const [loading, setLoading] = useState(false);
  const [statusToDelete, setStatusToDelete] =
    useState<IProjectTaskStatuses | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Preset colors from the second snippet
  const PRESET_COLORS = [
    "#ef4444",
    "#f97316",
    "#f59e0b",
    "#eab308",
    "#84cc16",
    "#22c55e",
    "#10b981",
    "#14b8a6",
    "#06b6d4",
    "#0ea5e9",
    "#3b82f6",
    "#6366f1",
    "#8b5cf6",
    "#a855f7",
    "#d946ef",
    "#ec4899",
    "#64748b",
  ];

  useEffect(() => {
    if (!isOpen) {
      resetForm();
    }
  }, [isOpen]);

  useEffect(() => {
    if (editingStatus) {
      setFormData({
        name: editingStatus.name || "",
        description: editingStatus.description || "",
        color_code: editingStatus.color_code || "#3b82f6",
      });
    }
  }, [editingStatus]);

  const resetForm = () => {
    setFormData({
      name: "",
      description: "",
      color_code: "#3b82f6",
    });
    setEditingStatus(null);
    setErrors({});
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setErrors((prev) => ({ ...prev, [field]: "" }));
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = "Status name is required";
    }

    if (!formData.color_code) {
      newErrors.color_code = "Color is required";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setLoading(true);
    try {
      if (editingStatus) {
        await PROJECTS_API.updateProjectTaskStatuses({
          project_id: editingStatus.id,
          data: formData,
        });
        toast.success("Status updated successfully");
      }
      await onSave();
      resetForm();
    } catch (err) {
      showErrorToast({
        error: err,
        defaultMessage: `Failed to ${editingStatus ? "update" : "create"} status`,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!statusToDelete) return;

    setIsDeleting(true);
    try {
      await PROJECTS_API.deleteProjectTaskStatuses({
        project_id: statusToDelete.id,
      });
      toast.success("Status deleted successfully");
      await onSave();
      setStatusToDelete(null);
    } catch (err) {
      showErrorToast({
        error: err,
        defaultMessage: "Failed to delete status",
      });
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <ProtectedComponent
      permissionCode={PERMISSION_CODES.CAN_EDIT_PROJECT_STATUSES}
    >
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="w-full max-w-[95vw] sm:max-w-lg md:max-w-2xl lg:max-w-3xl p-4 sm:p-6 max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-base sm:text-lg md:text-xl font-semibold">
              Manage Task Statuses
            </DialogTitle>
            <DialogDescription className="text-xs sm:text-sm text-gray-600">
              Edit or delete existing task statuses for this project
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6 mt-4">
            {/* Existing Statuses List */}
            <div className="space-y-3">
              <h3 className="text-sm sm:text-base font-medium text-gray-900">
                Existing Statuses
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-[40vh] sm:max-h-[200px] overflow-y-auto pr-2">
                {statuses.map((status) => (
                  <div
                    key={status.id}
                    className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center gap-2 sm:gap-3 flex-1 min-w-0">
                      <div
                        className="w-4 h-4 sm:w-5 sm:h-5 rounded-full flex-shrink-0"
                        style={{ backgroundColor: status.color_code }}
                      />
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm sm:text-base truncate">
                          {status.name}
                        </p>
                        {status.description && (
                          <RichTextDisplay
                            htmlContent={status.description}
                            className="text-xs sm:text-sm text-gray-500 line-clamp-2"
                          />
                        )}
                      </div>
                    </div>
                    <div className="flex gap-1 sm:gap-2 flex-shrink-0">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-10 w-10 sm:h-8 sm:w-8"
                        onClick={() => setEditingStatus(status)}
                        aria-label={`Edit ${status.name}`}
                      >
                        <Edit className="h-5 w-5 sm:h-4 sm:w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-10 w-10 sm:h-8 sm:w-8 text-red-600 hover:text-red-700"
                        onClick={() => setStatusToDelete(status)}
                        aria-label={`Delete ${status.name}`}
                      >
                        <Trash2 className="h-5 w-5 sm:h-4 sm:w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Edit Form - Only shows when editing */}
            {editingStatus && (
              <form onSubmit={handleSubmit} className="space-y-4 border-t pt-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm sm:text-base font-medium text-gray-900 truncate">
                    Edit Status: {editingStatus.name}
                  </h3>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={resetForm}
                    className="h-10 w-10 flex-shrink-0"
                    aria-label="Cancel editing"
                  >
                    <X className="h-5 w-5" />
                  </Button>
                </div>

                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label
                      htmlFor="name"
                      className="text-xs sm:text-sm font-medium"
                    >
                      Status Name *
                    </Label>
                    <Input
                      id="name"
                      value={formData.name}
                      onChange={(e) =>
                        handleInputChange("name", e.target.value)
                      }
                      placeholder="Enter status name"
                      className="text-sm h-10"
                    />
                    {errors.name && (
                      <p className="text-red-600 text-xs">{errors.name}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label
                      htmlFor="description"
                      className="text-xs sm:text-sm font-medium"
                    >
                      Description
                    </Label>
                    <RichTextEditor
                      value={formData.description}
                      onChange={(value) =>
                        handleInputChange("description", value)
                      }
                      maxLength={1000}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label
                      htmlFor="color_code"
                      className="text-xs sm:text-sm font-medium"
                    >
                      Color *
                    </Label>
                    <div className="flex flex-wrap gap-1.5 sm:gap-2 mb-3">
                      {PRESET_COLORS.map((color) => (
                        <button
                          key={color}
                          type="button"
                          onClick={() => handleInputChange("color_code", color)}
                          className={`w-7 h-7 sm:w-8 sm:h-8 rounded-md border-2 transition-all ${
                            formData.color_code === color
                              ? "border-primary scale-110"
                              : "border-transparent"
                          }`}
                          style={{ backgroundColor: color }}
                          title={color}
                        />
                      ))}
                    </div>
                    <div className="flex gap-2">
                      <Input
                        id="color_code"
                        type="color"
                        value={formData.color_code}
                        onChange={(e) =>
                          handleInputChange("color_code", e.target.value)
                        }
                        className="w-16 sm:w-20 h-9 sm:h-10 p-1 cursor-pointer flex-shrink-0"
                      />
                      <Input
                        type="text"
                        placeholder="#000000"
                        value={formData.color_code}
                        onChange={(e) =>
                          handleInputChange("color_code", e.target.value)
                        }
                        className="flex-1 h-9 sm:h-10 text-sm"
                      />
                    </div>
                    {errors.color_code && (
                      <p className="text-red-600 text-xs">
                        {errors.color_code}
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row justify-end gap-3 pt-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={resetForm}
                    disabled={loading}
                    className="rounded-full text-sm h-10 w-full sm:w-auto"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    className="rounded-full text-sm h-10 w-full sm:w-auto"
                    disabled={loading}
                  >
                    {loading ? "Updating..." : "Update Status"}
                  </Button>
                </div>
              </form>
            )}

            {!editingStatus && (
              <div className="text-center py-6 text-sm sm:text-base text-gray-500">
                Click the edit icon on a status to modify it
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {statusToDelete && (
        <ConfirmationDialog
          isOpen={!!statusToDelete}
          title={`Delete ${statusToDelete.name}`}
          description="Are you sure you want to delete this status? Tasks using this status may be affected."
          onConfirm={handleDelete}
          onClose={() => setStatusToDelete(null)}
          disabled={isDeleting}
        />
      )}
    </ProtectedComponent>
  );
}
