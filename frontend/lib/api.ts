import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
});

// Attach JWT token to all requests
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("mentor_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Handle 401 responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("mentor_token");
      window.location.href = "/";
    }
    return Promise.reject(error);
  }
);

// ── Auth ──────────────────────────────────────────────────────
export const authApi = {
  getMe: () => api.get("/api/auth/me").then((r) => r.data),
};

// ── Repositories ──────────────────────────────────────────────
export const repoApi = {
  analyze: (url: string) =>
    api.post("/api/repos/analyze", { url }).then((r) => r.data),

  get: (owner: string, name: string) =>
    api.get(`/api/repos/${owner}/${name}`).then((r) => r.data),

  getProgress: (owner: string, name: string) =>
    api.get(`/api/repos/${owner}/${name}/progress`).then((r) => r.data),

  getArchitecture: (owner: string, name: string) =>
    api.get(`/api/repos/${owner}/${name}/architecture`).then((r) => r.data),

  explainFile: (owner: string, name: string, path: string) =>
    api.get(`/api/repos/${owner}/${name}/file-explain`, { params: { path } }).then((r) => r.data),

  generateLearningPath: (owner: string, name: string) =>
    api.post(`/api/repos/${owner}/${name}/learning-path`).then((r) => r.data),
};

// ── Mentor Chat ───────────────────────────────────────────────
export const mentorApi = {
  createConversation: (repo_full_name?: string) =>
    api.post("/api/mentor/conversation", { repo_full_name }).then((r) => r.data),

  listConversations: () =>
    api.get("/api/mentor/conversations").then((r) => r.data),

  // Returns EventSource URL for streaming
  getChatStreamUrl: () => `${API_URL}/api/mentor/chat`,
};

// ── Issues ────────────────────────────────────────────────────
export const issuesApi = {
  getRecommended: (owner: string, name: string, limit?: number) =>
    api.get(`/api/issues/${owner}/${name}/recommended`, { params: { limit } }).then((r) => r.data),

  getTutor: (owner: string, name: string, issueNumber: number) =>
    api.get(`/api/issues/${owner}/${name}/${issueNumber}/tutor`).then((r) => r.data),
};

// ── PR Review ─────────────────────────────────────────────────
export const prApi = {
  review: (repo_full_name: string, pr_number: number) =>
    api.post("/api/pr/review", { repo_full_name, pr_number }).then((r) => r.data),

  getHistory: () =>
    api.get("/api/pr/history").then((r) => r.data),
};

// ── Users ─────────────────────────────────────────────────────
export const userApi = {
  getProfile: () =>
    api.get("/api/users/me/profile").then((r) => r.data),

  getKnowledgeGraph: () =>
    api.get("/api/users/me/knowledge-graph").then((r) => r.data),

  updateProgress: (pathId: string, day: number, topic: string) =>
    api.post(`/api/users/me/learning/${pathId}/progress`, { day, topic }).then((r) => r.data),
};
