import { IProjectTask } from "./types.utils";
import { IUser } from "./user.types";

export interface IProjectDashboard {
  total_projects: number;
  total_tasks: number;
  average_duration: number;
  employees_assigned: number;
  project_status_overview: ProjectStatusCount[];
  project_progress: ProjectProgress[];
  task_overview: TaskStatusCount[];
  recent_projects: RecentProject[];
}

export interface ProjectProgress {
  project: string;
  progress: number;
}

export interface RecentProject {
  name: string;
  start_date: string;
  end_date: string;
  progress: number;
  status: string;
}

export interface ProjectsAnalytics {
  total: number;
  by_status: ProjectStatusCount[];
}

export interface TasksAnalytics {
  total: number;
  by_status: TaskStatusCount[];
  by_priority: TaskPriorityCount[];
}

export interface ProjectStatusCount {
  status: string;
  count: number;
}

export interface TaskStatusCount {
  status: string;
  count: number;
}

export interface TaskPriorityCount {
  priority: string;
  count: number;
}

export interface IProjectStatus {
  id: number;
  created_at: string;
  updated_at: string;
  deleted_at: string;
  is_active: boolean;
  approval_status: string;
  status_name: string;
  description: string;
  color_code: string;
  created_by: number;
  updated_by: number;
  institution: number;
}

export interface IProjectStatusFormData {
  deleted_at: string;
  is_active: boolean;
  approval_status: string;
  status_name: string;
  description: string;
  color_code: string;
  created_by: number;
  updated_by: number;
  institution: number;
}

export interface IDefaultTaskStatusData {
  name: string;
  description: string;
  weight: number;
  color_code: string;
}

export interface ITaskStatus {
  id: number;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
  is_active: boolean;
  approval_status: string;
  name: string;
  description: string;
  weight: number;
  color_code: string;
  created_by: number;
  updated_by: number;
  institution?: number;
  task: number;
}

export interface IProjectTaskStatuses {
  id: number;
  name: string;
  description: string;
  weight: number;
  color_code: string;
  project: number;
  approvals: string;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
  is_active: string;
  created_by: number;
  updated_by: number;
  approval_status:
    | "under_creation"
    | "pending_approval"
    | "approved"
    | "rejected";
  is_current?: boolean;
  applied_project_task_status?: IProjectTaskStatuses;
}


export interface ITaskStandAloneStatuses {
  id: number;
  name: string;
  description: string;
  weight: number;
  color_code: string;
  task: number | null;
  approvals: string;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
  is_active: string;
  created_by: number;
  updated_by: number;
  approval_status:
    | "under_creation"
    | "pending_approval"
    | "approved"
    | "rejected";
  is_current?: boolean;
  institution?: number;
}

export interface ITaskStandAloneStatusesFormData {
  deleted_at: string;
  is_active: boolean;
  approval_status: string;
  name: string;
  description: string;
  weight: number;
  color_code: string;
  created_by: number;
  updated_by: number;
  institution: number;
  task: number;
}

export interface IProjectTaskStatusFormData {
  id?: number;
  name: string;
  description: string;
  weight: number;
  color_code: string;
  is_current?: boolean;
}

export interface ITaskStandAloneStatusFormData {
  id?: number;
  name: string;
  description: string;
  weight: number;
  color_code: string;
  is_current?: boolean;
}


export interface ITaskPriority {
  id: number;
  approvals: string;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
  is_active: boolean;
  approval_status: "under_creation" | string;
  name: string;
  description: string;
  weight: number;
  color_code: string;
  created_by: number;
  updated_by: number;
  institution: number;
}

export interface ITaskPriorityFormData {
  deleted_at?: string | null;
  is_active: boolean;
  approval_status: "under_creation" | string;
  name: string;
  description: string;
  weight: number;
  color_code: string;
  created_by: number;
  updated_by: number;
  institution: number;
}


export interface IProjectTaskPriority {
  id: number;
  approvals: string;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
  is_active: boolean;
  approval_status: "under_creation" | string;
  name: string;
  description: string;
  weight: number;
  color_code: string;
  created_by: number;
  updated_by: number;
  institution: number;
}

