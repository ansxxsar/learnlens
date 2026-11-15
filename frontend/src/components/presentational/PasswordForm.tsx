import { useState } from "react";
import type { FormEvent } from "react";
import type { SubmitStatus } from "../../hooks/useSubmitStatus";
import { AuthField } from "./AuthField";

interface PasswordFormProps {
  status: SubmitStatus;
  onSave: (currentPassword: string, newPassword: string) => Promise<boolean>;
}

export function PasswordForm({ status, onSave }: PasswordFormProps) {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isMismatch, setIsMismatch] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();

    const mismatch = newPassword !== confirmPassword;
    setIsMismatch(mismatch);
    if (mismatch) {
      return;
    }

    if (await onSave(currentPassword, newPassword)) {
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    }
  };

  return (
    <section className="account-card">
      <h2>Change password</h2>
      <form className="auth-form" onSubmit={(event) => void handleSubmit(event)}>
        {status.error && (
          <p className="error-message" role="alert">
            {status.error}
          </p>
        )}

        <AuthField
          label="Current password"
          type="password"
          autoComplete="current-password"
          required
          value={currentPassword}
          errors={status.fieldErrors.current_password}
          onChange={(event) => setCurrentPassword(event.target.value)}
        />
        <AuthField
          label="New password"
          type="password"
          autoComplete="new-password"
          required
          hint="At least 8 characters, not only numbers."
          value={newPassword}
          errors={status.fieldErrors.new_password}
          onChange={(event) => setNewPassword(event.target.value)}
        />
        <AuthField
          label="Confirm new password"
          type="password"
          autoComplete="new-password"
          required
          value={confirmPassword}
          errors={isMismatch ? ["The passwords do not match."] : undefined}
          onChange={(event) => setConfirmPassword(event.target.value)}
        />

        <div className="account-card__row">
          <button
            type="submit"
            className="primary-button"
            disabled={status.isSaving}
          >
            {status.isSaving ? "Saving..." : "Change password"}
          </button>
          {status.isSaved && (
            <p className="account-card__saved" role="status">
              ✓ Password changed. Other devices were signed out.
            </p>
          )}
        </div>
      </form>
    </section>
  );
}
