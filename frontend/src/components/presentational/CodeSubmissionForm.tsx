import { useState } from "react";
import { starterCode } from "../../data/languages";
import type { LanguageOption, ProgrammingLanguage } from "../../types";

interface CodeSubmissionFormProps {
  assignmentTitle: string;
  language: ProgrammingLanguage;
  languages: LanguageOption[];
  isSubmitting: boolean;
  onLanguageChange: (language: ProgrammingLanguage) => void;
  onSubmit: (code: string) => Promise<void>;
}

export function CodeSubmissionForm({
  assignmentTitle,
  language,
  languages,
  isSubmitting,
  onLanguageChange,
  onSubmit,
}: CodeSubmissionFormProps) {
  // One draft per language so switching languages never discards typed code.
  const [drafts, setDrafts] =
    useState<Record<ProgrammingLanguage, string>>(starterCode);
  const code = drafts[language];

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
        onChange={(event) =>
          setDrafts((current) => ({
            ...current,
            [language]: event.target.value,
          }))
        }
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
