import type { Gradebook, GradebookCell } from "../../types";
import { cellState, cellStateLabels, formatPoints } from "../../utils/grading";

interface GradebookTableProps {
  gradebook: Gradebook;
  selected: { assignmentId: number; studentId: number } | null;
  onSelect: (cell: GradebookCell) => void;
}

function CellButton({
  cell,
  maxPoints,
  isSelected,
  onSelect,
}: {
  cell: GradebookCell;
  maxPoints: number;
  isSelected: boolean;
  onSelect: () => void;
}) {
  const state = cellState(cell);
  const points =
    cell.grade !== null
      ? `${formatPoints(cell.grade.points)}/${formatPoints(maxPoints)}`
      : state === "running"
        ? "…"
        : `≈ ${formatPoints(cell.suggestedPoints ?? 0)}${cell.needsReview ? "+?" : ""}/${formatPoints(maxPoints)}`;

  return (
    <button
      type="button"
      className={`gradebook__cell gradebook__cell--${state} ${isSelected ? "gradebook__cell--selected" : ""}`}
      aria-pressed={isSelected}
      onClick={onSelect}
    >
      <span className="gradebook__points">{points}</span>
      <span className="gradebook__state">
        {cellStateLabels[state]} · #{cell.latest.attemptNumber}
      </span>
    </button>
  );
}

// Rows are students, columns are assignments. Only the teacher sees this.
export function GradebookTable({
  gradebook,
  selected,
  onSelect,
}: GradebookTableProps) {
  const cells = new Map(
    gradebook.cells.map((cell) => [
      `${cell.assignmentId}:${cell.studentId}`,
      cell,
    ]),
  );

  if (gradebook.students.length === 0) {
    return (
      <p className="state-message">
        No students are enrolled in your group yet.
      </p>
    );
  }
  if (gradebook.assignments.length === 0) {
    return (
      <p className="state-message">
        Publish an assignment to start the gradebook.
      </p>
    );
  }

  return (
    <div
      className="gradebook__scroll"
      tabIndex={0}
      aria-label="Gradebook, scrolls sideways"
    >
      <table className="gradebook">
        <thead>
          <tr>
            <th scope="col">Student</th>
            {gradebook.assignments.map((assignment) => (
              <th key={assignment.id} scope="col">
                {assignment.title}
                <span className="gradebook__max">
                  {formatPoints(assignment.maxPoints)} pts
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {gradebook.students.map((student) => (
            <tr key={student.id}>
              <th scope="row">
                {student.fullName}
                {student.sectionCode && (
                  <span className="gradebook__max">
                    Section {student.sectionCode}
                  </span>
                )}
              </th>
              {gradebook.assignments.map((assignment) => {
                const cell = cells.get(`${assignment.id}:${student.id}`);
                return (
                  <td key={assignment.id}>
                    {cell ? (
                      <CellButton
                        cell={cell}
                        maxPoints={assignment.maxPoints}
                        isSelected={
                          selected?.assignmentId === assignment.id &&
                          selected.studentId === student.id
                        }
                        onSelect={() => onSelect(cell)}
                      />
                    ) : (
                      <span className="gradebook__empty">No attempt</span>
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
