import axios, { AxiosError } from "axios";
import type { DocumentStatus } from "@/stores/document";
import type { Session, Message, Source, Link } from "@/stores/chat";
import { ElMessage } from "element-plus";

const MAX_RETRIES = 3;
const RETRY_DELAY = 1000;

function parseUTCDate(dateStr: string | Date): Date {
  if (dateStr instanceof Date) return dateStr;
  if (dateStr.endsWith("Z")) return new Date(dateStr);
  return new Date(dateStr + "Z");
}

const api = axios.create({
  baseURL: "/api",
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// 请求拦截：自动附加 JWT token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("auth_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    // 401 跳转登录（login 接口本身除外）
    if (
      error.response?.status === 401 &&
      !error.config?.url?.includes("/auth/login")
    ) {
      localStorage.removeItem("auth_token");
      localStorage.removeItem("auth_role");
      localStorage.removeItem("auth_display_name");
      window.location.href = "/login";
      return Promise.reject(error);
    }

    const config = error.config;
    if (!config) {
      return Promise.reject(error);
    }

    const retryCount = (config as any)._retryCount || 0;

    if (retryCount < MAX_RETRIES && shouldRetry(error)) {
      (config as any)._retryCount = retryCount + 1;

      await new Promise((resolve) =>
        setTimeout(resolve, RETRY_DELAY * (retryCount + 1)),
      );

      return api(config);
    }

    const errorMessage = getErrorMessage(error);
    ElMessage.error(errorMessage);

    return Promise.reject(error);
  },
);

function shouldRetry(error: AxiosError): boolean {
  return (
    !error.response ||
    error.response.status === 503 ||
    error.response.status === 502 ||
    error.response.status === 504 ||
    error.code === "ECONNABORTED" ||
    error.code === "ERR_NETWORK"
  );
}

function getErrorMessage(error: AxiosError): string {
  if (error.code === "ECONNABORTED") {
    return "请求超时，请稍后重试";
  }
  if (error.code === "ERR_NETWORK") {
    return "网络连接失败，请检查网络";
  }
  if (error.response) {
    const status = error.response.status;
    const data = error.response.data as any;

    if (data?.detail) {
      return data.detail;
    }

    switch (status) {
      case 400:
        return "请求参数错误";
      case 401:
        return "未授权，请重新登录";
      case 403:
        return "没有权限访问";
      case 404:
        return "请求的资源不存在";
      case 500:
        return "服务器内部错误";
      case 502:
        return "网关错误";
      case 503:
        return "服务暂时不可用";
      case 504:
        return "网关超时";
      default:
        return `请求失败 (${status})`;
    }
  }
  return "未知错误";
}

export interface UploadResponse {
  id: string;
  filename: string;
  status: DocumentStatus;
  size: number;
  uploadTime: string;
}

export interface DocumentItem {
  id: string;
  filename: string;
  status: DocumentStatus;
  size: number;
  uploadTime: string;
  chunk_count?: number;
  error?: string;
}

export interface DocumentsResponse {
  documents: DocumentItem[];
  total: number;
}

export interface ChatStreamRequest {
  question: string;
  session_id: string;
}

export interface SessionCreateRequest {
  title?: string;
}

export interface SessionUpdateRequest {
  title: string;
}

export interface SessionArchiveRequest {
  is_archived: boolean;
}

export interface SessionResponse {
  _id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message?: string;
  is_archived: boolean;
}

export interface SessionStatsResponse {
  total_sessions: number;
  archived_sessions: number;
  today_sessions: number;
  week_sessions: number;
  total_messages: number;
}

export interface MessagesResponse {
  messages: Message[];
  has_more?: boolean;
  next_cursor?: string;
}

