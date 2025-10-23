import apiRequest from "./apiRequest";
import { forceUrlToHttps } from "./helpers";
import { IPaginatedResponse } from "@/types/types.utils";
import {
  IAuditProjectLogs,
  IAuditTaskLogs,
  IChatDiscussionParticipants,
  IChatDiscussionParticipantsFormData,
  IProjectEmailConfiguration,
  IProjectEmailConfigurationFormData,
  IProjectChatDiscussionParticipants,
  IProjectChatDiscussionParticipantsFormData,
  IProjectChatMessage,
  IProjectChatMessageFormData,
  ITaskChatMessage,
  ITaskChatMessageFormData,
  ITaskTimeLine,
  ITaskTimeLineFormData,
  ITaskEmailConfiguration,
  ITaskEmailConfigurationFormData,
  IProjectCompletedTasks,
  IProjectFailedTasks,
  ICompletedTasks,
  IFailedTasks,
  IProjectTaskChatDiscussionParticipants,
  IProjectTaskChatDiscussionParticipantsFormData,
  IProjectTaskChatMessage,
  IProjectTaskChatMessageFormData,
} from "@/types/project.type";

export const TASK_CHAT_API = {
  getPaginatedMessages: async ({
    task,
    page = 1,
    ordering = "-created_at",
  }: {
    task: number;
    page?: number;
    page_size?: number;
    ordering?: string;
  }) => {
    const params = new URLSearchParams({
      task: task.toString(),
      page: page.toString(),
    });

    if (ordering) {
      params.append("ordering", ordering);
    }

    const endpoint = `tasks/task-messages/?${params.toString()}`;
    const response = await apiRequest.get(endpoint);

    return response.data as IPaginatedResponse<ITaskChatMessage>;
  },

  getMessagesFromUrl: async ({ url }: { url: string }) => {
    const response = await apiRequest.get(forceUrlToHttps(url));
    return response.data as IPaginatedResponse<ITaskChatMessage>;
  },

  create: async ({ data }: { data: ITaskChatMessageFormData }) => {
    const response = await apiRequest.post(`/tasks/task-messages/`, data);
    return response.data as ITaskChatMessage;
  },

  update: async ({
    messageId,
    data,
  }: {
    messageId: number;
    data: Partial<ITaskChatMessageFormData>;
  }) => {
    const response = await apiRequest.patch(
      `/tasks/task-messages/${messageId}/`,
      data
    );
    return response.data as ITaskChatMessage;
  },

  delete: async ({ messageId }: { messageId: number }) => {
    await apiRequest.delete(`/tasks/task-messages/${messageId}/`);
  },

  getById: async ({ messageId }: { messageId: number }) => {
    const response = await apiRequest.get(
      `/tasks/task-messages/${messageId}/`
    );
    return response.data as ITaskChatMessage;
  },
};


export const PROJECT_TASK_CHAT_API = {
  getPaginatedMessages: async ({
    task,
    page = 1,
    ordering = "-created_at",
  }: {
    task: number;
    page?: number;
    page_size?: number;
    ordering?: string;
  }) => {
    const params = new URLSearchParams({
      task: task.toString(),
      page: page.toString(),
    });

    if (ordering) {
      params.append("ordering", ordering);
    }

    const endpoint = `projects/task-messages/?${params.toString()}`;
    const response = await apiRequest.get(endpoint);

    return response.data as IPaginatedResponse<IProjectTaskChatMessage>;
  },

  getMessagesFromUrl: async ({ url }: { url: string }) => {
    const response = await apiRequest.get(forceUrlToHttps(url));
    return response.data as IPaginatedResponse<IProjectTaskChatMessage>;
  },

  create: async ({ data }: { data: IProjectTaskChatMessageFormData }) => {
    const response = await apiRequest.post(`/projects/task-messages/`, data);
    return response.data as IProjectTaskChatMessage;
  },

  update: async ({
    messageId,
    data,
  }: {
    messageId: number;
    data: Partial<IProjectTaskChatMessageFormData>;
  }) => {
    const response = await apiRequest.patch(
      `/projects/task-messages/${messageId}/`,
      data
    );
    return response.data as IProjectTaskChatMessage;
  },

  delete: async ({ messageId }: { messageId: number }) => {
    await apiRequest.delete(`/projects/task-messages/${messageId}/`);
  },

  getById: async ({ messageId }: { messageId: number }) => {
    const response = await apiRequest.get(
      `/projects/task-messages/${messageId}/`
    );
    return response.data as IProjectTaskChatMessage;
  },
};

