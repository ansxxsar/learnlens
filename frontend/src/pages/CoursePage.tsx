import { Link, useParams } from "react-router-dom";
import { mockAssignments, mockCourses } from "../data/mockData";

export function CoursePage() {
  const { courseSlug } = useParams();

  const course = mockCourses.find((item) => item.slug === courseSlug);

  if (!course) {
    return (
      <main className="courses-section">
        <h1>Course not found</h1>
        <Link to="/">Back to courses</Link>
      </main>
    );
  }

  const labs = mockAssignments.filter(
    (assignment) => assignment.courseId === course.id,
  );

  return (
    <div className="app">
      <header className="app-header">
        <Link className="brand" to="/">
          <span className="brand__icon">L</span>
          <span>LearnLens</span>
        </Link>

        <nav className="navigation" aria-label="Primary navigation">
          <Link className="navigation__link" to="/">
            My Courses
          </Link>
        </nav>
      </header>

      <section className="hero">
        <div>
          <span className="eyebrow">{course.category}</span>
          <h1>{course.title}</h1>
          <p>{course.description}</p>
          <p>Instructor: {course.instructor}</p>
        </div>
      </section>

      <main className="courses-section">
        <div className="section-heading">
          <span className="eyebrow">Course activities</span>
          <h2>Laboratory assignments</h2>
          <p>{labs.length} labs available</p>
        </div>

        {labs.length === 0 ? (
          <p className="state-message">
            No laboratory assignments have been published yet.
          </p>
        ) : (
          <div className="courses-grid">
            {labs.map((lab) => (
              <article className="course-card" key={lab.id}>
                <div className="course-card__content">
                  <span className="eyebrow">{lab.topic}</span>
                  <h3>{lab.title}</h3>
                  <p>{lab.description}</p>

                  <div className="course-card__footer">
                    <span>{lab.difficulty}</span>
                    <span className={`status status--${lab.status}`}>
                      {lab.status.replaceAll("-", " ")}
                    </span>
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
