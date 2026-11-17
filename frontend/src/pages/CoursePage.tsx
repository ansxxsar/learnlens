import { Link, Navigate, useParams } from "react-router-dom";
import { CourseContainer } from "../components/containers/CourseContainer";
import { PageHeader } from "../components/presentational/PageHeader";

export function CoursePage() {
  const { courseId } = useParams();
  const id = Number(courseId);

  if (!Number.isInteger(id) || id <= 0) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="app">
      <PageHeader />

      <main className="course-page__main">
        <Link className="course-page__back" to="/">
          ← All courses
        </Link>
        <CourseContainer key={id} courseId={id} />
      </main>
    </div>
  );
}
