import { useEffect, useState } from "react";
import { useSubmitStatus } from "../../hooks/useSubmitStatus";
import { approveGrade, fetchAttemptReview } from "../../services/api";
import type { AttemptReview, ScoreInput } from "../../types";
import { languageOptions } from "../../data/languages";
import { errorLabels } from "../../utils/testResults";
import { FeedbackPanel } from "../presentational/FeedbackPanel";
import { GradeForm } from "../presentational/GradeForm";

interface AttemptReviewContainerProps {
  courseId: number;
  assignmentId: number;
  submissionId: number;
  onApproved: () => void;
  onClose: () => void;
}

export function AttemptReviewContainer({
  courseId,
  assignmentId,
  submissionId: initialId,
  onApproved,
  onClose,
}: AttemptReviewContainerProps) {
  const [submissionId, setSubmissionId] = useState(initialId);
  const [review, setReview] = useState<AttemptReview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { status, run, reset } = useSubmitStatus();

  useEffect(() => {
    let isCurrent = true;
    fetchAttemptReview(courseId, assignmentId, submissionId)
      .then((loaded) => {
        if (isCurrent) setReview(loaded);
      })
      .catch((reason: unknown) => {
        if (isCurrent) {
          setError(
            reason instanceof Error
              ? reason.message
              : "Could not load the attempt.",
          );
        }
      });
    return () => {
      isCurrent = false;
    };
  }, [courseId, assignmentId, submissionId]);

  const handleApprove = async (scores: ScoreInput[]) => {
    await run(async () => {
      setReview(
        await approveGrade(courseId, assignmentId, submissionId, scores),
      );
      onApproved();
    });
  };

  if (error) return <p className="error-message">{error}</p>;
  if (!review) return <p className="state-message">Loading the attempt...</p>;

  const latest = review.attempts[0];
  const languageLabel =
    languageOptions.find((option) => option.id === review.language)?.label ??
    review.language;

  return (
    <section className="account-card review-panel" aria-label="Attempt review">
      <div className="assignment-details__heading">
        <div>
          <span className="eyebrow">{review.assignment.title}</span>
          <h3>{review.student.fullName}</h3>
        </div>
        <button className="secondary-button" type="button" onClick={onClose}>
          Close
        </button>
      </div>

      <div className="review-panel__meta">
        <label>
          Attempt{" "}
          <select
            className="account-card__select review-panel__attempts"
            value={submissionId}
            onChange={(event) => {
              reset();
              setReview(null);
              setSubmissionId(Number(event.target.value));
            }}
          >
            {review.attempts.map((attempt) => (
              <option key={attempt.id} value={attempt.id}>
                #{attempt.attemptNumber} · {attempt.passedCount}/
                {attempt.testCount} tests
                {attempt.id === latest?.id ? " (latest)" : ""}
              </option>
            ))}
          </select>
        </label>
        <span>{languageLabel}</span>
        <span>
          {review.passedCount} of {review.testCount} tests passed
        </span>
      </div>
      {latest && latest.id !== review.id && (
        <p className="auth-form__hint">
          This is not the latest attempt. Grades usually go on attempt #
          {latest.attemptNumber}.
        </p>
      )}

      <pre className="test-io__value review-panel__code">{review.code}</pre>

      <ul className="detail-list">
        {review.results.map((result, index) => (
          <li key={index} className="detail-list__item">
            <div className="detail-list__header">
              <strong>{result.testName}</strong>
              <span className="detail-list__meta">
                <span
                  className={`status test-visibility--${result.visibility}`}
                >
                  {result.visibility === "hidden" ? "Hidden" : "Public"}
                </span>
                <span
                  className={`status ${result.passed ? "test-result--passed" : "test-result--failed"}`}
                >
                  {result.passed
                    ? "Passed"
                    : result.errorType
                      ? errorLabels[result.errorType]
                      : "Failed"}
                </span>
                {result.runtimeMs !== null && (
                  <span>{result.runtimeMs} ms</span>
                )}
              </span>
            </div>
            {!result.passed && (
              <div className="test-io__pair test-io__pair--three">
                <div className="test-io">
                  <span className="test-io__label">Input</span>
                  <pre className="test-io__value">
                    {result.stdinInput || "(empty)"}
                  </pre>
                </div>
                <div className="test-io">
                  <span className="test-io__label">Expected</span>
                  <pre className="test-io__value">
                    {result.expectedOutput || "(empty)"}
                  </pre>
                </div>
                <div className="test-io">
                  <span className="test-io__label">Output</span>
                  <pre className="test-io__value">
                    {result.actualOutput || result.errorOutput || "(empty)"}
                  </pre>
                </div>
              </div>
            )}
          </li>
        ))}
      </ul>

      {review.feedback && <FeedbackPanel feedback={review.feedback} />}

      <GradeForm
        key={review.id}
        criteria={review.criteria}
        isGraded={review.isGraded}
        status={status}
        onApprove={(scores) => void handleApprove(scores)}
      />
      {status.isSaved && (
        <p className="account-card__saved" role="status">
          Grade saved. The student can see it now.
        </p>
      )}
    </section>
  );
}
