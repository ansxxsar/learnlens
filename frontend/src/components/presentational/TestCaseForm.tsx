import { useId, useState } from "react";
import type { FormEvent } from "react";
import type { SubmitStatus } from "../../hooks/useSubmitStatus";
import type {
  AssignmentTestCase,
  RubricCriterion,
  TestCaseInput,
  TestVisibility,
} from "../../types";
import {
  newTestCase,
  POINTS_MAX,
  POINTS_MIN,
  TEST_IO_MAX_LENGTH,
  TIME_LIMIT_MAX_MS,
  TIME_LIMIT_MIN_MS,
} from "../../utils/rubric";
import { AuthField } from "./AuthField";

interface TestCaseFormProps {
  // Missing when a new test is being added.
  test?: AssignmentTestCase;
  criteria: RubricCriterion[];
  status: SubmitStatus;
  onSave: (input: TestCaseInput) => void;
  onCancel: () => void;
}

// Number inputs are kept as text while typing, so a cleared field stays empty
// instead of jumping to 0.
interface Fields {
  name: string;
  visibility: TestVisibility;
  stdinInput: string;
  expectedOutput: string;
  weight: string;
  timeLimitMs: string;
  criterionId: string;
}

const toFields = (test: TestCaseInput): Fields => ({
  ...test,
  weight: String(test.weight),
  timeLimitMs: String(test.timeLimitMs),
  criterionId: test.criterionId === null ? "" : String(test.criterionId),
});

export function TestCaseForm({
  test,
  criteria,
  status,
  onSave,
  onCancel,
}: TestCaseFormProps) {
  const ids = {
    visibility: useId(),
    stdin: useId(),
    expected: useId(),
    criterion: useId(),
  };
  const [fields, setFields] = useState<Fields>(toFields(test ?? newTestCase));
  const errors = status.fieldErrors;

  const set = (name: keyof Fields) => (value: string) =>
    setFields((current) => ({ ...current, [name]: value }));

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    onSave({
      ...fields,
      weight: Number(fields.weight),
      timeLimitMs: Number(fields.timeLimitMs),
      criterionId:
        fields.criterionId === "" ? null : Number(fields.criterionId),
    });
  };

  return (
    <form className="auth-form detail-form" onSubmit={handleSubmit}>
      <h4>{test ? "Edit test" : "New test"}</h4>
      {status.error && (
        <p className="error-message" role="alert">
          {status.error}
        </p>
      )}

      <AuthField
        label="Name"
        type="text"
        required
        maxLength={255}
        placeholder="Adds two small numbers"
        value={fields.name}
        errors={errors.name}
        onChange={(event) => set("name")(event.target.value)}
      />

      <div className="auth-form__field">
        <label htmlFor={ids.visibility}>Who can see it</label>
        <select
          id={ids.visibility}
          className="account-card__select"
          value={fields.visibility}
          onChange={(event) => set("visibility")(event.target.value)}
        >
          <option value="hidden">
            Hidden: only you see the input and output
          </option>
          <option value="public">Public: students see it as an example</option>
        </select>
      </div>

      <div className="detail-form__pair">
        <div className="auth-form__field">
          <label htmlFor={ids.stdin}>Input (stdin)</label>
          <textarea
            id={ids.stdin}
            className="submission-form__code"
            rows={4}
            maxLength={TEST_IO_MAX_LENGTH}
            spellCheck={false}
            value={fields.stdinInput}
            aria-invalid={Boolean(errors.stdin_input)}
            onChange={(event) => set("stdinInput")(event.target.value)}
          />
          {errors.stdin_input && (
            <span className="auth-form__field-error">
              {errors.stdin_input.join(" ")}
            </span>
          )}
        </div>
        <div className="auth-form__field">
          <label htmlFor={ids.expected}>Expected output</label>
          <textarea
            id={ids.expected}
            className="submission-form__code"
            rows={4}
            maxLength={TEST_IO_MAX_LENGTH}
            spellCheck={false}
            value={fields.expectedOutput}
            aria-invalid={Boolean(errors.expected_output)}
            onChange={(event) => set("expectedOutput")(event.target.value)}
          />
          {errors.expected_output && (
            <span className="auth-form__field-error">
              {errors.expected_output.join(" ")}
            </span>
          )}
        </div>
      </div>

      <div className="auth-form__field">
        <label htmlFor={ids.criterion}>Counts toward</label>
        <select
          id={ids.criterion}
          className="account-card__select"
          value={fields.criterionId}
          aria-invalid={Boolean(errors.criterion)}
          onChange={(event) => set("criterionId")(event.target.value)}
        >
          <option value="">No rubric criterion</option>
          {criteria.map((criterion) => (
            <option key={criterion.id} value={criterion.id}>
              {criterion.title}
            </option>
          ))}
        </select>
        {errors.criterion && (
          <span className="auth-form__field-error">
            {errors.criterion.join(" ")}
          </span>
        )}
      </div>

      <div className="detail-form__pair">
        <AuthField
          label="Weight"
          type="number"
          required
          min={POINTS_MIN}
          max={POINTS_MAX}
          step="0.01"
          inputMode="decimal"
          value={fields.weight}
          errors={errors.weight}
          onChange={(event) => set("weight")(event.target.value)}
        />
        <AuthField
          label="Time limit (ms)"
          type="number"
          required
          min={TIME_LIMIT_MIN_MS}
          max={TIME_LIMIT_MAX_MS}
          step="100"
          inputMode="numeric"
          value={fields.timeLimitMs}
          errors={errors.time_limit_ms}
          onChange={(event) => set("timeLimitMs")(event.target.value)}
        />
      </div>

      <div className="account-card__row">
        <button
          className="primary-button"
          type="submit"
          disabled={status.isSaving}
        >
          {test ? "Save test" : "Add test"}
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
