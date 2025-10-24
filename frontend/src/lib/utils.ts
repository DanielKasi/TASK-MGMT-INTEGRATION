import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { toast } from "sonner";

import apiRequest from "./apiRequest";
import { forceUrlToHttps } from "./helpers";

import {
  IPaginatedResponse,
  IInstitutionWorkingDays,
  IWorkingDaysFormData,
  ISystemWorkingDay,
  IInstitutionAnalytics,
  ICalendar,
  IEvent,
  ChangePasswordData,
  ApprovalTasksDashboardResponse,
  IProject,
  IProjectFormData,
  IProjectTaskFormData,
  IProjectTask,
  IEmailProviderConfig,
  IEmailProviderConfigFormData,
  ICompanyEmail,
  IAttendance,
  IAttendanceFormData,
  IMeetingIntegrationFormData,
  IMeetingIntegration,
  IStandAloneTask,
  IStandAloneTaskFormData,
} from "@/types/types.utils";
import { IEmployee } from "@/types/types.utils";
import {
  IKYCDocument,
  IUserInstitution,
  IUserInstitutionFormData,
} from "@/types/other";

import {
  IDefaultTaskStatusData,
  IProjectDashboard,
  IProjectStatus,
  IProjectStatusConfigurationsFormData,
  IProjectStatusFormData,
  IProjectTaskStatuses,
  ITaskPriority,
  ITaskPriorityFormData,
  ITaskStandAloneStatuses,
  ITaskStatus,
  ITaskStandAloneStatusesFormData,
  IProjectTaskStatusFormData,
  IProjectTaskPriority,
  IProjectTaskPriorityFormData,
  ITaskStatusConfigurationsFormData,
} from "@/types/project.type";

import { IUser, Role, UserProfile } from "@/types/user.types";

