import type { Feedback, FeedbackItem, FeedbackKind } from "../../types";

interface FeedbackPanelProps {
  feedback: Feedback;
}

const sections: { kind: FeedbackKind; title: string }[] = [
  { kind: "strength", title: "What works" },
  { kind: "issue", title: "What to fix" },
  { kind: "next_step", title: "Next step" },
];

function Item({ item }: { item: FeedbackItem }) {
  return (
    <li>
      {item.message}
      {(item.lineStart !== null || item.criterionTitle) && (
        <span className="feedback-panel__refs">
          {item.lineStart !== null && <span>Line {item.lineStart}</span>}
          {item.criterionTitle && <span>Rubric: {item.criterionTitle}</span>}
        </span>
      )}
    </li>
  );
}

// Explains an attempt. It is practice guidance, never a grade.
export function FeedbackPanel({ feedback }: FeedbackPanelProps) {
  return (
    <section className="feedback-panel" aria-label="Feedback">
      <p className="feedback-panel__summary">{feedback.summary}</p>
      {sections.map(({ kind, title }) => {
        const items = feedback.items.filter((item) => item.kind === kind);
        if (items.length === 0) return null;
        return (
          <div
            key={kind}
            className={`feedback-panel__group feedback-panel__group--${kind}`}
          >
            <h5>{title}</h5>
            <ul>
              {items.map((item, index) => (
                <Item key={index} item={item} />
              ))}
            </ul>
          </div>
        );
      })}
      <p className="auth-form__hint">
        {feedback.source === "rules"
          ? "Automatic feedback based on your test results. It is not a grade."
          : "AI feedback based on your test results and the rubric. It is not a grade."}
      </p>
    </section>
  );
}
