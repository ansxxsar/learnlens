import { MyCoursesContainer } from "../components/containers/MyCoursesContainer";
import { ThemeSwitcherContainer } from "../components/containers/ThemeSwitcherContainer";
import { UserMenuContainer } from "../components/containers/UserMenuContainer";
import { BrandLink } from "../components/presentational/BrandLink";

interface TeacherHomePageProps {
  name: string;
}

export function TeacherHomePage({ name }: TeacherHomePageProps) {
  return (
    <div className="app">
      <header className="app-header">
        <BrandLink />

        <div className="app-header__actions">
          <ThemeSwitcherContainer />
          <UserMenuContainer />
        </div>
      </header>

      <section className="hero">
        <div>
          <span className="eyebrow">Teacher</span>
          <h1>Welcome, {name}</h1>
          <p>
            These are the courses you teach. Creating and managing tasks is
            coming next.
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
