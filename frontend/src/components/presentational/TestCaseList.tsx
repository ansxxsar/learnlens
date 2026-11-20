import type { ReactNode } from "react";
import type { PublicTestCase } from "../../types";

interface TestCaseListProps<T extends PublicTestCase> {
  tests: T[];
  emptyMessage: string;
  // Instructors only: badges such as "Hidden", and edit/delete buttons.
  renderMeta?: (test: T) => ReactNode;
  renderActions?: (test: T) => ReactNode;
}

// Shows the text exactly, with its spaces and line breaks; an empty value
// is labelled so it is not mistaken for a missing one.
function IoBlock({ label, value }: { label: string; value: string }) {
  return (
    <div className="test-io">
      <span className="test-io__label">{label}</span>
      {value ? (
        <pre className="test-io__value">{value}</pre>
      ) : (
        <span className="test-io__empty">(empty)</span>
      )}
    </div>
  );
}

export function TestCaseList<T extends PublicTestCase>({
  tests,
  emptyMessage,
  renderMeta,
  renderActions,
}: TestCaseListProps<T>) {
  if (tests.length === 0) {
    return <p className="state-message">{emptyMessage}</p>;
  }

  return (
    <ul className="detail-list">
      {tests.map((test) => (
        <li key={test.id} className="detail-list__item">
          <div className="detail-list__header">
            <strong>{test.name}</strong>
            {renderMeta?.(test)}
          </div>
          <div className="test-io__pair">
            <IoBlock label="Input" value={test.stdinInput} />
            <IoBlock label="Expected output" value={test.expectedOutput} />
          </div>
          {renderActions?.(test)}
        </li>
      ))}
    </ul>
  );
}
