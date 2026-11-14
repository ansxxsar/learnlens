# LearnLens – System Requirements Specification (SRS)

**Course:** PED 741 Software Development Practice · Assignment 3
**Team:** Ansar Murat, Ardak Artykbayeva
**Version:** 1.0 (Assignment 3) · builds on `specifications.md` (Lab 1) and `docs/erd/learnlens-erd.drawio`
**Diagrams:** [`docs/diagrams/behavioral/`](diagrams/behavioral/) · [`docs/diagrams/structural/`](diagrams/structural/)

---

## 1 Introduction

### 1.1 Purpose
This document specifies what the LearnLens MVP must do (functional requirements) and how well it must do it (non-functional requirements). Every requirement has an ID, is written as a testable **"shall"** statement, and is traced to use cases and UML diagrams in Section 8.

### 1.2 Product scope
LearnLens is an AI-assisted formative assessment platform for introductory programming courses. A student submits code, the platform runs it against instructor-defined tests in an isolated sandbox, and an AI service turns the test evidence into rubric-aligned feedback. The instructor keeps control of assignments, rubrics and final scores.

### 1.3 Definitions

| Term | Meaning |
|---|---|
| Attempt / Submission | One immutable set of files a student submits for an assignment |
| Public test | Test case whose input and result the student may see |
| Hidden test | Test case whose input and expected output are never shown to students |
| Evidence | Test results, error types and rubric criteria used to ground AI feedback |
| Fallback feedback | Feedback built only from test results when the AI service fails or is not confident |
| Section | A practice group inside a course, e.g. PED 277 "02 P" |

---

## 2 Problem space vs. solution space

The **problem space** describes the situation and needs *without* naming technology. The **solution space** describes what LearnLens will build to meet those needs.

| # | Problem space (current situation) | Solution space (LearnLens response) | Requirements |
|---|---|---|---|
| P1 | Instructors of 60–100 students review many similar submissions and repeat the same explanations. | Automated tests give first-pass evidence; AI drafts feedback; the instructor reviews only exceptions. | FR-13 – FR-16, FR-21 |
| P2 | Students get feedback days later, when it is no longer useful. | Test results within 30 s, feedback within 90 s of submitting. | NFR-P3, NFR-P4 |
| P3 | Classic autograders show only "pass/fail" or a score. | Feedback separates strengths, issues and next steps, linked to rubric criteria. | FR-15 |
| P4 | Unrestricted AI tools give wrong answers or full solutions. | Prompts use only rubric + public evidence; no full solutions; fallback when confidence is low. | FR-15 – FR-17 |
| P5 | Students cannot see how their skills develop over a semester. | Attempt history, XP, levels and skill mastery dashboard. | FR-19, FR-20 |
| P6 | Instructors cannot see which concepts the whole class struggles with. | Cohort analytics of common failed criteria and attempt patterns. | FR-22 |
| P7 | Running student code is a security risk. | Code runs only in isolated Docker workers with strict limits. | FR-13, NFR-S1 |

**Out of scope for the MVP:** native mobile apps, full LMS features (attendance, messaging, scheduling), plagiarism verdicts, languages other than Python, Java, C++, JavaScript, HTML and CSS, fully automatic final grading.

---

## 3 User personas

### Persona 1 – Aigerim, first-year student (primary user)

- **Context:** Physics Education student in PED 277 Introduction to Programming, section "02 P". First programming course; uses a laptop at university and a phone on the bus.
- **Goals:** understand *why* her code fails before the deadline; improve step by step; see her progress.
- **Frustrations:** "Wrong answer" with no explanation; waiting a week for grades; feeling embarrassed to ask the same question again.
- **What she needs from LearnLens:** fast, friendly, specific feedback; a clear status while grading runs; no public ranking.
- **Key use cases:** UC-02, UC-05, UC-06, UC-07.

### Persona 2 – Mr. Nurlan, instructor (primary user)

- **Context:** Assistant instructor teaching ~70 students in 3 practice sections plus a Data Structures course. Grades weekly labs.
- **Goals:** spend less time on repetitive first-pass feedback; keep control over rubrics and final scores; know which topics to re-teach.
- **Frustrations:** copying the same comment 40 times; no time for students who really need help; AI tools he cannot audit.
- **What he needs from LearnLens:** easy assignment setup with rubric and tests; preview before publishing; override with a reason; class-level analytics.
- **Key use cases:** UC-11, UC-12, UC-13, UC-14, UC-15, UC-17.

### Persona 3 – Daniyar, faculty IT administrator (secondary user)

- **Context:** Manages university systems; responsible for data protection and uptime.
- **Goals:** set up courses and sections each term; keep the sandbox and AI usage safe and within budget; investigate incidents.
- **What he needs from LearnLens:** bulk enrollment, audit logs, health monitoring, AI configuration.
- **Key use cases:** UC-18, UC-01.