import { MAIN_DOMAIN_URL } from "@/constants";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function validatePasswordStrength(password: string): {
  valid: boolean;
  errors: string[];
} {
  const errors: string[] = [];

  if (password.length < 8) {
    errors.push("Password must be at least 8 characters long.");
  }

  if (!/\d/.test(password)) {
    errors.push("Password must contain at least one digit.");
  }

  if (!/[A-Z]/.test(password)) {
    errors.push("Password must contain at least one uppercase letter.");
  }

  if (!/[a-z]/.test(password)) {
    errors.push("Password must contain at least one lowercase letter.");
  }

  if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    errors.push("Password must contain at least one special character.");
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

export interface TokenVerificationResponse {
  valid: boolean;
  detail?: string;
}

export interface PasswordResetResponse {
  detail: string;
}

export interface ForgotPasswordRequest {
  email: string;
  frontend_url?: string;
}

export interface VerifyTokenRequest {
  token: string;
}

export interface ResetPasswordRequest {
  token: string;
  new_password: string;
}

export const getContrastTextColor = (hexColor: string) => {
  const r = parseInt(hexColor.slice(1, 3), 16);
  const g = parseInt(hexColor.slice(3, 5), 16);
  const b = parseInt(hexColor.slice(5, 7), 16);
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return luminance > 0.5 ? "#000" : "#fff";
};

export interface LoginResponse {
  tokens: {
    access: string;
    refresh: string;
  };
  user: {
    id: number;
    email: string;
    fullname: string;
    is_active: boolean;
    is_email_verified: boolean;
    is_password_verified: boolean;
    is_staff: boolean;
  };
  institution_attached?: any[];
}

/**
 * Request a password reset
 * @param email User's email address
 * @param frontendUrl The frontend URL for the reset link
 */
export async function forgotPassword(
  email: string,
  frontendUrl?: string
): Promise<void> {
  const payload: ForgotPasswordRequest = {
    email,
    // Only include frontend_url if provided
    ...(frontendUrl && { frontend_url: frontendUrl }),
  };

  await apiRequest.post("/user/forgot-password", payload);
}

/**
 * Verify if a reset token is valid
 * @param token Reset token
 */
export async function verifyResetToken(
  token: string
): Promise<TokenVerificationResponse> {
  const response = await apiRequest.post("/user/verify-token", { token });

  return response.data;
}

/**
 * Reset password with token
 * @param token Reset token
 * @param newPassword New password
 */

export async function resetPassword(
  token: string,
  newPassword: string
): Promise<PasswordResetResponse> {
  const response = await apiRequest.post("/user/reset-password/", {
    token,
    new_password: newPassword,
  });

  return response.data;
}

// Helper function to get roles for an institution
export const getRoles = async ({
  institutionId,
}: {
  institutionId: number;
}): Promise<Role[]> => {
  const response = await apiRequest.get(
    `user/role/?Institution_id=${institutionId}`
  );

  if (response.data && response.data.results) {
    return response.data.results || [];
  }

  return Array.isArray(response.data) ? response.data : [];
};

export const getDashboardTasksAnalytics = async () => {
  try {
    const response = await apiRequest.get("approval/tasks-analytics/");

    return response.data as ApprovalTasksDashboardResponse;
  } catch (error) {
    throw error;
  }
};

export const getProjectDashboard = async () => {
  try {
    const response = await apiRequest.get("projects/project-analytics");

    return response.data as IProjectDashboard;
  } catch (error) {
    throw error;
  }
};

export const changePassword = async (data: ChangePasswordData) => {
  try {
    const response = await apiRequest.post("users/change-password/", data);

    return response.data as { message: string };
  } catch (error) {
    // console.error("Failed to change password:", error);
    throw error;
  }
};

export const ROLES_API = {
  getPaginatedFirstPage: async ({
    institutionId,
  }: {
    institutionId: number;
  }) => {
    const response = await apiRequest.get(
      `user/role/?Institution_id=${institutionId}`
    );

    return response.data as IPaginatedResponse<Role>;
  },

  getPaginatedFromUrl: async ({
    url,
  }: {
    url: string;
  }): Promise<IPaginatedResponse<Role>> => {
    const response = await apiRequest.get(forceUrlToHttps(url));

    return response.data as IPaginatedResponse<Role>;
  },
};

export const institutionAPI = {
  getDasboardAnalytics: async ({
    institutionId,
  }: {
    institutionId: number;
  }) => {
    const response = await apiRequest.get(
      `/institution/${institutionId}/dashboard-analytics/`
    );

    return response.data as IInstitutionAnalytics;
  },

  getWorkingDays: async () => {
    try {
      const response = await apiRequest.get("/institution/working-days/");

      return response.data as IInstitutionWorkingDays[];
    } catch (error) {
      throw error;
    }
  },

  createWorkingDays: async (data: IWorkingDaysFormData) => {
    try {
      const response = await apiRequest.post(
        "/institution/working-days/",
        data
      );

      return response.data as IInstitutionWorkingDays;
    } catch (error) {
      throw error;
    }
  },

  updateWorkingDays: async ({
    workingDaysId,
    data,
  }: {
    workingDaysId: number | string;
    data: IWorkingDaysFormData;
  }) => {
    try {
      const response = await apiRequest.patch(
        `/institution/working-days/${workingDaysId}/`,
        data
      );

      return response.data as IInstitutionWorkingDays;
    } catch (error) {
      throw error;
    }
  },

  createInstitution: async ({ data }: { data: FormData }) => {
    const response = await await apiRequest.post("institution/", data);

    return response as IUserInstitution;
  },

  updateInstitution: async ({
    institutionId,
    data,
  }: {
    institutionId: number;
    data: Partial<IUserInstitutionFormData> & { institution_logo?: File };
  }) => {
    const formData = new FormData();

    // Append all data fields to FormData
    Object.entries(data).forEach(([key, value]) => {
      if (key === "institution_logo" && value instanceof File) {
        formData.append(key, value);
      } else if (value !== undefined && value !== null) {
        formData.append(key, String(value));
      }
    });
    const response = await apiRequest.patch(
      `/institution/${institutionId}/`,
      formData
    );

    return response.data as IUserInstitution;
  },

  createKYCDocuments: async (
    documents: { document_title: string; document_file: File }[]
  ) => {
    const formData = new FormData();

    documents.forEach((doc) => {
      formData.append("document_title", doc.document_title);
      formData.append("document_file", doc.document_file);
    });

    const response = await apiRequest.post("/institution/kyc_docs", formData);

    return response.data;
  },

  getKYCDocuments: async (): Promise<IPaginatedResponse<IKYCDocument>> => {
    const response = await apiRequest.get("/institution/kyc_docs");

    return response.data as IPaginatedResponse<IKYCDocument>;
  },

  getKYCDocumentsFromUrl: async ({
    url,
  }: {
    url: string;
  }): Promise<IPaginatedResponse<IKYCDocument>> => {
    const response = await apiRequest.get(forceUrlToHttps(url));

    return response.data as IPaginatedResponse<IKYCDocument>;
  },

  updateKYCDocument: async ({
    documentId,
    data,
  }: {
    documentId: number;
    data: { document_title: string; document_file?: File };
  }) => {
    const formData = new FormData();

    formData.append("document_title", data.document_title);
    if (data.document_file) {
      formData.append("document_file", data.document_file);
    }

    const response = await apiRequest.patch(
      `/institution/kyc_doc/${documentId}/`,
      formData
    );

    return response.data as IKYCDocument;
  },

  deleteKYCDocument: async ({
    documentId,
  }: {
    documentId: number;
  }): Promise<boolean> => {
    try {
      const response = await apiRequest.delete(
        `/institution/kyc_doc/${documentId}/`
      );

      return response.status === 204;
    } catch (error) {
      throw error;
    }
  },
};

export const systemAPI = {
  getWorkingDays: async () => {
    try {
      const response = await apiRequest.get("/settings/system-days/");

      return response.data as ISystemWorkingDay[];
    } catch (error) {
      throw error;
    }
  },
};

export const employeeAPI = {
  getAll: async (institutionId: number): Promise<IEmployee[]> => {
    try {
      const response = await apiRequest.get(`/${institutionId}/employee/`);

      return response.data.results || response.data;
    } catch (error) {
      console.error("Error fetching employees:", error);
      throw error;
    }
  },
  getByUserId: async ({ user_id }: { user_id: number }) => {
    const response = await apiRequest.get(`/employee/${user_id}/?by_user=true`);

    return response.data as IEmployee;
  },

  generateCompanyEmail: async ({ employee_id }: { employee_id: number }) => {
    const response = await apiRequest.post(
      `/employee/employee-company-emails/${employee_id}/`,
      {
        employee: employee_id,
      }
    );
    return response as ICompanyEmail;
  },
};

// Calendar API functions
export const calendarAPI = {
  // Get calendar data for a specific institution and year
  getInstitutionCalendar: async ({ year }: { year: number; url?: string }) => {
    const response = await apiRequest.get(
      `calendar/institutions-calendar/?year=${year}`
    );

    if (response.status === 200) {
      return response.data as ICalendar;
    } else {
      throw new Error("Failed to fetch calendar data");
    }
  },
  // Get all events for an institution
  getEvents: async () => {
    const response = await apiRequest.get(`calendar/events/`);

    if (response.status === 200) {
      return response.data as IPaginatedResponse<IEvent>;
    } else {
      throw new Error("Failed to fetch events");
    }
  },

  // Create a new event
  createEvent: async (eventData: {
    institution: number;
    title: string;
    description: string;
    date: string;
    target_audience: "all" | "department" | "individual" | "specific_employees";
    event_mode: "physical" | "online" | "hybrid";
    department?: string;
    specific_employees?: string[];
  }) => {
    const response = await apiRequest.post("calendar/events/", eventData);

    if (response.status === 201) {
      return response.data;
    } else {
      throw new Error("Failed to create event");
    }
  },

  // Update an existing event
  updateEvent: async (
    eventId: number,
    eventData: {
      title?: string;
      description?: string;
      date?: string;
      target_audience?:
        | "all"
        | "department"
        | "individual"
        | "specific_employees";
      event_mode?: "physical" | "online" | "hybrid";
      department?: string;
      specific_employees?: string[];
    }
  ) => {
    const response = await apiRequest.patch(
      `calendar/events/${eventId}/`,
      eventData
    );

    if (response.status === 200) {
      return response.data;
    } else {
      throw new Error("Failed to update event");
    }
  },

  // Delete an event
  deleteEvent: async (eventId: number) => {
    const response = await apiRequest.delete(`calendar/events/${eventId}/`);

    if (response.status === 204) {
      return true;
    } else {
      throw new Error("Failed to delete event");
    }
  },

  // Get a specific event by ID
  getEvent: async (eventId: number) => {
    const response = await apiRequest.get(`calendar/events/${eventId}/`);

    if (response.status === 200) {
      return response.data;
    } else {
      throw new Error("Failed to fetch event");
    }
  },

  // Get public holidays for an institution
  getPublicHolidays: async (institutionId: number) => {
    const response = await apiRequest.get(
      `calendar/public-holidays/?institution=${institutionId}`
    );

    if (response.status === 200) {
      return response.data;
    } else {
      throw new Error("Failed to fetch public holidays");
    }
  },

  // Create a new public holiday
  createPublicHoliday: async (holidayData: {
    institution: number;
    title: string;
    date: string;
  }) => {
    const response = await apiRequest.post(
      "calendar/public-holidays/",
      holidayData
    );

    if (response.status === 201) {
      return response.data;
    } else {
      throw new Error("Failed to create public holiday");
    }
  },

  // Update a public holiday
  updatePublicHoliday: async (
    holidayId: number,
    holidayData: {
      title?: string;
      date?: string;
    }
  ) => {
    const response = await apiRequest.patch(
      `calendar/public-holidays/${holidayId}/`,
      holidayData
    );

    if (response.status === 200) {
      return response.data;
    } else {
      throw new Error("Failed to update public holiday");
    }
  },

  // Delete a public holiday
  deletePublicHoliday: async (holidayId: number) => {
    const response = await apiRequest.delete(
      `calendar/public-holidays/${holidayId}/`,
      {
        method: "DELETE",
      }
    );

    if (response.status === 204) {
      return true;
    } else {
      throw new Error("Failed to delete public holiday");
    }
  },

  // Get calendar data for a specific month/year
  getMonthCalendar: async (
    institutionId: number,
    year: number,
    month: number
  ) => {
    const response = await apiRequest.get(
      `calendar/institutions-calendar/?institution=${institutionId}&year=${year}&month=${month}`
    );

    if (response.status === 200) {
      return response.data;
    } else {
      throw new Error("Failed to fetch month calendar");
    }
  },
};

export const showErrorToast = ({
  error,
  defaultMessage,
}: {
  error: any;
  defaultMessage?: string;
}) => {
  const errorMessage =
    typeof error?.detail === "string"
      ? error.detail
      : typeof error?.error === "string"
        ? error.error
        : typeof error?.message === "string"
          ? error.message
          : defaultMessage;

  toast.error(errorMessage);
};

export const showSuccessToast = (message: string) => {
  toast.success(message);
};

export const usersAPI = {
  getProfilesByInstitutionId: async ({
    institutionId,
  }: {
    institutionId: number;
  }) => {
    const response = await apiRequest.get(
      `/institution/profile/${institutionId}/`
    );

    return response.data as IPaginatedResponse<UserProfile>;
  },

  getPaginatedUsers: async ({
    page = 1,
    search,
    ordering,
  }: {
    page?: number;
    search?: string;
    ordering?: string;
  }) => {
    const params = new URLSearchParams({
      page: page.toString(),
    });

    if (search) {
      params.append("search", search);
    }
    ordering && params.append("ordering", ordering);
    const endpoint = `user/?${params.toString()}`;
    const response = await apiRequest.get(endpoint);

    return response.data as IPaginatedResponse<IUser>;
  },

  getPaginatedUsersFromUrl: async ({ url }: { url: string }) => {
    const response = await apiRequest.get(forceUrlToHttps(url));

    return response.data as IPaginatedResponse<IUser>;
  },

  getUserById: async ({ userId }: { userId: number }) => {
    const response = await apiRequest.get(`/user/${userId}/`);
    return response.data as IUser;
  },
  getRelatedBranchUsers: async ({ userId }: { userId: number }) => {
    const response = await apiRequest.get(
      `/user/related-branch-users/${userId}/`
    );
    return response.data as IPaginatedResponse<IUser>;
  },
};

export const PROFILES_API = {
  getPaginatedUserProfiles: async ({
    page = 1,
    search,
    ordering,
  }: {
    page?: number;
    search?: string;
    ordering?: string;
  }) => {
    const params = new URLSearchParams({
      page: page.toString(),
    });

    if (search) {
      params.append("search", search);
    }
    ordering && params.append("ordering", ordering);
    const endpoint = `institution/profile/?${params.toString()}`;
    const response = await apiRequest.get(endpoint);

    return response.data as IPaginatedResponse<UserProfile>;
  },

  getPaginatedUserProfilesFromUrl: async ({ url }: { url: string }) => {
    const response = await apiRequest.get(forceUrlToHttps(url));

    return response.data as IPaginatedResponse<UserProfile>;
  },
};

export const PROJECTS_API = {
  getPaginatedProjects: async (params: {
    institutionId?: number;
    page?: number;
    search?: string;
    ordering?: string;
    status?: string;
    user_id?: number;
  }) => {
    const urlParams = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
      if (typeof value !== "undefined" && key !== "page") {
        urlParams.append(key, value.toString());
      }
      if (!params.page) {
        urlParams.append("page", "1");
      }
    });
    const endpoint = `projects/projects/?${urlParams.toString()}`;
    const response = await apiRequest.get(endpoint);

    return response.data as IPaginatedResponse<IProject>;
  },

  getPaginatedProjectsFromUrl: async ({ url }: { url: string }) => {
    const response = await apiRequest.get(forceUrlToHttps(url));
    return response.data as IPaginatedResponse<IProject>;
  },

  create: async ({
    data,
  }: {
    institutionId: number;
    data: IProjectFormData | FormData;
  }) => {
    const response = await apiRequest.post(`/projects/projects/`, data);

    return response.data as IProject;
  },

  update: async ({
    project_id,
    data,
  }: {
    project_id: number;
    data: Partial<IProjectFormData>;
  }) => {
    const response = await apiRequest.patch(
      `/projects/projects/${project_id}/details/`,
      data
    );

    return response.data as IProject;
  },
  delete: async ({ project_id }: { project_id: number }) => {
    await apiRequest.delete(`/projects/projects/${project_id}/details/`);
  },

  getByProjectById: async ({ project_id }: { project_id: number }) => {
    const response = await apiRequest.get(
      `/projects/projects/${project_id}/details/`
    );

    return response.data as IProject;
  },

  getDefaultTaskStatuses: async () => {
    const response = await apiRequest.get(`/projects/default-status/`);
    return response.data as IDefaultTaskStatusData[];
  },

  getPaginatedProjectsTaskStatuses: async (params: {
    institutionId?: number;
    page?: number;
    search?: string;
    ordering?: string;
    project: number;
    status?: string;
    user_id?: number;
  }) => {
    const urlParams = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
      if (typeof value !== "undefined" && key !== "page") {
        urlParams.append(key, value.toString());
      }
      if (!params.page) {
        urlParams.append("page", "1");
      }
    });
    const endpoint = `projects/task-status/?${urlParams.toString()}`;
    const response = await apiRequest.get(endpoint);

    return response.data as IPaginatedResponse<IProjectTaskStatuses>;
  },

  getPaginatedProjectsTaskStausesFromUrl: async ({ url }: { url: string }) => {
    const response = await apiRequest.get(forceUrlToHttps(url));
    return response.data as IPaginatedResponse<IProjectTaskStatuses>;
  },

   updateProjectTaskStatuses: async ({
    project_id,
    data,
  }: {
    project_id: number;
    data: Partial<IProjectFormData>;
  }) => {
    const response = await apiRequest.patch(
      `projects/task-status/${project_id}/details/`,
      data
    );

    return response.data as IProject;
  },
  deleteProjectTaskStatuses: async ({ project_id }: { project_id: number }) => {
    await apiRequest.delete(`projects/task-status/${project_id}/details/`);
  },

  getProjectTaskStatusesById: async ({ project_id }: { project_id: number }) => {
    const response = await apiRequest.get(
      `projects/task-status/${project_id}/details/`
    );

    return response.data as IProject;
  },

  getPaginatedTaskStandAloneStatuses: async (params: {
    institutionId?: number;
    page?: number;
    search?: string;
    ordering?: string;
    task: number;
    status?: string;
    user_id?: number;
  }) => {
    const urlParams = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
      if (typeof value !== "undefined" && key !== "page") {
        urlParams.append(key, value.toString());
      }
      if (!params.page) {
        urlParams.append("page", "1");
      }
    });
    const endpoint = `projects/standalone-task-status/?${urlParams.toString()}`;
    const response = await apiRequest.get(endpoint);

    return response.data as IPaginatedResponse<ITaskStandAloneStatuses>;
  },

  getPaginatedTaskStausesFromUrl: async ({ url }: { url: string }) => {
    const response = await apiRequest.get(forceUrlToHttps(url));
    return response.data as IPaginatedResponse<ITaskStandAloneStatuses>;
  },

  createOrUpdateDefaultStatus: async (
    data: IProjectStatusConfigurationsFormData
  ) => {
    const response = await apiRequest.post(`/projects/default-status/`, data);
    return response.data as IProjectStatusConfigurationsFormData;
  },
};

