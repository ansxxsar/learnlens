import { Link } from "react-router-dom";

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
      <p className="auth-form__switch">
        <Link to="/sign-out">Sign out</Link>
      </p>
    </section>
  );
}
