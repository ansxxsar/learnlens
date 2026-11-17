import { useEffect, useState } from "react";
import { useSubmitStatus } from "../../hooks/useSubmitStatus";
import { fetchMyAttempts, submitAttempt } from "../../services/api";
import { useAppStore } from "../../store/useAppStore";
import type { ProgrammingLanguage } from "../../types";
import { SubmissionForm } from "../presentational/SubmissionForm";

interface SubmissionContainerProps {
  courseId: number;
  assignmentId: number;
  onSubmitted: (attemptNumber: number) => void;
  onClose: () => void;
}

export function SubmissionContainer({
  courseId,
  assignmentId,
  onSubmitted,
  onClose,
}: SubmissionContainerProps) {
  const preferredLanguage = useAppStore(
    (state) => state.student?.preferredLanguage,
  );
  const [language, setLanguage] = useState<ProgrammingLanguage>(
    preferredLanguage ?? "python",
  );
  const [code, setCode] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [savedAttempt, setSavedAttempt] = useState<number | null>(null);
  const { status, run } = useSubmitStatus();

  // Starts from the last attempt, so fixing a mistake does not mean retyping.
  useEffect(() => {
    let isCurrent = true;

    fetchMyAttempts(courseId, assignmentId)
      .then(([latest]) => {
        if (isCurrent && latest) {
          setCode(latest.code);
          if (latest.language) setLanguage(latest.language);
        }
      })
      // Without the history the student can still write a fresh attempt.
      .catch(() => undefined)
      .finally(() => {
        if (isCurrent) setIsLoading(false);
      });

    return () => {
      isCurrent = false;
    };
  }, [courseId, assignmentId]);

  const handleSubmit = async () => {
    setSavedAttempt(null);
    await run(async () => {
      const attempt = await submitAttempt(
        courseId,
        assignmentId,
        language,
        code,
      );
      setSavedAttempt(attempt.attemptNumber);
      onSubmitted(attempt.attemptNumber);
    });
  };

  if (isLoading) {
    return <p className="state-message">Loading your last attempt...</p>;
  }

  return (
    <SubmissionForm
      language={language}
      code={code}
      status={status}
      savedAttempt={savedAttempt}
      onLanguageChange={setLanguage}
      onCodeChange={(value) => {
        setCode(value);
        setSavedAttempt(null);
      }}
      onSubmit={() => void handleSubmit()}
      onCancel={onClose}
    />
  );
}
