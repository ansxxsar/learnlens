import type { ThemePreference } from "../types";

// index.html reads the same key before the first paint.
const STORAGE_KEY = "learnlens-theme";

export const readThemePreference = (): ThemePreference => {
  const theme = document.documentElement.dataset.theme;
  return theme === "light" || theme === "dark" ? theme : "system";
};

// "system" is the absence of a choice: without data-theme, the CSS follows the
// device setting and updates by itself when that setting changes.
export const saveThemePreference = (preference: ThemePreference): void => {
  if (preference === "system") {
    delete document.documentElement.dataset.theme;
  } else {
    document.documentElement.dataset.theme = preference;
  }

  try {
    if (preference === "system") {
      localStorage.removeItem(STORAGE_KEY);
    } else {
      localStorage.setItem(STORAGE_KEY, preference);
    }
  } catch {
    // Storage can be blocked. The choice still applies until the page reloads.
  }
};
