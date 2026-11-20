import { useCallback, useEffect, useState } from "react";
import { fetchRubric } from "../services/api";
import type { PublicTestCase, RubricCriterion } from "../types";

interface DetailsState<T> {
  rubric: RubricCriterion[];
  tests: T[];
  isLoading: boolean;
  error: string | null;
}

type LoadTests<T> = (courseId: number, assignmentId: number) => Promise<T[]>;

const upsert = <T extends { id: number }>(items: T[], saved: T): T[] =>
  items.some((item) => item.id === saved.id)
    ? items.map((item) => (item.id === saved.id ? saved : item))
    : [...items, saved];

const byPosition = (a: RubricCriterion, b: RubricCriterion): number =>
  a.position - b.position || a.id - b.id;

// Loads an assignment's rubric and tests once per mount. `loadTests` decides
// which tests: every test for instructors, public ones for students. It must
// be a stable function, such as one imported from services/api.
export function useAssignmentDetails<T extends PublicTestCase>(
  courseId: number,
  assignmentId: number,
  loadTests: LoadTests<T>,
) {
  const [state, setState] = useState<DetailsState<T>>({
    rubric: [],
    tests: [],
    isLoading: true,
    error: null,
  });

  useEffect(() => {
    let isCurrent = true;

    Promise.all([
      fetchRubric(courseId, assignmentId),
      loadTests(courseId, assignmentId),
    ])
      .then(([rubric, tests]) => {
        if (isCurrent) setState({ rubric, tests, isLoading: false, error: null });
      })
      .catch((error: unknown) => {
        if (isCurrent) {
          setState({
            rubric: [],
            tests: [],
            isLoading: false,
            error:
              error instanceof Error
                ? error.message
                : "Something went wrong. Please try again.",
          });
        }
      });

    return () => {
      isCurrent = false;
    };
  }, [courseId, assignmentId, loadTests]);

  // These apply changes the server already accepted, without reloading.
  const saveCriterion = useCallback((saved: RubricCriterion) => {
    setState((current) => ({
      ...current,
      rubric: upsert(current.rubric, saved).sort(byPosition),
    }));
  }, []);

  const removeCriterion = useCallback((criterionId: number) => {
    setState((current) => ({
      ...current,
      rubric: current.rubric.filter((item) => item.id !== criterionId),
      // The server unlinks the criterion's tests; mirror that here.
      tests: current.tests.map((test) =>
        "criterionId" in test && test.criterionId === criterionId
          ? { ...test, criterionId: null }
          : test,
      ),
    }));
  }, []);

  const saveTest = useCallback((saved: T) => {
    setState((current) => ({ ...current, tests: upsert(current.tests, saved) }));
  }, []);

  const removeTest = useCallback((testId: number) => {
    setState((current) => ({
      ...current,
      tests: current.tests.filter((item) => item.id !== testId),
    }));
  }, []);

  return { ...state, saveCriterion, removeCriterion, saveTest, removeTest };
}
