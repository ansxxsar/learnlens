import { Link, useLocation } from "react-router-dom";
import {
  comparison,
  howItWorks,
  principles,
  teamMembers,
} from "../../data/about";
import { getReturnPath } from "../../utils/aboutNavigation";
import { AttemptDemo } from "./AttemptDemo";

const initialsOf = (name: string): string =>
  name
    .split(" ")
    .map((part) => part[0])
    .join("");

export function AboutContent() {
  const location = useLocation();

  return (
    <article className="about">
      <header className="about-hero">
        <span
          className="about-hero__shape about-hero__shape--pink"
          aria-hidden="true"
        />
        <span
          className="about-hero__shape about-hero__shape--blue"
          aria-hidden="true"
        />
        <span
          className="about-hero__shape about-hero__shape--ring"
          aria-hidden="true"
        />

        <div className="about-hero__text">
          <span className="about-pill">✦ About LearnLens</span>
          <h1>
            Every wrong answer is a <mark>step forward.</mark>
          </h1>
          <p>
            LearnLens is an AI-assisted assessment platform for introductory
            programming courses. It helps students understand their mistakes
            right after submitting code, and it saves instructors from repeating
            the same first-pass feedback.
          </p>
        </div>

        <AttemptDemo />
      </header>

      <section className="about-section reveal">
        <h2>Why we are building it</h2>
        <ul className="about-compare">
          {comparison.map((row) => (
            <li key={row.before}>
              <span className="about-compare__before">{row.before}</span>
              <span className="about-compare__arrow" aria-hidden="true">
                →
              </span>
              <span className="about-compare__after">{row.after}</span>
            </li>
          ))}
        </ul>
      </section>

      <section className="about-section reveal">
        <h2>How it works</h2>
        <ol className="about-steps">
          {howItWorks.map((step) => (
            <li className="about-step" key={step.title}>
              <span className="about-step__who">{step.who}</span>
              <h3>{step.title}</h3>
              <p>{step.text}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="about-section reveal">
        <h2>What we care about</h2>
        <div className="about-principles">
          {principles.map((principle) => (
            <div className="about-principle" key={principle.title}>
              <span className="about-principle__symbol" aria-hidden="true">
                {principle.symbol}
              </span>
              <h3>{principle.title}</h3>
              <p>{principle.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="about-section reveal">
        <h2>Our team</h2>
        <ul className="about-team">
          {teamMembers.map((name) => (
            <li key={name}>
              <span className="about-team__avatar" aria-hidden="true">
                {initialsOf(name)}
              </span>
              <strong>{name}</strong>
            </li>
          ))}
        </ul>
      </section>

      <section className="about-cta reveal">
        <div>
          <h2>Project status</h2>
          <p>
            <span className="about-cta__dot" aria-hidden="true" />
            LearnLens is being built as academic coursework and is still in
            development, so some of the features described here are not finished
            yet.
          </p>
        </div>
        <Link
          className="primary-button about-cta__button"
          to={getReturnPath(location.state)}
        >
          Back to LearnLens
        </Link>
      </section>
    </article>
  );
}
