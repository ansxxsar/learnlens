import { CoursesContainer } from "../components/containers/CoursesContainer";
import { UserMenuContainer } from "../components/containers/UserMenuContainer";

export function DashboardPage() {
  return (
    <div className="app">
      <header className="app-header">
        <a className="brand" href="/" aria-label="LearnLens home">
          <span className="brand__icon">L</span>
          <span>LearnLens</span>
        </a>

        <nav className="navigation" aria-label="Main navigation">
          <a
            className="navigation__link navigation__link--active"
            href="#dashboard"
          >
            Dashboard
          </a>

          <a className="navigation__link" href="#courses">
            Courses
          </a>

          <a className="navigation__link" href="#progress">
            Progress
          </a>
        </nav>

        <UserMenuContainer />
      </header>

      <section className="hero" id="dashboard">
        <div>
          <span className="eyebrow">Welcome back</span>
          <h1>Continue your learning journey.</h1>
          <p>
            Select a course, complete laboratory assignments, receive
            personalized feedback, and monitor your progress.
          </p>
        </div>

        <div className="hero__streak">
          <strong>5 day</strong>
          <span>learning streak</span>
        </div>
      </section>

      <CoursesContainer />
    </div>
  );
}
