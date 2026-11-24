import { useEffect, useState } from "react";
import { useSubmitStatus } from "../../hooks/useSubmitStatus";
import { fetchMyAttempts, submitAttempt } from "../../services/api";
import { useAppStore } from "../../store/useAppStore";
import type { ProgrammingLanguage, Submission } from "../../types";
import { isPending } from "../../utils/testResults";
import { AttemptResults } from "../presentational/AttemptResults";
import { SubmissionForm } from "../presentational/SubmissionForm";

// How often a running attempt is checked, and when the page stops asking.
// The attempt keeps running on the server either way.
const POLL_INTERVAL_MS = 2_000;
const POLL_GIVE_UP_MS = 3 * 60_000;

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
  // The newest attempt, whose results are shown under the form.
  const [latest, setLatest] = useState<Submission | null>(null);
  const [pollStartedAt, setPollStartedAt] = useState(() => Date.now());
  const { status, run } = useSubmitStatus();

  // Starts from the last attempt, so fixing a mistake does not mean retyping.
  useEffect(() => {
    let isCurrent = true;

    fetchMyAttempts(courseId, assignmentId)
      .then(([latest]) => {
        if (isCurrent && latest) {
          setCode(latest.code);
          if (latest.language) setLanguage(latest.language);
          setLatest(latest);
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

  const latestId = latest?.id;
  const latestIsPending = latest !== null && isPending(latest);

  // Asks for news until the newest attempt has finished running.
  useEffect(() => {
    if (!latestIsPending) return;
    let isCurrent = true;

    const timer = window.setInterval(() => {
      if (Date.now() - pollStartedAt > POLL_GIVE_UP_MS) {
        window.clearInterval(timer);
        return;
      }
      fetchMyAttempts(courseId, assignmentId)
        .then((attempts) => {
          const fresh = attempts.find((attempt) => attempt.id === latestId);
          if (isCurrent && fresh) setLatest(fresh);
        })
        // A failed check is tried again on the next tick.
        .catch(() => undefined);
    }, POLL_INTERVAL_MS);

    return () => {
      isCurrent = false;
      window.clearInterval(timer);
    };
  }, [courseId, assignmentId, latestId, latestIsPending, pollStartedAt]);

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
      setLatest(attempt);
      setPollStartedAt(Date.now());
      onSubmitted(attempt.attemptNumber);
    });
  };

  if (isLoading) {
    return <p className="state-message">Loading your last attempt...</p>;
  }

  return (
    <>
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
      {latest && <AttemptResults attempt={latest} />}
    </>
  );
}