export const PROJECTS_TASKS_API = {
  getPaginatedTasks: async (params: {
    project?: number;
    page?: number;
    search?: string;
    ordering?: string;
    status?: number;
    priority?: number;
    user?: number;
    progress_status?: string;
    unassigned?: boolean;
  }) => {
    const urlParams = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
      if (typeof value !== "undefined" && key !== "page") {
        urlParams.append(key, value.toString());
      }
      if (!params.page) {
        urlParams.append("page", "1");
      }
    });

    const endpoint = `projects/tasks/?${urlParams.toString()}`;
    const response = await apiRequest.get(endpoint);

    return response.data as IPaginatedResponse<IProjectTask>;
  },

  getPaginatedTasksFromUrl: async ({ url }: { url: string }) => {
    const response = await apiRequest.get(forceUrlToHttps(url));

    return response.data as IPaginatedResponse<IProjectTask>;
  },

  create: async ({
    data,
  }: {
    projectId: number;
    data: Partial<IProjectTaskFormData>;
  }) => {
    const response = await apiRequest.post(`projects/tasks/`, data);

    return response.data as IProjectTask;
  },

  update: async ({
    taskId,
    data,
  }: {
    taskId: number;
    data: Partial<IProjectTaskFormData>;
  }) => {
    const response = await apiRequest.patch(
      `projects/tasks/${taskId}/details/`,
      data
    );

    return response.data as IProjectTask;
  },

  delete: async ({ taskId }: { taskId: number }) => {
    await apiRequest.delete(`projects/tasks/${taskId}/details/`);
  },

  getByTaskId: async ({ taskId }: { taskId: number }) => {
    const response = await apiRequest.get(`projects/tasks/${taskId}/details/`);

    return response.data as IProjectTask;
  },
};

