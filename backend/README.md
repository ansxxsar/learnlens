# LearnLens backend

Django + Django REST Framework + PostgreSQL.

Apps:

- `accounts` – custom `User` model (table `users`)
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
