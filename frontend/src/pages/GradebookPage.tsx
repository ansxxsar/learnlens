import { Link, Navigate, useParams } from "react-router-dom";
import { GradebookContainer } from "../components/containers/GradebookContainer";
import { PageHeader } from "../components/presentational/PageHeader";

export function GradebookPage() {
  const { courseId } = useParams();
  const id = Number(courseId);

  if (!Number.isInteger(id) || id <= 0) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="app">
      <PageHeader />
      <main className="course-page__main">
        <Link className="course-page__back" to={`/course/${id}`}>
          ← Back to the course
        </Link>
        <GradebookContainer key={id} courseId={id} />
      </main>
    </div>
  );
}
