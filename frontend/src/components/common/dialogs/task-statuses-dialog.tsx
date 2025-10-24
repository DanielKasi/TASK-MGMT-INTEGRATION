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
import { showErrorToast } from "@/lib/utils";
import type { IProjectTaskStatusFormData } from "@/types/project.type";
import { RichTextEditor } from "../rich-editor";

interface TaskStatusDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSave: (status: IProjectTaskStatusFormData) => void;
  initialData?: IProjectTaskStatusFormData | null;
}

export function TaskStatusDialog({
  open,
  onOpenChange,
  onSave,
  initialData = null,
}: TaskStatusDialogProps) {
  const [statusName, setStatusName] = useState("");
  const [description, setDescription] = useState("");
  const [colorCode, setColorCode] = useState("#000000");
  const [weight, setWeight] = useState<number | undefined>(undefined);

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
    if (open) {
      if (initialData) {
        // Editing mode: preload values
        setStatusName(initialData.name || "");
        setDescription(initialData.description || "");
        setColorCode(initialData.color_code || "#000000");
        setWeight(initialData.weight || undefined);
      } else {
        // Creating mode: reset
        resetForm();
      }
    }
  }, [open, initialData]);

  const resetForm = () => {
    setStatusName("");
    setDescription("");
    setColorCode("#000000");
    setWeight(undefined);
  };

  const handleClose = () => {
    resetForm();
    onOpenChange(false);
  };

  const handleSave = () => {
    if (!statusName.trim()) {
      showErrorToast({
        error: null,
        defaultMessage: "Status name is required",
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

    const statusData: IProjectTaskStatusFormData = {
      id: Date.now(),
      name: statusName,
      description: description,
      color_code: colorCode,
      weight: weight,
    };

    onSave(statusData);
    handleClose();
  };

  const isEditMode = Boolean(initialData);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[90vw] sm:max-w-xl md:max-w-2xl lg:max-w-3xl rounded-xl p-4 sm:p-6">
        <DialogHeader>
          <DialogTitle className="text-base sm:text-lg md:text-xl">
            {isEditMode ? "Edit Task Status" : "Create Task Status"}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 sm:space-y-6 py-4 px-2 sm:px-4 overflow-y-auto max-h-[60vh] sm:max-h-[60svh]">
          <div className="space-y-2 sm:space-y-3">
            <label className="block text-xs sm:text-sm font-medium">
              Status Name <span className="text-destructive">*</span>
            </label>
            <Input
              placeholder="e.g., Planning, In Progress, Completed..."
              value={statusName}
              onChange={(e) => setStatusName(e.target.value)}
              className="h-10 sm:h-12 text-sm sm:text-base"
            />
          </div>

          <div className="space-y-2 sm:space-y-3">
            <label className="block text-xs sm:text-sm font-medium">
              Description
            </label>
            <RichTextEditor
              value={description}
              onChange={(value) => setDescription(value)}
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

        <DialogFooter className="flex flex-col sm:flex-row sm:space-x-2 gap-2 sm:gap-0">
          <Button
            variant="outline"
            onClick={handleClose}
            className="w-full sm:w-auto rounded-full text-xs sm:text-sm"
          >
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            className="w-full sm:w-auto rounded-full text-xs sm:text-sm"
          >
            {isEditMode ? "Save Changes" : "Create Status"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
