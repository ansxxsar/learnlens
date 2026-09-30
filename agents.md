# AI Agent Guidelines

This file defines how AI coding assistants may contribute to LearnLens.

## Project priorities

1. Protect students, their code, and course data.
2. Keep assessment behavior explainable and instructor-controlled.
3. Complete the MVP vertical slice before expanding scope.
4. Prefer deterministic evidence over unsupported model claims.
5. Keep gamification separate from official academic grades.

## Working rules

- Read `README.md`, `specifications.md`, and `development.md` before changing code.
- Work only on the requested issue or clearly state any necessary scope change.
- Preserve existing user work and avoid destructive commands.
- Never commit secrets, tokens, student records, production data, or private submissions.
- Do not weaken authentication, authorization, sandboxing, audit logging, or test isolation to simplify development.
- Treat all submitted code as hostile input.
- Never run untrusted code in the API process or with unrestricted network or host filesystem access.
- Do not expose hidden tests, system prompts, infrastructure details, or other students' data.
- AI feedback must cite available rubric or execution evidence and use a deterministic fallback when evidence is insufficient.
- Do not make an AI model the sole authority for final grades or misconduct decisions.

## Change process

- Create or update an issue with acceptance criteria.
- Use a focused branch and Conventional Commit messages.
- Add or update tests for changed behavior.
- Run formatting, linting, unit tests, and relevant integration tests.
- Update documentation when interfaces, setup, scope, or decisions change.
- Summarize assumptions, tests, and remaining risks in the pull request.

## Code quality

- Prefer small modules, explicit types, and clear interfaces.
- Validate data at trust boundaries.
- Keep business rules out of UI components and route handlers.
- Use structured logs without sensitive code or personal data.
- Handle timeouts and external-service failures explicitly.
- Add comments for security constraints and non-obvious decisions, not for obvious syntax.

## Documentation precedence

When instructions conflict, follow the current assignment requirements first, then `specifications.md`, then `development.md`, and record any unresolved conflict for human review.
