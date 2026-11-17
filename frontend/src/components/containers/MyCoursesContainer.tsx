import { useMyCourses } from "../../hooks/useMyCourses";
import { CourseCard } from "../presentational/CourseCard";

interface MyCoursesContainerProps {
  title: string;
  emptyMessage: string;
}

export function MyCoursesContainer({
  title,
  emptyMessage,
}: MyCoursesContainerProps) {
  const { courses, isLoading, error } = useMyCourses();

  return (
    <section className="my-courses" aria-labelledby="my-courses-title">
      <div className="section-heading">
        <span className="eyebrow">Courses</span>
        <h2 id="my-courses-title">{title}</h2>
      </div>

      {isLoading && <p className="state-message">Loading your courses...</p>}
      {error && <p className="error-message">{error}</p>}
      {!isLoading && !error && courses.length === 0 && (
        <p className="state-message">{emptyMessage}</p>
      )}

      {courses.length > 0 && (
        <div className="my-courses__grid">
          {courses.map((course) => (
            <CourseCard key={course.id} course={course} />
          ))}
        </div>
      )}
    </section>
  );
}
