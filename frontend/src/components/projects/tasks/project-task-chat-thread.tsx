"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useSelector } from "react-redux";
import { useInView } from "react-intersection-observer";
import { MessageSquare, Loader2, UserPlus, Users } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/platform/v1/components";
import { Badge } from "@/platform/v1/components";
import { ChatInput } from "./chat-input";
import { ChatMessageItem } from "./project-task-chat-message-item";
import { ConfirmationDialog } from "@/components/confirmation-dialog";
import { AddUsersToChatDialog } from "@/components/common/dialogs/add-users-to-chat-dialog";
import { ManageParticipantsDialog } from "@/components/common/dialogs/manage-participants-project-tasks-dialog";
import {
  IProjectTaskChatMessage,
  IProjectTaskChatMessageFormData,
  IProjectChatDiscussionParticipants,
} from "@/types/project.type";
import {
  PROJECT_TASK_CHAT_API,
  PROJECT_TASK_DISCUSSION_PARTICIPANT_API,
} from "@/lib/utils.chats";
import { showErrorToast } from "@/lib/utils";
import { selectSelectedInstitution, selectUser } from "@/store/auth/selectors-context-aware";

interface TaskChatThreadProps {
  taskId: number;
  taskAssignees: Array<{ id: number; name: string; profile_picture?: string }>;
  className?: string;
  onTaskUpdate?: () => void;
}

