import { MyCoursesContainer } from "../components/containers/MyCoursesContainer";
import { ProgressContainer } from "../components/containers/ProgressContainer";
import { PageHeader } from "../components/presentational/PageHeader";
import { useAppStore } from "../store/useAppStore";

export function DashboardPage() {
  // Loaded by ProgressContainer below; the hero shows the same streak.
  const progress = useAppStore((state) => state.progress);

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
          <a className="navigation__link" href="#courses">
            Courses
          </a>
          <a className="navigation__link" href="#progress">
            Progress
          </a>
        </nav>
      </PageHeader>

      <section className="hero" id="dashboard">
        <div>
          <span className="eyebrow">Student · Welcome back</span>
          <h1>Turn every attempt into progress.</h1>
          <p>
            Write code in Python, Java, C++, JavaScript, HTML, or CSS, understand
            your mistakes, and receive a clear next step.
          </p>
        </div>

        {progress && (
          <div className="hero__streak">
            <strong>
              {progress.streakDays} {progress.streakDays === 1 ? "day" : "days"}
            </strong>
            <span>learning streak</span>
          </div>
        )}
      </section>

      <main>
        <MyCoursesContainer
          title="My courses"
          emptyMessage="You are not enrolled in any course yet. Your teacher or an administrator will add you."
        />

        <div className="dashboard">
          <ProgressContainer />
        </div>
      </main>
    </div>
  );
}
