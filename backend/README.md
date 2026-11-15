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
