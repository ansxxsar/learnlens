import type { Course } from "../../types";

interface CourseCardProps {
  course: Course;
  onOpen: (courseSlug: string) => void;
}

export function CourseCard({ course, onOpen }: CourseCardProps) {
  const progress =
    course.totalLabs === 0
      ? 0
      : Math.round((course.completedLabs / course.totalLabs) * 100);

  return (
    <article className="course-card">
      <div
        className={`course-card__banner course-card__banner--${course.color}`}
      >
        <span>{course.category}</span>
      </div>

      <div className="course-card__content">
        <h3>{course.title}</h3>

        <p>{course.description}</p>

        <span className="course-card__instructor">
          Instructor: {course.instructor}
        </span>

        <div className="course-card__progress-header">
          <span>Course progress</span>
          <strong>{progress}%</strong>
        </div>

        <div
          className="course-card__progress"
          role="progressbar"
          aria-label={`${course.title} progress`}
          aria-valuenow={progress}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <div style={{ width: `${progress}%` }} />
        </div>

        <div className="course-card__footer">
          <span>
            {course.completedLabs} of {course.totalLabs} labs completed
          </span>

          <button type="button" onClick={() => onOpen(course.slug)}>
            Open course
          </button>
        </div>
      </div>
    </article>
  );
}
