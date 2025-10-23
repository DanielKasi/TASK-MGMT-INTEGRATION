"use client";

import React, { useState, useEffect } from "react";
import { Plus, Save, X } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
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

// CSS for mobile-specific overrides
const responsiveStyles = `
  /* Smooth scrolling for touch devices */
  .custom-fields-modal .added-fields {
    -webkit-overflow-scrolling: touch;
  }

  @media (max-width: 640px) {
    .custom-fields-modal {
      width: 95vw !important; /* Override max-w-[400px] for mobile */
      padding: 0.75rem !important;
    }

    .custom-fields-modal .button-group {
      flex-direction: column !important; /* Stack buttons vertically */
      align-items: stretch;
    }

    .custom-fields-modal .added-fields {
      max-height: 30vh !important; /* Smaller scroll area for mobile */
    }

    /* Ensure the X button in Added Fields doesn't touch the task content */
    .custom-fields-modal .added-fields .field-item {
      display: flex;
      align-items: center;
      gap: 0.75rem; /* Add gap between content and button */
      padding-right: 0.5rem; /* Ensure space for the button */
    }

    .custom-fields-modal .added-fields .field-item .delete-button {
      flex-shrink: 0; /* Prevent button from shrinking */
      margin-left: 0.5rem; /* Add margin to separate from content */
      width: 2rem; /* Fixed width for consistency */
      height: 2rem; /* Fixed height for consistency */
    }

    /* Adjust the Dialog's close button position on small devices */
    .custom-fields-modal button[data-testid="dialog-close-button"] {
      top: 0.5rem !important; /* Push the close button up */
      right: 0.5rem !important; /* Maintain right alignment */
    }
  }
`;

// Inject styles (move to a .css file in production)
if (typeof document !== "undefined") {
  const styleSheet = document.createElement("style");
  styleSheet.innerText = responsiveStyles;
  document.head.appendChild(styleSheet);
}

interface ICustomField {
  label: string;
  type: "text" | "number" | "bool" | "date" | "select";
  required: boolean;
  multiple: boolean;
  defaultValue: number;
  options?: number[] | string[];
}

interface CustomFieldsModalProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  fields: ICustomField[];
  onFieldsChange: (fields: ICustomField[]) => void;
}

