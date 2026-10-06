import { useState } from "react";

interface CodeSubmissionFormProps {
  assignmentTitle: string;
  isSubmitting: boolean;
  onSubmit: (code: string) => Promise<void>;
}

const starterCode = `def get_grade(score):
    # Write your solution here
    pass
`;

export function CodeSubmissionForm({
  assignmentTitle,
  isSubmitting,
  onSubmit,
}: CodeSubmissionFormProps) {
  const [code, setCode] = useState(starterCode);

  const handleSubmit = async () => {
    await onSubmit(code);
  };

  return (
    <section className="submission-panel">
      <div className="submission-panel__header">
        <div>
          <span className="eyebrow">Current assignment</span>
          <h2>{assignmentTitle}</h2>
        </div>

        <span className="language-badge">Python</span>
      </div>

      <label htmlFor="code-editor">Your solution</label>

      <textarea
        id="code-editor"
        className="code-editor"
        value={code}
        onChange={(event) => setCode(event.target.value)}
        spellCheck={false}
      />

      <button
        className="primary-button"
        type="button"
        disabled={isSubmitting}
        onClick={handleSubmit}
      >
        {isSubmitting ? "Assessing solution..." : "Submit for assessment"}
      </button>
    </section>
  );
}
