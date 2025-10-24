"use client";

import { useState, useEffect } from "react";
import { Switch } from "@/platform/v1/components";
import { Label } from "@/platform/v1/components";
import { Button } from "@/platform/v1/components";
import { AlertCircle, Pencil } from "lucide-react";
import {
  IProjectEmailConfiguration,
  IProjectEmailConfigurationFormData,
  IProjectStatusConfigurationsFormData,
} from "@/types/project.type";
import { PROJECTS_API, showErrorToast } from "@/lib/utils";
import { TaskStatusSearchableSelect } from "@/components/selects/configurations-searchable-select";
import { toast } from "sonner";
import { PROJECT_EMAIL_CONFIGURATION_API } from "@/lib/utils.chats";
import { useSelector } from "react-redux";
import { selectSelectedInstitution } from "@/store/auth/selectors-context-aware";

interface ConfigurationsProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: () => void;
  statusConfigData?: IProjectStatusConfigurationsFormData | null;
  emailConfigData?: IProjectEmailConfiguration[];
  projectId?: number;
  completedStatusName?: string;
  failedStatusName?: string;
  completedStatusColor?: string;
  failedStatusColor?: string;
}

export function ConfigurationInput({
  isOpen,
  onClose,
  onSave,
  statusConfigData,
  emailConfigData,
  projectId,
  completedStatusName,
  failedStatusName,
  completedStatusColor,
  failedStatusColor,
}: ConfigurationsProps) {
  const [completedStatus, setCompletedStatus] = useState<number | null>(null);
  const [failedStatus, setFailedStatus] = useState<number | null>(null);


  const [failureTaskIssuer, setFailureTaskIssuer] = useState(false);
  const [failureTaskLeader, setFailureTaskLeader] = useState(false);
  const [failureTaskAssignees, setFailureTaskAssignees] = useState(false);


  const [completionTaskIssuer, setCompletionTaskIssuer] = useState(false);
  const [completionTaskLeader, setCompletionTaskLeader] = useState(false);
  const [completionTaskAssignees, setCompletionTaskAssignees] = useState(false);

  const currentInstitution = useSelector(selectSelectedInstitution);
  const [savingStatus, setSavingStatus] = useState(false);
  const [savingEmail, setSavingEmail] = useState(false);
  const [isStatusViewMode, setIsStatusViewMode] = useState(false);
  const [isEmailViewMode, setIsEmailViewMode] = useState(false);
  const [statusConfigSaved, setStatusConfigSaved] = useState(false);

  useEffect(() => {
    if (isOpen) {
      if (statusConfigData) {
        setCompletedStatus(statusConfigData.completed_status || null);
        setFailedStatus(statusConfigData.failed_status || null);
        setStatusConfigSaved(true);
        setIsStatusViewMode(true);
      } else {
        setCompletedStatus(null);
        setFailedStatus(null);
        setStatusConfigSaved(false);
        setIsStatusViewMode(false);
      }

      if (emailConfigData && emailConfigData.length > 0) {
        const failureConfig = emailConfigData.find(
          (config) => config.intent === "failure"
        );
        const completionConfig = emailConfigData.find(
          (config) => config.intent === "completion"
        );

        if (failureConfig) {
          setFailureTaskIssuer(failureConfig.task_issuer || false);
          setFailureTaskLeader(failureConfig.task_leader || false);
          setFailureTaskAssignees(failureConfig.task_assignees || false);
        }

        if (completionConfig) {
          setCompletionTaskIssuer(completionConfig.task_issuer || false);
          setCompletionTaskLeader(completionConfig.task_leader || false);
          setCompletionTaskAssignees(completionConfig.task_assignees || false);
        }

        setIsEmailViewMode(true);
      }
    }
  }, [statusConfigData, emailConfigData, isOpen]);

  const resetForm = (resetAll: boolean = false) => {
    setCompletedStatus(null);
    setFailedStatus(null);
    setStatusConfigSaved(false);
    setIsStatusViewMode(false);

    if (resetAll) {
      setFailureTaskIssuer(false);
      setFailureTaskLeader(false);
      setFailureTaskAssignees(false);
      setCompletionTaskIssuer(false);
      setCompletionTaskLeader(false);
      setCompletionTaskAssignees(false);
      setIsEmailViewMode(false);
    }
  };

  const handleClose = () => {
    resetForm(true);
    onClose();
  };

  const handleSaveStatusConfig = async () => {
    if (!projectId) {
      toast.error("Missing project ID");
      return;
    }

    if (!completedStatus || !failedStatus) {
      toast.error("Please select both completion and failure status");
      return;
    }

    try {
      setSavingStatus(true);

      const statusConfig: IProjectStatusConfigurationsFormData = {
        project: projectId,
        completed_status: completedStatus,
        failed_status: failedStatus,
      };

      await PROJECTS_API.createOrUpdateDefaultStatus(statusConfig);

      toast.success("Task Status Configuration saved successfully");
      setStatusConfigSaved(true);
      setIsStatusViewMode(true);
      await onSave();
    } catch (e: any) {
      showErrorToast({
        error: e,
        defaultMessage: "Failed to save status configuration",
      });
    } finally {
      setSavingStatus(false);
    }
  };

  const handleSaveEmailConfig = async () => {
    if (!projectId) {
      toast.error("Missing project ID");
      return;
    }

    if (!currentInstitution?.id) {
      toast.error("No institution selected");
      return;
    }

    const hasFailureRecipients =
      failureTaskIssuer || failureTaskLeader || failureTaskAssignees;
    const hasCompletionRecipients =
      completionTaskIssuer || completionTaskLeader || completionTaskAssignees;

    if (!hasFailureRecipients && !hasCompletionRecipients) {
      toast.error(
        "Please enable at least one notification recipient for either failure or completion"
      );
      return;
    }

    try {
      setSavingEmail(true);

      const existingFailureConfig = emailConfigData?.find(
        (config) => config.intent === "failure"
      );
      const existingCompletionConfig = emailConfigData?.find(
        (config) => config.intent === "completion"
      );

      const isUpdating = existingFailureConfig || existingCompletionConfig;

      if (isUpdating) {
        if (hasFailureRecipients && existingFailureConfig?.id) {
          await PROJECT_EMAIL_CONFIGURATION_API.update({
            id: existingFailureConfig.id,
            data: {
              project: projectId,
              task_issuer: failureTaskIssuer,
              task_leader: failureTaskLeader,
              task_assignees: failureTaskAssignees,
              on_failure: true,
              on_completion: false,
              is_active: true,
              intent: "failure",
            },
          });
        }

        if (hasCompletionRecipients && existingCompletionConfig?.id) {
          await PROJECT_EMAIL_CONFIGURATION_API.update({
            id: existingCompletionConfig.id,
            data: {
              project: projectId,
              task_issuer: completionTaskIssuer,
              task_leader: completionTaskLeader,
              task_assignees: completionTaskAssignees,
              on_failure: false,
              on_completion: true,
              is_active: true,
              intent: "completion",
            },
          });
        }
      } else {
        const configurationsToSave: Partial<IProjectEmailConfigurationFormData>[] =
          [];

        if (hasFailureRecipients) {
          configurationsToSave.push({
            project: projectId,
            task_issuer: failureTaskIssuer,
            task_leader: failureTaskLeader,
            task_assignees: failureTaskAssignees,
            on_failure: true,
            on_completion: false,
            is_active: true,
            intent: "failure",
          });
        }

        if (hasCompletionRecipients) {
          configurationsToSave.push({
            project: projectId,
            task_issuer: completionTaskIssuer,
            task_leader: completionTaskLeader,
            task_assignees: completionTaskAssignees,
            on_failure: false,
            on_completion: true,
            is_active: true,
            intent: "completion",
          });
        }

        await PROJECT_EMAIL_CONFIGURATION_API.createBulk({
          data: configurationsToSave,
        });
      }

      toast.success("Email Configuration saved successfully");
      setIsEmailViewMode(true);
      await onSave();
    } catch (e: any) {
      showErrorToast({
        error: e,
        defaultMessage: "Failed to save email configuration",
      });
    } finally {
      setSavingEmail(false);
    }
  };

  const isEmailConfigEnabled = statusConfigSaved;

  return (
    <div className="flex flex-col h-full">
      <div
        className="flex-1 overflow-y-auto p-3 sm:p-4 space-y-3 max-w-full"
        style={{ maxHeight: "calc(100vh - 100px)" }}
      >
        {/* Task Status Configuration */}
        <div>
          <h3 className="text-base font-semibold text-gray-800 mb-3">
            Task Status Configuration
          </h3>

          {isStatusViewMode ? (
            <div className="space-y-4">
              <div className="space-y-1">
                <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Completion Status
                </label>
                <div className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{
                      backgroundColor: completedStatusColor || "#22c55e",
                    }}
                  ></div>
                  <span
                    className="text-sm font-medium"
                    style={{ color: "black" }}
                  >
                    {completedStatusName || "Not Set"}
                  </span>
                </div>
              </div>

              <div className="space-y-1 mt-3">
                <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Failure Status
                </label>
                <div className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{
                      backgroundColor: failedStatusColor || "#ef4444",
                    }}
                  ></div>
                  <span
                    className="text-sm font-medium"
                    style={{ color: "black" }}
                  >
                    {failedStatusName || "Not Set"}
                  </span>
                </div>
              </div>

              <div className="mt-3 text-sm text-gray-700 p-2 rounded-lg">
                {completedStatusName && failedStatusName ? (
                  <p>
                    Tasks will be marked as{" "}
                    <span
                      className="font-semibold"
                      style={{ color: completedStatusColor || "#22c55e" }}
                    >
                      {completedStatusName}
                    </span>{" "}
                    when completed and{" "}
                    <span
                      className="font-semibold"
                      style={{ color: failedStatusColor || "#ef4444" }}
                    >
                      {failedStatusName}
                    </span>{" "}
                    when failed.
                  </p>
                ) : (
                  <p className="text-gray-500">
                    Some statuses are not fully configured yet.
                  </p>
                )}
              </div>
              <div className="flex justify-end gap-2 mt-4">
                <button
                  onClick={() => setIsStatusViewMode(false)}
                  className="text-gray-600 hover:text-gray-800"
                  title="Edit Status Configuration"
                >
                  <Pencil className="h-5 w-5" />
                </button>
              </div>
            </div>
          ) : (
            <div>
              <div className="mb-3">
                <label className="block text-xs sm:text-sm font-medium mb-1">
                  Completion Status <span className="text-red-500">*</span>
                </label>
                <div className="w-full">
                  <TaskStatusSearchableSelect
                    value={completedStatus ? [completedStatus] : []}
                    projectId={projectId}
                    onValueChange={(values) =>
                      setCompletedStatus(Number(values[0]) || null)
                    }
                    placeholder="Select completion status..."
                    multiple={false}
                    excludedValues={failedStatus ? [failedStatus] : []}
                    className="w-full border-gray-300 rounded-md"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs sm:text-sm font-medium mb-1">
                  Failure Status <span className="text-red-500">*</span>
                </label>
                <div className="w-full">
                  <TaskStatusSearchableSelect
                    value={failedStatus ? [failedStatus] : []}
                    projectId={projectId}
                    onValueChange={(values) =>
                      setFailedStatus(Number(values[0]) || null)
                    }
                    placeholder="Select failure status..."
                    multiple={false}
                    excludedValues={completedStatus ? [completedStatus] : []}
                    className="w-full border-gray-300 rounded-md"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 mt-4">
                <Button
                  onClick={handleSaveStatusConfig}
                  disabled={savingStatus || !completedStatus || !failedStatus}
                  className="text-xs sm:text-sm rounded-full text-white"
                >
                  {savingStatus ? "Saving..." : "Save Status Configuration"}
                </Button>
              </div>
            </div>
          )}
        </div>

        <div className="border-t border-gray-200"></div>

        {/* Email Notification Configuration */}
        <div className="space-y-2">
          <h3 className="text-base font-semibold text-gray-800 mb-1">
            Email Notification Configuration
          </h3>

          {!isEmailConfigEnabled && (
            <div className="flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg mb-3">
              <AlertCircle className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
              <p className="text-xs text-amber-800">
                Please save the Task Status Configuration first before setting
                up email notifications.
              </p>
            </div>
          )}

          {isEmailViewMode ? (
            <div className="space-y-4">
              {/* On Task Completion Section */}
              <div className="p-3">
                <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-green-500"></div>
                  On Task Completion
                </h4>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Task Issuer</span>
                    <span
                      className={`text-sm font-medium ${
                        completionTaskIssuer
                          ? "text-green-600"
                          : "text-gray-400"
                      }`}
                    >
                      {completionTaskIssuer ? "Enabled" : "Disabled"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Task Leader</span>
                    <span
                      className={`text-sm font-medium ${
                        completionTaskLeader
                          ? "text-green-600"
                          : "text-gray-400"
                      }`}
                    >
                      {completionTaskLeader ? "Enabled" : "Disabled"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">
                      Task Assignees
                    </span>
                    <span
                      className={`text-sm font-medium ${
                        completionTaskAssignees
                          ? "text-green-600"
                          : "text-gray-400"
                      }`}
                    >
                      {completionTaskAssignees ? "Enabled" : "Disabled"}
                    </span>
                  </div>
                </div>
              </div>

              <div className="border-t border-gray-200"></div>

              {/* On Task Failure Section */}
              <div className="p-3">
                <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-red-500"></div>
                  On Task Failure
                </h4>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Task Issuer</span>
                    <span
                      className={`text-sm font-medium ${
                        failureTaskIssuer ? "text-green-600" : "text-gray-400"
                      }`}
                    >
                      {failureTaskIssuer ? "Enabled" : "Disabled"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Task Leader</span>
                    <span
                      className={`text-sm font-medium ${
                        failureTaskLeader ? "text-green-600" : "text-gray-400"
                      }`}
                    >
                      {failureTaskLeader ? "Enabled" : "Disabled"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">
                      Task Assignees
                    </span>
                    <span
                      className={`text-sm font-medium ${
                        failureTaskAssignees
                          ? "text-green-600"
                          : "text-gray-400"
                      }`}
                    >
                      {failureTaskAssignees ? "Enabled" : "Disabled"}
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-2 mt-4">
                <button
                  onClick={() => setIsEmailViewMode(false)}
                  className="text-gray-600 hover:text-gray-800"
                  title="Edit Email Configuration"
                >
                  <Pencil className="h-5 w-5" />
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <p className="text-xs text-gray-500 mb-3">
                Configure who receives email notifications for task failures and
                completions
              </p>

              {/* On Task Completion Configuration */}
              <div className="p-3">
                <h4 className="text-sm font-semibold text-gray-800 mb-2 flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-green-500"></div>
                  On Task Completion
                </h4>
                <p className="text-xs text-gray-600 mb-3">
                  Select recipients for completion notifications
                </p>
                <div className="space-y-2">
                  <div className="flex items-center justify-between space-x-2 p-2 rounded-lg">
                    <div className="space-y-0.5">
                      <Label
                        htmlFor="completion_task_issuer"
                        className="text-sm font-medium"
                      >
                        Task Issuer
                      </Label>
                      <p className="text-xs text-gray-500">
                        Person who created the task
                      </p>
                    </div>
                    <Switch
                      id="completion_task_issuer"
                      checked={completionTaskIssuer}
                      onCheckedChange={setCompletionTaskIssuer}
                      disabled={!isEmailConfigEnabled}
                    />
                  </div>

                  <div className="flex items-center justify-between space-x-2 p-2 rounded-lg">
                    <div className="space-y-0.5">
                      <Label
                        htmlFor="completion_task_leader"
                        className="text-sm font-medium"
                      >
                        Task Leader
                      </Label>
                      <p className="text-xs text-gray-500">
                        Task manager or leader
                      </p>
                    </div>
                    <Switch
                      id="completion_task_leader"
                      checked={completionTaskLeader}
                      onCheckedChange={setCompletionTaskLeader}
                      disabled={!isEmailConfigEnabled}
                    />
                  </div>

                  <div className="flex items-center justify-between space-x-2 p-2 rounded-lg">
                    <div className="space-y-0.5">
                      <Label
                        htmlFor="completion_task_assignees"
                        className="text-sm font-medium"
                      >
                        Task Assignees
                      </Label>
                      <p className="text-xs text-gray-500">
                        All assigned team members
                      </p>
                    </div>
                    <Switch
                      id="completion_task_assignees"
                      checked={completionTaskAssignees}
                      onCheckedChange={setCompletionTaskAssignees}
                      disabled={!isEmailConfigEnabled}
                    />
                  </div>
                </div>
              </div>

              <div className="border-t border-gray-200"></div>

              {/* On Task Failure Configuration */}
              <div className="p-3">
                <h4 className="text-sm font-semibold text-gray-800 mb-2 flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-red-500"></div>
                  On Task Failure
                </h4>
                <p className="text-xs text-gray-600 mb-3">
                  Select recipients for failure notifications
                </p>
                <div className="space-y-2">
                  <div className="flex items-center justify-between space-x-2 p-2 rounded-lg">
                    <div className="space-y-0.5">
                      <Label
                        htmlFor="failure_task_issuer"
                        className="text-sm font-medium"
                      >
                        Task Issuer
                      </Label>
                      <p className="text-xs text-gray-500">
                        Person who created the task
                      </p>
                    </div>
                    <Switch
                      id="failure_task_issuer"
                      checked={failureTaskIssuer}
                      onCheckedChange={setFailureTaskIssuer}
                      disabled={!isEmailConfigEnabled}
                    />
                  </div>

                  <div className="flex items-center justify-between space-x-2 p-2 rounded-lg">
                    <div className="space-y-0.5">
                      <Label
                        htmlFor="failure_task_leader"
                        className="text-sm font-medium"
                      >
                        Task Leader
                      </Label>
                      <p className="text-xs text-gray-500">
                        Task manager or leader
                      </p>
                    </div>
                    <Switch
                      id="failure_task_leader"
                      checked={failureTaskLeader}
                      onCheckedChange={setFailureTaskLeader}
                      disabled={!isEmailConfigEnabled}
                    />
                  </div>

                  <div className="flex items-center justify-between space-x-2 p-2 rounded-lg">
                    <div className="space-y-0.5">
                      <Label
                        htmlFor="failure_task_assignees"
                        className="text-sm font-medium"
                      >
                        Task Assignees
                      </Label>
                      <p className="text-xs text-gray-500">
                        All assigned team members
                      </p>
                    </div>
                    <Switch
                      id="failure_task_assignees"
                      checked={failureTaskAssignees}
                      onCheckedChange={setFailureTaskAssignees}
                      disabled={!isEmailConfigEnabled}
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-2 mt-4">
                <Button
                  variant="outline"
                  onClick={handleClose}
                  disabled={savingEmail}
                  className="text-xs sm:text-sm rounded-full"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleSaveEmailConfig}
                  disabled={savingEmail || !isEmailConfigEnabled}
                  className="text-xs sm:text-sm rounded-full text-white"
                >
                  {savingEmail ? "Saving..." : "Save Email Configuration"}
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
