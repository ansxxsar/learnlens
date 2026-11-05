import { Link } from "react-router-dom";

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
      <p className="auth-form__switch">
        <Link to="/sign-out">Sign out</Link>
      </p>
    </section>
  );
}