export const TASKS_API = {
  getPaginatedTasks: async (params: {
    task?: number;
    page?: number;
    search?: string;
    ordering?: string;
    status?: number;
    priority?: number;
    user?: number;
    progress_status?: string;
    unassigned?: boolean;
  }) => {
    const urlParams = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
      if (typeof value !== "undefined" && key !== "page") {
        urlParams.append(key, value.toString());
      }
      if (!params.page) {
        urlParams.append("page", "1");
      }
    });

    const endpoint = `tasks/tasks/?${urlParams.toString()}`;
    const response = await apiRequest.get(endpoint);

    return response.data as IPaginatedResponse<IStandAloneTask>;
  },

  getPaginatedTasksFromUrl: async ({ url }: { url: string }) => {
    const response = await apiRequest.get(forceUrlToHttps(url));

    return response.data as IPaginatedResponse<IStandAloneTask>;
  },

  create: async ({
    data,
  }: {
    projectId: number;
    data: Partial<IStandAloneTaskFormData>;
  }) => {
    const response = await apiRequest.post(`tasks/tasks/`, data);

    return response.data as IStandAloneTask;
  },

  update: async ({
    taskId,
    data,
  }: {
    taskId: number;
    data: Partial<IStandAloneTaskFormData>;
  }) => {
    const response = await apiRequest.patch(
      `tasks/tasks/${taskId}/details/`,
      data
    );

    return response.data as IStandAloneTask;
  },

  delete: async ({ taskId }: { taskId: number }) => {
    await apiRequest.delete(`tasks/tasks/${taskId}/details/`);
  },

  getByTaskId: async ({ taskId }: { taskId: number }) => {
    const response = await apiRequest.get(`tasks/tasks/${taskId}/details/`);

    return response.data as IStandAloneTask;
  },

    createOrUpdateDefaultStatus: async (
    data: ITaskStatusConfigurationsFormData
  ) => {
    const response = await apiRequest.post(`/tasks/default-task-status/`, data);
    return response.data as ITaskStatusConfigurationsFormData;
  },

};

