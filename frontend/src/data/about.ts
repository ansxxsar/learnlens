export interface DemoAttempt {
  changedLine: string;
  results: { label: string; passed: boolean }[];
  feedback: string;
}

// Results are what this code really returns for each test. The feedback only
// illustrates the idea: it gives a hint and never the finished answer.
export const demoAttempts: DemoAttempt[] = [
  {
    changedLine: 'if ch == "a":',
    results: [
      { label: 'count_vowels("hello") is 2', passed: false },
      { label: 'count_vowels("APPLE") is 2', passed: false },
      { label: 'count_vowels("sky") is 0', passed: true },
    ],
    feedback:
      "Good start: your loop checks every letter. But it only looks for one vowel. Which other letters should count?",
  },
  {
    changedLine: 'if ch in "aeiou":',
    results: [
      { label: 'count_vowels("hello") is 2', passed: true },
      { label: 'count_vowels("APPLE") is 2', passed: false },
      { label: 'count_vowels("sky") is 0', passed: true },
    ],
    feedback:
      'Nice, lowercase words work now. Look at "APPLE": how does Python compare capital and small letters?',
  },
  {
    changedLine: 'if ch.lower() in "aeiou":',
    results: [
      { label: 'count_vowels("hello") is 2', passed: true },
      { label: 'count_vowels("APPLE") is 2', passed: true },
      { label: 'count_vowels("sky") is 0', passed: true },
    ],
    feedback:
      "All tests pass! Can you explain in your own words why this change fixed it?",
  },
];

export const comparison = [
  {
    before: "Feedback arrives too late to use",
    after: "Feedback right after submitting",
  },
  {
    before: "Only a score, with no explanation",
    after: "What failed, and what to try next",
  },
  {
    before: "Instructors repeat the same comments",
    after: "More time for the students who need it",
  },
];

export const howItWorks = [
  {
    who: "Instructor",
    title: "Set the challenge",
    text: "Create an assignment with a rubric and automated tests.",
  },
  {
    who: "Student",
    title: "Write and submit",
    text: "Choose a language and send in your code.",
  },
  {
    who: "LearnLens",
    title: "Run it safely",
    text: "The code runs in an isolated environment, and tests check the result.",
  },
  {
    who: "LearnLens",
    title: "Explain the result",
    text: "AI feedback uses the test results and rubric, without giving away the solution.",
  },
  {
    who: "Student",
    title: "Think and try again",
    text: "Answer a short question, improve your code and submit again.",
  },
  {
    who: "Everyone",
    title: "See the progress",
    text: "Students track their growth, and instructors spot common mistakes.",
  },
];

export const principles = [
  {
    symbol: "◎",
    title: "Instructors stay in control",
    text: "They set the assignments, rubrics and feedback rules, and make the final academic decisions.",
  },
  {
    symbol: "✓",
    title: "Feedback is based on evidence",
    text: "It comes from test results and the rubric. If the AI service is down, students still get their test results.",
  },
  {
    symbol: "?",
    title: "Learning before answers",
    text: "LearnLens explains what went wrong and what to try next. It does not write complete solutions.",
  },
  {
    symbol: "★",
    title: "XP is not a grade",
    text: "XP and levels show personal progress, and stay separate from official grades.",
  },
];

export const teamMembers = ["Ansar Murat", "Ardak Artykbayeva"];
