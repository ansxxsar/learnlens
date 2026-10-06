import { useEffect } from "react";
import { languageOptions } from "../../data/languages";
import { useAppStore } from "../../store/useAppStore";
import { AssignmentCard } from "../presentational/AssignmentCard";
import { CodeSubmissionForm } from "../presentational/CodeSubmissionForm";
import { FeedbackPanel } from "../presentational/FeedbackPanel";
import { ProgressPanel } from "../presentational/ProgressPanel";

export function DashboardContainer() {
  const {
    assignments,
    progress,
    selectedAssignmentId,
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
    void loadDashboard();
  }, [loadDashboard]);

  if (isLoading) {
    return <p className="state-message">Loading LearnLens dashboard...</p>;
  }

  const selectedAssignment = assignments.find(
    (assignment) => assignment.id === selectedAssignmentId,
  );
  const allowedLanguages = languageOptions.filter((option) =>
    selectedAssignment?.languages.includes(option.id),
  );

  return (
    <main className="dashboard">
      {progress && <ProgressPanel progress={progress} />}

      {error && <p className="error-message">{error}</p>}

      <div className="dashboard__grid">
        <aside className="assignment-list" id="assignments">
          <div className="section-heading">
            <span className="eyebrow">Programming course</span>
            <h2>Assignments</h2>
          </div>

          {assignments.map((assignment) => (
            <AssignmentCard
              key={assignment.id}
              assignment={assignment}
              isSelected={assignment.id === selectedAssignmentId}
              onSelect={selectAssignment}
            />
          ))}
        </aside>

        <div className="workspace">
          {selectedAssignment ? (
            <CodeSubmissionForm
              assignmentTitle={selectedAssignment.title}
              language={selectedLanguage}
              languages={allowedLanguages}
              isSubmitting={isSubmitting}
              onLanguageChange={selectLanguage}
              onSubmit={submitCode}
            />
          ) : (
            <p className="state-message">Select an assignment.</p>
          )}

          {submissionResult && <FeedbackPanel result={submissionResult} />}
        </div>
      </div>
    </main>
  );
}
