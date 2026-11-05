import { useCallback, useState } from "react";
import { ApiError } from "../services/api";

export interface SubmitStatus {
  isSaving: boolean;
  isSaved: boolean;
  error: string | null;
  fieldErrors: Record<string, string[]>;
}

// Tracks one form's request, so each form on a page shows its own result.
export function useSubmitStatus() {
  const [status, setStatus] = useState<SubmitStatus>({
    isSaving: false,
    isSaved: false,
    error: null,
    fieldErrors: {},
  });

  const run = useCallback(async (action: () => Promise<void>) => {
    setStatus({ isSaving: true, isSaved: false, error: null, fieldErrors: {} });

    try {
      await action();
      setStatus({ isSaving: false, isSaved: true, error: null, fieldErrors: {} });
      return true;
    } catch (error) {
      setStatus({
        isSaving: false,
        isSaved: false,
        error:
          error instanceof Error
            ? error.message
            : "Something went wrong. Please try again.",
        fieldErrors: error instanceof ApiError ? error.fieldErrors : {},
      });
      return false;
    }
  }, []);

  return { status, run };
}
