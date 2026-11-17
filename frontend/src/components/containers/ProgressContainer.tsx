import { useEffect } from "react";
import { useAppStore } from "../../store/useAppStore";
import { ProgressPanel } from "../presentational/ProgressPanel";

export function ProgressContainer() {
  const progress = useAppStore((state) => state.progress);
  const error = useAppStore((state) => state.error);
  const loadProgress = useAppStore((state) => state.loadProgress);

  useEffect(() => {
    void loadProgress();
  }, [loadProgress]);

  if (error) {
    return <p className="error-message">{error}</p>;
  }
  return progress ? <ProgressPanel progress={progress} /> : null;
}
