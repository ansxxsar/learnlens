import { useId, useState } from "react";
import type { InputHTMLAttributes } from "react";

interface AuthFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  hint?: string;
  errors?: string[];
}

function EyeIcon({ isCrossedOut }: { isCrossedOut: boolean }) {
  return (
    <svg
      viewBox="0 0 24 24"
      width="20"
      height="20"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7-10-7-10-7Z" />
      <circle cx="12" cy="12" r="3" />
      {isCrossedOut && <path d="M4 4l16 16" />}
    </svg>
  );
}

export function AuthField({
  label,
  hint,
  errors,
  type,
  ...inputProps
}: AuthFieldProps) {
  const id = useId();
  const [isPasswordVisible, setIsPasswordVisible] = useState(false);
  const isPassword = type === "password";
  const hintId = `${id}-hint`;
  const errorId = `${id}-error`;
  const hasErrors = Boolean(errors?.length);
  const describedBy = [hint && hintId, hasErrors && errorId]
    .filter(Boolean)
    .join(" ");

  return (
    <div className="auth-form__field">
      <label htmlFor={id}>{label}</label>
      <div className="auth-form__input">
        <input
          {...inputProps}
          id={id}
          type={isPassword && isPasswordVisible ? "text" : type}
          aria-invalid={hasErrors}
          aria-describedby={describedBy || undefined}
        />
        {isPassword && (
          <button
            type="button"
            className="auth-form__toggle"
            aria-label={`${isPasswordVisible ? "Hide" : "Show"} ${label.toLowerCase()}`}
            onClick={() => setIsPasswordVisible((visible) => !visible)}
          >
            <EyeIcon isCrossedOut={isPasswordVisible} />
          </button>
        )}
      </div>
      {hint && (
        <span className="auth-form__hint" id={hintId}>
          {hint}
        </span>
      )}
      {hasErrors && (
        <span className="auth-form__field-error" id={errorId}>
          {errors?.join(" ")}
        </span>
      )}
    </div>
  );
}
