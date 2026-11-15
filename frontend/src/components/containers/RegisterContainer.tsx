import { useEffect } from "react";
import { useAppStore } from "../../store/useAppStore";
import { RegisterForm } from "../presentational/RegisterForm";

export function RegisterContainer() {
  const isAuthenticating = useAppStore((state) => state.isAuthenticating);
  const authError = useAppStore((state) => state.authError);
  const authFieldErrors = useAppStore((state) => state.authFieldErrors);
  const register = useAppStore((state) => state.register);
  const clearAuthErrors = useAppStore((state) => state.clearAuthErrors);

  useEffect(() => {
    clearAuthErrors();
  }, [clearAuthErrors]);

  return (
    <RegisterForm
      isSubmitting={isAuthenticating}
      error={authError}
      fieldErrors={authFieldErrors}
      onSubmit={(fullName, email, password) =>
        void register(fullName, email, password)
      }
    />
  );
}
