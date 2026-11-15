import { useEffect, useState } from "react";
import { demoAttempts } from "../../data/about";

const AUTO_ADVANCE_MS = 4500;

const prefersReducedMotion = (): boolean =>
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

export function AttemptDemo() {
  const [index, setIndex] = useState(0);
  // Plays by itself until the visitor takes over, and never for those who
  // asked their device to reduce motion.
  const [isAutoPlaying, setIsAutoPlaying] = useState(
    () => !prefersReducedMotion(),
  );
  const [isPaused, setIsPaused] = useState(false);

  useEffect(() => {
    if (!isAutoPlaying || isPaused) {
      return;
    }

    const timer = window.setInterval(() => {
      setIndex((current) => (current + 1) % demoAttempts.length);
    }, AUTO_ADVANCE_MS);

    return () => window.clearInterval(timer);
  }, [isAutoPlaying, isPaused]);

  const attempt = demoAttempts[index];
  const passedCount = attempt.results.filter((result) => result.passed).length;
  const total = attempt.results.length;

  return (
    <section
      className="attempt-demo"
      aria-label="Example of a student improving over three attempts"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
    >
      <div className="attempt-demo__top">
        <span className="attempt-demo__tag">Example · try it</span>
        <div className="attempt-demo__tabs">
          {demoAttempts.map((_, tabIndex) => (
            <button
              key={tabIndex}
              type="button"
              className="attempt-demo__tab"
              aria-pressed={tabIndex === index}
              onClick={() => {
                setIsAutoPlaying(false);
                setIndex(tabIndex);
              }}
            >
              Attempt {tabIndex + 1}
            </button>
          ))}
        </div>
      </div>

      <pre className="attempt-demo__code">
        <code>
          {"def count_vowels(word):\n    count = 0\n    for ch in word:\n"}
          <span className="attempt-demo__changed" key={index}>
            {`        ${attempt.changedLine}`}
          </span>
          {"\n            count += 1\n    return count"}
        </code>
      </pre>

      <div aria-live={isAutoPlaying ? "off" : "polite"}>
        <div className="attempt-demo__score">
          <strong>
            {passedCount} of {total} tests pass
          </strong>
          <div className="attempt-demo__bar" aria-hidden="true">
            <div
              className="attempt-demo__bar-value"
              style={{ width: `${(passedCount / total) * 100}%` }}
            />
          </div>
        </div>

        <ul className="attempt-demo__results">
          {attempt.results.map((result) => (
            <li
              key={result.label}
              className={
                result.passed
                  ? "attempt-demo__result attempt-demo__result--passed"
                  : "attempt-demo__result attempt-demo__result--failed"
              }
            >
              <span aria-hidden="true">{result.passed ? "✓" : "✗"}</span>
              <span>
                {result.label}
                <span className="visually-hidden">
                  {result.passed ? ": passed" : ": failed"}
                </span>
              </span>
            </li>
          ))}
        </ul>

        <p className="attempt-demo__feedback" key={index}>
          {attempt.feedback}
        </p>
      </div>
    </section>
  );
}
