import { useId, useState } from "react";
import type { FormEvent } from "react";
import { languageOptions } from "../../data/languages";
import type { SubmitStatus } from "../../hooks/useSubmitStatus";
import type { ProgrammingLanguage, StudentProfile } from "../../types";
import { AuthField } from "./AuthField";

interface ProfileFormProps {
  student: StudentProfile;
  status: SubmitStatus;
  onSave: (changes: {
    fullName: string;
    preferredLanguage: ProgrammingLanguage | null;
  }) => void;
}

export function ProfileForm({ student, status, onSave }: ProfileFormProps) {
  const languageId = useId();
  const [fullName, setFullName] = useState(student.name);
  const [language, setLanguage] = useState<ProgrammingLanguage | "">(
    student.preferredLanguage ?? "",
  );

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    onSave({ fullName, preferredLanguage: language || null });
  };

  return (
    <section className="account-card">
      <h2>Edit profile</h2>
      <form className="auth-form" onSubmit={handleSubmit}>
        {status.error && (
          <p className="error-message" role="alert">
            {status.error}
          </p>
        )}

        <AuthField
          label="Full name"
          type="text"
          autoComplete="name"
          required
          maxLength={255}
          value={fullName}
          errors={status.fieldErrors.full_name}
          onChange={(event) => setFullName(event.target.value)}
        />

        <div className="auth-form__field">
          <span>Email</span>
          <div className="account-card__readonly">{student.email}</div>
          <span className="auth-form__hint">
            Your university email can't be changed, because it decides your
            account type.
          </span>
        </div>

        <div className="auth-form__field">
          <label htmlFor={languageId}>Favorite language</label>
          <select
            id={languageId}
            className="account-card__select"
            value={language}
            onChange={(event) =>
              setLanguage(event.target.value as ProgrammingLanguage | "")
            }
          >
            <option value="">No favorite</option>
            {languageOptions.map((option) => (
              <option key={option.id} value={option.id}>
                {option.label}
              </option>
            ))}
          </select>
          <span className="auth-form__hint">
            Your code editor starts with this language when an assignment allows
            it.
          </span>
        </div>

        <div className="account-card__row">
          <button
            type="submit"
            className="primary-button"
            disabled={status.isSaving}
          >
            {status.isSaving ? "Saving..." : "Save changes"}
          </button>
          {status.isSaved && (
            <p className="account-card__saved" role="status">
              ✓ Saved
            </p>
          )}
        </div>
      </form>
    </section>
  );
}
