"use client";

import { Avatar, AvatarFallback, AvatarImage } from "@/platform/v1/components";
import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

export const AssigneeAvatarsWithTooltip = ({
  assignees,
  projectId,
}: {
  assignees: Array<{ id: number; name: string; avatar_url?: string }>;
  projectId?: number;
}) => {
  const [open, setOpen] = useState(false);
  const triggerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const params = useParams();
  const effectiveProjectId =
    projectId || (params.project_id ? Number(params.project_id) : undefined);

  const toggle = () => setOpen((prev) => !prev);
  const close = () => setOpen(false);

  // Close on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        triggerRef.current &&
        !triggerRef.current.contains(event.target as Node) &&
        tooltipRef.current &&
        !tooltipRef.current.contains(event.target as Node)
      ) {
        close();
      }
    };

    if (open) {
      document.addEventListener("mousedown", handleClickOutside);
      return () =>
        document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [open]);

  if (assignees.length === 0) {
    return <span className="text-xs text-gray-500">No assignees</span>;
  }

  const visibleAvatars = assignees.slice(0, 2);
  const extraCount = assignees.length - 2;

  return (
    <div className="relative">
      <div
        className="flex -space-x-1 cursor-pointer"
        onClick={toggle}
        ref={triggerRef}
      >
        {visibleAvatars.map((assignee) => (
          <Avatar
            key={assignee.id}
            className="h-6 w-6 border-2 border-white rounded-full"
          >
            <AvatarImage
              src={assignee.avatar_url || "/images/profile-placeholder.jpg"}
            />
            <AvatarFallback className="text-xs bg-gray-300">
              {assignee.name?.[0]?.toUpperCase() || "?"}
            </AvatarFallback>
          </Avatar>
        ))}
        {extraCount > 0 && (
          <div className="flex h-6 w-6 items-center justify-center rounded-full border-2 border-white bg-gray-200 text-xs font-medium">
            +{extraCount}
          </div>
        )}
      </div>

      {open && (
        <div
          ref={tooltipRef}
          className="fixed z-[99999] bg-white border rounded-md shadow-lg p-2 min-w-[160px]"
          style={{
            top: triggerRef.current?.getBoundingClientRect().top
              ? `${triggerRef.current.getBoundingClientRect().top - 10}px`
              : "0px",
            left: triggerRef.current?.getBoundingClientRect().left
              ? `${triggerRef.current.getBoundingClientRect().left}px`
              : "0px",
            transform: "translateY(-100%)",
          }}
        >
          <div className="text-xs font-medium text-gray-700 mb-1">
            Assignees:
          </div>
          <div className="space-y-1">
            {assignees.map((a) => {
              const queryParams = new URLSearchParams({ q: a.id.toString() });
              if (effectiveProjectId) {
                queryParams.append("project_id", effectiveProjectId.toString());
              }
              const linkUrl = effectiveProjectId
                ? `/projects/${effectiveProjectId}/tasks?q=${a.id}`
                : `/task-mgt/task/user-tasks?${queryParams.toString()}`;

              return (
                <Link
                  key={a.id}
                  href={linkUrl}
                  className="flex items-center gap-2 hover:bg-gray-100 p-1 rounded cursor-pointer transition-colors"
                  onClick={close}
                >
                  <Avatar className="h-5 w-5">
                    <AvatarImage
                      src={a.avatar_url || "/images/profile-placeholder.jpg"}
                    />
                    <AvatarFallback>
                      {a.name?.[0]?.toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <span className="text-sm">{a.name}</span>
                </Link>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
