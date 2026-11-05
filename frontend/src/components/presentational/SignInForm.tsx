import { useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";
import { AuthField } from "./AuthField";

interface SignInFormProps {
  isSubmitting: boolean;
  error: string | null;
  fieldErrors: Record<string, string[]>;
  onSubmit: (email: string, password: string) => void;
}

export function SignInForm({
  isSubmitting,
  error,
  fieldErrors,
  onSubmit,
}: SignInFormProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    onSubmit(email, password);
  };

  return (
    <section className="auth-panel">
      <span className="eyebrow">Account</span>
      <h1>Sign in to LearnLens</h1>

      <form className="auth-form" onSubmit={handleSubmit}>
        {error && (
          <p className="error-message" role="alert">
            {error}
          </p>
        )}

        <AuthField
          label="Email"
          type="email"
          autoComplete="email"
          required
          value={email}
          errors={fieldErrors.email}
          onChange={(event) => setEmail(event.target.value)}
        />

        <AuthField
          label="Password"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          errors={fieldErrors.password}
          onChange={(event) => setPassword(event.target.value)}
        />

        <button type="submit" className="primary-button" disabled={isSubmitting}>
          {isSubmitting ? "Signing in..." : "Sign in"}
        </button>
      </form>

      <p className="auth-form__switch">
        New to LearnLens? <Link to="/register">Create an account</Link>
      </p>
    </section>
  );
}
