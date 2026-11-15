import { useEffect } from "react";
import { useAppStore } from "../../store/useAppStore";
import { SignInForm } from "../presentational/SignInForm";

export function SignInContainer() {
  const isAuthenticating = useAppStore((state) => state.isAuthenticating);
  const authError = useAppStore((state) => state.authError);
  const authFieldErrors = useAppStore((state) => state.authFieldErrors);
  const signIn = useAppStore((state) => state.signIn);
  const clearAuthErrors = useAppStore((state) => state.clearAuthErrors);

  useEffect(() => {
    clearAuthErrors();
  }, [clearAuthErrors]);

  return (
    <SignInForm
      isSubmitting={isAuthenticating}
      error={authError}
      fieldErrors={authFieldErrors}
      onSubmit={(email, password) => void signIn(email, password)}
    />
  );
}