export const PROJECT_CHAT_API = {
  getPaginatedMessages: async ({
    project,
    page = 1,
    ordering = "-created_at",
  }: {
    project: number;
    page?: number;
    page_size?: number;
    ordering?: string;
  }) => {
    const params = new URLSearchParams({
      project: project.toString(),
      page: page.toString(),
    });

    if (ordering) {
      params.append("ordering", ordering);
    }

    const endpoint = `projects/project-messages/?${params.toString()}`;
    const response = await apiRequest.get(endpoint);

    return response.data as IPaginatedResponse<IProjectChatMessage>;
  },

  getMessagesFromUrl: async ({ url }: { url: string }) => {
    const response = await apiRequest.get(forceUrlToHttps(url));
    return response.data as IPaginatedResponse<IProjectChatMessage>;
  },

  create: async ({ data }: { data: IProjectChatMessageFormData }) => {
    const response = await apiRequest.post(`/projects/project-messages/`, data);
    return response.data as IProjectChatMessage;
  },

  update: async ({
    messageId,
    data,
  }: {
    messageId: number;
    data: Partial<IProjectChatMessageFormData>;
  }) => {
    const response = await apiRequest.patch(
      `/projects/project-messages/${messageId}/`,
      data
    );
    return response.data as IProjectChatMessage;
  },

  delete: async ({ messageId }: { messageId: number }) => {
    await apiRequest.delete(`/projects/project-messages/${messageId}/`);
  },

  getById: async ({ messageId }: { messageId: number }) => {
    const response = await apiRequest.get(
      `/projects/project-messages/${messageId}/`
    );
    return response.data as IProjectChatMessage;
  },
};

export const TASK_TIMELINE_API = {

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
    const endpoint = `tasks/task-extension/?${params.toString()}`;
    const response = await apiRequest.get(endpoint);

    return response.data as IPaginatedResponse<ITaskTimeLine>;
    },

   getAllPendingRequests: async ({
    task_id,
    page = 1,
  }: {
    task_id: number;
    page?: number;
    page_size?: number;
    ordering?: string;
  }) => {
    const params = new URLSearchParams({
      task_id: task_id.toString(),
      page: page.toString(),
    });

    const endpoint = `tasks/task-extension/?${params.toString()}`;
    const response = await apiRequest.get(endpoint);

    return response.data as IPaginatedResponse<ITaskTimeLine>;
  },

  getTaskExtensionsFromUrl: async ({ url }: { url: string }) => {
    const response = await apiRequest.get(forceUrlToHttps(url));
    return response.data as IPaginatedResponse<ITaskTimeLine>;
  },

  create: async ({ data }: { data: ITaskTimeLineFormData }) => {
    const response = await apiRequest.post(`/tasks/task-extension/`, data);
    return response.data as ITaskTimeLineFormData;
  },

  update: async ({
    taskId,
    data,
  }: {
    taskId: number;
    data: Partial<ITaskTimeLineFormData>;
  }) => {
    const response = await apiRequest.patch(
      `/tasks/task-extension/${taskId}/`,
      data
    );
    return response.data as ITaskTimeLine;
  },

  delete: async ({ tasktimelineId }: { tasktimelineId: number }) => {
    await apiRequest.delete(`/tasks/task-extension/${tasktimelineId}/`);
  },

  getById: async ({ tasktimelineId }: { tasktimelineId: number }) => {
    const response = await apiRequest.get(
      `/tasks/task-extension/${tasktimelineId}/`
    );
    return response.data as ITaskTimeLine;
  },


   approve: async ({
  task_extension_request,
  taskId,
  approval_reason,
}: {
  task_extension_request: number;
  taskId: number;
  approval_reason: string;
}) => {
 const response = await apiRequest.post(
  `/tasks/task-extension/approve/`,
  {
    task_extension_request: task_extension_request,
    task: taskId,
    approval_reason: approval_reason
  }
);
  return response.data as ITaskTimeLine;
},

