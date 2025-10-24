"use client";

import { useState } from "react";
import { Check, ChevronDown, X } from "lucide-react";

import { Button } from "@/platform/v1/components";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/platform/v1/components";
import { Badge } from "@/platform/v1/components";
import { cn } from "@/lib/utils";

interface MultiSelectItem {
  id: number;
  name: string;
  label?: string;
}

interface MultiSelectPopoverProps {
  items: MultiSelectItem[];
  selectedIds: number[];
  onSelectionChange: (ids: number[]) => void;
  placeholder?: string;
  emptyMessage?: string;
  maxHeight?: string;
  className?: string;
  disabled?: boolean;
}

export function MultiSelectPopover({
  items,
  selectedIds,
  onSelectionChange,
  placeholder = "Select items...",
  emptyMessage = "No items available",
  maxHeight = "200px",
  disabled = false,
}: MultiSelectPopoverProps) {
  const [open, setOpen] = useState(false);

  const toggleItem = (id: number) => {
    if (disabled) return;
    const newSelection = selectedIds.includes(id)
      ? selectedIds.filter((selectedId) => selectedId !== id)
      : [...selectedIds, id];

    onSelectionChange(newSelection);
  };

  const removeItem = (id: number) => {
    if (disabled) return;
    onSelectionChange(selectedIds.filter((selectedId) => selectedId !== id));
  };

  const selectedItems = items.filter((item) => selectedIds.includes(item.id));

  return (
    <div className="space-y-2">
      {/* Selected items display */}
      {selectedItems.length > 0 && (
        <div className="flex flex-wrap gap-1 max-h-[60px] overflow-y-auto">
          {selectedItems.map((item) => (
            <Badge key={item.id} variant="secondary" className="text-xs">
              {item.label || item.name}
              {!disabled && ( 
                <button
                  type="button"
                  className="ml-1 hover:bg-secondary-foreground/20 rounded-full p-0.5"
                  onClick={() => removeItem(item.id)}
                >
                  <X className="h-3 w-3" />
                </button>
              )}
            </Badge>
          ))}
        </div>
      )}
      <Popover open={open} onOpenChange={disabled ? undefined:setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            role="combobox"
            aria-expanded={open}
            disabled={disabled}
            className="w-full h-[40px] justify-between text-left font-normal bg-transparent rounded-xl"
          >
            <span className="truncate">
              {selectedIds.length === 0
                ? placeholder
                : `${selectedIds.length} item${selectedIds.length === 1 ? "" : "s"} selected`}
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
                      selectedIds.includes(item.id) && "bg-accent"
                    )}
                    onClick={() => toggleItem(item.id)}
                  >
                    <div
                      className={cn(
                        "flex h-4 w-4 items-center justify-center rounded-sm border border-primary",
                        selectedIds.includes(item.id)
                          ? "bg-primary text-primary-foreground"
                          : "opacity-50"
                      )}
                    >
                      {selectedIds.includes(item.id) && (
                        <Check className="h-3 w-3" />
                      )}
                    </div>
                    <span className="flex-1">{item.label || item.name}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </PopoverContent>
      </Popover>
    </div>
  );
}