export function TaskChatThread({
  taskId,
  taskAssignees,
  className = "",
  onTaskUpdate,
}: TaskChatThreadProps) {
  const [messages, setMessages] = useState<IProjectTaskChatMessage[]>([]);
  const [participants, setParticipants] = useState<
    IProjectChatDiscussionParticipants[]
  >([]);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [nextUrl, setNextUrl] = useState<string | null>(null);
  const [messageToDelete, setMessageToDelete] = useState<number | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isAddUsersOpen, setIsAddUsersOpen] = useState(false);
  const [isManageParticipantsOpen, setIsManageParticipantsOpen] =
    useState(false);
  const [currentUserParticipant, setCurrentUserParticipant] =
    useState<IProjectChatDiscussionParticipants | null>(null);

  const currentInstitution = useSelector(selectSelectedInstitution);
  const currentUser = useSelector(selectUser);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const { ref: loadMoreRef, inView } = useInView({ threshold: 0 });

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  const isUserAtBottom = useCallback(() => {
    if (!messagesContainerRef.current) return true;
    const { scrollTop, scrollHeight, clientHeight } =
      messagesContainerRef.current;
    return scrollHeight - scrollTop - clientHeight < 50; 
  }, []);

  const fetchParticipants = useCallback(async () => {
    try {
      const res =
        await PROJECT_TASK_DISCUSSION_PARTICIPANT_API.getPaginatedProjectTaskDiscussionParticipants(
          {
            page: 1,
            task: taskId,
          }
        );
      const taskParticipants = res.results.filter((p) => p.task === taskId);
      setParticipants(taskParticipants);

      const userParticipant = taskParticipants.find(
        (p) => (p as any).user?.id === currentUser?.id
      );
      setCurrentUserParticipant(userParticipant || null);
    } catch (error) {
      showErrorToast({
        error,
        defaultMessage: "Failed to fetch participants",
      });
    }
  }, [taskId, currentUser?.id]);

  const fetchFirstPage = useCallback(async () => {
    if (!currentInstitution || !taskId) return;

    setLoading(true);
    try {
      const res = await PROJECT_TASK_CHAT_API.getPaginatedMessages({
        task: taskId,
        page: 1,
      });

      setMessages(res.results.reverse());
      setNextUrl(res.next);
      setHasMore(!!res.next);

      setTimeout(scrollToBottom, 100);
    } catch (error) {
      showErrorToast({ error, defaultMessage: "Failed to fetch messages" });
      setHasMore(false);
    } finally {
      setLoading(false);
    }
  }, [currentInstitution, taskId, scrollToBottom]);

  const fetchNextPage = useCallback(async () => {
    if (!nextUrl || loading) return;

    setLoading(true);
    try {
      const res = await PROJECT_TASK_CHAT_API.getMessagesFromUrl({ url: nextUrl });

      setMessages((prev) => [...res.results.reverse(), ...prev]);
      setNextUrl(res.next);
      setHasMore(!!res.next);
    } catch (error) {
      showErrorToast({ error, defaultMessage: "Failed to load more messages" });
      setHasMore(false);
    } finally {
      setLoading(false);
    }
  }, [nextUrl, loading]);

  useEffect(() => {
    fetchFirstPage();
    fetchParticipants();
  }, [fetchFirstPage, fetchParticipants]);

  useEffect(() => {
    if (inView && hasMore && !loading) {
      fetchNextPage();
    }
  }, [inView, hasMore, loading, fetchNextPage]);

  const handleSendMessage = async (content: string) => {
    if (!currentUser || !currentInstitution) return;

    const wasAtBottom = isUserAtBottom();
    setSending(true);
    try {
      const data: IProjectTaskChatMessageFormData = {
        content,
        task: taskId,
      };

      const newMessage = await PROJECT_TASK_CHAT_API.create({ data });
      setMessages((prev) => [...prev, newMessage]);

      if (wasAtBottom) {
        setTimeout(scrollToBottom, 100);
      }
    } catch (error) {
      showErrorToast({ error, defaultMessage: "Failed to send message" });
    } finally {
      setSending(false);
    }
  };

  const handleEditMessage = async (messageId: number, newContent: string) => {
    try {
      const updatedMessage = await PROJECT_TASK_CHAT_API.update({
        messageId,
        data: { content: newContent },
      });

      setMessages((prev) =>
        prev.map((msg) => (msg.id === messageId ? updatedMessage : msg))
      );
      toast.success("Message updated");
    } catch (error) {
      showErrorToast({ error, defaultMessage: "Failed to update message" });
    }
  };

  const handleDeleteMessage = async () => {
    if (!messageToDelete) return;

    setIsDeleting(true);
    try {
      await PROJECT_TASK_CHAT_API.delete({ messageId: messageToDelete });
      setMessages((prev) => prev.filter((msg) => msg.id !== messageToDelete));
      toast.success("Message deleted");
    } catch (error) {
      showErrorToast({ error, defaultMessage: "Failed to delete message" });
    } finally {
      setMessageToDelete(null);
      setIsDeleting(false);
    }
  };

  // Check if current user is a task assignee
  const isTaskAssignee = taskAssignees.some(
    (assignee) => assignee.id === currentUser?.id
  );

  // Determine if user can send messages
  const canSendMessages =
    isTaskAssignee || (currentUserParticipant?.can_send ?? false);

  // Get participant user IDs
  const participantUserIds = participants
    .map((p) => (p as any).user?.id)
    .filter(Boolean);
  const taskAssigneeIds = taskAssignees.map((a) => a.id);
  const totalParticipants = taskAssigneeIds.length + participants.length;

  return (
    <div
      className={`flex flex-col h-full bg-white rounded-xl border border-gray-200 ${className}`}
    >
      {/* Header with Participants Info */}
      <div className="flex-shrink-0 flex items-center justify-between px-4 py-3 border-b">
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsManageParticipantsOpen(true)}
            className="h-8 px-2 hover:bg-muted"
          >
            <Users className="h-4 w-4 mr-1.5" />
            <span className="text-sm font-medium">{totalParticipants}</span>
          </Button>
          <Badge variant="secondary" className="text-xs">
            {participants.filter((p) => !p.can_send).length} viewer
            {participants.filter((p) => !p.can_send).length !== 1 ? "s" : ""}
          </Badge>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsAddUsersOpen(true)}
          className="h-8 px-2 hover:bg-muted"
        >
          <UserPlus className="h-4 w-4 mr-1" />
          Add
        </Button>
      </div>

      <div
        ref={messagesContainerRef}
        className="flex-1 max-h-[calc(100vh-200px)] overflow-y-auto p-4 space-y-6"
      >
        {/* Load More Trigger */}
        {hasMore && (
          <div ref={loadMoreRef} className="flex justify-center py-3">
            {loading && (
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-900" />
            )}
          </div>
        )}

        {loading && messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900" />
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground">
            <div className="flex items-center justify-center h-16 w-16 rounded-full bg-muted mb-3">
              <MessageSquare className="h-8 w-8" />
            </div>
            <p className="text-sm font-medium">No messages yet</p>
            <p className="text-xs mt-1">
              {canSendMessages
                ? "Start the conversation!"
                : "You're viewing this chat as a viewer"}
            </p>
          </div>
        ) : (
          messages.map((message) => (
            <ChatMessageItem
              key={message.id}
              message={message}
              isCurrentUser={message.author === currentUser?.id}
              onEdit={handleEditMessage}
              onDelete={(id) => setMessageToDelete(id)}
            />
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 border-t bg-white">
        {canSendMessages ? (
          <ChatInput
            onSend={handleSendMessage}
            disabled={sending}
            placeholder="Type your message..."
          />
        ) : (
          <div className="flex items-center justify-center py-3 px-4 bg-muted/50 rounded-lg">
            <p className="text-sm text-muted-foreground">
              You're viewing this chat as a viewer and cannot send messages
            </p>
          </div>
        )}
      </div>

      {/* Delete Confirmation */}
      {messageToDelete && (
        <ConfirmationDialog
          isOpen={!!messageToDelete}
          title="Delete Message"
          description="Are you sure you want to delete this message? This action cannot be undone."
          onConfirm={handleDeleteMessage}
          onClose={() => setMessageToDelete(null)}
          disabled={isDeleting}
        />
      )}

      {/* Add Users Dialog */}
      <AddUsersToChatDialog
        isOpen={isAddUsersOpen}
        onOpenChange={setIsAddUsersOpen}
        taskId={taskId}
        taskAssigneeIds={taskAssigneeIds}
        existingParticipantIds={participantUserIds}
        onUsersAdded={async () => {
          await fetchParticipants();
          onTaskUpdate?.();
        }}
      />

      {/* Manage Participants Dialog */}
      <ManageParticipantsDialog
        isOpen={isManageParticipantsOpen}
        onOpenChange={setIsManageParticipantsOpen}
        taskId={taskId}
        participants={participants}
        taskAssignees={taskAssignees}
        onParticipantsChanged={async () => {
          await fetchParticipants();
        }}
      />
    </div>
  );
}
