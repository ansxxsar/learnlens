import { create } from "zustand";
import { defaultLanguage } from "../data/languages";
import {
  ApiError,
  fetchAssignments,
  fetchCurrentStudent,
  fetchProgress,
  register as registerAccount,
  signIn as signInWithPassword,
  signOut as endSession,
  submitSolution,
} from "../services/api";
import type {
  Assignment,
  ProgrammingLanguage,
  StudentProfile,
  StudentProgress,
  SubmissionResult,
} from "../types";

// Keep the current language when the assignment allows it; otherwise use the
// assignment's first allowed language (e.g. HTML for the HTML assignment).
const languageFor = (
  assignment: Assignment | undefined,
  current: ProgrammingLanguage,
): ProgrammingLanguage =>
  !assignment || assignment.languages.includes(current)
    ? current
    : (assignment.languages[0] ?? current);

const authErrorState = (error: unknown) => ({
  isAuthenticating: false,
  authError:
    error instanceof Error
      ? error.message
      : "Something went wrong. Please try again.",
  authFieldErrors: error instanceof ApiError ? error.fieldErrors : {},
});

interface AppState {
  assignments: Assignment[];
  progress: StudentProgress | null;
  student: StudentProfile | null;
  selectedAssignmentId: number | null;
  selectedLanguage: ProgrammingLanguage;
  submissionResult: SubmissionResult | null;
  isLoading: boolean;
  isSubmitting: boolean;
  isSigningOut: boolean;
  isSignedOut: boolean;
  error: string | null;
  isAuthChecked: boolean;
  isAuthenticating: boolean;
  authError: string | null;
  authFieldErrors: Record<string, string[]>;
  loadSession: () => Promise<void>;
  signIn: (email: string, password: string) => Promise<void>;
  register: (fullName: string, email: string, password: string) => Promise<void>;
  clearAuthErrors: () => void;
  loadDashboard: () => Promise<void>;
  selectAssignment: (assignmentId: number) => void;
  selectLanguage: (language: ProgrammingLanguage) => void;
  submitCode: (code: string) => Promise<void>;
  signOut: () => Promise<void>;
}

export const useAppStore = create<AppState>((set, get) => ({
  assignments: [],
  progress: null,
  student: null,
  selectedAssignmentId: null,
  selectedLanguage: defaultLanguage,
  submissionResult: null,
  isLoading: false,
  isSubmitting: false,
  isSigningOut: false,
  isSignedOut: false,
  error: null,
  isAuthChecked: false,
  isAuthenticating: false,
  authError: null,
  authFieldErrors: {},

  loadSession: async () => {
    try {
      set({ student: await fetchCurrentStudent(), isAuthChecked: true });
    } catch {
      // Without a confirmed session, treat the visitor as signed out.
      set({ student: null, isAuthChecked: true });
    }
  },

  signIn: async (email, password) => {
    set({ isAuthenticating: true, authError: null, authFieldErrors: {} });

    try {
      const student = await signInWithPassword(email, password);
      set({ student, isAuthenticating: false, isSignedOut: false });
    } catch (error) {
      set(authErrorState(error));
    }
  },

  register: async (fullName, email, password) => {
    set({ isAuthenticating: true, authError: null, authFieldErrors: {} });

    try {
      const student = await registerAccount(fullName, email, password);
      set({ student, isAuthenticating: false, isSignedOut: false });
    } catch (error) {
      set(authErrorState(error));
    }
  },

  clearAuthErrors: () => {
    set({ authError: null, authFieldErrors: {} });
  },

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
        selectedLanguage: languageFor(assignments[0], get().selectedLanguage),
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
    const assignment = get().assignments.find(
      (candidate) => candidate.id === assignmentId,
    );

    set({
      selectedAssignmentId: assignmentId,
      selectedLanguage: languageFor(assignment, get().selectedLanguage),
      submissionResult: null,
      error: null,
    });
  },

  selectLanguage: (language) => {
    // Feedback belongs to one language, so clear it when the student switches.
    set({ selectedLanguage: language, submissionResult: null, error: null });
  },

  submitCode: async (code) => {
    const { selectedAssignmentId: assignmentId, selectedLanguage } = get();

    if (assignmentId === null) {
      set({ error: "Select an assignment first." });
      return;
    }

    set({ isSubmitting: true, error: null, submissionResult: null });

    try {
      const submissionResult = await submitSolution(
        assignmentId,
        selectedLanguage,
        code,
      );
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
      await endSession();

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
