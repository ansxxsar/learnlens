import { create } from "zustand";
import {
  fetchAssignments,
  fetchProgress,
  submitPythonCode,
} from "../services/api";
import type { Assignment, StudentProgress, SubmissionResult } from "../types";

interface AppState {
  assignments: Assignment[];
  progress: StudentProgress | null;
  selectedAssignmentId: number | null;
  submissionResult: SubmissionResult | null;
  isLoading: boolean;
  isSubmitting: boolean;
  error: string | null;
  loadDashboard: () => Promise<void>;
  selectAssignment: (assignmentId: number) => void;
  submitCode: (code: string) => Promise<void>;
}

export const useAppStore = create<AppState>((set, get) => ({
  assignments: [],
  progress: null,
  selectedAssignmentId: null,
  submissionResult: null,
  isLoading: false,
  isSubmitting: false,
  error: null,

  loadDashboard: async () => {
    set({ isLoading: true, error: null });

    try {
      const [assignments, progress] = await Promise.all([
        fetchAssignments(),
        fetchProgress(),
      ]);

      set({
        assignments,
        progress,
        selectedAssignmentId: assignments[0]?.id ?? null,
        isLoading: false,
      });
    } catch {
      set({
        error: "Unable to load the LearnLens dashboard.",
        isLoading: false,
      });
    }
  },

  selectAssignment: (assignmentId) => {
    set({
      selectedAssignmentId: assignmentId,
      submissionResult: null,
      error: null,
    });
  },

  submitCode: async (code) => {
    const assignmentId = get().selectedAssignmentId;

    if (assignmentId === null) {
      set({ error: "Select an assignment first." });
      return;
    }

    set({ isSubmitting: true, error: null, submissionResult: null });

    try {
      const submissionResult = await submitPythonCode(assignmentId, code);
      set({ submissionResult, isSubmitting: false });
    } catch (error) {
      set({
        error:
          error instanceof Error
            ? error.message
            : "Unable to submit the solution.",
        isSubmitting: false,
      });
    }
  },
}));