---

## 4 Assumptions and constraints

- **C-1** Backend: Django + Django REST Framework, PostgreSQL, Celery + Redis; frontend: React + TypeScript + Vite (see `development.md`).
- **C-2** Untrusted code runs only in Docker workers, never inside the web/API process.
- **C-3** The AI provider is accessed through a provider-independent `LLMClient` interface.
- **A-1** Courses have up to 300 enrolled students; peak load is 200 concurrent users before a deadline.
- **A-2** Students use current versions of Chrome, Firefox, Safari or Edge on laptop or phone.

---

## 5 Functional requirements

Priority uses MoSCoW (**M**ust, **S**hould, **C**ould). Each requirement includes a **verification** line describing how it will be tested.

### 5.1 Authentication and access control

| ID | Requirement | Priority | Verification |
|---|---|---|---|
| FR-01 | The system **shall** allow a registered, active user to sign in with email and password. | M | Valid credentials → session cookie issued, HTTP 200; invalid → HTTP 401 with a generic message. |
| FR-02 | The system **shall** invalidate the server-side session when the user signs out (`POST /auth/sign-out`). | M | After sign-out, reusing the old cookie returns HTTP 401. |
| FR-03 | The system **shall** lock sign-in for an account for 15 minutes after 5 consecutive failed attempts. | M | 6th attempt within 15 min returns HTTP 423 even with the correct password. |
| FR-04 | The system **shall** authorize every course-scoped request by the user's enrollment role in that course. | M | A student calling an instructor endpoint, or any user calling another course's data, receives HTTP 403. |

### 5.2 Course administration

| ID | Requirement | Priority | Verification |
|---|---|---|---|
| FR-05 | The system **shall** allow an administrator to create courses and sections (e.g. "02 P") and to enroll users with a role and an optional section of the same course. | M | Enrolling a user in a section of a different course is rejected with a validation error. |

### 5.3 Assignment management

| ID | Requirement | Priority | Verification |
|---|---|---|---|
| FR-06 | The system **shall** allow an instructor to create a draft assignment with title, instructions, due date, feedback depth (hint / guided / detailed) and late policy. | M | Draft is saved with `status = draft` and is invisible to students. |
| FR-07 | The system **shall** allow an instructor to add rubric criteria (title, max points) and test cases (input, expected output, weight, time limit, visibility public/hidden). | M | Criteria and tests are stored and linked to the assignment. |
| FR-08 | The system **shall** let the instructor preview an assignment exactly as a student sees it before publishing. | S | Preview hides hidden test data and shows the student layout. |
| FR-09 | The system **shall** allow publish only when the assignment has ≥ 1 rubric criterion, ≥ 1 test case and a due date in the future; it **shall** support close, reopen and archive. | M | Publishing an assignment without tests returns HTTP 400; state changes follow the Assignment state machine. |

### 5.4 Submission and execution

| ID | Requirement | Priority | Verification |
|---|---|---|---|
| FR-10 | The system **shall** allow an enrolled student to submit 1–10 source files (≤ 200 KB in total) in one supported language: Python, Java, C++, JavaScript, HTML or CSS. | M | 11 files or 201 KB → HTTP 400; empty submission is blocked in the UI. |
| FR-11 | The system **shall** reject a submission with HTTP 403 when the student is not enrolled, and with HTTP 409 when the assignment is not published or the deadline has passed and late submissions are not allowed. | M | Automated API tests for each case. |
| FR-12 | The system **shall** store each accepted submission as a new immutable attempt with an increasing attempt number and expose its status (`queued`, `running`, `tested`, `feedback_ready`, `failed`). | M | Earlier attempts cannot be modified through any endpoint; status is returned by `GET /api/submissions/{id}`. |
| FR-13 | The system **shall** execute every test case of a submission in an isolated worker and store pass/fail, actual output, runtime and error type (timeout, runtime, compile). | M | An infinite loop is stopped at the test's time limit and stored with `error_type = timeout`. |
| FR-14 | The system **shall** calculate automatic points for each rubric criterion from the weights of its passed test cases. | M | Unit test: 2 of 3 equally weighted tests passed on a 6-point criterion → 4.00 points. |

### 5.5 Feedback and learning support

