import { MyCoursesContainer } from "../components/containers/MyCoursesContainer";
import { PageHeader } from "../components/presentational/PageHeader";

interface TeacherHomePageProps {
  name: string;
}

export function TeacherHomePage({ name }: TeacherHomePageProps) {
  return (
    <div className="app">
      <PageHeader />

      <section className="hero">
        <div>
          <span className="eyebrow">Teacher</span>
          <h1>Welcome, {name}</h1>
          <p>
            Open a course to create assignments and publish them to your
            students.
          </p>
        </div>
      </section>

      <main>
        <MyCoursesContainer
          title="Courses I teach"
          emptyMessage="You do not teach any course yet. An administrator will add you to your courses."
        />
      </main>
    </div>
  );
}
