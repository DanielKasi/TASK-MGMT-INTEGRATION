"use client";

import { useSelector } from "react-redux";
import { useEffect, useState, useCallback, memo } from "react";
import PaginatedSearchableSelect, {
  PaginatedSelectItem,
} from "@/components/generic/paginated-searchable-select";
import { selectSelectedInstitution } from "@/store/auth/selectors-context-aware";
import { IUser } from "@/types/user.types";
import { usersAPI } from "@/lib/utils";

interface UserSearchableSelectProps {
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

export const UserSearchableSelect = memo(
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
  }: UserSearchableSelectProps) => {
    const currentInstitution = useSelector(selectSelectedInstitution);
    const [selectedItems, setSelectedItems] =
      useState<Array<string | number>>(value);
    const [pendingChange, setPendingChange] = useState<Array<
      string | number
    > | null>(null);

    useEffect(() => {
      setSelectedItems(value);
    }, [value]);

    useEffect(() => {
      if (pendingChange !== null) {
        onValueChange(pendingChange);
        setPendingChange(null);
      }
    }, [pendingChange, onValueChange]);

    const fetchFirstPage = useCallback(
      async (query?: { search?: string; page?: number }) => {
        if (!currentInstitution) {
          throw new Error("No institution found!");
        }
        return await usersAPI.getPaginatedUsers({ ...query });
      },
      [currentInstitution]
    );

    const fetchFromUrl = useCallback(async ({ url }: { url: string }) => {
      return await usersAPI.getPaginatedUsersFromUrl({ url });
    }, []);

    const handleSelect = useCallback(
      (itemId: string | number, _item: PaginatedSelectItem<IUser>) => {
        setSelectedItems((currentItems) => {
          if (!currentItems.includes(itemId)) {
            const newItems = multiple ? [...currentItems, itemId] : [itemId];
            setPendingChange(newItems);
            return newItems;
          }
          return currentItems;
        });
      },
      [multiple]
    );

    const handleRemove = useCallback(
      (itemId: string | number, _item: PaginatedSelectItem<IUser>) => {
        setSelectedItems((currentItems) => {
          const newItems = currentItems.filter(
            (id) => String(id) !== String(itemId)
          );
          setPendingChange(newItems);
          return newItems;
        });
      },
      []
    );

    return (
      <div className={className}>
        <PaginatedSearchableSelect<IUser, { search?: string; page?: number }>
          paginated
          fetchFirstPage={fetchFirstPage}
          fetchFromUrl={fetchFromUrl}
          getItemId={(user) => user.id}
          getItemLabel={(user) => user?.fullname || ""}
          getItemValue={(user) => user.id.toString()}
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

UserSearchableSelect.displayName = "UserSearchableSelect";

export default UserSearchableSelect;