reject: async ({
  task_extension_request,
  taskId,
  approval_reason,
}: {
  task_extension_request: number;
  taskId: number;
  approval_reason: string;
}) => {
  const response = await apiRequest.post(
  `/tasks/task-extension/reject/`,
  {
    task_extension_request: task_extension_request,
    task: taskId,
    approval_reason: approval_reason
  }
);
  return response.data as ITaskTimeLine;
},

};


export const PROJECT_TASK_TIMELINE_API = {

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
    const endpoint = `projects/task-extension/?${params.toString()}`;
    const response = await apiRequest.get(endpoint);

    return response.data as IPaginatedResponse<ITaskTimeLine>;
    },

   getAllPendingRequests: async ({
    task_id,
    page = 1,
  }: {
    task_id: number;
    page?: number;
    page_size?: number;
    ordering?: string;
  }) => {
    const params = new URLSearchParams({
      task_id: task_id.toString(),
      page: page.toString(),
    });

    const endpoint = `projects/task-extension/?${params.toString()}`;
    const response = await apiRequest.get(endpoint);

    return response.data as IPaginatedResponse<ITaskTimeLine>;
  },

  getTaskExtensionsFromUrl: async ({ url }: { url: string }) => {
    const response = await apiRequest.get(forceUrlToHttps(url));
    return response.data as IPaginatedResponse<ITaskTimeLine>;
  },

  create: async ({ data }: { data: ITaskTimeLineFormData }) => {
    const response = await apiRequest.post(`/projects/task-extension/`, data);
    return response.data as ITaskTimeLineFormData
  },

  update: async ({
    taskId,
    data,
  }: {
    taskId: number;
    data: Partial<ITaskTimeLineFormData>;
  }) => {
    const response = await apiRequest.patch(
      `/projects/task-extension/${taskId}/`,
      data
    );
    return response.data as ITaskTimeLine;
  },

  delete: async ({ tasktimelineId }: { tasktimelineId: number }) => {
    await apiRequest.delete(`/projects/task-extension/${tasktimelineId}/`);
  },

  getById: async ({ tasktimelineId }: { tasktimelineId: number }) => {
    const response = await apiRequest.get(
      `/projects/task-extension/${tasktimelineId}/`
    );
    return response.data as ITaskTimeLine;
  },


   approve: async ({
  task_extension_request,
  taskId,
  approval_reason,
}: {
  task_extension_request: number;
  taskId: number;
  approval_reason: string;
}) => {
 const response = await apiRequest.post(
  `/projects/task-extension/approve/`,
  {
    task_extension_request: task_extension_request,
    task: taskId,
    approval_reason: approval_reason
  }
);
  return response.data as ITaskTimeLine;
},

reject: async ({
  task_extension_request,
  taskId,
  approval_reason,
}: {
  task_extension_request: number;
  taskId: number;
  approval_reason: string;
}) => {
  const response = await apiRequest.post(
  `/projects/task-extension/reject/`,
  {
    task_extension_request: task_extension_request,
    task: taskId,
    approval_reason: approval_reason
  }
);
  return response.data as ITaskTimeLine;
},

};




