import { useState } from "react";
import { useCourse } from "../../hooks/useCourse";
import { useSubmitStatus } from "../../hooks/useSubmitStatus";
import {
  createAssignment,
  deleteAssignment,
  updateAssignment,
} from "../../services/api";
import type { AssignmentInput, CourseAssignment } from "../../types";
import type { StatusAction } from "../../utils/assignments";
import { AssignmentForm } from "../presentational/AssignmentForm";
import { CourseAssignmentItem } from "../presentational/CourseAssignmentItem";
import { CourseCard } from "../presentational/CourseCard";
import { SubmissionContainer } from "./SubmissionContainer";

interface CourseContainerProps {
  courseId: number;
}

// "new" while creating, an assignment while editing it, null when closed.
type FormTarget = "new" | CourseAssignment | null;

export function CourseContainer({ courseId }: CourseContainerProps) {
  const {
    course,
    assignments,
    isLoading,
    error,
    saveAssignment,
    removeAssignment,
  } = useCourse(courseId);
  const {
    status: formStatus,
    run: runForm,
    reset: resetForm,
  } = useSubmitStatus();
  const { status: actionStatus, run: runAction } = useSubmitStatus();
  const [formTarget, setFormTarget] = useState<FormTarget>(null);
  const [busyId, setBusyId] = useState<number | null>(null);
  // The assignment whose submission form a student has open.
  const [submittingId, setSubmittingId] = useState<number | null>(null);

  if (isLoading) {
    return <p className="state-message">Loading the course...</p>;
  }
  if (error || !course) {
    return <p className="error-message">{error}</p>;
  }

  // The page only offers the controls; the API decides who may use them.
  const canManage = course.role === "instructor";

  const openForm = (target: FormTarget) => {
    resetForm();
    setFormTarget(target);
  };

  const handleSave = async (input: AssignmentInput, publish: boolean) => {
    const target = formTarget;
    const isSaved = await runForm(async () => {
      saveAssignment(
        target === "new" || target === null
          ? await createAssignment(courseId, input, publish)
          : await updateAssignment(courseId, target.id, input),
      );
    });
    if (isSaved) setFormTarget(null);
  };

  const handleAction = async (
    assignment: CourseAssignment,
    action: StatusAction,
  ) => {
    if (
      action.isDanger &&
      !window.confirm(`${action.label} "${assignment.title}"?`)
    ) {
      return;
    }

    setBusyId(assignment.id);
    await runAction(async () => {
      if (action.status === null) {
        await deleteAssignment(courseId, assignment.id);
        removeAssignment(assignment.id);
      } else {
        saveAssignment(
          await updateAssignment(courseId, assignment.id, {
            status: action.status,
          }),
        );
      }
    });
    setBusyId(null);
  };

  return (
    <div className="course-page">
      <CourseCard course={course} />

      <section
        className="course-page__assignments"
        aria-labelledby="assignments-title"
      >
        <div className="course-page__heading">
          <div className="section-heading">
            <span className="eyebrow">{course.code}</span>
            <h2 id="assignments-title">Assignments</h2>
          </div>
          {canManage && formTarget === null && (
            <button
              className="primary-button"
              type="button"
              onClick={() => openForm("new")}
            >
              New assignment
            </button>
          )}
        </div>

        {formTarget !== null && (
          <AssignmentForm
            // A new key resets the fields when switching between assignments.
            key={formTarget === "new" ? "new" : formTarget.id}
            assignment={formTarget === "new" ? undefined : formTarget}
            status={formStatus}
            onSave={(input, publish) => void handleSave(input, publish)}
            onCancel={() => openForm(null)}
          />
        )}

        {actionStatus.error && (
          <p className="error-message" role="alert">
            {actionStatus.error}
          </p>
        )}

        {assignments.length === 0 ? (
          <p className="state-message">
            {canManage
              ? "No assignments yet. Create the first one for your students."
              : "Your teacher hasn't published any assignments yet."}
          </p>
        ) : (
          assignments.map((assignment) => (
            <CourseAssignmentItem
              key={assignment.id}
              assignment={assignment}
              canManage={canManage}
              isBusy={busyId === assignment.id}
              onEdit={() => openForm(assignment)}
              onAction={(action) => void handleAction(assignment, action)}
              isSubmitting={submittingId === assignment.id}
              onStartSubmission={() => setSubmittingId(assignment.id)}
            >
              {submittingId === assignment.id && (
                <SubmissionContainer
                  courseId={courseId}
                  assignmentId={assignment.id}
                  onSubmitted={(attemptNumber) =>
                    saveAssignment({
                      ...assignment,
                      attemptCount: attemptNumber,
                    })
                  }
                  onClose={() => setSubmittingId(null)}
                />
              )}
            </CourseAssignmentItem>
          ))
        )}
      </section>
    </div>
  );
}
