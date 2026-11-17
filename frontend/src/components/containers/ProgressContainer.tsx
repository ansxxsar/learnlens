import { useEffect } from "react";
import { useAppStore } from "../../store/useAppStore";
import { DailyProgressPanel } from "../presentational/DailyProgressPanel";

export function ProgressContainer() {
  const progress = useAppStore((state) => state.progress);
  const error = useAppStore((state) => state.error);
  const loadProgress = useAppStore((state) => state.loadProgress);

  // Reloaded on every visit, so a task submitted in a course shows as done.
  useEffect(() => {
    void loadProgress();
  }, [loadProgress]);

  if (error) {
    return <p className="error-message">{error}</p>;
  }
  if (!progress) {
    return <p className="state-message">Loading your progress...</p>;
  }
  return <DailyProgressPanel progress={progress} />;
}
