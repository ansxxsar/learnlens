import { useState } from "react";
import type { FormEvent } from "react";
import type { SubmitStatus } from "../../hooks/useSubmitStatus";
import type { ReviewCriterion, ScoreInput } from "../../types";
import { formatPoints } from "../../utils/grading";

interface GradeFormProps {
  criteria: ReviewCriterion[];
  isGraded: boolean;
  status: SubmitStatus;
  onApprove: (scores: ScoreInput[]) => void;
}

interface Row {
  points: string;
  reason: string;
}

const initialRow = (criterion: ReviewCriterion): Row => ({
  points: String(criterion.finalPoints ?? criterion.suggestedPoints ?? ""),
  reason: criterion.overrideReason ?? "",
});

// A changed suggestion needs a reason; the server checks this too.
const isOverride = (criterion: ReviewCriterion, row: Row): boolean =>
  criterion.suggestedPoints !== null &&
  row.points !== "" &&
  Number(row.points) !== criterion.suggestedPoints;

export function GradeForm({
  criteria,
  isGraded,
  status,
  onApprove,
}: GradeFormProps) {
  const [rows, setRows] = useState<Record<number, Row>>(() =>
    Object.fromEntries(
      criteria.map((criterion) => [criterion.id, initialRow(criterion)]),
    ),
  );

  const update = (id: number, change: Partial<Row>) =>
    setRows((current) => ({ ...current, [id]: { ...current[id], ...change } }));

  const total = criteria.reduce(
    (sum, criterion) => sum + Number(rows[criterion.id].points || 0),
    0,
  );
  const maxTotal = criteria.reduce(
    (sum, criterion) => sum + criterion.maxPoints,
    0,
  );

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    onApprove(
      criteria.map((criterion) => ({
        criterion: criterion.id,
        points:
          rows[criterion.id].points === ""
            ? null
            : Number(rows[criterion.id].points),
        reason: rows[criterion.id].reason,
      })),
    );
  };

  if (criteria.length === 0) {
    return (
      <p className="state-message">
        Add a rubric to this assignment before grading it.
      </p>
    );
  }

  return (
    <form className="auth-form grade-form" onSubmit={handleSubmit}>
      <h4>Grade</h4>
      {status.error && (
        <p className="error-message" role="alert">
          {status.error}
        </p>
      )}

      {criteria.map((criterion) => {
        const row = rows[criterion.id];
        const fieldError =
          status.fieldErrors[`score_${criterion.id}`]?.join(" ");
        return (
          <div key={criterion.id} className="grade-form__row">
            <div className="grade-form__criterion">
              <label htmlFor={`points-${criterion.id}`}>
                <strong>{criterion.title}</strong>
              </label>
              <span className="auth-form__hint">
                {criterion.isTested
                  ? `Suggested from tests: ${formatPoints(criterion.suggestedPoints ?? 0)}`
                  : "Tests cannot check this. Enter the points yourself."}
              </span>
            </div>
            <div className="grade-form__points">
              <input
                id={`points-${criterion.id}`}
                type="number"
                min={0}
                max={criterion.maxPoints}
                step="0.01"
                inputMode="decimal"
                required={!criterion.isTested}
                value={row.points}
                aria-invalid={Boolean(fieldError)}
                onChange={(event) =>
                  update(criterion.id, { points: event.target.value })
                }
              />
              <span>/ {formatPoints(criterion.maxPoints)}</span>
            </div>
            {isOverride(criterion, row) && (
              <input
                className="grade-form__reason"
                type="text"
                required
                maxLength={2000}
                placeholder="Why do you change the suggested points?"
                aria-label={`Reason for changing ${criterion.title}`}
                value={row.reason}
                onChange={(event) =>
                  update(criterion.id, { reason: event.target.value })
                }
              />
            )}
            {fieldError && (
              <span className="auth-form__field-error">{fieldError}</span>
            )}
          </div>
        );
      })}

      <div className="grade-form__footer">
        <strong>
          Total: {formatPoints(total)} / {formatPoints(maxTotal)}
        </strong>
        <button
          className="primary-button"
          type="submit"
          disabled={status.isSaving}
        >
          {status.isSaving
            ? "Saving..."
            : isGraded
              ? "Update grade"
              : "Approve grade"}
        </button>
      </div>
      <p className="auth-form__hint">
        The student sees the grade only after you approve it.
      </p>
    </form>
  );
}