| ID | Requirement | Priority | Verification |
|---|---|---|---|
| FR-15 | The system **shall** generate feedback for each tested attempt that is grounded only in the rubric and public evidence and is split into strengths, issues and next steps, each linked to a criterion or test result. | M | Feedback record stores `source`, `model_name`, `prompt_version` and ≥ 1 item of each kind. |
| FR-16 | The system **shall** produce deterministic fallback feedback from test results when the AI service returns an error, does not answer within 20 s, or reports confidence below 0.7. | M | With the AI service stubbed to fail, the attempt still reaches `feedback_ready` with `source = fallback`. |
| FR-17 | The system **shall not** include a complete replacement solution in student-facing feedback by default. | M | Output filter test: feedback containing a full function body that passes all tests is rejected and regenerated or replaced by fallback. |
| FR-18 | The system **shall** present one short multiple-choice reinforcement question after an attempt reaches `feedback_ready`, and show an explanation after the student answers; the answer **shall not** affect the official grade. | S | Answering changes `is_correct` and XP only, not `criterion_scores`. |
| FR-19 | The system **shall** show a student all previous attempts for an assignment and allow comparison of test outcomes and feedback between any two attempts. | S | Two attempts can be selected and are shown side by side. |
| FR-20 | The system **shall** display a student dashboard with completed assignments, attempts, XP, level and mastery per skill, clearly separated from official grades. | S | Dashboard values match the database for a seeded student. |

### 5.6 Instructor review and analytics

| ID | Requirement | Priority | Verification |
|---|---|---|---|
| FR-21 | The system **shall** allow an instructor to override the automatic points of a criterion only when a non-empty reason is entered, and **shall** record who changed it and when. | M | Override without reason → HTTP 400; with reason → `final_points`, `overridden_by`, `overridden_at` stored and audit entry written. |
| FR-22 | The system **shall** show instructors aggregated course analytics: completion rate, most frequently failed criteria, average attempts and skill trends, without public ranking of students. | S | Analytics endpoint returns aggregates only; per-student drill-down requires instructor role. |
| FR-23 | The system **shall** keep an append-only audit log of score overrides, AI feedback outputs (model, prompt version, evidence version) and administrative changes. | M | Audit records cannot be updated or deleted through the API or admin. |

---

## 6 Non-functional requirements

All targets are measured in the staging environment with 200 simulated concurrent users (A-1) unless stated otherwise.

### 6.1 Performance

| ID | Requirement | Measure |
|---|---|---|
| NFR-P1 | Read API endpoints (dashboard, assignment list, submission status) **shall** respond in ≤ 500 ms at the 95th percentile. | Load test (k6/Locust) |
| NFR-P2 | `POST /api/submissions` **shall** return `202 Accepted` in ≤ 1 s (p95), because grading runs asynchronously. | Load test |
| NFR-P3 | Deterministic test results **shall** be available ≤ 30 s (p95) after submission for assignments with ≤ 20 test cases. | Timestamp difference `submitted_at` → status `tested` |
| NFR-P4 | Feedback (AI or fallback) **shall** be available ≤ 90 s (p95) after submission. | Timestamp difference → `feedback_ready` |
| NFR-P5 | The worker pool **shall** process at least 100 submissions per minute during deadline peaks. | Queue throughput test |

### 6.2 Availability and reliability

| ID | Requirement | Measure |
|---|---|---|
| NFR-A1 | The web application and API **shall** have ≥ 99.5 % monthly availability during the teaching semester (≤ 3.6 h downtime per month, planned maintenance excluded and announced 48 h ahead). | Uptime monitor |
| NFR-A2 | An AI service outage **shall not** block access to test results, previous attempts or dashboards (graceful degradation via FR-16). | Chaos test with AI stub disabled |
| NFR-A3 | The database **shall** be backed up daily; recovery point objective ≤ 24 h and recovery time objective ≤ 4 h. | Quarterly restore drill |
| NFR-A4 | A failed sandbox job **shall** be retried automatically up to 3 times before the attempt is marked `failed`. | Fault-injection test |

### 6.3 Security and privacy

| ID | Requirement | Measure |
|---|---|---|
| NFR-S1 | Each sandbox run **shall** have no network access, ≤ 1 CPU, ≤ 256 MB memory, a read-only file system except `/tmp`, and a wall-clock limit equal to the test's `time_limit_ms` (max 10 s). | Security test suite (fork bomb, network call, large allocation) |
| NFR-S2 | Passwords **shall** be stored only as salted hashes using Django's PBKDF2-SHA256 default hasher; plain passwords **shall never** be logged. | Code review + DB inspection |
| NFR-S3 | Hidden test inputs and expected outputs **shall never** appear in any student-facing API response, log shown to students, or AI prompt. | Automated contract test on all student endpoints |
| NFR-S4 | All traffic **shall** use HTTPS (TLS 1.2 or higher); session cookies **shall** be `HttpOnly`, `Secure` and `SameSite=Lax`; state-changing requests **shall** require a CSRF token. | Security header scan |
| NFR-S5 | Sessions **shall** expire after 30 minutes of inactivity. | Integration test |
| NFR-S6 | The application **shall** have no open OWASP Top 10 findings of severity High or Critical before release. | OWASP ZAP scan |
| NFR-S7 | Only data needed for learning and assessment **shall** be stored; student code and personal data **shall not** be sent to the AI provider together with names or emails. | Prompt payload review |

