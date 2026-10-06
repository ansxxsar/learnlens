import { DashboardContainer } from "../components/containers/DashboardContainer";
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
          <a className="navigation__link" href="#assignments">
            Assignments
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

      <DashboardContainer />
    </div>
  );
}
