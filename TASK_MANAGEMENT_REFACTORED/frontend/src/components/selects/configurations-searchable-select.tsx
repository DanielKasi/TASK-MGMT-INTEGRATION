"use client";

import { useSelector } from "react-redux";
import { useEffect, useState, useCallback, memo } from "react";
import PaginatedSearchableSelect, {
  PaginatedSelectItem,
} from "@/components/generic/paginated-searchable-select";
import { selectSelectedInstitution } from "@/store/auth/selectors-context-aware";
import { IProjectTaskStatuses } from "@/types/project.type";
import { PROJECTS_API } from "@/lib/utils";

export interface TaskStatusSearchableSelectProps {
  value: (string | number)[];
  onValueChange: (value: (string | number)[]) => void;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
  triggerClassName?: string;
  multiple?: boolean;
  hideSelectedFromList?: boolean;
  showSelectedItems?: boolean;
  projectId?: number;
  excludedValues?: number[];
}

export const TaskStatusSearchableSelect = memo(
  ({
    value,
    onValueChange,
    disabled = false,
    showSelectedItems = true,
    className,
    triggerClassName,
    multiple = false,
    placeholder = `Select task status${multiple ? "es" : ""}`,
    hideSelectedFromList = false,
    projectId,
    excludedValues = [],
  }: TaskStatusSearchableSelectProps) => {
    const currentInstitution = useSelector(selectSelectedInstitution);
    const [selectedItems, setSelectedItems] =
      useState<Array<string | number>>(value);

    useEffect(() => {
      setSelectedItems(value);
    }, [value]);

    const fetchFirstPage = useCallback(
      async (query?: { search?: string; page?: number }) => {
        if (!currentInstitution) {
          throw new Error("No institution found!");
        }
        if (!projectId) {
          throw new Error("No project ID provided!");
        }

        const response = await PROJECTS_API.getPaginatedProjectsTaskStatuses({
          institutionId: currentInstitution.id,
          project: projectId,
          ...query,
        });

        const filtered = {
          ...response,
          results: response.results.filter(
            (status) => !excludedValues.includes(status.id)
          ),
        };

        return filtered;
      },
      [currentInstitution, projectId, excludedValues]
    );

    const handleSelect = useCallback(
      (
        itemId: string | number,
        _item: PaginatedSelectItem<IProjectTaskStatuses>
      ) => {
        if (!selectedItems.includes(itemId)) {
          if (multiple) {
            onValueChange([...selectedItems, itemId]);
          } else {
            onValueChange([itemId]);
          }
        }
      },
      [multiple, selectedItems, onValueChange]
    );

    const handleRemove = useCallback(
      (
        itemId: string | number,
        _item: PaginatedSelectItem<IProjectTaskStatuses>
      ) => {
        const newItems = selectedItems.filter(
          (id) => String(id) !== String(itemId)
        );
        setSelectedItems(newItems);
        onValueChange(newItems);
      },
      [selectedItems, onValueChange]
    );

    return (
      <div className={className}>
        <PaginatedSearchableSelect<
          IProjectTaskStatuses,
          { search?: string; page?: number }
        >
          paginated
          fetchFirstPage={fetchFirstPage}
          getItemId={(taskStatus) => taskStatus.id}
          getItemLabel={(taskStatus) => taskStatus.name || ""}
          getItemValue={(taskStatus) => taskStatus.id.toString()}
          selectedItems={selectedItems}
          onSelect={handleSelect}
          onRemove={handleRemove}
          showSelectedItems={showSelectedItems}
          multiple={multiple}
          disabled={disabled || !projectId}
          placeholder={placeholder}
          searchPlaceholder="Search task statuses by name"
          triggerClassName={`w-full justify-between focus:ring-orange-500 focus:border-orange-500 ${triggerClassName || ""}`}
          popoverClassName="w-full"
          hideSelectedFromList={hideSelectedFromList}
        />
      </div>
    );
  }
);

TaskStatusSearchableSelect.displayName = "TaskStatusSearchableSelect";

export default TaskStatusSearchableSelect;
