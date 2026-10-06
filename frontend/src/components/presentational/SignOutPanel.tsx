interface SignOutPanelProps {
  studentName: string | null;
  isSigningOut: boolean;
  isSignedOut: boolean;
  error: string | null;
  onConfirm: () => void;
  onCancel: () => void;
  onSignInAgain: () => void;
}

export function SignOutPanel({
  studentName,
  isSigningOut,
  isSignedOut,
  error,
  onConfirm,
  onCancel,
  onSignInAgain,
}: SignOutPanelProps) {
  if (isSignedOut) {
    return (
      <section className="sign-out-panel" aria-live="polite">
        <span className="sign-out-panel__icon" aria-hidden="true">
          ✓
        </span>
        <h1>You have been signed out</h1>
        <p>Thanks for learning with LearnLens. See you next time.</p>

        <div className="sign-out-panel__actions">
          <button
            type="button"
            className="primary-button"
            onClick={onSignInAgain}
          >
            Sign in again
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className="sign-out-panel">
      <span className="eyebrow">Account</span>
      <h1>Sign out of LearnLens?</h1>
      <p>
        {studentName ? `You are signed in as ${studentName}. ` : ""}
        Your submitted work is saved. Code you have not submitted yet will be
        lost.
      </p>

      {error && <p className="error-message">{error}</p>}

      <div className="sign-out-panel__actions">
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
