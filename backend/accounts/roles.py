"""Registration and account type rules, based on SDU email addresses.

At SDU, student emails start with a number and staff emails start with a
name. The account type only chooses which home page the app shows.

Security: the account type grants no permissions. Registration is open and
does not yet prove that someone owns the address, so anyone can register a
name email and see the teacher page. Course access, including creating
assignments, still comes only from an enrollment, which only an admin can
create (see courses/permissions.py).
"""

import re

from django.conf import settings

STUDENT_EMAIL_PATTERN = r'^[0-9]'


class AccountType:
    STUDENT = 'student'
    TEACHER = 'teacher'
    ADMIN = 'admin'


def is_registration_email_allowed(email):
    # Compares the whole domain, so "x@sdu.edu.kz.evil.com" and "x@notsdu.edu.kz" fail.
    return email.rpartition('@')[2].lower() == settings.REGISTRATION_EMAIL_DOMAIN


def is_student_email(email):
    return re.match(STUDENT_EMAIL_PATTERN, email) is not None


def get_account_type(user):
    roles = set(user.enrollments.values_list('role', flat=True))

    # An enrollment states the role for certain, so it wins over the email:
    # a TA may have a number email, and a student a name email.
    if 'instructor' in roles:
        return AccountType.TEACHER
    if user.is_admin:
        return AccountType.ADMIN
    if 'student' in roles or is_student_email(user.email):
        return AccountType.STUDENT
    return AccountType.TEACHER
