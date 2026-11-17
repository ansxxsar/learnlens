# LearnLens backend

Django + Django REST Framework + PostgreSQL.

Apps:

- `accounts` – custom `User` model (table `users`) and the `/auth` API
- `courses` – Phase 2 course setup: `courses`, `course_sections`, `enrollments`,
  `skills`, `assignments`, `rubric_criteria`, `test_cases`

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
```

## Common commands

```sh
python manage.py migrate           # create / update tables
python manage.py test              # run tests (needs the CREATEDB permission)
python manage.py createsuperuser   # admin login (email + password)
python manage.py runserver         # admin at http://127.0.0.1:8000/admin/
```

## Authentication API

Login uses Django session cookies. Only `@sdu.edu.kz` emails can register, and new accounts have no
courses until they are enrolled. The `account_type` in the profile comes from these rules:

| Account | `account_type` |
|---|---|
| Has an instructor enrollment | `teacher` |
| Admin | `admin` |
| Email starts with a number, or has a student enrollment | `student` |
| Anyone else (a name-based email with no enrollment) | `pending_teacher` |

To approve a teacher, open **Users** in the admin site, filter by **Waiting for approval**, then add an
enrollment with the `instructor` role. The email never grants teacher access by itself. Registration does
not verify that someone owns the address yet, so add email verification before real users can register.

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
