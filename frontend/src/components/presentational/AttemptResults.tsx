import type { Submission, TestResult } from "../../types";
import { errorLabels } from "../../utils/testResults";

interface AttemptResultsProps {
  attempt: Submission;
}

function OutputBlock({ label, value }: { label: string; value: string }) {
  return (
    <div className="test-io">
      <span className="test-io__label">{label}</span>
      {value ? (
        <pre className="test-io__value">{value}</pre>
      ) : (
        <span className="test-io__empty">(empty)</span>
      )}
    </div>
  );
}

function ResultItem({ result }: { result: TestResult }) {
  const label = result.passed
    ? "Passed"
    : result.errorType
      ? errorLabels[result.errorType]
      : "Failed";
  // Only public tests come with outputs; the server sends null for hidden ones.
  const showOutputs = !result.passed && result.actualOutput !== null;

  return (
    <li className="detail-list__item">
      <div className="detail-list__header">
        <strong>{result.testName}</strong>
        <span className="detail-list__meta">
          <span
            className={`status ${result.passed ? "test-result--passed" : "test-result--failed"}`}
          >
            {label}
          </span>
          {result.runtimeMs !== null && <span>{result.runtimeMs} ms</span>}
        </span>
      </div>

      {showOutputs && (
        <div className="test-io__pair test-io__pair--three">
          <OutputBlock label="Input" value={result.stdinInput ?? ""} />
          <OutputBlock label="Expected" value={result.expectedOutput ?? ""} />
          <OutputBlock label="Your output" value={result.actualOutput ?? ""} />
        </div>
      )}
      {!result.passed && result.errorOutput && (
        <div className="test-io test-result__error">
          <span className="test-io__label">
            {result.errorType === "compile_error"
              ? "Compiler message"
              : "Error output"}
          </span>
          <pre className="test-io__value">{result.errorOutput}</pre>
        </div>
      )}
      {!result.passed && result.isHidden && !result.errorOutput && (
        <p className="auth-form__hint">
          The input of hidden tests is not shown. Check edge cases such as
          empty input, negative numbers or very large values.
        </p>
      )}
    </li>
  );
}

// Shows one attempt's progress and, once it has run, its test results. Kept
// separate from grades: these are automatic checks only.
export function AttemptResults({ attempt }: AttemptResultsProps) {
  const heading = `Attempt ${attempt.attemptNumber}`;

  if (attempt.status === "queued" || attempt.status === "running") {
    return (
      <section className="attempt-results" aria-live="polite">
        <h4>{heading}</h4>
        <p className="state-message">
          {attempt.status === "queued"
            ? "Waiting for a free runner..."
            : "Running your code against the tests..."}
        </p>
      </section>
    );
  }

  if (attempt.status === "failed") {
    return (
      <section className="attempt-results" aria-live="polite">
        <h4>{heading}</h4>
        <p className="error-message">
          Your code could not be checked because of a problem on our side, not
          in your code. Your attempt is saved and will be checked once the
          problem is fixed.
        </p>
      </section>
    );
  }

  const compileError = attempt.results.find(
    (result) => result.errorType === "compile_error",
  );
  const allPassed =
    attempt.testCount > 0 && attempt.passedCount === attempt.testCount;

  return (
    <section className="attempt-results" aria-live="polite">
      <div className="assignment-details__heading">
        <h4>{heading}</h4>
        {attempt.testCount > 0 && (
          <span
            className={`status ${allPassed ? "test-result--passed" : "test-result--failed"}`}
          >
            {attempt.passedCount} of {attempt.testCount} tests passed
          </span>
        )}
      </div>

      {attempt.testCount === 0 ? (
        <p className="state-message">
          There are no automatic tests for this attempt yet.
        </p>
      ) : compileError ? (
        // Every test fails the same way, so the message is shown once.
        <div className="test-io test-result__error">
          <span className="test-io__label">Your code didn't compile</span>
          <pre className="test-io__value">{compileError.errorOutput}</pre>
        </div>
      ) : (
        <ul className="detail-list">
          {attempt.results.map((result, index) => (
            <ResultItem key={index} result={result} />
          ))}
        </ul>
      )}
    </section>
  );
}
