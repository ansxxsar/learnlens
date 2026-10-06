# LearnLens Product Specifications

## 1 Product vision

LearnLens provides fast, actionable, and personalized formative feedback for programming assignments. It combines deterministic code testing with AI-generated explanations so that students learn from each attempt while instructors control assignments, rubrics, and assessment policies.

## 2 Problem statement

Manual review of programming work is time-consuming and repetitive, especially in large introductory classes. Existing autograders often return only pass or fail results, while unconstrained AI feedback can be inaccurate, inconsistent, or reveal complete solutions. LearnLens addresses this gap by grounding feedback in instructor-defined rubrics, execution results, and submission history.

## 3 Goals

- Reduce repetitive first-pass assessment work for instructors.
- Give students timely explanations and next-step guidance.
- Encourage mastery through revision, reflection, and visible progress.
- Preserve instructor control, transparency, privacy, and academic integrity.
- Provide semester-level evidence of individual and class progress.

## 4 Non-goals for the MVP

- Replacing the instructor's final academic judgment
- Building a complete LMS with attendance, messaging, and scheduling
- Supporting languages beyond Python, Java, C++, JavaScript, HTML, and CSS
- Delivering native Android and iOS applications
- Detecting plagiarism as a definitive misconduct decision
- Generating complete answers for students

## 5 User roles

### Student

Views assigned work, chooses a supported language, submits code, receives feedback, answers reinforcement questions, resubmits, and reviews personal progress.

### Instructor

Creates assignments, test cases, rubrics, deadlines, and feedback rules; reviews submissions and AI feedback; overrides results; and views cohort analytics.

### Administrator

Manages course access, system health, AI configuration, and audit records. This role may remain limited during the MVP.

## 6 Core user stories and acceptance criteria

### US 1 Submit code in a supported language

As a student, I want to choose Python, Java, C++, JavaScript, HTML, or CSS and submit my code so that I can receive feedback on my current attempt.

Acceptance criteria:

- Only enrolled students can submit to an available assignment.
- The submission is timestamped and stored as a new immutable attempt.
- The interface shows queued, running, completed, or failed status.
- Late or closed submissions follow the instructor's configured policy.

### US 2 Execute automated tests

As a student, I want my code checked against tests so that I can see objective evidence about correctness.

Acceptance criteria:

- Execution occurs in an isolated worker with CPU, memory, time, process, file, and network limits.
- Public-test results may be shown to the student.
- Hidden-test inputs and expected outputs are not exposed.
- Runtime errors are captured without revealing infrastructure secrets.

### US 3 Receive personalized feedback

As a student, I want feedback tied to my code and failed criteria so that I know what to improve next.

Acceptance criteria:

- Feedback references the rubric and test evidence for the current attempt.
- Feedback separates strengths, issues, and recommended next steps.
- The system avoids presenting a complete replacement solution by default.
- Low-confidence or failed AI output falls back to deterministic test feedback.
- The exact prompt version, model response, and evidence references are auditable by authorized staff.

### US 4 Revise and resubmit

As a student, I want to make another attempt so that I can learn from feedback.

Acceptance criteria:

- Previous attempts remain visible and unchanged.
- The student can compare test outcomes and feedback between attempts.
- Progress is based on demonstrated improvement, not submission count alone.

### US 5 Reinforce learning

As a student, I want a short question after submission so that I can check whether I understand the underlying concept.

Acceptance criteria:

- Questions are linked to the assignment objective or detected misconception.
- The student receives an explanation after answering.
- Questions do not affect the official grade in the MVP.

### US 6 View progress

As a student, I want a progress dashboard so that I can see my development during the semester.

Acceptance criteria:

- The dashboard shows completed assignments, attempts, mastery by skill, XP, and level.
- The interface distinguishes practice rewards from official grades.
- Progress calculations are documented and reproducible.

### US 7 Manage assessment

As an instructor, I want to configure and review assessments so that automation follows my course rules.

Acceptance criteria:

- The instructor can create a title, instructions, deadline, rubric, tests, and feedback policy.
- The instructor can preview the student experience before publishing.
- The instructor can review and override automated results with a recorded reason.

### US 8 Monitor the cohort

As an instructor, I want aggregated analytics so that I can identify concepts that require reteaching.

Acceptance criteria:

- The dashboard shows completion, common failed criteria, attempt patterns, and skill trends.
- A teacher can drill down to an individual student when authorized.
- Analytics avoid ranking students publicly.

## 7 Functional requirements

- FR 1: The system shall support student and instructor authentication.
- FR 2: The system shall enforce course-level role-based authorization.
- FR 3: Instructors shall create, edit, publish, close, and archive assignments.
- FR 4: Students shall choose a supported language (Python, Java, C++, JavaScript, HTML, or CSS), submit source code, and view attempt history.
- FR 5: The system shall queue and execute submissions in isolated workers.
- FR 6: The system shall calculate deterministic test outcomes before requesting AI feedback.
- FR 7: The system shall generate rubric-aligned feedback from approved evidence.
- FR 8: Instructors shall review and override automated assessment outputs.
- FR 9: The system shall generate or select a short reinforcement question after a completed attempt.
- FR 10: The system shall maintain XP, levels, skill mastery, and achievements separately from official grades.
- FR 11: Dashboards shall present individual progress and aggregated course analytics.
- FR 12: The system shall maintain audit logs for assessment-relevant changes and AI outputs.

## 8 Non-functional requirements

- Security: untrusted code must never execute inside the web or API process.
- Performance: ordinary submissions should return deterministic test results within 30 seconds under normal course load.
- Availability: a failed AI request must not prevent access to test results or previous submissions.
- Accessibility: core flows should target WCAG 2.2 AA and support keyboard navigation.
- Responsive design: core student and instructor flows must work on current laptop and mobile browsers.
- Privacy: collect only necessary student data and restrict access by course role.
- Explainability: each feedback item must be traceable to a rubric criterion, test result, or code location.
- Maintainability: frontend, API, execution worker, and AI feedback service must have clear interfaces and automated tests.

## 9 Key domain entities

- User, Course, Enrollment
- Assignment, RubricCriterion, TestCase
- Submission, ExecutionResult, FeedbackItem
- ReinforcementQuestion, StudentAnswer
- Skill, MasteryRecord, XPEvent, Achievement
- AuditEvent

## 10 Primary workflow

1. The instructor publishes an assignment with a rubric and tests.
2. The student chooses a supported language and submits code.
3. The API stores the attempt and queues an execution job.
4. An isolated worker runs tests and returns structured results.
5. The feedback service receives only approved code, rubric, and test evidence.
6. The platform saves feedback and a confidence or fallback status.
7. The student reviews feedback, answers a reinforcement question, and optionally resubmits.
8. Progress and instructor analytics update from recorded events.

## 11 Ethical and academic integrity safeguards

- Inform users when feedback is AI-generated.
- Let instructors inspect and override AI feedback.
- Avoid full solution generation by default.
- Validate AI statements against execution evidence where possible.
- Keep official grading policy separate from gamification rewards.
- Log model and prompt versions for reproducibility.
- Define retention and deletion rules before collecting real student data.

## 12 MVP acceptance definition

The MVP is complete when an instructor can publish one assignment with tests and a rubric, a student can submit code in any supported language and safely execute it, receive grounded feedback and a reinforcement question, resubmit, and see updated progress, while the instructor can review the complete attempt trail and class-level error summary.
