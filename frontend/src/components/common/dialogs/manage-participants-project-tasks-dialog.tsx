"use client";

import { useState } from "react";
import {
  Users,
  Eye,
  MessageSquare,
  Trash2,
  Shield,
  Loader2,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/platform/v1/components";
import { Button } from "@/platform/v1/components";
import { Avatar, AvatarFallback, AvatarImage } from "@/platform/v1/components";
import { Badge } from "@/platform/v1/components";
import { ScrollArea } from "@/platform/v1/components";
import { Switch } from "@/platform/v1/components";
import { toast } from "sonner";
import { showErrorToast } from "@/lib/utils";
import { PROJECT_TASK_DISCUSSION_PARTICIPANT_API } from "@/lib/utils.chats";
import { IProjectChatDiscussionParticipants } from "@/types/project.type";
import { ConfirmationDialog } from "@/components/confirmation-dialog";

interface ManageParticipantsDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  taskId: number;
  participants: IProjectChatDiscussionParticipants[];
  taskAssignees: Array<{ id: number; name: string; profile_picture?: string }>;
  onParticipantsChanged?: () => void;
}

export function ManageParticipantsDialog({
  isOpen,
  onOpenChange,
  taskId,
  participants,
  taskAssignees,
  onParticipantsChanged,
}: ManageParticipantsDialogProps) {
  const [updatingIds, setUpdatingIds] = useState<number[]>([]);
  const [participantToDelete, setParticipantToDelete] =
    useState<IProjectChatDiscussionParticipants | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  const additionalParticipants = participants.filter(
  (participant) => !taskAssignees.some(
    (assignee) => assignee.id === (participant as any).user?.id
  )
);


  const handleToggleMessagePermission = async (
    participant: IProjectChatDiscussionParticipants
  ) => {
    setUpdatingIds((prev) => [...prev, participant.id]);
    try {
      const updatedParticipant =
        await PROJECT_TASK_DISCUSSION_PARTICIPANT_API.update({
          id: participant.id,
          data: {
            can_send: !participant.can_send,
          },
        });
      const newStatus = updatedParticipant.can_send ? "Participant" : "Viewer";
      toast.success(`User role updated to ${newStatus}`);

      if (onParticipantsChanged) {
        await onParticipantsChanged();
        await new Promise((resolve) => setTimeout(resolve, 300)); 
      }
    } catch (error) {
      showErrorToast({
        error,
        defaultMessage: "Failed to update participant",
      });
    } finally {
      setUpdatingIds((prev) => prev.filter((id) => id !== participant.id));
    }
  };
  const handleDeleteParticipant = async () => {
    if (!participantToDelete) return;

    setIsDeleting(true);
    try {
      await PROJECT_TASK_DISCUSSION_PARTICIPANT_API.delete({
        id: participantToDelete.id,
      });

      toast.success("Participant removed from chat");
      onParticipantsChanged?.();
      await new Promise((resolve) => setTimeout(resolve, 100));
    } catch (error) {
      showErrorToast({
        error,
        defaultMessage: "Failed to remove participant",
      });
    } finally {
      setParticipantToDelete(null);
      setIsDeleting(false);
    }
  };

  return (
    <>
      <Dialog open={isOpen} onOpenChange={onOpenChange}>
        <DialogContent className="sm:max-w-[600px] max-h-[80vh] flex flex-col p-0">
          <DialogHeader className="px-6 pt-6 pb-4 border-b">
            <DialogTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Manage Chat Participants
            </DialogTitle>
            <DialogDescription>
              View and manage who can participate in this task discussion
            </DialogDescription>
          </DialogHeader>

          <ScrollArea className="flex-1 px-6 max-h-[60vh]">
            <div className="space-y-6 py-4">
              {/* Task Assignees Section */}
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Shield className="h-4 w-4 text-primary" />
                  <h3 className="text-sm font-semibold">
                    Task Assignees ({taskAssignees.length})
                  </h3>
                </div>
                <p className="text-xs text-muted-foreground">
                  Automatically included in the chat. Cannot be removed.
                </p>
                <div className="space-y-2">
                  {taskAssignees.map((assignee) => (
                    <div
                      key={`assignee-${assignee.id}`} 
                      className="flex items-center gap-3 p-3 rounded-lg border bg-primary/5 border-primary/20"
                    >
                      <Avatar className="h-10 w-10">
                        <AvatarImage
                          src={assignee.profile_picture}
                          alt={assignee.name}
                        />
                        <AvatarFallback className="bg-primary/10 text-primary text-xs">
                          {getInitials(assignee.name)}
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">
                          {assignee.name}
                        </p>
                        <div className="flex items-center gap-1 mt-0.5">
                          <MessageSquare className="h-3 w-3 text-green-600" />
                          <span className="text-xs text-muted-foreground">
                            Can send messages
                          </span>
                        </div>
                      </div>
                      <Badge
                        variant="secondary"
                        className="bg-primary/10 text-primary border-primary/20"
                      >
                        Assignee
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>

              {/* Additional Participants Section */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Users className="h-4 w-4 text-muted-foreground" />
                    <h3 className="text-sm font-semibold">
                      Additional Participants ({participants.length})
                    </h3>
                  </div>
                </div>
                {participants.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <p className="text-sm">No additional participants</p>
                    <p className="text-xs mt-1">
                      Use the + button to add users to this chat
                    </p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {additionalParticipants.map((participant) => {
                      const isUpdating = updatingIds.includes(participant.id);
                      const userName =
                        (participant as any).user?.name || "Unknown User";
                      const userPicture = (participant as any).user
                        ?.profile_picture;

                      return (
                        <div
                          key={`participant-${participant.id}`} 
                          className="flex items-center gap-3 p-3 rounded-lg border hover:bg-muted/50 transition-colors"
                        >
                          <Avatar className="h-10 w-10">
                            <AvatarImage src={userPicture} alt={userName} />
                            <AvatarFallback className="bg-muted text-xs">
                              {getInitials(userName)}
                            </AvatarFallback>
                          </Avatar>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium truncate">
                              {userName}
                            </p>
                            <div className="flex items-center gap-1 mt-0.5">
                              {participant.can_send ? (
                                <>
                                  <MessageSquare className="h-3 w-3 text-green-600" />
                                  <span className="text-xs text-muted-foreground">
                                    Can send messages
                                  </span>
                                </>
                              ) : (
                                <>
                                  <Eye className="h-3 w-3 text-amber-600" />
                                  <span className="text-xs text-muted-foreground">
                                    Viewer only
                                  </span>
                                </>
                              )}
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <div className="flex flex-col items-center gap-1">
                              <Switch
                                checked={participant.can_send}
                                onCheckedChange={() =>
                                  handleToggleMessagePermission(participant)
                                }
                                disabled={isUpdating}
                                className="scale-75"
                              />
                              <span className="text-[10px] text-muted-foreground">
                                {participant.can_send ? "Active" : "Viewer"}
                              </span>
                            </div>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 text-destructive hover:text-destructive hover:bg-destructive/10"
                              onClick={() =>
                                setParticipantToDelete(participant)
                              }
                              disabled={isUpdating}
                            >
                              {isUpdating ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <Trash2 className="h-4 w-4" />
                              )}
                            </Button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          </ScrollArea>

          <div className="px-6 py-4 border-t bg-muted/30">
            <Button
              onClick={() => onOpenChange(false)}
              className="w-full"
              variant="outline"
            >
              Close
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      {participantToDelete && (
        <ConfirmationDialog
          isOpen={!!participantToDelete}
          title="Remove Participant"
          description={`Are you sure you want to remove this participant from the chat? They will no longer be able to view or send messages.`}
          onConfirm={handleDeleteParticipant}
          onClose={() => setParticipantToDelete(null)}
          disabled={isDeleting}
        />
      )}
    </>
  );
}
