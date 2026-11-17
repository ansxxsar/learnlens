import { create } from "zustand";
import {
  ApiError,
  fetchCurrentStudent,
  fetchProgress,
  register as registerAccount,
  removeProfilePhoto as deleteProfilePhoto,
  signIn as signInWithPassword,
  signOut as endSession,
  updateProfile as saveProfile,
  uploadProfilePhoto as saveProfilePhoto,
} from "../services/api";
import type {
  ProgrammingLanguage,
  StudentProfile,
  StudentProgress,
  ThemePreference,
} from "../types";
import { readThemePreference, saveThemePreference } from "../services/theme";

const authErrorState = (error: unknown) => ({
  isAuthenticating: false,
  authError:
    error instanceof Error
      ? error.message
      : "Something went wrong. Please try again.",
  authFieldErrors: error instanceof ApiError ? error.fieldErrors : {},
});

interface AppState {
  progress: StudentProgress | null;
  student: StudentProfile | null;
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
  loadProgress: () => Promise<void>;
  signOut: () => Promise<void>;
}

export const useAppStore = create<AppState>((set) => ({
  progress: null,
  student: null,
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
    });
  },

  uploadPhoto: async (photo) => {
    set({ student: await saveProfilePhoto(photo) });
  },

  removePhoto: async () => {
    set({ student: await deleteProfilePhoto() });
  },

  loadProgress: async () => {
    try {
      set({ progress: await fetchProgress(), error: null });
    } catch {
      set({ error: "Unable to load your progress." });
    }
  },

  signOut: async () => {
    set({ isSigningOut: true, error: null });

    try {
      await endSession();

      // Drop every piece of student data so nothing stays visible after sign-out.
      set({
        progress: null,
        student: null,
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
