"use client";

import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/platform/v1/components";
import { Button } from "@/platform/v1/components";
import { Input } from "@/platform/v1/components";
import { Label } from "@/platform/v1/components";
import { Textarea } from "@/platform/v1/components";
import { toast } from "sonner";
import { showErrorToast } from "@/lib/utils";
import { ITaskTimeLine, ITaskTimeLineFormData } from "@/types/project.type";
import { IProjectTask, IStandAloneTask } from "@/types/types.utils";
import {
  TASK_TIMELINE_API,
  PROJECT_TASK_TIMELINE_API,
} from "@/lib/utils.chats";

interface TaskTimelineDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  taskId: number;
  currentEndDate?: string;
  isCreator?: boolean;
  isLeader?: boolean;
  timelineToEdit?: ITaskTimeLine & { id: number };
  onSuccess?: () => void;
  selectedAction?: "approve" | "reject";
  selectedTimeline?: ITaskTimeLine;
  task?: IStandAloneTask | IProjectTask;
  hasExtendPermission?: boolean;
  isProjectTask?: boolean;
}

export function TaskTimelineDialog({
  isOpen,
  onOpenChange,
  taskId,
  currentEndDate,
  timelineToEdit,
  isCreator = false,
  isLeader = false,
  onSuccess,
  selectedAction,
  hasExtendPermission = false,
  selectedTimeline,
  task,
  isProjectTask = false,
}: TaskTimelineDialogProps) {
  const [loading, setLoading] = useState(false);
  const [timelineRequests, setTimelineRequests] = useState<ITaskTimeLine[]>([]);
  const [loadingRequests, setLoadingRequests] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState<
    (ITaskTimeLine & { action?: "approve" | "reject" }) | null
  >(null);
  const [isCreatingNewRequest, setIsCreatingNewRequest] = useState(false);
  const [approvalMessage, setApprovalMessage] = useState("");
  const [messageError, setMessageError] = useState<string | null>(null);
  const [formData, setFormData] = useState<ITaskTimeLineFormData>({
    new_end_date: currentEndDate || "",
    task: taskId,
    request_reason: "",
  });
  const [errors, setErrors] = useState<
    Partial<Record<keyof ITaskTimeLineFormData, string>>
  >({});
  const [isClosing, setIsClosing] = useState(false);
  const API = isProjectTask ? PROJECT_TASK_TIMELINE_API : TASK_TIMELINE_API;

  const fetchTimelineRequests = async () => {
    if (!isCreator && !hasExtendPermission) return;
    setLoadingRequests(true);
    try {
      const response = await API.getAllPendingRequests({
        task_id: taskId,
        page: 1,
      });
      setTimelineRequests(
        response.results.filter((r) => r.task?.id === taskId)
      );
    } catch (error) {
      showErrorToast({
        error,
        defaultMessage: "Failed to fetch timeline requests",
      });
    } finally {
      setLoadingRequests(false);
    }
  };

  useEffect(() => {
    if ((isCreator || hasExtendPermission) && isOpen) {
      fetchTimelineRequests();
    }
  }, [taskId, isCreator, hasExtendPermission, isOpen]);

  const handleApprove = async (
    request: ITaskTimeLine & { id: number },
    approvalMessage: string
  ) => {
    setLoading(true);
    try {
      await API.approve({
        task_extension_request: request.id,
        taskId: taskId,
        approval_reason: approvalMessage,
      });
      toast.success("Timeline extension approved!");
      if (isCreator) fetchTimelineRequests();
      onSuccess?.();
    } catch (error) {
      showErrorToast({
        error,
        defaultMessage: "Failed to approve timeline extension",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async (
    request: ITaskTimeLine & { id: number },
    rejectionMessage: string
  ) => {
    setLoading(true);
    try {
      await API.reject({
        task_extension_request: request.id,
        taskId: taskId,
        approval_reason: rejectionMessage,
      });
      toast.success("Timeline extension rejected!");
      if (isCreator) fetchTimelineRequests();
      onSuccess?.();
    } catch (error) {
      showErrorToast({
        error,
        defaultMessage: "Failed to reject timeline extension",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (
    field: keyof ITaskTimeLineFormData,
    value: string | number
  ) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));

    if (errors[field]) {
      setErrors((prev) => ({
        ...prev,
        [field]: undefined,
      }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof ITaskTimeLineFormData, string>> = {};

    if (!formData.new_end_date) {
      newErrors.new_end_date = "End date and time is required";
    }

    if (!formData.request_reason.trim()) {
      newErrors.request_reason = "Reason is required";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (selectedTimeline && selectedAction) {
      if (!approvalMessage.trim()) {
        setMessageError("Please provide a reason");
        return;
      }

      setLoading(true);
      try {
        if (selectedAction === "approve") {
          await handleApprove(
            selectedTimeline as ITaskTimeLine & { id: number },
            approvalMessage
          );
        } else {
          await handleReject(
            selectedTimeline as ITaskTimeLine & { id: number },
            approvalMessage
          );
        }
        setApprovalMessage("");
        setMessageError(null);
        onSuccess?.();
        onOpenChange(false);
      } catch (error) {
        showErrorToast({
          error,
          defaultMessage: `Failed to ${selectedAction} timeline extension`,
        });
      } finally {
        setLoading(false);
      }
      return;
    }

    if (selectedRequest) {
      const textarea = document.getElementById(
        `message-${selectedRequest.id}`
      ) as HTMLTextAreaElement;
      const message = textarea?.value.trim();
      if (!message) {
        toast.error("Please provide a message");
        return;
      }

      setLoading(true);
      try {
        if (selectedRequest.action === "approve") {
          await handleApprove(
            selectedRequest as ITaskTimeLine & { id: number },
            message
          );
        } else {
          await handleReject(
            selectedRequest as ITaskTimeLine & { id: number },
            message
          );
        }
        setSelectedRequest(null);
        onSuccess?.();
        onOpenChange(false);
      } catch (error) {
        showErrorToast({
          error,
          defaultMessage: `Failed to ${selectedRequest.action} timeline extension`,
        });
      } finally {
        setLoading(false);
      }
      return;
    }

    if (!validateForm()) return;

    setLoading(true);
    try {
      if (timelineToEdit) {
        await API.update({
          taskId: timelineToEdit.id,
          data: formData,
        });
        toast.success("Timeline updated successfully!");
      } else {
        await API.create({
          data: formData,
        });
        toast.success("Timeline created successfully!");
      }
      onSuccess?.();
      onOpenChange(false);
    } catch (error) {
      showErrorToast({
        error,
        defaultMessage: timelineToEdit
          ? "Failed to update timeline"
          : "Failed to create timeline",
      });
    } finally {
      setLoading(false);
    }
  };

const handleCancel = () => {
  setFormData({
    new_end_date: currentEndDate || "",
    task: taskId,
    request_reason: "",
  });
  setErrors({});
  setSelectedRequest(null);
  setIsCreatingNewRequest(false);
  setApprovalMessage("");
  setMessageError(null);
  onOpenChange(false); 
};

return (
  <Dialog open={isOpen} onOpenChange={onOpenChange}>
    <DialogContent className="w-full max-w-[500px] sm:max-w-[400px] md:max-w-[500px] mx-auto p-4 sm:p-6">
      {(() => {
        if (isClosing) {
          if (selectedTimeline && selectedAction) {
            return (
              <>
                <DialogHeader>
                  <DialogTitle className="text-lg sm:text-xl">
                    {selectedAction === "approve" ? "Approve" : "Reject"} Timeline Extension
                  </DialogTitle>
                  <DialogDescription className="text-sm sm:text-base">
                    Provide a reason for {selectedAction === "approve" ? "approving" : "rejecting"} the
                    timeline extension request.
                  </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="approval-message" className="text-sm sm:text-base">
                      {selectedAction === "approve" ? "Approval" : "Rejection"} Reason{" "}
                      <span className="text-red-500">*</span>
                    </Label>
                    <Textarea
                      id="approval-message"
                      placeholder={`Explain your ${selectedAction === "approve" ? "approval" : "rejection"}...`}
                      value={approvalMessage}
                      onChange={(e) => {
                        setApprovalMessage(e.target.value);
                        setMessageError(null);
                      }}
                      className={`min-h-[80px] sm:min-h-[100px] ${messageError ? "border-red-500" : ""}`}
                      maxLength={500}
                      disabled
                    />
                    {messageError && (
                      <p className="text-xs sm:text-sm text-red-500">{messageError}</p>
                    )}
                    <p className="text-xs text-gray-500">
                      {approvalMessage.length}/500 characters
                    </p>
                  </div>
                  <DialogFooter className="flex flex-col sm:flex-row gap-2 sm:gap-3">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={handleCancel}
                      disabled
                      className="w-full sm:w-auto text-sm sm:text-base py-2 rounded-full"
                    >
                      Cancel
                    </Button>
                    <Button
                      type="submit"
                      disabled
                      className="w-full sm:w-auto text-sm sm:text-base py-2 rounded-full"
                    >
                      {selectedAction === "approve" ? "Approve" : "Reject"}
                    </Button>
                  </DialogFooter>
                </form>
              </>
            );
          } else if (isLeader && !isCreator && !timelineToEdit) {
            return (
              <>
                <DialogHeader>
                  <DialogTitle className="text-lg sm:text-xl">
                    Request Task Timeline Extension
                  </DialogTitle>
                  <DialogDescription className="text-sm sm:text-base">
                    Set a new end date & time and provide a reason for the timeline change
                  </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="new_end_date" className="text-sm sm:text-base">
                      New End Date & Time <span className="text-red-500">*</span>
                    </Label>
                    <Input
                      id="new_end_date"
                      type="datetime-local"
                      value={formData.new_end_date}
                      onChange={(e) => handleInputChange("new_end_date", e.target.value)}
                      className={`text-sm sm:text-base ${errors.new_end_date ? "border-red-500" : ""}`}
                      disabled
                    />
                    {errors.new_end_date && (
                      <p className="text-xs sm:text-sm text-red-500">{errors.new_end_date}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="reason" className="text-sm sm:text-base">
                      Reason for Change <span className="text-red-500">*</span>
                    </Label>
                    <Textarea
                      id="reason"
                      placeholder="Explain why the timeline is being adjusted..."
                      value={formData.request_reason}
                      onChange={(e) => handleInputChange("request_reason", e.target.value)}
                      className={`min-h-[80px] sm:min-h-[100px] ${errors.request_reason ? "border-red-500" : ""}`}
                      maxLength={500}
                      disabled
                    />
                    {errors.request_reason && (
                      <p className="text-xs sm:text-sm text-red-500">{errors.request_reason}</p>
                    )}
                    <p className="text-xs text-gray-500">
                      {formData.request_reason.length}/500 characters
                    </p>
                  </div>
                  <DialogFooter className="flex flex-col sm:flex-row gap-2 sm:gap-3">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={handleCancel}
                      disabled
                      className="w-full sm:w-auto text-sm sm:text-base py-2"
                    >
                      Cancel
                    </Button>
                    <Button
                      type="submit"
                      disabled
                      className="w-full sm:w-auto text-sm sm:text-base py-2"
                    >
                      Submit Request
                    </Button>
                  </DialogFooter>
                </form>
              </>
            );
          } else if (isCreator || hasExtendPermission) {
            return (
              <>
                <DialogHeader>
                  <DialogTitle className="text-lg sm:text-xl">
                    Manage Timeline Extensions
                  </DialogTitle>
                  <DialogDescription className="text-sm sm:text-base">
                    Review and approve or reject timeline extension requests for task:{" "}
                    {task?.task_name || "Task"}
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  {task && (
                    <div className="rounded-lg p-3 sm:p-4 space-y-2 bg-gray-50">
                      <h3 className="text-sm font-medium">Task Details</h3>
                      <div className="space-y-1 text-sm">
                        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1">
                          <Label className="font-medium">Task Name:</Label>
                          <span>{task.task_name}</span>
                        </div>
                        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1">
                          <Label className="font-medium">Current End Date & Time </Label>
                          <span>
                            {task.end_date ? new Date(task.end_date).toLocaleString() : "N/A"}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                  <div className="space-y-4 max-h-[50vh] sm:max-h-[300px] overflow-y-auto pr-2">
                    {loadingRequests ? (
                      <p className="text-center text-sm text-gray-500">Loading requests...</p>
                    ) : timelineRequests.length === 0 ? (
                      <p className="text-center text-sm text-gray-500">No pending timeline requests</p>
                    ) : (
                      timelineRequests.map((request) => (
                        <div
                          key={request.id}
                          className="rounded-lg p-3 sm:p-4 space-y-3 bg-gray-50"
                        >
                          <div className="space-y-2 text-sm">
                            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1">
                              <Label className="font-medium">Requested By:</Label>
                              <span>{request.requested_by?.name || "Unknown"}</span>
                            </div>
                            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1">
                              <Label className="font-medium">New End Date & Time:</Label>
                              <span>
                                {request.new_end_date
                                  ? new Date(request.new_end_date).toLocaleString()
                                  : "N/A"}
                              </span>
                            </div>
                            <div className="space-y-1">
                              <Label className="font-medium">Reason:</Label>
                              <p className="text-gray-600">{request.request_reason}</p>
                            </div>
                          </div>
                          {selectedRequest?.id === request.id ? (
                            <div className="space-y-2">
                              <Label htmlFor={`message-${request.id}`} className="text-sm">
                                {selectedRequest.action === "approve" ? "Approval" : "Rejection"}{" "}
                                Message <span className="text-red-500">*</span>
                              </Label>
                              <Textarea
                                id={`message-${request.id}`}
                                placeholder={`Explain your ${selectedRequest.action === "approve" ? "approval" : "rejection"}...`}
                                className="min-h-[80px] sm:min-h-[80px] text-sm"
                                defaultValue=""
                                disabled
                              />
                              <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
                                <Button
                                  type="button"
                                  size="sm"
                                  disabled
                                  className="w-full sm:w-auto text-xs sm:text-sm py-2 rounded-full mt-2"
                                >
                                  Confirm {selectedRequest.action === "approve" ? "Approval" : "Rejection"}
                                </Button>
                                <Button
                                  type="button"
                                  variant="outline"
                                  size="sm"
                                  onClick={() => setSelectedRequest(null)}
                                  disabled
                                  className="w-full sm:w-auto text-xs sm:text-sm py-2 mt-2 rounded-full"
                                >
                                  Cancel
                                </Button>
                              </div>
                            </div>
                          ) : (
                            <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
                              <Button
                                type="button"
                                variant="destructive"
                                size="sm"
                                onClick={() => setSelectedRequest({ ...request, action: "reject" })}
                                disabled
                                className="w-full sm:w-auto text-xs sm:text-sm py-2 rounded-full flex-1"
                              >
                                Reject
                              </Button>
                              <Button
                                type="button"
                                size="sm"
                                onClick={() => setSelectedRequest({ ...request, action: "approve" })}
                                disabled
                                className="w-full sm:w-auto text-xs sm:text-sm py-2 rounded-full flex-1"
                              >
                                Approve
                              </Button>
                            </div>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </>
            );
          } else {
            return (
              <>
                <DialogHeader>
                  <DialogTitle className="text-lg sm:text-xl">
                    {timelineToEdit ? "Edit Task Timeline Extension" : "Request Task Timeline Extension"}
                  </DialogTitle>
                  <DialogDescription className="text-sm sm:text-base">
                    {timelineToEdit
                      ? "Modify the timeline end date and reason for this task"
                      : "Set a new end date & time and provide a reason for the timeline change"}
                  </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="new_end_date" className="text-sm sm:text-base">
                      New End Date & Time <span className="text-red-500">*</span>
                    </Label>
                    <Input
                      id="new_end_date"
                      type="datetime-local"
                      value={formData.new_end_date}
                      onChange={(e) => handleInputChange("new_end_date", e.target.value)}
                      className={`text-sm sm:text-base ${errors.new_end_date ? "border-red-500" : ""}`}
                      disabled
                    />
                    {errors.new_end_date && (
                      <p className="text-xs sm:text-sm text-red-500">{errors.new_end_date}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="reason" className="text-sm sm:text-base">
                      Reason for Change <span className="text-red-500">*</span>
                    </Label>
                    <Textarea
                      id="reason"
                      placeholder="Explain why the timeline is being adjusted..."
                      value={formData.request_reason}
                      onChange={(e) => handleInputChange("request_reason", e.target.value)}
                      className={`min-h-[80px] sm:min-h-[100px] ${errors.request_reason ? "border-red-500" : ""}`}
                      maxLength={500}
                      disabled
                    />
                    {errors.request_reason && (
                      <p className="text-xs sm:text-sm text-red-500">{errors.request_reason}</p>
                    )}
                    <p className="text-xs text-gray-500">
                      {formData.request_reason.length}/500 characters
                    </p>
                  </div>
                  <DialogFooter className="flex flex-col sm:flex-row gap-2 sm:gap-3">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={handleCancel}
                      disabled
                      className="w-full sm:w-auto text-sm sm:text-base py-2"
                    >
                      Cancel
                    </Button>
                    <Button
                      type="submit"
                      disabled
                      className="w-full sm:w-auto text-sm sm:text-base py-2"
                    >
                      {timelineToEdit ? "Update Timeline" : "Submit Request"}
                    </Button>
                  </DialogFooter>
                </form>
              </>
            );
          }
        } else if (selectedTimeline && selectedAction) {
          return (
            <>
              <DialogHeader>
                <DialogTitle className="text-lg sm:text-xl">
                  {selectedAction === "approve" ? "Approve" : "Reject"} Timeline Extension
                </DialogTitle>
                <DialogDescription className="text-sm sm:text-base">
                  Provide a reason for {selectedAction === "approve" ? "approving" : "rejecting"} the
                  timeline extension request.
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="approval-message" className="text-sm sm:text-base">
                    {selectedAction === "approve" ? "Approval" : "Rejection"} Reason{" "}
                    <span className="text-red-500">*</span>
                  </Label>
                  <Textarea
                    id="approval-message"
                    placeholder={`Explain your ${selectedAction === "approve" ? "approval" : "rejection"}...`}
                    value={approvalMessage}
                    onChange={(e) => {
                      setApprovalMessage(e.target.value);
                      setMessageError(null);
                    }}
                    className={`min-h-[80px] sm:min-h-[100px] ${messageError ? "border-red-500" : ""}`}
                    maxLength={500}
                  />
                  {messageError && (
                    <p className="text-xs sm:text-sm text-red-500">{messageError}</p>
                  )}
                  <p className="text-xs text-gray-500">
                    {approvalMessage.length}/500 characters
                  </p>
                </div>
                <DialogFooter className="flex flex-col sm:flex-row gap-2 sm:gap-3">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleCancel}
                    disabled={loading}
                    className="w-full sm:w-auto text-sm sm:text-base py-2 rounded-full"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    disabled={loading}
                    className="w-full sm:w-auto text-sm sm:text-base py-2 rounded-full"
                  >
                    {loading
                      ? selectedAction === "approve"
                        ? "Approving..."
                        : "Rejecting..."
                      : selectedAction === "approve"
                        ? "Approve"
                        : "Reject"}
                  </Button>
                </DialogFooter>
              </form>
            </>
          );
        } else if (isLeader && !isCreator && !timelineToEdit) {
          return (
            <>
              <DialogHeader>
                <DialogTitle className="text-lg sm:text-xl">
                  Request Task Timeline Extension
                </DialogTitle>
                <DialogDescription className="text-sm sm:text-base">
                  Set a new end date & time and provide a reason for the timeline change
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="new_end_date" className="text-sm sm:text-base">
                    New End Date & Time <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="new_end_date"
                    type="datetime-local"
                    value={formData.new_end_date}
                    onChange={(e) => handleInputChange("new_end_date", e.target.value)}
                    className={`text-sm sm:text-base ${errors.new_end_date ? "border-red-500" : ""}`}
                  />
                  {errors.new_end_date && (
                    <p className="text-xs sm:text-sm text-red-500">{errors.new_end_date}</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="reason" className="text-sm sm:text-base">
                    Reason for Change <span className="text-red-500">*</span>
                  </Label>
                  <Textarea
                    id="reason"
                    placeholder="Explain why the timeline is being adjusted..."
                    value={formData.request_reason}
                    onChange={(e) => handleInputChange("request_reason", e.target.value)}
                    className={`min-h-[80px] sm:min-h-[100px] ${errors.request_reason ? "border-red-500" : ""}`}
                    maxLength={500}
                  />
                  {errors.request_reason && (
                    <p className="text-xs sm:text-sm text-red-500">{errors.request_reason}</p>
                  )}
                  <p className="text-xs text-gray-500">
                    {formData.request_reason.length}/500 characters
                  </p>
                </div>
                <DialogFooter className="flex flex-col sm:flex-row gap-2 sm:gap-3">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleCancel}
                    disabled={loading}
                    className="w-full sm:w-auto text-sm sm:text-base py-2"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    disabled={loading}
                    className="w-full sm:w-auto text-sm sm:text-base py-2"
                  >
                    {loading ? "Submitting Request..." : "Submit Request"}
                  </Button>
                </DialogFooter>
              </form>
            </>
          );
        } else if (isCreator || hasExtendPermission) {
          return (
            <>
              <DialogHeader>
                <DialogTitle className="text-lg sm:text-xl">
                  Manage Timeline Extensions
                </DialogTitle>
                <DialogDescription className="text-sm sm:text-base">
                  Review and approve or reject timeline extension requests for task:{" "}
                  {task?.task_name || "Task"}
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                {task && (
                  <div className="rounded-lg p-3 sm:p-4 space-y-2 bg-gray-50">
                    <h3 className="text-sm font-medium">Task Details</h3>
                    <div className="space-y-1 text-sm">
                      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1">
                        <Label className="font-medium">Task Name:</Label>
                        <span>{task.task_name}</span>
                      </div>
                      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1">
                        <Label className="font-medium">Current End Date & Time </Label>
                        <span>
                          {task.end_date ? new Date(task.end_date).toLocaleString() : "N/A"}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
                <div className="space-y-4 max-h-[50vh] sm:max-h-[300px] overflow-y-auto pr-2">
                  {loadingRequests ? (
                    <p className="text-center text-sm text-gray-500">Loading requests...</p>
                  ) : timelineRequests.length === 0 ? (
                    <p className="text-center text-sm text-gray-500">No pending timeline requests</p>
                  ) : (
                    timelineRequests.map((request) => (
                      <div
                        key={request.id}
                        className="rounded-lg p-3 sm:p-4 space-y-3 bg-gray-50"
                      >
                        <div className="space-y-2 text-sm">
                          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1">
                            <Label className="font-medium">Requested By:</Label>
                            <span>{request.requested_by?.name || "Unknown"}</span>
                          </div>
                          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1">
                            <Label className="font-medium">New End Date & Time:</Label>
                            <span>
                              {request.new_end_date
                                ? new Date(request.new_end_date).toLocaleString()
                                : "N/A"}
                            </span>
                          </div>
                          <div className="space-y-1">
                            <Label className="font-medium">Reason:</Label>
                            <p className="text-gray-600">{request.request_reason}</p>
                          </div>
                        </div>
                        {selectedRequest?.id === request.id ? (
                          <div className="space-y-2">
                            <Label htmlFor={`message-${request.id}`} className="text-sm">
                              {selectedRequest.action === "approve" ? "Approval" : "Rejection"}{" "}
                              Message <span className="text-red-500">*</span>
                            </Label>
                            <Textarea
                              id={`message-${request.id}`}
                              placeholder={`Explain your ${selectedRequest.action === "approve" ? "approval" : "rejection"}...`}
                              className="min-h-[80px] sm:min-h-[80px] text-sm"
                              defaultValue=""
                            />
                            <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
                              <Button
                                type="button"
                                size="sm"
                                onClick={(e) => {
                                  const textarea = document.getElementById(
                                    `message-${request.id}`
                                  ) as HTMLTextAreaElement;
                                  const message = textarea?.value.trim();
                                  if (!message) {
                                    toast.error("Please provide a message");
                                    return;
                                  }
                                  if (selectedRequest.action === "approve") {
                                    handleApprove(
                                      request as ITaskTimeLine & { id: number },
                                      message
                                    );
                                  } else {
                                    handleReject(
                                      request as ITaskTimeLine & { id: number },
                                      message
                                    );
                                  }
                                }}
                                disabled={loading}
                                className="w-full sm:w-auto text-xs sm:text-sm py-2 rounded-full mt-2"
                              >
                                Confirm {selectedRequest.action === "approve" ? "Approval" : "Rejection"}
                              </Button>
                              <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                onClick={() => setSelectedRequest(null)}
                                disabled={loading}
                                className="w-full sm:w-auto text-xs sm:text-sm py-2 mt-2 rounded-full"
                              >
                                Cancel
                              </Button>
                            </div>
                          </div>
                        ) : (
                          <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
                            <Button
                              type="button"
                              variant="destructive"
                              size="sm"
                              onClick={() => setSelectedRequest({ ...request, action: "reject" })}
                              disabled={loading}
                              className="w-full sm:w-auto text-xs sm:text-sm py-2 rounded-full flex-1"
                            >
                              Reject
                            </Button>
                            <Button
                              type="button"
                              size="sm"
                              onClick={() => setSelectedRequest({ ...request, action: "approve" })}
                              disabled={loading}
                              className="w-full sm:w-auto text-xs sm:text-sm py-2 rounded-full flex-1"
                            >
                              Approve
                            </Button>
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>
            </>
          );
        } else {
          return (
            <>
              <DialogHeader>
                <DialogTitle className="text-lg sm:text-xl">
                  {timelineToEdit ? "Edit Task Timeline Extension" : "Request Task Timeline Extension"}
                </DialogTitle>
                <DialogDescription className="text-sm sm:text-base">
                  {timelineToEdit
                    ? "Modify the timeline end date and reason for this task"
                    : "Set a new end date & time and provide a reason for the timeline change"}
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="new_end_date" className="text-sm sm:text-base">
                    New End Date & Time <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="new_end_date"
                    type="datetime-local"
                    value={formData.new_end_date}
                    onChange={(e) => handleInputChange("new_end_date", e.target.value)}
                    className={`text-sm sm:text-base ${errors.new_end_date ? "border-red-500" : ""}`}
                  />
                  {errors.new_end_date && (
                    <p className="text-xs sm:text-sm text-red-500">{errors.new_end_date}</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="reason" className="text-sm sm:text-base">
                    Reason for Change <span className="text-red-500">*</span>
                  </Label>
                  <Textarea
                    id="reason"
                    placeholder="Explain why the timeline is being adjusted..."
                    value={formData.request_reason}
                    onChange={(e) => handleInputChange("request_reason", e.target.value)}
                    className={`min-h-[80px] sm:min-h-[100px] ${errors.request_reason ? "border-red-500" : ""}`}
                    maxLength={500}
                  />
                  {errors.request_reason && (
                    <p className="text-xs sm:text-sm text-red-500">{errors.request_reason}</p>
                  )}
                  <p className="text-xs text-gray-500">
                    {formData.request_reason.length}/500 characters
                  </p>
                </div>
                <DialogFooter className="flex flex-col sm:flex-row gap-2 sm:gap-3">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleCancel}
                    disabled={loading}
                    className="w-full sm:w-auto text-sm sm:text-base py-2"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    disabled={loading}
                    className="w-full sm:w-auto text-sm sm:text-base py-2"
                  >
                    {loading
                      ? timelineToEdit
                        ? "Updating..."
                        : "Submitting Request..."
                      : timelineToEdit
                        ? "Update Timeline"
                        : "Submit Request"}
                  </Button>
                </DialogFooter>
              </form>
            </>
          );
        }
      })()}
    </DialogContent>
  </Dialog>
);
}
