"use client";

import { useState } from "react";
import { Edit2, Trash2, Check, X } from "lucide-react";
import { Avatar, AvatarFallback } from "@/platform/v1/components";
import { Button } from "@/platform/v1/components";
import type { IProjectChatMessage } from "@/types/project.type";
import { formatDistanceToNow } from "date-fns";

interface ChatMessageItemProps {
  message: IProjectChatMessage;
  isCurrentUser: boolean;
  onEdit?: (messageId: number, newContent: string) => void;
  onDelete?: (messageId: number) => void;
}

const getUserColor = (userId: number) => {
  const colors = [
    "bg-slate-400",
    "bg-gray-400",
    "bg-zinc-400",
    "bg-neutral-400",
    "bg-stone-400",
  ];
  return colors[userId % colors.length];
};

export function ChatMessageItem({
  message,
  isCurrentUser,
  onEdit,
  onDelete,
}: ChatMessageItemProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState(message.content);

  const handleSaveEdit = () => {
    if (editedContent.trim() && onEdit) {
      onEdit(message.id, editedContent.trim());
      setIsEditing(false);
    }
  };

  const handleCancelEdit = () => {
    setEditedContent(message.content);
    setIsEditing(false);
  };

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <div
      className={`flex gap-2 mb-1 ${isCurrentUser ? "flex-row-reverse" : "flex-row"}`}
    >
      <Avatar
        className={`h-8 w-8 flex-shrink-0 ${getUserColor(message.author ?? 0)}`}
      >
        <AvatarFallback
          className={`text-xs font-medium text-white ${getUserColor(message.author ?? 0)}`}
        >
          {getInitials(message.author_name)}
        </AvatarFallback>
      </Avatar>

      <div
        className={`flex flex-col gap-1 max-w-[75%] ${isCurrentUser ? "items-end" : "items-start"}`}
      >
        <div
          className={`flex items-center gap-1.5 px-1 ${isCurrentUser ? "flex-row-reverse" : "flex-row"}`}
        >
          <span className="text-xs font-medium text-foreground/80">
            {message.author_name}
          </span>
          <span className="text-[10px] text-muted-foreground">
            {formatDistanceToNow(new Date(message.created_at), {
              addSuffix: true,
            })}
          </span>
          {message.is_edited && (
            <span className="text-[10px] text-muted-foreground italic">
              (edited)
            </span>
          )}
        </div>

        <div className="flex flex-col gap-1.5 w-full">
          <div
            className={`rounded-lg px-3 py-2 shadow-sm ${
              isCurrentUser
                ? "bg-[#d9fdd3] text-gray-900"
                : "bg-white text-gray-900 border border-gray-100"
            }`}
          >
            {isEditing ? (
              <div className="space-y-2">
                <textarea
                  value={editedContent}
                  onChange={(e) => setEditedContent(e.target.value)}
                  className="w-full min-h-[80px] p-2 text-sm rounded-lg border bg-background text-foreground resize-none focus:outline-none focus:ring-2 focus:ring-ring"
                  autoFocus
                />
              </div>
            ) : (
              <p className="text-sm whitespace-pre-wrap break-words leading-relaxed">
                {message.content}
              </p>
            )}
          </div>

          {isCurrentUser && (onEdit || onDelete) && (
            <div
              className={`flex items-center gap-1 ${isCurrentUser ? "justify-end" : "justify-start"}`}
            >
              {isEditing ? (
                <>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={handleCancelEdit}
                    className="h-7 px-2 text-xs gap-1"
                  >
                    <X className="h-3 w-3" />
                    Cancel
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleSaveEdit}
                    className="h-7 px-2 text-xs gap-1 bg-[#25d366] hover:bg-[#20bd5a] text-white"
                  >
                    <Check className="h-3 w-3" />
                    Save
                  </Button>
                </>
              ) : (
                <>
                  {onEdit && (
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => setIsEditing(true)}
                      className="h-7 px-2 text-xs gap-1 text-muted-foreground hover:text-foreground"
                    >
                      <Edit2 className="h-3 w-3" />
                      Edit
                    </Button>
                  )}
                  {onDelete && (
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => onDelete(message.id)}
                      className="h-7 px-2 text-xs gap-1 text-muted-foreground hover:text-destructive"
                    >
                      <Trash2 className="h-3 w-3" />
                      Delete
                    </Button>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
