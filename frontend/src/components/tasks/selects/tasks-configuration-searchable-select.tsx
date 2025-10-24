"use client";

import { useSelector } from "react-redux";
import { useEffect, useState, useCallback, memo } from "react";
import PaginatedSearchableSelect, {
  PaginatedSelectItem,
} from "@/components/generic/paginated-searchable-select";
import { selectSelectedInstitution } from "@/store/auth/selectors-context-aware";
import { ITaskStandAloneStatuses } from "@/types/project.type";
import { TASK_STATUS_API } from "@/lib/utils";

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
  taskId?: number;
  excludedValues?: number[];
  taskStatuses?: ITaskStandAloneStatuses[];
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
    taskId,
    excludedValues = [],
    taskStatuses,
  }: TaskStatusSearchableSelectProps) => {
    const currentInstitution = useSelector(selectSelectedInstitution);
    const [selectedItems, setSelectedItems] =
      useState<Array<string | number>>(value);

    useEffect(() => {
      setSelectedItems(value);
    }, [value]);

    const fetchFirstPage = useCallback(
      async (query?: { search?: string; page?: number }) => {
        if (taskStatuses) {
          const searchTerm = query?.search?.toLowerCase() || "";
          const filtered = taskStatuses.filter((status) => {
            const matchesSearch = status.name
              ?.toLowerCase()
              .includes(searchTerm);
            const notExcluded = !excludedValues.includes(status.id);
            return matchesSearch && notExcluded;
          });

          return {
            results: filtered,
            count: filtered.length,
            next: null,
            previous: null,
          };
        }

        if (!currentInstitution) {
          throw new Error("No institution found!");
        }
        if (!taskId) {
          throw new Error("No task ID provided!");
        }

        const response = await TASK_STATUS_API.getPaginatedTaskStatuses({
          institutionId: currentInstitution.id,
          taskId: taskId,
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
      [currentInstitution, taskId, excludedValues, taskStatuses]
    );
    const handleSelect = useCallback(
      (
        itemId: string | number,
        _item: PaginatedSelectItem<ITaskStandAloneStatuses>
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
        _item: PaginatedSelectItem<ITaskStandAloneStatuses>
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
          ITaskStandAloneStatuses,
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
          disabled={disabled || !taskId}
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
