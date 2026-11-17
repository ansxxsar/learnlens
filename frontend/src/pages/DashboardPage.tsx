import { DashboardContainer } from "../components/containers/DashboardContainer";
import { MyCoursesContainer } from "../components/containers/MyCoursesContainer";
import { PageHeader } from "../components/presentational/PageHeader";

export function DashboardPage() {
  return (
    <div className="app">
      <PageHeader>
        <nav className="navigation" aria-label="Main navigation">
          <a
            className="navigation__link navigation__link--active"
            href="#dashboard"
          >
            Dashboard
          </a>
          <a className="navigation__link" href="#assignments">
            Assignments
          </a>
          <a className="navigation__link" href="#progress">
            Progress
          </a>
        </nav>
      </PageHeader>

      <section className="hero" id="dashboard">
        <div>
          <span className="eyebrow">Welcome back</span>
          <h1>Turn every attempt into progress.</h1>
          <p>
            Write code in Python, Java, C++, JavaScript, HTML, or CSS, understand
            your mistakes, and receive a clear next step.
          </p>
        </div>

        <div className="hero__streak">
          <strong>5 day</strong>
          <span>learning streak</span>
        </div>
      </section>

      <MyCoursesContainer
        title="My courses"
        emptyMessage="You are not enrolled in any course yet. Your teacher or an administrator will add you."
      />

      <DashboardContainer />
    </div>
  );
}
