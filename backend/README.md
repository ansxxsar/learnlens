# LearnLens backend

Django + Django REST Framework + PostgreSQL.

Apps:

- `accounts` – custom `User` model (table `users`) and the `/auth` API
- `courses` – Phase 2 course setup: `courses`, `course_sections`, `enrollments`,
  `skills`, `assignments`, `rubric_criteria`, `test_cases`
- `submissions` – attempts and their results: `submissions`, `submission_files`, `test_results`
- `execution` – the Celery worker that runs attempts in isolated Docker containers (no tables)

Table and column names follow [docs/erd/learnlens-erd.drawio](../docs/erd/learnlens-erd.drawio).

## Setup (macOS)

```sh
# PostgreSQL
brew install postgresql@18
brew services start postgresql@18
createuser learnlens --createdb --pwprompt
createdb learnlens --owner=learnlens

# Python environment
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Settings: copy the template, then set DJANGO_SECRET_KEY and POSTGRES_PASSWORD
cp .env.example .env

# Code execution: Redis (job queue) and Docker (isolated runners)
brew install redis colima docker
brew services start redis
colima start --cpu 2 --memory 4
docker pull python:3.12-alpine
docker pull node:22-alpine
docker pull eclipse-temurin:21-jdk-alpine
docker build -t learnlens-runner-cpp:1 -f execution/images/cpp.Dockerfile execution/images
```

If `docker pull` fails with `docker-credential-desktop: executable file not found`, remove the
`"credsStore": "desktop"` line from `~/.docker/config.json` (left over from Docker Desktop).

## Common commands

```sh
python manage.py migrate           # create / update tables
python manage.py test              # run tests (needs the CREATEDB permission)
python manage.py createsuperuser   # admin login (email + password)
python manage.py runserver         # admin at http://127.0.0.1:8000/admin/
celery -A config worker -l info --concurrency 2   # runs submitted code (second terminal)
python manage.py requeue_submissions [--failed]   # resend attempts after Redis or Docker was down
```

Without a running worker, attempts stay `queued`. The runner security tests in `execution/tests.py` are
skipped when Docker or the runner images are missing.

## Authentication API

Login uses Django session cookies. Only `@sdu.edu.kz` emails can register, and new accounts have no
courses until they are enrolled. The `account_type` in the profile chooses the home page: the teacher
page or the student page. It comes from these rules, in order:

| Account | `account_type` |
|---|---|
| Has an instructor enrollment | `teacher` |
| Admin | `admin` |
| Has a student enrollment, or the email starts with a number | `student` |
| Anyone else (a name-based email) | `teacher` |

The account type grants no permissions. A new teacher sees an empty teacher page until an admin enrolls
them: open **Users** in the admin site, filter by **Teachers without a course**, check that the person
really is a teacher, then add an enrollment with the `instructor` role. Registration does not verify that
someone owns the address yet, so add email verification before real users can register.

| Endpoint | Purpose | Success |
|---|---|---|
| `GET /auth/csrf` | Sets the `csrftoken` cookie | 204 |
| `POST /auth/sign-in` | Body: `{"email", "password"}`. Starts a session, returns the profile | 200 |
| `POST /auth/register` | Body: `{"full_name", "email", "password"}`. Creates an account and signs in | 201 |
| `POST /auth/sign-out` | Deletes the session on the server | 204 |
| `GET /auth/me` | Returns the current user and their course roles | 200 |
| `PATCH /auth/me` | Body: `{"full_name", "preferred_language"}`, either one. Email cannot be changed | 200 |
| `GET /auth/me/photo` | Returns the current user's photo as a JPEG | 200 |
| `PUT /auth/me/photo` | Multipart field `photo`: JPEG, PNG or WebP, up to 5 MB | 200 |
| `DELETE /auth/me/photo` | Removes the photo | 200 |
| `POST /auth/change-password` | Body: `{"current_password", "new_password"}`. Signs out other devices | 204 |

- Requests that change data must send the `csrftoken` cookie value in an `X-CSRFToken` header.
- `401` means not signed in (or wrong credentials), `403` means not allowed or a missing CSRF token,
  and `429` means too many sign-in or register attempts.
- Every API view requires a signed-in user by default. For course endpoints, use `IsCourseMember` or
  `IsCourseInstructor` from `courses/permissions.py`.
