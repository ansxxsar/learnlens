import { IconLink } from "./IconLink";

interface PendingApprovalPanelProps {
  email: string;
}

export function PendingApprovalPanel({ email }: PendingApprovalPanelProps) {
  return (
    <section className="auth-panel" aria-live="polite">
      <span className="eyebrow">Teacher account</span>
      <h1>Waiting for approval</h1>
      <p>
        Your account {email} needs to be approved by an administrator before you
        can use LearnLens as a teacher. If you are a student, ask to be enrolled
        in your course.
      </p>
      <div className="auth-panel__links">
        <IconLink to="/account" icon="account" label="My account" />
        <IconLink to="/sign-out" icon="signOut" label="Sign out" isDanger />
      </div>
    </section>
  );
}
