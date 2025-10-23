import { useDraggable } from "@dnd-kit/core";
import { Card } from "@/platform/v1/components";
import { Badge } from "@/platform/v1/components";
import { IProjectTask } from "@/types/types.utils";
import { AssigneeAvatarsWithTooltip } from "@/components/common/assignee-avatar-with-tooltip";

interface DraggableTaskCardProps {
  task: IProjectTask;
  projectId: number;
  actions: React.ReactNode;
}

export function DraggableTaskCard({
  task,
  projectId,
  actions,
}: DraggableTaskCardProps) {
  const { attributes, listeners, setNodeRef, transform, isDragging } =
    useDraggable({
      id: task.id,
      data: {
        type: "task",
        task,
      },
    });

  const style = transform
    ? {
        transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
        opacity: isDragging ? 0.5 : 1,
        zIndex: isDragging ? 50 : 1,
      }
    : undefined;

  return (
    <div ref={setNodeRef} style={style}>
      <Card
        className={`p-3 sm:p-4 rounded-xl border shadow-sm hover:shadow-md transition-shadow duration-200 ${
          isDragging ? "cursor-grabbing shadow-xl" : "cursor-grab"
        }`}
        {...attributes}
        {...listeners}
      >
        <div className="flex justify-between items-start">
          <h4 className="font-medium text-xs sm:text-sm">{task.task_name}</h4>
          <div
            onPointerDown={(e) => e.stopPropagation()}
            onClick={(e) => e.stopPropagation()}
            onMouseDown={(e) => e.stopPropagation()}
            onTouchStart={(e) => e.stopPropagation()}
          >
            {actions}
          </div>
        </div>
        <div className="mt-2 sm:mt-3 flex justify-between items-end">
          <Badge
            style={{
              backgroundColor: task.priority?.color
                ? `${task.priority.color}30`
                : "rgba(120, 120, 120, 0.3)",
              color: task.priority?.color || "rgba(120, 120, 120, 1)",
              border: `1.5px solid ${task.priority?.color || "rgba(120, 120, 120, 1)"}`,
            }}
            className="..."
          >
            {task.priority?.name || "No Priority"}
          </Badge>
          <AssigneeAvatarsWithTooltip
            assignees={task.user_assignees}
            projectId={projectId}
          />
        </div>
      </Card>
    </div>
  );
}
