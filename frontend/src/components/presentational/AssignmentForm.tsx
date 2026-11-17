import { useId, useState } from "react";
import type { FormEvent } from "react";
import type { SubmitStatus } from "../../hooks/useSubmitStatus";
import type {
  AssignmentInput,
  CourseAssignment,
  FeedbackDepth,
} from "../../types";
import {
  feedbackDepthOptions,
  fromLocalInputValue,
  toLocalInputValue,
} from "../../utils/assignments";
import { AuthField } from "./AuthField";

interface AssignmentFormProps {
  // Missing when a new assignment is being created.
  assignment?: CourseAssignment;
  status: SubmitStatus;
  onSave: (input: AssignmentInput, publish: boolean) => void;
  onCancel: () => void;
}

export function AssignmentForm({
  assignment,
  status,
  onSave,
  onCancel,
}: AssignmentFormProps) {
  const instructionsId = useId();
  const depthId = useId();
  const [title, setTitle] = useState(assignment?.title ?? "");
  const [instructions, setInstructions] = useState(
    assignment?.instructions ?? "",
  );
  const [dueAt, setDueAt] = useState(
    assignment ? toLocalInputValue(assignment.dueAt) : "",
  );
  const [feedbackDepth, setFeedbackDepth] = useState<FeedbackDepth>(
    assignment?.feedbackDepth ?? "guided",
  );
  const isNew = assignment === undefined;

  const save = (publish: boolean) => {
    onSave(
      {
        title,
        instructions,
        dueAt: fromLocalInputValue(dueAt),
        feedbackDepth,
      },
      publish,
    );
  };

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    save(false);
  };

  return (
    <section className="account-card assignment-form">
      <h2>{isNew ? "New assignment" : "Edit assignment"}</h2>
      <form className="auth-form" onSubmit={handleSubmit}>
        {status.error && (
          <p className="error-message" role="alert">
            {status.error}
          </p>
        )}

        <AuthField
          label="Title"
          type="text"
          required
          maxLength={255}
          value={title}
          errors={status.fieldErrors.title}
          onChange={(event) => setTitle(event.target.value)}
        />

        <div className="auth-form__field">
          <label htmlFor={instructionsId}>Instructions</label>
          <textarea
            id={instructionsId}
            className="assignment-form__textarea"
            required
            rows={6}
            maxLength={20000}
            value={instructions}
            aria-invalid={Boolean(status.fieldErrors.instructions)}
            onChange={(event) => setInstructions(event.target.value)}
          />
          {status.fieldErrors.instructions && (
            <span className="auth-form__field-error">
              {status.fieldErrors.instructions.join(" ")}
            </span>
          )}
        </div>

        <AuthField
          label="Deadline"
          type="datetime-local"
          required
          value={dueAt}
          errors={status.fieldErrors.due_at}
          onChange={(event) => setDueAt(event.target.value)}
        />

        <div className="auth-form__field">
          <label htmlFor={depthId}>Feedback depth</label>
          <select
            id={depthId}
            className="account-card__select"
            value={feedbackDepth}
            onChange={(event) =>
              setFeedbackDepth(event.target.value as FeedbackDepth)
            }
          >
            {feedbackDepthOptions.map((option) => (
              <option key={option.id} value={option.id}>
                {option.label}
              </option>
            ))}
          </select>
          <span className="auth-form__hint">
            How much the feedback explains to students after they submit.
          </span>
        </div>

        <div className="account-card__row">
          {isNew ? (
            <>
              <button
                className="primary-button"
                type="button"
                disabled={status.isSaving}
                onClick={(event) => {
                  // Runs the browser's required-field checks first.
                  if (event.currentTarget.form?.reportValidity()) save(true);
                }}
              >
                Publish now
              </button>
              <button
                className="secondary-button"
                type="submit"
                disabled={status.isSaving}
              >
                Save as draft
              </button>
            </>
          ) : (
            <button
              className="primary-button"
              type="submit"
              disabled={status.isSaving}
            >
              Save changes
            </button>
          )}
          <button
            className="secondary-button"
            type="button"
            disabled={status.isSaving}
            onClick={onCancel}
          >
            Cancel
          </button>
        </div>
      </form>
    </section>
  );
}
