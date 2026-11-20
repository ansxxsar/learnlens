import { useState } from "react";
import { useGradebook } from "../../hooks/useGradebook";
import type { GradebookCell } from "../../types";
import { GradebookTable } from "../presentational/GradebookTable";
import { AttemptReviewContainer } from "./AttemptReviewContainer";

interface GradebookContainerProps {
  courseId: number;
}

export function GradebookContainer({ courseId }: GradebookContainerProps) {
  const { gradebook, error, reload } = useGradebook(courseId);
  const [selected, setSelected] = useState<GradebookCell | null>(null);

  if (error) return <p className="error-message">{error}</p>;
  if (!gradebook)
    return <p className="state-message">Loading the gradebook...</p>;

  const waiting = gradebook.cells.filter(
    (cell) => !cell.grade || cell.grade.isOutdated,
  ).length;

  return (
    <div className="gradebook-page">
      <div className="section-heading">
        <span className="eyebrow">Gradebook</span>
        <h2>Student work</h2>
      </div>
      <p className="auth-form__hint">
        Points marked ≈ are suggested from the tests. Open a cell to check the
        code, then approve the grade. Students see a grade only after you
        approve it.
        {waiting > 0 && ` ${waiting} attempt(s) are waiting for your review.`}
      </p>

      <GradebookTable
        gradebook={gradebook}
        selected={selected}
        onSelect={setSelected}
      />

      {selected && (
        <AttemptReviewContainer
          // A new key starts fresh when another cell is opened.
          key={`${selected.assignmentId}:${selected.studentId}`}
          courseId={courseId}
          assignmentId={selected.assignmentId}
          submissionId={selected.latest.id}
          onApproved={reload}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  );
}