export const PROJECT_STATUS_API = {
  getPaginatedProjectStatuses: async ({
    page = 1,
    search,
    ordering,
  }: {
    page?: number;
    search?: string;
    ordering?: string;
  }) => {
    const params = new URLSearchParams({
      page: page.toString(),
    });

    if (search) {
      params.append("search", search);
    }
    ordering && params.append("ordering", ordering);

    const endpoint = `projects/project-status/?${params.toString()}`;
    const response = await apiRequest.get(endpoint);

    return response.data as IPaginatedResponse<IProjectStatus>;
  },

  getPaginatedProjectStatusesFromUrl: async ({ url }: { url: string }) => {
    const response = await apiRequest.get(forceUrlToHttps(url));
    return response.data as IPaginatedResponse<IProjectStatus>;
  },

  create: async ({ data }: { data: Partial<IProjectStatusFormData> }) => {
    const response = await apiRequest.post(`/projects/project-status/`, data);

    return response.data as IProjectStatus;
  },

  update: async ({
    project_status_id,
    data,
  }: {
    project_status_id: number;
    data: Partial<IProjectStatusFormData>;
  }) => {
    const response = await apiRequest.patch(
      `/projects/project-status/${project_status_id}/details/`,
      data
    );

    return response.data as IProjectStatus;
  },

  delete: async ({ project_status_id }: { project_status_id: number }) => {
    await apiRequest.delete(
      `/projects/project-status/${project_status_id}/details/`
    );
  },

  getById: async ({ project_status_id }: { project_status_id: number }) => {
    const response = await apiRequest.get(
      `/projects/project-status/${project_status_id}/details/`
    );

    return response.data as IProjectStatus;
  },

  getPaginatedProjectTaskStatuses: async ({
    page = 1,
    search,
    ordering,
  }: {
    page?: number;
    search?: string;
    ordering?: string;
  }) => {
    const params = new URLSearchParams({
      page: page.toString(),
    });

    if (search) {
      params.append("search", search);
    }
    ordering && params.append("ordering", ordering);

    const endpoint = `projects/task-status/?${params.toString()}`;
    const response = await apiRequest.get(endpoint);

    return response.data as IPaginatedResponse<ITaskStatus>;
  },

  getPaginatedTaskStatusesFromUrl: async ({ url }: { url: string }) => {
    const response = await apiRequest.get(forceUrlToHttps(url));
    return response.data as IPaginatedResponse<ITaskStatus>;
  },

  createProjectTaskStatus: async ({
    data,
  }: {
    data: Partial<IProjectTaskStatusFormData>;
  }) => {
    const response = await apiRequest.post(
      `projects/task-status/`,
      data
    );
    return response.data as IProjectTaskStatuses;
  },

  updateProjectTaskStatus: async ({
    project_task_status_id,
    data,
  }: {
    project_task_status_id: number;
    data: Partial<IProjectTaskStatusFormData>;
  }) => {
    const response = await apiRequest.patch(
      `projects/task-status/${project_task_status_id}/details/`,
      data
    );
    return response.data as IProjectTaskStatuses;
  },

  deleteProjectTaskStatus: async ({
    project_task_status_id,
  }: {
    project_task_status_id: number;
  }) => {
    await apiRequest.delete(
      `projects/task-status/${project_task_status_id}/details/`
    );
  },
};


