import { Link } from "react-router-dom";
import type { MyCourse } from "../../types";

interface CourseCardProps {
  course: MyCourse;
  // Set on the course list, where the whole card opens the course.
  isLink?: boolean;
}

const studentCountLabel = (count: number): string =>
  count === 1 ? "1 student" : `${count} students`;

export function CourseCard({ course, isLink = false }: CourseCardProps) {
  const isTeaching = course.role === "instructor";

  return (
    <article className={`course-card ${isLink ? "course-card--link" : ""}`}>
      <div className="course-card__header">
        <span className="course-card__code">{course.code}</span>
        <span className="course-card__term">{course.term}</span>
      </div>

      <h3>
        {isLink ? (
          // The link covers the whole card through CSS, so the card is one
          // big click target while screen readers hear only the title.
          <Link className="course-card__link" to={`/course/${course.id}`}>
            {course.title}
          </Link>
        ) : (
          course.title
        )}
      </h3>

      <dl className="course-card__details">
        <div>
          <dt>Section</dt>
          <dd>{course.sectionCode ?? "Whole course"}</dd>
        </div>

        {isTeaching && course.studentCount !== null ? (
          <div>
            <dt>Students</dt>
            <dd>{studentCountLabel(course.studentCount)}</dd>
          </div>
        ) : (
          <div>
            <dt>
              {course.instructorNames.length > 1 ? "Teachers" : "Teacher"}
            </dt>
            <dd>
              {course.instructorNames.length > 0
                ? course.instructorNames.join(", ")
                : "Not assigned yet"}
            </dd>
          </div>
        )}
      </dl>
    </article>
  );
}