- Uploaded photos are rebuilt as 256×256 JPEGs, which removes metadata such as GPS location. They are stored
  in `backend/media/` (never committed) and are only served through the endpoint above.

## Courses API

A course is shared by its teachers and students through enrollments. A section is one teacher's group
inside a course: a student who picked a teacher is enrolled in that teacher's section. An instructor with
no section teaches the whole course.

| Endpoint | Purpose | Success |
|---|---|---|
| `GET /courses` | The signed-in user's own courses | 200 |
| `GET /courses/{id}` | One of those courses (members only) | 200 |
| `GET /courses/{id}/assignments` | The course's assignments (members only, see below) | 200 |
| `POST /courses/{id}/assignments` | Instructors: body `{"title", "instructions", "due_at", "feedback_depth", "publish"}` | 201 |
| `PATCH /courses/{id}/assignments/{aid}` | Instructors: any of the fields above, or `"status"` | 200 |
| `DELETE /courses/{id}/assignments/{aid}` | Instructors: deletes a draft | 204 |

Each course has `id`, `code`, `title`, `term`, `role` (`student` or `instructor`), `section_code`,
`instructor_names` and `student_count`.

- `instructor_names` lists the teachers of the user's section plus anyone who teaches the whole course.
  Teachers are shown by name only, never by email.
- `student_count` is only sent to instructors: the students in their section, or in the whole course if
  they have no section. Students get `null`.
- Courses are created, and people enrolled, in the admin site for now.

Assignment rules (in `courses/services.py`):

- Students see only `published` and `closed` assignments. Drafts and archived work are hidden from them.
- New assignments are drafts unless `"publish": true` is sent. `status`, `course` and `published_at` cannot be
  set directly.
- Status moves only as `draft → published → closed ⇄ published`, and `published` or `closed → archived`.
  Archived assignments cannot be changed.
- Only drafts can be deleted, because published work may already have student attempts.
- `due_at` must be in the future whenever it is set.
- Assignments belong to the whole course, so every instructor of the course can manage them.
- Responses never include test cases, so hidden tests cannot leak through these endpoints.

### Rubric and tests

Each assignment has a rubric (scored criteria) and test cases (an input and the exact output expected). The
tests are what the execution workers will run once they exist.

| Endpoint | Purpose | Success |
|---|---|---|
| `GET /courses/{id}/assignments/{aid}/rubric` | Members: the criteria in `position` order | 200 |
| `POST /courses/{id}/assignments/{aid}/rubric` | Instructors: body `{"title", "description", "max_points", "position"}` | 201 |
| `PATCH /courses/{id}/assignments/{aid}/rubric/{cid}` | Instructors: any of the fields above | 200 |
| `DELETE /courses/{id}/assignments/{aid}/rubric/{cid}` | Instructors: removes the criterion | 204 |
| `GET /courses/{id}/assignments/{aid}/tests` | Instructors: every test. Students: public tests only | 200 |
| `POST /courses/{id}/assignments/{aid}/tests` | Instructors: body `{"name", "visibility", "stdin_input", "expected_output", "weight", "time_limit_ms", "criterion"}` | 201 |
| `PATCH /courses/{id}/assignments/{aid}/tests/{tid}` | Instructors: any of the fields above | 200 |
| `DELETE /courses/{id}/assignments/{aid}/tests/{tid}` | Instructors: removes the test | 204 |

- **Hidden tests never reach students.** The query itself filters them out, and students get only `id`,
  `name`, `stdin_input` and `expected_output` of public tests.
- New tests are `hidden` unless `"visibility": "public"` is sent.
- Students can read the rubric and public tests of `published` and `closed` assignments only; others answer
  404. Instructors can prepare them on drafts.
- `max_points` and `weight` are between 0.01 and 1000. `time_limit_ms` is between 100 and 10,000, so one test
  cannot hold a worker for long. Input and expected output are at most 20,000 characters each, and their
  whitespace is kept exactly.
- `criterion` links a test to a criterion of the same assignment, or is `null`. Deleting a criterion keeps
  its tests and only unlinks them.
- New criteria go to the end of the rubric unless `position` is sent.
- The rubric and tests of an archived assignment cannot be changed. Tests can still be edited after
  publishing; earlier attempts are not re-checked automatically.
