import { useDroppable } from "@dnd-kit/core";
import { IProjectTask } from "@/types/types.utils";
import { DraggableTaskCard } from "@/components/common/draggable-task-card";

interface DroppableStatusColumnProps {
  statusId: number;
  statusName: string;
  tasks: IProjectTask[];
  projectId: number;
  taskActionsDropdown: (task: IProjectTask) => React.ReactNode;
}

export function DroppableStatusColumn({
  statusId,
  statusName,
  tasks,
  projectId,
  taskActionsDropdown,
}: DroppableStatusColumnProps) {
  const { setNodeRef, isOver } = useDroppable({
    id: statusId,
  });

  return (
    <div className="w-64 sm:w-72 flex-shrink-0">
      <div className="mb-3 sm:mb-4 p-2 flex items-center justify-start gap-2 sm:gap-4 rounded-xl bg-gray-100">
        <h3 className="font-medium text-xs sm:text-sm">{statusName}</h3>
        <span className="text-xs sm:text-sm text-gray-600">
          ({tasks.length})
        </span>
      </div>
      <div
        ref={setNodeRef}
        className={`space-y-2 sm:space-y-3 max-h-[500px] overflow-y-auto p-3 rounded-lg transition-all duration-300 min-h-[200px] ${
          isOver
            ? "border-2 border-blue-400 border-dashed"
            : "border-2 border-transparent"
        }`}
      >
        {tasks.map((task) => (
          <DraggableTaskCard
            key={task.id}
            task={task}
            projectId={projectId}
            actions={taskActionsDropdown(task)}
          />
        ))}
      </div>
    </div>
  );
}