import { create } from "zustand";
import { persist } from "zustand/middleware";

// ── User Store ────────────────────────────────────────────────
interface User {
  id: string;
  github_login: string;
  github_name: string;
  github_avatar_url: string;
  top_languages: string[];
  expertise_level: string;
  profile_analyzed: boolean;
}

interface UserStore {
  user: User | null;
  token: string | null;
  setUser: (user: User) => void;
  setToken: (token: string) => void;
  logout: () => void;
}

export const useUserStore = create<UserStore>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      setUser: (user) => set({ user }),
      setToken: (token) => {
        if (typeof window !== "undefined") {
          localStorage.setItem("mentor_token", token);
        }
        set({ token });
      },
      logout: () => {
        if (typeof window !== "undefined") {
          localStorage.removeItem("mentor_token");
        }
        set({ user: null, token: null });
      },
    }),
    { name: "mentor-user" }
  )
);

// ── Chatbot Store ─────────────────────────────────────────────
interface ChatbotStore {
  isOpen: boolean;
  setIsOpen: (isOpen: boolean) => void;
}

export const useChatbotStore = create<ChatbotStore>((set) => ({
  isOpen: false,
  setIsOpen: (isOpen) => set({ isOpen }),
}));

// ── Repo Store ────────────────────────────────────────────────
interface Repository {
  id: string;
  full_name: string;
  owner: string;
  name: string;
  description: string;
  stars: number;
  language: string;
  analysis_status: string;
  analysis_progress: number;
  purpose?: string;
  tech_stack?: string[];
  architecture_summary?: string;
  subsystems?: any[];
  architecture_diagram?: { nodes: any[]; edges: any[] };
  difficulty_level?: string;
  learning_prerequisites?: string[];
}

interface RepoStore {
  currentRepo: Repository | null;
  analyzedRepos: Repository[];
  setCurrentRepo: (repo: Repository) => void;
  updateRepoProgress: (progress: number, stage: string, status: string) => void;
  addAnalyzedRepo: (repo: Repository) => void;
}

export const useRepoStore = create<RepoStore>()((set) => ({
  currentRepo: null,
  analyzedRepos: [],
  setCurrentRepo: (repo) => set({ currentRepo: repo }),
  updateRepoProgress: (progress, stage, status) =>
    set((state) => ({
      currentRepo: state.currentRepo
        ? { ...state.currentRepo, analysis_progress: progress, analysis_stage: stage, analysis_status: status }
        : null,
    })),
  addAnalyzedRepo: (repo) =>
    set((state) => ({
      analyzedRepos: [repo, ...state.analyzedRepos.filter((r) => r.id !== repo.id)],
    })),
}));

// ── Mentor Store ──────────────────────────────────────────────
interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
  sources?: string[];
}

interface MentorStore {
  conversationId: string | null;
  messages: Message[];
  isStreaming: boolean;
  setConversationId: (id: string) => void;
  addMessage: (msg: Message) => void;
  updateLastMessage: (content: string) => void;
  setStreaming: (streaming: boolean) => void;
  clearConversation: () => void;
}

export const useMentorStore = create<MentorStore>()((set) => ({
  conversationId: null,
  messages: [],
  isStreaming: false,
  setConversationId: (id) => set({ conversationId: id }),
  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  updateLastMessage: (content) =>
    set((state) => ({
      messages: state.messages.map((m, i) =>
        i === state.messages.length - 1 ? { ...m, content } : m
      ),
    })),
  setStreaming: (streaming) => set({ isStreaming: streaming }),
  clearConversation: () => set({ messages: [], conversationId: null }),
}));