export const documentApi = {
  upload: async (
    file: File,
    onProgress?: (progress: number) => void,
  ): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append("file", file);

    const response = await api.post<UploadResponse>(
      "/documents/upload",
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (e) => {
          if (e.total && onProgress) {
            onProgress(Math.round((e.loaded * 100) / e.total));
          }
        },
      },
    );
    return response.data;
  },

  list: async (page = 1, pageSize = 10): Promise<DocumentsResponse> => {
    const response = await api.get<DocumentsResponse>("/documents", {
      params: { page, pageSize },
    });
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/documents/${id}`);
  },

  reindex: async (id: string): Promise<void> => {
    await api.post(`/documents/${id}/reindex`);
  },
};

export const chatApi = {
  // ============================================================================
  // 接口已废弃 - 2026-03-17
  // 原因：已统一使用 askStreamV2 接口，此接口不再使用
  // ============================================================================
  // askStream: async (
  //   question: string,
  //   sessionId: string,
  //   onMessage: (text: string) => void,
  //   onDone: (sources: Source[]) => void,
  //   onError: (error: Error) => void
  // ): Promise<void> => {
  //   try {
  //     const response = await fetch('/api/chat/ask/stream', {
  //       method: 'POST',
  //       headers: { 'Content-Type': 'application/json' },
  //       body: JSON.stringify({ question, session_id: sessionId })
  //     })

  //     if (!response.ok) {
  //       throw new Error(`HTTP error! status: ${response.status}`)
  //     }

  //     const reader = response.body?.getReader()
  //     const decoder = new TextDecoder()
  //     let sources: Source[] = []
  //     let buffer = ''

  //     if (!reader) {
  //       throw new Error('No reader available')
  //     }

  //     while (true) {
  //       const { done, value } = await reader.read()
  //       if (done) break

  //       buffer += decoder.decode(value, { stream: true })
  //       const lines = buffer.split('\n')
  //       buffer = lines.pop() || ''

  //       for (const line of lines) {
  //         if (line.startsWith('data: ')) {
  //           const data = line.slice(6)
  //           if (data === '[DONE]') {
  //             onDone(sources)
  //             return
  //           }
  //
  //           try {
  //             const parsed = JSON.parse(data)
  //             if (parsed.type === 'text') {
  //               onMessage(parsed.content)
  //             } else if (parsed.type === 'sources') {
  //               sources = parsed.sources
  //             } else if (parsed.type === 'done') {
  //               // V2 API 格式：sources 在 done 消息中
  //               sources = parsed.sources || []
  //             } else if (parsed.type === 'error') {
  //               throw new Error(parsed.message || '服务器错误')
  //             }
  //           } catch (e) {
  //             if (e instanceof SyntaxError) {
  //               onMessage(data)
  //             } else {
  //               throw e
  //             }
  //           }
  //         }
  //       }
  //     }

  //     if (buffer.startsWith('data: ')) {
  //       const data = buffer.slice(6)
  //       if (data !== '[DONE]') {
  //         try {
  //           const parsed = JSON.parse(data)
  //           if (parsed.type === 'sources') {
  //             sources = parsed.sources
  //           } else if (parsed.type === 'done') {
  //             // V2 API 格式：sources 在 done 消息中
  //             sources = parsed.sources || []
  //           }
  //         } catch {}
  //       }
  //     }

  //     onDone(sources)
  //   } catch (error) {
  //     onError(error as Error)
  //   }
  // },

  // V2 API - 使用新架构
  askStreamV2: async (
    question: string,
    sessionId: string,
    onMessage: (text: string) => void,
    onDone: (
      sources: Source[],
      suggestedQuestions?: string[],
      relatedLinks?: Link[],
      uiComponents?: any,
      processState?: any,
    ) => void,
    onError: (error: Error) => void,
    onWarning?: (message: string) => void,
    signal?: AbortSignal,
  ): Promise<void> => {
    try {
      // 获取 JWT token 并添加到请求头
      const token = localStorage.getItem("auth_token");
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch("/api/chat/v2/ask/stream", {
        method: "POST",
        headers,
        body: JSON.stringify({ question, session_id: sessionId }),
        signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let sources: Source[] = [];
      let suggestedQuestions: string[] = [];
      let relatedLinks: Link[] = [];
      let uiComponents: any = null;
      let processState: any = null;
      let buffer = "";

      if (!reader) {
        throw new Error("No reader available");
      }

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6);
            if (data === "[DONE]") {
              onDone(
                sources,
                suggestedQuestions,
                relatedLinks,
                uiComponents,
                processState,
              );
              return;
            }

            try {
              const parsed = JSON.parse(data);
              if (parsed.type === "text") {
                onMessage(parsed.content);
              } else if (parsed.type === "done") {
                sources = parsed.sources || [];
                suggestedQuestions = parsed.suggested_questions || [];
                relatedLinks = parsed.related_links || [];
                uiComponents = parsed.ui_components || null;
                processState = parsed.process_state || null;
              } else if (parsed.type === "sources") {
                sources = parsed.sources;
              } else if (parsed.type === "suggested_questions") {
                suggestedQuestions = parsed.questions || [];
              } else if (parsed.type === "related_links") {
                relatedLinks = parsed.links || [];
              } else if (parsed.type === "error") {
                throw new Error(
                  parsed.content || parsed.message || "服务器错误",
                );
              } else if (parsed.type === "warning") {
                if (onWarning) {
                  onWarning(parsed.message || "警告");
                }
              }
            } catch (e) {
              if (e instanceof SyntaxError) {
                onMessage(data);
              } else {
                throw e;
              }
            }
          }
        }
      }

      onDone(
        sources,
        suggestedQuestions,
        relatedLinks,
        uiComponents,
        processState,
      );
    } catch (error) {
      if ((error as Error).name === "AbortError") {
        onError(new Error("ABORTED"));
      } else {
        onError(error as Error);
      }
    }
  },

  getSessions: async (includeArchived = false): Promise<Session[]> => {
    const response = await api.get<SessionResponse[]>("/chat/sessions", {
      params: { include_archived: includeArchived },
    });
    return response.data.map((s) => ({
      id: s._id,
      title: s.title,
      createdAt: parseUTCDate(s.created_at),
      updatedAt: parseUTCDate(s.updated_at),
      messageCount: s.message_count,
      lastMessage: s.last_message,
      isArchived: s.is_archived,
    }));
  },

  searchSessions: async (
    keyword: string,
    includeArchived = false,
  ): Promise<Session[]> => {
    const response = await api.get<SessionResponse[]>("/chat/sessions/search", {
      params: { keyword, include_archived: includeArchived },
    });
    return response.data.map((s) => ({
      id: s._id,
      title: s.title,
      createdAt: parseUTCDate(s.created_at),
      updatedAt: parseUTCDate(s.updated_at),
      messageCount: s.message_count,
      lastMessage: s.last_message,
      isArchived: s.is_archived,
    }));
  },

  getSessionStats: async (): Promise<SessionStatsResponse> => {
    const response = await api.get<SessionStatsResponse>(
      "/chat/sessions/stats",
    );
    return response.data;
  },

  createSession: async (title: string = "新对话"): Promise<Session> => {
    const response = await api.post<SessionResponse>("/chat/sessions", {
      title,
    });
    const s = response.data;
    return {
      id: s._id,
      title: s.title,
      createdAt: parseUTCDate(s.created_at),
      updatedAt: parseUTCDate(s.updated_at),
      messageCount: s.message_count,
      lastMessage: s.last_message,
      isArchived: s.is_archived,
    };
  },

  updateSession: async (sessionId: string, title: string): Promise<void> => {
    await api.patch(`/chat/sessions/${sessionId}`, { title });
  },

  archiveSession: async (
    sessionId: string,
    isArchived: boolean = true,
  ): Promise<void> => {
    await api.patch(`/chat/sessions/${sessionId}/archive`, {
      is_archived: isArchived,
    });
  },

  deleteSession: async (sessionId: string): Promise<void> => {
    await api.delete(`/chat/sessions/${sessionId}`);
  },

  getMessages: async (sessionId: string): Promise<MessagesResponse> => {
    const response = await api.get<MessagesResponse>(
      `/chat/sessions/${sessionId}/messages`,
    );
    return response.data;
  },

  loadMoreMessages: async (
    sessionId: string,
    cursor?: string,
    limit: number = 20,
  ): Promise<MessagesResponse> => {
    const response = await api.get<MessagesResponse>(
      `/chat/sessions/${sessionId}/messages/load-more`,
      {
        params: { cursor, limit },
      },
    );
    return response.data;
  },

  exportPdf: async (
    messageId: string,
    sessionId: string,
    title?: string,
  ): Promise<Blob> => {
    const response = await api.post(
      "/chat/export/pdf",
      {
        message_id: messageId,
        session_id: sessionId,
        title: title || "AI问答导出",
      },
      {
        responseType: "blob",
      },
    );
    return response.data;
  },

  getMostQueriedDocuments: async (
    limit: number = 5,
  ): Promise<
    { filename: string; query_count: number; last_queried: string }[]
  > => {
    const response = await api.get<{
      documents: {
        filename: string;
        query_count: number;
        last_queried: string;
      }[];
    }>("/chat/documents/most-queried", {
      params: { limit },
    });
    return response.data.documents;
  },

  optimizeQuery: async (
    query: string,
  ): Promise<{
    original_query: string;
    optimized_query: string;
    query_type?: string;
    keywords?: string[];
    from_cache?: boolean;
    fallback?: boolean;
  }> => {
    const response = await api.post<{
      original_query: string;
      optimized_query: string;
      query_type?: string;
      keywords?: string[];
      from_cache?: boolean;
      fallback?: boolean;
    }>("/chat/optimize-query", {
      query,
    });
    return response.data;
  },
};

export interface FlowStepEntryLink {
  external_link_id?: string;
  label?: string;
  url?: string;
  open_in_new_tab: boolean;
}

export interface FlowStep {
  sequence: number;
  title: string;
  description: string;
  entry_link?: FlowStepEntryLink;
}

export interface FlowGuide {
  id: string;
  name: string;
  category: string;
  description: string;
  steps: FlowStep[];
  status: "active" | "disabled";
  triggers: string[];
  source_document_id?: string;
  source_document_name?: string;
  created_at: string;
  updated_at: string;
}

export interface FlowGuideGroup {
  category: string;
  guides: { id: string; name: string; description: string }[];
}

export interface ExternalLink {
  id: string;
  title: string;
  url: string;
  description: string;
}

export interface PendingDuplicate {
  id: string;
  document_id: string;
  document_name: string;
  existing_guide_id: string;
  existing_guide_name: string;
  new_guide_data: Partial<FlowGuide>;
  resolved: boolean;
  created_at: string;
}

export const flowGuideApi = {
  getGrouped: async (): Promise<FlowGuideGroup[]> => {
    const response = await api.get<FlowGuideGroup[]>("/flow-guides/grouped");
    return response.data;
  },
  list: async (params?: {
    status?: string;
    category?: string;
  }): Promise<FlowGuide[]> => {
    const response = await api.get<FlowGuide[]>("/flow-guides", { params });
    return response.data;
  },
  getById: async (id: string): Promise<FlowGuide> => {
    const response = await api.get<FlowGuide>(`/flow-guides/${id}`);
    return response.data;
  },
  create: async (
    data: Omit<FlowGuide, "id" | "created_at" | "updated_at">,
  ): Promise<FlowGuide> => {
    const response = await api.post<FlowGuide>("/flow-guides", data);
    return response.data;
  },
  update: async (id: string, data: Partial<FlowGuide>): Promise<FlowGuide> => {
    const response = await api.put<FlowGuide>(`/flow-guides/${id}`, data);
    return response.data;
  },
  delete: async (id: string): Promise<void> => {
    await api.delete(`/flow-guides/${id}`);
  },
  toggleStatus: async (
    id: string,
    status: "active" | "disabled",
  ): Promise<void> => {
    await api.patch(`/flow-guides/${id}/status`, { status });
  },
  getPendingDuplicates: async (): Promise<PendingDuplicate[]> => {
    const response = await api.get<PendingDuplicate[]>(
      "/flow-guides/pending-duplicates",
    );
    return response.data;
  },
  resolveDuplicate: async (
    pendingId: string,
    action: "overwrite" | "keep" | "save_as_new",
  ): Promise<void> => {
    await api.post("/flow-guides/resolve-duplicate", {
      pending_id: pendingId,
      action,
    });
  },
  getExternalLinks: async (): Promise<ExternalLink[]> => {
    const response = await api.get<ExternalLink[]>(
      "/flow-guides/external-links",
    );
    return response.data;
  },
};

export default api;
