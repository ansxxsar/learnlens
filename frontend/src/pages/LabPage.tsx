import { useEffect } from "react";
import { Link, useParams } from "react-router-dom";
import { CodeSubmissionForm } from "../components/presentational/CodeSubmissionForm";
import { FeedbackPanel } from "../components/presentational/FeedbackPanel";
import { languageOptions } from "../data/languages";
import { mockAssignments, mockCourses } from "../data/mockData";
import { useAppStore } from "../store/useAppStore";

export function LabPage() {
  const { courseSlug, labId } = useParams();

  const course = mockCourses.find((item) => item.slug === courseSlug);

  const lab = mockAssignments.find(
    (assignment) =>
      assignment.id === Number(labId) && assignment.courseId === course?.id,
  );

  const {
    selectedLanguage,
    submissionResult,
    isLoading,
    isSubmitting,
    error,
    loadDashboard,
    selectAssignment,
    selectLanguage,
    submitCode,
  } = useAppStore();

  useEffect(() => {
    if (!lab) {
      return;
    }

    const loadLab = async () => {
      await loadDashboard();
      selectAssignment(lab.id);
    };

    void loadLab();
  }, [lab, loadDashboard, selectAssignment]);

  if (!course || !lab) {
    return (
      <main className="courses-section">
        <span className="eyebrow">LearnLens</span>
        <h1>Laboratory assignment not found</h1>
        <p>The requested laboratory assignment does not exist.</p>

        <Link className="secondary-button" to="/">
          Back to courses
        </Link>
      </main>
    );
  }

  const allowedLanguages = languageOptions.filter((option) =>
    lab.languages.includes(option.id),
  );

  return (
    <div className="app">
      <header className="app-header">
        <Link className="brand" to="/" aria-label="LearnLens home">
          <span className="brand__icon">L</span>
          <span>LearnLens</span>
        </Link>

        <nav className="navigation" aria-label="Primary navigation">
          <Link className="navigation__link" to="/">
            My Courses
          </Link>

          <Link className="navigation__link" to={`/courses/${course.slug}`}>
            {course.title}
          </Link>
        </nav>
      </header>

      <section className="hero">
        <div>
          <span className="eyebrow">{lab.topic}</span>
          <h1>{lab.title}</h1>
          <p>{lab.description}</p>
        </div>

        <div className="hero__streak">
          <strong>+{lab.xp} XP</strong>
          <span>{lab.difficulty}</span>
        </div>
      </section>

      <main className="dashboard">
        <Link className="back-link" to={`/courses/${course.slug}`}>
          <span className="back-link__arrow" aria-hidden="true">
            ←
          </span>
          <span>Back to laboratory list</span>
        </Link>

        {error && <p className="error-message">{error}</p>}

        {isLoading ? (
          <p className="state-message">Loading laboratory workspace...</p>
        ) : (
          <div className="workspace">
            <CodeSubmissionForm
              assignmentTitle={lab.title}
              language={selectedLanguage}
              languages={allowedLanguages}
              isSubmitting={isSubmitting}
              onLanguageChange={selectLanguage}
              onSubmit={submitCode}
            />

            {submissionResult && <FeedbackPanel result={submissionResult} />}
          </div>
        )}
      </main>
    </div>
  );
}