export const TASK_STATUS_API = {
  getPaginatedTaskStatuses: async ({
    page = 1,
    search,
    ordering,
  }: {
    page?: number;
    search?: string;
    ordering?: string;
    institutionId?: number;
    taskId?:number;
    
  }) => {
    const params = new URLSearchParams({
      page: page.toString(),
    });

    if (search) {
      params.append("search", search);
    }
    ordering && params.append("ordering", ordering);

    const endpoint = `tasks/task-status/?${params.toString()}`;
    const response = await apiRequest.get(endpoint);

    return response.data as IPaginatedResponse<ITaskStandAloneStatuses >;
  },

  getPaginatedTaskStatusesFromUrl: async ({ url }: { url: string }) => {
    const response = await apiRequest.get(forceUrlToHttps(url));
    return response.data as IPaginatedResponse<ITaskStandAloneStatuses >;
  },

  create: async ({ data }: { data: Partial<IStandAloneTaskFormData> }) => {
    const response = await apiRequest.post(`/tasks/task-status/`, data);

    return response.data as ITaskStatus;
  },

  update: async ({
    task_status_id,
    data,
  }: {
    task_status_id: number;
    data: Partial<IStandAloneTaskFormData>;
  }) => {
    const response = await apiRequest.patch(
      `/tasks/task-status/${task_status_id}/details/`,
      data
    );

    return response.data as ITaskStatus;
  },

  delete: async ({ task_status_id }: { task_status_id: number }) => {
    await apiRequest.delete(`/tasks/task-status/${task_status_id}/details/`);
  },

  getById: async ({ task_status_id }: { task_status_id: number }) => {
    const response = await apiRequest.get(
      `/tasks/task-status/${task_status_id}/details/`
    );

    return response.data as ITaskStatus;
  },
};

