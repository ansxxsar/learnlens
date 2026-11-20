import { useState } from "react";
import { useAssignmentDetails } from "../../hooks/useAssignmentDetails";
import { useSubmitStatus } from "../../hooks/useSubmitStatus";
import {
  createCriterion,
  createTestCase,
  deleteCriterion,
  deleteTestCase,
  fetchPublicTestCases,
  fetchTestCases,
  updateCriterion,
  updateTestCase,
} from "../../services/api";
import type {
  AssignmentTestCase,
  RubricCriterion,
  RubricCriterionInput,
  TestCaseInput,
} from "../../types";
import { RubricCriterionForm } from "../presentational/RubricCriterionForm";
import { RubricList } from "../presentational/RubricList";
import { TestCaseForm } from "../presentational/TestCaseForm";
import { TestCaseList } from "../presentational/TestCaseList";

interface AssignmentDetailsContainerProps {
  courseId: number;
  assignmentId: number;
  canManage: boolean;
  // Archived assignments are frozen; instructors can still read them.
  isReadOnly: boolean;
}

export function AssignmentDetailsContainer({
  canManage,
  ...props
}: AssignmentDetailsContainerProps) {
  return canManage ? (
    <InstructorDetails {...props} />
  ) : (
    <StudentDetails courseId={props.courseId} assignmentId={props.assignmentId} />
  );
}

// Students: the rubric and the public tests as examples. The API never sends
// hidden tests to them, so there is nothing to filter here.
function StudentDetails({
  courseId,
  assignmentId,
}: {
  courseId: number;
  assignmentId: number;
}) {
  const { rubric, tests, isLoading, error } = useAssignmentDetails(
    courseId,
    assignmentId,
    fetchPublicTestCases,
  );

  if (isLoading) return <p className="state-message">Loading...</p>;
  if (error) return <p className="error-message">{error}</p>;

  return (
    <div className="assignment-details">
      <section>
        <h4>How it is graded</h4>
        <RubricList
          criteria={rubric}
          emptyMessage="Your teacher hasn't added a rubric yet."
        />
      </section>
      <section>
        <h4>Examples</h4>
        <TestCaseList
          tests={tests}
          emptyMessage="No examples for this assignment."
        />
        {tests.length > 0 && (
          <p className="auth-form__hint">
            Your code reads the input and should print exactly the expected
            output. Your teacher may also check it with tests not shown here.
          </p>
        )}
      </section>
    </div>
  );
}

type Target<T> = "new" | T | null;

