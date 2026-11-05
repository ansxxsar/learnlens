interface SignOutPanelProps {
  studentName: string | null;
  isSigningOut: boolean;
  isSignedOut: boolean;
  error: string | null;
  onConfirm: () => void;
  onCancel: () => void;
  onSignIn: () => void;
  onRegister: () => void;
}

export function SignOutPanel({
  studentName,
  isSigningOut,
  isSignedOut,
  error,
  onConfirm,
  onCancel,
  onSignIn,
  onRegister,
}: SignOutPanelProps) {
  if (isSignedOut) {
    return (
      <section className="auth-panel" aria-live="polite">
        <span className="auth-panel__icon" aria-hidden="true">
          ✓
        </span>
        <h1>You have been signed out</h1>
        <p>
          Thanks for learning with LearnLens. Sign in to your account, or create
          a new one.
        </p>

        <div className="auth-panel__actions">
          <button
            type="button"
            className="secondary-button"
            onClick={onRegister}
          >
            Create account
          </button>
          <button type="button" className="primary-button" onClick={onSignIn}>
            Sign in
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className="auth-panel">
      <span className="eyebrow">Account</span>
      <h1>Sign out of LearnLens?</h1>
      <p>
        {studentName ? `You are signed in as ${studentName}. ` : ""}
        Your submitted work is saved. Code you have not submitted yet will be
        lost.
      </p>

      {error && <p className="error-message">{error}</p>}

      <div className="auth-panel__actions">
        <button
          type="button"
          className="secondary-button"
          onClick={onCancel}
          disabled={isSigningOut}
        >
          Cancel
        </button>
        <button
          type="button"
          className="primary-button"
          onClick={onConfirm}
          disabled={isSigningOut}
        >
          {isSigningOut ? "Signing out..." : "Sign out"}
        </button>
      </div>
    </section>
  );
}
