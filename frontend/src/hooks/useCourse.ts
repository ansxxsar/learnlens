import { useCallback, useEffect, useState } from "react";
import { ApiError, fetchCourse, fetchCourseAssignments } from "../services/api";
import type { CourseAssignment, MyCourse } from "../types";

interface CourseState {
  course: MyCourse | null;
  assignments: CourseAssignment[];
  isLoading: boolean;
  error: string | null;
}

const messageFor = (error: unknown): string => {
  if (
    error instanceof ApiError &&
    (error.status === 403 || error.status === 404)
  ) {
    return "This course doesn't exist or you are not enrolled in it.";
  }
  return error instanceof Error
    ? error.message
    : "Something went wrong. Please try again.";
};

// Loads once per mount. Give the component a key of the course id so that
// moving to another course starts from a fresh loading state.
export function useCourse(courseId: number) {
  const [state, setState] = useState<CourseState>({
    course: null,
    assignments: [],
    isLoading: true,
    error: null,
  });

  useEffect(() => {
    // Ignores a response that arrives after the page was left.
    let isCurrent = true;

    Promise.all([fetchCourse(courseId), fetchCourseAssignments(courseId)])
      .then(([course, assignments]) => {
        if (isCurrent) {
          setState({ course, assignments, isLoading: false, error: null });
        }
      })
      .catch((error: unknown) => {
        if (isCurrent) {
          setState({
            course: null,
            assignments: [],
            isLoading: false,
            error: messageFor(error),
          });
        }
      });

    return () => {
      isCurrent = false;
    };
  }, [courseId]);

  // Applies a change the server already accepted, without reloading the list.
  const saveAssignment = useCallback((saved: CourseAssignment) => {
    setState((current) => {
      const exists = current.assignments.some((item) => item.id === saved.id);
      const assignments = exists
        ? current.assignments.map((item) =>
            item.id === saved.id ? saved : item,
          )
        : [...current.assignments, saved];
      // Same order as the API. Dates are compared as times, because the
      // strings may carry different time zone offsets.
      assignments.sort(
        (a, b) => Date.parse(a.dueAt) - Date.parse(b.dueAt) || a.id - b.id,
      );
      return { ...current, assignments };
    });
  }, []);

  const removeAssignment = useCallback((assignmentId: number) => {
    setState((current) => ({
      ...current,
      assignments: current.assignments.filter(
        (item) => item.id !== assignmentId,
      ),
    }));
  }, []);

  return { ...state, saveAssignment, removeAssignment };
}