export interface IProjectTaskPriorityFormData {
  deleted_at?: string | null;
  is_active: boolean;
  approval_status: "under_creation" | string;
  name: string;
  description: string;
  weight: number;
  color_code: string;
  created_by: number;
  updated_by: number;
  institution: number;
}


export interface ITaskChatMessage {
  id: number;
  content: string;
  author: number | null;
  author_name: string;
  task: number;
  created_at: string;
  updated_at: string;
  is_edited?: boolean;
}

export interface ITaskChatMessageFormData {
  content: string;
  task: number;
}

export interface IProjectTaskChatMessage {
  id: number;
  content: string;
  author: number | null;
  author_name: string;
  task: number;
  created_at: string;
  updated_at: string;
  is_edited?: boolean;
}

export interface IProjectTaskChatMessageFormData {
  content: string;
  task: number;
}

export interface IProjectChatMessage {
  id: number;
  content: string;
  author: number | null;
  author_name: string;
  task: number;
  created_at: string;
  updated_at: string;
  is_edited?: boolean;
}

export interface IProjectChatMessageFormData {
  content: string;
  project: number;
}

export interface ICustomField {
  label: string;
  type: "text" | "number" | "bool" | "date" | "select";
  required: boolean;
  multiple: boolean;
  defaultValue: number;
  options?: number[] | string[];
}

export interface ITask {
  id: number;
  name: string;
  description?: string;
  old_start_date?: string;
  old_end_date?: string;
}

export interface ITaskTimeLine {
  id: number;
  //new_start_date: string;
  new_end_date: string | null;
  task: ITask;
  request_reason: string;
  approved: boolean;
  requested_by: { id: number; name: string } | null;
  approval_reason?: string | null;
  approved_by?: number;
  approval_date?: string;
  created_at: string;
  updated_at: string;
  accepted: boolean | null;
}

export interface ITaskTimeLineFormData {
  //new_start_date: string;
  new_end_date: string;
  task: number;
  request_reason: string;
  approval_reason?: string;
  accepted?: boolean;
}

// Define constant values
export const CONTENT_TYPES = {
  TASK: "Task",
  PROJECT: "Project",
} as const;

export type CONTENT_TYPES = (typeof CONTENT_TYPES)[keyof typeof CONTENT_TYPES];

export interface IAuditLog {
  id: number;
  institution: { id: number; name: string };
  user: { id: number; name: string };
  object_id: number;
  action: string;
  timestamp: string;
  changes: { [key: string]: { old: any; new: any } } | null;
  description: string;
  content_type: CONTENT_TYPES;
}

export interface IAuditTaskLogs extends IAuditLog {}
export interface IAuditProjectLogs extends IAuditLog {}

export interface IProjectStatusConfigurationsFormData {
  project: number;
  completed_status: number;
  failed_status: number;
}

export interface ITaskStatusConfigurationsFormData {
  task: number;
  completed_status: number;
  failed_status: number;
}


export interface IProjectEmailConfiguration {
  id: number;
  created_at: string;
  updated_at: string;
  deleted_at: string;
  is_active: boolean;
  approval_status: string;
  task_issuer: boolean;
  task_leader: boolean;
  task_assignees: boolean;
  on_failure: boolean;
  on_completion: boolean;
  created_by: number;
  updated_by: number;
  project: number;
  intent:string;
}

export interface IProjectEmailConfigurationFormData {
  id: number;
  is_active: boolean;
  approval_status: string;
  task_issuer: boolean;
  task_leader: boolean;
  task_assignees: boolean;
  on_failure: boolean;
  on_completion: boolean;
  created_by: number;
  updated_by: number;
  project: number;
  intent: string,
}


export interface ITaskEmailConfiguration {
  id: number;
  created_at: string;
  updated_at: string;
  deleted_at: string;
  is_active: boolean;
  approval_status: string;
  task_issuer: boolean;
  task_leader: boolean;
  task_assignees: boolean;
  on_failure: boolean;
  on_completion: boolean;
  created_by: number;
  updated_by: number;
  task: number;
  intent:string;
}

