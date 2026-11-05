import type { LanguageOption, ProgrammingLanguage } from "../../types";

interface CodeSubmissionFormProps {
  assignmentTitle: string;
  language: ProgrammingLanguage;
  code: string;
  languages: LanguageOption[];
  isSubmitting: boolean;
  onLanguageChange: (language: ProgrammingLanguage) => void;
  onCodeChange: (code: string) => void;
  onSubmit: (code: string) => Promise<void>;
}

export function CodeSubmissionForm({
  assignmentTitle,
  language,
  code,
  languages,
  isSubmitting,
  onLanguageChange,
  onCodeChange,
  onSubmit,
}: CodeSubmissionFormProps) {
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

        <div className="language-picker">
          <label htmlFor="language-select">Language</label>
          <select
            id="language-select"
            className="language-select"
            value={language}
            disabled={isSubmitting || languages.length < 2}
            onChange={(event) =>
              onLanguageChange(event.target.value as ProgrammingLanguage)
            }
          >
            {languages.map((option) => (
              <option key={option.id} value={option.id}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <label htmlFor="code-editor">Your solution</label>

      <textarea
        id="code-editor"
        className="code-editor"
        value={code}
        onChange={(event) => onCodeChange(event.target.value)}
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
