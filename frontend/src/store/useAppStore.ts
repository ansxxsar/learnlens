import { create } from "zustand";
import {
  fetchAssignments,
  fetchProgress,
  fetchStudent,
  signOutStudent,
  submitPythonCode,
} from "../services/api";
import type {
  Assignment,
  StudentProfile,
  StudentProgress,
  SubmissionResult,
} from "../types";

interface AppState {
  assignments: Assignment[];
  progress: StudentProgress | null;
  student: StudentProfile | null;
  selectedAssignmentId: number | null;
  submissionResult: SubmissionResult | null;
  isLoading: boolean;
  isSubmitting: boolean;
  isSigningOut: boolean;
  isSignedOut: boolean;
  error: string | null;
  loadDashboard: () => Promise<void>;
  selectAssignment: (assignmentId: number) => void;
  submitCode: (code: string) => Promise<void>;
  signOut: () => Promise<void>;
}

export const useAppStore = create<AppState>((set, get) => ({
  assignments: [],
  progress: null,
  student: null,
  selectedAssignmentId: null,
  submissionResult: null,
  isLoading: false,
  isSubmitting: false,
  isSigningOut: false,
  isSignedOut: false,
  error: null,

  loadDashboard: async () => {
    set({ isLoading: true, isSignedOut: false, error: null });

    try {
      const [assignments, progress, student] = await Promise.all([
        fetchAssignments(),
        fetchProgress(),
        fetchStudent(),
      ]);

      set({
        assignments,
        progress,
        student,
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

  signOut: async () => {
    set({ isSigningOut: true, error: null });

    try {
      await signOutStudent();

      // Drop every piece of student data so nothing stays visible after sign-out.
      set({
        assignments: [],
        progress: null,
        student: null,
        selectedAssignmentId: null,
        submissionResult: null,
        isSigningOut: false,
        isSignedOut: true,
      });
    } catch {
      set({
        error: "Unable to sign out. Please try again.",
        isSigningOut: false,
      });
    }
  },
}));