export const AUDIT_LOG_API = {
   getPaginatedTaskAuditLogs: async ({
      page = 1,
      search,
      ordering,
      object_id,
      content_type,
    }: {
      task_id: number;
      page?: number;
      search?: string;
      ordering?: string;
      object_id?:number;
      content_type?: string;
    }) => {
      const params = new URLSearchParams({
        page: page.toString(),
      });

      if (search) {
        params.append("search", search);
      }
      if (object_id) {
        params.append("object_id", object_id.toString());
      }
      if (content_type) {
        params.append("content_type", content_type);
      }
      if (ordering) {
        params.append("ordering", ordering);
      }
    const endpoint = `audit/auditlogs/?${params.toString()}`;
    const response = await apiRequest.get(endpoint);

    return response.data as IPaginatedResponse<IAuditTaskLogs>;
    },

    getAuditTaskLogsFromUrl: async ({ url }: { url: string }) => {
    const response = await apiRequest.get(forceUrlToHttps(url));
    return response.data as IPaginatedResponse<IAuditTaskLogs>;
  },

  getPaginatedProjectAuditLogs: async ({
      page = 1,
      search,
      ordering,
      object_id,
      content_type,
    }: {
      project_id: number;
      page?: number;
      search?: string;
      ordering?: string;
      object_id?:number;
      content_type?: string;
    }) => {
      const params = new URLSearchParams({
        page: page.toString(),
      });

      if (search) {
        params.append("search", search);
      }

      if (object_id) {
        params.append("object_id", object_id.toString());
      }
      if (content_type) {
        params.append("content_type", content_type);
      }
      if (ordering) {
        params.append("ordering", ordering);
      }
    const endpoint = `audit/auditlogs/?${params.toString()}`;
    const response = await apiRequest.get(endpoint);

    return response.data as IPaginatedResponse<IAuditProjectLogs>;
    },

    getAuditProjectLogsFromUrl: async ({ url }: { url: string }) => {
    const response = await apiRequest.get(forceUrlToHttps(url));
    return response.data as IPaginatedResponse<IAuditProjectLogs>;
  },
};