export function CustomFieldsModal({
  isOpen,
  onOpenChange,
  fields,
  onFieldsChange,
}: CustomFieldsModalProps) {
  const [fieldName, setFieldName] = useState("");
  const [fieldType, setFieldType] = useState<ICustomField["type"]>("text");
  const [fieldRequired, setFieldRequired] = useState(false);
  const [fieldMultiple, setFieldMultiple] = useState(false);
  const [options, setOptions] = useState<string[]>([""]);
  const [localFields, setLocalFields] = useState<ICustomField[]>(fields);

  useEffect(() => {
    setLocalFields(fields);
  }, [fields]);

  const addOption = () => {
    setOptions([...options, ""]);
  };

  const updateOption = (index: number, value: string) => {
    const newOptions = [...options];
    newOptions[index] = value;
    setOptions(newOptions);
  };

  const removeOption = (index: number) => {
    if (options.length > 1) {
      const newOptions = options.filter((_, i) => i !== index);
      setOptions(newOptions);
    }
  };

  const clearForm = () => {
    setFieldName("");
    setFieldType("text");
    setOptions([""]);
    setFieldRequired(false);
    setFieldMultiple(false);
  };

  const addField = () => {
    if (!fieldName.trim()) {
      return;
    }

    if (fieldType === "select" && !options.some((opt) => opt.trim())) {
      return;
    }

    const newField: ICustomField = {
      label: fieldName.trim(),
      type: fieldType,
      required: fieldRequired,
      multiple: fieldMultiple,
      defaultValue: 0,
    };

    if (fieldType === "select") {
      newField.options = options
        .filter((opt) => opt.trim())
        .map((opt) => opt.trim());
    }

    const newFields = [...localFields, newField];
    setLocalFields(newFields);
    clearForm();
  };

  const removeField = (index: number) => {
    setLocalFields(localFields.filter((_, i) => i !== index));
  };

  const handleSave = () => {
    onFieldsChange(localFields);
    onOpenChange(false);
  };

  const handleCancel = () => {
    setLocalFields(fields);
    clearForm();
    onOpenChange(false);
  };

  const handleTypeChange = (newType: ICustomField["type"]) => {
    setFieldType(newType);
    setOptions([""]);
    setFieldMultiple(false);
  };

  const isAddButtonEnabled = () => {
    if (!fieldName.trim()) {
      return false;
    }

    if (fieldType === "select" && !options.some((opt) => opt.trim())) {
      return false;
    }

    return true;
  };

  const getFieldTypeLabel = (type: string): string => {
    const typeLabels = {
      text: "Text",
      number: "Number",
      bool: "Boolean",
      date: "Date",
      select: "Select",
    };
    return typeLabels[type as keyof typeof typeLabels] || type;
  };

  const renderThirdField = () => {
    switch (fieldType) {
      case "text":
        return (
          <div className="space-y-3">
            <Label>Preview</Label>
            <div className="border-b border-gray-300 pb-2">
              <input
                type="text"
                placeholder="Text input field"
                className="w-full bg-transparent border-none outline-none text-sm min-h-10"
              />
            </div>
          </div>
        );

      case "number":
        return (
          <div className="space-y-3">
            <Label>Preview</Label>
            <div className="border-b border-gray-300 pb-2">
              <input
                type="number"
                placeholder="Number input field"
                className="w-full bg-transparent border-none outline-none text-sm min-h-10"
              />
            </div>
          </div>
        );

      case "bool":
        return (
          <div className="space-y-3">
            <Label>Preview</Label>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                className="rounded border-gray-300 h-5 w-5"
              />
              <span className="text-sm text-gray-600">Boolean field</span>
            </div>
          </div>
        );

      case "date":
        return (
          <div className="space-y-3">
            <Label>Preview</Label>
            <div className="border-b border-gray-300 pb-2">
              <input
                type="date"
                className="w-full bg-transparent border-none outline-none text-sm min-h-10"
              />
            </div>
          </div>
        );

      case "select":
        return (
          <div className="space-y-3">
            <Label>Options</Label>
            <div className="space-y-2">
              {options.map((option, index) => (
                <div key={index} className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded-sm border-2 border-gray-400 flex-shrink-0"></div>
                  <div className="flex-1 border-b border-gray-300 pb-1">
                    <input
                      type="text"
                      placeholder={`Option ${index + 1}`}
                      value={option}
                      onChange={(e) => updateOption(index, e.target.value)}
                      className="w-full bg-transparent border-none outline-none text-sm min-h-10"
                    />
                  </div>
                  {options.length > 1 && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => removeOption(index)}
                      className="h-8 w-8 p-0 text-gray-400 hover:text-red-600"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              ))}
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={addOption}
                className="text-blue-600 hover:text-blue-700 justify-start p-0 h-8"
              >
                Add option
              </Button>
            </div>
            <div className="flex items-center space-x-2 pt-2">
              <input
                type="checkbox"
                id="field-multiple"
                checked={fieldMultiple}
                onChange={(e) => setFieldMultiple(e.target.checked)}
                className="rounded border-gray-300 h-5 w-5"
              />
              <Label htmlFor="field-multiple" className="text-sm">
                Allow multiple selections
              </Label>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="custom-fields-modal max-w-[400px] max-h-[90vh] overflow-y-auto p-6 mt-3">
        <DialogHeader>
          <DialogTitle>Add Project Tasks Fields</DialogTitle>
          <DialogDescription>
            Create a custom field to set fields on project tasks
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-6">
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="field-name">Field Name</Label>
              <Input
                id="field-name"
                placeholder="e.g., Priority, Status, Department"
                value={fieldName}
                onChange={(e) => setFieldName(e.target.value)}
                className="min-h-10 text-base"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="field-type">Field Type</Label>
              <Select value={fieldType} onValueChange={handleTypeChange}>
                <SelectTrigger className="min-h-10 text-base">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="text">Text</SelectItem>
                  <SelectItem value="number">Number</SelectItem>
                  <SelectItem value="bool">Boolean</SelectItem>
                  <SelectItem value="date">Date</SelectItem>
                  <SelectItem value="select">Select</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center space-x-2 pt-2">
              <input
                type="checkbox"
                id="field-required"
                checked={fieldRequired}
                onChange={(e) => setFieldRequired(e.target.checked)}
                className="rounded border-gray-300 h-5 w-5"
              />
              <Label htmlFor="field-required" className="text-sm">
                Make this field required
              </Label>
            </div>

            <div className="pt-4">{renderThirdField()}</div>
          </div>

          {localFields.length > 0 && (
            <div className="space-y-3">
              <h4 className="font-medium text-base">
                Added Fields ({localFields.length})
              </h4>
              <div className="space-y-2 max-h-48 overflow-y-auto added-fields">
                {localFields.map((field, index) => (
                  <div
                    key={index}
                    className="field-item flex items-center justify-between p-3 border rounded-lg bg-gray-50"
                  >
                    <div className="flex-1">
                      <p className="font-medium text-sm">{field.label}</p>
                      <div className="flex items-center gap-2 mt-1 flex-wrap">
                        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                          {getFieldTypeLabel(field.type)}
                        </span>
                        {field.required && (
                          <span className="text-xs text-red-600">Required</span>
                        )}
                        {field.multiple && (
                          <span className="text-xs text-gray-600">
                            Multiple
                          </span>
                        )}
                        {field.options && (
                          <span className="text-xs text-gray-500">
                            {field.options.length} options
                          </span>
                        )}
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeField(index)}
                      className="delete-button h-8 w-8 p-0 text-red-600 hover:text-red-700 hover:bg-red-50"
                      aria-label={`Remove ${field.label} field`}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
        <div className="flex justify-between items-center gap-3 pt-4 button-group">
          <Button
            onClick={addField}
            disabled={!isAddButtonEnabled()}
            size="sm"
            variant="outline"
            className="min-h-10"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Field
          </Button>
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={handleCancel}
              className="min-h-10"
            >
              Cancel
            </Button>
            <Button
              onClick={handleSave}
              className="min-h-10 px-4 rounded-full text-sm flex items-center justify-center"
            >
              Save Fields ({localFields.length})
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
