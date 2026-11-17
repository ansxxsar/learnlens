import { useEffect, useState } from "react";
import { fetchMyCourses } from "../services/api";
import type { MyCourse } from "../types";

interface MyCoursesState {
  courses: MyCourse[];
  isLoading: boolean;
  error: string | null;
}

export function useMyCourses() {
  const [state, setState] = useState<MyCoursesState>({
    courses: [],
    isLoading: true,
    error: null,
  });

  useEffect(() => {
    // Ignores a response that arrives after the page was left.
    let isCurrent = true;

    fetchMyCourses()
      .then((courses) => {
        if (isCurrent) setState({ courses, isLoading: false, error: null });
      })
      .catch((error: unknown) => {
        if (isCurrent) {
          setState({
            courses: [],
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
  }, []);

  return state;
}
