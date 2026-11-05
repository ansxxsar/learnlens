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

Login uses Django session cookies. Accounts are created in the admin; there is no self-registration.

| Endpoint | Purpose | Success |
|---|---|---|
| `GET /auth/csrf` | Sets the `csrftoken` cookie | 204 |
| `POST /auth/sign-in` | Body: `{"email", "password"}`. Starts a session, returns the profile | 200 |
| `POST /auth/sign-out` | Deletes the session on the server | 204 |
| `GET /auth/me` | Returns the current user and their course roles | 200 |

- `POST` requests must send the `csrftoken` cookie value in an `X-CSRFToken` header.
- `401` means not signed in (or wrong credentials), `403` means not allowed or a missing CSRF token,
  and `429` means too many sign-in attempts.
- Every API view requires a signed-in user by default. For course endpoints, use `IsCourseMember` or
  `IsCourseInstructor` from `courses/permissions.py`.
