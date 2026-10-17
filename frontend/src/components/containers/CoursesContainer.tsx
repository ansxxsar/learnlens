import { useNavigate } from "react-router-dom";
import { mockCourses } from "../../data/mockData";
import { CourseCard } from "../presentational/CourseCard";

export function CoursesContainer() {
  const navigate = useNavigate();

  const openCourse = (courseSlug: string) => {
    navigate(`/courses/${courseSlug}`);
  };

  return (
    <main className="courses-section" id="courses">
      <div className="section-heading">
        <span className="eyebrow">Your learning</span>
        <h2>My Courses</h2>
        <p>Select a course to view and complete its laboratory assignments.</p>
      </div>

      <div className="courses-grid">
        {mockCourses.map((course) => (
          <CourseCard key={course.id} course={course} onOpen={openCourse} />
        ))}
      </div>
    </main>
  );
}
