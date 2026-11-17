import type { MyCourse } from "../../types";

interface CourseCardProps {
  course: MyCourse;
}

const studentCountLabel = (count: number): string =>
  count === 1 ? "1 student" : `${count} students`;

export function CourseCard({ course }: CourseCardProps) {
  const isTeaching = course.role === "instructor";

  return (
    <article className="course-card">
      <div className="course-card__header">
        <span className="course-card__code">{course.code}</span>
        <span className="course-card__term">{course.term}</span>
      </div>

      <h3>{course.title}</h3>

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
            <dt>{course.instructorNames.length > 1 ? "Teachers" : "Teacher"}</dt>
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
