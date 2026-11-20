import { useId, useState } from "react";
import type { FormEvent } from "react";
import type { SubmitStatus } from "../../hooks/useSubmitStatus";
import type { RubricCriterion, RubricCriterionInput } from "../../types";
import { POINTS_MAX, POINTS_MIN } from "../../utils/rubric";
import { AuthField } from "./AuthField";

interface RubricCriterionFormProps {
  // Missing when a new criterion is being added.
  criterion?: RubricCriterion;
  status: SubmitStatus;
  onSave: (input: RubricCriterionInput) => void;
  onCancel: () => void;
}

export function RubricCriterionForm({
  criterion,
  status,
  onSave,
  onCancel,
}: RubricCriterionFormProps) {
  const descriptionId = useId();
  const [title, setTitle] = useState(criterion?.title ?? "");
  const [description, setDescription] = useState(criterion?.description ?? "");
  const [maxPoints, setMaxPoints] = useState(
    criterion ? String(criterion.maxPoints) : "",
  );

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    onSave({ title, description, maxPoints: Number(maxPoints) });
  };

  return (
    <form className="auth-form detail-form" onSubmit={handleSubmit}>
      <h4>{criterion ? "Edit criterion" : "New criterion"}</h4>
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
        placeholder="Correct output"
        value={title}
        errors={status.fieldErrors.title}
        onChange={(event) => setTitle(event.target.value)}
      />

      <div className="auth-form__field">
        <label htmlFor={descriptionId}>What earns the points (optional)</label>
        <textarea
          id={descriptionId}
          className="assignment-form__textarea"
          rows={3}
          maxLength={2000}
          value={description}
          aria-invalid={Boolean(status.fieldErrors.description)}
          onChange={(event) => setDescription(event.target.value)}
        />
        {status.fieldErrors.description && (
          <span className="auth-form__field-error">
            {status.fieldErrors.description.join(" ")}
          </span>
        )}
      </div>

      <AuthField
        label="Points"
        type="number"
        required
        min={POINTS_MIN}
        max={POINTS_MAX}
        step="0.01"
        inputMode="decimal"
        value={maxPoints}
        errors={status.fieldErrors.max_points}
        onChange={(event) => setMaxPoints(event.target.value)}
      />

      <div className="account-card__row">
        <button
          className="primary-button"
          type="submit"
          disabled={status.isSaving}
        >
          {criterion ? "Save criterion" : "Add criterion"}
        </button>
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
  );
}
