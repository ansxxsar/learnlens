import type { SubmissionResult } from "../../types";

interface FeedbackPanelProps {
  result: SubmissionResult;
}

export function FeedbackPanel({ result }: FeedbackPanelProps) {
  return (
    <section className="feedback-panel">
      <div className="feedback-panel__score">
        <span>Assessment score</span>
        <strong>{result.feedback.score}%</strong>
        <small>
          {result.passedTests} of {result.totalTests} tests passed
        </small>
      </div>

      <div>
        <h3>What you did well</h3>
        <ul>
          {result.feedback.strengths.map((strength) => (
            <li key={strength}>{strength}</li>
          ))}
        </ul>

        <h3>What to improve</h3>
        <ul>
          {result.feedback.improvements.map((improvement) => (
            <li key={improvement}>{improvement}</li>
          ))}
        </ul>

        <h3>Recommended next step</h3>
        <p>{result.feedback.nextStep}</p>
      </div>
    </section>
  );
}
