import { Link, useParams } from "react-router-dom";
import { mockAssignments, mockCourses } from "../data/mockData";

export function LabPage() {
  const { courseSlug, labId } = useParams();

  const course = mockCourses.find((item) => item.slug === courseSlug);

  const lab = mockAssignments.find(
    (assignment) =>
      assignment.id === Number(labId) && assignment.courseId === course?.id,
  );

  if (!course || !lab) {
    return (
      <main className="courses-section">
        <span className="eyebrow">LearnLens</span>
        <h1>Laboratory assignment not found</h1>
        <p>The requested laboratory assignment does not exist.</p>

        <Link className="secondary-button" to="/">
          Back to courses
        </Link>
      </main>
    );
  }

  return (
    <div className="app">
      <header className="app-header">
        <Link className="brand" to="/" aria-label="LearnLens home">
          <span className="brand__icon">L</span>
          <span>LearnLens</span>
        </Link>

        <nav className="navigation" aria-label="Primary navigation">
          <Link className="navigation__link" to="/">
            My Courses
          </Link>

          <Link className="navigation__link" to={`/courses/${course.slug}`}>
            {course.title}
          </Link>
        </nav>
      </header>

      <section className="hero">
        <div>
          <span className="eyebrow">{lab.topic}</span>
          <h1>{lab.title}</h1>
          <p>{lab.description}</p>
        </div>

        <div className="hero__streak">
          <strong>+{lab.xp} XP</strong>
          <span>{lab.difficulty}</span>
        </div>
      </section>

      <main className="dashboard">
        <Link className="back-link" to={`/courses/${course.slug}`}>
          <span className="back-link__arrow" aria-hidden="true">
            ←
          </span>
          <span>Back to laboratory list</span>
        </Link>
        <section className="submission-panel">
          <span className="eyebrow">Laboratory information</span>
          <h2>{lab.title}</h2>

          <p>{lab.description}</p>

          <div className="assignment-card__footer">
            <span>Difficulty: {lab.difficulty}</span>

            <span className={`status status--${lab.status}`}>
              {lab.status.replaceAll("-", " ")}
            </span>
          </div>
        </section>
      </main>
    </div>
  );
}
