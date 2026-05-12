import { create } from "zustand";

import type { AIExplain } from "../lib/schemas";

export const LANGUAGES = ["python", "c", "cpp", "java", "javascript", "typescript", "golang"] as const;

type AppState = {
  language: string;
  recentProblemId: string | null;
  setLanguage: (language: string) => void;
  setRecentProblemId: (problemId: string) => void;
  getDraft: (problemId: string, language: string) => string;
  setDraft: (problemId: string, language: string, code: string) => void;
  getCachedExplain: (submissionId: string) => AIExplain | null;
  setCachedExplain: (submissionId: string, explain: AIExplain) => void;
};

export const useAppStore = create<AppState>((set) => ({
  language: localStorage.getItem("fastoj.language") ?? "python",
  recentProblemId: localStorage.getItem("fastoj.recentProblem"),
  setLanguage: (language) => {
    localStorage.setItem("fastoj.language", language);
    set({ language });
  },
  setRecentProblemId: (problemId) => {
    localStorage.setItem("fastoj.recentProblem", problemId);
    set({ recentProblemId: problemId });
  },
  getDraft: (problemId, language) => localStorage.getItem(`fastoj.draft.${problemId}.${language}`) ?? "",
  setDraft: (problemId, language, code) => {
    localStorage.setItem(`fastoj.draft.${problemId}.${language}`, code);
  },
  getCachedExplain: (submissionId) => {
    const raw = localStorage.getItem(`fastoj.ai.explain.${submissionId}`);
    return raw ? JSON.parse(raw) : null;
  },
  setCachedExplain: (submissionId, explain) => {
    localStorage.setItem(`fastoj.ai.explain.${submissionId}`, JSON.stringify(explain));
  },
}));
