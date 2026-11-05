import { useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";
import { AuthField } from "./AuthField";

interface RegisterFormProps {
  isSubmitting: boolean;
  error: string | null;
  fieldErrors: Record<string, string[]>;
  onSubmit: (fullName: string, email: string, password: string) => void;
}

export function RegisterForm({
  isSubmitting,
  error,
  fieldErrors,
  onSubmit,
}: RegisterFormProps) {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordMismatch, setPasswordMismatch] = useState(false);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();

    const isMismatch = password !== confirmPassword;
    setPasswordMismatch(isMismatch);
    if (!isMismatch) {
      onSubmit(fullName, email, password);
    }
  };

  return (
    <section className="auth-panel">
      <span className="eyebrow">Account</span>
      <h1>Create your account</h1>

      <form className="auth-form" onSubmit={handleSubmit}>
        {error && (
          <p className="error-message" role="alert">
            {error}
          </p>
        )}

        <AuthField
          label="Full name"
          type="text"
          autoComplete="name"
          required
          maxLength={255}
          value={fullName}
          errors={fieldErrors.full_name}
          onChange={(event) => setFullName(event.target.value)}
        />

        <AuthField
          label="Email"
          type="email"
          autoComplete="email"
          required
          maxLength={255}
          hint="Use your @sdu.edu.kz email."
          value={email}
          errors={fieldErrors.email}
          onChange={(event) => setEmail(event.target.value)}
        />

        <AuthField
          label="Password"
          type="password"
          autoComplete="new-password"
          required
          hint="At least 8 characters, not only numbers."
          value={password}
          errors={fieldErrors.password}
          onChange={(event) => setPassword(event.target.value)}
        />

        <AuthField
          label="Confirm password"
          type="password"
          autoComplete="new-password"
          required
          value={confirmPassword}
          errors={passwordMismatch ? ["The passwords do not match."] : undefined}
          onChange={(event) => setConfirmPassword(event.target.value)}
        />

        <button type="submit" className="primary-button" disabled={isSubmitting}>
          {isSubmitting ? "Creating account..." : "Create account"}
        </button>
      </form>

      <p className="auth-form__switch">
        Already have an account? <Link to="/sign-in">Sign in</Link>
      </p>
    </section>
  );
}
