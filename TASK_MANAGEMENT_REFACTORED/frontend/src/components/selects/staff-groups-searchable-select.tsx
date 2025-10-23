"use client";

import { useSelector } from "react-redux";
import { useEffect, useState, useCallback, memo } from "react";
import PaginatedSearchableSelect, {
  PaginatedSelectItem,
} from "@/components/generic/paginated-searchable-select";
import { selectSelectedInstitution } from "@/store/auth/selectors-context-aware";
import { USER_GROUPS_API } from "@/lib/api/approvals/utils";
import { IUserGroup } from "@/types/approvals.types";

interface StaffGroupsSearchableSelectProps {
  value: (string | number)[];
  onValueChange: (value: (string | number)[]) => void;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
  triggerClassName?: string;
  multiple?: boolean;
  hideSelectedFromList?: boolean;
  showSelectedItems?: boolean;
}

export const StaffGroupsSearchableSelect = memo(
  ({
    value,
    onValueChange,
    disabled = false,
    showSelectedItems = true,
    placeholder = "Select employee(s)",
    className,
    triggerClassName,
    multiple = false,
    hideSelectedFromList = false,
  }: StaffGroupsSearchableSelectProps) => {
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
        return await USER_GROUPS_API.fetchAll({ ...query });
      },
      [currentInstitution]
    );

    const fetchFromUrl = useCallback(async ({ url }: { url: string }) => {
      return await USER_GROUPS_API.fetchFromUrl({ url });
    }, []);

    const handleSelect = useCallback(
      (itemId: string | number, _item: PaginatedSelectItem<IUserGroup>) => {
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
      (itemId: string | number, _item: PaginatedSelectItem<IUserGroup>) => {
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
        <PaginatedSearchableSelect<IUserGroup, { search?: string; page?: number }>
          paginated
          fetchFirstPage={fetchFirstPage}
          fetchFromUrl={fetchFromUrl}
          getItemId={(user_group) => user_group.id}
          getItemLabel={(user_group) => user_group.name || ""}
          getItemValue={(user_group) => user_group.id.toString()}
          selectedItems={selectedItems}
          onSelect={handleSelect}
          onRemove={handleRemove}
          showSelectedItems={showSelectedItems}
          multiple={multiple}
          disabled={disabled}
          placeholder={placeholder}
          searchPlaceholder="Search profiles by name"
          triggerClassName={`w-full justify-between focus:ring-orange-500 focus:border-orange-500 ${triggerClassName || ""}`}
          popoverClassName="w-full"
          hideSelectedFromList={hideSelectedFromList}
        />
      </div>
    );
  }
);

StaffGroupsSearchableSelect.displayName = "StaffGroupsSearchableSelect";

export default StaffGroupsSearchableSelect;