export const AttendanceAPI = {
  createAttendanceRecord: async (data: IAttendanceFormData) => {
    const response = await apiRequest.post(
      `/employee/${data.employee}/attendance/`,
      data
    );

    return response.data;
  },

  fetchAttendanceRecords: async ({
    date,
    search,
    page = 1,
    ordering,
  }: {
    date?: string;
    institutionId?: number;
    page?: number;
    search?: string;
    ordering?: string;
  }) => {
    const params = new URLSearchParams({
      page: page.toString(),
    });

    if (search) {
      params.append("search", search);
    }
    if (date) {
      params.append("date", date);
    }
    ordering && params.append("ordering", ordering);
    const response = await apiRequest.get(
      `/employee/attendance/?${params.toString()}`
    );

    return response.data as IPaginatedResponse<IAttendance>;
  },

  fetchAttendanceRecordsByEmployee: async ({
    employee_id,
    date,
    search,
    page = 1,
    ordering,
  }: {
    employee_id: number;
    date?: string;
    institutionId?: number;
    page?: number;
    search?: string;
    ordering?: string;
  }) => {
    const params = new URLSearchParams({
      page: page.toString(),
      employee_id: employee_id.toString(),
    });

    if (search) {
      params.append("search", search);
    }
    if (date) {
      params.append("date", date);
    }
    ordering && params.append("ordering", ordering);
    const response = await apiRequest.get(
      `/employee/attendance/?${params.toString()}`
    );

    return response.data as IPaginatedResponse<IAttendance>;
  },

  fetchAttendanceRecordsFromUrl: async (url: string) => {
    const response = await apiRequest.get(forceUrlToHttps(url));

    return response.data as IPaginatedResponse<IAttendance>;
  },

  // Fetch attendance records for a specific employee over a date range
  fetchEmployeeAttendanceRecords: async (
    employeeId: number | string,
    startDate?: string,
    endDate?: string
  ) => {
    let url = `/employee/${employeeId}/attendance/`;
    const params = [];

    if (startDate) params.push(`start_date=${startDate}`);
    if (endDate) params.push(`end_date=${endDate}`);
    if (params.length) url += `?${params.join("&")}`;
    const response = await apiRequest.get(forceUrlToHttps(url));

    return response.data as IPaginatedResponse<IAttendance>;
  },

  updateAttendanceRecord: async (
    id: number,
    data: Partial<IAttendanceFormData>
  ) => {
    const response = await apiRequest.patch(
      `/employee/attendance/${id}/`,
      data
    );

    return response.data;
  },

  deleteAttendanceRecord: async (id: number) => {
    const response = await apiRequest.delete(`/employee/attendance/${id}/`);

    return response.data;
  },
};

export const TASK_PRIORITY_API = {
  getPaginatedTaskPriority: async ({
    page = 1,
    search,
    ordering,
  }: {
    page?: number;
    search?: string;
    ordering?: string;
  }) => {
    const params = new URLSearchParams({
      page: page.toString(),
    });

    if (search) {
      params.append("search", search);
    }
    ordering && params.append("ordering", ordering);

    const endpoint = `tasks/task-priority/?${params.toString()}`;
    const response = await apiRequest.get(endpoint);

    return response.data as IPaginatedResponse<ITaskPriority>;
  },

  getPaginatedTaskPriorityFromUrl: async ({ url }: { url: string }) => {
    const response = await apiRequest.get(forceUrlToHttps(url));
    return response.data as IPaginatedResponse<ITaskPriority>;
  },

  create: async ({ data }: { data: Partial<ITaskPriorityFormData> }) => {
    const response = await apiRequest.post(`/tasks/task-priority/`, data);

    return response.data as ITaskPriority;
  },

  update: async ({
    task_priority_id,
    data,
  }: {
    task_priority_id: number;
    data: Partial<ITaskPriorityFormData>;
  }) => {
    const response = await apiRequest.patch(
      `/tasks/task-priority/${task_priority_id}/details/`,
      data
    );

    return response.data as ITaskPriority;
  },

  delete: async ({ task_priority_id }: { task_priority_id: number }) => {
    await apiRequest.delete(
      `/tasks/task-priority/${task_priority_id}/details/`
    );
  },

  getById: async ({ task_priority_id }: { task_priority_id: number }) => {
    const response = await apiRequest.get(
      `/tasks/task-priority/${task_priority_id}/details/`
    );

    return response.data as ITaskPriority;
  },
};