- Skills cannot be linked to criteria through the API yet (admin only).

## Submissions and daily progress API

Students submit code to published assignments of their own courses. **The API never runs it.** It saves
the attempt as `queued` and hands it to the execution worker (see [Code execution](#code-execution)).

| Endpoint | Purpose | Success |
|---|---|---|
| `GET /courses/{id}/assignments/{aid}/submissions` | Students: their own attempts, newest first, with their code and test results | 200 |
| `POST /courses/{id}/assignments/{aid}/submissions` | Students: body `{"language", "code"}`. Saves a new attempt | 201 |
| `GET /progress` | The signed-in user's daily practice and open tasks | 200 |

- `language` is one of `python`, `java`, `cpp`, `javascript`, `html`, `css`. It decides the entry file
  (`main.py`, `Main.java`, ...), which is how the language is stored, as the ERD has no language column.
- Code must be non-empty and at most 50,000 characters. Whitespace is kept exactly.
- Closed assignments take no new attempts. Drafts and archived ones answer 404. Instructors get 403.
- At most 20 submissions per minute per user (`429` after that).
- In `GET /courses/{id}/assignments`, students also get `attempt_count`, their own number of attempts.

`GET /progress` returns `today`, `streak_days`, `practiced_today`, `week` (the last 7 days with a count of
submissions each), `tasks` (published assignments in the user's student courses, soonest deadline first,
each with `is_done` and `is_overdue`), `completed_tasks` and `total_tasks`.

- A task is done once the student has submitted to it at least once. Progress tracks practice, not
  correctness, and is kept separate from grades.
- Days start at midnight in `TIME_ZONE` (`Asia/Almaty`), not UTC.
- The streak counts days in a row with at least one submission. It stays alive until the end of today, so
  it counts back from yesterday when today has no submission yet.

## Code execution

A Celery worker (`execution/`) takes each queued attempt, runs it against every test case of its
assignment, stores one `test_results` row per test and sets the attempt to `completed`. If Docker itself
fails, the attempt becomes `failed` and can be retried with `manage.py requeue_submissions --failed`.

| Language | Image | Steps |
|---|---|---|
| Python | `python:3.12-alpine` | `python3 -I main.py` |
| JavaScript | `node:22-alpine` | `node main.js` |
| Java | `eclipse-temurin:21-jdk-alpine` | `javac Main.java`, then `java Main` (class must be `Main`) |
| C++ | `learnlens-runner-cpp:1` (built from `execution/images/`) | `g++ -std=c++17 -O2`, then `./main` |

HTML and CSS attempts are not run yet; they complete with no results.

**Isolation (execution/runner.py).** Submitted code is hostile. Every test runs in a new container with no
network, a read-only root filesystem (64 MB tmpfs for `/work` and `/tmp`), 256 MB of memory (512 MB for
Java) and no swap, one CPU, 64 processes (128 for Java), 16 MB per file, 64 open files, no capabilities,
`no-new-privileges`, user 65534 and no logs. Nothing from the host is mounted and the worker's environment
variables are not passed in. The container is removed when it stops. The host enforces the limits that the
code could otherwise tamper with: the test's time limit (after a separate 20-second compile budget) and
64 KiB per output stream.

The worker needs the Docker daemon, so it must run as its own process; the API never runs code. In
production the daemon must not be reachable from the API, and the runner needs more defence in depth, such
as gVisor or a separate VM per worker (development.md).

**Verdicts.** A test passes when the program exits with 0 and its output matches the expected output, line
by line, ignoring spaces at line ends and blank lines at the end. Otherwise `error_type` is one of
`compile_error`, `time_limit`, `output_limit`, `memory_limit` (killed by the out-of-memory killer),
`runtime_error` (non-zero exit) or `wrong_answer`. `runtime_ms` is wall time measured by the host, so it
includes a little start-up time.

**What students see.** In `results`, public tests include the input, expected output, the program's output
and its stderr. Hidden tests are named "Hidden test 1, 2, ..." and include only `passed`, `error_type` and
`runtime_ms`, because a program can print its secret input. The only exception is a compiler message,
which depends on the code alone. Each attempt also has `passed_count` and `test_count`.

Known limits: Java and C++ are compiled again for each test; changing tests does not re-run old attempts;
instructors cannot see their students' results in the app yet.
