# LearnLens

LearnLens is an AI-assisted formative assessment platform for introductory programming courses. It helps students understand mistakes immediately after submitting code and helps instructors reduce repetitive grading work while retaining oversight of assessment criteria and final decisions.

## Problem

Programming instructors often review many similar submissions, repeat the same explanations, and struggle to provide detailed feedback quickly. Students may receive feedback too late to use it, see only a score, or fail to understand how their skills develop across a semester.

## Proposed solution

For the first release, LearnLens focuses on one complete learning cycle:

1. An instructor creates a Python assignment, rubric, and automated tests.
2. A student submits Python code.
3. The platform runs the code in an isolated execution environment.
4. Deterministic tests produce objective evidence about correctness.
5. An AI feedback service converts that evidence into personalized, rubric-aligned guidance without directly giving away the final solution.
6. The student answers a short reflection or reinforcement question and may resubmit.
7. The student and instructor dashboards update progress and common-error analytics.

## Target users

- Students in introductory Python programming courses
- Instructors and teaching assistants managing programming assignments

## MVP scope

The MVP will include authentication and role-based access, Python assignment creation, code submission, isolated test execution, rubric-aligned AI feedback, resubmission history, short post-submission questions, XP and level progress, and instructor analytics.

The MVP will not include a native mobile application, support for multiple programming languages, a complete learning-management system, real-time multiplayer features, or fully automatic final grading. The web interface will be responsive and usable on laptops and phones.

## Success indicators

- Students receive feedback shortly after submission.
- Students can identify what failed and what concept to review.
- Instructors spend less time on repetitive first-pass feedback.
- Feedback is grounded in test results and the instructor's rubric.
- Students can see improvement across attempts and over the semester.

## Repository documents

- [specifications.md](specifications.md) — product requirements, roles, user stories, and acceptance criteria
- [development.md](development.md) — architecture, milestones, workflow, testing, and risks
- [agents.md](agents.md) — rules for AI coding assistants contributing to the repository

## Planned technology

- Frontend: React, TypeScript, and Vite
- Backend API: Django and Django REST Framework
- Background jobs: Celery and Redis
- Database: PostgreSQL
- Code execution: isolated Docker workers with strict resource and network limits
- AI feedback: provider-independent LLM service grounded in rubrics and test evidence

## Project status

Lab 1 defines the product vision, MVP scope, requirements, development approach, and repository standards. Implementation begins after requirements review.

## Team

- **Team member 1:** Ansar Murat  
- **Team member 2:** Ardak Artykbayeva

## Repository

**GitHub Classroom URL:** https://github.com/ansxxsar/learnlens

## License

This repository is created for academic coursework. A software license will be selected before public distribution.