export const PROJECT_TASK_PRIORITY_API = {
  getPaginatedProjectTaskPriority: async ({
    page = 1,
    search,
    ordering,
  }: {
    page?: number;
    search?: string;
    ordering?: string;
  }) => {
    const params = new URLSearchParams({
      page: page.toString(),
    });

    if (search) {
      params.append("search", search);
    }
    ordering && params.append("ordering", ordering);

    const endpoint = `projects/task-priority/?${params.toString()}`;
    const response = await apiRequest.get(endpoint);

    return response.data as IPaginatedResponse<IProjectTaskPriority>;
  },

  getPaginatedProjectTaskPriorityFromUrl: async ({ url }: { url: string }) => {
    const response = await apiRequest.get(forceUrlToHttps(url));
    return response.data as IPaginatedResponse<IProjectTaskPriority>;
  },

  create: async ({ data }: { data: Partial<IProjectTaskPriorityFormData> }) => {
    const response = await apiRequest.post(`/projects/task-priority/`, data);

    return response.data as IProjectTaskPriority;
  },

  update: async ({
    task_priority_id,
    data,
  }: {
    task_priority_id: number;
    data: Partial<IProjectTaskPriorityFormData>;
  }) => {
    const response = await apiRequest.patch(
      `/projects/task-priority/${task_priority_id}/details/`,
      data
    );

    return response.data as IProjectTaskPriority;
  },

  delete: async ({ task_priority_id }: { task_priority_id: number }) => {
    await apiRequest.delete(
      `/projects/task-priority/${task_priority_id}/details/`
    );
  },

  getById: async ({ task_priority_id }: { task_priority_id: number }) => {
    const response = await apiRequest.get(
      `/projects/task-priority/${task_priority_id}/details/`
    );

    return response.data as IProjectTaskPriority;
  },
};


export const MEETINGS_INTEGRATION_API = {
  getPaginated: async ({
    page = 1,
    search,
    ordering,
  }: {
    page?: number;
    search?: string;
    ordering?: string;
  }) => {
    const params = new URLSearchParams({
      page: page.toString(),
    });

    if (search) {
      params.append("search", search);
    }
    if (ordering) {
      params.append("ordering", ordering);
    }
    const endpoint = `settings/meeting-integration/?${params.toString()}`;
    const response = await apiRequest.get(endpoint);

    return response.data as IPaginatedResponse<IMeetingIntegration>;
  },

  getPaginatedFromUrl: async ({ url }: { url: string }) => {
    const response = await apiRequest.get(url);

    return response.data as IPaginatedResponse<IMeetingIntegration>;
  },

  create: async ({ data }: { data: IMeetingIntegrationFormData }) => {
    const response = await apiRequest.post(
      `settings/meeting-integration/`,
      data
    );

    return response.data as IMeetingIntegration;
  },

  update: async ({
    integrationId,
    data,
  }: {
    integrationId: number;
    data: Partial<IMeetingIntegrationFormData>;
  }) => {
    const response = await apiRequest.patch(
      `settings/meeting-integration/${integrationId}/`,
      data
    );

    return response.data as IMeetingIntegration;
  },

  delete: async ({ integrationId }: { integrationId: number }) => {
    await apiRequest.delete(`settings/meeting-integration/${integrationId}/`);
  },

  getById: async ({ integrationId }: { integrationId: number }) => {
    const response = await apiRequest.get(
      `settings/meeting-integration/${integrationId}/`
    );

    return response.data as IMeetingIntegration;
  },
};

export const EMAIL_PROVIDER_CONFIG_API = {
  getPaginated: async ({
    page = 1,
    search,
    ordering,
  }: {
    page?: number;
    search?: string;
    ordering?: string;
  }) => {
    const params = new URLSearchParams({
      page: page.toString(),
    });

    if (search) {
      params.append("search", search);
    }
    if (ordering) {
      params.append("ordering", ordering);
    }
    const endpoint = `settings/email-provider-config/?${params.toString()}`;
    const response = await apiRequest.get(endpoint);

    return response.data as IPaginatedResponse<IEmailProviderConfig>;
  },

  getPaginatedFromUrl: async ({ url }: { url: string }) => {
    const response = await apiRequest.get(url);

    return response.data as IPaginatedResponse<IEmailProviderConfig>;
  },

  create: async ({ data }: { data: IEmailProviderConfigFormData }) => {
    const response = await apiRequest.post(
      `settings/email-provider-config/`,
      data
    );

    return response.data as IEmailProviderConfig;
  },

  update: async ({
    configId,
    data,
  }: {
    configId: number;
    data: Partial<IEmailProviderConfigFormData>;
  }) => {
    const response = await apiRequest.patch(
      `settings/email-provider-config/${configId}/`,
      data
    );

    return response.data as IEmailProviderConfig;
  },

  delete: async ({ configId }: { configId: number }) => {
    await apiRequest.delete(`settings/email-provider-config/${configId}/`);
  },

  getById: async ({ configId }: { configId: number }) => {
    const response = await apiRequest.get(
      `settings/email-provider-config/${configId}/`
    );

    return response.data as IEmailProviderConfig;
  },
};
