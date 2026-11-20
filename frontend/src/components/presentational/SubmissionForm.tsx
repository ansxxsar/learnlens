import { useId } from "react";
import type { FormEvent } from "react";
import { languageOptions } from "../../data/languages";
import type { SubmitStatus } from "../../hooks/useSubmitStatus";
import type { ProgrammingLanguage } from "../../types";

interface SubmissionFormProps {
  language: ProgrammingLanguage;
  code: string;
  status: SubmitStatus;
  savedAttempt: number | null;
  onLanguageChange: (language: ProgrammingLanguage) => void;
  onCodeChange: (code: string) => void;
  onSubmit: () => void;
  onCancel: () => void;
}

export function SubmissionForm({
  language,
  code,
  status,
  savedAttempt,
  onLanguageChange,
  onCodeChange,
  onSubmit,
  onCancel,
}: SubmissionFormProps) {
  const languageId = useId();
  const codeId = useId();

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    onSubmit();
  };

  return (
    <form className="auth-form submission-form" onSubmit={handleSubmit}>
      {status.error && (
        <p className="error-message" role="alert">
          {status.error}
        </p>
      )}

      <div className="auth-form__field">
        <label htmlFor={languageId}>Language</label>
        <select
          id={languageId}
          className="account-card__select"
          value={language}
          onChange={(event) =>
            onLanguageChange(event.target.value as ProgrammingLanguage)
          }
        >
          {languageOptions.map((option) => (
            <option key={option.id} value={option.id}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <div className="auth-form__field">
        <label htmlFor={codeId}>Your code</label>
        <textarea
          id={codeId}
          className="submission-form__code"
          required
          rows={10}
          maxLength={50000}
          spellCheck={false}
          autoCapitalize="off"
          autoCorrect="off"
          value={code}
          aria-invalid={Boolean(status.fieldErrors.code)}
          onChange={(event) => onCodeChange(event.target.value)}
        />
        {status.fieldErrors.code && (
          <span className="auth-form__field-error">
            {status.fieldErrors.code.join(" ")}
          </span>
        )}
      </div>

      {savedAttempt !== null && (
        <p className="account-card__saved" role="status">
          Attempt {savedAttempt} saved. It counts for today's progress, and
          its test results will appear below.
        </p>
      )}

      <div className="account-card__row">
        <button
          className="primary-button"
          type="submit"
          disabled={status.isSaving}
        >
          {status.isSaving ? "Submitting..." : "Submit solution"}
        </button>
        <button
          className="secondary-button"
          type="button"
          disabled={status.isSaving}
          onClick={onCancel}
        >
          Close
        </button>
      </div>
    </form>
  );
}
