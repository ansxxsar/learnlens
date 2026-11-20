import { useCallback, useEffect, useState } from "react";
import { ApiError, fetchGradebook } from "../services/api";
import type { Gradebook } from "../types";

const messageFor = (error: unknown): string => {
  if (
    error instanceof ApiError &&
    (error.status === 403 || error.status === 404)
  ) {
    return "Only the teachers of this course can open its gradebook.";
  }
  return error instanceof Error
    ? error.message
    : "Something went wrong. Please try again.";
};

export function useGradebook(courseId: number) {
  const [gradebook, setGradebook] = useState<Gradebook | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let isCurrent = true;
    fetchGradebook(courseId)
      .then((book) => {
        if (isCurrent) {
          setGradebook(book);
          setError(null);
        }
      })
      .catch((reason: unknown) => {
        if (isCurrent) setError(messageFor(reason));
      });
    return () => {
      isCurrent = false;
    };
  }, [courseId, version]);

  // Loads the sheet again, for example after a grade was approved.
  const reload = useCallback(() => setVersion((value) => value + 1), []);

  return { gradebook, error, reload };
}
