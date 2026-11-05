import { IconLink } from "./IconLink";

interface TeacherHomePanelProps {
  name: string;
  courses: string[];
}

export function TeacherHomePanel({ name, courses }: TeacherHomePanelProps) {
  return (
    <section className="auth-panel">
      <span className="eyebrow">Teacher</span>
      <h1>Welcome, {name}</h1>
      <p>Creating and managing tasks is coming next. Your courses:</p>
      <ul className="teacher-courses">
        {courses.map((course) => (
          <li key={course}>{course}</li>
        ))}
      </ul>
      <div className="auth-panel__links">
        <IconLink to="/account" icon="account" label="My account" />
        <IconLink to="/sign-out" icon="signOut" label="Sign out" isDanger />
      </div>
    </section>
  );
}