export const PROJECT_EMAIL_CONFIGURATION_API = {
  getPaginatedProjectEmailConfiguration: async ({
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

    const endpoint = `/projects/task-config/?${params.toString()}`;
    const response = await apiRequest.get(endpoint);

    return response.data as IPaginatedResponse<IProjectEmailConfiguration>;
  },

  getPaginatedProjectEmailConfigurationFromUrl: async ({ url }: { url: string }) => {
    const response = await apiRequest.get(forceUrlToHttps(url));
    return response.data as IPaginatedResponse<IProjectEmailConfiguration>;
  },

  createBulk: async ({ data }: { data: Partial<IProjectEmailConfigurationFormData>[] }) => {
  const response = await apiRequest.post(`/projects/task-config/`, data);
  return response.data as IProjectEmailConfiguration[];
},

  update: async ({
    id,
    data,
  }: {
    id: number;
    data: Partial<IProjectEmailConfigurationFormData>;
  }) => {
    const response = await apiRequest.patch(
      `/projects/task-config/${id}/details/`,
      data
    );

    return response.data as IProjectEmailConfiguration;
  },

  delete: async ({ id }: { id: number }) => {
    await apiRequest.delete(
      `/projects/task-config/${id}/details/`
    );
  },

  getById: async ({ id }: { id: number }) => {
    const response = await apiRequest.get(
      `/projects/task-config/${id}/details/`
    );

    return response.data as IProjectEmailConfiguration;
  },
};


export const TASKSTANDALONE_EMAIL_CONFIGURATION_API = {
  getPaginatedTaskEmailConfiguration: async ({
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

    const endpoint = `/tasks/task-config/?${params.toString()}`;
    const response = await apiRequest.get(endpoint);

    return response.data as IPaginatedResponse<ITaskEmailConfiguration>;
  },

  getPaginatedProjectEmailConfigurationFromUrl: async ({ url }: { url: string }) => {
    const response = await apiRequest.get(forceUrlToHttps(url));
    return response.data as IPaginatedResponse<ITaskEmailConfiguration>;
  },

  createBulk: async ({ data }: { data: Partial<ITaskEmailConfigurationFormData>[] }) => {
  const response = await apiRequest.post(`/tasks/task-config/`, data);
  return response.data as ITaskEmailConfiguration[];
},

  update: async ({
    id,
    data,
  }: {
    id: number;
    data: Partial<ITaskEmailConfigurationFormData>;
  }) => {
    const response = await apiRequest.patch(
      `/tasks/task-config/${id}/details/`,
      data
    );

    return response.data as ITaskEmailConfiguration;
  },

  delete: async ({ id }: { id: number }) => {
    await apiRequest.delete(
      `/tasks/task-config/${id}/details/`
    );
  },

  getById: async ({ id }: { id: number }) => {
    const response = await apiRequest.get(
      `/tasks/task-config/${id}/details/`
    );

    return response.data as ITaskEmailConfiguration;
  },
};




export const TASK_CHAT_DISCUSSION_PARTICIPANT_API = {
  getPaginatedTaskDiscussionParticipants: async ({
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

    const endpoint = `/tasks/task-discussion-participant/?${params.toString()}`;
    const response = await apiRequest.get(endpoint);

    return response.data as IPaginatedResponse<IChatDiscussionParticipants>;
  },

  getPaginatedTaskDiscussionParticipantsFromUrl: async ({ url }: { url: string }) => {
    const response = await apiRequest.get(forceUrlToHttps(url));
    return response.data as IPaginatedResponse<IChatDiscussionParticipants>;
  },

  create: async ({ data }: { data: Partial<IChatDiscussionParticipantsFormData> }) => {
    const response = await apiRequest.post(`/tasks/task-discussion-participant/`, data);

    return response.data as IChatDiscussionParticipantsFormData;
  },

  update: async ({
    id,
    data,
  }: {
    id: number;
    data: Partial<IChatDiscussionParticipantsFormData>;
  }) => {
    const response = await apiRequest.patch(
      `/tasks/task-discussion-participant/${id}/details/`,
      data
    );

    return response.data as IChatDiscussionParticipantsFormData;
  },

  delete: async ({ id }: { id: number }) => {
    await apiRequest.delete(
      `/tasks/task-discussion-participant/${id}/details/`
    );
  },

  getById: async ({ id }: { id: number }) => {
    const response = await apiRequest.get(
      `/tasks/task-discussion-participant/${id}/details/`
    );

    return response.data as IChatDiscussionParticipants;
  },
};



export const TASK_PROJECT_DISCUSSION_PARTICIPANT_API = {
  getPaginatedProjectDiscussionParticipants: async ({
    project,
    page = 1,
    search,
    ordering,
  }: {
    project: number;
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

    if (project) {
        params.append("project", project.toString());
      }

    ordering && params.append("ordering", ordering);

    const endpoint = `/projects/project-discussion-participant/?${params.toString()}`;
    const response = await apiRequest.get(endpoint);

    return response.data as IPaginatedResponse<IProjectChatDiscussionParticipants>;
  },

  getPaginatedProjectDiscussionParticipantsFromUrl: async ({ url }: { url: string }) => {
    const response = await apiRequest.get(forceUrlToHttps(url));
    return response.data as IPaginatedResponse<IProjectChatDiscussionParticipants>;
  },

  create: async ({ data }: { data: Partial<IProjectChatDiscussionParticipantsFormData> }) => {
    const response = await apiRequest.post(`/projects/project-discussion-participant/`, data);

    return response.data as IProjectChatDiscussionParticipantsFormData;
  },

  update: async ({
    id,
    data,
  }: {
    id: number;
    data: Partial<IProjectChatDiscussionParticipantsFormData>;
  }) => {
    const response = await apiRequest.patch(
      `/projects/project-discussion-participant/${id}/details/`,
      data
    );

    return response.data as IProjectChatDiscussionParticipantsFormData;
  },

  delete: async ({ id }: { id: number }) => {
    await apiRequest.delete(
      `/projects/project-discussion-participant/${id}/details/`
    );
  },

  getById: async ({ id }: { id: number }) => {
    const response = await apiRequest.get(
      `/projects/project-discussion-participant/${id}/details/`
    );

    return response.data as IProjectChatDiscussionParticipants;
  },
};


export const PROJECT_TASK_DISCUSSION_PARTICIPANT_API = {
  getPaginatedProjectTaskDiscussionParticipants: async ({
    task,
    page = 1,
    search,
    ordering,
  }: {
    task: number;
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

    if (task) {
        params.append("task", task.toString());
      }

    ordering && params.append("ordering", ordering);

    const endpoint = `/projects/task-discussion-participant/?${params.toString()}`;
    const response = await apiRequest.get(endpoint);

    return response.data as IPaginatedResponse<IProjectTaskChatDiscussionParticipants>;
  },

  getPaginatedProjectTaskDiscussionParticipantsFromUrl: async ({ url }: { url: string }) => {
    const response = await apiRequest.get(forceUrlToHttps(url));
    return response.data as IPaginatedResponse<IProjectTaskChatDiscussionParticipants>;
  },

  create: async ({ data }: { data: Partial<IProjectTaskChatDiscussionParticipantsFormData> }) => {
    const response = await apiRequest.post(`/projects/task-discussion-participant/`, data);

    return response.data as IProjectTaskChatDiscussionParticipantsFormData;
  },

  update: async ({
    id,
    data,
  }: {
    id: number;
    data: Partial<IProjectTaskChatDiscussionParticipantsFormData>;
  }) => {
    const response = await apiRequest.patch(
      `/projects/task-discussion-participant/${id}/details/`,
      data
    );

    return response.data as IProjectTaskChatDiscussionParticipantsFormData;
  },

  delete: async ({ id }: { id: number }) => {
    await apiRequest.delete(
      `/projects/task-discussion-participant/${id}/details/`
    );
  },

  getById: async ({ id }: { id: number }) => {
    const response = await apiRequest.get(
      `/projects/task-discussion-participant/${id}/details/`
    );

    return response.data as IProjectTaskChatDiscussionParticipants;
  },
};




export const PROJECT_TASKS_STATUSES_API = {
  getPaginatedProjectCompletedTasks: async ({
    progress_status,
    page = 1,
    search,
    ordering,
  }: {
    progress_status?: string;
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

    if (progress_status) {
        params.append("progress_status", progress_status);
      }


    ordering && params.append("ordering", ordering);

    const endpoint = `/projects/task-state/?${params.toString()}`;
    const response = await apiRequest.get(endpoint);

    return response.data as IPaginatedResponse<IProjectCompletedTasks>;
  },

  getPaginatedProjectCompletedTasksFromUrl: async ({ url }: { url: string }) => {
    const response = await apiRequest.get(forceUrlToHttps(url));
    return response.data as IPaginatedResponse<IProjectCompletedTasks>;
  },


    getPaginatedProjectFailedTasks: async ({
    progress_status,
    page = 1,
    search,
    ordering,
  }: {
    progress_status?: string;
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

    if (progress_status) {
        params.append("progress_status", progress_status);
      }


    ordering && params.append("ordering", ordering);

    const endpoint = `/projects/task-state/?${params.toString()}`;
    const response = await apiRequest.get(endpoint);

    return response.data as IPaginatedResponse<IProjectFailedTasks>;
  },

  getPaginatedProjectFailedTasksFromUrl: async ({ url }: { url: string }) => {
    const response = await apiRequest.get(forceUrlToHttps(url));
    return response.data as IPaginatedResponse<IProjectFailedTasks>;
  },
}



export const TASKS_STATUSES_API = {
  getPaginatedCompletedTasks: async ({
    progress_status,
    page = 1,
    search,
    ordering,
  }: {
    progress_status?: string;
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

    if (progress_status) {
        params.append("progress_status", progress_status);
      }


    ordering && params.append("ordering", ordering);

    const endpoint = `/tasks/task-state/?${params.toString()}`;
    const response = await apiRequest.get(endpoint);

    return response.data as IPaginatedResponse<ICompletedTasks>;
  },

  getPaginatedCompletedTasksFromUrl: async ({ url }: { url: string }) => {
    const response = await apiRequest.get(forceUrlToHttps(url));
    return response.data as IPaginatedResponse<ICompletedTasks>;
  },


    getPaginatedFailedTasks: async ({
    progress_status,
    page = 1,
    search,
    ordering,
  }: {
    progress_status?: string;
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

    if (progress_status) {
        params.append("progress_status", progress_status);
      }


    ordering && params.append("ordering", ordering);

    const endpoint = `/tasks/task-state/?${params.toString()}`;
    const response = await apiRequest.get(endpoint);

    return response.data as IPaginatedResponse<IFailedTasks>;
  },

  getPaginatedFailedTasksFromUrl: async ({ url }: { url: string }) => {
    const response = await apiRequest.get(forceUrlToHttps(url));
    return response.data as IPaginatedResponse<IFailedTasks>;
  },
}











