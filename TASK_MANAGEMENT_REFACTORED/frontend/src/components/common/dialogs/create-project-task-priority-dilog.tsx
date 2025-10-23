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
import {
  showErrorToast,
  showSuccessToast,
  PROJECT_TASK_PRIORITY_API,
  
} from "@/lib/utils";
import type {
  IProjectTaskPriority,
  IProjectTaskPriorityFormData,
} from "@/types/project.type";
import { useSelector } from "react-redux";
import { selectSelectedInstitution } from "@/store/auth/selectors-context-aware";
import { RichTextEditor } from "../rich-editor";

interface ProjectTaskPriorityDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: () => void;
  initialData?: IProjectTaskPriority | null;
}

export function ProjectTaskPriorityDialog({
  isOpen,
  onClose,
  onSave,
  initialData,
}: ProjectTaskPriorityDialogProps) {
  const [priorityName, setPriorityName] = useState("");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);
  const [weight, setWeight] = useState<number | undefined>(undefined);
  const [colorCode, setColorCode] = useState("#000000");
  const currentInstitution = useSelector(selectSelectedInstitution);

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
    if (initialData) {
      setPriorityName(initialData.name);
      setDescription(initialData.description || "");
      setWeight(initialData.weight);
      setColorCode(initialData.color_code || "#000000");
    } else {
      resetForm();
    }
  }, [initialData, isOpen]);

  const resetForm = () => {
    setPriorityName("");
    setDescription("");
    setWeight(undefined);
    setColorCode("#000000");
  };
  const handleClose = () => {
    resetForm();
    onClose();
  };

  const handleSave = async () => {
    if (!priorityName.trim()) {
      showErrorToast({
        error: null,
        defaultMessage: "Priority name is required",
      });
      return;
    }

    if (!weight || weight <= 0) {
      showErrorToast({
        error: null,
        defaultMessage: "Weight must be greater than 0",
      });
      return;
    }
    try {
      setSaving(true);

      const priorityData: Partial<IProjectTaskPriorityFormData> = {
        name: priorityName,
        description: description,
        weight: weight,
        color_code: colorCode,
        is_active: true,
        institution: currentInstitution?.id,
        approval_status: initialData ? "under_update" : "under_creation",
      };

      if (initialData) {
        await PROJECT_TASK_PRIORITY_API.update({
          task_priority_id: initialData.id,
          data: priorityData,
        });
        showSuccessToast("Task priority updated successfully!");
      } else {
        await PROJECT_TASK_PRIORITY_API.create({ data: priorityData });
        showSuccessToast("Task priority created successfully!");
      }

      onSave();
      handleClose();
    } catch (e: any) {
      showErrorToast({
        error: e,
        defaultMessage: "Failed to save task priority",
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-[90vw] sm:max-w-xl md:max-w-2xl lg:max-w-3xl rounded-xl p-4 sm:p-6">
        <DialogHeader>
          <DialogTitle className="text-lg sm:text-xl">
            {initialData ? "Edit Project Task Priority" : "Create Project Task Priority"}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 sm:space-y-6 py-4 px-2 sm:px-4 overflow-y-auto max-h-[60vh] sm:max-h-[60svh]">
          <div>
            <label className="block text-xs sm:text-sm font-medium mb-2">
              Priority Name <span className="text-destructive">*</span>
            </label>
            <Input
              placeholder="e.g., High, Medium, Low, Critical..."
              value={priorityName}
              onChange={(e) => setPriorityName(e.target.value)}
              className="h-9 sm:h-10 text-sm"
            />
          </div>

          <div>
            <label className="block text-xs sm:text-sm font-medium mb-2">
              Description
            </label>
            <RichTextEditor
              value={description || ""}
              onChange={(value) => setDescription(value || "")}
              placeholder="Enter your description..."
              disabled={false}
              maxLength={1000}
            />
          </div>

          <div>
            <label className="block text-xs sm:text-sm font-medium mb-2">
              Weight <span className="text-destructive">*</span>
            </label>
            <Input
              type="number"
              value={weight === undefined ? "" : weight}
              onChange={(e) => {
                const val = e.target.value;
                setWeight(val === "" ? undefined : Number(val));
              }}
              className="h-9 sm:h-10 text-sm"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Higher numbers indicate higher priority
            </p>
          </div>

          <div>
            <label className="block text-xs sm:text-sm font-medium mb-2">
              Color
            </label>
            <div className="flex flex-wrap gap-1.5 sm:gap-2 mb-3">
              {PRESET_COLORS.map((color) => (
                <button
                  key={color}
                  type="button"
                  onClick={() => setColorCode(color)}
                  className={`w-7 h-7 sm:w-8 sm:h-8 rounded-md border-2 transition-all ${
                    colorCode === color
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
                type="color"
                value={colorCode}
                onChange={(e) => setColorCode(e.target.value)}
                className="w-16 sm:w-20 h-9 sm:h-10 p-1 cursor-pointer flex-shrink-0"
              />
              <Input
                type="text"
                placeholder="#000000"
                value={colorCode}
                onChange={(e) => setColorCode(e.target.value)}
                className="flex-1 h-9 sm:h-10 text-sm"
              />
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button
            className="w-full rounded-full h-9 sm:h-10 text-sm"
            onClick={handleSave}
            disabled={saving}
          >
            {saving
              ? "Saving..."
              : initialData
                ? "Update Priority"
                : "Create Priority"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