export interface ITaskEmailConfigurationFormData {
  id: number;
  is_active: boolean;
  approval_status: string;
  task_issuer: boolean;
  task_leader: boolean;
  task_assignees: boolean;
  on_failure: boolean;
  on_completion: boolean;
  created_by: number;
  updated_by: number;
  task: number;
  intent: string,
}


export interface IChatDiscussionParticipants {
  id: number;
  user: IUser;
  created_at: string;
  updated_at: string;
  deleted_at: string;
  is_active: true;
  approval_status: string;
  can_send: boolean;
  created_by: number;
  updated_by: number;
  task: number;
  added_by: number | null;
}

export interface IChatDiscussionParticipantsFormData {
  id: number;
  user: number;
  created_at: string;
  updated_at: string;
  deleted_at: string;
  is_active: true;
  approval_status: string;
  can_send: boolean;
  created_by: number;
  updated_by: number;
  task: number;
  added_by: number | null;
}

export interface IProjectChatDiscussionParticipants {
  id: number;
  user: IUser;
  created_at: string;
  updated_at: string;
  deleted_at: string;
  is_active: true;
  approval_status: string;
  can_send: boolean;
  created_by: number;
  updated_by: number;
  project: number;
  added_by: number | null;
}

export interface IProjectChatDiscussionParticipantsFormData {
  id: number;
  user: number;
  created_at: string;
  updated_at: string;
  deleted_at: string;
  is_active: true;
  approval_status: string;
  can_send: boolean;
  created_by: number;
  updated_by: number;
  project: number;
  added_by: number;
  task: number;
}


export interface IProjectTaskChatDiscussionParticipants {
  id: number;
  user: IUser;
  created_at: string;
  updated_at: string;
  deleted_at: string;
  is_active: true;
  approval_status: string;
  can_send: boolean;
  created_by: number;
  updated_by: number;
  project: number;
  task: number;
  added_by: number | null;
}

export interface IProjectTaskChatDiscussionParticipantsFormData {
  id: number;
  user: number;
  created_at: string;
  updated_at: string;
  deleted_at: string;
  is_active: true;
  approval_status: string;
  can_send: boolean;
  created_by: number;
  updated_by: number;
  project: number;
  added_by: number;
}



export interface IProjectTaskState {
    id: number;
    approvals: string;
    task_name: string;
    applied_project_task_status: { 
        id: number;
        color_code: string;
        weight: number;
        name: string;
    };
    project: { 
        id: number;
        project_name: string;
    };
    priority: { 
        id: number; 
        name: string; 
        color: string; 
        weight: number;
    };
    progress_status: string;
    progress_status_display: string;
    created_at: string;
    updated_at: string;
    deleted_at: string | null; 
    is_active: boolean;
    approval_status: string;
    description: string;
    start_date: string;
    end_date: string;
    completion_date: string | null; 
    freeze_assignee: boolean;
    custom_fields: Record<string, any>; 
    created_by: number; 
    updated_by: number; 
    user_manager: { id: number; name: string }; 
    user_assignees: Array<{ id: number; name: string }>; 
    staff_group_assignees: Array<{ id: number; name: string }>; 
    task_documents: any[]; 
}


export type IProjectCompletedTasks = IProjectTaskState;
export type IProjectFailedTasks = IProjectTaskState;

export interface ITaskState {
   id: number;
   approvals: string;
   task_statuses : string;
   task_name : string;
    priority: { 
        id: number; 
        name: string; 
        color: string; 
        weight: number;
    };
    progress_status: string;
    progress_status_display: string;
    created_at: string;
    updated_at: string;
    deleted_at: string;
    is_active: boolean;
    approval_status: string;
    description: string;
    start_date: string;
    end_date: string;
    completion_date: string;
    freeze_assignee: boolean;
    custom_fields: string;
    created_by: number;
    updated_by: number;
    applied_task_status: {
       id: number;
        color_code: string;
        weight: number;
        name: string;
    }
    completed_status: number;
    failed_status: number;
}

export type ICompletedTasks = ITaskState;
export type IFailedTasks = ITaskState;