### 6.4 Usability, accessibility and maintainability

| ID | Requirement | Measure |
|---|---|---|
| NFR-U1 | Core student and instructor flows **shall** meet WCAG 2.2 AA and be fully usable by keyboard. | axe audit + manual keyboard test |
| NFR-U2 | Core flows **shall** work on screens from 360 px (phone) to 1920 px wide. | Responsive test on 3 device sizes |
| NFR-U3 | A first-time student **shall** be able to submit an attempt in ≤ 3 minutes without help (≥ 80 % of 10 test users). | Usability test |
| NFR-M1 | Backend code **shall** keep ≥ 70 % automated test coverage; every API endpoint **shall** be documented in an OpenAPI specification. | CI coverage report |

---

## 7 Use case overview

Full tabular specifications are in [`diagrams/behavioral/README.md`](diagrams/behavioral/README.md).

| ID | Use case | Primary actor | Relationship |
|---|---|---|---|
| UC-01 | Sign In | User (Student, Instructor, Administrator) | — |
| UC-02 | Submit Code Attempt | Student | «include» UC-08, UC-03, UC-04 |
| UC-03 | Execute Tests in Sandbox | Code Execution Sandbox | included by UC-02 |
| UC-04 | Generate Rubric-Aligned Feedback | AI Feedback Service | included by UC-02 |
| UC-05 | Answer Reinforcement Question | Student | «extend» UC-02 |
| UC-06 | View Attempt History | Student | — |
| UC-07 | View Progress Dashboard | Student | — |
| UC-08 | Verify Enrollment & Deadline | — | included by UC-02 |
| UC-09 | Compare Attempts | Student | «extend» UC-06 |
| UC-10 | Use Test-Only Fallback Feedback | — | «extend» UC-04 |
| UC-11 | Create & Publish Assignment | Instructor | «include» UC-12 |
| UC-12 | Configure Rubric & Test Cases | Instructor | included by UC-11 |
| UC-13 | Preview as Student | Instructor | «extend» UC-11 |
| UC-14 | Review Submission | Instructor | — |
| UC-15 | Override Automated Score | Instructor | «extend» UC-14, «include» UC-16 |
| UC-16 | Record Audit Log Entry | — | included by UC-15 |
| UC-17 | View Cohort Analytics | Instructor | — |
| UC-18 | Manage Courses, Sections & Enrollments | Administrator | — |

---

## 8 Traceability matrix

| Requirement | Use cases | Diagrams |
|---|---|---|
| FR-01 – FR-03 | UC-01 | Session state machine |
| FR-04 | UC-08 | Activity (Gateway lane), Sequence (alt 401/403) |
| FR-05 | UC-18 | Class (Course, CourseSection, Enrollment) |
| FR-06 – FR-09 | UC-11, UC-12, UC-13 | Assignment state machine, Class (Assignment) |
| FR-10 – FR-12 | UC-02, UC-08 | Activity, Sequence (steps 3–15), Submission state machine |
| FR-13, FR-14 | UC-03 | Activity (Backend lane), Sequence (steps 16–21), CRC SandboxRunner / GradingWorker |
| FR-15 – FR-17 | UC-04, UC-10 | Activity (AI decision), Sequence (alt 23–27), CRC FeedbackService |
| FR-18 | UC-05 | Class (ReinforcementQuestion), Submission state machine |
| FR-19, FR-20 | UC-06, UC-07, UC-09 | Class (SkillProgress) |
| FR-21, FR-23 | UC-14, UC-15, UC-16 | Class (CriterionScore), CRC AuditLogger |
| FR-22 | UC-17 | — |
| NFR-P2, NFR-P3 | UC-02 | Activity (fork), Sequence (202 + async worker) |
| NFR-S1, NFR-S3 | UC-03 | Activity notes, Class (DockerSandboxRunner, TestCase.isVisibleTo) |
| NFR-A2, NFR-A4 | UC-04, UC-10 | Submission state machine (retry, fallback) |

---

## 9 Diagram index

| Diagram | Editable source (draw.io) | Image |
|---|---|---|
| Use Case Diagram | `diagrams/behavioral/use-case-diagram.drawio` | `use-case-diagram.png` |
| Activity Diagram with swimlanes | `diagrams/behavioral/activity-diagram-submit-code.drawio` | `activity-diagram-submit-code.png` |
| State Machine Diagrams | `diagrams/behavioral/state-machine-diagram.drawio` | `state-machine-diagram.png` |
| CRC Cards | `diagrams/structural/crc-cards.drawio` (+ tables in README) | `crc-cards.png` |
| Class Diagram | `diagrams/structural/class-diagram.drawio` | `class-diagram.png` |
| Sequence Diagram | `diagrams/structural/sequence-diagram-submit-code.drawio` | `sequence-diagram-submit-code.png` |
