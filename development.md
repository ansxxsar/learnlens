# LearnLens Development Plan

## 1 Delivery strategy

Development will use a vertical-slice approach. The team will first complete one end-to-end Python assessment flow before expanding analytics or gamification. This reduces integration risk and creates a demonstrable product early.

## 2 Proposed architecture

### Client application

A responsive React and TypeScript web application will provide separate student and instructor experiences. The MVP will use one adaptive web codebase for laptop and mobile browsers rather than separate native applications.

### Application API

Django and Django REST Framework will manage users, courses, assignments, rubrics, submissions, progress, and authorization. PostgreSQL will store application records.

### Asynchronous processing

Celery and Redis will handle code-execution and AI-feedback jobs outside the request cycle. Job states will be visible to the client.

### Code execution

Submission code will run in short-lived isolated Docker workers with no outbound network access and strict CPU, memory, process, filesystem, and timeout limits. Production deployment must add defense in depth and must not expose the Docker daemon directly to the application.

### AI feedback service

The feedback service will consume a constrained evidence package containing the rubric, selected code, structured test results, and relevant submission history. It will return structured feedback. A deterministic fallback will remain available when the service times out or returns invalid output.

## 3 Planned API areas

- `/auth` for authentication and sessions
- `/courses` and `/enrollments` for course membership
- `/assignments` for instructions, rubrics, tests, status, and deadlines
- `/submissions` for attempts and processing status
- `/feedback` for structured formative feedback
- `/progress` for mastery, XP, levels, and achievements
- `/analytics` for instructor-authorized summaries

Exact endpoint conventions will be documented with an OpenAPI specification during implementation.

## 4 Milestones

### Milestone 1 Foundation and design

- Confirm personas, problem statement, MVP, and non-goals.
- Initialize the GitHub Classroom repository and documentation.
- Define wireframes, data model, architecture decisions, and issue backlog.
- Configure linting, formatting, tests, environment templates, and CI.

### Milestone 2 Course and assignment management

- Implement authentication and role authorization.
- Implement courses, enrollment, assignment creation, rubric configuration, and availability windows.
- Add student assignment list and instructor preview.

### Milestone 3 Submission and safe execution

- Implement immutable attempts and job states.
- Build an isolated Python runner and structured test result format.
- Add execution limits, failure handling, and security tests.

### Milestone 4 Feedback and revision loop

- Implement evidence-grounded structured AI feedback.
- Add deterministic fallback and instructor review.
- Add attempt comparison, reinforcement questions, and resubmission.

### Milestone 5 Progress and instructor analytics

- Implement skills, XP, levels, and selected achievements.
- Add student progress and cohort misconception dashboards.
- Distinguish gamification from official grades throughout the interface.

### Milestone 6 Validation and release

- Conduct usability tests with representative tasks.
- Complete accessibility, security, performance, and privacy checks.
- Resolve critical defects and prepare the final demonstration and report.

## 5 Team workflow

- Use GitHub Issues for traceable tasks and acceptance criteria.
- Create short-lived branches named `feat/...`, `fix/...`, `docs/...`, or `test/...`.
- Open pull requests for review before merging into `main`.
- Keep pull requests focused and link them to an issue.
- Protect `main` after repository setup and require passing checks.
- Never commit secrets; provide safe placeholders in `.env.example`.

## 6 Commit convention

Use Conventional Commits:

- `feat:` new user-facing functionality
- `fix:` defect correction
- `docs:` documentation only
- `test:` test additions or corrections
- `refactor:` internal restructuring without changed behavior
- `chore:` tooling, dependencies, or maintenance
- `ci:` continuous integration changes

Examples:

- `docs: define LearnLens product scope`
- `feat: add Python submission endpoint`
- `test: cover execution timeout policy`
- `fix: prevent students from viewing hidden tests`

## 7 Quality strategy

- Frontend unit and component tests for critical UI states
- Backend unit tests for business rules and permissions
- API integration tests for the submission lifecycle
- Runner security tests for timeouts, process limits, filesystem access, and disabled networking
- Contract tests for structured AI responses and deterministic fallbacks
- End-to-end tests for the instructor publish and student submit flows
- Manual accessibility and usability checks before each milestone review

## 8 Definition of done

A change is complete when it meets documented acceptance criteria, includes appropriate tests, passes linting and CI, contains no secrets, updates relevant documentation, receives peer review, and can be demonstrated in the integrated application.

## 9 Major risks and mitigations

### Unsafe code execution

Mitigation: isolate workers, apply resource and network limits, use disposable filesystems, keep infrastructure credentials unavailable, and test hostile cases.

### Hallucinated or inconsistent feedback

Mitigation: ground generation in structured evidence, require schema validation, record provenance, use conservative prompts, provide fallback feedback, and allow instructor override.

### Excessive project scope

Mitigation: maintain explicit non-goals and finish the vertical slice before adding languages, native mobile apps, or advanced social gamification.

### Student privacy and bias

Mitigation: minimize collected data, enforce authorization, document retention, avoid public ranking, review analytics for unfair interpretations, and pilot with non-sensitive or consented data.

### Academic integrity concerns

Mitigation: avoid complete solution generation, separate coaching from grading, preserve attempt history, disclose AI involvement, and let instructors configure feedback depth.

### External AI service failure or cost

Mitigation: process asynchronously, set limits, cache safe reusable outputs where appropriate, monitor usage, and preserve deterministic test feedback when AI is unavailable.

## 10 Initial backlog

1. Confirm final team and course metadata.
2. Accept the GitHub Classroom assignment and make the repository public if course policy requires it.
3. Add repository protection and issue labels.
4. Create low-fidelity student and instructor flow wireframes.
5. Define the initial database model and execution-result schema.
6. Create the development environment and CI pipeline.
7. Implement the first end-to-end Python submission slice.
