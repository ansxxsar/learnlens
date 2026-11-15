import { create } from "zustand";
import { defaultLanguage, starterCode } from "../data/languages";
import {
  ApiError,
  fetchAssignments,
  fetchCurrentStudent,
  fetchProgress,
  register as registerAccount,
  removeProfilePhoto as deleteProfilePhoto,
  signIn as signInWithPassword,
  signOut as endSession,
  submitSolution,
  updateProfile as saveProfile,
  uploadProfilePhoto as saveProfilePhoto,
} from "../services/api";
import type {
  Assignment,
  ProgrammingLanguage,
  StudentProfile,
  StudentProgress,
  SubmissionResult,
  ThemePreference,
} from "../types";
import { readThemePreference, saveThemePreference } from "../services/theme";

// Keep the current language when the assignment allows it; otherwise use the
// assignment's first allowed language (e.g. HTML for the HTML assignment).
const languageFor = (
  assignment: Assignment | undefined,
  current: ProgrammingLanguage,
): ProgrammingLanguage =>
  !assignment || assignment.languages.includes(current)
    ? current
    : (assignment.languages[0] ?? current);

const preferredLanguageOf = (
  student: StudentProfile | null,
  current: ProgrammingLanguage,
): ProgrammingLanguage => student?.preferredLanguage ?? current;

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
  // In the store so unsubmitted code survives leaving the dashboard. One draft
  // per language, so switching languages never discards typed code.
  codeDrafts: Record<ProgrammingLanguage, string>;
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
  themePreference: ThemePreference;
  setThemePreference: (preference: ThemePreference) => void;
  loadSession: () => Promise<void>;
  signIn: (email: string, password: string) => Promise<void>;
  register: (fullName: string, email: string, password: string) => Promise<void>;
  clearAuthErrors: () => void;
  // These throw on failure, so the form that called them can show the error.
  updateProfile: (changes: {
    fullName: string;
    preferredLanguage: ProgrammingLanguage | null;
  }) => Promise<void>;
  uploadPhoto: (photo: File) => Promise<void>;
  removePhoto: () => Promise<void>;
  loadDashboard: () => Promise<void>;
  selectAssignment: (assignmentId: number) => void;
  selectLanguage: (language: ProgrammingLanguage) => void;
  setCodeDraft: (language: ProgrammingLanguage, code: string) => void;
  submitCode: (code: string) => Promise<void>;
  signOut: () => Promise<void>;
}

export const useAppStore = create<AppState>((set, get) => ({
  assignments: [],
  progress: null,
  student: null,
  selectedAssignmentId: null,
  selectedLanguage: defaultLanguage,
  codeDrafts: starterCode,
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
  themePreference: readThemePreference(),

  setThemePreference: (preference) => {
    saveThemePreference(preference);
    set({ themePreference: preference });
  },

  loadSession: async () => {
    try {
      const student = await fetchCurrentStudent();
      set({
        student,
        selectedLanguage: preferredLanguageOf(student, get().selectedLanguage),
        isAuthChecked: true,
      });
    } catch {
      // Without a confirmed session, treat the visitor as signed out.
      set({ student: null, isAuthChecked: true });
    }
  },

  signIn: async (email, password) => {
    set({ isAuthenticating: true, authError: null, authFieldErrors: {} });

    try {
      const student = await signInWithPassword(email, password);
      set({
        student,
        selectedLanguage: preferredLanguageOf(student, get().selectedLanguage),
        isAuthenticating: false,
        isSignedOut: false,
      });
    } catch (error) {
      set(authErrorState(error));
    }
  },

  register: async (fullName, email, password) => {
    set({ isAuthenticating: true, authError: null, authFieldErrors: {} });

    try {
      const student = await registerAccount(fullName, email, password);
      set({
        student,
        selectedLanguage: preferredLanguageOf(student, get().selectedLanguage),
        isAuthenticating: false,
        isSignedOut: false,
      });
    } catch (error) {
      set(authErrorState(error));
    }
  },

  clearAuthErrors: () => {
    set({ authError: null, authFieldErrors: {} });
  },

  updateProfile: async (changes) => {
    const student = await saveProfile(changes);
    set({
      student,
      selectedLanguage: preferredLanguageOf(student, get().selectedLanguage),
    });
  },

  uploadPhoto: async (photo) => {
    set({ student: await saveProfilePhoto(photo) });
  },

  removePhoto: async () => {
    set({ student: await deleteProfilePhoto() });
  },

  loadDashboard: async () => {
    set({ isLoading: true, error: null });

    try {
      const [assignments, progress] = await Promise.all([
        fetchAssignments(),
        fetchProgress(),
      ]);

      // Coming back to the dashboard keeps the assignment the student had open.
      const selectedAssignment =
        assignments.find(
          (assignment) => assignment.id === get().selectedAssignmentId,
        ) ?? assignments[0];

      set({
        assignments,
        progress,
        selectedAssignmentId: selectedAssignment?.id ?? null,
        selectedLanguage: languageFor(
          selectedAssignment,
          get().selectedLanguage,
        ),
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

  setCodeDraft: (language, code) => {
    set((state) => ({
      codeDrafts: { ...state.codeDrafts, [language]: code },
    }));
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
        selectedLanguage: defaultLanguage,
        codeDrafts: starterCode,
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