function InstructorDetails({
  courseId,
  assignmentId,
  isReadOnly,
}: Omit<AssignmentDetailsContainerProps, "canManage">) {
  const details = useAssignmentDetails(courseId, assignmentId, fetchTestCases);
  const criterionForm = useSubmitStatus();
  const testForm = useSubmitStatus();
  const deletion = useSubmitStatus();
  const [criterionTarget, setCriterionTarget] =
    useState<Target<RubricCriterion>>(null);
  const [testTarget, setTestTarget] = useState<Target<AssignmentTestCase>>(null);
  const [busyKey, setBusyKey] = useState<string | null>(null);

  if (details.isLoading) return <p className="state-message">Loading...</p>;
  if (details.error) return <p className="error-message">{details.error}</p>;

  const criterionTitle = (id: number | null) =>
    details.rubric.find((criterion) => criterion.id === id)?.title;

  const openCriterion = (target: Target<RubricCriterion>) => {
    criterionForm.reset();
    setCriterionTarget(target);
  };

  const openTest = (target: Target<AssignmentTestCase>) => {
    testForm.reset();
    setTestTarget(target);
  };

  const saveCriterion = async (input: RubricCriterionInput) => {
    const target = criterionTarget;
    const isSaved = await criterionForm.run(async () => {
      details.saveCriterion(
        target === "new" || target === null
          ? await createCriterion(courseId, assignmentId, input)
          : await updateCriterion(courseId, assignmentId, target.id, input),
      );
    });
    if (isSaved) setCriterionTarget(null);
  };

  const saveTest = async (input: TestCaseInput) => {
    const target = testTarget;
    const isSaved = await testForm.run(async () => {
      details.saveTest(
        target === "new" || target === null
          ? await createTestCase(courseId, assignmentId, input)
          : await updateTestCase(courseId, assignmentId, target.id, input),
      );
    });
    if (isSaved) setTestTarget(null);
  };

  const remove = async (
    key: string,
    label: string,
    action: () => Promise<void>,
  ) => {
    if (!window.confirm(`Delete "${label}"?`)) return;
    setBusyKey(key);
    await deletion.run(action);
    setBusyKey(null);
  };

  const rowActions = (key: string, onEdit: () => void, onDelete: () => void) =>
    !isReadOnly && (
      <div className="course-assignment__actions">
        <button
          className="secondary-button"
          type="button"
          disabled={busyKey === key}
          onClick={onEdit}
        >
          Edit
        </button>
        <button
          className="secondary-button secondary-button--danger"
          type="button"
          disabled={busyKey === key}
          onClick={onDelete}
        >
          Delete
        </button>
      </div>
    );

  const hiddenCount = details.tests.filter(
    (test) => test.visibility === "hidden",
  ).length;

  return (
    <div className="assignment-details">
      {deletion.status.error && (
        <p className="error-message" role="alert">
          {deletion.status.error}
        </p>
      )}

      <section>
        <div className="assignment-details__heading">
          <h4>Rubric</h4>
          {!isReadOnly && criterionTarget === null && (
            <button
              className="secondary-button"
              type="button"
              onClick={() => openCriterion("new")}
            >
              Add criterion
            </button>
          )}
        </div>
        <RubricList
          criteria={details.rubric}
          emptyMessage="No criteria yet. Students see the rubric, so they know how their work is judged."
          renderActions={(criterion) =>
            rowActions(
              `criterion-${criterion.id}`,
              () => openCriterion(criterion),
              () =>
                void remove(`criterion-${criterion.id}`, criterion.title, async () => {
                  await deleteCriterion(courseId, assignmentId, criterion.id);
                  details.removeCriterion(criterion.id);
                }),
            )
          }
        />
        {criterionTarget !== null && (
          <RubricCriterionForm
            key={criterionTarget === "new" ? "new" : criterionTarget.id}
            criterion={criterionTarget === "new" ? undefined : criterionTarget}
            status={criterionForm.status}
            onSave={(input) => void saveCriterion(input)}
            onCancel={() => openCriterion(null)}
          />
        )}
      </section>

      <section>
        <div className="assignment-details__heading">
          <h4>Tests</h4>
          {!isReadOnly && testTarget === null && (
            <button
              className="secondary-button"
              type="button"
              onClick={() => openTest("new")}
            >
              Add test
            </button>
          )}
        </div>
        {details.tests.length > 0 && (
          <p className="auth-form__hint">
            {details.tests.length - hiddenCount} public · {hiddenCount} hidden.
            Students only see public tests.
          </p>
        )}
        <TestCaseList
          tests={details.tests}
          emptyMessage="No tests yet. Add at least one so submissions can be checked automatically."
          renderMeta={(test) => (
            <span className="detail-list__meta">
              <span className={`status test-visibility--${test.visibility}`}>
                {test.visibility === "hidden" ? "Hidden" : "Public"}
              </span>
              {criterionTitle(test.criterionId) && (
                <span>→ {criterionTitle(test.criterionId)}</span>
              )}
              <span>
                weight {test.weight} · {test.timeLimitMs} ms
              </span>
            </span>
          )}
          renderActions={(test) =>
            rowActions(
              `test-${test.id}`,
              () => openTest(test),
              () =>
                void remove(`test-${test.id}`, test.name, async () => {
                  await deleteTestCase(courseId, assignmentId, test.id);
                  details.removeTest(test.id);
                }),
            )
          }
        />
        {testTarget !== null && (
          <TestCaseForm
            key={testTarget === "new" ? "new" : testTarget.id}
            test={testTarget === "new" ? undefined : testTarget}
            criteria={details.rubric}
            status={testForm.status}
            onSave={(input) => void saveTest(input)}
            onCancel={() => openTest(null)}
          />
        )}
      </section>
    </div>
  );
}
