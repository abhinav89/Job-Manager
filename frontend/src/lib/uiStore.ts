import type { ResumeTemplate } from "./resumeTemplates";
import { create } from "zustand";

type ResumeUiState = {
  editorMode: "friendly" | "preview" | "source";
  selectedTemplate: ResumeTemplate;
  setEditorMode: (mode: "friendly" | "preview" | "source") => void;
  setSelectedTemplate: (template: ResumeTemplate) => void;
};

export const useResumeUiStore = create<ResumeUiState>((set) => ({
  editorMode: "friendly",
  selectedTemplate: "classic",
  setEditorMode: (editorMode) => set({ editorMode }),
  setSelectedTemplate: (selectedTemplate) => set({ selectedTemplate }),
}));
